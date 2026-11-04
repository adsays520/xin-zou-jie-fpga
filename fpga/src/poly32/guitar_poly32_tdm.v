// 32 independent voice contexts on ONE physical-string arithmetic engine.
// Fixed budget: 32 slots x 31 clocks = 992 clocks / 48 kHz frame.
// Each slot: restore, 21 FSM clocks, FIR/gain/mix/allocator, context save.
// Events enter a 16-entry FIFO. Full allocation fades the quietest playing voice
// over 64 audio samples before reuse. Initializing notes are never stolen.
module guitar_poly32_tdm #(
    parameter ENABLE_PICK_SOFTENER = 0,
    parameter ENABLE_VOICE_FIR = 0,
    parameter ENABLE_VOICE_ADSR = 1,
    // Piano voicing keeps the physical steel-string resonator, but replaces
    // the guitar pick contour with a short hammer excitation, pitch-dependent
    // spectral darkening and pitch-dependent natural decay.
    parameter ENABLE_PIANO_TIMBRE = 0,
    parameter ENABLE_TAIL_HF_DAMPING = 0,
    parameter ENABLE_DYNAMIC_TAIL_EQ = 1,
    parameter [23:0] QUIET_THRESHOLD = 24'd2048,
    parameter integer QUIET_FRAMES = 2048,
    parameter integer MIN_AGE_FRAMES = 4800
)(
    input wire clk, rst_n, sample_tick, note_on, poly_mode,
    input wire pitch_enabled,
    input wire [23:0] pitch_ratio_q20,
    input wire [9:0] requested_delay_len, requested_pick_offset,
    input wire [15:0] requested_loop_gain_q15, requested_scrape_q15,
    input wire [23:0] requested_damping_q23, requested_allpass_q23,
    input wire [31:0] requested_init_phase_step,
    input wire [15:0] requested_noise_mix_q15,
    input wire [1:0] requested_excitation_smooth,
    input wire [2:0] requested_string_sel,
    input wire [6:0] velocity,
    input wire requested_custom_envelope,
    input wire envelope_ram_we,
    input wire [11:0] envelope_ram_addr,
    input wire [15:0] envelope_ram_data,
    output wire sample_valid,
    output wire signed [23:0] sample_out,
    output wire active,
    output reg [5:0] active_count,
    output wire [31:0] occupied,
    output reg [31:0] dropped_events,
    output reg [31:0] stolen_events,
    output reg deadline_miss,
    output wire limited
);
    // Per-voice ADSR constants. The controller is intentionally part of this
    // TDM module so synthesis cannot discard a separate hierarchy while the
    // gain state remains stored with each voice context.
    // The recorded board output showed that the former 85 ms Attack masked
    // the string's existing pick transient: level did not peak until roughly
    // 120..200 ms, while Decay changed gain by only 0.63 dB.  Use a physical
    // pluck contour instead: near-instant contact, a clearly separate body
    // decay, then a shallow Sustain slope.  This is gain control only; pitch,
    // excitation data and the physical-string feedback remain unchanged.
    localparam [17:0] ADSR_ATTACK_FRAMES  = 18'd256;   // 5.33 ms
    localparam [17:0] ADSR_DECAY_FRAMES   = 18'd4096;  // 85.33 ms
    localparam [15:0] ADSR_SUSTAIN_Q15    = 16'd24576; // -2.50 dB
    localparam [15:0] ADSR_SUSTAIN_FLOOR_Q15 = 16'd22528; // -3.25 dB
    // Sustain continues a very shallow decline until the 1.100 s Release.
    // Release uses a long exponential fall plus a final half-rate linear
    // taper, reaching exact digital zero just before the 1.400 s guard.
    localparam [17:0] ADSR_RELEASE_START  = 18'd52800; // 1.1000 s
    localparam [17:0] ADSR_TAPER_START    = 18'd64800; // 1.3500 s
    localparam [17:0] ADSR_NOTE_FRAMES    = 18'd67200; // 1.4000 s guard
    localparam [15:0] ADSR_UNITY_Q15      = 16'd32768;
    localparam [15:0] ADSR_ATTACK_STEP    = 16'd128;
    localparam [15:0] ADSR_DECAY_STEP     = 16'd2;
    localparam [17:0] ADSR_DECAY_END =
        ADSR_ATTACK_FRAMES + ADSR_DECAY_FRAMES;
    // Per-voice dynamic high-shelf.  The one-pole split runs from Note-On,
    // but high_gain=1 reconstructs the input bit-for-bit through the complete
    // attack/body.  Only the Release tail reduces the high-band residual.
    localparam [15:0] TAIL_EQ_GAIN_STEP_Q15 = 16'd4;
    localparam [15:0] TAIL_EQ_WOUND_MIN_Q15 = 16'd2048; // -24.08 dB
    localparam [15:0] TAIL_EQ_PLAIN_MIN_Q15 = 16'd4096; // -18.06 dB

    localparam [17:0] PIANO_BRIGHT_HOLD = 18'd960; // 20 ms hammer/steel attack
    localparam [17:0] PIANO_LOW_TAPER   = 18'd230400; // 4.800 s
    localparam [17:0] PIANO_LOW_END     = 18'd240000; // 5.000 s
    localparam [17:0] PIANO_MID_TAPER   = 18'd134400; // 2.800 s
    localparam [17:0] PIANO_MID_END     = 18'd144000; // 3.000 s
    localparam [17:0] PIANO_HIGH_TAPER  = 18'd52800;  // 1.100 s
    localparam [17:0] PIANO_HIGH_END    = 18'd57600;  // 1.200 s

    // The custom curve spans the same 1.400 s one-shot lifetime as the
    // existing ADSR. age * 3994 is a Q16 table position: its upper twelve
    // bits address the 4096-word RAM and its lower sixteen bits interpolate.
    localparam [11:0] CUSTOM_ENV_SCALE_Q16 = 12'd3994;

    wire [160:0] event_in = {
        requested_custom_envelope,
        requested_delay_len, requested_pick_offset,
        requested_loop_gain_q15, requested_scrape_q15,
        requested_damping_q23, requested_allpass_q23,
        requested_init_phase_step, requested_noise_mix_q15,
        requested_excitation_smooth, requested_string_sel, velocity
    };
    // UART can deliver fewer than four events during a 64-frame steal fade;
    // 16 entries retain margin without creating a 64x160 register crossbar.
    reg [160:0] fifo [0:15];
    reg [3:0] write_ptr, read_ptr;
    reg [4:0] fifo_count;
    // Isolate the top-level note decoder from the distributed FIFO write
    // crossbar. This adds one 50 MHz clock (20 ns), not an audio-frame delay.
    reg [160:0] pending_event;
    reg pending_event_valid;
    // Allocation consumes at most one event per audio frame. Therefore only
    // one slot can be fresh at a time: hold its complete parameters once,
    // instead of routing a 32x160 parameter array across the device.
    reg [160:0] fresh_event;
    reg [31:0] allocated;
    reg fresh_valid;
    reg [4:0] fresh_slot;
    // Capture the selected voice's control before loading the shared core.
    // This keeps the 32-way allocation select off the core's arithmetic path.
    reg slot_allocated_q;
    reg slot_fresh_q;
    reg running;
    reg [4:0] slot, cycle;
    reg [5:0] frame_count;
    reg signed [28:0] sum;
    reg mix_start;
    reg free_found, min_found;
    reg [4:0] free_slot, min_slot;
    reg [23:0] min_level;
    reg steal_pending;
    reg [4:0] steal_slot;
    reg [160:0] steal_event;

    // One selected voice's tail state is restored/saved together with the
    // physical-string context. This removes seven 32-way register crossbars.
    reg [17:0] age_work;
    reg [15:0] envelope_gain_work;
    reg [16:0] fade_gain_work;
    reg [23:0] level_work;
    reg [11:0] quiet_work;
    reg signed [23:0] z1_work, z2_work;
    reg [2:0] string_work;
    reg custom_env_work;
    reg [31:0] retiring;
    reg signed [23:0] filtered, enveloped, final_sample;
    reg signed [40:0] envelope_product;
    reg signed [41:0] fade_product;
    reg [23:0] peak_work;
    reg [23:0] peak_step_q,peak_decay_q,filtered_magnitude_q;
    // One transient flag for the currently scheduled slot. core_valid is a
    // one-clock pulse inside cycles 2..22 and must be retained until cycle 29.
    reg core_sample_emitted_work;

    wire event_custom_env;
    wire [9:0] p_delay, p_pick;
    wire [15:0] p_loop, p_scrape, p_noise;
    wire [23:0] p_damp, p_allpass;
    wire [31:0] p_phase;
    wire [1:0] p_smooth;
    wire [2:0] event_string;
    wire [6:0] p_velocity;
    assign {event_custom_env,p_delay,p_pick,p_loop,p_scrape,p_damp,p_allpass,p_phase,
            p_noise,p_smooth,event_string,p_velocity} = fresh_event;
    wire [2:0] p_string = string_work;
    // Delay length is an unambiguous pitch proxy and is already present in
    // every Note-On event.  Store the resulting three-way piano register in
    // the existing string_work field, avoiding any extra per-voice RAM bits.
    localparam [2:0] PIANO_LOW  = 3'd0;
    localparam [2:0] PIANO_MID  = 3'd1;
    localparam [2:0] PIANO_HIGH = 3'd2;
    wire [2:0] piano_register = (p_delay >= 10'd218) ? PIANO_LOW
        : ((p_delay <= 10'd92) ? PIANO_HIGH : PIANO_MID);
    // Move the periodic/noise excitation blend one quarter of the remaining
    // distance toward filtered noise.  This reduces the bell-like periodic
    // seed without turning the attack into unfiltered hiss.  Pitch, delay,
    // loop gain and fractional tuning are untouched.
    wire [16:0] p_noise_wide = {1'b0, p_noise};
    wire [16:0] softened_noise_wide = p_noise_wide
        + ((17'd32768 - p_noise_wide) >> 2);
    wire [15:0] piano_noise = (piano_register == PIANO_LOW) ? 16'd24576
        : ((piano_register == PIANO_MID) ? 16'd22528 : 16'd20480);
    wire [15:0] core_noise = ENABLE_PIANO_TIMBRE ? piano_noise
        : (ENABLE_PICK_SOFTENER ? softened_noise_wide[15:0] : p_noise);
    // The existing 2.6 ms decaying scrape-noise path becomes the hammer/felt
    // contact.  Low notes are softer; high notes retain a harder wooden tick.
    wire [15:0] piano_hammer = (piano_register == PIANO_LOW) ? (p_scrape >> 2)
        : ((piano_register == PIANO_MID) ? (p_scrape >> 1)
                                         : (p_scrape - (p_scrape >> 2)));
    wire [15:0] core_scrape = ENABLE_PIANO_TIMBRE ? piano_hammer
        : (ENABLE_PICK_SOFTENER ? (p_scrape >> 1) : p_scrape);
    // A physical pluck cannot impose a sample-wide corner on the string.  The
    // strongest existing five-tap blend suppresses that circulating corner;
    // it is still only a 75% blend, so useful string harmonics remain.
    wire [1:0] piano_smooth = (piano_register == PIANO_LOW) ? 2'd3
        : ((piano_register == PIANO_MID) ? 2'd2 : 2'd1);
    wire [1:0] core_smooth = ENABLE_PIANO_TIMBRE ? piano_smooth
        : (ENABLE_PICK_SOFTENER ? 2'd3 : p_smooth);
    // The softened excitation controls are only consumed by a fresh note.
    // Capture them one cycle before note_on so the distributed slot/fresh
    // selection is not on the excitation multiplier's timing path.
    reg [15:0] core_noise_q15_reg;
    reg [15:0] core_scrape_q15_reg;
    reg [1:0] core_smooth_reg;
    reg [11:0] custom_ram_read_addr;
    reg [15:0] custom_gain0;
    reg [15:0] custom_gain1;

    wire [15:0] custom_ram_dout;
    wire custom_ram_secco, custom_ram_decco;
    wire [7:0] custom_ram_dop, custom_ram_eccp;
    Gowin_ADSR u_custom_envelope_ram (
        .secco(custom_ram_secco), .decco(custom_ram_decco),
        .dout(custom_ram_dout), .dop(custom_ram_dop),
        .eccp(custom_ram_eccp),
        .clka(clk), .clkb(clk),
        .cea(envelope_ram_we), .ceb(1'b1), .oce(1'b1),
        .reset(!rst_n), .ada(envelope_ram_addr),
        .adb(custom_ram_read_addr), .din(envelope_ram_data)
    );

    wire core_valid, core_active, core_playing;
    wire signed [23:0] core_sample;
    wire [138:0] auxiliary_context_out;
    wire [138:0] auxiliary_context_in = {
        custom_env_work,
        age_work, envelope_gain_work, fade_gain_work, level_work,
        quiet_work, z1_work, z2_work, string_work
    };
    wire core_enable = running && cycle >= 2 && cycle <= 22;
    // Slot controls are prepared before cycle 0 so the context load and RAM
    // pre-read retain their original timing.
    wire core_load   = running && cycle == 0;
    wire core_save   = running && cycle == 30;
    wire mix_busy;
    wire selected_fresh = fresh_valid && fresh_slot == slot;
    wire signed [25:0] faded_wide = fade_product >>> 16;
    wire signed [23:0] contribution = slot_allocated_q
        ? faded_wide[23:0] : 24'sd0;
    wire [23:0] magnitude = contribution[23] ? -contribution : contribution;
    wire [23:0] filtered_magnitude = filtered[23] ? -filtered : filtered;
    wire [23:0] peak_step = (level_work >> 10) ? (level_work >> 10) : 24'd1;
    wire [23:0] peak_decayed = level_work > peak_step ? level_work-peak_step : 24'd0;
    // Allocation follows the physical voice level, before the low-level
    // expander, so cleaner gain cannot recursively force itself downward.
    wire [23:0] peak_next = filtered_magnitude > peak_decayed
        ? filtered_magnitude : peak_decayed;
    wire take_event = running && slot == 31 && cycle == 30
        && !steal_pending && fifo_count != 0 && (free_found || min_found);
    wire push_event = pending_event_valid && (fifo_count < 16 || take_event);
    assign occupied = allocated;
    assign active = |allocated;

    wire signed [25:0] fir_sum =
        $signed({{2{core_sample[23]}},core_sample})
        + ($signed({{2{z1_work[23]}},z1_work}) <<< 1)
        + $signed({{2{z2_work[23]}},z2_work});
    wire signed [25:0] fir_truncated = fir_sum[25] ? fir_sum+26'sd3 : fir_sum;
    // z1_work is the low-band state and z2_work[15:0] is the high-band gain
    // when the dynamic EQ is enabled. Wound strings use a lower shelf corner
    // (~0.49 kHz); plain strings use ~1.02 kHz. No filter is inserted in the
    // physical-string feedback loop.
    wire tail_eq_wound = !ENABLE_PIANO_TIMBRE && string_work >= 3'd3;
    wire signed [24:0] tail_eq_delta =
        $signed({core_sample[23], core_sample})
      - $signed({z1_work[23], z1_work});
    wire signed [24:0] tail_eq_lp_step = ENABLE_PIANO_TIMBRE
        ? ((string_work == PIANO_LOW) ? (tail_eq_delta >>> 4)
            : ((string_work == PIANO_MID) ? (tail_eq_delta >>> 3)
                                           : (tail_eq_delta >>> 2)))
        : (tail_eq_wound ? (tail_eq_delta >>> 4) : (tail_eq_delta >>> 3));
    wire signed [24:0] tail_eq_lp_wide =
        $signed({z1_work[23], z1_work}) + tail_eq_lp_step;
    wire signed [23:0] tail_eq_lp_next = tail_eq_lp_wide[23:0];
    wire signed [24:0] tail_eq_high =
        $signed({core_sample[23], core_sample})
      - $signed({tail_eq_lp_next[23], tail_eq_lp_next});
    wire [15:0] tail_eq_gain_current = z2_work[15:0];
    wire [15:0] tail_eq_gain_min = ENABLE_PIANO_TIMBRE
        ? ((string_work == PIANO_LOW) ? 16'd4096
            : ((string_work == PIANO_MID) ? 16'd8192 : 16'd13107))
        : (tail_eq_wound ? TAIL_EQ_WOUND_MIN_Q15 : TAIL_EQ_PLAIN_MIN_Q15);
    wire piano_brightness_decay = ENABLE_PIANO_TIMBRE &&
        age_work >= PIANO_BRIGHT_HOLD;
    wire [15:0] tail_eq_gain_next = !ENABLE_DYNAMIC_TAIL_EQ
        ? ADSR_UNITY_Q15
        : ((!piano_brightness_decay && age_work < ADSR_RELEASE_START)
            ? ADSR_UNITY_Q15
            : ((tail_eq_gain_current > tail_eq_gain_min
                + TAIL_EQ_GAIN_STEP_Q15)
                ? tail_eq_gain_current - TAIL_EQ_GAIN_STEP_Q15
                : tail_eq_gain_min));
    wire signed [41:0] tail_eq_high_product =
        $signed(tail_eq_high) * $signed({1'b0, tail_eq_gain_next});
    wire signed [26:0] tail_eq_high_scaled = tail_eq_high_product >>> 15;
    wire signed [26:0] tail_eq_output_wide =
        $signed({{3{tail_eq_lp_next[23]}}, tail_eq_lp_next})
      + tail_eq_high_scaled;
    wire signed [23:0] tail_eq_sample = tail_eq_output_wide[23:0];
    wire signed [25:0] enveloped_wide = envelope_product >>> 15;
    wire [29:0] custom_env_position = age_work * CUSTOM_ENV_SCALE_Q16;
    wire [11:0] custom_env_index =
        (age_work >= ADSR_NOTE_FRAMES - 1'b1)
        ? 12'hfff : custom_env_position[27:16];
    wire [11:0] custom_env_next_index =
        (custom_env_index == 12'hfff)
        ? 12'hfff : custom_env_index + 1'b1;
    wire [15:0] custom_env_fraction = custom_env_position[15:0];
    wire signed [16:0] custom_gain_delta =
        $signed({1'b0, custom_gain1}) - $signed({1'b0, custom_gain0});
    wire signed [33:0] custom_gain_product = custom_gain_delta
        * $signed({1'b0, custom_env_fraction});
    wire signed [33:0] custom_gain_wide =
        $signed({18'd0, custom_gain0}) + (custom_gain_product >>> 16);
    wire [15:0] custom_gain_interpolated = custom_gain_wide[33]
        ? 16'd0 : (|custom_gain_wide[32:16]
            ? 16'hffff : custom_gain_wide[15:0]);
    wire [15:0] selected_envelope_gain = custom_env_work
        ? custom_gain_interpolated
        : (ENABLE_VOICE_ADSR ? envelope_gain_work : ADSR_UNITY_Q15);
    wire custom_envelope_done = custom_env_work &&
        (age_work >= ADSR_NOTE_FRAMES - 1'b1);
    wire [15:0] adsr_release_decay = envelope_gain_work >> 12;
    wire [15:0] adsr_release_step =
        (adsr_release_decay != 16'd0) ? adsr_release_decay : 16'd1;
    reg [15:0] adsr_gain_next;
    reg [1:0] adsr_stage;
    reg adsr_done;
    wire [17:0] piano_attack_frames = (string_work == PIANO_LOW) ? 18'd192
        : ((string_work == PIANO_MID) ? 18'd128 : 18'd64);
    wire [15:0] piano_attack_step = (string_work == PIANO_LOW) ? 16'd171
        : ((string_work == PIANO_MID) ? 16'd256 : 16'd512);
    wire [17:0] piano_taper_start = (string_work == PIANO_LOW)
        ? PIANO_LOW_TAPER : ((string_work == PIANO_MID)
        ? PIANO_MID_TAPER : PIANO_HIGH_TAPER);
    wire [17:0] piano_note_end = (string_work == PIANO_LOW)
        ? PIANO_LOW_END : ((string_work == PIANO_MID)
        ? PIANO_MID_END : PIANO_HIGH_END);
    // Q1.15 has only 32768 positive unity counts, so low and middle notes use
    // fractional-count rates implemented as periodic one-count decrements.
    // High notes can lose one or two counts every sample and die naturally.
    wire [15:0] piano_high_decay_step = envelope_gain_work >> 14;
    wire [15:0] piano_decay_step = (string_work == PIANO_LOW)
        ? ((age_work[2:0] == 3'd0) ? 16'd1 : 16'd0)
        : ((string_work == PIANO_MID)
            ? ((age_work[1:0] == 2'd0) ? 16'd1 : 16'd0)
            : ((piano_high_decay_step != 0)
                ? piano_high_decay_step : 16'd1));

    // Inline Attack/Decay/Sustain/Release controller. Only gain and age are
    // context state; this combinational decision logic is shared by all 32
    // time-multiplexed voices.
    always @* begin
        adsr_gain_next = envelope_gain_work;
        adsr_stage = 2'd0;
        adsr_done = 1'b0;

        if (!ENABLE_VOICE_ADSR) begin
            adsr_gain_next = ADSR_UNITY_Q15;
            adsr_stage = 2'd2;
        end else if (ENABLE_PIANO_TIMBRE) begin
            // A piano has no held sustain stage: after hammer contact the
            // amplitude continuously decays.  Low/mid/high registers use
            // progressively shorter exponential constants and lifetimes.
            if (age_work < piano_attack_frames) begin
                adsr_stage = 2'd0;
                if (envelope_gain_work < ADSR_UNITY_Q15 - piano_attack_step)
                    adsr_gain_next = envelope_gain_work + piano_attack_step;
                else
                    adsr_gain_next = ADSR_UNITY_Q15;
            end else if (age_work < piano_taper_start) begin
                adsr_stage = 2'd1;
                if (piano_decay_step == 16'd0)
                    adsr_gain_next = envelope_gain_work;
                else if (envelope_gain_work > piano_decay_step)
                    adsr_gain_next = envelope_gain_work - piano_decay_step;
                else
                    adsr_gain_next = 16'd0;
            end else if (age_work < piano_note_end) begin
                adsr_stage = 2'd3;
                if (envelope_gain_work > 16'd2)
                    adsr_gain_next = envelope_gain_work - 16'd2;
                else begin
                    adsr_gain_next = 16'd0;
                    adsr_done = 1'b1;
                end
            end else begin
                adsr_stage = 2'd3;
                adsr_gain_next = 16'd0;
                adsr_done = 1'b1;
            end
        end else if (age_work < ADSR_ATTACK_FRAMES) begin
            adsr_stage = 2'd0;
            if (envelope_gain_work < ADSR_UNITY_Q15 - ADSR_ATTACK_STEP)
                adsr_gain_next = envelope_gain_work + ADSR_ATTACK_STEP;
            else
                adsr_gain_next = ADSR_UNITY_Q15;
        end else if (age_work < ADSR_DECAY_END) begin
            adsr_stage = 2'd1;
            // 8192 Q15 counts over 4096 samples: the pick peak separates
            // audibly from the string body without changing the excitation.
            if (envelope_gain_work > ADSR_SUSTAIN_Q15 + ADSR_DECAY_STEP)
                adsr_gain_next = envelope_gain_work - ADSR_DECAY_STEP;
            else
                adsr_gain_next = ADSR_SUSTAIN_Q15;
        end else if (age_work < ADSR_RELEASE_START) begin
            adsr_stage = 2'd2;
            // One Q15 count per 32 samples keeps Sustain alive while allowing
            // a small continuous loss instead of another uniform fast decay.
            if ((age_work[4:0] == 5'd0) &&
                envelope_gain_work > ADSR_SUSTAIN_FLOOR_Q15)
                adsr_gain_next = envelope_gain_work - 16'd1;
            else
                adsr_gain_next = envelope_gain_work;
        end else if (age_work < ADSR_NOTE_FRAMES) begin
            adsr_stage = 2'd3;
            // A 1/4096 exponential slope preserves a natural ringing tail for
            // 250 ms.  The last 50 ms uses a half-rate one-count taper so the
            // voice reaches exact zero without an audible end discontinuity.
            if (envelope_gain_work == 16'd0) begin
                adsr_gain_next = 16'd0;
                adsr_done = 1'b1;
            end else if (age_work < ADSR_TAPER_START) begin
                if (envelope_gain_work > adsr_release_step)
                    adsr_gain_next = envelope_gain_work - adsr_release_step;
                else
                    adsr_gain_next = 16'd0;
            end else if (!age_work[0]) begin
                if (envelope_gain_work > 16'd1)
                    adsr_gain_next = envelope_gain_work - 16'd1;
                else begin
                    adsr_gain_next = 16'd0;
                    adsr_done = 1'b1;
                end
            end
        end else begin
            adsr_stage = 2'd3;
            adsr_gain_next = 16'd0;
            adsr_done = 1'b1;
        end
    end

    guitar_voice_tdm_core #(
        .ENABLE_TAIL_HF_DAMPING(ENABLE_TAIL_HF_DAMPING)
    ) u_core (
        .clk(clk), .rst_n(rst_n), .enable(core_enable),
        .pitch_enabled(pitch_enabled),.pitch_ratio_q20(pitch_ratio_q20),
        .context_load(core_load), .context_save(core_save),
        .context_new(slot_fresh_q || !slot_allocated_q), .context_id(slot),
        // Four-chunk context RAM needs an early prefetch window. Cycle 23
        // leaves seven clocks before the following slot loads its context.
        .context_prefetch_id(!running ? 5'd0 : (cycle>=23 ? slot+5'd1 : slot)),
        .auxiliary_context_in(auxiliary_context_in),
        .auxiliary_context_out(auxiliary_context_out),
        .sample_tick(running && cycle==3),
        .note_on(running && cycle==2 && slot_fresh_q && slot_allocated_q),
        .requested_delay_len(p_delay), .requested_pick_offset(p_pick),
        .requested_loop_gain_q15(p_loop), .requested_scrape_q15(core_scrape_q15_reg),
        .requested_damping_q23(p_damp), .requested_allpass_q23(p_allpass),
        .requested_init_phase_step(p_phase), .requested_noise_mix_q15(core_noise_q15_reg),
        .requested_excitation_smooth(core_smooth_reg), .velocity(p_velocity),
        .sample_valid(core_valid), .sample_out(core_sample),
        .active(core_active), .playing(core_playing)
    );

    poly32_bus_manager u_bus_manager (
        .clk(clk), .rst_n(rst_n), .input_valid(mix_start),
        .sum_in(sum),
        .output_valid(sample_valid), .sample_out(sample_out),
        .busy(mix_busy), .limited(limited)
    );

    // Parameters are committed before fresh is asserted; the next frame's
    // context reset/Note-On initializes ALL core state before RAM is audible.
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            write_ptr<=0; read_ptr<=0; fifo_count<=0; dropped_events<=0;
            pending_event<=0; pending_event_valid<=0;
        end else begin
            // A new command can replace the command being consumed in this
            // clock, allowing lossless back-to-back triggers.
            if (note_on) begin
                pending_event<=event_in;
                pending_event_valid<=1'b1;
            end else if (pending_event_valid) begin
                pending_event_valid<=1'b0;
            end
            if (push_event) begin
                fifo[write_ptr]<=pending_event;
                write_ptr<=write_ptr+1'b1;
            end
            if (pending_event_valid && !push_event)
                dropped_events<=dropped_events+1'b1;
            if (take_event) read_ptr<=read_ptr+1'b1;
            case ({push_event,take_event})
                2'b10: fifo_count<=fifo_count+1'b1;
                2'b01: fifo_count<=fifo_count-1'b1;
                default: ;
            endcase
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            allocated<=0; fresh_valid<=0; fresh_slot<=0;
            slot_allocated_q<=0; slot_fresh_q<=0;
            retiring<=0; running<=0;
            slot<=0; cycle<=0; frame_count<=0; active_count<=0;
            sum<=0; mix_start<=0; free_found<=0; min_found<=0;
            free_slot<=0; min_slot<=0; min_level<=24'hffffff;
            steal_pending<=0; steal_slot<=0; steal_event<=0;
            fresh_event<=0;
            stolen_events<=0; deadline_miss<=0;
            filtered<=0; enveloped<=0; final_sample<=0;
            envelope_product<=0; fade_product<=0;
            peak_work<=0;peak_step_q<=0;peak_decay_q<=0;filtered_magnitude_q<=0;
            core_sample_emitted_work<=0;
            age_work<=0;
            envelope_gain_work<=ENABLE_VOICE_ADSR ? 16'd0 : 16'd32768;
            fade_gain_work<=65536;
            level_work<=0; quiet_work<=0; z1_work<=0;
            z2_work<=ENABLE_DYNAMIC_TAIL_EQ ? 24'sd32768 : 24'sd0;
            string_work<=0;
            custom_env_work<=1'b0;
            core_noise_q15_reg<=0; core_scrape_q15_reg<=0;
            core_smooth_reg<=0;
            custom_ram_read_addr<=12'd0;
            custom_gain0<=16'd0; custom_gain1<=16'd0;
        end else begin
            mix_start<=0;
            if (sample_tick) begin
                if (running || mix_busy) deadline_miss<=1;
                else begin
                    running<=1; slot<=0; cycle<=0; sum<=0; frame_count<=0;
                    free_found<=0; min_found<=0; min_level<=24'hffffff;
                    slot_allocated_q<=allocated[0];
                    slot_fresh_q<=fresh_valid && fresh_slot==0;
                end
            end
            if (running) begin
                if (core_valid)
                    core_sample_emitted_work<=1'b1;
                cycle<=cycle+1'b1;
                case(cycle)
                    0: begin
                        core_sample_emitted_work<=1'b0;
                        if (selected_fresh || !allocated[slot]) begin
                            age_work<=0;
                            envelope_gain_work<=ENABLE_VOICE_ADSR
                                ? 16'd0 : 16'd32768;
                            fade_gain_work<=65536; level_work<=0;
                            quiet_work<=0; z1_work<=0;
                            z2_work<=ENABLE_DYNAMIC_TAIL_EQ
                                ? 24'sd32768 : 24'sd0;
                            string_work<=selected_fresh
                                ? (ENABLE_PIANO_TIMBRE ? piano_register
                                                       : event_string)
                                : 3'd0;
                            custom_env_work<=selected_fresh
                                ? event_custom_env : 1'b0;
                        end else begin
                            {custom_env_work,age_work,envelope_gain_work,fade_gain_work,
                             level_work,quiet_work,z1_work,z2_work,
                             string_work}<=auxiliary_context_out;
                        end
                    end
                    1: begin
                        core_noise_q15_reg<=core_noise;
                        core_scrape_q15_reg<=core_scrape;
                        core_smooth_reg<=core_smooth;
                        custom_ram_read_addr<=custom_env_index;
                    end
                    2: custom_ram_read_addr<=custom_env_next_index;
                    3: custom_gain0<=custom_ram_dout;
                    4: custom_gain1<=custom_ram_dout;
                    23: if (selected_fresh) fresh_valid<=0;
                    24: begin
                        filtered <= ENABLE_DYNAMIC_TAIL_EQ
                            ? tail_eq_sample
                            : (ENABLE_VOICE_FIR
                                ? fir_truncated >>> 2 : core_sample);
                        if (ENABLE_DYNAMIC_TAIL_EQ) begin
                            z1_work <= tail_eq_lp_next;
                            z2_work <= $signed({8'd0, tail_eq_gain_next});
                        end else begin
                            z2_work<=z1_work;
                            z1_work<=core_sample;
                        end
                    end
                    25: begin
                        envelope_product <= filtered * $signed({1'b0, selected_envelope_gain});
                        peak_step_q<=peak_step;
                    end
                    26: begin
                        enveloped <= enveloped_wide[23:0];
                        filtered_magnitude_q<=filtered_magnitude;
                        peak_decay_q<=level_work>peak_step_q?level_work-peak_step_q:24'd0;
                    end
                    27: fade_product <= enveloped * $signed({1'b0,fade_gain_work});
                    28: begin
                        final_sample<=contribution;
                        // Split level decay/peak detection from the minimum
                        // search. Both use this same frame's contribution.
                        peak_work<=filtered_magnitude_q>peak_decay_q?filtered_magnitude_q:peak_decay_q;
                    end
                    29: begin
                        sum<=sum+$signed({{5{final_sample[23]}},final_sample});
                        if (slot_allocated_q) begin
                            frame_count<=frame_count+1'b1;
                            level_work<=peak_work;
                            // ADSR age begins with the first real output sample,
                            // not while the delay line is being initialized.
                            if (core_sample_emitted_work) begin
                                if (age_work!=18'h3ffff) age_work<=age_work+1'b1;
                                if (custom_env_work) begin
                                    // age_work is also the custom table phase;
                                    // the RAM data itself is never copied into
                                    // the per-voice context.
                                    quiet_work<=12'd0;
                                end else if (ENABLE_VOICE_ADSR) begin
                                    envelope_gain_work<=adsr_gain_next;
                                    quiet_work<=12'd0;
                                end
                            end
                            // At least 100 ms protects attack/initialization.
                            // Retirement observes the actually audible,
                            // post-expander sample.  Requiring every sample in
                            // the hold window to be quiet remains safe at zero
                            // crossings and reaches exact zero sooner.
                            if (!ENABLE_VOICE_ADSR) begin
                                if (age_work>=MIN_AGE_FRAMES && magnitude<QUIET_THRESHOLD) begin
                                    if (quiet_work<QUIET_FRAMES)
                                        quiet_work<=quiet_work+1'b1;
                                    else retiring[slot]<=1;
                                end else quiet_work<=0;
                            end
                            // ADSR completion is independent of the short fade
                            // used when stealing a full-bank voice.
                            if (((custom_env_work && custom_envelope_done) ||
                                 (!custom_env_work && ENABLE_VOICE_ADSR &&
                                  adsr_done)) &&
                                !(steal_pending && steal_slot==slot)) begin
                                allocated[slot]<=0;
                                envelope_gain_work<=16'd0;
                                custom_env_work<=1'b0;
                                quiet_work<=12'd0;
                                fade_gain_work<=17'd65536;
                                if (!free_found && (poly_mode || slot==0)) begin
                                    free_found<=1;
                                    free_slot<=slot;
                                end
                            end
                            if (retiring[slot] || (steal_pending && steal_slot==slot)) begin
                                if (fade_gain_work>17'd1024)
                                    fade_gain_work<=fade_gain_work-17'd1024;
                                else if (fade_gain_work!=0) fade_gain_work<=0;
                                else begin
                                    allocated[slot]<=0; retiring[slot]<=0;
                                    if (steal_pending && steal_slot==slot) begin
                                        fresh_event<=steal_event;
                                        allocated[slot]<=1;
                                        fresh_valid<=1; fresh_slot<=slot;
                                        age_work<=0;
                                        envelope_gain_work<=ENABLE_VOICE_ADSR
                                            ? 16'd0 : 16'd32768;
                                        fade_gain_work<=65536; z1_work<=0;
                                        z2_work<=ENABLE_DYNAMIC_TAIL_EQ
                                            ? 24'sd32768 : 24'sd0;
                                        level_work<=0; quiet_work<=0;
                                        string_work<=ENABLE_PIANO_TIMBRE
                                            ? ((steal_event[159:150] >= 10'd218)
                                                ? PIANO_LOW
                                                : ((steal_event[159:150] <= 10'd92)
                                                    ? PIANO_HIGH : PIANO_MID))
                                            : steal_event[9:7];
                                        custom_env_work<=steal_event[160];
                                        steal_pending<=0;
                                    end else if (!free_found && (poly_mode || slot==0)) begin
                                        // Make a naturally reclaimed slot
                                        // available to this frame's allocator.
                                        free_found<=1; free_slot<=slot;
                                    end
                                end
                            end
                            // A just-replaced slot still exposes the old core's
                            // playing flag until the next context load. Do not
                            // select it again while completing this steal.
                            if (core_playing && !retiring[slot] &&
                                !(steal_pending && steal_slot==slot) &&
                                (!min_found || peak_work<min_level) && (poly_mode || slot==0)) begin
                                min_found<=1; min_level<=peak_work; min_slot<=slot;
                            end
                        end else if (!free_found && (poly_mode || slot==0)) begin
                            free_found<=1; free_slot<=slot;
                        end
                    end
                    30: begin
                        cycle<=0;
                        if (slot==31) begin
                            running<=0; mix_start<=1; active_count<=frame_count;
                            if (take_event) begin
                                if (free_found) begin
                                    fresh_event<=fifo[read_ptr];
                                    allocated[free_slot]<=1; retiring[free_slot]<=0;
                                    fresh_valid<=1; fresh_slot<=free_slot;
                                end else begin
                                    steal_pending<=1; steal_slot<=min_slot; steal_event<=fifo[read_ptr];
                                    stolen_events<=stolen_events+1'b1;
                                end
                            end
                        end else begin
                            slot_allocated_q<=allocated[slot+5'd1];
                            slot_fresh_q<=fresh_valid && fresh_slot==(slot+5'd1);
                            slot<=slot+1'b1;
                        end
                    end
                    default: ;
                endcase
            end
        end
    end
endmodule

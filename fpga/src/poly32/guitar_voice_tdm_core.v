// Context-switched derivative of guitar_voice.v. Arithmetic and state transitions
// are unchanged; only context save/load, clock enables and banked RAM differ.
// Monophonic physically-modelled acoustic steel-string voice.
//
// All six strings share circular pick excitation, independent damping and
// fractional allpass tuning, and the same feedback loop. Material/voicing
// differences are note parameters, latched together even during retrigger.
module guitar_voice_tdm_core #(
    parameter integer SAMPLE_W        = 24,
    parameter integer MAX_DELAY       = 600,
    parameter integer MAX_PICK_OFFSET = 160,
    // Preserve the attack and body of the note, then progressively increase
    // the existing loop low-pass loss during the release tail. This removes
    // persistent upper partials without changing delay length or excitation.
    parameter ENABLE_TAIL_HF_DAMPING  = 1
)(
    input  wire                         clk,
    input  wire                         rst_n,
    output wire playing,
    input wire enable,
    input wire context_load,
    input wire context_save,
    input wire context_new,
    input wire [4:0] context_id,
    input wire [4:0] context_prefetch_id,
    input wire [138:0] auxiliary_context_in,
    output wire [138:0] auxiliary_context_out,
    input  wire                         sample_tick,
    input wire pitch_enabled,
    input wire [23:0] pitch_ratio_q20,
    input  wire                         note_on,
    input  wire [9:0]                   requested_delay_len,
    input  wire [15:0]                  requested_loop_gain_q15,
    input  wire [9:0]                   requested_pick_offset,
    input  wire [15:0]                  requested_scrape_q15,
    input  wire [23:0]                  requested_damping_q23,
    input  wire [23:0]                  requested_allpass_q23,
    input  wire [31:0]                  requested_init_phase_step,
    input  wire [15:0]                  requested_noise_mix_q15,
    input  wire [1:0]                   requested_excitation_smooth,
    input  wire [6:0]                   velocity,
    output reg                          sample_valid,
    output reg signed [SAMPLE_W-1:0]    sample_out,
    output reg                          active
);
    localparam [4:0] ST_IDLE       = 5'd0;
    localparam [4:0] ST_INIT_RAW   = 5'd2;
    localparam [4:0] ST_COMB_CUR   = 5'd3;
    localparam [4:0] ST_COMB_SHIFT = 5'd4;
    localparam [4:0] ST_COMB_WRITE = 5'd5;
    localparam [4:0] ST_WAIT       = 5'd6;
    localparam [4:0] ST_READ       = 5'd7;
    localparam [4:0] ST_DAMP       = 5'd8;
    localparam [4:0] ST_ALLPASS    = 5'd9;
    localparam [4:0] ST_PROCESS    = 5'd10;
    localparam [4:0] ST_INIT_MIX   = 5'd11;
    localparam [4:0] ST_INIT_WRITE = 5'd12;
    localparam [4:0] ST_COMB_COMMIT= 5'd13;
    localparam [4:0] ST_INIT_COMMIT= 5'd14;
    localparam [4:0] ST_LOOP_COMMIT= 5'd15;
    localparam [4:0] ST_INIT_SHAPE = 5'd16;
    localparam [4:0] ST_TAIL_DAMP  = 5'd17;
    localparam [4:0] ST_COMB_CALC  = 5'd18;
    localparam [4:0] ST_PITCH_WAIT0=20,ST_PITCH_WAIT1=21,ST_PITCH_READ=22;
    localparam [4:0] ST_PITCH_DELTA=23,ST_PITCH_MUL=24,ST_PITCH_APPLY=25;

    localparam [15:0] ATTACK_STEP_Q15    = 16'd1366;
    localparam [15:0] RETRIGGER_STEP_Q15 = 16'd1024;
    localparam [15:0] SCRAPE_DECAY_STEP  = 16'd16;
    localparam [17:0] MAX_AGE_SAMPLES    = 18'd228000;
    localparam [17:0] TAIL_DAMP_START    = 18'd19200;  // 0.400 s
    localparam [17:0] TAIL_DAMP_FULL     = 18'd51968;  // 1.083 s
    localparam [23:0] TAIL_DAMP_MAX_Q23  = 24'd2097152; // +0.2500

    // Complete per-voice sequential context; no reset on the storage array.
    // Pending-retrigger fields are intentionally not stored: the allocator
    // never retriggers an occupied context. Removing them makes room for the
    // scheduler's 138-bit per-voice tail state in the same 15 RAM lanes.
    // Two 33-bit products fit in the previously unused 99 context bits.
    // RAM lane count, context transfer cycles and 32-voice budget are unchanged.
    wire [1006:0] context_data;
    reg [15:0] pitch_fraction;
    reg signed [23:0] pitch_neighbor;
    reg signed [24:0] pitch_difference;
    reg signed [41:0] pitch_product;
    // Runtime interpolation finishes within the existing 21-clock voice slot;
    // its transient registers never cross a context boundary. Only the Q16
    // fractional phase is saved within the existing 1024-bit/four-RAM context.

    reg signed [32:0] init_current_product,init_shift_product;
    reg [4:0] state;
    assign playing = active && state == ST_WAIT;

    reg [9:0] delay_len_reg;
    reg [15:0] loop_gain_q15_reg;
    reg [9:0] pick_offset_reg;
    reg [15:0] scrape_start_q15_reg;
    reg [23:0] damping_q23_reg;
    reg [23:0] allpass_q23_reg;
    reg [31:0] init_phase_step_reg;
    reg [15:0] noise_mix_q15_reg;
    reg [1:0] excitation_smooth_reg;
    reg [6:0] velocity_reg;

    reg [9:0] pending_delay_len;
    reg [15:0] pending_loop_gain_q15;
    reg [9:0] pending_pick_offset;
    reg [15:0] pending_scrape_q15;
    reg [23:0] pending_damping_q23;
    reg [23:0] pending_allpass_q23;
    reg [31:0] pending_init_phase_step;
    reg [15:0] pending_noise_mix_q15;
    reg [1:0] pending_excitation_smooth;
    reg [6:0] pending_velocity;
    reg retrigger_pending;

    reg [9:0] init_index;
    reg [9:0] read_pointer;
    reg signed [23:0] previous_noise;
    reg signed [23:0] excitation_z1;
    reg signed [23:0] excitation_z2;
    reg signed [23:0] excitation_z3;
    reg signed [23:0] excitation_z4;
    reg signed [23:0] init_filtered_noise;
    reg signed [23:0] init_fm_seed;
    reg signed [23:0] init_raw_excitation;
    reg signed [23:0] comb_current;
    reg signed [23:0] previous_loop;
    reg signed [23:0] previous_damped;
    reg signed [23:0] previous_allpass;
    reg signed [23:0] damped_sample;
    reg signed [23:0] allpass_sample;
    reg signed [23:0] current_sample;
    reg signed [23:0] previous_scrape_noise;
    reg [23:0] lfsr;
    reg [31:0] init_phase;
    reg [31:0] mod1_phase;
    reg [31:0] mod2_phase;
    reg [15:0] output_gain_q15;
    reg [15:0] scrape_envelope_q15;
    reg [17:0] age_samples;
    reg signed [23:0] dry_sample_pipe;
    wire pitch_on=(pitch_enabled===1'b1);
    wire [20:0] phase_advance={5'd0,pitch_fraction}+(pitch_on?{1'b0,pitch_ratio_q20[23:4]}:21'd65536);
    wire [10:0] pointer_sum={1'b0,read_pointer}+phase_advance[20:16];
    wire [10:0] pointer_wrapped=pointer_sum-{1'b0,delay_len_reg};
    wire [9:0] pointer_next=pointer_sum>={1'b0,delay_len_reg}?pointer_wrapped[9:0]:pointer_sum[9:0];
    wire [9:0] neighbor_pointer=read_pointer==delay_len_reg-1'b1 ? 10'd0 : read_pointer+1'b1;
    wire [9:0] pitch_read_address=(state==ST_PITCH_WAIT0||state==ST_PITCH_WAIT1||state==ST_PITCH_READ)?neighbor_pointer:read_pointer;

    poly32_context_ram #(.WIDTH(1007)) u_context_ram (
        .clk(clk), .reset(!rst_n), .we(context_save),
        .write_id(context_id), .read_id(context_prefetch_id),
        .din({pitch_fraction,init_current_product,init_shift_product,state, delay_len_reg, loop_gain_q15_reg, pick_offset_reg,
            scrape_start_q15_reg, damping_q23_reg, allpass_q23_reg,
            init_phase_step_reg, noise_mix_q15_reg, excitation_smooth_reg,
            velocity_reg, init_index, read_pointer, previous_noise,
            excitation_z1, excitation_z2, excitation_z3, excitation_z4,
            init_filtered_noise, init_fm_seed, init_raw_excitation,
            comb_current, previous_loop, previous_damped, previous_allpass,
            damped_sample, allpass_sample, current_sample,
            previous_scrape_noise, lfsr, init_phase, mod1_phase, mod2_phase,
            output_gain_q15, scrape_envelope_q15, age_samples, sample_out,
            sample_valid, active, dry_sample_pipe, auxiliary_context_in}),
        .dout(context_data)
    );
    assign auxiliary_context_out = context_data[138:0];

    function signed [23:0] sat24;
        input signed [51:0] value;
        begin
            if (value > 52'sd8388607)
                sat24 = 24'sh7fffff;
            else if (value < -52'sd8388608)
                sat24 = 24'sh800000;
            else
                sat24 = value[23:0];
        end
    endfunction

    // One measured pluck shape, reduced from the supplied 246-sample
    // 48-kHz recording to 64 phase points.  A linear endpoint trend and DC
    // were removed before reduction so the circular delay has no artificial
    // wrap impulse.  The lookup below is linearly interpolated; the table no
    // longer becomes a 64-step staircase when stretched across a long string.
    // Peak level remains the same Q23/4 level as the old seed.  This is an
    // excitation shape only; it is never replayed as sampled audio.
    function signed [23:0] reference_pluck64;
        input [5:0] index;
        begin
            case (index)
                6'd0:  reference_pluck64 = -24'sd182916;
                6'd1:  reference_pluck64 =  24'sd547821;
                6'd2:  reference_pluck64 =  24'sd1219028;
                6'd3:  reference_pluck64 =  24'sd1828836;
                6'd4:  reference_pluck64 =  24'sd2097151;
                6'd5:  reference_pluck64 =  24'sd1645867;
                6'd6:  reference_pluck64 =  24'sd664410;
                6'd7:  reference_pluck64 =  24'sd498699;
                6'd8:  reference_pluck64 =  24'sd990441;
                6'd9:  reference_pluck64 = -24'sd90524;
                6'd10: reference_pluck64 = -24'sd448652;
                6'd11: reference_pluck64 =  24'sd658948;
                6'd12: reference_pluck64 =  24'sd527610;
                6'd13: reference_pluck64 = -24'sd205512;
                6'd14: reference_pluck64 =  24'sd56328;
                6'd15: reference_pluck64 =  24'sd903636;
                6'd16: reference_pluck64 =  24'sd801441;
                6'd17: reference_pluck64 = -24'sd141907;
                6'd18: reference_pluck64 = -24'sd221186;
                6'd19: reference_pluck64 =  24'sd136924;
                6'd20: reference_pluck64 =  24'sd68479;
                6'd21: reference_pluck64 =  24'sd311388;
                6'd22: reference_pluck64 = -24'sd24073;
                6'd23: reference_pluck64 = -24'sd470126;
                6'd24: reference_pluck64 = -24'sd44889;
                6'd25: reference_pluck64 =  24'sd589454;
                6'd26: reference_pluck64 =  24'sd60704;
                6'd27: reference_pluck64 = -24'sd584989;
                6'd28: reference_pluck64 =  24'sd68533;
                6'd29: reference_pluck64 =  24'sd82037;
                6'd30: reference_pluck64 = -24'sd848234;
                6'd31: reference_pluck64 = -24'sd471318;
                6'd32: reference_pluck64 =  24'sd918367;
                6'd33: reference_pluck64 =  24'sd1077211;
                6'd34: reference_pluck64 =  24'sd25762;
                6'd35: reference_pluck64 = -24'sd1027306;
                6'd36: reference_pluck64 = -24'sd389477;
                6'd37: reference_pluck64 =  24'sd698819;
                6'd38: reference_pluck64 =  24'sd968130;
                6'd39: reference_pluck64 =  24'sd1624143;
                6'd40: reference_pluck64 =  24'sd1686965;
                6'd41: reference_pluck64 =  24'sd773134;
                6'd42: reference_pluck64 =  24'sd728353;
                6'd43: reference_pluck64 =  24'sd556788;
                6'd44: reference_pluck64 =  24'sd805800;
                6'd45: reference_pluck64 =  24'sd1120818;
                6'd46: reference_pluck64 =  24'sd205991;
                6'd47: reference_pluck64 = -24'sd462743;
                6'd48: reference_pluck64 = -24'sd943668;
                6'd49: reference_pluck64 = -24'sd1315620;
                6'd50: reference_pluck64 = -24'sd866346;
                6'd51: reference_pluck64 = -24'sd1067925;
                6'd52: reference_pluck64 = -24'sd1619589;
                6'd53: reference_pluck64 = -24'sd1598987;
                6'd54: reference_pluck64 = -24'sd2026110;
                6'd55: reference_pluck64 = -24'sd2075873;
                6'd56: reference_pluck64 = -24'sd1305656;
                6'd57: reference_pluck64 = -24'sd1298504;
                6'd58: reference_pluck64 = -24'sd1159836;
                6'd59: reference_pluck64 = -24'sd936107;
                6'd60: reference_pluck64 = -24'sd1133576;
                6'd61: reference_pluck64 = -24'sd1126797;
                6'd62: reference_pluck64 = -24'sd676651;
                default: reference_pluck64 = -24'sd182916;
            endcase
            end
    endfunction

    wire lfsr_feedback = lfsr[23] ^ lfsr[22] ^ lfsr[21] ^ lfsr[16];
    wire [23:0] lfsr_next = {lfsr[22:0], lfsr_feedback};
    wire signed [23:0] raw_init_noise = $signed(lfsr) >>> 2;

    // Eight fractional phase bits interpolate between adjacent table points.
    // The 32-bit phase accumulator and its increment are unchanged, so this
    // removes lookup stair steps without altering pitch.  For example, E2
    // formerly held each of the 64 values for about nine audio samples.
    wire [5:0] reference_index = init_phase[31:26];
    wire [5:0] reference_next_index = reference_index + 6'd1;
    wire [7:0] reference_fraction_q8 = init_phase[25:18];
    wire signed [23:0] reference_point_a =
        reference_pluck64(reference_index);
    wire signed [23:0] reference_point_b =
        reference_pluck64(reference_next_index);
    wire signed [24:0] reference_delta =
        $signed({reference_point_b[23], reference_point_b})
      - $signed({reference_point_a[23], reference_point_a});
    // Keep both multiplier inputs as named signed nets.  Gowin synthesis can
    // otherwise lose an inferred DSP input pin when a cast, sign-dependent
    // rounding add and arithmetic shift are collapsed into one expression.
    wire signed [8:0] reference_fraction_signed =
        $signed({1'b0, reference_fraction_q8});
    wire signed [33:0] reference_delta_product =
        reference_delta * reference_fraction_signed;
    // A fixed part-select is wiring, not a CSHIFT node.  Truncation is below
    // one Q23 count and avoids the Gowin SP00019 DSP27/CSHIFT internal error.
    wire signed [25:0] reference_interpolated_delta =
        reference_delta_product[33:8];
    wire signed [25:0] reference_interpolated_wide =
        $signed({{2{reference_point_a[23]}}, reference_point_a})
      + reference_interpolated_delta;
    wire signed [23:0] reference_seed =
        reference_interpolated_wide[23:0];

    // 0.58*x[n] + 0.42*x[n-1], matching the Python initialization FIR.
    wire signed [40:0] init_noise_now_product =
        $signed(raw_init_noise) * 17'sd19005;
    wire signed [40:0] init_noise_old_product =
        $signed(previous_noise) * 17'sd13763;
    wire signed [41:0] init_noise_sum =
        $signed({init_noise_now_product[40], init_noise_now_product})
      + $signed({init_noise_old_product[40], init_noise_old_product});
    wire signed [23:0] filtered_init_noise = sat24(init_noise_sum >>> 15);

    wire [16:0] noise_mix_q15 = {1'b0, noise_mix_q15_reg};
    wire [16:0] fm_mix_q15 = 17'd32768 - noise_mix_q15;
    wire signed [40:0] noise_mix_product =
        $signed(init_filtered_noise) * $signed(noise_mix_q15);
    wire signed [40:0] fm_mix_product =
        $signed(init_fm_seed) * $signed(fm_mix_q15);
    wire signed [41:0] raw_excitation_sum =
        $signed({noise_mix_product[40], noise_mix_product})
      + $signed({fm_mix_product[40], fm_mix_product});
    wire signed [23:0] raw_excitation = sat24(raw_excitation_sum >>> 15);

    // [1 4 6 4 1]/16 excitation smoothing. Blend is explicit per string:
    // 0 = dry, 1 = 25%, 2 = 50%, 3 = 75%; independent of pitch.
    wire signed [24:0] fir5_edges =
        $signed({init_raw_excitation[23], init_raw_excitation})
      + $signed({excitation_z4[23], excitation_z4});
    wire signed [24:0] fir5_inner =
        $signed({excitation_z1[23], excitation_z1})
      + $signed({excitation_z3[23], excitation_z3});
    wire signed [25:0] fir5_center_tripled =
        ($signed({{2{excitation_z2[23]}}, excitation_z2}) <<< 1)
      + $signed({{2{excitation_z2[23]}}, excitation_z2});
    wire signed [27:0] fir5_middle =
        ($signed({{3{fir5_inner[24]}}, fir5_inner}) <<< 2)
      + ($signed({{2{fir5_center_tripled[25]}}, fir5_center_tripled}) <<< 1);
    wire signed [28:0] fir5_sum =
        $signed({{4{fir5_edges[24]}}, fir5_edges})
      + $signed({fir5_middle[27], fir5_middle});
    wire signed [23:0] fir5_excitation = fir5_sum[27:4];
    wire signed [26:0] raw_extended =
        $signed({{3{init_raw_excitation[23]}}, init_raw_excitation});
    wire signed [26:0] smooth_extended =
        $signed({{3{init_filtered_noise[23]}}, init_filtered_noise});
    wire signed [26:0] shaped_excitation =
        (excitation_smooth_reg == 2'd3)
        ? (raw_extended >>> 2) + smooth_extended - (smooth_extended >>> 2)
        : ((excitation_smooth_reg == 2'd2)
        ? (raw_extended >>> 1) + (smooth_extended >>> 1)
        : ((excitation_smooth_reg == 2'd1)
        ? raw_extended - (raw_extended >>> 2) + (smooth_extended >>> 2)
        : raw_extended));

    wire [23:0] delay_ram_dout;
    wire [23:0] scratch_ram_dout;
    wire [10:0] wrapped_pick_address =
        {1'b0, init_index} + {1'b0, delay_len_reg} - {1'b0, pick_offset_reg};
    wire [9:0] comb_read_address = (init_index >= pick_offset_reg)
        ? init_index - pick_offset_reg : wrapped_pick_address[9:0];
    // Restore the preceding CUR read when resuming a paused COMB_SHIFT.
    wire [9:0] scratch_read_address = ((state==ST_COMB_COMMIT) || (enable && state==ST_COMB_WRITE))
        ? init_index+10'd1 : ((state == ST_COMB_CUR) ||
        (!enable && state == ST_COMB_SHIFT))
        ? init_index : comb_read_address;
    wire signed [25:0] shifted_scratch =
        ($signed({{2{scratch_ram_dout[23]}},scratch_ram_dout})>>>1)+
        ($signed({{2{scratch_ram_dout[23]}},scratch_ram_dout})>>>2);
    // floor(x/2)+floor(x/4) = 3*floor(x/4)+x[1], including negative x.
    // Move the pre-DSP add to the velocity side; the residual uses the DSP MAC.
    wire signed [9:0] velocity_tripled = $signed({3'b000,velocity_reg})+
        ($signed({3'b000,velocity_reg})<<<1);
    wire signed [23:0] shifted_base = $signed(scratch_ram_dout)>>>2;
    wire signed [32:0] shifted_correction = scratch_ram_dout[1]
        ? $signed({26'd0,velocity_reg}) : 33'sd0;
    wire signed [33:0] velocity_difference =
        $signed({init_current_product[32],init_current_product})-
        $signed({init_shift_product[32],init_shift_product});
    wire signed [25:0] circular_comb =
        $signed({{2{comb_current[23]}}, comb_current})
      - ($signed({{2{init_raw_excitation[23]}}, init_raw_excitation}) >>> 1)
      - ($signed({{2{init_raw_excitation[23]}}, init_raw_excitation}) >>> 2);
    wire signed [32:0] circular_velocity_product =
        $signed(circular_comb) * $signed({1'b0, velocity_reg});

    // Shared loop: damping and fractional delay are independent. The tail
    // boost is zero through 0.40 s, then rises by 1/131072 per audio sample
    // until +0.25. It reuses the original damping multiplier, so this is a
    // frequency-dependent loop loss rather than another output envelope.
    wire [17:0] tail_damp_elapsed = age_samples - TAIL_DAMP_START;
    wire [23:0] tail_damp_ramp_q23 = {tail_damp_elapsed, 6'b0};
    wire [23:0] tail_damp_boost_q23 = (!ENABLE_TAIL_HF_DAMPING ||
        age_samples < TAIL_DAMP_START) ? 24'd0 :
        (age_samples >= TAIL_DAMP_FULL ? TAIL_DAMP_MAX_Q23
                                        : tail_damp_ramp_q23);
    wire [24:0] effective_damping_sum =
        {1'b0, damping_q23_reg} + {1'b0, tail_damp_boost_q23};
    wire [23:0] effective_damping_q23 = effective_damping_sum[24]
        ? 24'h7fffff : effective_damping_sum[23:0];
    wire signed [24:0] damping_delta =
        $signed({previous_loop[23], previous_loop})
      - $signed({current_sample[23], current_sample});
    wire signed [48:0] damping_product =
        $signed(damping_delta) * $signed({1'b0, effective_damping_q23});
    wire signed [48:0] current_q23 =
        $signed({{25{current_sample[23]}}, current_sample}) <<< 23;
    wire signed [48:0] damping_accumulator = current_q23 + damping_product;
    wire signed [23:0] next_damped_sample = sat24(damping_accumulator >>> 23);

    // A second low-pass pole fades in over the same tail interval. Its state
    // reuses previous_damped, which is already the all-pass input history.
    // The 32768-sample ramp reaches exactly Q23 0.5 using only a shift.
    wire [24:0] tail_stage_beta_ramp = {tail_damp_elapsed, 7'b0};
    wire [23:0] tail_stage_beta_q23 = (!ENABLE_TAIL_HF_DAMPING ||
        age_samples < TAIL_DAMP_START) ? 24'd0 :
        (age_samples >= TAIL_DAMP_FULL ? 24'd4194304
                                        : tail_stage_beta_ramp[23:0]);
    wire signed [24:0] tail_stage_delta =
        $signed({previous_damped[23], previous_damped})
      - $signed({damped_sample[23], damped_sample});
    wire signed [48:0] tail_stage_product =
        $signed(tail_stage_delta) * $signed({1'b0, tail_stage_beta_q23});
    wire signed [48:0] damped_q23 =
        $signed({{25{damped_sample[23]}}, damped_sample}) <<< 23;
    wire signed [48:0] tail_stage_accumulator = damped_q23 + tail_stage_product;
    wire signed [23:0] next_tail_damped_sample =
        sat24(tail_stage_accumulator >>> 23);

    // Non-recursive fractional delay. The old first-order all-pass preserved
    // high-frequency magnitude, but every sharp delay-line transition excited
    // its alternating impulse-response tail. That short ring was written back
    // into RAM on every circulation. The Q23 coefficient is now the exact
    // two-point interpolation fraction solved per note; this keeps the target
    // fundamental while making each transition monotonic rather than ringing.
    wire signed [24:0] fractional_delta =
        $signed({previous_damped[23], previous_damped})
      - $signed({damped_sample[23], damped_sample});
    wire signed [48:0] fractional_product =
        $signed(fractional_delta) * $signed({1'b0, allpass_q23_reg});
    wire signed [48:0] damped_sample_q23 =
        $signed({{25{damped_sample[23]}}, damped_sample}) <<< 23;
    wire signed [48:0] fractional_accumulator =
        damped_sample_q23 + fractional_product;
    wire signed [23:0] next_allpass_sample =
        sat24(fractional_accumulator >>> 23);

    wire signed [23:0] loop_write_sample =
        allpass_sample;
    wire signed [39:0] feedback_product =
        $signed(loop_write_sample) * $signed({1'b0, loop_gain_q15_reg});
    wire signed [23:0] feedback_sample = sat24(feedback_product >>> 15);

    wire signed [24:0] scrape_delta =
        $signed({lfsr[23], lfsr})
      - $signed({previous_scrape_noise[23], previous_scrape_noise});
    wire signed [40:0] scrape_product =
        $signed(scrape_delta) * $signed({1'b0, scrape_envelope_q15});
    wire signed [23:0] scrape_sample = sat24(scrape_product >>> 15);
    wire signed [24:0] dry_sum =
        $signed({current_sample[23], current_sample})
      + $signed({scrape_sample[23], scrape_sample});
    wire signed [23:0] dry_sample = sat24(dry_sum);
    wire signed [39:0] output_product =
        $signed(dry_sample_pipe) * $signed({1'b0, output_gain_q15});
    wire signed [23:0] gained_sample = sat24(output_product >>> 15);

    // Explicit Gowin semi-dual-port memories. Port A is write-only and port
    // B is the one-cycle synchronous read port (READ_MODE=bypass in the IP).
    wire delay_ram_write = enable && ((state == ST_COMB_COMMIT) || (state == ST_LOOP_COMMIT));
    wire scratch_ram_write = enable && (state == ST_INIT_COMMIT);
    // init_index is free during playback and holds the pre-increment loop
    // address across the registered feedback-write commit.
    wire [9:0] delay_ram_write_address = init_index;
    // comb_current is also the registered runtime feedback write value once
    // initialization has finished. One source removes a device-wide state
    // controlled mux from every delay RAM data input.
    wire [23:0] delay_ram_write_data = sat24(velocity_difference >>> 7);
    wire [23:0] scratch_ram_write_data = init_raw_excitation;
    wire delay_ram_secco;
    wire delay_ram_decco;
    wire [7:0] delay_ram_dop;
    wire [7:0] delay_ram_eccp;
    wire scratch_ram_secco;
    wire scratch_ram_decco;
    wire [7:0] scratch_ram_dop;
    wire [7:0] scratch_ram_eccp;

    poly32_road_bank u_string_delay_ram (
        .secco(delay_ram_secco), .decco(delay_ram_decco),
        .dout(delay_ram_dout), .dop(delay_ram_dop),
        .eccp(delay_ram_eccp), .clka(clk), .clkb(clk),
        .cea(delay_ram_write), .ceb(1'b1), .oce(1'b1),
        .reset(!rst_n), .bank(context_id), .ada(delay_ram_write_address),
        .adb(pitch_read_address), .last_address(delay_len_reg-10'd1),
        .init_pack(state == ST_COMB_COMMIT), .din(delay_ram_write_data)
    );

    poly32_scratch_bank u_excitation_scratch_ram (
        .secco(scratch_ram_secco), .decco(scratch_ram_decco),
        .dout(scratch_ram_dout), .dop(scratch_ram_dop),
        .eccp(scratch_ram_eccp), .clka(clk), .clkb(clk),
        .cea(scratch_ram_write), .ceb(1'b1), .oce(1'b1),
        .reset(!rst_n), .bank(context_id), .ada(init_index),
        .last_address(delay_len_reg-10'd1),
        .adb(scratch_read_address), .din(scratch_ram_write_data)
    );

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= ST_IDLE;
            delay_len_reg <= 10'd582;
            loop_gain_q15_reg <= 16'd31865;
            pick_offset_reg <= 10'd82;
            scrape_start_q15_reg <= 16'd2200;
            damping_q23_reg <= 24'd2117125;
            allpass_q23_reg <= 24'd5578383;
            init_phase_step_reg <= 32'd7379669;
            noise_mix_q15_reg <= 16'd15073;
            excitation_smooth_reg <= 2'd3;
            velocity_reg <= 7'd110;
            pending_delay_len <= 10'd582;
            pending_loop_gain_q15 <= 16'd31865;
            pending_pick_offset <= 10'd82;
            pending_scrape_q15 <= 16'd2200;
            pending_damping_q23 <= 24'd2117125;
            pending_allpass_q23 <= 24'd5578383;
            pending_init_phase_step <= 32'd7379669;
            pending_noise_mix_q15 <= 16'd15073;
            pending_excitation_smooth <= 2'd3;
            pending_velocity <= 7'd110;
            retrigger_pending <= 1'b0;
            init_index <= 10'd0;
            read_pointer <= 10'd0;
            pitch_fraction<=0;
            previous_noise <= 24'sd0;
            excitation_z1 <= 24'sd0;
            excitation_z2 <= 24'sd0;
            excitation_z3 <= 24'sd0;
            excitation_z4 <= 24'sd0;
            init_filtered_noise <= 24'sd0;
            init_fm_seed <= 24'sd0;
            init_raw_excitation <= 24'sd0;
            comb_current <= 24'sd0;
            init_current_product<=0;init_shift_product<=0;
            previous_loop <= 24'sd0;
            previous_damped <= 24'sd0;
            previous_allpass <= 24'sd0;
            damped_sample <= 24'sd0;
            allpass_sample <= 24'sd0;
            current_sample <= 24'sd0;
            previous_scrape_noise <= 24'sd0;
            lfsr <= 24'hc53a91;
            init_phase <= 32'd0;
            mod1_phase <= 32'h43a6c517;
            mod2_phase <= 32'hbd8e3129;
            output_gain_q15 <= 16'd0;
            scrape_envelope_q15 <= 16'd0;
            age_samples <= 18'd0;
            dry_sample_pipe <= 24'sd0;
            sample_valid <= 1'b0;
            sample_out <= 24'sd0;
            active <= 1'b0;
        end else if (context_load && context_new) begin
            state <= ST_IDLE;
            delay_len_reg <= 10'd582;
            loop_gain_q15_reg <= 16'd31865;
            pick_offset_reg <= 10'd82;
            scrape_start_q15_reg <= 16'd2200;
            damping_q23_reg <= 24'd2117125;
            allpass_q23_reg <= 24'd5578383;
            init_phase_step_reg <= 32'd7379669;
            noise_mix_q15_reg <= 16'd15073;
            excitation_smooth_reg <= 2'd3;
            velocity_reg <= 7'd110;
            pending_delay_len <= 10'd582;
            pending_loop_gain_q15 <= 16'd31865;
            pending_pick_offset <= 10'd82;
            pending_scrape_q15 <= 16'd2200;
            pending_damping_q23 <= 24'd2117125;
            pending_allpass_q23 <= 24'd5578383;
            pending_init_phase_step <= 32'd7379669;
            pending_noise_mix_q15 <= 16'd15073;
            pending_excitation_smooth <= 2'd3;
            pending_velocity <= 7'd110;
            retrigger_pending <= 1'b0;
            init_index <= 10'd0;
            read_pointer <= 10'd0;
                pitch_fraction<=0;
            previous_noise <= 24'sd0;
            excitation_z1 <= 24'sd0;
            excitation_z2 <= 24'sd0;
            excitation_z3 <= 24'sd0;
            excitation_z4 <= 24'sd0;
            init_filtered_noise <= 24'sd0;
            init_fm_seed <= 24'sd0;
            init_raw_excitation <= 24'sd0;
            comb_current <= 24'sd0;
            init_current_product<=0;init_shift_product<=0;
            previous_loop <= 24'sd0;
            previous_damped <= 24'sd0;
            previous_allpass <= 24'sd0;
            damped_sample <= 24'sd0;
            allpass_sample <= 24'sd0;
            current_sample <= 24'sd0;
            previous_scrape_noise <= 24'sd0;
            lfsr <= 24'hc53a91;
            init_phase <= 32'd0;
            mod1_phase <= 32'h43a6c517;
            mod2_phase <= 32'hbd8e3129;
            output_gain_q15 <= 16'd0;
            scrape_envelope_q15 <= 16'd0;
            age_samples <= 18'd0;
            dry_sample_pipe <= 24'sd0;
            sample_valid <= 1'b0;
            sample_out <= 24'sd0;
            active <= 1'b0;
        end else if (context_load) begin
            {pitch_fraction,init_current_product,init_shift_product,state, delay_len_reg, loop_gain_q15_reg, pick_offset_reg,
             scrape_start_q15_reg, damping_q23_reg, allpass_q23_reg,
             init_phase_step_reg, noise_mix_q15_reg, excitation_smooth_reg,
             velocity_reg, init_index, read_pointer, previous_noise,
             excitation_z1, excitation_z2, excitation_z3, excitation_z4,
             init_filtered_noise, init_fm_seed, init_raw_excitation,
             comb_current, previous_loop, previous_damped, previous_allpass,
             damped_sample, allpass_sample, current_sample,
             previous_scrape_noise, lfsr, init_phase, mod1_phase, mod2_phase,
             output_gain_q15, scrape_envelope_q15, age_samples, sample_out,
             sample_valid, active, dry_sample_pipe} <= context_data[1006:139];
        end else if (enable) begin
            sample_valid <= 1'b0;
            if(state==ST_PROCESS)begin
                // Static RAM-data path also serves feedback writes, with exact
                // S24*128 packing. No initialization/runtime mux at 32 RAM banks.
                init_current_product<=$signed({feedback_sample,7'd0});
                init_shift_product<=0;
            end

            if (note_on) begin
                if ((state == ST_IDLE) ||
                    (state == ST_INIT_RAW) || (state == ST_COMB_CUR) ||
                    (state == ST_COMB_SHIFT) || (state == ST_COMB_WRITE) ||
                    (state == ST_COMB_COMMIT) ||
                    (state == ST_INIT_MIX) || (state == ST_INIT_WRITE) ||
                    (state == ST_INIT_SHAPE) || (state == ST_INIT_COMMIT)) begin
                    delay_len_reg <= (requested_delay_len < 10'd16)
                        ? 10'd16 : ((requested_delay_len > MAX_DELAY)
                        ? MAX_DELAY : requested_delay_len);
                    loop_gain_q15_reg <= requested_loop_gain_q15;
                    pick_offset_reg <= (requested_pick_offset < 10'd1)
                        ? 10'd1 : ((requested_pick_offset > MAX_PICK_OFFSET)
                        ? MAX_PICK_OFFSET : requested_pick_offset);
                    scrape_start_q15_reg <= requested_scrape_q15;
                    damping_q23_reg <= requested_damping_q23;
                    allpass_q23_reg <= requested_allpass_q23;
                    init_phase_step_reg <= requested_init_phase_step;
                    noise_mix_q15_reg <= requested_noise_mix_q15;
                    excitation_smooth_reg <= requested_excitation_smooth;
                    velocity_reg <= velocity;
                    init_index <= 10'd0;
                    pitch_fraction<=0;
                    previous_noise <= 24'sd0;
                    excitation_z1 <= 24'sd0;
                    excitation_z2 <= 24'sd0;
                    excitation_z3 <= 24'sd0;
                    excitation_z4 <= 24'sd0;
                    init_filtered_noise <= 24'sd0;
                    init_fm_seed <= 24'sd0;
                    init_raw_excitation <= 24'sd0;
                    init_phase <= 32'd0;
                    mod1_phase <= {lfsr, 8'h35};
                    mod2_phase <= {lfsr[11:0], lfsr[23:12], 8'hc7};
                    lfsr <= lfsr ^ 24'h5a6c3d;
                    output_gain_q15 <= 16'd0;
                    sample_out <= 24'sd0;
                    active <= 1'b1;
                    state <= ST_INIT_RAW;
                end else begin
                    pending_delay_len <= requested_delay_len;
                    pending_loop_gain_q15 <= requested_loop_gain_q15;
                    pending_pick_offset <= requested_pick_offset;
                    pending_scrape_q15 <= requested_scrape_q15;
                    pending_damping_q23 <= requested_damping_q23;
                    pending_allpass_q23 <= requested_allpass_q23;
                    pending_init_phase_step <= requested_init_phase_step;
                    pending_noise_mix_q15 <= requested_noise_mix_q15;
                    pending_excitation_smooth <= requested_excitation_smooth;
                    pending_velocity <= velocity;
                    retrigger_pending <= 1'b1;
                end
            end else begin
                case (state)
                    ST_IDLE: begin
                        active <= 1'b0;
                        sample_out <= 24'sd0;
                        if (sample_tick) sample_valid <= 1'b1;
                    end

                    ST_INIT_RAW: begin
                        // Stage 1: the two-tap noise FIR and measured lookup end in
                        // registers, avoiding cascaded DSPs on the RAM input.
                        init_filtered_noise <= filtered_init_noise;
                        init_fm_seed <= reference_seed;
                        previous_noise <= raw_init_noise;
                        init_phase <= init_phase + init_phase_step_reg;
                        lfsr <= (lfsr_next == 24'd0) ? 24'h1 : lfsr_next;
                        state <= ST_INIT_MIX;
                    end

                    ST_INIT_MIX: begin
                        // Stage 2: combine the registered noise and FM seed.
                        init_raw_excitation <= raw_excitation;
                        state <= ST_INIT_WRITE;
                    end

                    ST_INIT_WRITE: begin
                        // Stage 3: register the five-tap result before blend.
                        excitation_z4 <= excitation_z3;
                        excitation_z3 <= excitation_z2;
                        excitation_z2 <= excitation_z1;
                        excitation_z1 <= init_raw_excitation;
                        init_filtered_noise <= fir5_excitation;
                        state <= ST_INIT_SHAPE;
                    end

                    ST_INIT_SHAPE: begin
                        // Stage 4: identical raw/smoothed blend, now bounded by
                        // registers on both sides for 50 MHz placement.
                        init_raw_excitation <= sat24(shaped_excitation);
                        state <= ST_INIT_COMMIT;
                    end

                    ST_INIT_COMMIT: begin
                        if (init_index == delay_len_reg - 1'b1) begin
                            init_index <= 10'd0;
                            state <= ST_COMB_CUR;
                        end else begin
                            init_index <= init_index + 1'b1;
                            state <= ST_INIT_RAW;
                        end
                    end

                    ST_COMB_CUR: begin
                        state <= ST_COMB_SHIFT;
                    end

                    ST_COMB_SHIFT: begin
                        comb_current <= $signed(scratch_ram_dout);
                        init_current_product <= $signed(scratch_ram_dout)*$signed({1'b0,velocity_reg});
                        state <= ST_COMB_WRITE;
                    end

                    ST_COMB_WRITE: begin
                        // The initialization excitation has already been
                        // committed to scratch RAM. Reuse its context field
                        // to register the shifted read before comb arithmetic.
                        init_raw_excitation <= $signed(scratch_ram_dout);
                        init_shift_product <= shifted_base*velocity_tripled+shifted_correction;
                        state <= ST_COMB_COMMIT;
                    end

                    ST_COMB_CALC: begin
                        comb_current <= sat24(circular_velocity_product >>> 7);
                        state <= ST_COMB_COMMIT;
                    end

                    ST_COMB_COMMIT: begin
                        if (init_index == delay_len_reg - 1'b1) begin
                            read_pointer <= 10'd0;
                pitch_fraction<=0;
                            previous_loop <= 24'sd0;
                            previous_damped <= 24'sd0;
                            previous_allpass <= 24'sd0;
                            damped_sample <= 24'sd0;
                            allpass_sample <= 24'sd0;
                            previous_scrape_noise <= 24'sd0;
                            output_gain_q15 <= 16'd0;
                            scrape_envelope_q15 <= scrape_start_q15_reg;
                            age_samples <= 18'd0;
                            dry_sample_pipe <= 24'sd0;
                            retrigger_pending <= 1'b0;
                            state <= ST_WAIT;
                        end else begin
                            init_index <= init_index + 1'b1;
                            state <= ST_COMB_SHIFT;
                        end
                    end

                    ST_WAIT: if (sample_tick) state <= ST_READ;

                    ST_READ: begin
                        current_sample <= $signed(delay_ram_dout);
                        state <= pitch_on&&pitch_fraction!=0 ? ST_PITCH_WAIT0 : ST_DAMP;
                    end
                    ST_PITCH_WAIT0:state<=ST_PITCH_WAIT1;
                    ST_PITCH_WAIT1:state<=ST_PITCH_READ;
                    ST_PITCH_READ:begin pitch_neighbor<=$signed(delay_ram_dout);state<=ST_PITCH_DELTA;end
                    ST_PITCH_DELTA:begin
                        pitch_difference<=$signed({pitch_neighbor[23],pitch_neighbor})-$signed({current_sample[23],current_sample});
                        state<=ST_PITCH_MUL;
                    end
                    ST_PITCH_MUL:begin pitch_product<=pitch_difference*$signed({1'b0,pitch_fraction});state<=ST_PITCH_APPLY;end
                    ST_PITCH_APPLY:begin
                        current_sample<=current_sample+$signed(pitch_product[41:16]);state<=ST_DAMP;
                    end

                    ST_DAMP: begin
                        damped_sample <= next_damped_sample;
                        previous_loop <= current_sample;
                        state <= ST_TAIL_DAMP;
                    end

                    ST_TAIL_DAMP: begin
                        damped_sample <= next_tail_damped_sample;
                        state <= ST_ALLPASS;
                    end

                    ST_ALLPASS: begin
                        // Same sample and gain as ST_PROCESS, one clock earlier.
                        dry_sample_pipe <= dry_sample;
                        allpass_sample <= next_allpass_sample;
                        previous_damped <= damped_sample;
                        previous_allpass <= next_allpass_sample;
                        state <= ST_PROCESS;
                    end

                    ST_PROCESS: begin
                        lfsr <= (lfsr_next == 24'd0) ? 24'h1 : lfsr_next;
                        previous_scrape_noise <= lfsr;
                        sample_valid <= 1'b1;
                        age_samples <= age_samples + 1'b1;
                        init_index <= read_pointer;
                        read_pointer<=pointer_next;
                        pitch_fraction<=pitch_on?phase_advance[15:0]:16'd0;
                        if (scrape_envelope_q15 > SCRAPE_DECAY_STEP)
                            scrape_envelope_q15 <=
                                scrape_envelope_q15 - SCRAPE_DECAY_STEP;
                        else scrape_envelope_q15 <= 16'd0;

                        if (retrigger_pending) begin
                            sample_out <= gained_sample;
                            if (output_gain_q15 <= RETRIGGER_STEP_Q15) begin
                                delay_len_reg <= (pending_delay_len < 10'd16)
                                    ? 10'd16 : ((pending_delay_len > MAX_DELAY)
                                    ? MAX_DELAY : pending_delay_len);
                                loop_gain_q15_reg <= pending_loop_gain_q15;
                                pick_offset_reg <= (pending_pick_offset < 10'd1)
                                    ? 10'd1 : ((pending_pick_offset > MAX_PICK_OFFSET)
                                    ? MAX_PICK_OFFSET : pending_pick_offset);
                                scrape_start_q15_reg <= pending_scrape_q15;
                                damping_q23_reg <= pending_damping_q23;
                                allpass_q23_reg <= pending_allpass_q23;
                                init_phase_step_reg <= pending_init_phase_step;
                                noise_mix_q15_reg <= pending_noise_mix_q15;
                                excitation_smooth_reg <= pending_excitation_smooth;
                                velocity_reg <= pending_velocity;
                                init_index <= 10'd0;
                                previous_noise <= 24'sd0;
                                excitation_z1 <= 24'sd0;
                                excitation_z2 <= 24'sd0;
                                excitation_z3 <= 24'sd0;
                                excitation_z4 <= 24'sd0;
                                init_filtered_noise <= 24'sd0;
                                init_fm_seed <= 24'sd0;
                                init_raw_excitation <= 24'sd0;
                                init_phase <= 32'd0;
                                mod1_phase <= {lfsr, 8'h35};
                                mod2_phase <=
                                    {lfsr[11:0], lfsr[23:12], 8'hc7};
                                output_gain_q15 <= 16'd0;
                                sample_out <= 24'sd0;
                                retrigger_pending <= 1'b0;
                                state <= ST_INIT_RAW;
                            end else begin
                                output_gain_q15 <=
                                    output_gain_q15 - RETRIGGER_STEP_Q15;
                                comb_current <= feedback_sample;
                                state <= ST_LOOP_COMMIT;
                            end
                        end else if (age_samples >= MAX_AGE_SAMPLES - 1'b1) begin
                            sample_out <= 24'sd0;
                            output_gain_q15 <= 16'd0;
                            active <= 1'b0;
                            state <= ST_IDLE;
                        end else begin
                            sample_out <= gained_sample;
                            comb_current <= feedback_sample;
                            if (output_gain_q15 < 16'd32767 - ATTACK_STEP_Q15)
                                output_gain_q15 <=
                                    output_gain_q15 + ATTACK_STEP_Q15;
                            else output_gain_q15 <= 16'd32767;
                            state <= ST_LOOP_COMMIT;
                        end
                    end

                    ST_LOOP_COMMIT: state <= ST_WAIT;

                    default: begin
                        state <= ST_IDLE;
                        sample_out <= 24'sd0;
                        active <= 1'b0;
                    end
                endcase
            end
        end
    end
endmodule

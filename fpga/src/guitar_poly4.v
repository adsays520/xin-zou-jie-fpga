// Four-voice wrapper around the unchanged physical-string guitar_voice core.
//
// Allocation is idle-first starting at the round-robin pointer. If all four
// voices are active, the pointed voice is retriggered through guitar_voice's
// existing de-click path. Each instance owns independent RAM and decay state.
// The mixer preserves single-note level, reserves headroom as notes are added,
// and keeps that headroom until every voice has stopped. It never raises gain
// while a tail is sounding, then saturates once at the 24-bit boundary before
// the shared guitar-body filter.
module guitar_poly4 #(
    parameter integer SAMPLE_W        = 24,
    parameter integer MAX_DELAY       = 600,
    parameter integer MAX_PICK_OFFSET = 160
)(
    input  wire                         clk,
    input  wire                         rst_n,
    input  wire                         sample_tick,
    input  wire                         note_on,
    input  wire                         force_voice0,
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
    output wire                         active
);
    reg [1:0] round_robin;
    reg [1:0] selected_voice;
    reg [2:0] headroom_count;

    wire voice0_valid;
    wire voice1_valid;
    wire voice2_valid;
    wire voice3_valid;
    wire voice0_active;
    wire voice1_active;
    wire voice2_active;
    wire voice3_active;
    wire signed [SAMPLE_W-1:0] voice0_sample;
    wire signed [SAMPLE_W-1:0] voice1_sample;
    wire signed [SAMPLE_W-1:0] voice2_sample;
    wire signed [SAMPLE_W-1:0] voice3_sample;
    wire selected_voice_active =
        (selected_voice == 2'd0) ? voice0_active :
        (selected_voice == 2'd1) ? voice1_active :
        (selected_voice == 2'd2) ? voice2_active : voice3_active;

    // Prefer an idle voice while retaining deterministic round-robin order.
    always @* begin
        if (force_voice0) begin
            // A monophonic source must retrigger one voice instead of leaving
            // up to four long physical-string tails behind it.
            selected_voice = 2'd0;
        end else begin
            selected_voice = round_robin;
            case (round_robin)
                2'd0: begin
                    if (!voice0_active) selected_voice = 2'd0;
                    else if (!voice1_active) selected_voice = 2'd1;
                    else if (!voice2_active) selected_voice = 2'd2;
                    else if (!voice3_active) selected_voice = 2'd3;
                end
                2'd1: begin
                    if (!voice1_active) selected_voice = 2'd1;
                    else if (!voice2_active) selected_voice = 2'd2;
                    else if (!voice3_active) selected_voice = 2'd3;
                    else if (!voice0_active) selected_voice = 2'd0;
                end
                2'd2: begin
                    if (!voice2_active) selected_voice = 2'd2;
                    else if (!voice3_active) selected_voice = 2'd3;
                    else if (!voice0_active) selected_voice = 2'd0;
                    else if (!voice1_active) selected_voice = 2'd1;
                end
                default: begin
                    if (!voice3_active) selected_voice = 2'd3;
                    else if (!voice0_active) selected_voice = 2'd0;
                    else if (!voice1_active) selected_voice = 2'd1;
                    else if (!voice2_active) selected_voice = 2'd2;
                end
            endcase
        end
    end

    wire [3:0] voice_note_on = note_on
        ? (4'b0001 << selected_voice) : 4'b0000;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            round_robin <= 2'd0;
            headroom_count <= 3'd1;
        end else if (note_on) begin
            round_robin <= selected_voice + 1'b1;
            // Grow headroom only if allocation really adds an idle voice.
            // A forced monophonic retrigger keeps the existing voice count.
            case (active_count + (selected_voice_active ? 3'd0 : 3'd1))
                3'd0, 3'd1: headroom_count <= 3'd1;
                3'd2: if (headroom_count < 3'd2)
                    headroom_count <= 3'd2;
                3'd3: if (headroom_count < 3'd3)
                    headroom_count <= 3'd3;
                default: headroom_count <= 3'd4;
            endcase
        end else if (active_count == 3'd0) begin
            // Gain may return to unity only in silence. Resetting here cannot
            // amplify quantisation residue at the end of a note or chord.
            headroom_count <= 3'd1;
        end
    end

    guitar_voice #(
        .SAMPLE_W(SAMPLE_W), .MAX_DELAY(MAX_DELAY),
        .MAX_PICK_OFFSET(MAX_PICK_OFFSET)
    ) u_voice0 (
        .clk(clk), .rst_n(rst_n), .sample_tick(sample_tick),
        .note_on(voice_note_on[0]),
        .requested_delay_len(requested_delay_len),
        .requested_loop_gain_q15(requested_loop_gain_q15),
        .requested_pick_offset(requested_pick_offset),
        .requested_scrape_q15(requested_scrape_q15),
        .requested_damping_q23(requested_damping_q23),
        .requested_allpass_q23(requested_allpass_q23),
        .requested_init_phase_step(requested_init_phase_step),
        .requested_noise_mix_q15(requested_noise_mix_q15),
        .requested_excitation_smooth(requested_excitation_smooth),
        .velocity(velocity), .sample_valid(voice0_valid),
        .sample_out(voice0_sample), .active(voice0_active)
    );

    guitar_voice #(
        .SAMPLE_W(SAMPLE_W), .MAX_DELAY(MAX_DELAY),
        .MAX_PICK_OFFSET(MAX_PICK_OFFSET)
    ) u_voice1 (
        .clk(clk), .rst_n(rst_n), .sample_tick(sample_tick),
        .note_on(voice_note_on[1]),
        .requested_delay_len(requested_delay_len),
        .requested_loop_gain_q15(requested_loop_gain_q15),
        .requested_pick_offset(requested_pick_offset),
        .requested_scrape_q15(requested_scrape_q15),
        .requested_damping_q23(requested_damping_q23),
        .requested_allpass_q23(requested_allpass_q23),
        .requested_init_phase_step(requested_init_phase_step),
        .requested_noise_mix_q15(requested_noise_mix_q15),
        .requested_excitation_smooth(requested_excitation_smooth),
        .velocity(velocity), .sample_valid(voice1_valid),
        .sample_out(voice1_sample), .active(voice1_active)
    );

    guitar_voice #(
        .SAMPLE_W(SAMPLE_W), .MAX_DELAY(MAX_DELAY),
        .MAX_PICK_OFFSET(MAX_PICK_OFFSET)
    ) u_voice2 (
        .clk(clk), .rst_n(rst_n), .sample_tick(sample_tick),
        .note_on(voice_note_on[2]),
        .requested_delay_len(requested_delay_len),
        .requested_loop_gain_q15(requested_loop_gain_q15),
        .requested_pick_offset(requested_pick_offset),
        .requested_scrape_q15(requested_scrape_q15),
        .requested_damping_q23(requested_damping_q23),
        .requested_allpass_q23(requested_allpass_q23),
        .requested_init_phase_step(requested_init_phase_step),
        .requested_noise_mix_q15(requested_noise_mix_q15),
        .requested_excitation_smooth(requested_excitation_smooth),
        .velocity(velocity), .sample_valid(voice2_valid),
        .sample_out(voice2_sample), .active(voice2_active)
    );

    guitar_voice #(
        .SAMPLE_W(SAMPLE_W), .MAX_DELAY(MAX_DELAY),
        .MAX_PICK_OFFSET(MAX_PICK_OFFSET)
    ) u_voice3 (
        .clk(clk), .rst_n(rst_n), .sample_tick(sample_tick),
        .note_on(voice_note_on[3]),
        .requested_delay_len(requested_delay_len),
        .requested_loop_gain_q15(requested_loop_gain_q15),
        .requested_pick_offset(requested_pick_offset),
        .requested_scrape_q15(requested_scrape_q15),
        .requested_damping_q23(requested_damping_q23),
        .requested_allpass_q23(requested_allpass_q23),
        .requested_init_phase_step(requested_init_phase_step),
        .requested_noise_mix_q15(requested_noise_mix_q15),
        .requested_excitation_smooth(requested_excitation_smooth),
        .velocity(velocity), .sample_valid(voice3_valid),
        .sample_out(voice3_sample), .active(voice3_active)
    );

    wire [2:0] active_count =
        {2'b00, voice0_active} + {2'b00, voice1_active} +
        {2'b00, voice2_active} + {2'b00, voice3_active};
    wire signed [25:0] voice0_extended =
        {{(26-SAMPLE_W){voice0_sample[SAMPLE_W-1]}}, voice0_sample};
    wire signed [25:0] voice1_extended =
        {{(26-SAMPLE_W){voice1_sample[SAMPLE_W-1]}}, voice1_sample};
    wire signed [25:0] voice2_extended =
        {{(26-SAMPLE_W){voice2_sample[SAMPLE_W-1]}}, voice2_sample};
    wire signed [25:0] voice3_extended =
        {{(26-SAMPLE_W){voice3_sample[SAMPLE_W-1]}}, voice3_sample};
    wire signed [25:0] mix_sum =
        voice0_extended + voice1_extended +
        voice2_extended + voice3_extended;

    // 21845 / 65536 is 0.333328, used only for exactly three voices.
    wire signed [42:0] mix_third_product =
        $signed(mix_sum) * 17'sd21845;
    reg signed [42:0] scaled_mix;

    always @* begin
        case (headroom_count)
            3'd1: scaled_mix = {{17{mix_sum[25]}}, mix_sum};
            3'd2: scaled_mix = $signed(mix_sum) >>> 1;
            3'd3: scaled_mix = mix_third_product >>> 16;
            default: scaled_mix = $signed(mix_sum) >>> 2;
        endcase
    end

    function signed [SAMPLE_W-1:0] sat_sample;
        input signed [42:0] value;
        begin
            if (value > 43'sd8388607)
                sat_sample = 24'sh7fffff;
            else if (value < -43'sd8388608)
                sat_sample = 24'sh800000;
            else
                sat_sample = value[SAMPLE_W-1:0];
        end
    endfunction

    assign active = (active_count != 3'd0);
    // Idle cores report a zero at sample_tick, while playing cores report a
    // few system clocks later. Gate by active so the body filter sees exactly
    // one mixed sample per audio frame. Continue feeding zero after all four
    // voices stop so the shared body resonances can decay naturally.
    wire playing_sample_valid =
        (voice0_valid && voice0_active) ||
        (voice1_valid && voice1_active) ||
        (voice2_valid && voice2_active) ||
        (voice3_valid && voice3_active);
    wire mixed_sample_valid = active ? playing_sample_valid : voice0_valid;

    // Register the mix before the shared body model. This breaks the long
    // voice-sum/body-filter combinational path and adds only one 50 MHz cycle
    // (20 ns), far below one 48 kHz audio-sample interval.
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sample_valid <= 1'b0;
            sample_out <= {SAMPLE_W{1'b0}};
        end else begin
            sample_valid <= mixed_sample_valid;
            if (mixed_sample_valid)
                sample_out <= sat_sample(scaled_mix);
        end
    end
endmodule

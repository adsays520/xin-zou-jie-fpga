// Four independent instances of the unchanged physical-string voice.
//
// This module only allocates Note-On events. It does not mix samples and does
// not contain timbre processing. In monophonic mode every event retriggers
// voice 0; in polyphonic mode an idle-first round-robin allocator is used.
module guitar_voice_bank4 #(
    parameter integer SAMPLE_W        = 24,
    parameter integer MAX_DELAY       = 600,
    parameter integer MAX_PICK_OFFSET = 160,
    parameter integer ENABLE_OUTPUT_POLISH = 1
)(
    input  wire                         clk,
    input  wire                         rst_n,
    input  wire                         clear,
    input  wire                         poly_mode,
    input  wire                         sample_tick,
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
    input  wire [2:0]                   requested_string_sel,
    input  wire [6:0]                   velocity,
    output wire                         voice0_valid,
    output wire                         voice0_active,
    output wire signed [SAMPLE_W-1:0]   voice0_sample,
    output wire                         voice1_valid,
    output wire                         voice1_active,
    output wire signed [SAMPLE_W-1:0]   voice1_sample,
    output wire                         voice2_valid,
    output wire                         voice2_active,
    output wire signed [SAMPLE_W-1:0]   voice2_sample,
    output wire                         voice3_valid,
    output wire                         voice3_active,
    output wire signed [SAMPLE_W-1:0]   voice3_sample,
    output wire                         any_active
);
    wire bank_rst_n = rst_n && !clear;
    reg [1:0] round_robin;
    reg [1:0] selected_voice;

    wire                         voice0_raw_valid;
    wire                         voice1_raw_valid;
    wire                         voice2_raw_valid;
    wire                         voice3_raw_valid;
    wire signed [SAMPLE_W-1:0]   voice0_raw_sample;
    wire signed [SAMPLE_W-1:0]   voice1_raw_sample;
    wire signed [SAMPLE_W-1:0]   voice2_raw_sample;
    wire signed [SAMPLE_W-1:0]   voice3_raw_sample;

    always @* begin
        if (!poly_mode) begin
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

    always @(posedge clk or negedge bank_rst_n) begin
        if (!bank_rst_n)
            round_robin <= 2'd0;
        else if (note_on)
            round_robin <= selected_voice + 1'b1;
    end

    guitar_voice #(
        .SAMPLE_W(SAMPLE_W), .MAX_DELAY(MAX_DELAY),
        .MAX_PICK_OFFSET(MAX_PICK_OFFSET)
    ) u_voice0 (
        .clk(clk), .rst_n(bank_rst_n), .sample_tick(sample_tick),
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
        .velocity(velocity), .sample_valid(voice0_raw_valid),
        .sample_out(voice0_raw_sample), .active(voice0_active)
    );

    guitar_voice #(
        .SAMPLE_W(SAMPLE_W), .MAX_DELAY(MAX_DELAY),
        .MAX_PICK_OFFSET(MAX_PICK_OFFSET)
    ) u_voice1 (
        .clk(clk), .rst_n(bank_rst_n), .sample_tick(sample_tick),
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
        .velocity(velocity), .sample_valid(voice1_raw_valid),
        .sample_out(voice1_raw_sample), .active(voice1_active)
    );

    guitar_voice #(
        .SAMPLE_W(SAMPLE_W), .MAX_DELAY(MAX_DELAY),
        .MAX_PICK_OFFSET(MAX_PICK_OFFSET)
    ) u_voice2 (
        .clk(clk), .rst_n(bank_rst_n), .sample_tick(sample_tick),
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
        .velocity(velocity), .sample_valid(voice2_raw_valid),
        .sample_out(voice2_raw_sample), .active(voice2_active)
    );

    guitar_voice #(
        .SAMPLE_W(SAMPLE_W), .MAX_DELAY(MAX_DELAY),
        .MAX_PICK_OFFSET(MAX_PICK_OFFSET)
    ) u_voice3 (
        .clk(clk), .rst_n(bank_rst_n), .sample_tick(sample_tick),
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
        .velocity(velocity), .sample_valid(voice3_raw_valid),
        .sample_out(voice3_raw_sample), .active(voice3_active)
    );

    generate
        if (ENABLE_OUTPUT_POLISH != 0) begin : g_output_polish
            guitar_output_polish u_polish0 (
                .clk(clk), .rst_n(bank_rst_n), .note_on(voice_note_on[0]),
                .string_sel(requested_string_sel),
                .sample_valid(voice0_raw_valid), .sample_in(voice0_raw_sample),
                .output_valid(voice0_valid), .sample_out(voice0_sample)
            );
            guitar_output_polish u_polish1 (
                .clk(clk), .rst_n(bank_rst_n), .note_on(voice_note_on[1]),
                .string_sel(requested_string_sel),
                .sample_valid(voice1_raw_valid), .sample_in(voice1_raw_sample),
                .output_valid(voice1_valid), .sample_out(voice1_sample)
            );
            guitar_output_polish u_polish2 (
                .clk(clk), .rst_n(bank_rst_n), .note_on(voice_note_on[2]),
                .string_sel(requested_string_sel),
                .sample_valid(voice2_raw_valid), .sample_in(voice2_raw_sample),
                .output_valid(voice2_valid), .sample_out(voice2_sample)
            );
            guitar_output_polish u_polish3 (
                .clk(clk), .rst_n(bank_rst_n), .note_on(voice_note_on[3]),
                .string_sel(requested_string_sel),
                .sample_valid(voice3_raw_valid), .sample_in(voice3_raw_sample),
                .output_valid(voice3_valid), .sample_out(voice3_sample)
            );
        end else begin : g_output_bypass
            assign voice0_valid = voice0_raw_valid;
            assign voice1_valid = voice1_raw_valid;
            assign voice2_valid = voice2_raw_valid;
            assign voice3_valid = voice3_raw_valid;
            assign voice0_sample = voice0_raw_sample;
            assign voice1_sample = voice1_raw_sample;
            assign voice2_sample = voice2_raw_sample;
            assign voice3_sample = voice3_raw_sample;
        end
    endgenerate

    assign any_active = voice0_active || voice1_active ||
                        voice2_active || voice3_active;
endmodule

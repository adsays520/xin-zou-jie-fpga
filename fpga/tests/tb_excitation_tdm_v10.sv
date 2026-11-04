`timescale 1ns/1ps
module tb_excitation_tdm_v10;
    reg clk = 0;
    always #10 clk = ~clk;
    GSR GSR(.GSRI(1'b1));
    reg rst_n = 0, sample_tick = 0, note_on = 0, pitch_enabled = 0;
    reg [23:0] pitch_ratio = 24'd1048576;
    reg [2:0] string_sel = 0;
    reg [4:0] fret = 0;
    reg [6:0] velocity = 110;
    wire [9:0] delay_len, pick_offset;
    wire [15:0] loop_gain, scrape, noise_mix;
    wire [23:0] damping, allpass;
    wire [31:0] phase_step;
    wire [1:0] smooth;
    wire candidate_valid, reference_valid, candidate_active, reference_active;
    wire signed [23:0] candidate_sample, reference_sample;
    wire [5:0] candidate_count, reference_count;
    wire [31:0] candidate_occupied, reference_occupied;
    wire [31:0] candidate_dropped, reference_dropped, candidate_stolen, reference_stolen;
    wire candidate_deadline, reference_deadline, candidate_limited, reference_limited;
    integer frame, pcm_checks = 0, context_checks = 0, nonzero_frames = 0;
    integer max_voices = 0, notes = 0;

    guitar_note_params params(
        .string_sel(string_sel), .fret_sel(fret), .delay_len(delay_len),
        .loop_gain_q15(loop_gain), .pick_offset(pick_offset), .scrape_q15(scrape),
        .damping_q23(damping), .allpass_q23(allpass), .init_phase_step(phase_step),
        .noise_mix_q15(noise_mix), .excitation_smooth(smooth)
    );

`define TDM_INSTANCE(module_name, instance_name, prefix) \
    module_name #(.ENABLE_TAIL_HF_DAMPING(1)) instance_name( \
        .clk(clk), .rst_n(rst_n), .sample_tick(sample_tick), .note_on(note_on), .poly_mode(1'b1), \
        .pitch_enabled(pitch_enabled), .pitch_ratio_q20(pitch_ratio), \
        .requested_delay_len(delay_len), .requested_pick_offset(pick_offset), \
        .requested_loop_gain_q15(loop_gain), .requested_scrape_q15(scrape), \
        .requested_damping_q23(damping), .requested_allpass_q23(allpass), \
        .requested_init_phase_step(phase_step), .requested_noise_mix_q15(noise_mix), \
        .requested_excitation_smooth(smooth), .requested_string_sel(string_sel), .velocity(velocity), \
        .requested_custom_envelope(1'b0), .envelope_ram_we(1'b0), \
        .envelope_ram_addr(12'd0), .envelope_ram_data(16'd0), \
        .sample_valid(prefix``_valid), .sample_out(prefix``_sample), .active(prefix``_active), \
        .active_count(prefix``_count), .occupied(prefix``_occupied), .dropped_events(prefix``_dropped), \
        .stolen_events(prefix``_stolen), .deadline_miss(prefix``_deadline), .limited(prefix``_limited) \
    );
    `TDM_INSTANCE(guitar_poly32_tdm, dut, candidate)
    `TDM_INSTANCE(guitar_poly32_tdm_v9_reference, reference, reference)
`undef TDM_INSTANCE

    always @(negedge clk) if (rst_n) begin
        if ({candidate_valid, candidate_active, candidate_count, candidate_occupied,
                candidate_dropped, candidate_stolen, candidate_deadline, candidate_limited}
                !== {reference_valid, reference_active, reference_count, reference_occupied,
                reference_dropped, reference_stolen, reference_deadline, reference_limited})
            $fatal(1, "TDM schedule/allocation mismatch frame=%0d", frame);
        if (candidate_deadline || candidate_dropped != 0)
            $fatal(1, "TDM deadline or queue fault");
        if (candidate_count > max_voices) max_voices = candidate_count;
        if (dut.core_save) begin
            if (dut.u_core.u_context_ram.din !== reference.u_core.u_context_ram.din)
                $fatal(1, "1007-bit saved context mismatch frame=%0d slot=%0d", frame, dut.slot);
            context_checks = context_checks + 1;
        end
        if (candidate_valid) begin
            if (candidate_sample !== reference_sample || ^candidate_sample === 1'bx)
                $fatal(1, "TDM PCM mismatch frame=%0d candidate=%0d reference=%0d",
                    frame, candidate_sample, reference_sample);
            pcm_checks = pcm_checks + 1;
            if (candidate_sample != 0) nonzero_frames = nonzero_frames + 1;
        end
    end

    initial begin
        repeat (12) @(negedge clk);
        rst_n = 1;
        repeat (12) @(negedge clk);
        for (frame = 0; frame < 920; frame = frame + 1) begin
            string_sel = frame % 6;
            fret = (frame * 7) % 21;
            velocity = 70 + frame % 58;
            pitch_enabled = frame >= 300;
            pitch_ratio = frame < 600 ? 24'd1176987 : 24'd934175;
            note_on = frame < 32 || (frame >= 240 && frame < 248);
            if (note_on) notes = notes + 1;
            sample_tick = 1;
            @(negedge clk);
            sample_tick = 0;
            note_on = 0;
            repeat (1040) @(negedge clk);
        end
        if (max_voices != 32 || notes != 40 || pcm_checks != 920
                || context_checks < 29000 || nonzero_frames < 500 || candidate_stolen < 8)
            $fatal(1, "TDM insufficient coverage voices=%0d notes=%0d PCM=%0d contexts=%0d nonzero=%0d stolen=%0d",
                max_voices, notes, pcm_checks, context_checks, nonzero_frames, candidate_stolen);
        $display("PASS EXCITATION TDM V10: %0d PCM frames, %0d full contexts, 32 voices, 40 notes, %0d steals, pitch up/down; bit-exact versus frozen v9",
            pcm_checks, context_checks, candidate_stolen);
        $finish;
    end
    initial begin
        #25000000;
        $fatal(1, "TDM timeout");
    end
endmodule

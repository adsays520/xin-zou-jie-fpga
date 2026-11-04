`timescale 1ns/1ps
module tb_excitation_math_v10;
    reg clk = 0;
    always #10 clk = ~clk;
    GSR GSR(.GSRI(1'b1));
    reg signed [23:0] raw_value = 0;
    reg signed [23:0] first_value = 0;
    reg signed [23:0] second_value = 0;
    reg signed [23:0] third_value = 0;
    reg signed [23:0] fourth_value = 0;
    reg signed [23:0] corners [0:6];
    integer checks = 0;
    integer raw_index, first_index, second_index, third_index, fourth_index, trial;
    reg [31:0] random_state = 32'h12345678;
    longint signed expected_sum;
    longint signed expected_sample;

    guitar_voice_tdm_core dut(
        .clk(clk), .rst_n(1'b0), .enable(1'b0),
        .context_load(1'b0), .context_save(1'b0), .context_new(1'b0),
        .context_id(5'd0), .context_prefetch_id(5'd0), .auxiliary_context_in(139'd0),
        .sample_tick(1'b0), .pitch_enabled(1'b0), .pitch_ratio_q20(24'd1048576),
        .note_on(1'b0), .requested_delay_len(10'd2), .requested_loop_gain_q15(16'd0),
        .requested_pick_offset(10'd0), .requested_scrape_q15(16'd0),
        .requested_damping_q23(24'd0), .requested_allpass_q23(24'd0),
        .requested_init_phase_step(32'd0), .requested_noise_mix_q15(16'd0),
        .requested_excitation_smooth(2'd0), .velocity(7'd0)
    );

    task next_random;
        begin
            random_state = random_state ^ (random_state << 13);
            random_state = random_state ^ (random_state >> 17);
            random_state = random_state ^ (random_state << 5);
        end
    endtask

    task check_value;
        begin
            #1;
            expected_sum = raw_value;
            expected_sum = expected_sum + 4 * longint'(first_value)
                + 6 * longint'(second_value) + 4 * longint'(third_value)
                + longint'(fourth_value);
            expected_sample = expected_sum >>> 4;
            if (expected_sample < -8388608 || expected_sample > 8388607)
                $fatal(1, "convex FIR bound violated");
            if ($signed(dut.fir5_sum) !== expected_sum
                    || $signed(dut.fir5_excitation) !== expected_sample)
                $fatal(1, "balanced FIR mismatch check=%0d got=%0d expected=%0d", checks,
                    $signed(dut.fir5_excitation), expected_sample);
            checks = checks + 1;
        end
    endtask

    initial begin
        force dut.init_raw_excitation = raw_value;
        force dut.excitation_z1 = first_value;
        force dut.excitation_z2 = second_value;
        force dut.excitation_z3 = third_value;
        force dut.excitation_z4 = fourth_value;
        corners[0] = -8388608;
        corners[1] = -8388607;
        corners[2] = -1;
        corners[3] = 0;
        corners[4] = 1;
        corners[5] = 8388606;
        corners[6] = 8388607;
        for (raw_index = 0; raw_index < 7; raw_index = raw_index + 1)
            for (first_index = 0; first_index < 7; first_index = first_index + 1)
                for (second_index = 0; second_index < 7; second_index = second_index + 1)
                    for (third_index = 0; third_index < 7; third_index = third_index + 1)
                        for (fourth_index = 0; fourth_index < 7; fourth_index = fourth_index + 1) begin
                            raw_value = corners[raw_index];
                            first_value = corners[first_index];
                            second_value = corners[second_index];
                            third_value = corners[third_index];
                            fourth_value = corners[fourth_index];
                            check_value;
                        end
        for (trial = 0; trial < 100000; trial = trial + 1) begin
            next_random; raw_value = random_state[23:0];
            next_random; first_value = random_state[23:0];
            next_random; second_value = random_state[23:0];
            next_random; third_value = random_state[23:0];
            next_random; fourth_value = random_state[23:0];
            check_value;
        end
        $display("PASS EXCITATION MATH V10: %0d signed 24-bit cases; exact sum and floor divide; no saturation needed", checks);
        $finish;
    end
endmodule

`timescale 1ns/1ps
// Simulation only. It writes signed 24-bit post-body E2 samples as text; this file is
// deliberately not included in the Gowin project file.
module tb_guitar_audio_top;
    reg clk = 1'b0;
    reg rst = 1'b1;
    reg key_next_n = 1'b1;
    reg key_pluck_n = 1'b1;
    wire HP_BCK, HP_WS, HP_DIN, PA_EN;
    wire led_1_n, led_2_n, led_3_n, led_4_n, led_5_n, led_6_n;
    integer pcm_file;
    integer sample_count;

    guitar_audio_top dut (
        .clk(clk), .rst(rst), .key_next_n(key_next_n),
        .key_pluck_n(key_pluck_n), .HP_BCK(HP_BCK), .HP_WS(HP_WS),
        .HP_DIN(HP_DIN), .PA_EN(PA_EN), .led_1_n(led_1_n),
        .led_2_n(led_2_n), .led_3_n(led_3_n), .led_4_n(led_4_n),
        .led_5_n(led_5_n), .led_6_n(led_6_n)
    );

    always #10 clk = ~clk; // 50 MHz

    initial begin
        pcm_file = $fopen("guitar_c4_pcm.txt", "w");
        sample_count = 0;
        #200;
        rst = 1'b0;        // release S1: top generates the first low-E pluck
        #40000000;         // 40 ms, enough to see > 1,800 48 kHz samples
        $fclose(pcm_file);
        $display("Captured %0d PCM samples", sample_count);
        $finish;
    end

    always @(posedge clk) begin
        if (dut.body_sample_valid) begin
            $fwrite(pcm_file, "%0d\n", $signed(dut.body_sample_q23));
            sample_count = sample_count + 1;
        end
    end
endmodule

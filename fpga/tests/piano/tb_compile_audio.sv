module tb_compile_audio; GSR GSR(.GSRI(1'b1)); guitar_audio_top dut(.clk(1'b0),.rst(1'b1),.key_next_n(1'b1),.key_pluck_n(1'b1),.uart_rx_i(1'b1)); endmodule

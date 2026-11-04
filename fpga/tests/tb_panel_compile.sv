module tb_panel_compile;
 GSR GSR(1'b1);
 guitar_audio_top dut(.clk(1'b0),.rst(1'b1),.key_next_n(1'b1),.key_pluck_n(1'b1),.uart_rx_i(1'b1),
 .sw1_enc_a(1'b1),.sw1_enc_b(1'b1),.sw2_enc_a(1'b1),.sw2_enc_b(1'b1),
 .sw1_up_n(1'b1),.sw1_right_n(1'b1),.sw1_down_n(1'b1),.sw1_left_n(1'b1));
endmodule

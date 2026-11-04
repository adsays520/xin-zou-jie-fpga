// Smooth commanded Q20 phase rate every audio frame. Pitch processing is
// inside each original guitar voice, preserving its excitation and envelope.
module guitar_pitch_shift(input wire clk,rst_n,sample_tick,
 input wire [23:0] ratio_q20,output reg [23:0] ratio_smoothed);
 wire signed [24:0] delta=$signed({1'b0,ratio_q20})-$signed({1'b0,ratio_smoothed});
 wire signed [24:0] step=(delta>0&&delta<64)?25'sd1:(delta<0&&delta>-64)?-25'sd1:(delta>>>6);
 always @(posedge clk or negedge rst_n)
  if(!rst_n)ratio_smoothed<=24'd1048576;
  else if(sample_tick)ratio_smoothed<=ratio_smoothed+step;
endmodule

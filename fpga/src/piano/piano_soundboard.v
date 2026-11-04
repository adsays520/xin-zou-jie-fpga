// SMS parameters already include soundboard radiation. Unity stereo output.
module piano_soundboard(input wire clk,rst_n,sample_valid,
 input wire signed [23:0] sample_in,input wire [2:0] pedal_level,
 output reg output_valid,output reg signed [23:0] sample_out_l,sample_out_r);
 always @(posedge clk or negedge rst_n)begin
  if(!rst_n)begin output_valid<=0;sample_out_l<=0;sample_out_r<=0;end
  else begin output_valid<=sample_valid;
   if(sample_valid)begin sample_out_l<=sample_in;sample_out_r<=sample_in;end
  end
 end
endmodule

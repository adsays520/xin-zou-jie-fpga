`timescale 1ns/1ps
module tb_audio_tick_v13;
 reg clk=0,rst_n=0;
 always #10 clk=~clk;
 reg [15:0] left=0,right=0;
 wire req,tick,bck,ws,din,ref_req,ref_tick,ref_bck,ref_ws,ref_din;
 integer cycles,scenario,checks=0,frames=0;
 reg [31:0] prng_state=32'habc98765;
 audio_drive dut(clk,rst_n,left,right,req,tick,bck,ws,din);
 audio_drive_v12_reference reference(clk,rst_n,left,right,ref_req,ref_tick,ref_bck,ref_ws,ref_din);
 initial begin
  for(scenario=0;scenario<8;scenario=scenario+1)begin
   @(negedge clk);rst_n=0;repeat(scenario+1)@(negedge clk);rst_n=1;
   for(cycles=0;cycles<500000;cycles=cycles+1)begin
    @(negedge clk);
    if({req,tick,bck,ws,din}!=={ref_req,ref_tick,ref_bck,ref_ws,ref_din})
     $fatal(1,"sample tick/I2S cycle mismatch scenario=%0d cycle=%0d",scenario,cycles);
    prng_state=(prng_state<<1)^({32{prng_state[31]}}&32'h04c11db7);
    left=prng_state[15:0];right=prng_state[31:16];
    checks=checks+1;
    if(tick)frames=frames+1;
   end
  end
  if(frames<3800)$fatal(1,"insufficient frame ticks");
  $display("PASS V13 audio: %0d clock-exact sample enables and I2S comparisons, %0d frames, eight asynchronous resets",checks,frames);
  $finish;
 end
 initial begin #100000000;$fatal(1,"audio tick equivalence timeout");end
endmodule

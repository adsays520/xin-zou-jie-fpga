`timescale 1ns/1ps
module tb_drums_gate;
 reg clk=0;always #10 clk=~clk;
 GSR GSR(.GSRI(1'b1));
 reg rst_n=0,tick=0,hit=0,panic=0;reg [3:0] voice=0;reg [1:0] kit=0;
 wire rv,gv,rd,gd,rc,gc;wire signed [23:0] rl,rr,gl,gr;
 drum_synth_rtl rtl(.clk(clk),.rst_n(rst_n),.sample_tick(tick),.panic(panic),.hit(hit),.hit_voice(voice),.hit_velocity(7'd110),.hit2(1'b0),.hit2_voice(4'd0),.hit2_velocity(7'd0),.kit(kit),.level_we(1'b0),.level_voice(4'd0),.level_value(7'd0),.sample_valid(rv),.sample_l(rl),.sample_r(rr),.deadline_miss(rd),.clipped(rc));
 drum_synth gate(.clk(clk),.rst_n(rst_n),.sample_tick(tick),.panic(panic),.hit(hit),.hit_voice(voice),.hit_velocity(7'd110),.hit2(1'b0),.hit2_voice(4'd0),.hit2_velocity(7'd0),.kit(kit),.level_we(1'b0),.level_voice(4'd0),.level_value(7'd0),.sample_valid(gv),.sample_l(gl),.sample_r(gr),.deadline_miss(gd),.clipped(gc));
 integer k,v,n,cycles,frames=0;
 always @(negedge clk)if(rst_n)begin
  if({rv,rd,rc,rl,rr}!=={gv,gd,gc,gl,gr})$fatal(1,"gate mismatch k=%0d v=%0d n=%0d RTL=%h/%h gate=%h/%h valid=%b/%b",k,v,n,rl,rr,gl,gr,rv,gv);
 end
 initial begin
  force GSR.GSRI=0;repeat(5)@(negedge clk);force GSR.GSRI=1;
  for(k=0;k<3;k=k+1)for(v=0;v<12;v=v+1)begin
   rst_n=0;repeat(5)@(negedge clk);kit=k;voice=v;rst_n=1;
   repeat(3)@(negedge clk);hit=1;@(negedge clk);hit=0;
   for(n=0;n<(v==0?192:64);n=n+1)begin
    tick=1;@(negedge clk);tick=0;cycles=1;
    while(!rv)begin @(negedge clk);cycles=cycles+1;if(cycles>1041)$fatal(1,"deadline");end
    repeat(4)@(negedge clk);frames=frames+1;
   end
   $display("PASS gate kit=%0d voice=%0d",k,v);
  end
  $display("PASS post-synthesis drums: 3 kits x 12 voices, %0d frames; every cycle/output bit identical",frames);$finish;
 end
endmodule

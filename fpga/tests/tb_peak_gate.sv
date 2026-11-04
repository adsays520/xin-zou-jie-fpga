`timescale 1ns/1ps
module tb_peak_gate;
 reg clk=0;always #10 clk=~clk;reg global_reset_n=0;GSR GSR(.GSRI(global_reset_n));
 reg rst_n=0,start=0,clear=0;reg signed[31:0]l=0,r=0;
 wire rv,gv,rhit,ghit;wire signed[23:0]rl,rr,gl,gr;integer n,c;
 performance_peak_control_rtl rtl(.clk(clk),.rst_n(rst_n),.start(start),.clear(clear),.sample_l(l),.sample_r(r),.valid(rv),.safety_hit(rhit),.out_l(rl),.out_r(rr));
 performance_peak_control gate(.clk(clk),.rst_n(rst_n),.start(start),.clear(clear),.sample_l(l),.sample_r(r),.valid(gv),.safety_hit(ghit),.out_l(gl),.out_r(gr));
 always@(negedge clk)if(rst_n&&{rv,rhit,rl,rr}!=={gv,ghit,gl,gr})$fatal(1,"peak gate mismatch n=%0d RTL=%h/%h gate=%h/%h",n,rl,rr,gl,gr);
 initial begin global_reset_n=0;repeat(5)@(negedge clk);global_reset_n=1;rst_n=1;
  for(n=0;n<512;n=n+1)begin
   l=n<64?(n%11-5)*100000:(n%11-5)*3000000;r=n<64?(n%7-3)*100000:(n%7-3)*3000000;
   if(n==256)begin clear=1;@(negedge clk);clear=0;end
   start=1;@(negedge clk);start=0;c=0;
   while(!rv)begin @(negedge clk);c=c+1;if(c>100)$fatal(1,"peak timeout");end
   repeat(4)@(negedge clk);
  end
  $display("PASS post-synthesis peak: stereo unity/limiting/clear, 512 frames, every cycle/output bit identical");$finish;
 end
endmodule

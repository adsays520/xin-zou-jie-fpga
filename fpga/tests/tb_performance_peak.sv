`timescale 1ns/1ps
module tb_performance_peak;
 reg clk=0;always #10 clk=~clk;
 reg rst_n=0,start=0,clear=0;
 reg signed [31:0] l=0,r=0;wire signed [23:0] ol,orr;wire valid,safety;
 performance_peak_control dut(.clk(clk),.rst_n(rst_n),.start(start),.clear(clear),.sample_l(l),.sample_r(r),.valid(valid),.safety_hit(safety),.out_l(ol),.out_r(orr));
 integer n,cycles;reg signed [31:0] expected[0:255];
 task frame;begin start=1;@(negedge clk);start=0;cycles=1;
  while(!valid)begin @(negedge clk);cycles=cycles+1;if(cycles>60)$fatal(1,"deadline");end
  if(safety||^ol===1'bx||^orr===1'bx)$fatal(1,"safety clamp or X at n=%0d",n);
  repeat(3)@(negedge clk);
 end endtask
 task reset_history;begin clear=1;@(negedge clk);clear=0;end endtask
 initial begin
  repeat(5)@(negedge clk);rst_n=1;
  for(n=0;n<256;n=n+1)begin l=(n%2?-1:1)*n*20000;r=l/2;expected[n]=l;frame();
   if(n>=32&&(ol!=expected[n-32]||orr!=expected[n-32]/2))$fatal(1,"unity/delay n=%0d",n);
  end
  reset_history();
  for(n=0;n<2048;n=n+1)begin l=n%2?-16777216:16777214;r=l/2;frame();
   if(n>=32)begin
    if(ol>7600000||ol< -7600000)$fatal(1,"peak range");
    if(ol-2*orr>2||ol-2*orr< -2)$fatal(1,"stereo image");
   end
  end
  reset_history();
  for(n=0;n<512;n=n+1)begin l=n%64==0?16777214:0;r=-l;frame();
   if(ol+orr>1||ol+orr< -1)$fatal(1,"sign symmetry");
  end
  reset_history();l=0;r=0;frame();if(ol||orr)$fatal(1,"clear");
  $display("PASS peak control: unity, 32-frame delay, stereo, full-scale sums, impulses, clear; no safety clipping");$finish;
 end
endmodule

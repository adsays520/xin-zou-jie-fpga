`timescale 1ns/1ps
module tb_panel_pitch;
 reg clk=0,rst_n=0,cw=0,ccw=0,clear=0;always #10 clk=~clk;
 wire [23:0]ratio,inverse;wire active;wire[1:0]gesture;wire[4:0]steps;wire signed[12:0]cents;
 panel_pitch #(.CLOCK_HZ(1000)) dut(.clk(clk),.rst_n(rst_n),.slide_step(cw),.vibrato_step(ccw),.clear(clear),
 .slide_semi(8'd1),.vibrato_cents(8'd5),.vibrato_hz(8'd5),.return_10ms(8'd25),
 .ratio_q20(ratio),.inverse_q20(inverse),.active(active),.gesture(gesture),.steps(steps),.cents(cents));
 task ticks;input integer n;begin repeat(n)@(negedge clk);end endtask
 task click;input direction;begin if(direction)cw=1;else ccw=1;ticks(1);cw=0;ccw=0;ticks(20);end endtask
 integer i,maximum;reg[47:0] product;
 initial begin
  ticks(8);rst_n=1;ticks(5);if(ratio!=1048576||inverse!=1048576)$fatal(1,"unity startup");
  click(1);click(1);ticks(100);
  if(steps!=2||gesture!=1||cents<199||cents>200)$fatal(1,"2 detents must yield +2 semitones: %d",cents);
  if(ratio<1176000||ratio>1177500)$fatal(1,"slide ratio");
  product=ratio*inverse;if(product<1099500000000||product>1099520000000)$fatal(1,"reciprocal pair");
  click(0);if(gesture!=2||steps!=1)$fatal(1,"direction change must replace gesture");
  click(0);maximum=0;
  for(i=0;i<180;i=i+1)begin ticks(1);if(i>40&&cents>maximum)maximum=cents;if(cents>12||cents< -12)$fatal(1,"vibrato depth bound %d",cents);end
  if(maximum<5)$fatal(1,"vibrato missing");
  ticks(650);if(cents!=0||ratio!=1048576||inverse!=1048576||active)$fatal(1,"idle must return exactly to original pitch");
  $display("PASS panel pitch: per-detent +semitones/depth, direction replacement, reciprocal ratios, sinusoidal vibrato, automatic exact return");$finish;
 end
endmodule

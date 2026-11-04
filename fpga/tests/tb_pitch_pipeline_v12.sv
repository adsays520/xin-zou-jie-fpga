`timescale 1ns/1ps
module tb_pitch_pipeline_v12;
 reg clk=0,rst_n=0,slide_step=0,vibrato_step=0,clear=0;
 always #10 clk=~clk;
 reg [7:0] slide_semi=1,vibrato_cents=5,vibrato_hz=5,return_10ms=25;
 wire [23:0] ratio,inverse,reference_ratio,reference_inverse;
 wire active,reference_active;
 wire [1:0] gesture,reference_gesture;
 wire [4:0] steps,reference_steps;
 wire signed [12:0] cents,reference_cents;
 reg signed [20:0] target_delay_0,target_delay_1;
 reg signed [20:0] mathematical_target_q;
 integer cycles=0,checks=0,scenario,detent,overflow_checks=0;
 panel_pitch #(.CLOCK_HZ(100000)) dut(clk,rst_n,slide_step,vibrato_step,clear,
  slide_semi,vibrato_cents,vibrato_hz,return_10ms,ratio,inverse,active,gesture,steps,cents);
 panel_pitch_v11_reference #(.CLOCK_HZ(100000)) reference(clk,rst_n,slide_step,vibrato_step,clear,
  slide_semi,vibrato_cents,vibrato_hz,return_10ms,reference_ratio,reference_inverse,reference_active,
  reference_gesture,reference_steps,reference_cents);
 always @(posedge clk)begin
  if(reference_gesture==1)begin
   mathematical_target_q<=reference_steps*slide_semi>12?307200:reference_steps*slide_semi*25600;
   if(reference_steps*slide_semi*25600>1048575)overflow_checks=overflow_checks+1;
  end else mathematical_target_q<=reference.target;
 end
 always @(negedge clk)begin
  cycles=cycles+1;
  if(cycles>12&&rst_n)begin
   if(dut.target_q!==target_delay_1)$fatal(1,"pitch target pipeline mismatch cycle=%0d actual=%0d expected=%0d",cycles,dut.target_q,target_delay_1);
   if(gesture!==reference_gesture||steps!==reference_steps)$fatal(1,"gesture semantics changed");
   if(cents>1200||cents< -101)$fatal(1,"pitch bound");
   checks=checks+1;
  end
  target_delay_1=target_delay_0;
  target_delay_0=mathematical_target_q;
 end
 task click(input direction);
  begin
   @(posedge clk);#1;slide_step=direction;vibrato_step=!direction;
   @(posedge clk);#1;slide_step=0;vibrato_step=0;
   repeat(1000)@(posedge clk);
  end
 endtask
 initial begin
  repeat(10)@(posedge clk);#1;rst_n=1;
  for(scenario=0;scenario<4;scenario=scenario+1)begin
   slide_semi=scenario[0]?4:1;vibrato_cents=scenario[1]?20:1;
   vibrato_hz=scenario[0]?10:1;return_10ms=scenario[1]?50:10;
   for(detent=0;detent<15;detent=detent+1)click(1);
   for(detent=0;detent<23;detent=detent+1)click(0);
   repeat(90000)@(posedge clk);
   #1;
   if(active||cents!=0||ratio!=1048576||inverse!=1048576)$fatal(1,"pitch did not return to exact unity");
   click(1);#1;clear=1;@(posedge clk);#1;clear=0;
   repeat(30000)@(posedge clk);
  end
  if(overflow_checks==0)$fatal(1,"maximum-slide signed overflow was not exercised");
  $display("PASS V12 pitch: %0d mathematical targets, %0d legacy-overflow corrections, same gestures, maximum detents and unity return",checks,overflow_checks);
  $finish;
 end
 initial begin #20000000;$fatal(1,"pitch pipeline timeout");end
endmodule

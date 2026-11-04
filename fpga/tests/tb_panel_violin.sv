`timescale 1ns/1ps
module tb_panel_violin;
 reg clk=0,rst=0,tick=0,cmd=0;always #10 clk=~clk;
 reg[23:0] inv=1048576;wire r0,r1,v0,v1,miss0,miss1,ov0,ov1,err0,err1;
 wire signed[23:0]s0,s1;wire[15:0]cycles0,cycles1;
 violin_core base(.clk(clk),.rst_n(rst),.sample_tick(tick),.panel_inverse_q20(24'd1048576),.command_valid(cmd),.command_on(1'b1),.command_legato(1'b0),.command_force_off(1'b0),.command_key(7'd69),.command_velocity(7'd110),.ready_o(r0),.sample_o(s0),.sample_valid_o(v0),.deadline_miss_o(miss0),.overflow_o(ov0),.invalid_event_o(err0),.last_cycles_o(cycles0));
 violin_core #(.PANEL_PITCH(1)) panel(.clk(clk),.rst_n(rst),.sample_tick(tick),.panel_inverse_q20(inv),.command_valid(cmd),.command_on(1'b1),.command_legato(1'b0),.command_force_off(1'b0),.command_key(7'd69),.command_velocity(7'd110),.ready_o(r1),.sample_o(s1),.sample_valid_o(v1),.deadline_miss_o(miss1),.overflow_o(ov1),.invalid_event_o(err1),.last_cycles_o(cycles1));
 integer i,k,maximum=0,half_checked=0;
 initial begin
 repeat(4)@(negedge clk);rst=1;wait(r0&&r1);repeat(2)@(negedge clk);cmd=1;@(negedge clk);cmd=0;repeat(20)@(negedge clk);
 for(i=0;i<600;i=i+1)begin
  if(i==200)inv=524288;if(i==400)inv=1079280;
  tick=1;@(negedge clk);tick=0;
  for(k=1;k<1041;k=k+1)begin
   if(miss0||miss1||ov0||ov1||err0||err1)$fatal(1,"violin status flags frame=%d",i);
   if(i<200&&(v0!==v1||s0!==s1))$fatal(1,"violin unity mismatch");
   if(i>=205&&i<400&&panel.state==24)begin
    if(panel.modulated_period<base.modulated_period/2-2||panel.modulated_period>base.modulated_period/2+2)$fatal(1,"inverse delay mismatch");
    half_checked=half_checked+1;
   end
   if(cycles1>maximum)maximum=cycles1;
   @(negedge clk);
  end
 end
 if(half_checked==0||maximum>=1041)$fatal(1,"violin coverage/deadline");
 $display("PASS panel violin: unity exact, octave half-delay, negative vibrato; max cycles=%d",maximum);$finish;
 end
 initial begin #30000000;$fatal(1,"timeout");end
endmodule

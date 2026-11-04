`timescale 1ns/1ps
module tb_panel_controller;
 reg clk=0,rst_n=0,row=0,col=0,up=0,right=0,down=0,left=0,ready=0;
 always #10 clk=~clk;
 reg[255:0]values;wire[47:0]command;wire valid,editing,reset;wire[3:0]page,fr,fc;wire[7:0]ss,vc,vh,rt;
 panel_controller dut(.clk(clk),.rst_n(rst_n),.row_next(row),.col_next(col),.up(up),.right(right),.down(down),.left(left),
 .values(values),.command_ready(ready),.command_data(command),.command_valid(valid),.page(page),.focus_row(fr),.focus_col(fc),.editing(editing),
 .slide_semi(ss),.vibrato_cents(vc),.vibrato_hz(vh),.return_10ms(rt),.reset_pitch(reset));
 task wait3;begin repeat(3)@(negedge clk);end endtask
 task press;input integer button;begin
  case(button)0:row=1;1:col=1;2:up=1;3:right=1;4:down=1;5:left=1;endcase
  @(negedge clk);row=0;col=0;up=0;right=0;down=0;left=0;wait3;
 end endtask
 reg[47:0]first;integer i;reg[7:0]op,xorval;
 initial begin
  values=0;values[16+:8]=64;values[24+:8]=64;values[32+:8]=80;values[40+:8]=127;
  values[56+:8]=40;values[64+:8]=64;values[96+:8]=32;values[144+:8]=35;
  values[200+:8]=1;values[208+:8]=5;values[216+:8]=5;values[224+:8]=25;
  wait3;rst_n=1;wait3;press(1);press(4);
  if(page!=1||fr!=1||fc!=0)$fatal(1,"select Guitar FX page");
  press(4);if(!editing)$fatal(1,"confirm must enter edit");press(3);
  if(!valid)$fatal(1,"amp edit missing");first=command;
  values[24+:8]=101;repeat(8)begin wait3;if(command!==first)$fatal(1,"backpressure changed snapshot");end
  for(i=0;i<5;i=i+1)begin
   if(!valid)$fatal(1,"atomic FX sequence truncated");op=command[39:32];
   if(op!=8'h40+i)$fatal(1,"FX packet order");
   xorval=command[47:40]^command[39:32]^command[31:24]^command[23:16]^command[15:8]^command[7:0];
   if(xorval!=0)$fatal(1,"command checksum");
   if(i==0&&(command[31:24]!=1||command[15:8]!=64))$fatal(1,"frozen FX values");
   ready=1;@(negedge clk);ready=0;wait3;
  end
  if(valid)$fatal(1,"transaction did not complete");
  press(2);if(editing)$fatal(1,"back must leave edit");press(2);if(fr!=0)$fatal(1,"back must go page header");
  for(i=0;i<4;i=i+1)press(1);press(4);if(page!=5||fr!=0||fc!=5)$fatal(1,"wave page header alignment");
  press(1);press(4);if(page!=6)$fatal(1,"spectrum page");press(1);press(4);if(page!=7)$fatal(1,"XY page");
  $display("PASS panel controller: row/column/page navigation, confirm/back/edit, frozen atomic FX with CRC under backpressure, 3 distinct visual pages");$finish;
 end
endmodule

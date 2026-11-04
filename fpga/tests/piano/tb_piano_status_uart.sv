`include "src/piano/sms_ddr/bank_config.vh"
`timescale 1ns/1ps
module tb_piano_status_uart;
 reg clk=0,rst_n=0,query=0,request=0;
 always #10 clk=~clk;
 reg [7:0] seq=0,err=0;reg [2:0] status=3;reg [10:0] count=1100;
 wire status_tx,status_busy,hold_verification,verification_tx,verification_busy;
 wire tx=status_busy?status_tx:verification_tx;
 piano_bank_status_tx dut(clk,rst_n,query,seq,status,count,err,verification_busy,hold_verification,status_tx,status_busy);
 verification_telemetry v(.clk(clk),.rst_n(rst_n),.sample_tick(1'b1),.request(request&&!hold_verification),
  .sample_l(16'h1234),.sample_r(16'habcd),.flags(8'h46),.active_count(3'd5),.latency_cycles(32'h12345678),.uart_tx(verification_tx),.busy(verification_busy));
 localparam BIT_NS=8680;
 reg [7:0] rx[0:2113];reg [7:0] b;integer n=0,k;
 initial forever begin
  @(negedge tx);#(BIT_NS+BIT_NS/2);b=0;
  for(k=0;k<8;k=k+1)begin b[k]=tx;#BIT_NS;end
  if(tx!==1'b1)$fatal(1,"UART stop bit/interleaving");
  rx[n]=b;n=n+1;
 end
 task ask(input [7:0] s);begin @(negedge clk);seq=s;query=1;@(negedge clk);query=0;end endtask
 task wait_bytes(input integer total);begin wait(n==total);wait(!status_busy);repeat(8)@(negedge clk);end endtask
 task check_status(input integer base,input [7:0] s,input [2:0] st,input [10:0] c,input [7:0] e);
  reg [7:0] x;reg [31:0] crc;integer j;
  begin
   crc=`PIANO_BANK_CRC32;x=0;
   if(rx[base]!==8'hb7||rx[base+1]!==8'h53||rx[base+2]!==s||rx[base+3]!=={5'd0,st}||
     rx[base+4]!==c[7:0]||rx[base+5]!=={5'd0,c[10:8]}||rx[base+10]!==e)$fatal(1,"status header/state snapshot");
   for(j=0;j<4;j=j+1)if(rx[base+6+j]!==crc[j*8+:8])$fatal(1,"status bank CRC mismatch");
   for(j=0;j<12;j=j+1)x=x^rx[base+j];
   if(x!==0)$fatal(1,"status XOR mismatch");
  end
 endtask
 function [15:0] crc_byte(input [15:0] val,input [7:0] data);
 reg [15:0] c;integer j;begin c=val^{data,8'd0};for(j=0;j<8;j=j+1)c=c[15]?(c<<1)^16'h1021:c<<1;crc_byte=c;end endfunction
 integer j;reg [15:0] crc;
 initial begin
  repeat(8)@(negedge clk);rst_n=1;ask(8'h21);
  // Simultaneous audio capture request is held while a status packet owns UART.
  request=1;repeat(4)@(negedge clk);request=0;
  if(verification_busy)$fatal(1,"telemetry ignored hold");
  wait_bytes(12);check_status(0,8'h21,3,1100,0);
  request=1;@(negedge clk);request=0;wait(verification_busy);
  status=2;err=3;ask(8'h99);
  if(!hold_verification||status_busy)$fatal(1,"query did not wait for telemetry packet");
  wait_bytes(2090);
  if(rx[12]!==8'hd3||rx[13]!==8'h91||rx[14]!==1||rx[15]!==8'h46)$fatal(1,"telemetry header interleaved");
  crc=16'hffff;
  for(j=14;j<2076;j=j+1)crc=crc_byte(crc,rx[j]);
  if({rx[2076],rx[2077]}!==crc)$fatal(1,"telemetry CRC/length interleaved");
  for(j=28;j<2076;j=j+4)if({rx[j+3],rx[j+2],rx[j+1],rx[j]}!==32'habcd1234)$fatal(1,"telemetry samples corrupted");
  check_status(2078,8'h99,2,1100,3);
  if(hold_verification||verification_busy)$fatal(1,"UART owner not released");
  $display("PASS DDR status UART: actual 115200 8N1; 12-byte sequence/state/count/CRC/error/XOR; telemetry 2066-byte CRC intact; packet arbitration");$finish;
 end
 initial begin #300000000;$fatal(1,"status timeout bytes=%0d",n);end
endmodule

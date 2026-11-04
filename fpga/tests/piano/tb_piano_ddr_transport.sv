`timescale 1ns/1ps
module tb_piano_ddr_transport;
 reg clk=0,mem_clk=0,rst_n=0,gsr_n=0;
 always #10 clk=~clk;
 always #5 mem_clk=~mem_clk;
 GSR GSR(.GSRI(gsr_n));
 reg req_valid=0,rsp_ready=0,freeze=0,corrupt=0;
 reg [63:0] req_data=0;
 wire req_ready,rsp_valid,fault;
 wire [63:0] rsp_data;
 wire cmd_ready,wr_data_rdy,cmd_en,wr_data_en,wr_data_end,rd_data_valid,rd_data_end;
 wire [2:0] cmd;wire [28:0] addr;wire [255:0] wr_data,rd_data;wire [31:0] mask;
 piano_ddr_transport #(.TIMEOUT(512)) dut(
  .clk(clk),.sys_rst_n(rst_n),.mem_clk(mem_clk),.mem_rst_n(rst_n),.calibrated(rst_n),
  .req_valid(req_valid),.req_ready(req_ready),.req_data(req_data),.rsp_valid(rsp_valid),.rsp_ready(rsp_ready),.rsp_data(rsp_data),.fault(fault),
  .cmd_ready(cmd_ready),.wr_data_rdy(wr_data_rdy),.cmd(cmd),.cmd_en(cmd_en),.addr(addr),
  .wr_data(wr_data),.wr_data_mask(mask),.wr_data_en(wr_data_en),.wr_data_end(wr_data_end),.rd_data(rd_data),.rd_data_valid(rd_data_valid),.rd_data_end(rd_data_end));
 ddr_parameter_app_model memory(mem_clk,rst_n,freeze,corrupt,cmd,cmd_en,addr,cmd_ready,wr_data,mask,wr_data_en,wr_data_end,wr_data_rdy,rd_data,rd_data_valid,rd_data_end);
 task send(input [63:0] data);
  begin @(negedge clk);req_data=data;req_valid=1;
   while(!req_ready)@(negedge clk);@(negedge clk);req_valid=0;
  end
 endtask
 task receive(output reg [63:0] data,input integer pause);
  begin rsp_ready=0;repeat(pause)@(negedge clk);
   while(!rsp_valid)begin @(negedge clk);if(fault)$fatal(1,"transport fault");end
   data=rsp_data;rsp_ready=1;@(negedge clk);rsp_ready=0;
  end
 endtask
 task reset;
  begin rst_n=0;req_valid=0;rsp_ready=0;freeze=0;repeat(8)@(negedge clk);rst_n=1;repeat(8)@(negedge clk);end
 endtask
 reg [255:0] value,readback;
 reg [63:0] word;
 reg [28:0] location;
 integer n,b,index;
 initial begin
  repeat(2)@(negedge clk);gsr_n=1;reset;
  for(n=0;n<256;n=n+1)begin
   index=n==255?8799:(n*37)%8800;
   location=29'h100000+(index<<3);
   for(b=0;b<8;b=b+1)value[b*32+:32]=32'h81234567^(n*32'h1020304)^(b*32'h193875ad);
   send({1'b1,34'd0,location});
   for(b=0;b<4;b=b+1)send(value[b*64+:64]);
   receive(word,n%9);if(word!==64'h5049414e4f5f4f4b)$fatal(1,"write acknowledgement");
   send({35'd0,location});
   for(b=0;b<4;b=b+1)begin receive(word,(n+b)%7);readback[b*64+:64]=word;end
   if(readback!==value)$fatal(1,"256-bit DDR/CDC ordering n=%0d",n);
  end
  if(memory.writes!=256||memory.reads!=256)$fatal(1,"DDR command count");
  // Reset while a write packet has only half its payload.
  send({1'b1,34'd0,29'h100000});send(64'hffff);reset;
  send({1'b1,34'd0,29'h100000});for(b=0;b<4;b=b+1)send(64'h123456789abcdef0+b);
  receive(word,5);if(word!==64'h5049414e4f5f4f4b)$fatal(1,"reset packet recovery");
  freeze=1;send({35'd0,29'h100000});wait(fault);repeat(5)@(negedge clk);
  if(cmd_en||wr_data_en||rsp_valid)$fatal(1,"timeout must stop traffic");
  $display("PASS DDR transport: 256 full-width writes/reads, independent command/data stalls, stereo-word lanes, 50/100 MHz CDC, response backpressure, reset, timeout");
  $finish;
 end
 initial begin #100000000;$fatal(1,"timeout");end
endmodule

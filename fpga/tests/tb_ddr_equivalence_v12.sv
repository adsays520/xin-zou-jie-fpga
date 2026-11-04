`timescale 1ns/1ps
module ddr_equivalence_v12_case #(parameter LIMIT=512,SEED=1,EPISODES=20,CYCLES=900)(output reg done=0);
 reg clk=0,mem_clk=0,rst_n=0;
 always #10 clk=~clk;
 always #5 mem_clk=~mem_clk;
 reg req_valid=0,rsp_ready=0,cmd_ready=0,wr_ready=0,rd_valid=0,rd_end=1;
 reg [63:0] req_data=0;
 reg [255:0] rd_data=0;
 wire req_ready,ref_ready,rsp_valid,ref_rsp_valid,fault,ref_fault;
 wire [63:0] rsp_data,ref_rsp_data;
 wire [2:0] cmd,ref_cmd;
 wire cmd_en,ref_cmd_en,wr_en,ref_wr_en,wr_end,ref_wr_end;
 wire [28:0] addr,ref_addr;
 wire [255:0] wr_data,ref_wr_data;
 wire [31:0] mask,ref_mask;
 integer remaining=0,episode,cycle,checks=0,accepts=0,timeout_hits=0;
 reg [31:0] random_state=SEED;
 function [31:0] next_random(input [31:0] value);
  reg [31:0] mixed;
  begin mixed=value^(value<<13);mixed=mixed^(mixed>>17);next_random=mixed^(mixed<<5);end
 endfunction
 piano_ddr_transport #(.TIMEOUT(LIMIT)) dut(clk,rst_n,mem_clk,rst_n,rst_n,
  req_valid,req_ready,req_data,rsp_valid,rsp_ready,rsp_data,fault,
  cmd_ready,wr_ready,cmd,cmd_en,addr,wr_data,mask,wr_en,wr_end,rd_data,rd_valid,rd_end);
 piano_ddr_transport_v11_reference #(.TIMEOUT(LIMIT)) reference(clk,rst_n,mem_clk,rst_n,rst_n,
  req_valid,ref_ready,req_data,ref_rsp_valid,rsp_ready,ref_rsp_data,ref_fault,
  cmd_ready,wr_ready,ref_cmd,ref_cmd_en,ref_addr,ref_wr_data,ref_mask,ref_wr_en,ref_wr_end,rd_data,rd_valid,rd_end);
 always @(negedge mem_clk)if(rst_n)begin
  if({fault,cmd_en,wr_en,wr_end,cmd,addr,mask}!=={ref_fault,ref_cmd_en,ref_wr_en,ref_wr_end,ref_cmd,ref_addr,ref_mask})
   $fatal(1,"DDR control mismatch timeout=%0d episode=%0d cycle=%0d",LIMIT,episode,cycle);
  if(wr_data!==ref_wr_data||dut.state!==reference.state||dut.timer!==reference.timer)
   $fatal(1,"DDR payload/state/timer mismatch timeout=%0d",LIMIT);
  if(dut.timer_expired!==(reference.timer>=LIMIT-1))$fatal(1,"DDR timeout predictor is not cycle exact limit=%0d",LIMIT);
  if(dut.timer_expired&&reference.state!=0)timeout_hits=timeout_hits+1;
  checks=checks+1;
 end
 always @(posedge clk)if(rst_n&&req_valid&&req_ready)begin
  remaining<=remaining==0?(req_data[63]?4:0):remaining-1;
  accepts=accepts+1;
 end
 always @(negedge clk)if(rst_n)begin
  if({req_ready,rsp_valid}!=={ref_ready,ref_rsp_valid})$fatal(1,"DDR FIFO handshake mismatch timeout=%0d",LIMIT);
  if(rsp_valid&&rsp_data!==ref_rsp_data)$fatal(1,"DDR response mismatch timeout=%0d",LIMIT);
 end
 initial begin
  for(episode=0;episode<EPISODES;episode=episode+1)begin
   rst_n=0;req_valid=0;remaining=0;
   repeat(10)@(negedge clk);rst_n=1;
   for(cycle=0;cycle<CYCLES;cycle=cycle+1)begin
    @(negedge clk);#1;
    random_state=next_random(random_state);
    req_valid=|random_state[2:0];rsp_ready=random_state[3];
    cmd_ready=episode%4==0?0:|random_state[5:4];
    wr_ready=episode%4==1?0:|random_state[7:6];
    rd_valid=episode%4==2?0:(dut.state==3&&random_state[8]);
    rd_end=episode%5!=0||random_state[9];
    rd_data={8{random_state}};
    req_data=remaining==0?{random_state[10],34'd0,random_state[28:3],3'd0}:
      {random_state,random_state^32'h8f25a117};
   end
  end
  rst_n=0;
  if(accepts<EPISODES)$fatal(1,"DDR insufficient traffic");
  if(LIMIT>1&&timeout_hits==0)$fatal(1,"actual timeout boundary not covered");
  $display("PASS V12 DDR: timeout=%0d checks=%0d accepts=%0d, cycle-exact packets/stalls/faults/resets",LIMIT,checks,accepts);
  done=1;
 end
endmodule
module tb_ddr_equivalence_v12;
 GSR GSR(1'b1);
 wire [6:0] done;
 ddr_equivalence_v12_case #(.LIMIT(1),.SEED(32'h1243)) case1(done[0]);
 ddr_equivalence_v12_case #(.LIMIT(2),.SEED(32'h2345)) case2(done[1]);
 ddr_equivalence_v12_case #(.LIMIT(3),.SEED(32'h3456)) case3(done[2]);
 ddr_equivalence_v12_case #(.LIMIT(7),.SEED(32'h4567)) case7(done[3]);
 ddr_equivalence_v12_case #(.LIMIT(32),.SEED(32'h5678)) case32(done[4]);
 ddr_equivalence_v12_case #(.LIMIT(512),.SEED(32'h6789)) case512(done[5]);
 ddr_equivalence_v12_case #(.LIMIT(100000),.SEED(32'h789a),.EPISODES(1),.CYCLES(52000)) case100000(done[6]);
 initial begin wait(&done);$finish;end
 initial begin #3000000;$fatal(1,"DDR equivalence timeout");end
endmodule

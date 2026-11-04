`timescale 1ns/1ps
module queue_equivalence_v13_case #(parameter DEPTH=16)(output reg done=0);
 reg clk=0,rst_n=0,clear=0,tick=0,uart_valid=0,local_valid=0;
 always #10 clk=~clk;
 reg [14:0] uart_event=0,local_event=0;
 wire ready,valid,overflow,ref_ready,ref_valid,ref_overflow;
 wire [14:0] data,ref_data;
 wire [$clog2(DEPTH+1)-1:0] count,ref_count;
 integer cycle;
 reg [31:0] random_state=32'h263487aa+DEPTH;
 pluck_event_queue #(.DEPTH(DEPTH)) dut(clk,rst_n,clear,tick,uart_valid,uart_event,
  local_valid,local_event,ready,valid,data,count,overflow);
 pluck_event_queue_v12_reference #(.DEPTH(DEPTH)) reference(clk,rst_n,clear,tick,uart_valid,uart_event,
  local_valid,local_event,ref_ready,ref_valid,ref_data,ref_count,ref_overflow);
 initial begin
  repeat(3)@(negedge clk);rst_n=1;
  for(cycle=0;cycle<10000;cycle=cycle+1)begin
   @(negedge clk);
   if({ready,valid,count,overflow}!=={ref_ready,ref_valid,ref_count,ref_overflow})$fatal(1,"queue state mismatch depth=%0d cycle=%0d",DEPTH,cycle);
   if(valid&&data!==ref_data)$fatal(1,"queue event order mismatch depth=%0d",DEPTH);
   random_state=random_state^(random_state<<13);
   random_state=random_state^(random_state>>17);
   random_state=random_state^(random_state<<5);
   tick=cycle<80?0:cycle<160?1:random_state[0];
   uart_valid=cycle<80?1:random_state[1];local_valid=cycle<80?1:random_state[2];
   clear=cycle>160&&random_state[7:3]==0;
   uart_event=random_state[14:0];local_event=random_state[29:15];
  end
  $display("PASS V13 queue: depth=%0d, 10000 exact dual-writer/full-pop/push/wrap/flush/overflow cycles",DEPTH);
  done=1;
 end
endmodule
module tb_queue_equivalence_v13;
 wire [3:0] done;
 queue_equivalence_v13_case #(.DEPTH(2)) case2(done[0]);
 queue_equivalence_v13_case #(.DEPTH(4)) case4(done[1]);
 queue_equivalence_v13_case #(.DEPTH(16)) case16(done[2]);
 queue_equivalence_v13_case #(.DEPTH(32)) case32(done[3]);
 initial begin wait(&done);$finish;end
 initial begin #1000000;$fatal(1,"queue equivalence timeout");end
endmodule

`timescale 1ns/1ps
module tb_ensemble_capabilities_v8;
 reg clk=0,rst_n=0,query=0,other_busy=1,enabled=0,piano_ready=1;
 reg [7:0] request_id=8'h4a;
 always #10 clk=~clk;
 wire tx,busy,hold_other,received_valid;wire [7:0] received;
 reg [7:0] packet[0:5];integer count=0;
 ensemble_capabilities dut(.clk(clk),.rst_n(rst_n),.query(query),.query_sequence(request_id),
  .ensemble_mode(enabled),.piano_ready(piano_ready),.other_busy(other_busy),.tx(tx),.busy(busy),.hold_other(hold_other));
 uart_rx_8n1 receiver(.clk(clk),.rst_n(rst_n),.rx_i(tx),.data_o(received),.data_valid_o(received_valid));
 always @(posedge clk)if(received_valid)begin packet[count%6]<=received;count++;end
 task request;
  begin @(negedge clk);query=1;@(negedge clk);query=0;end
 endtask
 task check_packet(input [7:0] flags);
  begin
   if(packet[0]!=8'hd8||packet[1]!=8'h45||packet[2]!=request_id||packet[3]!=8'h08||packet[4]!=flags||
      (packet[0]^packet[1]^packet[2]^packet[3]^packet[4]^packet[5])!=0)$fatal(1,"invalid capabilities response");
  end
 endtask
 initial begin
  repeat(5)@(negedge clk);rst_n=1;request();repeat(1000)@(negedge clk);
  if(busy||!hold_other||count)$fatal(1,"transmitter arbitration");
  other_busy=0;wait(count==6);@(negedge clk);check_packet(7);wait(!busy);
  enabled=1;piano_ready=0;request_id=8'h4b;request();wait(count==12);@(negedge clk);check_packet(8'h13);
  wait(!busy);@(negedge clk);if(hold_other)$fatal(1,"transmitter stuck");
  $display("PASS ENSEMBLE CAPABILITIES V8: actual 115200 UART, sequence/XOR, bank/verification wait, mode and bank-ready flags");
  $finish;
 end
 initial begin #5000000;$fatal(1,"capability timeout");end
endmodule

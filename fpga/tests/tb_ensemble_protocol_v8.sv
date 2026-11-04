`timescale 1ns/1ps
module tb_ensemble_protocol_v8;
 reg clk=0,rst_n=0,byte_valid=0;reg [7:0] byte_data=0;
 always #10 clk=~clk;
 wire enabled,changed,valid,query;
 wire [1:0] target;
 wire [7:0] payload_a,payload_b,payload_c,request_id;
 wire [6:0] bass_level;
 integer events=0,queries=0,changes=0;
 guitar_uart_trigger #(.EXTERNAL_BYTES(1)) dut(.clk(clk),.rst_n(rst_n),.uart_rx_i(1'b1),
  .external_byte_data(byte_data),.external_byte_valid(byte_valid),.stage_active(1'b0),.stage_valid(1'b0),.stage_index(8'd0),.stage_data(8'd0),
  .local_level_step(1'b0),.local_level_bus(2'd0),.envelope_write_allowed(1'b1),.bank_upload_ready(1'b1),
  .ensemble_mode(enabled),.ensemble_changed(changed),.ensemble_valid(valid),.ensemble_query(query),
  .ensemble_target(target),.ensemble_a(payload_a),.ensemble_b(payload_b),.ensemble_c(payload_c),
  .ensemble_sequence(request_id),.bass_bus_level(bass_level));
 always @(posedge clk)begin if(valid)events++;if(query)queries++;if(changed)changes++;end
 task send_byte(input [7:0] data);
  begin @(negedge clk);byte_data=data;byte_valid=1;@(negedge clk);byte_valid=0;repeat(3)@(negedge clk);end
 endtask
 task tx(input [7:0] opcode,first,second,third,input corrupt);
  begin send_byte(8'ha5);send_byte(opcode);send_byte(first);send_byte(second);send_byte(third);
   send_byte(8'ha5^opcode^first^second^third^{7'd0,corrupt});end
 endtask
 integer instrument;
 initial begin
  repeat(5)@(negedge clk);rst_n=1;
  tx(8'h0a,6,0,100,0);if(events!=0)$fatal(1,"target note accepted outside ensemble");
  tx(8'h0e,1,0,0,1);if(enabled)$fatal(1,"bad XOR enabled ensemble");
  tx(8'h0e,1,0,0,0);if(!enabled||changes!=1)$fatal(1,"enable");
  for(instrument=0;instrument<4;instrument++)begin
   tx(8'h0a+instrument,instrument<2?6:67,instrument<2?5:100,instrument<2?100:1,0);
   if(target!==instrument[1:0]||events!=instrument+1)$fatal(1,"target dispatch");
  end
  tx(8'h0b,1,0,100,0);tx(8'h0c,20,100,1,0);tx(8'h0d,54,100,1,0);
  if(events!=4)$fatal(1,"invalid range accepted");
  tx(8'h70,4,56,0,0);if(bass_level!=56)$fatal(1,"Bass level");
  tx(8'h0f,123,0,0,0);if(queries!=1||request_id!=123)$fatal(1,"capability query");
  tx(4,1,0,0,0);if(enabled||changes!=2)$fatal(1,"legacy timbre did not leave ensemble");
  tx(8'h0e,1,0,0,0);tx(3,1,0,0,0);if(enabled)$fatal(1,"legacy mode did not leave ensemble");
  tx(8'h0e,1,0,0,0);tx(8'h0e,0,0,0,0);if(enabled)$fatal(1,"stop");
  $display("PASS ENSEMBLE PROTOCOL V8: explicit enable, 4 independent targets, ranges/XOR, Bass bus, query, legacy return and stop");
  $finish;
 end
 initial begin #5000000;$fatal(1,"protocol timeout");end
endmodule

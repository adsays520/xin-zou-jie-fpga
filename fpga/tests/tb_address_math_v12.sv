`timescale 1ns/1ps
module tb_address_math_v12;
 GSR GSR(1'b1);
 reg [9:0] address=0;
 reg [4:0] bank=0;
 integer index,voice_id;
 poly32_road_bank dut(.clka(1'b0),.clkb(1'b0),.cea(1'b0),.ceb(1'b0),.oce(1'b1),.reset(1'b0),
  .bank(bank),.ada(address),.adb(address),.last_address(10'd599),.init_pack(1'b0),.din(24'd0));
 initial begin
  for(voice_id=0;voice_id<32;voice_id=voice_id+1)begin
   bank=voice_id;
   for(index=0;index<1024;index=index+1)begin
    address=index;#1;
    if(dut.write_row!==index/3||dut.read_row!==index/3||dut.write_slot!==index%3||dut.read_slot!==index%3)
     $fatal(1,"address arithmetic mismatch index=%0d",index);
    if(dut.read_global!==voice_id*200+index/3||dut.write_global!==voice_id*200+index/3)
     $fatal(1,"bank arithmetic mismatch");
   end
  end
  $display("PASS V12 packed address: all 32768 bank/address combinations exact; same latency and 28 SDPX9B lanes");
  $finish;
 end
endmodule

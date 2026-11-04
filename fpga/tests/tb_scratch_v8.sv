`timescale 1ns/1ps
module tb_scratch_v8;
 reg clk=0,reset=1,write_enable=0,read_enable=0;
 always #10 clk=~clk;
 GSR GSR(.GSRI(1'b1));
 reg [4:0] bank=0;
 reg [9:0] write_address=0,read_address=0,last_address=599;
 reg [23:0] data=0;
 wire [23:0] actual;
 reg [23:0] expected[0:19199];
 integer lengths[0:31];
 integer address,voice,round,checks=0;
 reg [31:0] random_state=32'h51c209ab;
 poly32_scratch_bank dut(.secco(),.decco(),.dout(actual),.dop(),.eccp(),
  .clka(clk),.clkb(clk),.cea(write_enable),.ceb(read_enable),.oce(1'b1),.reset(reset),
  .bank(bank),.ada(write_address),.adb(read_address),.last_address(last_address),.din(data));
 function [31:0] random_next(input [31:0] value);
  reg [31:0] work;
  begin work=value^(value<<13);work=work^(work>>17);random_next=work^(work<<5);end
 endfunction
 initial begin
  repeat(5)@(negedge clk);reset=0;
  for(round=0;round<4;round=round+1)begin
   for(voice=0;voice<32;voice=voice+1)lengths[voice]=round==0?600:round==1?1+voice:round==2?599-voice:16+voice*17;
   for(address=0;address<600;address=address+1)begin
    for(voice=0;voice<32;voice=voice+1)if(address<lengths[voice])begin
     @(negedge clk);bank=voice;write_address=address;last_address=lengths[voice]-1;
     random_state=random_next(random_state);data=random_state[23:0];write_enable=1;
     expected[voice*600+address]=data;
    end
   end
   @(negedge clk);write_enable=0;
   for(voice=31;voice>=0;voice=voice-1)begin
    for(address=lengths[voice]-1;address>=0;address=address-1)begin
     @(negedge clk);bank=voice;read_address=address;read_enable=1;
     @(posedge clk);#1;
     if(actual!==expected[voice*600+address])$fatal(1,"scratch round=%0d voice=%0d address=%0d got=%h expected=%h",round,voice,address,actual,expected[voice*600+address]);
     checks++;
    end
   end
   @(negedge clk);read_enable=0;reset=1;repeat(2)@(negedge clk);reset=0;
  end
  $display("PASS SCRATCH V8: %0d exact 24-bit reads, 32 interleaved voices, maximum 600, odd/even partial words, physical SDP36KE",checks);
  $finish;
 end
 initial begin #20000000;$fatal(1,"scratch timeout");end
endmodule

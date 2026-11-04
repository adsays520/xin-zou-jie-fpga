`timescale 1ns/1ps
module tb_packed_road;
 reg clk=0;always #10 clk=~clk;
 GSR GSR(.GSRI(1'b1));
 reg reset=1,cea=0,ceb=0,init_pack=1;
 reg [4:0] bank=0;reg [9:0] ada=0,adb=0,last_address=0;reg [23:0] din=0;
 wire [23:0] got,old;
 poly32_road_bank u_new(.secco(),.decco(),.dout(got),.dop(),.eccp(),.clka(clk),.clkb(clk),
   .cea(cea),.ceb(ceb),.oce(1'b1),.reset(reset),.bank(bank),.ada(ada),.adb(adb),
   .last_address(last_address),.init_pack(init_pack),.din(din));
 poly32_road_bank_gold u_gold(.secco(),.decco(),.dout(old),.dop(),.eccp(),.clka(clk),.clkb(clk),
   .cea(cea),.ceb(ceb),.oce(1'b1),.reset(reset),.bank(bank),.ada(ada),.adb(adb),
   .last_address(last_address),.init_pack(init_pack),.din(din));
 reg [23:0] expected[0:19199];
 integer lengths[0:31];integer v,a,k,b,n,checks=0,writes=0;reg [31:0] random_state=32'h185624a7;
 function [31:0] next_random(input [31:0] x);reg [31:0] t;begin t=x^(x<<13);t=t^(t>>17);next_random=t^(t<<5);end endfunction
 task read_check(input integer voice_id,address_id);
  begin
   @(negedge clk);bank=voice_id;adb=address_id;ceb=1;
   @(posedge clk);#1;
   if(got!==expected[voice_id*600+address_id]||old!==expected[voice_id*600+address_id])
    $fatal(1,"packed RAM mismatch voice=%0d addr=%0d new=%h old=%h expected=%h",voice_id,address_id,got,old,expected[voice_id*600+address_id]);
   checks=checks+1;
   @(negedge clk);ceb=0;
  end
 endtask
 initial begin
  repeat(10)@(negedge clk);reset=0;
  for(v=0;v<32;v=v+1)begin
   lengths[v]=v<3?v+1:603-v;
   for(a=0;a<lengths[v];a=a+1)begin
    @(negedge clk);bank=v;ada=a;last_address=lengths[v]-1;cea=1;
    random_state=next_random(random_state);din=random_state[23:0];expected[v*600+a]=din;
   end
   @(negedge clk);cea=0;
  end
  init_pack=0;
  for(v=0;v<32;v=v+1)for(a=0;a<lengths[v];a=a+1)read_check(v,a);
  for(k=0;k<12000;k=k+1)begin
   random_state=next_random(random_state);b=random_state%32;
   random_state=next_random(random_state);n=random_state%lengths[b];
   read_check(b,n);
   if(k%3==0)begin
    @(negedge clk);bank=b;ada=n;last_address=lengths[b]-1;cea=1;
    random_state=next_random(random_state);din=random_state[23:0];expected[b*600+n]=din;
    @(negedge clk);cea=0;writes=writes+1;
    read_check(b,n);read_check(b,(n+1)%lengths[b]);
   end
  end
  $display("PASS PACKED ROAD: %0d exact sample reads, %0d playback updates, all 32 voices, partial words, cross-voice and randomized read-modify-write",checks,writes);$finish;
 end
 initial begin #20000000;$fatal(1,"packed memory timeout");end
endmodule

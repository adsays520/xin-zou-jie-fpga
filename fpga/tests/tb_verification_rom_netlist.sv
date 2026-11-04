`timescale 1ns/1ps
module tb_verification_rom_netlist;
reg clk=0;always #10 clk=~clk;
GSR GSR(.GSRI(1'b1));
reg rst_n=0,sample_tick=0,running=0,start_event=0;
reg [63:0] frequencies=0;reg [27:0] gains=0,pans=0;
wire signed [23:0] a_l,a_r,b_l,b_r;
wire av,bv,alv,blv,adm,bdm;wire [31:0] alc,blc;wire [2:0] ac,bc;
verification_dds actual(.clk(clk),.rst_n(rst_n),.sample_tick(sample_tick),.running(running),.start_event(start_event),.frequencies(frequencies),.gains(gains),.pans(pans),.sample_l(a_l),.sample_r(a_r),.sample_valid(av),.latency_valid(alv),.deadline_miss(adm),.latency_cycles(alc),.active_count(ac));
verification_dds_reference reference(.clk(clk),.rst_n(rst_n),.sample_tick(sample_tick),.running(running),.start_event(start_event),.frequencies(frequencies),.gains(gains),.pans(pans),.sample_l(b_l),.sample_r(b_r),.sample_valid(bv),.latency_valid(blv),.deadline_miss(bdm),.latency_cycles(blc),.active_count(bc));
reg [1023:0] covered=0;
reg compare_enable=0;integer checks=0,nonzero=0,ticks=0,j,k,n;
reg [31:0] rnd=32'h13579bdf;
function [31:0] next_random(input [31:0] x);reg [31:0] t;begin t=x^(x<<13);t=t^(t>>17);next_random=t^(t<<5);end endfunction
always @(posedge clk)begin
 if(rst_n&&sample_tick&&running)begin
  ticks=ticks+1;
  for(j=0;j<4;j=j+1)covered[reference.phase[j][31:22]]=1'b1;
 end
 #2;
 if(compare_enable)begin
  if({a_l,a_r,av,alv,adm,alc,ac}!=={b_l,b_r,bv,blv,bdm,blc,bc})
   $fatal(1,"netlist mismatch time=%0t audio %h/%h ref %h/%h valid %b/%b",$time,a_l,a_r,b_l,b_r,av,bv);
  checks=checks+1;if(av&&(a_l!=0||a_r!=0))nonzero=nonzero+1;
 end
end
initial begin
 repeat(8)@(negedge clk);compare_enable=1;rst_n=1;
 for(k=0;k<32768;k=k+1)begin
  @(negedge clk);rnd=next_random(rnd);frequencies[31:0]=rnd;
  rnd=next_random(rnd);frequencies[63:32]=rnd;
  rnd=next_random(rnd);gains=rnd[27:0];rnd=next_random(rnd);pans=rnd[27:0];
  running=(k%173!=0);start_event=(k%997==0);sample_tick=1;
  if(k%509==0)gains=0;
  if(k%511==0)begin gains={4{7'd127}};pans=0;end
  if(k%521==0)begin gains={4{7'd127}};pans={4{7'd127}};end
  @(negedge clk);sample_tick=0;start_event=0;
  repeat(8)@(negedge clk);
  if(k%4096==4095)begin rst_n=0;repeat(4)@(negedge clk);rst_n=1;end
 end
 // Deliberately overlapping ticks also compare the sticky deadline diagnostic.
 repeat(20)begin @(negedge clk);sample_tick=~sample_tick;end
 @(negedge clk);sample_tick=0;repeat(12)@(negedge clk);
 n=0;for(k=0;k<1024;k=k+1)if(covered[k])n=n+1;
 if(n!=1024||nonzero<30000||checks<300000||!adm)$fatal(1,"coverage insufficient n=%0d nonzero=%0d checks=%0d deadline=%b",n,nonzero,checks,adm);
 $display("PASS VERIFICATION ROM NETLIST: %0d clocks, %0d nonzero stereo frames, all %0d sine addresses, reset/gain/pan/start/valid/latency/deadline compared to unchanged RTL",checks,nonzero,n);$finish;
end
endmodule

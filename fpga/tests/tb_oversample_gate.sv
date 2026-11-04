`timescale 1ns/1ps
module tb_oversample_gate;
 reg clk=0;always #10 clk=~clk;reg rst_n=0,start=0;
 reg [4:0] amp=0;reg [6:0] drive=127;reg signed [23:0] sample_in=0;
 wire rd,gd;wire signed [23:0] rv,gv;
 guitar_fx_oversample_rtl rtl(.clk(clk),.rst_n(rst_n),.clear(1'b0),.start(start),.amp(amp),.drive(drive),.sample_in(sample_in),.done(rd),.sample_out(rv));
 guitar_fx_oversample gate(.clk_d(clk),.rst_d(!rst_n),.clear_voice_bank(1'b0),.clearing(1'b0),.os_start(start),.a(amp[3:0]),.dr(drive),.x(sample_in),.os_done(gd),.os_out(gv));
 integer a,n,c,nonzero;
 always @(negedge clk)if(rst_n && {rd,rv}!=={gd,gv})$fatal(1,"oversample gate mismatch amp=%0d frame=%0d clock=%0d RTL=%h gate=%h",a,n,c,rv,gv);
 initial begin
  force GSR.GSRI=0;repeat(4)@(negedge clk);force GSR.GSRI=1;
  for(a=1;a<=10;a=a+1)begin
   rst_n=0;repeat(5)@(negedge clk);amp=a;rst_n=1;repeat(260)@(negedge clk);
   nonzero=0;
   for(n=0;n<96;n=n+1)begin
    sample_in=(n%16-8)*24'sd100000;start=1;@(negedge clk);start=0;
    for(c=0;c<1041;c=c+1)@(negedge clk);
    if(rv!=0)nonzero=nonzero+1;
   end
   if(nonzero<32)$fatal(1,"insufficient active output amp=%0d nonzero=%0d",a,nonzero);
  end
  $display("PASS post-synthesis oversample: 10 amps x 96 frames, active output after FIR warmup, all cycles/outputs exact");$finish;
 end
endmodule

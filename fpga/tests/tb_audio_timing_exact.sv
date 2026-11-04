`timescale 1ns/1ps
module tb_audio_timing_exact;
 reg clk=0;always #10 clk=~clk;reg rst_n=0;
 reg [15:0] left=16'hA597,right=16'h1234;
 wire [4:0] old_pins,new_pins;
 audio_drive old_driver(.clk(clk),.rst_n(rst_n),.idata_left(left),.idata_right(right),
 .req(old_pins[0]),.sample_tick(old_pins[1]),.HP_BCK(old_pins[2]),.HP_WS(old_pins[3]),.HP_DIN(old_pins[4]));
 audio_drive_updated new_driver(.clk(clk),.rst_n(rst_n),.idata_left(left),.idata_right(right),
 .req(new_pins[0]),.sample_tick(new_pins[1]),.HP_BCK(new_pins[2]),.HP_WS(new_pins[3]),.HP_DIN(new_pins[4]));
 integer n,frames=0;
 initial begin
  repeat(5)@(negedge clk);rst_n=1;
  for(n=0;n<500000;n=n+1)begin @(negedge clk);
   if(old_pins!==new_pins)$fatal(1,"audio clock/serializer mismatch at %0d",n);
   if(old_pins[1])begin frames=frames+1;left=left+16'h89A7;right=right-16'h93D5;end
  end
  $display("PASS exact I2S clock lookahead: 500000 cycles, %0d frames, BCK/WS/DIN/request/tick identical",frames);$finish;
 end
endmodule
module tb_oversample_exact;
 reg clk=0;always #10 clk=~clk;reg rst_n=0,start=0;
 reg [4:0] amp=0;reg [6:0] drive=96;reg signed [23:0] sample_in=0;
 wire od,nd;wire signed [23:0] ov,nv;
 guitar_fx_oversample old_os(.clk(clk),.rst_n(rst_n),.clear(1'b0),.start(start),.amp(amp),.drive(drive),.sample_in(sample_in),.done(od),.sample_out(ov));
 guitar_fx_oversample_updated new_os(.clk(clk),.rst_n(rst_n),.clear(1'b0),.start(start),.amp(amp),.drive(drive),.sample_in(sample_in),.done(nd),.sample_out(nv));
 integer a,n,c,max_cycles=0;reg seen_old,seen_new;reg signed [23:0] reference_value;
 initial begin
  for(a=1;a<=10;a=a+1)begin
   rst_n=0;repeat(5)@(negedge clk);rst_n=1;repeat(260)@(negedge clk);amp=a;
   for(n=0;n<96;n=n+1)begin
    sample_in=n[0] ? 24'sh180000 : -24'sh170000;seen_old=0;seen_new=0;c=0;
    start=1;@(negedge clk);start=0;
    while(!seen_new)begin @(negedge clk);c=c+1;
     if(od)begin seen_old=1;reference_value=ov;end
     if(nd)begin seen_new=1;if(!seen_old || nv!==reference_value)$fatal(1,"amp %0d frame %0d numerical mismatch",a,n);end
     if(c>1040)$fatal(1,"oversample misses 48k deadline");
    end
    if(c>max_cycles)max_cycles=c;repeat(1041-c)@(negedge clk);
   end
  end
  $display("PASS oversample pipeline: 10 amps x 96 frames bit-exact output; max clocks=%0d",max_cycles);$finish;
 end
endmodule

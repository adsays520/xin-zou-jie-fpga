`timescale 1ns/1ps
module tb_effects_deadline;
 reg clk=0;always #10 clk=~clk;reg rst_n=0,tick=0;
 wire valid,deadline;integer a,m,f,n,c,max_cycles=0;
 guitar_fx dut(.clk(clk),.rst_n(rst_n),.sample_tick(tick),.history_clear(1'b0),.sample_in(24'sh120000),
 .amp(5'd0),.drive(7'd127),.tone(7'd64),.level(7'd80),.mix(7'd127),.rate(7'd127),.depth(7'd127),.threshold(7'd32),
 .modulation(3'd0),.flags(3'd0),.changed(1'b0),.output_valid(valid),.deadline_miss(deadline));
 initial begin
  for(a=1;a<=10;a=a+1)for(m=0;m<6;m=m+1)for(f=0;f<2;f=f+1)begin
   rst_n=0;repeat(5)@(negedge clk);rst_n=1;repeat(260)@(negedge clk);
   dut.a=a;dut.mo=m;dut.fl=f?7:0;dut.dr=127;dut.ra=127;dut.de=127;
   for(n=0;n<8;n=n+1)begin
    tick=1;@(negedge clk);tick=0;c=1;
    while(!valid)begin @(negedge clk);c=c+1;if(c>1041)$fatal(1,"effects deadline amp=%0d mod=%0d flags=%0d",a,m,f);end
    if(deadline)$fatal(1,"deadline sticky");if(c>max_cycles)max_cycles=c;
    repeat(1042-c)@(negedge clk);
   end
  end
  $display("PASS complete effects deadline: 10 amps x 6 modulation modes x cabinet/gate/compressor off/on; max cycles=%0d",max_cycles);$finish;
 end
endmodule

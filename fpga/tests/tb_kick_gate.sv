`timescale 1ns/1ps
module tb_kick_gate;
 reg clk=0;always #10 clk=~clk;reg global_reset_n=0;GSR GSR(.GSRI(global_reset_n));
 reg rst_n=0,start=0,clear=0,strike=0;reg[6:0]velocity=110;reg[1:0]kit=0;
 wire rv,gv,ra,ga;wire signed[31:0]rs,gs;integer k,v,n,c,frames=0;
 kick_modal_rtl rtl(.clk(clk),.rst_n(rst_n),.start(start),.clear(clear),.strike(strike),.velocity(velocity),.kit(kit),.valid(rv),.sample(rs),.active(ra));
 kick_modal gate(.clk(clk),.rst_n(rst_n),.start(start),.clear(clear),.strike(strike),.velocity(velocity),.kit(kit),.valid(gv),.sample(gs),.active(ga));
 always@(negedge clk)if(rst_n&&{rv,ra,rs}!=={gv,ga,gs})$fatal(1,"kick gate mismatch kit=%0d vel=%0d n=%0d RTL=%h gate=%h",k,v,n,rs,gs);
 initial begin global_reset_n=0;repeat(5)@(negedge clk);global_reset_n=1;
  for(k=0;k<3;k=k+1)for(v=0;v<3;v=v+1)begin
   rst_n=0;repeat(5)@(negedge clk);kit=k;velocity=v==0?32:v==1?110:127;rst_n=1;
   for(n=0;n<256;n=n+1)begin
    start=1;strike=n==0||n==180;@(negedge clk);start=0;strike=0;c=0;
    while(!rv)begin @(negedge clk);c=c+1;if(c>256)$fatal(1,"kick timeout");end
    repeat(4)@(negedge clk);frames=frames+1;
   end
   clear=1;@(negedge clk);clear=0;repeat(4)@(negedge clk);
   if(rs||gs||ra||ga)$fatal(1,"kick clear");
   $display("PASS kick gate kit=%0d velocity=%0d",k,velocity);
  end
  $display("PASS post-synthesis kick: all 3 kits and 3 velocities, %0d frames, every cycle/output bit identical",frames);$finish;
 end
endmodule

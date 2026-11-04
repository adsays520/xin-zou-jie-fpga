`timescale 1ns/1ps
module tb_panel_visuals;
 GSR GSR(1'b1);
 reg clk=0,rst=0,tick=0;always #10 clk=~clk;
 reg signed[15:0]l=0,r=0;reg[7:0]x=0,y=0;reg[3:0]page=5;
 wire[15:0]plot,pixel;
 verification_visuals visual(.clk(clk),.rst_n(rst),.sample_tick(tick),.sample_l(l),.sample_r(r),.display_page(page-5),.pixel_x(x),.pixel_y(y),.pixel_rgb(plot));
 panel_raster raster(.clk(clk),.x(x),.y(y),.plot_rgb(plot),.page(page),.row(4'd0),.col(page),.editing(1'b0),.values(256'd0),.pixel_rgb(pixel));
 integer i,p,ix,iy,fd;reg[511:0]name;real a;
 initial begin
 repeat(4)@(negedge clk);rst=1;repeat(17000)@(negedge clk);
 for(i=0;i<3000;i=i+1)begin
 a=6.283185307179586*i/128.0;l=$rtoi(9000*$sin(a));r=$rtoi(9000*$cos(a));tick=1;@(negedge clk);tick=0;repeat(1040)@(negedge clk);
 end
 for(p=5;p<8;p=p+1)begin
 page=p;name="";$sformat(name,"tests/results/panel_page_%0d.rgb565",p);fd=$fopen(name,"wb");
 for(iy=0;iy<160;iy=iy+1)for(ix=0;ix<128;ix=ix+1)begin
  x=ix;y=iy;repeat(8)@(negedge clk);if(^pixel===1'bx)$fatal(1,"unknown plot pixel %d %d page%d",ix,iy,p);
  $fwrite(fd,"%c%c",pixel[15:8],pixel[7:0]);
 end
 $fclose(fd);
 end
 $display("PASS panel visuals: audio-derived waveform, spectrum, XY through actual display raster");$finish;
 end
endmodule

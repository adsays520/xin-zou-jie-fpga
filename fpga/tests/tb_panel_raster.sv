`timescale 1ns/1ps
module tb_panel_raster;
 reg clk=0;always #10 clk=~clk;
 reg[7:0]x=0,y=0;reg[3:0]page=0,row=1,col=0;wire[15:0]pixel;
 panel_raster dut(.clk(clk),.x(x),.y(y),.plot_rgb(16'h10c3),.page(page),.row(row),.col(col),.editing(1'b0),
 .values(256'h000100190505016e60696e6402232a1e28281920000101322802645a50400400),.pixel_rgb(pixel));
 integer p,ix,iy,fd;reg[511:0]name;
 initial begin
  for(p=0;p<5;p=p+1)begin
   page=p;name="";$sformat(name,"tests/results/panel_page_%0d.rgb565",p);fd=$fopen(name,"wb");
   for(iy=0;iy<160;iy=iy+1)for(ix=0;ix<128;ix=ix+1)begin
    x=ix;y=iy;repeat(6)@(negedge clk);if(^pixel===1'bx)$fatal(1,"unknown pixel %d %d",ix,iy);
    $fwrite(fd,"%c%c",pixel[15:8],pixel[7:0]);
   end
   $fclose(fd);
  end
  $display("PASS panel raster: five complete RGB565 control pages, no unknown pixels");$finish;
 end
endmodule

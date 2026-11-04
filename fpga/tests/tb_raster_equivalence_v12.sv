`timescale 1ns/1ps
module tb_raster_equivalence_v12;
 reg clk=0;
 always #10 clk=~clk;
 reg [7:0] x=0,y=0;
 reg [3:0] page=0,row=0,col=0;
 reg editing=0;
 reg [255:0] values=0;
 reg [15:0] plot=16'h10c3;
 wire [15:0] pixel,reference_pixel;
 reg [15:0] previous_reference;
 integer page_index,scenario,pixel_index,warmup,checks=0;
 panel_raster dut(clk,x,y,plot,page,row,col,editing,values,pixel);
 panel_raster_v11_reference reference(clk,x,y,plot,page,row,col,editing,values,reference_pixel);
 task compare_pixel;
  begin
   @(negedge clk);
   if(warmup>10)begin
    if(pixel!==previous_reference)$fatal(1,"raster mismatch page=%d scenario=%d pixel=%d new=%h reference=%h",page,scenario,pixel_index,pixel,previous_reference);
    if(^pixel===1'bx)$fatal(1,"unknown raster pixel");
    checks=checks+1;
   end
   previous_reference=reference_pixel;
   warmup=warmup+1;
  end
 endtask
 initial begin
  for(page_index=0;page_index<8;page_index=page_index+1)begin
   for(scenario=0;scenario<4;scenario=scenario+1)begin
    page=page_index;row=scenario==0?0:scenario==1?1:scenario==2?3:6;
    col=scenario==0?page_index:scenario[0];editing=scenario[1];
    values=scenario==0?256'd0:scenario==1?{32{8'd127}}:
     scenario==2?256'h000100190505016e60696e6402232a1e28281920000101322802645a50400400:
     256'h7f006432190a0100057f64090a060502017f645a50460301027f100d0a09070503;
    plot=scenario[0]?16'h8ed1:16'h10c3;
    warmup=0;
    for(pixel_index=0;pixel_index<20480;pixel_index=pixel_index+1)begin
     x=pixel_index%128;y=pixel_index/128;
     compare_pixel;
    end
    repeat(12)compare_pixel;
   end
  end
  $display("PASS V12 raster: %0d exact RGB565 comparisons, all eight pages, continuous one-pixel/clock input, focus/edit/enums/numbers",checks);
  $finish;
 end
 initial begin #20000000;$fatal(1,"raster equivalence timeout");end
endmodule

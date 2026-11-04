`timescale 1ns/1ps
module tb_panel_lcd;
 reg clk=0,rst=0;always #10 clk=~clk;
 wire sck,sda,cs,dc;integer bits=0,count=0,frames=0;reg[7:0]shift=0;time started;
 wire [7:0] expected_x=count<11?0:((count-11)/2)%128;
 wire [7:0] expected_y=count<11?0:((count-11)/2)/128;
 wire [15:0] expected_pixel;
 panel_raster_v11_reference reference(.clk(clk),.x(expected_x),.y(expected_y),.plot_rgb(16'h10c3),
  .page(4'd0),.row(4'd1),.col(4'd0),.editing(1'b0),.values(256'd0),.pixel_rgb(expected_pixel));
 st7735_status #(.PANEL_UI(1)) dut(.clk(clk),.rst_n(rst),.panel_values(256'd0),.panel_page(4'd0),.panel_row(4'd1),.panel_col(4'd0),.panel_editing(1'b0),.guitar_level(7'd127),.piano_level(7'd127),.drum_level(7'd127),.selected_bus(2'd0),.page(2'd0),.visual_page_select(2'd0),.visual_pixel_rgb(16'h10c3),.fx_drive(7'd0),.fx_tone(7'd0),.fx_mix(7'd0),.fx_amp(5'd0),.fx_modulation(3'd0),.chorus_mix(7'd0),.delay_mix(7'd0),.chorus_depth(7'd0),.drum_playing(1'b0),.lcd_sck(sck),.lcd_sda(sda),.lcd_cs_n(cs),.lcd_dc(dc));
 function[7:0]header(input integer index);
 case(index)0:header=8'h2a;4:header=127;5:header=8'h2b;9:header=159;10:header=8'h2c;default:header=0;endcase
 endfunction
 always @(posedge sck)begin
 if(cs)$fatal(1,"clock while deselected");
 shift={shift[6:0],sda};bits=bits+1;
 if(bits==8)begin
 bits=0;
 if(count<11)begin
 if(shift!==header(count))$fatal(1,"window header index%d data%h",count,shift);
 if(dc!==!(count==0||count==5||count==10))$fatal(1,"header DC");
 end else begin
 if(!dc||^shift===1'bx)$fatal(1,"pixel data/DC");
 if(shift!==((count-11)%2==0?expected_pixel[15:8]:expected_pixel[7:0]))$fatal(1,"serialized pixel mismatch index=%0d byte=%h reference=%h",count,shift,expected_pixel);
 end
 count=count+1;
 if(count==40971)begin
  frames=frames+1;
  $display("PASS panel LCD: complete128x160 RGB565 stream; frame_ns=%0t",$time-started);
  if($time-started>65000000)$fatal(1,"refresh below15fps");
  $finish;
 end
 end
 end
 initial begin
 repeat(4)@(negedge clk);rst=1;@(negedge clk);
 // Skip only the manufacturer's startup delay; exercise real byte/SPI/pixel FSM.
 force dut.state=11;force dut.delay_count=0;@(negedge clk);release dut.state;release dut.delay_count;started=$time;
 end
 initial begin #100000000;$fatal(1,"LCD timeout");end
endmodule

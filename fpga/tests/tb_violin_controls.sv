`timescale 1ns/1ps
module tb_violin_controls;
reg clk=0,rst_n=0,byte_valid=0;
reg [7:0] byte_data=0;
wire timbre_set,timbre_violin,note_on,note_off,legato;
wire [6:0] key,velocity,level;
wire hall_mode_out;
integer on_count=0,off_count=0;
always #10 clk=~clk;
guitar_uart_trigger #(.EXTERNAL_BYTES(1)) parser(.clk(clk),.rst_n(rst_n),.uart_rx_i(1'b1),
 .external_byte_data(byte_data),.external_byte_valid(byte_valid),.local_level_step(1'b0),.local_level_bus(2'd0),
 .envelope_write_allowed(1'b1),.timbre_set(timbre_set),.timbre_violin(timbre_violin),
 .violin_note_on(note_on),.violin_note_off(note_off),.violin_legato(legato),.violin_key(key),.violin_velocity(velocity),.violin_bus_level(level),.hall_mode(hall_mode_out));
always @(posedge clk)begin if(note_on)on_count++;if(note_off)off_count++;end
task send_byte(input [7:0] value);
 begin @(negedge clk);byte_data=value;byte_valid=1;@(negedge clk);byte_valid=0;end
endtask
task send_frame(input [7:0] opcode,first,second,third,input corrupt);
 begin send_byte(8'ha5);send_byte(opcode);send_byte(first);send_byte(second);send_byte(third);send_byte(8'ha5^opcode^first^second^third^corrupt);repeat(3)@(negedge clk);end
endtask
reg enabled=1,hall_mode=0,hall_valid=0;
reg [127:0] keys=0;reg [5:0] hall_mask=0;reg [47:0] hall_velocity=0;
wire [47:0] touch_data;wire touch_valid,hall_ready;
integer touch_count=0;reg [47:0] last;
touch_to_command #(.PIANO_GATE_CLKS(1000)) touch(.clk(clk),.rst_n(rst_n),.enabled(enabled),.keys(keys),.instrument(2'd3),
 .hall_mode(hall_mode),.hall_mask(hall_mask),.hall_velocity(hall_velocity),.hall_frets(30'd0),.hall_valid(hall_valid),.hall_ready(hall_ready),
 .command_data(touch_data),.command_valid(touch_valid),.command_ready(1'b1));
always @(posedge clk)if(touch_valid)begin touch_count++;last=touch_data;end
task expect_touch(input integer count,input [7:0] note,vel,action);
 begin repeat(400)@(negedge clk);
 if(touch_count!=count||last!=={8'ha5,8'h08,note,vel,action,(8'ha5^8'h08^note^vel^action)})$fatal(1,"Violin touch expected=%0d got=%0d data=%h",count,touch_count,last);
 end
endtask
initial begin
 repeat(5)@(negedge clk);rst_n=1;
 if(hall_mode_out!==0)$fatal(1,"Reset direct-touch mode");
 send_frame(9,2,0,0,0);if(hall_mode_out!==1)$fatal(1,"Hall override rejected");
 send_frame(9,3,0,0,0);send_frame(9,1,1,0,0);send_frame(9,0,0,0,1);
 if(hall_mode_out!==1)$fatal(1,"Malformed mode accepted");
 send_frame(3,1,0,0,0);if(hall_mode_out!==1)$fatal(1,"Poly mode altered Hall override");
 send_frame(9,1,0,0,0);if(hall_mode_out!==0)$fatal(1,"Direct mode rejected");
 send_frame(9,0,0,0,0);if(hall_mode_out!==0)$fatal(1,"Default mode rejected");
 send_frame(4,3,0,0,0);if(!timbre_violin)$fatal(1,"Timbre 3 rejected");
 send_frame(8,55,127,1,0);if(on_count!=1||key!=55||velocity!=127||legato)$fatal(1,"Violin on rejected");
 send_frame(8,100,80,3,0);if(on_count!=2||!legato)$fatal(1,"Legato rejected");
 send_frame(8,100,1,0,0);if(off_count!=1)$fatal(1,"Violin off rejected");
 send_frame(8,54,100,1,0);send_frame(8,101,100,1,0);send_frame(8,69,0,1,0);send_frame(8,69,100,2,0);send_frame(8,69,100,1,1);
 if(on_count!=2)$fatal(1,"Malformed violin frame accepted");
 send_frame(8'h70,3,73,0,0);if(level!=73)$fatal(1,"Violin bus rejected");
 send_byte(8'ha5);send_byte(8'h21);
 for(integer packet_index=0;packet_index<6;packet_index++)begin
  send_byte(8'ha5);send_byte(8'h08);send_byte(69);send_byte(100);send_byte(1);send_byte(8'ha5^8'h08^69^100^1);
 end
 repeat(5)@(negedge clk);if(on_count!=2)$fatal(1,"Upload payload spoofed violin event");
 keys[0]=1;expect_touch(1,55,100,1);
 keys[48]=1;expect_touch(2,63,100,3);
 keys[48]=0;expect_touch(3,55,100,3);
 keys=0;expect_touch(4,55,1,0);
 keys[125]=1;expect_touch(5,96,100,1);
 enabled=0;expect_touch(6,96,1,0);
 keys=0;hall_mode=1;enabled=1;repeat(500)@(negedge clk);
 hall_mask=8;hall_velocity=48'd90<<24;hall_valid=1;@(negedge clk);hall_valid=0;
 expect_touch(7,62,90,1);
 repeat(1200)@(negedge clk);expect_touch(8,62,1,0);
 $display("PASS R15 controls: fourth timbre, ranges/XOR/upload isolation, independent bus, held-note fallback, legato, disable release, Hall velocity/gate");$finish;
end
initial begin #10000000;$fatal(1,"Timeout");end
endmodule

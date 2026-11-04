module violin_touch_control #(parameter integer GATE_CLKS=6000000)(
 input wire clk,rst_n,selected,enabled,input wire [127:0] keys,
 input wire hall_mode,input wire [5:0] hall_mask,input wire [47:0] hall_velocity,
 input wire [29:0] hall_frets,input wire hall_valid,output wire hall_ready,
 output reg [47:0] command_data,output reg command_valid,input wire command_ready
);
reg [6:0] scan_index,scan_note,current_note;
reg scan_found,gate,last_hall_mode;
reg [125:0] scan_keys;
reg [5:0] pending_hall;
reg [47:0] pending_velocity;
reg [29:0] pending_frets;
reg [$clog2(GATE_CLKS+1)-1:0] gate_timer;
integer pick_column,search_column;
reg [6:0] hall_note;
function [6:0] midi_base;
 input [2:0] column;
 begin case(column)3:midi_base=62;4:midi_base=69;5:midi_base=76;default:midi_base=55;endcase end
endfunction
wire [6:0] candidate_note=midi_base(scan_index%6)+scan_index/6;
wire candidate_pressed=scan_keys[scan_index];
wire found=scan_found||candidate_pressed;
wire [6:0] best_note=candidate_pressed?candidate_note:scan_note;
assign hall_ready=pending_hall==0;
always @*begin
 pick_column=-1;
 for(search_column=5;search_column>=0;search_column=search_column-1)
  if(pending_hall[search_column])pick_column=search_column;
 hall_note=55;
 if(pick_column>=0)hall_note=midi_base(pick_column)+pending_frets[pick_column*5+:5];
end
task emit;
 input [6:0] note,velocity;input [7:0] action;
 begin command_data<={8'ha5,8'h08,1'b0,note,1'b0,velocity,action,(8'ha5^8'h08^{1'b0,note}^{1'b0,velocity}^action)};command_valid<=1;end
endtask
always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin
  scan_index<=0;scan_note<=55;current_note<=55;scan_found<=0;gate<=0;scan_keys<=0;
  pending_hall<=0;pending_velocity<=0;pending_frets<=0;gate_timer<=0;command_data<=0;command_valid<=0;last_hall_mode<=0;
 end else if(!selected)begin
  gate<=0;command_valid<=0;pending_hall<=0;gate_timer<=0;scan_index<=0;scan_found<=0;scan_keys<=keys[125:0];last_hall_mode<=hall_mode;
 end else begin
  if(command_valid&&command_ready)command_valid<=0;
  if(gate_timer!=0)gate_timer<=gate_timer-1'b1;
  if(hall_valid&&hall_ready&&enabled&&hall_mode)begin pending_hall<=hall_mask;pending_velocity<=hall_velocity;pending_frets<=hall_frets;end
  if(!command_valid)begin
   if(!enabled||last_hall_mode!=hall_mode)begin
    if(gate)emit(current_note,1,0);
    gate<=0;pending_hall<=0;scan_index<=0;scan_found<=0;scan_keys<=enabled?keys[125:0]:126'd0;
   end else if(hall_mode)begin
    if(pending_hall!=0&&enabled)begin
     emit(hall_note,pending_velocity[pick_column*8+:8],1);current_note<=hall_note;gate<=1;gate_timer<=GATE_CLKS;pending_hall[pick_column]<=0;
    end else if(gate&&gate_timer==0)begin emit(current_note,1,0);gate<=0;end
   end else begin
    if(scan_index==125)begin
     scan_index<=0;scan_found<=0;scan_keys<=enabled?keys[125:0]:126'd0;
     if(found&&(!gate||current_note!=best_note))begin emit(best_note,100,gate?3:1);current_note<=best_note;gate<=1;end
     else if(!found&&gate)begin emit(current_note,1,0);gate<=0;end
    end else begin
     scan_index<=scan_index+1'b1;
     if(candidate_pressed)begin scan_found<=1;scan_note<=candidate_note;end
    end
   end
   last_hall_mode<=hall_mode;
  end
 end
end
endmodule

`timescale 1ns/1ps
module violin_channel #(parameter PANEL_PITCH=0)(
 input wire clk,rst_n,sample_tick,selected,timbre_change,
 input wire [23:0] panel_inverse_q20,panel_ratio_q20,
 input wire note_on,note_off,legato,input wire [6:0] key,velocity,
 input wire pluck,input wire [2:0] string_sel,input wire [4:0] fret_sel,input wire [6:0] pluck_velocity,
 output wire signed [23:0] sample_out,output wire fault,active
);
wire ready,command_ready,deadline,overflow,invalid,core_active;
reg queue_fault,panic_pending;
reg [22:0] pluck_timer;
reg [6:0] pluck_key;
reg local_gate;
reg [6:0] base_key;
always @*begin
 case(string_sel)
  0:base_key=76;1:base_key=69;2:base_key=62;default:base_key=55;
 endcase
end
wire local_on=selected&&pluck&&!note_on&&!note_off;
wire local_off=selected&&local_gate&&pluck_timer==1;
wire force_off=timbre_change||panic_pending;
wire event_valid=force_off||(selected&&(note_on||note_off))||local_on||local_off;
wire event_on=!force_off&&(note_on||local_on);
wire [6:0] event_key=(note_on||note_off)?key:local_on?(base_key+fret_sel):pluck_key;
always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin queue_fault<=0;panic_pending<=0;pluck_timer<=0;local_gate<=0;pluck_key<=55;end
 else begin
  if(event_valid&&!command_ready)begin queue_fault<=1;panic_pending<=1;end
  else if(force_off&&command_ready)panic_pending<=0;
  if(pluck_timer!=0)pluck_timer<=pluck_timer-1'b1;
  if(local_on)begin pluck_timer<=6000000;local_gate<=1;pluck_key<=base_key+fret_sel;end
  if(local_off||note_on||note_off||timbre_change)begin local_gate<=0;pluck_timer<=0;end
 end
end
violin_core #(.PANEL_PITCH(PANEL_PITCH)) u_core(.panel_inverse_q20(panel_inverse_q20),.panel_ratio_q20(panel_ratio_q20),.clk(clk),.rst_n(rst_n),.sample_tick(sample_tick),
 .command_valid(event_valid),.command_ready(command_ready),
 .command_on(event_on),.command_legato(legato&&!local_on),.command_force_off(force_off),
 .command_key(event_key),.command_velocity(local_on?pluck_velocity:velocity),
 .active_o(core_active),.ready_o(ready),.sample_o(sample_out),.sample_valid_o(),.produced_o(),
 .internal_valid_o(),.internal_sample_o(),.deadline_miss_o(deadline),
 .overflow_o(overflow),.invalid_event_o(invalid),.last_cycles_o());
assign fault=queue_fault||deadline||overflow||invalid;
assign active=selected&&core_active;
endmodule

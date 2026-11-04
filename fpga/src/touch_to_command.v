module touch_to_command #(parameter integer PIANO_GATE_CLKS=6000000)(
 input wire clk,rst_n,enabled,input wire [127:0] keys,input wire [1:0] instrument,
 input wire hall_mode,input wire [5:0] hall_mask,input wire [47:0] hall_velocity,
 input wire [29:0] hall_frets,
 input wire hall_valid,output wire hall_ready,output wire [29:0] selected_frets,
 output wire [47:0] command_data,output wire command_valid,input wire command_ready
);
wire [47:0] legacy_data,violin_data;
wire legacy_valid,violin_valid,legacy_hall_ready,violin_hall_ready;
wire violin_selected=instrument==3;
touch_to_command_legacy #(.PIANO_GATE_CLKS(PIANO_GATE_CLKS)) u_legacy(
 .clk(clk),.rst_n(rst_n),.enabled(enabled&&!violin_selected),.keys(keys),.instrument(instrument),
 .hall_mode(hall_mode),.hall_mask(hall_mask),.hall_velocity(hall_velocity),.hall_frets(hall_frets),
 .hall_valid(hall_valid&&!violin_selected),.hall_ready(legacy_hall_ready),.selected_frets(selected_frets),
 .command_data(legacy_data),.command_valid(legacy_valid),.command_ready(command_ready&&!violin_selected));
violin_touch_control #(.GATE_CLKS(PIANO_GATE_CLKS)) u_violin(
 .clk(clk),.rst_n(rst_n),.selected(violin_selected),.enabled(enabled),.keys(keys),
 .hall_mode(hall_mode),.hall_mask(hall_mask),.hall_velocity(hall_velocity),.hall_frets(hall_frets),
 .hall_valid(hall_valid&&violin_selected),.hall_ready(violin_hall_ready),
 .command_data(violin_data),.command_valid(violin_valid),.command_ready(command_ready&&violin_selected));
assign command_data=violin_selected?violin_data:legacy_data;
assign command_valid=violin_selected?violin_valid:legacy_valid;
assign hall_ready=violin_selected?violin_hall_ready:legacy_hall_ready;
endmodule

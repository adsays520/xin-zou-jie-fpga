// SIMULATION ONLY. Application-interface behavior replaces the encrypted PHY.
// The hardware project never includes this file. No electrical/calibration
// correctness can be inferred from this mock.
`timescale 1ns/1ps
module Gowin_PLL(
    output reg lock=0,output wire clkout0,clkout1,clkout2,
    input wire clkin,reset,enclk0,enclk1,enclk2
);
    reg fast=0;always #1.25 fast=~fast;
    reg reference_clk=0;always #5 reference_clk=~reference_clk;
    assign clkout0=fast;assign clkout1=reference_clk;assign clkout2=fast&&enclk2;
    initial begin repeat(20)@(posedge clkin);lock=1;end
endmodule
module DDR3_Memory_Interface_Top(
    input wire clk,memory_clk,pll_lock,rst_n,
    output wire pll_stop,clk_out,ddr_rst,
    output reg init_calib_complete=0,
    output wire cmd_ready,input wire [2:0] cmd,input wire cmd_en,
    input wire [28:0] addr,
    output wire wr_data_rdy,input wire [255:0] wr_data,
    input wire wr_data_en,wr_data_end,input wire [31:0] wr_data_mask,
    output wire [255:0] rd_data,output wire rd_data_valid,rd_data_end,
    input wire sr_req,ref_req,burst,output wire sr_ack,ref_ack,
    output wire [14:0] O_ddr_addr,output wire [2:0] O_ddr_ba,
    output wire O_ddr_cs_n,O_ddr_ras_n,O_ddr_cas_n,O_ddr_we_n,
    output wire O_ddr_clk,O_ddr_clk_n,O_ddr_cke,O_ddr_odt,O_ddr_reset_n,
    output wire [3:0] O_ddr_dqm,
    inout wire [31:0] IO_ddr_dq,inout wire [3:0] IO_ddr_dqs,IO_ddr_dqs_n
);
    reg user_clk=0;always #5 user_clk=~user_clk;
    reg freeze=0,corrupt=0;reg [6:0] init_count=0;
    assign pll_stop=1;assign clk_out=user_clk;assign ddr_rst=!init_calib_complete;
    assign sr_ack=0;assign ref_ack=0;
    assign O_ddr_addr=0;assign O_ddr_ba=0;
    assign O_ddr_cs_n=1;assign O_ddr_ras_n=1;assign O_ddr_cas_n=1;assign O_ddr_we_n=1;
    assign O_ddr_clk=memory_clk;assign O_ddr_clk_n=!memory_clk;
    assign O_ddr_cke=1;assign O_ddr_odt=0;assign O_ddr_reset_n=rst_n;assign O_ddr_dqm=0;
    assign IO_ddr_dq=32'bz;assign IO_ddr_dqs=4'bz;assign IO_ddr_dqs_n=4'bz;
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin init_count<=0;init_calib_complete<=0;end
        else if(pll_lock&&!init_calib_complete)begin
            if(init_count==63)init_calib_complete<=1;
            else init_count<=init_count+1'b1;
        end
    end
    ddr_parameter_app_model application(
        .clk(user_clk),.rst_n(rst_n&&pll_lock&&init_calib_complete),
        .freeze(freeze),.corrupt(corrupt),.cmd(cmd),.cmd_en(cmd_en),.addr(addr),.cmd_ready(cmd_ready),
        .wr_data(wr_data),.wr_data_mask(wr_data_mask),.wr_data_en(wr_data_en),.wr_data_end(wr_data_end),
        .wr_data_rdy(wr_data_rdy),.rd_data(rd_data),.rd_data_valid(rd_data_valid),.rd_data_end(rd_data_end));
endmodule


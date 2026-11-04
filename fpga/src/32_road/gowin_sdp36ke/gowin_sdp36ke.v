//Copyright (C)2014-2026 Gowin Semiconductor Corporation.
//All rights reserved.
//File Title: IP file
//Tool Version: V1.9.12.03 (64-bit)
//IP Version: 1.0
//Part Number: GW5AST-LV138FPG676AES
//Device: GW5AST-138
//Device Version: B
//Created Time: Wed Sep  9 18:58:46 2026

module road_32 (secco, decco, dout, dop, eccp, clka, clkb, cea, ceb, oce, reset, ada, adb, din);

output secco;
output decco;
output [23:0] dout;
output [7:0] dop;
output [7:0] eccp;
input clka;
input clkb;
input cea;
input ceb;
input oce;
input reset;
input [9:0] ada;
input [9:0] adb;
input [23:0] din;

wire [39:0] dout_w;
wire [23:0] dout_0;
wire [7:0] dop_0;
wire [7:0] eccp_0;
wire [23:0] dout_1;
wire [7:0] dop_1;
wire [7:0] eccp_1;
wire dff_q_0;
wire gw_gnd;

wire secco_o_0;
wire decco_o_0;
wire secco_o_1;
wire decco_o_1;
assign secco = (decco_o_0 | decco_o_1)? 0 : (secco_o_0 | secco_o_1);
assign decco = decco_o_0 | decco_o_1;
assign gw_gnd = 1'b0;

SDP36KE sdp36ke_inst_0 (
    .DO({dout_w[39:0],dout_0[23:0]}),
    .DOP(dop_0[7:0]),
    .SECCO(secco_o_0),
    .DECCO(decco_o_0),
    .ECCP(eccp_0[7:0]),
    .CLKA(clka),
    .CLKB(clkb),
    .CEA(cea),
    .CEB(ceb),
    .OCE(oce),
    .RESET(reset),
    .ADA(ada[8:0]),
    .ADB(adb[8:0]),
    .DI({gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,din[23:0]}),
    .DIP({gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd}),
    .BLKSELA({gw_gnd,gw_gnd,ada[9]}),
    .BLKSELB({gw_gnd,gw_gnd,adb[9]}),
    .SECCI(gw_gnd),
    .DECCI(gw_gnd)
);

defparam sdp36ke_inst_0.ECC_WRITE_EN = "TRUE";
defparam sdp36ke_inst_0.ECC_READ_EN = "TRUE";
defparam sdp36ke_inst_0.READ_MODE = 1'b0;
defparam sdp36ke_inst_0.BLK_SEL_A = 3'b000;
defparam sdp36ke_inst_0.BLK_SEL_B = 3'b000;
defparam sdp36ke_inst_0.RESET_MODE = "SYNC";
defparam sdp36ke_inst_0.INIT_FILE = "NONE";
SDP36KE sdp36ke_inst_1 (
    .DO({dout_w[39:0],dout_1[23:0]}),
    .DOP(dop_1[7:0]),
    .SECCO(secco_o_1),
    .DECCO(decco_o_1),
    .ECCP(eccp_1[7:0]),
    .CLKA(clka),
    .CLKB(clkb),
    .CEA(cea),
    .CEB(ceb),
    .OCE(oce),
    .RESET(reset),
    .ADA(ada[8:0]),
    .ADB(adb[8:0]),
    .DI({gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,din[23:0]}),
    .DIP({gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd}),
    .BLKSELA({gw_gnd,gw_gnd,ada[9]}),
    .BLKSELB({gw_gnd,gw_gnd,adb[9]}),
    .SECCI(gw_gnd),
    .DECCI(gw_gnd)
);

defparam sdp36ke_inst_1.ECC_WRITE_EN = "TRUE";
defparam sdp36ke_inst_1.ECC_READ_EN = "TRUE";
defparam sdp36ke_inst_1.READ_MODE = 1'b0;
defparam sdp36ke_inst_1.BLK_SEL_A = 3'b001;
defparam sdp36ke_inst_1.BLK_SEL_B = 3'b001;
defparam sdp36ke_inst_1.RESET_MODE = "SYNC";
defparam sdp36ke_inst_1.INIT_FILE = "NONE";
DFFRE dff_inst_0 (
  .Q(dff_q_0),
  .D(adb[9]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
MUX2 mux_inst_0 (
  .O(dout[0]),
  .I0(dout_0[0]),
  .I1(dout_1[0]),
  .S0(dff_q_0)
);
MUX2 mux_inst_1 (
  .O(dout[1]),
  .I0(dout_0[1]),
  .I1(dout_1[1]),
  .S0(dff_q_0)
);
MUX2 mux_inst_2 (
  .O(dout[2]),
  .I0(dout_0[2]),
  .I1(dout_1[2]),
  .S0(dff_q_0)
);
MUX2 mux_inst_3 (
  .O(dout[3]),
  .I0(dout_0[3]),
  .I1(dout_1[3]),
  .S0(dff_q_0)
);
MUX2 mux_inst_4 (
  .O(dout[4]),
  .I0(dout_0[4]),
  .I1(dout_1[4]),
  .S0(dff_q_0)
);
MUX2 mux_inst_5 (
  .O(dout[5]),
  .I0(dout_0[5]),
  .I1(dout_1[5]),
  .S0(dff_q_0)
);
MUX2 mux_inst_6 (
  .O(dout[6]),
  .I0(dout_0[6]),
  .I1(dout_1[6]),
  .S0(dff_q_0)
);
MUX2 mux_inst_7 (
  .O(dout[7]),
  .I0(dout_0[7]),
  .I1(dout_1[7]),
  .S0(dff_q_0)
);
MUX2 mux_inst_8 (
  .O(dout[8]),
  .I0(dout_0[8]),
  .I1(dout_1[8]),
  .S0(dff_q_0)
);
MUX2 mux_inst_9 (
  .O(dout[9]),
  .I0(dout_0[9]),
  .I1(dout_1[9]),
  .S0(dff_q_0)
);
MUX2 mux_inst_10 (
  .O(dout[10]),
  .I0(dout_0[10]),
  .I1(dout_1[10]),
  .S0(dff_q_0)
);
MUX2 mux_inst_11 (
  .O(dout[11]),
  .I0(dout_0[11]),
  .I1(dout_1[11]),
  .S0(dff_q_0)
);
MUX2 mux_inst_12 (
  .O(dout[12]),
  .I0(dout_0[12]),
  .I1(dout_1[12]),
  .S0(dff_q_0)
);
MUX2 mux_inst_13 (
  .O(dout[13]),
  .I0(dout_0[13]),
  .I1(dout_1[13]),
  .S0(dff_q_0)
);
MUX2 mux_inst_14 (
  .O(dout[14]),
  .I0(dout_0[14]),
  .I1(dout_1[14]),
  .S0(dff_q_0)
);
MUX2 mux_inst_15 (
  .O(dout[15]),
  .I0(dout_0[15]),
  .I1(dout_1[15]),
  .S0(dff_q_0)
);
MUX2 mux_inst_16 (
  .O(dout[16]),
  .I0(dout_0[16]),
  .I1(dout_1[16]),
  .S0(dff_q_0)
);
MUX2 mux_inst_17 (
  .O(dout[17]),
  .I0(dout_0[17]),
  .I1(dout_1[17]),
  .S0(dff_q_0)
);
MUX2 mux_inst_18 (
  .O(dout[18]),
  .I0(dout_0[18]),
  .I1(dout_1[18]),
  .S0(dff_q_0)
);
MUX2 mux_inst_19 (
  .O(dout[19]),
  .I0(dout_0[19]),
  .I1(dout_1[19]),
  .S0(dff_q_0)
);
MUX2 mux_inst_20 (
  .O(dout[20]),
  .I0(dout_0[20]),
  .I1(dout_1[20]),
  .S0(dff_q_0)
);
MUX2 mux_inst_21 (
  .O(dout[21]),
  .I0(dout_0[21]),
  .I1(dout_1[21]),
  .S0(dff_q_0)
);
MUX2 mux_inst_22 (
  .O(dout[22]),
  .I0(dout_0[22]),
  .I1(dout_1[22]),
  .S0(dff_q_0)
);
MUX2 mux_inst_23 (
  .O(dout[23]),
  .I0(dout_0[23]),
  .I1(dout_1[23]),
  .S0(dff_q_0)
);
MUX2 mux_inst_24 (
  .O(dop[0]),
  .I0(dop_0[0]),
  .I1(dop_1[0]),
  .S0(dff_q_0)
);
MUX2 mux_inst_25 (
  .O(dop[1]),
  .I0(dop_0[1]),
  .I1(dop_1[1]),
  .S0(dff_q_0)
);
MUX2 mux_inst_26 (
  .O(dop[2]),
  .I0(dop_0[2]),
  .I1(dop_1[2]),
  .S0(dff_q_0)
);
MUX2 mux_inst_27 (
  .O(dop[3]),
  .I0(dop_0[3]),
  .I1(dop_1[3]),
  .S0(dff_q_0)
);
MUX2 mux_inst_28 (
  .O(dop[4]),
  .I0(dop_0[4]),
  .I1(dop_1[4]),
  .S0(dff_q_0)
);
MUX2 mux_inst_29 (
  .O(dop[5]),
  .I0(dop_0[5]),
  .I1(dop_1[5]),
  .S0(dff_q_0)
);
MUX2 mux_inst_30 (
  .O(dop[6]),
  .I0(dop_0[6]),
  .I1(dop_1[6]),
  .S0(dff_q_0)
);
MUX2 mux_inst_31 (
  .O(dop[7]),
  .I0(dop_0[7]),
  .I1(dop_1[7]),
  .S0(dff_q_0)
);
MUX2 mux_inst_32 (
  .O(eccp[0]),
  .I0(eccp_0[0]),
  .I1(eccp_1[0]),
  .S0(dff_q_0)
);
MUX2 mux_inst_33 (
  .O(eccp[1]),
  .I0(eccp_0[1]),
  .I1(eccp_1[1]),
  .S0(dff_q_0)
);
MUX2 mux_inst_34 (
  .O(eccp[2]),
  .I0(eccp_0[2]),
  .I1(eccp_1[2]),
  .S0(dff_q_0)
);
MUX2 mux_inst_35 (
  .O(eccp[3]),
  .I0(eccp_0[3]),
  .I1(eccp_1[3]),
  .S0(dff_q_0)
);
MUX2 mux_inst_36 (
  .O(eccp[4]),
  .I0(eccp_0[4]),
  .I1(eccp_1[4]),
  .S0(dff_q_0)
);
MUX2 mux_inst_37 (
  .O(eccp[5]),
  .I0(eccp_0[5]),
  .I1(eccp_1[5]),
  .S0(dff_q_0)
);
MUX2 mux_inst_38 (
  .O(eccp[6]),
  .I0(eccp_0[6]),
  .I1(eccp_1[6]),
  .S0(dff_q_0)
);
MUX2 mux_inst_39 (
  .O(eccp[7]),
  .I0(eccp_0[7]),
  .I1(eccp_1[7]),
  .S0(dff_q_0)
);
endmodule //road_32

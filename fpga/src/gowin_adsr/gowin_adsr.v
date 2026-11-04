//Copyright (C)2014-2026 Gowin Semiconductor Corporation.
//All rights reserved.
//File Title: IP file
//Tool Version: V1.9.12.03 (64-bit)
//IP Version: 1.0
//Part Number: GW5AST-LV138FPG676AES
//Device: GW5AST-138
//Device Version: B
//Created Time: Fri Sep 18 17:39:07 2026

module Gowin_ADSR (secco, decco, dout, dop, eccp, clka, clkb, cea, ceb, oce, reset, ada, adb, din);

output secco;
output decco;
output [15:0] dout;
output [7:0] dop;
output [7:0] eccp;
input clka;
input clkb;
input cea;
input ceb;
input oce;
input reset;
input [11:0] ada;
input [11:0] adb;
input [15:0] din;

wire [47:0] dout_w;
wire [15:0] dout_0;
wire [7:0] dop_0;
wire [7:0] eccp_0;
wire [15:0] dout_1;
wire [7:0] dop_1;
wire [7:0] eccp_1;
wire [15:0] dout_2;
wire [7:0] dop_2;
wire [7:0] eccp_2;
wire [15:0] dout_3;
wire [7:0] dop_3;
wire [7:0] eccp_3;
wire [15:0] dout_4;
wire [7:0] dop_4;
wire [7:0] eccp_4;
wire [15:0] dout_5;
wire [7:0] dop_5;
wire [7:0] eccp_5;
wire [15:0] dout_6;
wire [7:0] dop_6;
wire [7:0] eccp_6;
wire [15:0] dout_7;
wire [7:0] dop_7;
wire [7:0] eccp_7;
wire dff_q_0;
wire dff_q_1;
wire dff_q_2;
wire dff_q_3;
wire dff_q_4;
wire dff_q_5;
wire dff_q_6;
wire dff_q_7;
wire dff_q_8;
wire dff_q_9;
wire dff_q_10;
wire dff_q_11;
wire dff_q_12;
wire dff_q_13;
wire dff_q_14;
wire dff_q_15;
wire dff_q_16;
wire dff_q_17;
wire dff_q_18;
wire dff_q_19;
wire dff_q_20;
wire dff_q_21;
wire dff_q_22;
wire dff_q_23;
wire dff_q_24;
wire dff_q_25;
wire dff_q_26;
wire dff_q_27;
wire dff_q_28;
wire dff_q_29;
wire dff_q_30;
wire dff_q_31;
wire dff_q_32;
wire dff_q_33;
wire dff_q_34;
wire dff_q_35;
wire dff_q_36;
wire dff_q_37;
wire dff_q_38;
wire dff_q_39;
wire dff_q_40;
wire dff_q_41;
wire dff_q_42;
wire dff_q_43;
wire dff_q_44;
wire dff_q_45;
wire dff_q_46;
wire dff_q_47;
wire dff_q_48;
wire dff_q_49;
wire dff_q_50;
wire dff_q_51;
wire dff_q_52;
wire dff_q_53;
wire dff_q_54;
wire dff_q_55;
wire dff_q_56;
wire dff_q_57;
wire dff_q_58;
wire dff_q_59;
wire dff_q_60;
wire dff_q_61;
wire dff_q_62;
wire dff_q_63;
wire dff_q_64;
wire dff_q_65;
wire dff_q_66;
wire dff_q_67;
wire dff_q_68;
wire dff_q_69;
wire dff_q_70;
wire dff_q_71;
wire dff_q_72;
wire dff_q_73;
wire dff_q_74;
wire dff_q_75;
wire dff_q_76;
wire dff_q_77;
wire dff_q_78;
wire dff_q_79;
wire dff_q_80;
wire dff_q_81;
wire dff_q_82;
wire dff_q_83;
wire dff_q_84;
wire dff_q_85;
wire dff_q_86;
wire dff_q_87;
wire dff_q_88;
wire dff_q_89;
wire dff_q_90;
wire dff_q_91;
wire dff_q_92;
wire dff_q_93;
wire dff_q_94;
wire dff_q_95;
wire dff_q_96;
wire dff_q_97;
wire dff_q_98;
wire dff_q_99;
wire mux_o_0;
wire mux_o_1;
wire mux_o_2;
wire mux_o_3;
wire mux_o_4;
wire mux_o_5;
wire mux_o_6;
wire mux_o_7;
wire mux_o_8;
wire mux_o_9;
wire mux_o_10;
wire mux_o_11;
wire mux_o_12;
wire mux_o_13;
wire mux_o_14;
wire mux_o_15;
wire mux_o_16;
wire mux_o_17;
wire mux_o_18;
wire mux_o_19;
wire mux_o_20;
wire mux_o_21;
wire mux_o_22;
wire mux_o_23;
wire mux_o_24;
wire mux_o_25;
wire mux_o_26;
wire mux_o_27;
wire mux_o_28;
wire mux_o_29;
wire mux_o_30;
wire mux_o_31;
wire mux_o_32;
wire mux_o_33;
wire mux_o_34;
wire mux_o_35;
wire mux_o_36;
wire mux_o_37;
wire mux_o_38;
wire mux_o_39;
wire mux_o_40;
wire mux_o_41;
wire mux_o_42;
wire mux_o_43;
wire mux_o_44;
wire mux_o_45;
wire mux_o_46;
wire mux_o_47;
wire mux_o_48;
wire mux_o_49;
wire mux_o_50;
wire mux_o_51;
wire mux_o_52;
wire mux_o_53;
wire mux_o_54;
wire mux_o_55;
wire mux_o_56;
wire mux_o_57;
wire mux_o_58;
wire mux_o_59;
wire mux_o_60;
wire mux_o_61;
wire mux_o_62;
wire mux_o_63;
wire mux_o_64;
wire mux_o_65;
wire mux_o_66;
wire mux_o_67;
wire mux_o_68;
wire mux_o_69;
wire mux_o_70;
wire mux_o_71;
wire mux_o_72;
wire mux_o_73;
wire mux_o_74;
wire mux_o_75;
wire mux_o_76;
wire mux_o_77;
wire mux_o_78;
wire mux_o_79;
wire mux_o_80;
wire mux_o_81;
wire mux_o_82;
wire mux_o_83;
wire mux_o_84;
wire mux_o_85;
wire mux_o_86;
wire mux_o_87;
wire mux_o_88;
wire mux_o_89;
wire mux_o_90;
wire mux_o_91;
wire mux_o_92;
wire mux_o_93;
wire mux_o_94;
wire mux_o_95;
wire mux_o_112;
wire mux_o_113;
wire mux_o_114;
wire mux_o_115;
wire mux_o_116;
wire mux_o_117;
wire mux_o_118;
wire mux_o_119;
wire mux_o_120;
wire mux_o_121;
wire mux_o_122;
wire mux_o_123;
wire mux_o_124;
wire mux_o_125;
wire mux_o_126;
wire mux_o_127;
wire mux_o_128;
wire mux_o_129;
wire mux_o_130;
wire mux_o_131;
wire mux_o_132;
wire mux_o_133;
wire mux_o_134;
wire mux_o_135;
wire mux_o_136;
wire mux_o_137;
wire mux_o_138;
wire mux_o_139;
wire mux_o_140;
wire mux_o_141;
wire mux_o_142;
wire mux_o_143;
wire mux_o_144;
wire mux_o_145;
wire mux_o_146;
wire mux_o_147;
wire mux_o_148;
wire mux_o_149;
wire mux_o_150;
wire mux_o_151;
wire mux_o_152;
wire mux_o_153;
wire mux_o_154;
wire mux_o_155;
wire mux_o_156;
wire mux_o_157;
wire mux_o_158;
wire mux_o_159;
wire mux_o_168;
wire mux_o_169;
wire mux_o_170;
wire mux_o_171;
wire mux_o_172;
wire mux_o_173;
wire mux_o_174;
wire mux_o_175;
wire mux_o_176;
wire mux_o_177;
wire mux_o_178;
wire mux_o_179;
wire mux_o_180;
wire mux_o_181;
wire mux_o_182;
wire mux_o_183;
wire mux_o_184;
wire mux_o_185;
wire mux_o_186;
wire mux_o_187;
wire mux_o_188;
wire mux_o_189;
wire mux_o_190;
wire mux_o_191;
wire mux_o_192;
wire mux_o_193;
wire mux_o_194;
wire mux_o_195;
wire mux_o_196;
wire mux_o_197;
wire mux_o_198;
wire mux_o_199;
wire mux_o_200;
wire mux_o_201;
wire mux_o_202;
wire mux_o_203;
wire mux_o_204;
wire mux_o_205;
wire mux_o_206;
wire mux_o_207;
wire mux_o_208;
wire mux_o_209;
wire mux_o_210;
wire mux_o_211;
wire mux_o_212;
wire mux_o_213;
wire mux_o_214;
wire mux_o_215;
wire gw_gnd;

wire secco_o_0;
wire decco_o_0;
wire secco_o_1;
wire decco_o_1;
wire secco_o_2;
wire decco_o_2;
wire secco_o_3;
wire decco_o_3;
wire secco_o_4;
wire decco_o_4;
wire secco_o_5;
wire decco_o_5;
wire secco_o_6;
wire decco_o_6;
wire secco_o_7;
wire decco_o_7;
assign secco = (decco_o_0 | decco_o_1 | decco_o_2 | decco_o_3 | decco_o_4 | decco_o_5 | decco_o_6 | decco_o_7)? 0 : (secco_o_0 | secco_o_1 | secco_o_2 | secco_o_3 | secco_o_4 | secco_o_5 | secco_o_6 | secco_o_7);
assign decco = decco_o_0 | decco_o_1 | decco_o_2 | decco_o_3 | decco_o_4 | decco_o_5 | decco_o_6 | decco_o_7;
assign gw_gnd = 1'b0;

SDP36KE sdp36ke_inst_0 (
    .DO({dout_w[47:0],dout_0[15:0]}),
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
    .DI({gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,din[15:0]}),
    .DIP({gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd}),
    .BLKSELA({ada[11],ada[10],ada[9]}),
    .BLKSELB({adb[11],adb[10],adb[9]}),
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
    .DO({dout_w[47:0],dout_1[15:0]}),
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
    .DI({gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,din[15:0]}),
    .DIP({gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd}),
    .BLKSELA({ada[11],ada[10],ada[9]}),
    .BLKSELB({adb[11],adb[10],adb[9]}),
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
SDP36KE sdp36ke_inst_2 (
    .DO({dout_w[47:0],dout_2[15:0]}),
    .DOP(dop_2[7:0]),
    .SECCO(secco_o_2),
    .DECCO(decco_o_2),
    .ECCP(eccp_2[7:0]),
    .CLKA(clka),
    .CLKB(clkb),
    .CEA(cea),
    .CEB(ceb),
    .OCE(oce),
    .RESET(reset),
    .ADA(ada[8:0]),
    .ADB(adb[8:0]),
    .DI({gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,din[15:0]}),
    .DIP({gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd}),
    .BLKSELA({ada[11],ada[10],ada[9]}),
    .BLKSELB({adb[11],adb[10],adb[9]}),
    .SECCI(gw_gnd),
    .DECCI(gw_gnd)
);

defparam sdp36ke_inst_2.ECC_WRITE_EN = "TRUE";
defparam sdp36ke_inst_2.ECC_READ_EN = "TRUE";
defparam sdp36ke_inst_2.READ_MODE = 1'b0;
defparam sdp36ke_inst_2.BLK_SEL_A = 3'b010;
defparam sdp36ke_inst_2.BLK_SEL_B = 3'b010;
defparam sdp36ke_inst_2.RESET_MODE = "SYNC";
defparam sdp36ke_inst_2.INIT_FILE = "NONE";
SDP36KE sdp36ke_inst_3 (
    .DO({dout_w[47:0],dout_3[15:0]}),
    .DOP(dop_3[7:0]),
    .SECCO(secco_o_3),
    .DECCO(decco_o_3),
    .ECCP(eccp_3[7:0]),
    .CLKA(clka),
    .CLKB(clkb),
    .CEA(cea),
    .CEB(ceb),
    .OCE(oce),
    .RESET(reset),
    .ADA(ada[8:0]),
    .ADB(adb[8:0]),
    .DI({gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,din[15:0]}),
    .DIP({gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd}),
    .BLKSELA({ada[11],ada[10],ada[9]}),
    .BLKSELB({adb[11],adb[10],adb[9]}),
    .SECCI(gw_gnd),
    .DECCI(gw_gnd)
);

defparam sdp36ke_inst_3.ECC_WRITE_EN = "TRUE";
defparam sdp36ke_inst_3.ECC_READ_EN = "TRUE";
defparam sdp36ke_inst_3.READ_MODE = 1'b0;
defparam sdp36ke_inst_3.BLK_SEL_A = 3'b011;
defparam sdp36ke_inst_3.BLK_SEL_B = 3'b011;
defparam sdp36ke_inst_3.RESET_MODE = "SYNC";
defparam sdp36ke_inst_3.INIT_FILE = "NONE";
SDP36KE sdp36ke_inst_4 (
    .DO({dout_w[47:0],dout_4[15:0]}),
    .DOP(dop_4[7:0]),
    .SECCO(secco_o_4),
    .DECCO(decco_o_4),
    .ECCP(eccp_4[7:0]),
    .CLKA(clka),
    .CLKB(clkb),
    .CEA(cea),
    .CEB(ceb),
    .OCE(oce),
    .RESET(reset),
    .ADA(ada[8:0]),
    .ADB(adb[8:0]),
    .DI({gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,din[15:0]}),
    .DIP({gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd}),
    .BLKSELA({ada[11],ada[10],ada[9]}),
    .BLKSELB({adb[11],adb[10],adb[9]}),
    .SECCI(gw_gnd),
    .DECCI(gw_gnd)
);

defparam sdp36ke_inst_4.ECC_WRITE_EN = "TRUE";
defparam sdp36ke_inst_4.ECC_READ_EN = "TRUE";
defparam sdp36ke_inst_4.READ_MODE = 1'b0;
defparam sdp36ke_inst_4.BLK_SEL_A = 3'b100;
defparam sdp36ke_inst_4.BLK_SEL_B = 3'b100;
defparam sdp36ke_inst_4.RESET_MODE = "SYNC";
defparam sdp36ke_inst_4.INIT_FILE = "NONE";
SDP36KE sdp36ke_inst_5 (
    .DO({dout_w[47:0],dout_5[15:0]}),
    .DOP(dop_5[7:0]),
    .SECCO(secco_o_5),
    .DECCO(decco_o_5),
    .ECCP(eccp_5[7:0]),
    .CLKA(clka),
    .CLKB(clkb),
    .CEA(cea),
    .CEB(ceb),
    .OCE(oce),
    .RESET(reset),
    .ADA(ada[8:0]),
    .ADB(adb[8:0]),
    .DI({gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,din[15:0]}),
    .DIP({gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd}),
    .BLKSELA({ada[11],ada[10],ada[9]}),
    .BLKSELB({adb[11],adb[10],adb[9]}),
    .SECCI(gw_gnd),
    .DECCI(gw_gnd)
);

defparam sdp36ke_inst_5.ECC_WRITE_EN = "TRUE";
defparam sdp36ke_inst_5.ECC_READ_EN = "TRUE";
defparam sdp36ke_inst_5.READ_MODE = 1'b0;
defparam sdp36ke_inst_5.BLK_SEL_A = 3'b101;
defparam sdp36ke_inst_5.BLK_SEL_B = 3'b101;
defparam sdp36ke_inst_5.RESET_MODE = "SYNC";
defparam sdp36ke_inst_5.INIT_FILE = "NONE";
SDP36KE sdp36ke_inst_6 (
    .DO({dout_w[47:0],dout_6[15:0]}),
    .DOP(dop_6[7:0]),
    .SECCO(secco_o_6),
    .DECCO(decco_o_6),
    .ECCP(eccp_6[7:0]),
    .CLKA(clka),
    .CLKB(clkb),
    .CEA(cea),
    .CEB(ceb),
    .OCE(oce),
    .RESET(reset),
    .ADA(ada[8:0]),
    .ADB(adb[8:0]),
    .DI({gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,din[15:0]}),
    .DIP({gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd}),
    .BLKSELA({ada[11],ada[10],ada[9]}),
    .BLKSELB({adb[11],adb[10],adb[9]}),
    .SECCI(gw_gnd),
    .DECCI(gw_gnd)
);

defparam sdp36ke_inst_6.ECC_WRITE_EN = "TRUE";
defparam sdp36ke_inst_6.ECC_READ_EN = "TRUE";
defparam sdp36ke_inst_6.READ_MODE = 1'b0;
defparam sdp36ke_inst_6.BLK_SEL_A = 3'b110;
defparam sdp36ke_inst_6.BLK_SEL_B = 3'b110;
defparam sdp36ke_inst_6.RESET_MODE = "SYNC";
defparam sdp36ke_inst_6.INIT_FILE = "NONE";
SDP36KE sdp36ke_inst_7 (
    .DO({dout_w[47:0],dout_7[15:0]}),
    .DOP(dop_7[7:0]),
    .SECCO(secco_o_7),
    .DECCO(decco_o_7),
    .ECCP(eccp_7[7:0]),
    .CLKA(clka),
    .CLKB(clkb),
    .CEA(cea),
    .CEB(ceb),
    .OCE(oce),
    .RESET(reset),
    .ADA(ada[8:0]),
    .ADB(adb[8:0]),
    .DI({gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,din[15:0]}),
    .DIP({gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd,gw_gnd}),
    .BLKSELA({ada[11],ada[10],ada[9]}),
    .BLKSELB({adb[11],adb[10],adb[9]}),
    .SECCI(gw_gnd),
    .DECCI(gw_gnd)
);

defparam sdp36ke_inst_7.ECC_WRITE_EN = "TRUE";
defparam sdp36ke_inst_7.ECC_READ_EN = "TRUE";
defparam sdp36ke_inst_7.READ_MODE = 1'b0;
defparam sdp36ke_inst_7.BLK_SEL_A = 3'b111;
defparam sdp36ke_inst_7.BLK_SEL_B = 3'b111;
defparam sdp36ke_inst_7.RESET_MODE = "SYNC";
defparam sdp36ke_inst_7.INIT_FILE = "NONE";
DFFRE dff_inst_0 (
  .Q(dff_q_0),
  .D(adb[9]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_1 (
  .Q(dff_q_1),
  .D(adb[9]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_2 (
  .Q(dff_q_2),
  .D(adb[9]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_3 (
  .Q(dff_q_3),
  .D(adb[9]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_4 (
  .Q(dff_q_4),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_5 (
  .Q(dff_q_5),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_6 (
  .Q(dff_q_6),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_7 (
  .Q(dff_q_7),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_8 (
  .Q(dff_q_8),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_9 (
  .Q(dff_q_9),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_10 (
  .Q(dff_q_10),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_11 (
  .Q(dff_q_11),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_12 (
  .Q(dff_q_12),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_13 (
  .Q(dff_q_13),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_14 (
  .Q(dff_q_14),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_15 (
  .Q(dff_q_15),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_16 (
  .Q(dff_q_16),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_17 (
  .Q(dff_q_17),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_18 (
  .Q(dff_q_18),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_19 (
  .Q(dff_q_19),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_20 (
  .Q(dff_q_20),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_21 (
  .Q(dff_q_21),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_22 (
  .Q(dff_q_22),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_23 (
  .Q(dff_q_23),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_24 (
  .Q(dff_q_24),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_25 (
  .Q(dff_q_25),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_26 (
  .Q(dff_q_26),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_27 (
  .Q(dff_q_27),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_28 (
  .Q(dff_q_28),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_29 (
  .Q(dff_q_29),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_30 (
  .Q(dff_q_30),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_31 (
  .Q(dff_q_31),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_32 (
  .Q(dff_q_32),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_33 (
  .Q(dff_q_33),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_34 (
  .Q(dff_q_34),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_35 (
  .Q(dff_q_35),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_36 (
  .Q(dff_q_36),
  .D(adb[11]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_37 (
  .Q(dff_q_37),
  .D(adb[11]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_38 (
  .Q(dff_q_38),
  .D(adb[11]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_39 (
  .Q(dff_q_39),
  .D(adb[11]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_40 (
  .Q(dff_q_40),
  .D(adb[11]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_41 (
  .Q(dff_q_41),
  .D(adb[11]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_42 (
  .Q(dff_q_42),
  .D(adb[11]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_43 (
  .Q(dff_q_43),
  .D(adb[11]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_44 (
  .Q(dff_q_44),
  .D(adb[11]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_45 (
  .Q(dff_q_45),
  .D(adb[11]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_46 (
  .Q(dff_q_46),
  .D(adb[11]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_47 (
  .Q(dff_q_47),
  .D(adb[11]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_48 (
  .Q(dff_q_48),
  .D(adb[11]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_49 (
  .Q(dff_q_49),
  .D(adb[11]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_50 (
  .Q(dff_q_50),
  .D(adb[11]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_51 (
  .Q(dff_q_51),
  .D(adb[11]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_52 (
  .Q(dff_q_52),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_53 (
  .Q(dff_q_53),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_54 (
  .Q(dff_q_54),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_55 (
  .Q(dff_q_55),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_56 (
  .Q(dff_q_56),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_57 (
  .Q(dff_q_57),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_58 (
  .Q(dff_q_58),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_59 (
  .Q(dff_q_59),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_60 (
  .Q(dff_q_60),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_61 (
  .Q(dff_q_61),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_62 (
  .Q(dff_q_62),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_63 (
  .Q(dff_q_63),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_64 (
  .Q(dff_q_64),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_65 (
  .Q(dff_q_65),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_66 (
  .Q(dff_q_66),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_67 (
  .Q(dff_q_67),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_68 (
  .Q(dff_q_68),
  .D(adb[11]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_69 (
  .Q(dff_q_69),
  .D(adb[11]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_70 (
  .Q(dff_q_70),
  .D(adb[11]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_71 (
  .Q(dff_q_71),
  .D(adb[11]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_72 (
  .Q(dff_q_72),
  .D(adb[11]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_73 (
  .Q(dff_q_73),
  .D(adb[11]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_74 (
  .Q(dff_q_74),
  .D(adb[11]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_75 (
  .Q(dff_q_75),
  .D(adb[11]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_76 (
  .Q(dff_q_76),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_77 (
  .Q(dff_q_77),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_78 (
  .Q(dff_q_78),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_79 (
  .Q(dff_q_79),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_80 (
  .Q(dff_q_80),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_81 (
  .Q(dff_q_81),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_82 (
  .Q(dff_q_82),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_83 (
  .Q(dff_q_83),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_84 (
  .Q(dff_q_84),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_85 (
  .Q(dff_q_85),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_86 (
  .Q(dff_q_86),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_87 (
  .Q(dff_q_87),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_88 (
  .Q(dff_q_88),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_89 (
  .Q(dff_q_89),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_90 (
  .Q(dff_q_90),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_91 (
  .Q(dff_q_91),
  .D(adb[10]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_92 (
  .Q(dff_q_92),
  .D(adb[11]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_93 (
  .Q(dff_q_93),
  .D(adb[11]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_94 (
  .Q(dff_q_94),
  .D(adb[11]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_95 (
  .Q(dff_q_95),
  .D(adb[11]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_96 (
  .Q(dff_q_96),
  .D(adb[11]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_97 (
  .Q(dff_q_97),
  .D(adb[11]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_98 (
  .Q(dff_q_98),
  .D(adb[11]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
DFFRE dff_inst_99 (
  .Q(dff_q_99),
  .D(adb[11]),
  .CLK(clkb),
  .CE(ceb),
  .RESET(gw_gnd)
);
MUX2 mux_inst_0 (
  .O(mux_o_0),
  .I0(dout_0[0]),
  .I1(dout_1[0]),
  .S0(dff_q_0)
);
MUX2 mux_inst_1 (
  .O(mux_o_1),
  .I0(dout_2[0]),
  .I1(dout_3[0]),
  .S0(dff_q_1)
);
MUX2 mux_inst_2 (
  .O(mux_o_2),
  .I0(dout_4[0]),
  .I1(dout_5[0]),
  .S0(dff_q_2)
);
MUX2 mux_inst_3 (
  .O(mux_o_3),
  .I0(dout_6[0]),
  .I1(dout_7[0]),
  .S0(dff_q_3)
);
MUX2 mux_inst_4 (
  .O(mux_o_4),
  .I0(dout_0[1]),
  .I1(dout_1[1]),
  .S0(dff_q_0)
);
MUX2 mux_inst_5 (
  .O(mux_o_5),
  .I0(dout_2[1]),
  .I1(dout_3[1]),
  .S0(dff_q_1)
);
MUX2 mux_inst_6 (
  .O(mux_o_6),
  .I0(dout_4[1]),
  .I1(dout_5[1]),
  .S0(dff_q_2)
);
MUX2 mux_inst_7 (
  .O(mux_o_7),
  .I0(dout_6[1]),
  .I1(dout_7[1]),
  .S0(dff_q_3)
);
MUX2 mux_inst_8 (
  .O(mux_o_8),
  .I0(dout_0[2]),
  .I1(dout_1[2]),
  .S0(dff_q_0)
);
MUX2 mux_inst_9 (
  .O(mux_o_9),
  .I0(dout_2[2]),
  .I1(dout_3[2]),
  .S0(dff_q_1)
);
MUX2 mux_inst_10 (
  .O(mux_o_10),
  .I0(dout_4[2]),
  .I1(dout_5[2]),
  .S0(dff_q_2)
);
MUX2 mux_inst_11 (
  .O(mux_o_11),
  .I0(dout_6[2]),
  .I1(dout_7[2]),
  .S0(dff_q_3)
);
MUX2 mux_inst_12 (
  .O(mux_o_12),
  .I0(dout_0[3]),
  .I1(dout_1[3]),
  .S0(dff_q_0)
);
MUX2 mux_inst_13 (
  .O(mux_o_13),
  .I0(dout_2[3]),
  .I1(dout_3[3]),
  .S0(dff_q_1)
);
MUX2 mux_inst_14 (
  .O(mux_o_14),
  .I0(dout_4[3]),
  .I1(dout_5[3]),
  .S0(dff_q_2)
);
MUX2 mux_inst_15 (
  .O(mux_o_15),
  .I0(dout_6[3]),
  .I1(dout_7[3]),
  .S0(dff_q_3)
);
MUX2 mux_inst_16 (
  .O(mux_o_16),
  .I0(dout_0[4]),
  .I1(dout_1[4]),
  .S0(dff_q_0)
);
MUX2 mux_inst_17 (
  .O(mux_o_17),
  .I0(dout_2[4]),
  .I1(dout_3[4]),
  .S0(dff_q_1)
);
MUX2 mux_inst_18 (
  .O(mux_o_18),
  .I0(dout_4[4]),
  .I1(dout_5[4]),
  .S0(dff_q_2)
);
MUX2 mux_inst_19 (
  .O(mux_o_19),
  .I0(dout_6[4]),
  .I1(dout_7[4]),
  .S0(dff_q_3)
);
MUX2 mux_inst_20 (
  .O(mux_o_20),
  .I0(dout_0[5]),
  .I1(dout_1[5]),
  .S0(dff_q_0)
);
MUX2 mux_inst_21 (
  .O(mux_o_21),
  .I0(dout_2[5]),
  .I1(dout_3[5]),
  .S0(dff_q_1)
);
MUX2 mux_inst_22 (
  .O(mux_o_22),
  .I0(dout_4[5]),
  .I1(dout_5[5]),
  .S0(dff_q_2)
);
MUX2 mux_inst_23 (
  .O(mux_o_23),
  .I0(dout_6[5]),
  .I1(dout_7[5]),
  .S0(dff_q_3)
);
MUX2 mux_inst_24 (
  .O(mux_o_24),
  .I0(dout_0[6]),
  .I1(dout_1[6]),
  .S0(dff_q_0)
);
MUX2 mux_inst_25 (
  .O(mux_o_25),
  .I0(dout_2[6]),
  .I1(dout_3[6]),
  .S0(dff_q_1)
);
MUX2 mux_inst_26 (
  .O(mux_o_26),
  .I0(dout_4[6]),
  .I1(dout_5[6]),
  .S0(dff_q_2)
);
MUX2 mux_inst_27 (
  .O(mux_o_27),
  .I0(dout_6[6]),
  .I1(dout_7[6]),
  .S0(dff_q_3)
);
MUX2 mux_inst_28 (
  .O(mux_o_28),
  .I0(dout_0[7]),
  .I1(dout_1[7]),
  .S0(dff_q_0)
);
MUX2 mux_inst_29 (
  .O(mux_o_29),
  .I0(dout_2[7]),
  .I1(dout_3[7]),
  .S0(dff_q_1)
);
MUX2 mux_inst_30 (
  .O(mux_o_30),
  .I0(dout_4[7]),
  .I1(dout_5[7]),
  .S0(dff_q_2)
);
MUX2 mux_inst_31 (
  .O(mux_o_31),
  .I0(dout_6[7]),
  .I1(dout_7[7]),
  .S0(dff_q_3)
);
MUX2 mux_inst_32 (
  .O(mux_o_32),
  .I0(dout_0[8]),
  .I1(dout_1[8]),
  .S0(dff_q_0)
);
MUX2 mux_inst_33 (
  .O(mux_o_33),
  .I0(dout_2[8]),
  .I1(dout_3[8]),
  .S0(dff_q_1)
);
MUX2 mux_inst_34 (
  .O(mux_o_34),
  .I0(dout_4[8]),
  .I1(dout_5[8]),
  .S0(dff_q_2)
);
MUX2 mux_inst_35 (
  .O(mux_o_35),
  .I0(dout_6[8]),
  .I1(dout_7[8]),
  .S0(dff_q_3)
);
MUX2 mux_inst_36 (
  .O(mux_o_36),
  .I0(dout_0[9]),
  .I1(dout_1[9]),
  .S0(dff_q_0)
);
MUX2 mux_inst_37 (
  .O(mux_o_37),
  .I0(dout_2[9]),
  .I1(dout_3[9]),
  .S0(dff_q_1)
);
MUX2 mux_inst_38 (
  .O(mux_o_38),
  .I0(dout_4[9]),
  .I1(dout_5[9]),
  .S0(dff_q_2)
);
MUX2 mux_inst_39 (
  .O(mux_o_39),
  .I0(dout_6[9]),
  .I1(dout_7[9]),
  .S0(dff_q_3)
);
MUX2 mux_inst_40 (
  .O(mux_o_40),
  .I0(dout_0[10]),
  .I1(dout_1[10]),
  .S0(dff_q_0)
);
MUX2 mux_inst_41 (
  .O(mux_o_41),
  .I0(dout_2[10]),
  .I1(dout_3[10]),
  .S0(dff_q_1)
);
MUX2 mux_inst_42 (
  .O(mux_o_42),
  .I0(dout_4[10]),
  .I1(dout_5[10]),
  .S0(dff_q_2)
);
MUX2 mux_inst_43 (
  .O(mux_o_43),
  .I0(dout_6[10]),
  .I1(dout_7[10]),
  .S0(dff_q_3)
);
MUX2 mux_inst_44 (
  .O(mux_o_44),
  .I0(dout_0[11]),
  .I1(dout_1[11]),
  .S0(dff_q_0)
);
MUX2 mux_inst_45 (
  .O(mux_o_45),
  .I0(dout_2[11]),
  .I1(dout_3[11]),
  .S0(dff_q_1)
);
MUX2 mux_inst_46 (
  .O(mux_o_46),
  .I0(dout_4[11]),
  .I1(dout_5[11]),
  .S0(dff_q_2)
);
MUX2 mux_inst_47 (
  .O(mux_o_47),
  .I0(dout_6[11]),
  .I1(dout_7[11]),
  .S0(dff_q_3)
);
MUX2 mux_inst_48 (
  .O(mux_o_48),
  .I0(dout_0[12]),
  .I1(dout_1[12]),
  .S0(dff_q_0)
);
MUX2 mux_inst_49 (
  .O(mux_o_49),
  .I0(dout_2[12]),
  .I1(dout_3[12]),
  .S0(dff_q_1)
);
MUX2 mux_inst_50 (
  .O(mux_o_50),
  .I0(dout_4[12]),
  .I1(dout_5[12]),
  .S0(dff_q_2)
);
MUX2 mux_inst_51 (
  .O(mux_o_51),
  .I0(dout_6[12]),
  .I1(dout_7[12]),
  .S0(dff_q_3)
);
MUX2 mux_inst_52 (
  .O(mux_o_52),
  .I0(dout_0[13]),
  .I1(dout_1[13]),
  .S0(dff_q_0)
);
MUX2 mux_inst_53 (
  .O(mux_o_53),
  .I0(dout_2[13]),
  .I1(dout_3[13]),
  .S0(dff_q_1)
);
MUX2 mux_inst_54 (
  .O(mux_o_54),
  .I0(dout_4[13]),
  .I1(dout_5[13]),
  .S0(dff_q_2)
);
MUX2 mux_inst_55 (
  .O(mux_o_55),
  .I0(dout_6[13]),
  .I1(dout_7[13]),
  .S0(dff_q_3)
);
MUX2 mux_inst_56 (
  .O(mux_o_56),
  .I0(dout_0[14]),
  .I1(dout_1[14]),
  .S0(dff_q_0)
);
MUX2 mux_inst_57 (
  .O(mux_o_57),
  .I0(dout_2[14]),
  .I1(dout_3[14]),
  .S0(dff_q_1)
);
MUX2 mux_inst_58 (
  .O(mux_o_58),
  .I0(dout_4[14]),
  .I1(dout_5[14]),
  .S0(dff_q_2)
);
MUX2 mux_inst_59 (
  .O(mux_o_59),
  .I0(dout_6[14]),
  .I1(dout_7[14]),
  .S0(dff_q_3)
);
MUX2 mux_inst_60 (
  .O(mux_o_60),
  .I0(dout_0[15]),
  .I1(dout_1[15]),
  .S0(dff_q_0)
);
MUX2 mux_inst_61 (
  .O(mux_o_61),
  .I0(dout_2[15]),
  .I1(dout_3[15]),
  .S0(dff_q_1)
);
MUX2 mux_inst_62 (
  .O(mux_o_62),
  .I0(dout_4[15]),
  .I1(dout_5[15]),
  .S0(dff_q_2)
);
MUX2 mux_inst_63 (
  .O(mux_o_63),
  .I0(dout_6[15]),
  .I1(dout_7[15]),
  .S0(dff_q_3)
);
MUX2 mux_inst_64 (
  .O(mux_o_64),
  .I0(mux_o_0),
  .I1(mux_o_1),
  .S0(dff_q_4)
);
MUX2 mux_inst_65 (
  .O(mux_o_65),
  .I0(mux_o_2),
  .I1(mux_o_3),
  .S0(dff_q_5)
);
MUX2 mux_inst_66 (
  .O(mux_o_66),
  .I0(mux_o_4),
  .I1(mux_o_5),
  .S0(dff_q_6)
);
MUX2 mux_inst_67 (
  .O(mux_o_67),
  .I0(mux_o_6),
  .I1(mux_o_7),
  .S0(dff_q_7)
);
MUX2 mux_inst_68 (
  .O(mux_o_68),
  .I0(mux_o_8),
  .I1(mux_o_9),
  .S0(dff_q_8)
);
MUX2 mux_inst_69 (
  .O(mux_o_69),
  .I0(mux_o_10),
  .I1(mux_o_11),
  .S0(dff_q_9)
);
MUX2 mux_inst_70 (
  .O(mux_o_70),
  .I0(mux_o_12),
  .I1(mux_o_13),
  .S0(dff_q_10)
);
MUX2 mux_inst_71 (
  .O(mux_o_71),
  .I0(mux_o_14),
  .I1(mux_o_15),
  .S0(dff_q_11)
);
MUX2 mux_inst_72 (
  .O(mux_o_72),
  .I0(mux_o_16),
  .I1(mux_o_17),
  .S0(dff_q_12)
);
MUX2 mux_inst_73 (
  .O(mux_o_73),
  .I0(mux_o_18),
  .I1(mux_o_19),
  .S0(dff_q_13)
);
MUX2 mux_inst_74 (
  .O(mux_o_74),
  .I0(mux_o_20),
  .I1(mux_o_21),
  .S0(dff_q_14)
);
MUX2 mux_inst_75 (
  .O(mux_o_75),
  .I0(mux_o_22),
  .I1(mux_o_23),
  .S0(dff_q_15)
);
MUX2 mux_inst_76 (
  .O(mux_o_76),
  .I0(mux_o_24),
  .I1(mux_o_25),
  .S0(dff_q_16)
);
MUX2 mux_inst_77 (
  .O(mux_o_77),
  .I0(mux_o_26),
  .I1(mux_o_27),
  .S0(dff_q_17)
);
MUX2 mux_inst_78 (
  .O(mux_o_78),
  .I0(mux_o_28),
  .I1(mux_o_29),
  .S0(dff_q_18)
);
MUX2 mux_inst_79 (
  .O(mux_o_79),
  .I0(mux_o_30),
  .I1(mux_o_31),
  .S0(dff_q_19)
);
MUX2 mux_inst_80 (
  .O(mux_o_80),
  .I0(mux_o_32),
  .I1(mux_o_33),
  .S0(dff_q_20)
);
MUX2 mux_inst_81 (
  .O(mux_o_81),
  .I0(mux_o_34),
  .I1(mux_o_35),
  .S0(dff_q_21)
);
MUX2 mux_inst_82 (
  .O(mux_o_82),
  .I0(mux_o_36),
  .I1(mux_o_37),
  .S0(dff_q_22)
);
MUX2 mux_inst_83 (
  .O(mux_o_83),
  .I0(mux_o_38),
  .I1(mux_o_39),
  .S0(dff_q_23)
);
MUX2 mux_inst_84 (
  .O(mux_o_84),
  .I0(mux_o_40),
  .I1(mux_o_41),
  .S0(dff_q_24)
);
MUX2 mux_inst_85 (
  .O(mux_o_85),
  .I0(mux_o_42),
  .I1(mux_o_43),
  .S0(dff_q_25)
);
MUX2 mux_inst_86 (
  .O(mux_o_86),
  .I0(mux_o_44),
  .I1(mux_o_45),
  .S0(dff_q_26)
);
MUX2 mux_inst_87 (
  .O(mux_o_87),
  .I0(mux_o_46),
  .I1(mux_o_47),
  .S0(dff_q_27)
);
MUX2 mux_inst_88 (
  .O(mux_o_88),
  .I0(mux_o_48),
  .I1(mux_o_49),
  .S0(dff_q_28)
);
MUX2 mux_inst_89 (
  .O(mux_o_89),
  .I0(mux_o_50),
  .I1(mux_o_51),
  .S0(dff_q_29)
);
MUX2 mux_inst_90 (
  .O(mux_o_90),
  .I0(mux_o_52),
  .I1(mux_o_53),
  .S0(dff_q_30)
);
MUX2 mux_inst_91 (
  .O(mux_o_91),
  .I0(mux_o_54),
  .I1(mux_o_55),
  .S0(dff_q_31)
);
MUX2 mux_inst_92 (
  .O(mux_o_92),
  .I0(mux_o_56),
  .I1(mux_o_57),
  .S0(dff_q_32)
);
MUX2 mux_inst_93 (
  .O(mux_o_93),
  .I0(mux_o_58),
  .I1(mux_o_59),
  .S0(dff_q_33)
);
MUX2 mux_inst_94 (
  .O(mux_o_94),
  .I0(mux_o_60),
  .I1(mux_o_61),
  .S0(dff_q_34)
);
MUX2 mux_inst_95 (
  .O(mux_o_95),
  .I0(mux_o_62),
  .I1(mux_o_63),
  .S0(dff_q_35)
);
MUX2 mux_inst_96 (
  .O(dout[0]),
  .I0(mux_o_64),
  .I1(mux_o_65),
  .S0(dff_q_36)
);
MUX2 mux_inst_97 (
  .O(dout[1]),
  .I0(mux_o_66),
  .I1(mux_o_67),
  .S0(dff_q_37)
);
MUX2 mux_inst_98 (
  .O(dout[2]),
  .I0(mux_o_68),
  .I1(mux_o_69),
  .S0(dff_q_38)
);
MUX2 mux_inst_99 (
  .O(dout[3]),
  .I0(mux_o_70),
  .I1(mux_o_71),
  .S0(dff_q_39)
);
MUX2 mux_inst_100 (
  .O(dout[4]),
  .I0(mux_o_72),
  .I1(mux_o_73),
  .S0(dff_q_40)
);
MUX2 mux_inst_101 (
  .O(dout[5]),
  .I0(mux_o_74),
  .I1(mux_o_75),
  .S0(dff_q_41)
);
MUX2 mux_inst_102 (
  .O(dout[6]),
  .I0(mux_o_76),
  .I1(mux_o_77),
  .S0(dff_q_42)
);
MUX2 mux_inst_103 (
  .O(dout[7]),
  .I0(mux_o_78),
  .I1(mux_o_79),
  .S0(dff_q_43)
);
MUX2 mux_inst_104 (
  .O(dout[8]),
  .I0(mux_o_80),
  .I1(mux_o_81),
  .S0(dff_q_44)
);
MUX2 mux_inst_105 (
  .O(dout[9]),
  .I0(mux_o_82),
  .I1(mux_o_83),
  .S0(dff_q_45)
);
MUX2 mux_inst_106 (
  .O(dout[10]),
  .I0(mux_o_84),
  .I1(mux_o_85),
  .S0(dff_q_46)
);
MUX2 mux_inst_107 (
  .O(dout[11]),
  .I0(mux_o_86),
  .I1(mux_o_87),
  .S0(dff_q_47)
);
MUX2 mux_inst_108 (
  .O(dout[12]),
  .I0(mux_o_88),
  .I1(mux_o_89),
  .S0(dff_q_48)
);
MUX2 mux_inst_109 (
  .O(dout[13]),
  .I0(mux_o_90),
  .I1(mux_o_91),
  .S0(dff_q_49)
);
MUX2 mux_inst_110 (
  .O(dout[14]),
  .I0(mux_o_92),
  .I1(mux_o_93),
  .S0(dff_q_50)
);
MUX2 mux_inst_111 (
  .O(dout[15]),
  .I0(mux_o_94),
  .I1(mux_o_95),
  .S0(dff_q_51)
);
MUX2 mux_inst_112 (
  .O(mux_o_112),
  .I0(dop_0[0]),
  .I1(dop_1[0]),
  .S0(dff_q_0)
);
MUX2 mux_inst_113 (
  .O(mux_o_113),
  .I0(dop_2[0]),
  .I1(dop_3[0]),
  .S0(dff_q_1)
);
MUX2 mux_inst_114 (
  .O(mux_o_114),
  .I0(dop_4[0]),
  .I1(dop_5[0]),
  .S0(dff_q_2)
);
MUX2 mux_inst_115 (
  .O(mux_o_115),
  .I0(dop_6[0]),
  .I1(dop_7[0]),
  .S0(dff_q_3)
);
MUX2 mux_inst_116 (
  .O(mux_o_116),
  .I0(dop_0[1]),
  .I1(dop_1[1]),
  .S0(dff_q_0)
);
MUX2 mux_inst_117 (
  .O(mux_o_117),
  .I0(dop_2[1]),
  .I1(dop_3[1]),
  .S0(dff_q_1)
);
MUX2 mux_inst_118 (
  .O(mux_o_118),
  .I0(dop_4[1]),
  .I1(dop_5[1]),
  .S0(dff_q_2)
);
MUX2 mux_inst_119 (
  .O(mux_o_119),
  .I0(dop_6[1]),
  .I1(dop_7[1]),
  .S0(dff_q_3)
);
MUX2 mux_inst_120 (
  .O(mux_o_120),
  .I0(dop_0[2]),
  .I1(dop_1[2]),
  .S0(dff_q_0)
);
MUX2 mux_inst_121 (
  .O(mux_o_121),
  .I0(dop_2[2]),
  .I1(dop_3[2]),
  .S0(dff_q_1)
);
MUX2 mux_inst_122 (
  .O(mux_o_122),
  .I0(dop_4[2]),
  .I1(dop_5[2]),
  .S0(dff_q_2)
);
MUX2 mux_inst_123 (
  .O(mux_o_123),
  .I0(dop_6[2]),
  .I1(dop_7[2]),
  .S0(dff_q_3)
);
MUX2 mux_inst_124 (
  .O(mux_o_124),
  .I0(dop_0[3]),
  .I1(dop_1[3]),
  .S0(dff_q_0)
);
MUX2 mux_inst_125 (
  .O(mux_o_125),
  .I0(dop_2[3]),
  .I1(dop_3[3]),
  .S0(dff_q_1)
);
MUX2 mux_inst_126 (
  .O(mux_o_126),
  .I0(dop_4[3]),
  .I1(dop_5[3]),
  .S0(dff_q_2)
);
MUX2 mux_inst_127 (
  .O(mux_o_127),
  .I0(dop_6[3]),
  .I1(dop_7[3]),
  .S0(dff_q_3)
);
MUX2 mux_inst_128 (
  .O(mux_o_128),
  .I0(dop_0[4]),
  .I1(dop_1[4]),
  .S0(dff_q_0)
);
MUX2 mux_inst_129 (
  .O(mux_o_129),
  .I0(dop_2[4]),
  .I1(dop_3[4]),
  .S0(dff_q_1)
);
MUX2 mux_inst_130 (
  .O(mux_o_130),
  .I0(dop_4[4]),
  .I1(dop_5[4]),
  .S0(dff_q_2)
);
MUX2 mux_inst_131 (
  .O(mux_o_131),
  .I0(dop_6[4]),
  .I1(dop_7[4]),
  .S0(dff_q_3)
);
MUX2 mux_inst_132 (
  .O(mux_o_132),
  .I0(dop_0[5]),
  .I1(dop_1[5]),
  .S0(dff_q_0)
);
MUX2 mux_inst_133 (
  .O(mux_o_133),
  .I0(dop_2[5]),
  .I1(dop_3[5]),
  .S0(dff_q_1)
);
MUX2 mux_inst_134 (
  .O(mux_o_134),
  .I0(dop_4[5]),
  .I1(dop_5[5]),
  .S0(dff_q_2)
);
MUX2 mux_inst_135 (
  .O(mux_o_135),
  .I0(dop_6[5]),
  .I1(dop_7[5]),
  .S0(dff_q_3)
);
MUX2 mux_inst_136 (
  .O(mux_o_136),
  .I0(dop_0[6]),
  .I1(dop_1[6]),
  .S0(dff_q_0)
);
MUX2 mux_inst_137 (
  .O(mux_o_137),
  .I0(dop_2[6]),
  .I1(dop_3[6]),
  .S0(dff_q_1)
);
MUX2 mux_inst_138 (
  .O(mux_o_138),
  .I0(dop_4[6]),
  .I1(dop_5[6]),
  .S0(dff_q_2)
);
MUX2 mux_inst_139 (
  .O(mux_o_139),
  .I0(dop_6[6]),
  .I1(dop_7[6]),
  .S0(dff_q_3)
);
MUX2 mux_inst_140 (
  .O(mux_o_140),
  .I0(dop_0[7]),
  .I1(dop_1[7]),
  .S0(dff_q_0)
);
MUX2 mux_inst_141 (
  .O(mux_o_141),
  .I0(dop_2[7]),
  .I1(dop_3[7]),
  .S0(dff_q_1)
);
MUX2 mux_inst_142 (
  .O(mux_o_142),
  .I0(dop_4[7]),
  .I1(dop_5[7]),
  .S0(dff_q_2)
);
MUX2 mux_inst_143 (
  .O(mux_o_143),
  .I0(dop_6[7]),
  .I1(dop_7[7]),
  .S0(dff_q_3)
);
MUX2 mux_inst_144 (
  .O(mux_o_144),
  .I0(mux_o_112),
  .I1(mux_o_113),
  .S0(dff_q_52)
);
MUX2 mux_inst_145 (
  .O(mux_o_145),
  .I0(mux_o_114),
  .I1(mux_o_115),
  .S0(dff_q_53)
);
MUX2 mux_inst_146 (
  .O(mux_o_146),
  .I0(mux_o_116),
  .I1(mux_o_117),
  .S0(dff_q_54)
);
MUX2 mux_inst_147 (
  .O(mux_o_147),
  .I0(mux_o_118),
  .I1(mux_o_119),
  .S0(dff_q_55)
);
MUX2 mux_inst_148 (
  .O(mux_o_148),
  .I0(mux_o_120),
  .I1(mux_o_121),
  .S0(dff_q_56)
);
MUX2 mux_inst_149 (
  .O(mux_o_149),
  .I0(mux_o_122),
  .I1(mux_o_123),
  .S0(dff_q_57)
);
MUX2 mux_inst_150 (
  .O(mux_o_150),
  .I0(mux_o_124),
  .I1(mux_o_125),
  .S0(dff_q_58)
);
MUX2 mux_inst_151 (
  .O(mux_o_151),
  .I0(mux_o_126),
  .I1(mux_o_127),
  .S0(dff_q_59)
);
MUX2 mux_inst_152 (
  .O(mux_o_152),
  .I0(mux_o_128),
  .I1(mux_o_129),
  .S0(dff_q_60)
);
MUX2 mux_inst_153 (
  .O(mux_o_153),
  .I0(mux_o_130),
  .I1(mux_o_131),
  .S0(dff_q_61)
);
MUX2 mux_inst_154 (
  .O(mux_o_154),
  .I0(mux_o_132),
  .I1(mux_o_133),
  .S0(dff_q_62)
);
MUX2 mux_inst_155 (
  .O(mux_o_155),
  .I0(mux_o_134),
  .I1(mux_o_135),
  .S0(dff_q_63)
);
MUX2 mux_inst_156 (
  .O(mux_o_156),
  .I0(mux_o_136),
  .I1(mux_o_137),
  .S0(dff_q_64)
);
MUX2 mux_inst_157 (
  .O(mux_o_157),
  .I0(mux_o_138),
  .I1(mux_o_139),
  .S0(dff_q_65)
);
MUX2 mux_inst_158 (
  .O(mux_o_158),
  .I0(mux_o_140),
  .I1(mux_o_141),
  .S0(dff_q_66)
);
MUX2 mux_inst_159 (
  .O(mux_o_159),
  .I0(mux_o_142),
  .I1(mux_o_143),
  .S0(dff_q_67)
);
MUX2 mux_inst_160 (
  .O(dop[0]),
  .I0(mux_o_144),
  .I1(mux_o_145),
  .S0(dff_q_68)
);
MUX2 mux_inst_161 (
  .O(dop[1]),
  .I0(mux_o_146),
  .I1(mux_o_147),
  .S0(dff_q_69)
);
MUX2 mux_inst_162 (
  .O(dop[2]),
  .I0(mux_o_148),
  .I1(mux_o_149),
  .S0(dff_q_70)
);
MUX2 mux_inst_163 (
  .O(dop[3]),
  .I0(mux_o_150),
  .I1(mux_o_151),
  .S0(dff_q_71)
);
MUX2 mux_inst_164 (
  .O(dop[4]),
  .I0(mux_o_152),
  .I1(mux_o_153),
  .S0(dff_q_72)
);
MUX2 mux_inst_165 (
  .O(dop[5]),
  .I0(mux_o_154),
  .I1(mux_o_155),
  .S0(dff_q_73)
);
MUX2 mux_inst_166 (
  .O(dop[6]),
  .I0(mux_o_156),
  .I1(mux_o_157),
  .S0(dff_q_74)
);
MUX2 mux_inst_167 (
  .O(dop[7]),
  .I0(mux_o_158),
  .I1(mux_o_159),
  .S0(dff_q_75)
);
MUX2 mux_inst_168 (
  .O(mux_o_168),
  .I0(eccp_0[0]),
  .I1(eccp_1[0]),
  .S0(dff_q_0)
);
MUX2 mux_inst_169 (
  .O(mux_o_169),
  .I0(eccp_2[0]),
  .I1(eccp_3[0]),
  .S0(dff_q_1)
);
MUX2 mux_inst_170 (
  .O(mux_o_170),
  .I0(eccp_4[0]),
  .I1(eccp_5[0]),
  .S0(dff_q_2)
);
MUX2 mux_inst_171 (
  .O(mux_o_171),
  .I0(eccp_6[0]),
  .I1(eccp_7[0]),
  .S0(dff_q_3)
);
MUX2 mux_inst_172 (
  .O(mux_o_172),
  .I0(eccp_0[1]),
  .I1(eccp_1[1]),
  .S0(dff_q_0)
);
MUX2 mux_inst_173 (
  .O(mux_o_173),
  .I0(eccp_2[1]),
  .I1(eccp_3[1]),
  .S0(dff_q_1)
);
MUX2 mux_inst_174 (
  .O(mux_o_174),
  .I0(eccp_4[1]),
  .I1(eccp_5[1]),
  .S0(dff_q_2)
);
MUX2 mux_inst_175 (
  .O(mux_o_175),
  .I0(eccp_6[1]),
  .I1(eccp_7[1]),
  .S0(dff_q_3)
);
MUX2 mux_inst_176 (
  .O(mux_o_176),
  .I0(eccp_0[2]),
  .I1(eccp_1[2]),
  .S0(dff_q_0)
);
MUX2 mux_inst_177 (
  .O(mux_o_177),
  .I0(eccp_2[2]),
  .I1(eccp_3[2]),
  .S0(dff_q_1)
);
MUX2 mux_inst_178 (
  .O(mux_o_178),
  .I0(eccp_4[2]),
  .I1(eccp_5[2]),
  .S0(dff_q_2)
);
MUX2 mux_inst_179 (
  .O(mux_o_179),
  .I0(eccp_6[2]),
  .I1(eccp_7[2]),
  .S0(dff_q_3)
);
MUX2 mux_inst_180 (
  .O(mux_o_180),
  .I0(eccp_0[3]),
  .I1(eccp_1[3]),
  .S0(dff_q_0)
);
MUX2 mux_inst_181 (
  .O(mux_o_181),
  .I0(eccp_2[3]),
  .I1(eccp_3[3]),
  .S0(dff_q_1)
);
MUX2 mux_inst_182 (
  .O(mux_o_182),
  .I0(eccp_4[3]),
  .I1(eccp_5[3]),
  .S0(dff_q_2)
);
MUX2 mux_inst_183 (
  .O(mux_o_183),
  .I0(eccp_6[3]),
  .I1(eccp_7[3]),
  .S0(dff_q_3)
);
MUX2 mux_inst_184 (
  .O(mux_o_184),
  .I0(eccp_0[4]),
  .I1(eccp_1[4]),
  .S0(dff_q_0)
);
MUX2 mux_inst_185 (
  .O(mux_o_185),
  .I0(eccp_2[4]),
  .I1(eccp_3[4]),
  .S0(dff_q_1)
);
MUX2 mux_inst_186 (
  .O(mux_o_186),
  .I0(eccp_4[4]),
  .I1(eccp_5[4]),
  .S0(dff_q_2)
);
MUX2 mux_inst_187 (
  .O(mux_o_187),
  .I0(eccp_6[4]),
  .I1(eccp_7[4]),
  .S0(dff_q_3)
);
MUX2 mux_inst_188 (
  .O(mux_o_188),
  .I0(eccp_0[5]),
  .I1(eccp_1[5]),
  .S0(dff_q_0)
);
MUX2 mux_inst_189 (
  .O(mux_o_189),
  .I0(eccp_2[5]),
  .I1(eccp_3[5]),
  .S0(dff_q_1)
);
MUX2 mux_inst_190 (
  .O(mux_o_190),
  .I0(eccp_4[5]),
  .I1(eccp_5[5]),
  .S0(dff_q_2)
);
MUX2 mux_inst_191 (
  .O(mux_o_191),
  .I0(eccp_6[5]),
  .I1(eccp_7[5]),
  .S0(dff_q_3)
);
MUX2 mux_inst_192 (
  .O(mux_o_192),
  .I0(eccp_0[6]),
  .I1(eccp_1[6]),
  .S0(dff_q_0)
);
MUX2 mux_inst_193 (
  .O(mux_o_193),
  .I0(eccp_2[6]),
  .I1(eccp_3[6]),
  .S0(dff_q_1)
);
MUX2 mux_inst_194 (
  .O(mux_o_194),
  .I0(eccp_4[6]),
  .I1(eccp_5[6]),
  .S0(dff_q_2)
);
MUX2 mux_inst_195 (
  .O(mux_o_195),
  .I0(eccp_6[6]),
  .I1(eccp_7[6]),
  .S0(dff_q_3)
);
MUX2 mux_inst_196 (
  .O(mux_o_196),
  .I0(eccp_0[7]),
  .I1(eccp_1[7]),
  .S0(dff_q_0)
);
MUX2 mux_inst_197 (
  .O(mux_o_197),
  .I0(eccp_2[7]),
  .I1(eccp_3[7]),
  .S0(dff_q_1)
);
MUX2 mux_inst_198 (
  .O(mux_o_198),
  .I0(eccp_4[7]),
  .I1(eccp_5[7]),
  .S0(dff_q_2)
);
MUX2 mux_inst_199 (
  .O(mux_o_199),
  .I0(eccp_6[7]),
  .I1(eccp_7[7]),
  .S0(dff_q_3)
);
MUX2 mux_inst_200 (
  .O(mux_o_200),
  .I0(mux_o_168),
  .I1(mux_o_169),
  .S0(dff_q_76)
);
MUX2 mux_inst_201 (
  .O(mux_o_201),
  .I0(mux_o_170),
  .I1(mux_o_171),
  .S0(dff_q_77)
);
MUX2 mux_inst_202 (
  .O(mux_o_202),
  .I0(mux_o_172),
  .I1(mux_o_173),
  .S0(dff_q_78)
);
MUX2 mux_inst_203 (
  .O(mux_o_203),
  .I0(mux_o_174),
  .I1(mux_o_175),
  .S0(dff_q_79)
);
MUX2 mux_inst_204 (
  .O(mux_o_204),
  .I0(mux_o_176),
  .I1(mux_o_177),
  .S0(dff_q_80)
);
MUX2 mux_inst_205 (
  .O(mux_o_205),
  .I0(mux_o_178),
  .I1(mux_o_179),
  .S0(dff_q_81)
);
MUX2 mux_inst_206 (
  .O(mux_o_206),
  .I0(mux_o_180),
  .I1(mux_o_181),
  .S0(dff_q_82)
);
MUX2 mux_inst_207 (
  .O(mux_o_207),
  .I0(mux_o_182),
  .I1(mux_o_183),
  .S0(dff_q_83)
);
MUX2 mux_inst_208 (
  .O(mux_o_208),
  .I0(mux_o_184),
  .I1(mux_o_185),
  .S0(dff_q_84)
);
MUX2 mux_inst_209 (
  .O(mux_o_209),
  .I0(mux_o_186),
  .I1(mux_o_187),
  .S0(dff_q_85)
);
MUX2 mux_inst_210 (
  .O(mux_o_210),
  .I0(mux_o_188),
  .I1(mux_o_189),
  .S0(dff_q_86)
);
MUX2 mux_inst_211 (
  .O(mux_o_211),
  .I0(mux_o_190),
  .I1(mux_o_191),
  .S0(dff_q_87)
);
MUX2 mux_inst_212 (
  .O(mux_o_212),
  .I0(mux_o_192),
  .I1(mux_o_193),
  .S0(dff_q_88)
);
MUX2 mux_inst_213 (
  .O(mux_o_213),
  .I0(mux_o_194),
  .I1(mux_o_195),
  .S0(dff_q_89)
);
MUX2 mux_inst_214 (
  .O(mux_o_214),
  .I0(mux_o_196),
  .I1(mux_o_197),
  .S0(dff_q_90)
);
MUX2 mux_inst_215 (
  .O(mux_o_215),
  .I0(mux_o_198),
  .I1(mux_o_199),
  .S0(dff_q_91)
);
MUX2 mux_inst_216 (
  .O(eccp[0]),
  .I0(mux_o_200),
  .I1(mux_o_201),
  .S0(dff_q_92)
);
MUX2 mux_inst_217 (
  .O(eccp[1]),
  .I0(mux_o_202),
  .I1(mux_o_203),
  .S0(dff_q_93)
);
MUX2 mux_inst_218 (
  .O(eccp[2]),
  .I0(mux_o_204),
  .I1(mux_o_205),
  .S0(dff_q_94)
);
MUX2 mux_inst_219 (
  .O(eccp[3]),
  .I0(mux_o_206),
  .I1(mux_o_207),
  .S0(dff_q_95)
);
MUX2 mux_inst_220 (
  .O(eccp[4]),
  .I0(mux_o_208),
  .I1(mux_o_209),
  .S0(dff_q_96)
);
MUX2 mux_inst_221 (
  .O(eccp[5]),
  .I0(mux_o_210),
  .I1(mux_o_211),
  .S0(dff_q_97)
);
MUX2 mux_inst_222 (
  .O(eccp[6]),
  .I0(mux_o_212),
  .I1(mux_o_213),
  .S0(dff_q_98)
);
MUX2 mux_inst_223 (
  .O(eccp[7]),
  .I0(mux_o_214),
  .I1(mux_o_215),
  .S0(dff_q_99)
);
endmodule //Gowin_ADSR

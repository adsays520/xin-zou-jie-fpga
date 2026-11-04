//
//Written by GowinSynthesis
//Tool Version "V1.9.12.03 (64-bit)"
//Tue Oct 20 11:29:12 2026

//Source file index table:
//file0 "\C:/Users/Junejay_Huang/Desktop/gowin-2/tmp/ensemble_rom_block_probe_20261020/src/verification/verification_dds.v"
`timescale 100 ps/100 ps
module verification_dds (
  clk,
  rst_n,
  sample_tick,
  running,
  start_event,
  frequencies,
  gains,
  pans,
  sample_l,
  sample_r,
  sample_valid,
  latency_valid,
  deadline_miss,
  latency_cycles,
  active_count
)
;
input clk;
input rst_n;
input sample_tick;
input running;
input start_event;
input [63:0] frequencies;
input [27:0] gains;
input [27:0] pans;
output [23:0] sample_l;
output [23:0] sample_r;
output sample_valid;
output latency_valid;
output deadline_miss;
output [31:0] latency_cycles;
output [2:0] active_count;
wire clk_d;
wire rst_n_d;
wire sample_tick_d;
wire running_d;
wire start_event_d;
wire n3584_4;
wire n3583_3;
wire latency_valid_7;
wire timer_31_8;
wire \sine_q[3]_0_17 ;
wire \sine_q[3]_1_15 ;
wire \sine_q[3]_2_15 ;
wire \sine_q[3]_3_15 ;
wire \sine_q[3]_4_15 ;
wire \sine_q[3]_5_15 ;
wire \sine_q[3]_6_15 ;
wire \sine_q[3]_7_15 ;
wire \sine_q[3]_8_15 ;
wire \sine_q[3]_9_15 ;
wire \sine_q[3]_10_15 ;
wire \sine_q[3]_11_15 ;
wire \sine_q[3]_12_15 ;
wire \sine_q[3]_13_15 ;
wire \sine_q[3]_14_15 ;
wire \sine_q[3]_15_15 ;
wire \sine_q[2]_0_15 ;
wire \sine_q[2]_1_15 ;
wire \sine_q[2]_2_15 ;
wire \sine_q[2]_3_15 ;
wire \sine_q[2]_4_15 ;
wire \sine_q[2]_5_15 ;
wire \sine_q[2]_6_15 ;
wire \sine_q[2]_7_15 ;
wire \sine_q[2]_8_15 ;
wire \sine_q[2]_9_15 ;
wire \sine_q[2]_10_15 ;
wire \sine_q[2]_11_15 ;
wire \sine_q[2]_12_15 ;
wire \sine_q[2]_13_15 ;
wire \sine_q[2]_14_15 ;
wire \sine_q[2]_15_15 ;
wire \sine_q[1]_0_15 ;
wire \sine_q[1]_1_15 ;
wire \sine_q[1]_2_15 ;
wire \sine_q[1]_3_15 ;
wire \sine_q[1]_4_15 ;
wire \sine_q[1]_5_15 ;
wire \sine_q[1]_6_15 ;
wire \sine_q[1]_7_15 ;
wire \sine_q[1]_8_15 ;
wire \sine_q[1]_9_15 ;
wire \sine_q[1]_10_15 ;
wire \sine_q[1]_11_15 ;
wire \sine_q[1]_12_15 ;
wire \sine_q[1]_13_15 ;
wire \sine_q[1]_14_15 ;
wire \sine_q[1]_15_15 ;
wire \sine_q[0]_0_15 ;
wire \sine_q[0]_1_15 ;
wire \sine_q[0]_2_15 ;
wire \sine_q[0]_3_15 ;
wire \sine_q[0]_4_15 ;
wire \sine_q[0]_5_15 ;
wire \sine_q[0]_6_15 ;
wire \sine_q[0]_7_15 ;
wire \sine_q[0]_8_15 ;
wire \sine_q[0]_9_15 ;
wire \sine_q[0]_10_15 ;
wire \sine_q[0]_11_15 ;
wire \sine_q[0]_12_15 ;
wire \sine_q[0]_13_15 ;
wire \sine_q[0]_14_15 ;
wire \sine_q[0]_15_15 ;
wire n331_8;
wire n330_7;
wire n329_7;
wire n328_7;
wire n327_7;
wire n326_7;
wire n325_7;
wire n324_7;
wire n322_7;
wire n321_7;
wire n320_7;
wire n319_7;
wire n318_7;
wire n317_7;
wire n316_7;
wire n315_7;
wire n314_7;
wire n313_7;
wire n312_7;
wire n311_7;
wire n310_7;
wire n309_7;
wire n308_7;
wire n307_7;
wire n306_7;
wire n305_7;
wire n304_7;
wire n303_7;
wire n302_7;
wire n301_7;
wire n300_7;
wire n533_6;
wire n534_6;
wire n535_6;
wire n536_6;
wire n537_6;
wire n538_6;
wire n539_6;
wire n540_6;
wire n541_6;
wire n542_6;
wire n543_6;
wire n544_6;
wire n545_6;
wire n546_6;
wire n547_6;
wire n548_6;
wire n549_6;
wire n550_6;
wire n551_6;
wire n552_6;
wire n553_6;
wire n554_6;
wire n555_6;
wire n556_6;
wire n557_6;
wire n558_6;
wire n559_6;
wire n560_6;
wire n561_6;
wire n562_6;
wire n563_6;
wire n564_6;
wire n630_6;
wire n631_6;
wire n632_6;
wire n633_6;
wire n634_6;
wire n635_6;
wire n636_6;
wire n637_6;
wire n638_6;
wire n639_6;
wire n640_6;
wire n641_6;
wire n642_6;
wire n643_6;
wire n644_6;
wire n645_6;
wire n646_6;
wire n647_6;
wire n648_6;
wire n649_6;
wire n650_6;
wire n651_6;
wire n652_6;
wire n653_6;
wire n654_6;
wire n655_6;
wire n656_6;
wire n657_6;
wire n658_6;
wire n659_6;
wire n660_6;
wire n661_6;
wire n727_6;
wire n728_6;
wire n729_6;
wire n730_6;
wire n731_6;
wire n732_6;
wire n733_6;
wire n734_6;
wire n735_6;
wire n736_6;
wire n737_6;
wire n738_6;
wire n739_6;
wire n740_6;
wire n741_6;
wire n742_6;
wire n743_6;
wire n744_6;
wire n745_6;
wire n746_6;
wire n747_6;
wire n748_6;
wire n749_6;
wire n750_6;
wire n751_6;
wire n752_6;
wire n753_6;
wire n754_6;
wire n755_6;
wire n756_6;
wire n757_6;
wire n758_6;
wire n824_6;
wire n825_6;
wire n826_6;
wire n827_6;
wire n828_6;
wire n829_6;
wire n830_6;
wire n831_6;
wire n832_6;
wire n833_6;
wire n834_6;
wire n835_6;
wire n836_6;
wire n837_6;
wire n838_6;
wire n839_6;
wire n840_6;
wire n841_6;
wire n842_6;
wire n843_6;
wire n844_6;
wire n845_6;
wire n846_6;
wire n847_6;
wire n848_6;
wire n849_6;
wire n850_6;
wire n851_6;
wire n852_6;
wire n853_6;
wire n854_6;
wire n855_6;
wire n887_6;
wire n886_6;
wire n885_6;
wire n884_6;
wire n883_6;
wire n882_6;
wire n881_6;
wire n880_6;
wire n879_6;
wire n878_6;
wire n877_6;
wire n876_6;
wire n875_6;
wire n874_6;
wire n873_6;
wire n872_6;
wire n790_6;
wire n789_6;
wire n788_6;
wire n787_6;
wire n786_6;
wire n785_6;
wire n784_6;
wire n783_6;
wire n782_6;
wire n781_6;
wire n780_6;
wire n779_6;
wire n778_6;
wire n777_6;
wire n776_6;
wire n775_6;
wire n693_6;
wire n692_6;
wire n691_6;
wire n690_6;
wire n689_6;
wire n688_6;
wire n687_6;
wire n686_6;
wire n685_6;
wire n684_6;
wire n683_6;
wire n682_6;
wire n681_6;
wire n680_6;
wire n679_6;
wire n678_6;
wire n596_6;
wire n595_6;
wire n594_6;
wire n593_6;
wire n592_6;
wire n591_6;
wire n590_6;
wire n589_6;
wire n588_6;
wire n587_6;
wire n586_6;
wire n585_6;
wire n584_6;
wire n583_6;
wire n582_6;
wire n581_6;
wire n3584_5;
wire n3584_6;
wire n3584_7;
wire n3584_8;
wire n3583_4;
wire timer_31_10;
wire n328_8;
wire n327_8;
wire n325_8;
wire n324_8;
wire n323_8;
wire n321_8;
wire n318_8;
wire n316_8;
wire n313_8;
wire n312_8;
wire n311_8;
wire n309_8;
wire n308_8;
wire n307_8;
wire n305_8;
wire n301_8;
wire active_count_d_2_5;
wire active_count_d_1_5;
wire active_count_d_1_6;
wire active_count_d_0_5;
wire active_count_d_0_6;
wire active_count_d_0_7;
wire n3584_9;
wire n3584_10;
wire n3584_11;
wire n3584_12;
wire n3584_13;
wire n3584_14;
wire n3584_15;
wire n3584_16;
wire n3584_17;
wire n3584_18;
wire n3584_19;
wire timer_31_11;
wire timer_31_12;
wire n323_9;
wire n318_9;
wire active_count_d_2_6;
wire active_count_d_2_7;
wire active_count_d_0_8;
wire active_count_d_0_9;
wire active_count_d_2_8;
wire active_count_d_2_9;
wire n320_10;
wire n300_10;
wire timer_31_14;
wire n304_10;
wire n315_10;
wire n323_11;
wire n364_9;
wire sample_valid_d;
wire deadline_miss_d;
wire latency_valid_d;
wire measuring;
wire \sine_q[3]_0_6 ;
wire \sine_q[3]_0_21 ;
wire \sine_q[3]_0_19 ;
wire n871_3;
wire \sine_q[3]_1_17 ;
wire \sine_q[3]_2_17 ;
wire \sine_q[3]_3_17 ;
wire \sine_q[3]_4_17 ;
wire \sine_q[3]_5_17 ;
wire \sine_q[3]_6_17 ;
wire \sine_q[3]_7_17 ;
wire \sine_q[3]_8_17 ;
wire \sine_q[3]_9_17 ;
wire \sine_q[3]_10_17 ;
wire \sine_q[3]_11_17 ;
wire \sine_q[3]_12_17 ;
wire \sine_q[3]_13_17 ;
wire \sine_q[3]_14_17 ;
wire \sine_q[3]_15_17 ;
wire \sine_q[2]_0_17 ;
wire \sine_q[2]_1_17 ;
wire \sine_q[2]_2_17 ;
wire \sine_q[2]_3_17 ;
wire \sine_q[2]_4_17 ;
wire \sine_q[2]_5_17 ;
wire \sine_q[2]_6_17 ;
wire \sine_q[2]_7_17 ;
wire \sine_q[2]_8_17 ;
wire \sine_q[2]_9_17 ;
wire \sine_q[2]_10_17 ;
wire \sine_q[2]_11_17 ;
wire \sine_q[2]_12_17 ;
wire \sine_q[2]_13_17 ;
wire \sine_q[2]_14_17 ;
wire \sine_q[2]_15_17 ;
wire \sine_q[1]_0_17 ;
wire \sine_q[1]_1_17 ;
wire \sine_q[1]_2_17 ;
wire \sine_q[1]_3_17 ;
wire \sine_q[1]_4_17 ;
wire \sine_q[1]_5_17 ;
wire \sine_q[1]_6_17 ;
wire \sine_q[1]_7_17 ;
wire \sine_q[1]_8_17 ;
wire \sine_q[1]_9_17 ;
wire \sine_q[1]_10_17 ;
wire \sine_q[1]_11_17 ;
wire \sine_q[1]_12_17 ;
wire \sine_q[1]_13_17 ;
wire \sine_q[1]_14_17 ;
wire \sine_q[1]_15_17 ;
wire \sine_q[0]_0_17 ;
wire \sine_q[0]_1_17 ;
wire \sine_q[0]_2_17 ;
wire \sine_q[0]_3_17 ;
wire \sine_q[0]_4_17 ;
wire \sine_q[0]_5_17 ;
wire \sine_q[0]_6_17 ;
wire \sine_q[0]_7_17 ;
wire \sine_q[0]_8_17 ;
wire \sine_q[0]_9_17 ;
wire \sine_q[0]_10_17 ;
wire \sine_q[0]_11_17 ;
wire \sine_q[0]_12_17 ;
wire \sine_q[0]_13_17 ;
wire \sine_q[0]_14_17 ;
wire \sine_q[0]_15_17 ;
wire n1081_2;
wire n1082_1;
wire n1083_1;
wire n1084_1;
wire n1085_1;
wire n1086_1;
wire n1087_1;
wire n1088_1;
wire n1089_1;
wire n1090_1;
wire n1091_1;
wire n1092_1;
wire n1093_1;
wire n1094_1;
wire n1095_1;
wire n1096_1;
wire n1097_1;
wire n1098_1;
wire n1099_1;
wire n1100_1;
wire n1101_1;
wire n1102_1;
wire n1103_1;
wire n1104_2;
wire n1105_2;
wire n1106_1;
wire n1107_1;
wire n1108_1;
wire n1109_1;
wire n1110_1;
wire n1111_1;
wire n1112_1;
wire n1113_1;
wire n1114_1;
wire n1115_1;
wire n1116_1;
wire n1117_1;
wire n1118_1;
wire n1119_1;
wire n1120_1;
wire n1121_1;
wire n1122_1;
wire n1123_1;
wire n1124_1;
wire n1125_1;
wire n1126_1;
wire n1127_1;
wire n1128_2;
wire n1129_2;
wire n1130_1;
wire n1131_1;
wire n1132_1;
wire n1133_1;
wire n1134_1;
wire n1135_1;
wire n1136_1;
wire n1137_1;
wire n1138_1;
wire n1139_1;
wire n1140_1;
wire n1141_1;
wire n1142_1;
wire n1143_1;
wire n1144_1;
wire n1145_1;
wire n1146_1;
wire n1147_1;
wire n1148_1;
wire n1149_1;
wire n1150_1;
wire n1151_1;
wire n1152_2;
wire n1153_2;
wire n1154_1;
wire n1155_1;
wire n1156_1;
wire n1157_1;
wire n1158_1;
wire n1159_1;
wire n1160_1;
wire n1161_1;
wire n1162_1;
wire n1163_1;
wire n1164_1;
wire n1165_1;
wire n1166_1;
wire n1167_1;
wire n1168_1;
wire n1169_1;
wire n1170_1;
wire n1171_1;
wire n1172_1;
wire n1173_1;
wire n1174_1;
wire n1175_1;
wire n1176_2;
wire n501_1;
wire n502_1;
wire n503_1;
wire n504_1;
wire n505_1;
wire n506_1;
wire n507_1;
wire n508_1;
wire n509_1;
wire n510_1;
wire n511_1;
wire n512_1;
wire n513_1;
wire n514_1;
wire n515_1;
wire n516_1;
wire n517_1;
wire n518_1;
wire n519_1;
wire n520_1;
wire n521_1;
wire n522_1;
wire n523_1;
wire n524_1;
wire n525_1;
wire n526_1;
wire n527_1;
wire n528_1;
wire n529_1;
wire n530_1;
wire n531_1;
wire n532_1;
wire n598_1;
wire n599_1;
wire n600_1;
wire n601_1;
wire n602_1;
wire n603_1;
wire n604_1;
wire n605_1;
wire n606_1;
wire n607_1;
wire n608_1;
wire n609_1;
wire n610_1;
wire n611_1;
wire n612_1;
wire n613_1;
wire n614_1;
wire n615_1;
wire n616_1;
wire n617_1;
wire n618_1;
wire n619_1;
wire n620_1;
wire n621_1;
wire n622_1;
wire n623_1;
wire n624_1;
wire n625_1;
wire n626_1;
wire n627_1;
wire n628_1;
wire n629_1;
wire n695_1;
wire n696_1;
wire n697_1;
wire n698_1;
wire n699_1;
wire n700_1;
wire n701_1;
wire n702_1;
wire n703_1;
wire n704_1;
wire n705_1;
wire n706_1;
wire n707_1;
wire n708_1;
wire n709_1;
wire n710_1;
wire n711_1;
wire n712_1;
wire n713_1;
wire n714_1;
wire n715_1;
wire n716_1;
wire n717_1;
wire n718_1;
wire n719_1;
wire n720_1;
wire n721_1;
wire n722_1;
wire n723_1;
wire n724_1;
wire n725_1;
wire n726_1;
wire n792_1;
wire n793_1;
wire n794_1;
wire n795_1;
wire n796_1;
wire n797_1;
wire n798_1;
wire n799_1;
wire n800_1;
wire n801_1;
wire n802_1;
wire n803_1;
wire n804_1;
wire n805_1;
wire n806_1;
wire n807_1;
wire n808_1;
wire n809_1;
wire n810_1;
wire n811_1;
wire n812_1;
wire n813_1;
wire n814_1;
wire n815_1;
wire n816_1;
wire n817_1;
wire n818_1;
wire n819_1;
wire n820_1;
wire n821_1;
wire n822_1;
wire n823_1;
wire mix_l_0_2;
wire mix_l_0_3;
wire mix_l_1_2;
wire mix_l_1_3;
wire mix_l_2_2;
wire mix_l_2_3;
wire mix_l_3_2;
wire mix_l_3_3;
wire mix_l_4_2;
wire mix_l_4_3;
wire mix_l_5_2;
wire mix_l_5_3;
wire mix_l_6_2;
wire mix_l_6_3;
wire mix_l_7_2;
wire mix_l_7_3;
wire mix_l_8_2;
wire mix_l_8_3;
wire mix_l_9_2;
wire mix_l_9_3;
wire mix_l_10_2;
wire mix_l_10_3;
wire mix_l_11_2;
wire mix_l_11_3;
wire mix_l_12_2;
wire mix_l_12_3;
wire mix_l_13_2;
wire mix_l_13_3;
wire mix_l_14_2;
wire mix_l_14_3;
wire mix_l_15_2;
wire mix_l_15_3;
wire mix_l_16_2;
wire mix_l_16_3;
wire mix_l_17_2;
wire mix_l_17_3;
wire mix_l_18_2;
wire mix_l_18_3;
wire mix_l_19_2;
wire mix_l_19_3;
wire mix_l_33_2;
wire mix_l_33_0_COUT;
wire mix_l_0_4;
wire mix_l_0_5;
wire mix_l_1_4;
wire mix_l_1_5;
wire mix_l_2_4;
wire mix_l_2_5;
wire mix_l_3_4;
wire mix_l_3_5;
wire mix_l_4_4;
wire mix_l_4_5;
wire mix_l_5_4;
wire mix_l_5_5;
wire mix_l_6_4;
wire mix_l_6_5;
wire mix_l_7_4;
wire mix_l_7_5;
wire mix_l_8_4;
wire mix_l_8_5;
wire mix_l_9_4;
wire mix_l_9_5;
wire mix_l_10_4;
wire mix_l_10_5;
wire mix_l_11_4;
wire mix_l_11_5;
wire mix_l_12_4;
wire mix_l_12_5;
wire mix_l_13_4;
wire mix_l_13_5;
wire mix_l_14_4;
wire mix_l_14_5;
wire mix_l_15_4;
wire mix_l_15_5;
wire mix_l_16_4;
wire mix_l_16_5;
wire mix_l_17_4;
wire mix_l_17_5;
wire mix_l_18_4;
wire mix_l_18_5;
wire mix_l_19_4;
wire mix_l_19_5;
wire mix_l_33_4;
wire mix_l_33_1_COUT;
wire mix_l_0_7;
wire mix_l_1_7;
wire mix_l_2_7;
wire mix_l_3_7;
wire mix_l_4_7;
wire mix_l_5_7;
wire mix_l_6_7;
wire mix_l_7_7;
wire mix_l_8_7;
wire mix_l_9_7;
wire mix_l_10_7;
wire mix_l_11_7;
wire mix_l_12_7;
wire mix_l_13_7;
wire mix_l_14_7;
wire mix_l_15_7;
wire mix_l_16_7;
wire mix_l_17_7;
wire mix_l_18_7;
wire mix_l_19_7;
wire mix_l_33_2_COUT;
wire mix_r_0_2;
wire mix_r_0_3;
wire mix_r_1_2;
wire mix_r_1_3;
wire mix_r_2_2;
wire mix_r_2_3;
wire mix_r_3_2;
wire mix_r_3_3;
wire mix_r_4_2;
wire mix_r_4_3;
wire mix_r_5_2;
wire mix_r_5_3;
wire mix_r_6_2;
wire mix_r_6_3;
wire mix_r_7_2;
wire mix_r_7_3;
wire mix_r_8_2;
wire mix_r_8_3;
wire mix_r_9_2;
wire mix_r_9_3;
wire mix_r_10_2;
wire mix_r_10_3;
wire mix_r_11_2;
wire mix_r_11_3;
wire mix_r_12_2;
wire mix_r_12_3;
wire mix_r_13_2;
wire mix_r_13_3;
wire mix_r_14_2;
wire mix_r_14_3;
wire mix_r_15_2;
wire mix_r_15_3;
wire mix_r_16_2;
wire mix_r_16_3;
wire mix_r_17_2;
wire mix_r_17_3;
wire mix_r_18_2;
wire mix_r_18_3;
wire mix_r_19_2;
wire mix_r_19_3;
wire mix_r_33_2;
wire mix_r_33_0_COUT;
wire mix_r_0_4;
wire mix_r_0_5;
wire mix_r_1_4;
wire mix_r_1_5;
wire mix_r_2_4;
wire mix_r_2_5;
wire mix_r_3_4;
wire mix_r_3_5;
wire mix_r_4_4;
wire mix_r_4_5;
wire mix_r_5_4;
wire mix_r_5_5;
wire mix_r_6_4;
wire mix_r_6_5;
wire mix_r_7_4;
wire mix_r_7_5;
wire mix_r_8_4;
wire mix_r_8_5;
wire mix_r_9_4;
wire mix_r_9_5;
wire mix_r_10_4;
wire mix_r_10_5;
wire mix_r_11_4;
wire mix_r_11_5;
wire mix_r_12_4;
wire mix_r_12_5;
wire mix_r_13_4;
wire mix_r_13_5;
wire mix_r_14_4;
wire mix_r_14_5;
wire mix_r_15_4;
wire mix_r_15_5;
wire mix_r_16_4;
wire mix_r_16_5;
wire mix_r_17_4;
wire mix_r_17_5;
wire mix_r_18_4;
wire mix_r_18_5;
wire mix_r_19_4;
wire mix_r_19_5;
wire mix_r_33_4;
wire mix_r_33_1_COUT;
wire mix_r_0_7;
wire mix_r_1_7;
wire mix_r_2_7;
wire mix_r_3_7;
wire mix_r_4_7;
wire mix_r_5_7;
wire mix_r_6_7;
wire mix_r_7_7;
wire mix_r_8_7;
wire mix_r_9_7;
wire mix_r_10_7;
wire mix_r_11_7;
wire mix_r_12_7;
wire mix_r_13_7;
wire mix_r_14_7;
wire mix_r_15_7;
wire mix_r_16_7;
wire mix_r_17_7;
wire mix_r_18_7;
wire mix_r_19_7;
wire mix_r_33_2_COUT;
wire n232_6;
wire n1273_6;
wire n1274_6;
wire n1275_6;
wire n1276_6;
wire n1277_6;
wire n1278_6;
wire n1279_6;
wire n1344_6;
wire n1345_6;
wire n1346_6;
wire n1347_6;
wire n1348_6;
wire n1349_6;
wire n1350_6;
wire n1415_6;
wire n1416_6;
wire n1417_6;
wire n1418_6;
wire n1419_6;
wire n1420_6;
wire n1421_6;
wire n1486_6;
wire n1487_6;
wire n1488_6;
wire n1489_6;
wire n1490_6;
wire n1491_6;
wire n1492_6;
wire [63:0] frequencies_d;
wire [27:0] gains_d;
wire [27:0] pans_d;
wire [2:0] active_count_d;
wire [23:8] sample_l_d;
wire [23:8] sample_r_d;
wire [2:0] valid_pipe;
wire [31:0] latency_cycles_d;
wire [31:22] \phase[0] ;
wire [31:22] \phase[1] ;
wire [31:22] \phase[2] ;
wire [31:22] \phase[3] ;
wire [31:0] timer;
wire [15:0] \sine_q[0] ;
wire [15:0] \sine_q[1] ;
wire [15:0] \sine_q[2] ;
wire [15:0] \sine_q[3] ;
wire [31:14] \left_q[0] ;
wire [26:0] n13110;
wire [31:14] \right_q[0] ;
wire [31:14] \left_q[1] ;
wire [26:0] n13820;
wire [31:14] \right_q[1] ;
wire [31:14] \left_q[2] ;
wire [26:0] n14530;
wire [31:14] \right_q[2] ;
wire [31:14] \left_q[3] ;
wire [26:0] n15240;
wire [31:14] \right_q[3] ;
wire [33:0] mix_l;
wire [33:0] mix_r;
wire [31:16] DO;
wire [31:16] DO_0;
wire [31:16] DO_1;
wire [31:16] DO_2;
wire [47:24] DOUT;
wire [47:0] CASO;
wire [26:0] SOA;
wire [47:24] DOUT_0;
wire [47:0] CASO_0;
wire [26:0] SOA_0;
wire [47:24] DOUT_1;
wire [47:0] CASO_1;
wire [26:0] SOA_1;
wire [47:24] DOUT_2;
wire [47:0] CASO_2;
wire [26:0] SOA_2;
wire [47:0] DOUT_3;
wire [47:0] CASO_3;
wire [47:0] DOUT_4;
wire [47:0] CASO_4;
wire [26:0] SOA_3;
wire [47:0] DOUT_5;
wire [47:0] CASO_5;
wire [47:0] DOUT_6;
wire [47:0] CASO_6;
wire [26:0] SOA_4;
wire [47:0] DOUT_7;
wire [47:0] CASO_7;
wire [47:0] DOUT_8;
wire [47:0] CASO_8;
wire [26:0] SOA_5;
wire [47:0] DOUT_9;
wire [47:0] CASO_9;
wire [47:0] DOUT_10;
wire [47:0] CASO_10;
wire [26:0] SOA_6;
wire [47:32] DOUT_11;
wire [47:0] CASO_11;
wire [26:0] SOA_7;
wire [47:32] DOUT_12;
wire [47:0] CASO_12;
wire [26:0] SOA_8;
wire [47:32] DOUT_13;
wire [47:0] CASO_13;
wire [26:0] SOA_9;
wire [47:32] DOUT_14;
wire [47:0] CASO_14;
wire [26:0] SOA_10;
wire VCC;
wire GND;
  IBUF clk_ibuf (
    .O(clk_d),
    .I(clk) 
);
  IBUF rst_n_ibuf (
    .O(rst_n_d),
    .I(rst_n) 
);
  IBUF sample_tick_ibuf (
    .O(sample_tick_d),
    .I(sample_tick) 
);
  IBUF running_ibuf (
    .O(running_d),
    .I(running) 
);
  IBUF start_event_ibuf (
    .O(start_event_d),
    .I(start_event) 
);
  IBUF frequencies_0_ibuf (
    .O(frequencies_d[0]),
    .I(frequencies[0]) 
);
  IBUF frequencies_1_ibuf (
    .O(frequencies_d[1]),
    .I(frequencies[1]) 
);
  IBUF frequencies_2_ibuf (
    .O(frequencies_d[2]),
    .I(frequencies[2]) 
);
  IBUF frequencies_3_ibuf (
    .O(frequencies_d[3]),
    .I(frequencies[3]) 
);
  IBUF frequencies_4_ibuf (
    .O(frequencies_d[4]),
    .I(frequencies[4]) 
);
  IBUF frequencies_5_ibuf (
    .O(frequencies_d[5]),
    .I(frequencies[5]) 
);
  IBUF frequencies_6_ibuf (
    .O(frequencies_d[6]),
    .I(frequencies[6]) 
);
  IBUF frequencies_7_ibuf (
    .O(frequencies_d[7]),
    .I(frequencies[7]) 
);
  IBUF frequencies_8_ibuf (
    .O(frequencies_d[8]),
    .I(frequencies[8]) 
);
  IBUF frequencies_9_ibuf (
    .O(frequencies_d[9]),
    .I(frequencies[9]) 
);
  IBUF frequencies_10_ibuf (
    .O(frequencies_d[10]),
    .I(frequencies[10]) 
);
  IBUF frequencies_11_ibuf (
    .O(frequencies_d[11]),
    .I(frequencies[11]) 
);
  IBUF frequencies_12_ibuf (
    .O(frequencies_d[12]),
    .I(frequencies[12]) 
);
  IBUF frequencies_13_ibuf (
    .O(frequencies_d[13]),
    .I(frequencies[13]) 
);
  IBUF frequencies_14_ibuf (
    .O(frequencies_d[14]),
    .I(frequencies[14]) 
);
  IBUF frequencies_15_ibuf (
    .O(frequencies_d[15]),
    .I(frequencies[15]) 
);
  IBUF frequencies_16_ibuf (
    .O(frequencies_d[16]),
    .I(frequencies[16]) 
);
  IBUF frequencies_17_ibuf (
    .O(frequencies_d[17]),
    .I(frequencies[17]) 
);
  IBUF frequencies_18_ibuf (
    .O(frequencies_d[18]),
    .I(frequencies[18]) 
);
  IBUF frequencies_19_ibuf (
    .O(frequencies_d[19]),
    .I(frequencies[19]) 
);
  IBUF frequencies_20_ibuf (
    .O(frequencies_d[20]),
    .I(frequencies[20]) 
);
  IBUF frequencies_21_ibuf (
    .O(frequencies_d[21]),
    .I(frequencies[21]) 
);
  IBUF frequencies_22_ibuf (
    .O(frequencies_d[22]),
    .I(frequencies[22]) 
);
  IBUF frequencies_23_ibuf (
    .O(frequencies_d[23]),
    .I(frequencies[23]) 
);
  IBUF frequencies_24_ibuf (
    .O(frequencies_d[24]),
    .I(frequencies[24]) 
);
  IBUF frequencies_25_ibuf (
    .O(frequencies_d[25]),
    .I(frequencies[25]) 
);
  IBUF frequencies_26_ibuf (
    .O(frequencies_d[26]),
    .I(frequencies[26]) 
);
  IBUF frequencies_27_ibuf (
    .O(frequencies_d[27]),
    .I(frequencies[27]) 
);
  IBUF frequencies_28_ibuf (
    .O(frequencies_d[28]),
    .I(frequencies[28]) 
);
  IBUF frequencies_29_ibuf (
    .O(frequencies_d[29]),
    .I(frequencies[29]) 
);
  IBUF frequencies_30_ibuf (
    .O(frequencies_d[30]),
    .I(frequencies[30]) 
);
  IBUF frequencies_31_ibuf (
    .O(frequencies_d[31]),
    .I(frequencies[31]) 
);
  IBUF frequencies_32_ibuf (
    .O(frequencies_d[32]),
    .I(frequencies[32]) 
);
  IBUF frequencies_33_ibuf (
    .O(frequencies_d[33]),
    .I(frequencies[33]) 
);
  IBUF frequencies_34_ibuf (
    .O(frequencies_d[34]),
    .I(frequencies[34]) 
);
  IBUF frequencies_35_ibuf (
    .O(frequencies_d[35]),
    .I(frequencies[35]) 
);
  IBUF frequencies_36_ibuf (
    .O(frequencies_d[36]),
    .I(frequencies[36]) 
);
  IBUF frequencies_37_ibuf (
    .O(frequencies_d[37]),
    .I(frequencies[37]) 
);
  IBUF frequencies_38_ibuf (
    .O(frequencies_d[38]),
    .I(frequencies[38]) 
);
  IBUF frequencies_39_ibuf (
    .O(frequencies_d[39]),
    .I(frequencies[39]) 
);
  IBUF frequencies_40_ibuf (
    .O(frequencies_d[40]),
    .I(frequencies[40]) 
);
  IBUF frequencies_41_ibuf (
    .O(frequencies_d[41]),
    .I(frequencies[41]) 
);
  IBUF frequencies_42_ibuf (
    .O(frequencies_d[42]),
    .I(frequencies[42]) 
);
  IBUF frequencies_43_ibuf (
    .O(frequencies_d[43]),
    .I(frequencies[43]) 
);
  IBUF frequencies_44_ibuf (
    .O(frequencies_d[44]),
    .I(frequencies[44]) 
);
  IBUF frequencies_45_ibuf (
    .O(frequencies_d[45]),
    .I(frequencies[45]) 
);
  IBUF frequencies_46_ibuf (
    .O(frequencies_d[46]),
    .I(frequencies[46]) 
);
  IBUF frequencies_47_ibuf (
    .O(frequencies_d[47]),
    .I(frequencies[47]) 
);
  IBUF frequencies_48_ibuf (
    .O(frequencies_d[48]),
    .I(frequencies[48]) 
);
  IBUF frequencies_49_ibuf (
    .O(frequencies_d[49]),
    .I(frequencies[49]) 
);
  IBUF frequencies_50_ibuf (
    .O(frequencies_d[50]),
    .I(frequencies[50]) 
);
  IBUF frequencies_51_ibuf (
    .O(frequencies_d[51]),
    .I(frequencies[51]) 
);
  IBUF frequencies_52_ibuf (
    .O(frequencies_d[52]),
    .I(frequencies[52]) 
);
  IBUF frequencies_53_ibuf (
    .O(frequencies_d[53]),
    .I(frequencies[53]) 
);
  IBUF frequencies_54_ibuf (
    .O(frequencies_d[54]),
    .I(frequencies[54]) 
);
  IBUF frequencies_55_ibuf (
    .O(frequencies_d[55]),
    .I(frequencies[55]) 
);
  IBUF frequencies_56_ibuf (
    .O(frequencies_d[56]),
    .I(frequencies[56]) 
);
  IBUF frequencies_57_ibuf (
    .O(frequencies_d[57]),
    .I(frequencies[57]) 
);
  IBUF frequencies_58_ibuf (
    .O(frequencies_d[58]),
    .I(frequencies[58]) 
);
  IBUF frequencies_59_ibuf (
    .O(frequencies_d[59]),
    .I(frequencies[59]) 
);
  IBUF frequencies_60_ibuf (
    .O(frequencies_d[60]),
    .I(frequencies[60]) 
);
  IBUF frequencies_61_ibuf (
    .O(frequencies_d[61]),
    .I(frequencies[61]) 
);
  IBUF frequencies_62_ibuf (
    .O(frequencies_d[62]),
    .I(frequencies[62]) 
);
  IBUF frequencies_63_ibuf (
    .O(frequencies_d[63]),
    .I(frequencies[63]) 
);
  IBUF gains_0_ibuf (
    .O(gains_d[0]),
    .I(gains[0]) 
);
  IBUF gains_1_ibuf (
    .O(gains_d[1]),
    .I(gains[1]) 
);
  IBUF gains_2_ibuf (
    .O(gains_d[2]),
    .I(gains[2]) 
);
  IBUF gains_3_ibuf (
    .O(gains_d[3]),
    .I(gains[3]) 
);
  IBUF gains_4_ibuf (
    .O(gains_d[4]),
    .I(gains[4]) 
);
  IBUF gains_5_ibuf (
    .O(gains_d[5]),
    .I(gains[5]) 
);
  IBUF gains_6_ibuf (
    .O(gains_d[6]),
    .I(gains[6]) 
);
  IBUF gains_7_ibuf (
    .O(gains_d[7]),
    .I(gains[7]) 
);
  IBUF gains_8_ibuf (
    .O(gains_d[8]),
    .I(gains[8]) 
);
  IBUF gains_9_ibuf (
    .O(gains_d[9]),
    .I(gains[9]) 
);
  IBUF gains_10_ibuf (
    .O(gains_d[10]),
    .I(gains[10]) 
);
  IBUF gains_11_ibuf (
    .O(gains_d[11]),
    .I(gains[11]) 
);
  IBUF gains_12_ibuf (
    .O(gains_d[12]),
    .I(gains[12]) 
);
  IBUF gains_13_ibuf (
    .O(gains_d[13]),
    .I(gains[13]) 
);
  IBUF gains_14_ibuf (
    .O(gains_d[14]),
    .I(gains[14]) 
);
  IBUF gains_15_ibuf (
    .O(gains_d[15]),
    .I(gains[15]) 
);
  IBUF gains_16_ibuf (
    .O(gains_d[16]),
    .I(gains[16]) 
);
  IBUF gains_17_ibuf (
    .O(gains_d[17]),
    .I(gains[17]) 
);
  IBUF gains_18_ibuf (
    .O(gains_d[18]),
    .I(gains[18]) 
);
  IBUF gains_19_ibuf (
    .O(gains_d[19]),
    .I(gains[19]) 
);
  IBUF gains_20_ibuf (
    .O(gains_d[20]),
    .I(gains[20]) 
);
  IBUF gains_21_ibuf (
    .O(gains_d[21]),
    .I(gains[21]) 
);
  IBUF gains_22_ibuf (
    .O(gains_d[22]),
    .I(gains[22]) 
);
  IBUF gains_23_ibuf (
    .O(gains_d[23]),
    .I(gains[23]) 
);
  IBUF gains_24_ibuf (
    .O(gains_d[24]),
    .I(gains[24]) 
);
  IBUF gains_25_ibuf (
    .O(gains_d[25]),
    .I(gains[25]) 
);
  IBUF gains_26_ibuf (
    .O(gains_d[26]),
    .I(gains[26]) 
);
  IBUF gains_27_ibuf (
    .O(gains_d[27]),
    .I(gains[27]) 
);
  IBUF pans_0_ibuf (
    .O(pans_d[0]),
    .I(pans[0]) 
);
  IBUF pans_1_ibuf (
    .O(pans_d[1]),
    .I(pans[1]) 
);
  IBUF pans_2_ibuf (
    .O(pans_d[2]),
    .I(pans[2]) 
);
  IBUF pans_3_ibuf (
    .O(pans_d[3]),
    .I(pans[3]) 
);
  IBUF pans_4_ibuf (
    .O(pans_d[4]),
    .I(pans[4]) 
);
  IBUF pans_5_ibuf (
    .O(pans_d[5]),
    .I(pans[5]) 
);
  IBUF pans_6_ibuf (
    .O(pans_d[6]),
    .I(pans[6]) 
);
  IBUF pans_7_ibuf (
    .O(pans_d[7]),
    .I(pans[7]) 
);
  IBUF pans_8_ibuf (
    .O(pans_d[8]),
    .I(pans[8]) 
);
  IBUF pans_9_ibuf (
    .O(pans_d[9]),
    .I(pans[9]) 
);
  IBUF pans_10_ibuf (
    .O(pans_d[10]),
    .I(pans[10]) 
);
  IBUF pans_11_ibuf (
    .O(pans_d[11]),
    .I(pans[11]) 
);
  IBUF pans_12_ibuf (
    .O(pans_d[12]),
    .I(pans[12]) 
);
  IBUF pans_13_ibuf (
    .O(pans_d[13]),
    .I(pans[13]) 
);
  IBUF pans_14_ibuf (
    .O(pans_d[14]),
    .I(pans[14]) 
);
  IBUF pans_15_ibuf (
    .O(pans_d[15]),
    .I(pans[15]) 
);
  IBUF pans_16_ibuf (
    .O(pans_d[16]),
    .I(pans[16]) 
);
  IBUF pans_17_ibuf (
    .O(pans_d[17]),
    .I(pans[17]) 
);
  IBUF pans_18_ibuf (
    .O(pans_d[18]),
    .I(pans[18]) 
);
  IBUF pans_19_ibuf (
    .O(pans_d[19]),
    .I(pans[19]) 
);
  IBUF pans_20_ibuf (
    .O(pans_d[20]),
    .I(pans[20]) 
);
  IBUF pans_21_ibuf (
    .O(pans_d[21]),
    .I(pans[21]) 
);
  IBUF pans_22_ibuf (
    .O(pans_d[22]),
    .I(pans[22]) 
);
  IBUF pans_23_ibuf (
    .O(pans_d[23]),
    .I(pans[23]) 
);
  IBUF pans_24_ibuf (
    .O(pans_d[24]),
    .I(pans[24]) 
);
  IBUF pans_25_ibuf (
    .O(pans_d[25]),
    .I(pans[25]) 
);
  IBUF pans_26_ibuf (
    .O(pans_d[26]),
    .I(pans[26]) 
);
  IBUF pans_27_ibuf (
    .O(pans_d[27]),
    .I(pans[27]) 
);
  OBUF sample_l_0_obuf (
    .O(sample_l[0]),
    .I(GND) 
);
  OBUF sample_l_1_obuf (
    .O(sample_l[1]),
    .I(GND) 
);
  OBUF sample_l_2_obuf (
    .O(sample_l[2]),
    .I(GND) 
);
  OBUF sample_l_3_obuf (
    .O(sample_l[3]),
    .I(GND) 
);
  OBUF sample_l_4_obuf (
    .O(sample_l[4]),
    .I(GND) 
);
  OBUF sample_l_5_obuf (
    .O(sample_l[5]),
    .I(GND) 
);
  OBUF sample_l_6_obuf (
    .O(sample_l[6]),
    .I(GND) 
);
  OBUF sample_l_7_obuf (
    .O(sample_l[7]),
    .I(GND) 
);
  OBUF sample_l_8_obuf (
    .O(sample_l[8]),
    .I(sample_l_d[8]) 
);
  OBUF sample_l_9_obuf (
    .O(sample_l[9]),
    .I(sample_l_d[9]) 
);
  OBUF sample_l_10_obuf (
    .O(sample_l[10]),
    .I(sample_l_d[10]) 
);
  OBUF sample_l_11_obuf (
    .O(sample_l[11]),
    .I(sample_l_d[11]) 
);
  OBUF sample_l_12_obuf (
    .O(sample_l[12]),
    .I(sample_l_d[12]) 
);
  OBUF sample_l_13_obuf (
    .O(sample_l[13]),
    .I(sample_l_d[13]) 
);
  OBUF sample_l_14_obuf (
    .O(sample_l[14]),
    .I(sample_l_d[14]) 
);
  OBUF sample_l_15_obuf (
    .O(sample_l[15]),
    .I(sample_l_d[15]) 
);
  OBUF sample_l_16_obuf (
    .O(sample_l[16]),
    .I(sample_l_d[16]) 
);
  OBUF sample_l_17_obuf (
    .O(sample_l[17]),
    .I(sample_l_d[17]) 
);
  OBUF sample_l_18_obuf (
    .O(sample_l[18]),
    .I(sample_l_d[18]) 
);
  OBUF sample_l_19_obuf (
    .O(sample_l[19]),
    .I(sample_l_d[19]) 
);
  OBUF sample_l_20_obuf (
    .O(sample_l[20]),
    .I(sample_l_d[20]) 
);
  OBUF sample_l_21_obuf (
    .O(sample_l[21]),
    .I(sample_l_d[21]) 
);
  OBUF sample_l_22_obuf (
    .O(sample_l[22]),
    .I(sample_l_d[22]) 
);
  OBUF sample_l_23_obuf (
    .O(sample_l[23]),
    .I(sample_l_d[23]) 
);
  OBUF sample_r_0_obuf (
    .O(sample_r[0]),
    .I(GND) 
);
  OBUF sample_r_1_obuf (
    .O(sample_r[1]),
    .I(GND) 
);
  OBUF sample_r_2_obuf (
    .O(sample_r[2]),
    .I(GND) 
);
  OBUF sample_r_3_obuf (
    .O(sample_r[3]),
    .I(GND) 
);
  OBUF sample_r_4_obuf (
    .O(sample_r[4]),
    .I(GND) 
);
  OBUF sample_r_5_obuf (
    .O(sample_r[5]),
    .I(GND) 
);
  OBUF sample_r_6_obuf (
    .O(sample_r[6]),
    .I(GND) 
);
  OBUF sample_r_7_obuf (
    .O(sample_r[7]),
    .I(GND) 
);
  OBUF sample_r_8_obuf (
    .O(sample_r[8]),
    .I(sample_r_d[8]) 
);
  OBUF sample_r_9_obuf (
    .O(sample_r[9]),
    .I(sample_r_d[9]) 
);
  OBUF sample_r_10_obuf (
    .O(sample_r[10]),
    .I(sample_r_d[10]) 
);
  OBUF sample_r_11_obuf (
    .O(sample_r[11]),
    .I(sample_r_d[11]) 
);
  OBUF sample_r_12_obuf (
    .O(sample_r[12]),
    .I(sample_r_d[12]) 
);
  OBUF sample_r_13_obuf (
    .O(sample_r[13]),
    .I(sample_r_d[13]) 
);
  OBUF sample_r_14_obuf (
    .O(sample_r[14]),
    .I(sample_r_d[14]) 
);
  OBUF sample_r_15_obuf (
    .O(sample_r[15]),
    .I(sample_r_d[15]) 
);
  OBUF sample_r_16_obuf (
    .O(sample_r[16]),
    .I(sample_r_d[16]) 
);
  OBUF sample_r_17_obuf (
    .O(sample_r[17]),
    .I(sample_r_d[17]) 
);
  OBUF sample_r_18_obuf (
    .O(sample_r[18]),
    .I(sample_r_d[18]) 
);
  OBUF sample_r_19_obuf (
    .O(sample_r[19]),
    .I(sample_r_d[19]) 
);
  OBUF sample_r_20_obuf (
    .O(sample_r[20]),
    .I(sample_r_d[20]) 
);
  OBUF sample_r_21_obuf (
    .O(sample_r[21]),
    .I(sample_r_d[21]) 
);
  OBUF sample_r_22_obuf (
    .O(sample_r[22]),
    .I(sample_r_d[22]) 
);
  OBUF sample_r_23_obuf (
    .O(sample_r[23]),
    .I(sample_r_d[23]) 
);
  OBUF sample_valid_obuf (
    .O(sample_valid),
    .I(sample_valid_d) 
);
  OBUF latency_valid_obuf (
    .O(latency_valid),
    .I(latency_valid_d) 
);
  OBUF deadline_miss_obuf (
    .O(deadline_miss),
    .I(deadline_miss_d) 
);
  OBUF latency_cycles_0_obuf (
    .O(latency_cycles[0]),
    .I(latency_cycles_d[0]) 
);
  OBUF latency_cycles_1_obuf (
    .O(latency_cycles[1]),
    .I(latency_cycles_d[1]) 
);
  OBUF latency_cycles_2_obuf (
    .O(latency_cycles[2]),
    .I(latency_cycles_d[2]) 
);
  OBUF latency_cycles_3_obuf (
    .O(latency_cycles[3]),
    .I(latency_cycles_d[3]) 
);
  OBUF latency_cycles_4_obuf (
    .O(latency_cycles[4]),
    .I(latency_cycles_d[4]) 
);
  OBUF latency_cycles_5_obuf (
    .O(latency_cycles[5]),
    .I(latency_cycles_d[5]) 
);
  OBUF latency_cycles_6_obuf (
    .O(latency_cycles[6]),
    .I(latency_cycles_d[6]) 
);
  OBUF latency_cycles_7_obuf (
    .O(latency_cycles[7]),
    .I(latency_cycles_d[7]) 
);
  OBUF latency_cycles_8_obuf (
    .O(latency_cycles[8]),
    .I(latency_cycles_d[8]) 
);
  OBUF latency_cycles_9_obuf (
    .O(latency_cycles[9]),
    .I(latency_cycles_d[9]) 
);
  OBUF latency_cycles_10_obuf (
    .O(latency_cycles[10]),
    .I(latency_cycles_d[10]) 
);
  OBUF latency_cycles_11_obuf (
    .O(latency_cycles[11]),
    .I(latency_cycles_d[11]) 
);
  OBUF latency_cycles_12_obuf (
    .O(latency_cycles[12]),
    .I(latency_cycles_d[12]) 
);
  OBUF latency_cycles_13_obuf (
    .O(latency_cycles[13]),
    .I(latency_cycles_d[13]) 
);
  OBUF latency_cycles_14_obuf (
    .O(latency_cycles[14]),
    .I(latency_cycles_d[14]) 
);
  OBUF latency_cycles_15_obuf (
    .O(latency_cycles[15]),
    .I(latency_cycles_d[15]) 
);
  OBUF latency_cycles_16_obuf (
    .O(latency_cycles[16]),
    .I(latency_cycles_d[16]) 
);
  OBUF latency_cycles_17_obuf (
    .O(latency_cycles[17]),
    .I(latency_cycles_d[17]) 
);
  OBUF latency_cycles_18_obuf (
    .O(latency_cycles[18]),
    .I(latency_cycles_d[18]) 
);
  OBUF latency_cycles_19_obuf (
    .O(latency_cycles[19]),
    .I(latency_cycles_d[19]) 
);
  OBUF latency_cycles_20_obuf (
    .O(latency_cycles[20]),
    .I(latency_cycles_d[20]) 
);
  OBUF latency_cycles_21_obuf (
    .O(latency_cycles[21]),
    .I(latency_cycles_d[21]) 
);
  OBUF latency_cycles_22_obuf (
    .O(latency_cycles[22]),
    .I(latency_cycles_d[22]) 
);
  OBUF latency_cycles_23_obuf (
    .O(latency_cycles[23]),
    .I(latency_cycles_d[23]) 
);
  OBUF latency_cycles_24_obuf (
    .O(latency_cycles[24]),
    .I(latency_cycles_d[24]) 
);
  OBUF latency_cycles_25_obuf (
    .O(latency_cycles[25]),
    .I(latency_cycles_d[25]) 
);
  OBUF latency_cycles_26_obuf (
    .O(latency_cycles[26]),
    .I(latency_cycles_d[26]) 
);
  OBUF latency_cycles_27_obuf (
    .O(latency_cycles[27]),
    .I(latency_cycles_d[27]) 
);
  OBUF latency_cycles_28_obuf (
    .O(latency_cycles[28]),
    .I(latency_cycles_d[28]) 
);
  OBUF latency_cycles_29_obuf (
    .O(latency_cycles[29]),
    .I(latency_cycles_d[29]) 
);
  OBUF latency_cycles_30_obuf (
    .O(latency_cycles[30]),
    .I(latency_cycles_d[30]) 
);
  OBUF latency_cycles_31_obuf (
    .O(latency_cycles[31]),
    .I(latency_cycles_d[31]) 
);
  OBUF active_count_0_obuf (
    .O(active_count[0]),
    .I(active_count_d[0]) 
);
  OBUF active_count_1_obuf (
    .O(active_count[1]),
    .I(active_count_d[1]) 
);
  OBUF active_count_2_obuf (
    .O(active_count[2]),
    .I(active_count_d[2]) 
);
  LUT4 n3584_s0 (
    .F(n3584_4),
    .I0(n3584_5),
    .I1(n3584_6),
    .I2(n3584_7),
    .I3(n3584_8) 
);
defparam n3584_s0.INIT=16'h7F00;
  LUT2 n3583_s0 (
    .F(n3583_3),
    .I0(n3583_4),
    .I1(sample_tick_d) 
);
defparam n3583_s0.INIT=4'h4;
  LUT2 latency_valid_s5 (
    .F(latency_valid_7),
    .I0(n3584_4),
    .I1(start_event_d) 
);
defparam latency_valid_s5.INIT=4'hE;
  LUT4 timer_31_s3 (
    .F(timer_31_8),
    .I0(timer_31_14),
    .I1(timer_31_10),
    .I2(measuring),
    .I3(start_event_d) 
);
defparam timer_31_s3.INIT=16'hFF70;
  LUT4 \sine_q[3]_0_s11  (
    .F(\sine_q[3]_0_17 ),
    .I0(\sine_q[3]_0_19 ),
    .I1(n887_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[3]_0_s11 .INIT=16'hCA00;
  LUT4 \sine_q[3]_1_s9  (
    .F(\sine_q[3]_1_15 ),
    .I0(\sine_q[3]_1_17 ),
    .I1(n886_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[3]_1_s9 .INIT=16'hCA00;
  LUT4 \sine_q[3]_2_s9  (
    .F(\sine_q[3]_2_15 ),
    .I0(\sine_q[3]_2_17 ),
    .I1(n885_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[3]_2_s9 .INIT=16'hCA00;
  LUT4 \sine_q[3]_3_s9  (
    .F(\sine_q[3]_3_15 ),
    .I0(\sine_q[3]_3_17 ),
    .I1(n884_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[3]_3_s9 .INIT=16'hCA00;
  LUT4 \sine_q[3]_4_s9  (
    .F(\sine_q[3]_4_15 ),
    .I0(\sine_q[3]_4_17 ),
    .I1(n883_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[3]_4_s9 .INIT=16'hCA00;
  LUT4 \sine_q[3]_5_s9  (
    .F(\sine_q[3]_5_15 ),
    .I0(\sine_q[3]_5_17 ),
    .I1(n882_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[3]_5_s9 .INIT=16'hCA00;
  LUT4 \sine_q[3]_6_s9  (
    .F(\sine_q[3]_6_15 ),
    .I0(\sine_q[3]_6_17 ),
    .I1(n881_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[3]_6_s9 .INIT=16'hCA00;
  LUT4 \sine_q[3]_7_s9  (
    .F(\sine_q[3]_7_15 ),
    .I0(\sine_q[3]_7_17 ),
    .I1(n880_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[3]_7_s9 .INIT=16'hCA00;
  LUT4 \sine_q[3]_8_s9  (
    .F(\sine_q[3]_8_15 ),
    .I0(\sine_q[3]_8_17 ),
    .I1(n879_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[3]_8_s9 .INIT=16'hCA00;
  LUT4 \sine_q[3]_9_s9  (
    .F(\sine_q[3]_9_15 ),
    .I0(\sine_q[3]_9_17 ),
    .I1(n878_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[3]_9_s9 .INIT=16'hCA00;
  LUT4 \sine_q[3]_10_s9  (
    .F(\sine_q[3]_10_15 ),
    .I0(\sine_q[3]_10_17 ),
    .I1(n877_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[3]_10_s9 .INIT=16'hCA00;
  LUT4 \sine_q[3]_11_s9  (
    .F(\sine_q[3]_11_15 ),
    .I0(\sine_q[3]_11_17 ),
    .I1(n876_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[3]_11_s9 .INIT=16'hCA00;
  LUT4 \sine_q[3]_12_s9  (
    .F(\sine_q[3]_12_15 ),
    .I0(\sine_q[3]_12_17 ),
    .I1(n875_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[3]_12_s9 .INIT=16'hCA00;
  LUT4 \sine_q[3]_13_s9  (
    .F(\sine_q[3]_13_15 ),
    .I0(\sine_q[3]_13_17 ),
    .I1(n874_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[3]_13_s9 .INIT=16'hCA00;
  LUT4 \sine_q[3]_14_s9  (
    .F(\sine_q[3]_14_15 ),
    .I0(\sine_q[3]_14_17 ),
    .I1(n873_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[3]_14_s9 .INIT=16'hCA00;
  LUT4 \sine_q[3]_15_s9  (
    .F(\sine_q[3]_15_15 ),
    .I0(\sine_q[3]_15_17 ),
    .I1(n872_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[3]_15_s9 .INIT=16'hCA00;
  LUT4 \sine_q[2]_0_s9  (
    .F(\sine_q[2]_0_15 ),
    .I0(\sine_q[2]_0_17 ),
    .I1(n790_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[2]_0_s9 .INIT=16'hCA00;
  LUT4 \sine_q[2]_1_s9  (
    .F(\sine_q[2]_1_15 ),
    .I0(\sine_q[2]_1_17 ),
    .I1(n789_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[2]_1_s9 .INIT=16'hCA00;
  LUT4 \sine_q[2]_2_s9  (
    .F(\sine_q[2]_2_15 ),
    .I0(\sine_q[2]_2_17 ),
    .I1(n788_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[2]_2_s9 .INIT=16'hCA00;
  LUT4 \sine_q[2]_3_s9  (
    .F(\sine_q[2]_3_15 ),
    .I0(\sine_q[2]_3_17 ),
    .I1(n787_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[2]_3_s9 .INIT=16'hCA00;
  LUT4 \sine_q[2]_4_s9  (
    .F(\sine_q[2]_4_15 ),
    .I0(\sine_q[2]_4_17 ),
    .I1(n786_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[2]_4_s9 .INIT=16'hCA00;
  LUT4 \sine_q[2]_5_s9  (
    .F(\sine_q[2]_5_15 ),
    .I0(\sine_q[2]_5_17 ),
    .I1(n785_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[2]_5_s9 .INIT=16'hCA00;
  LUT4 \sine_q[2]_6_s9  (
    .F(\sine_q[2]_6_15 ),
    .I0(\sine_q[2]_6_17 ),
    .I1(n784_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[2]_6_s9 .INIT=16'hCA00;
  LUT4 \sine_q[2]_7_s9  (
    .F(\sine_q[2]_7_15 ),
    .I0(\sine_q[2]_7_17 ),
    .I1(n783_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[2]_7_s9 .INIT=16'hCA00;
  LUT4 \sine_q[2]_8_s9  (
    .F(\sine_q[2]_8_15 ),
    .I0(\sine_q[2]_8_17 ),
    .I1(n782_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[2]_8_s9 .INIT=16'hCA00;
  LUT4 \sine_q[2]_9_s9  (
    .F(\sine_q[2]_9_15 ),
    .I0(\sine_q[2]_9_17 ),
    .I1(n781_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[2]_9_s9 .INIT=16'hCA00;
  LUT4 \sine_q[2]_10_s9  (
    .F(\sine_q[2]_10_15 ),
    .I0(\sine_q[2]_10_17 ),
    .I1(n780_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[2]_10_s9 .INIT=16'hCA00;
  LUT4 \sine_q[2]_11_s9  (
    .F(\sine_q[2]_11_15 ),
    .I0(\sine_q[2]_11_17 ),
    .I1(n779_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[2]_11_s9 .INIT=16'hCA00;
  LUT4 \sine_q[2]_12_s9  (
    .F(\sine_q[2]_12_15 ),
    .I0(\sine_q[2]_12_17 ),
    .I1(n778_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[2]_12_s9 .INIT=16'hCA00;
  LUT4 \sine_q[2]_13_s9  (
    .F(\sine_q[2]_13_15 ),
    .I0(\sine_q[2]_13_17 ),
    .I1(n777_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[2]_13_s9 .INIT=16'hCA00;
  LUT4 \sine_q[2]_14_s9  (
    .F(\sine_q[2]_14_15 ),
    .I0(\sine_q[2]_14_17 ),
    .I1(n776_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[2]_14_s9 .INIT=16'hCA00;
  LUT4 \sine_q[2]_15_s9  (
    .F(\sine_q[2]_15_15 ),
    .I0(\sine_q[2]_15_17 ),
    .I1(n775_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[2]_15_s9 .INIT=16'hCA00;
  LUT4 \sine_q[1]_0_s9  (
    .F(\sine_q[1]_0_15 ),
    .I0(\sine_q[1]_0_17 ),
    .I1(n693_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[1]_0_s9 .INIT=16'hCA00;
  LUT4 \sine_q[1]_1_s9  (
    .F(\sine_q[1]_1_15 ),
    .I0(\sine_q[1]_1_17 ),
    .I1(n692_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[1]_1_s9 .INIT=16'hCA00;
  LUT4 \sine_q[1]_2_s9  (
    .F(\sine_q[1]_2_15 ),
    .I0(\sine_q[1]_2_17 ),
    .I1(n691_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[1]_2_s9 .INIT=16'hCA00;
  LUT4 \sine_q[1]_3_s9  (
    .F(\sine_q[1]_3_15 ),
    .I0(\sine_q[1]_3_17 ),
    .I1(n690_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[1]_3_s9 .INIT=16'hCA00;
  LUT4 \sine_q[1]_4_s9  (
    .F(\sine_q[1]_4_15 ),
    .I0(\sine_q[1]_4_17 ),
    .I1(n689_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[1]_4_s9 .INIT=16'hCA00;
  LUT4 \sine_q[1]_5_s9  (
    .F(\sine_q[1]_5_15 ),
    .I0(\sine_q[1]_5_17 ),
    .I1(n688_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[1]_5_s9 .INIT=16'hCA00;
  LUT4 \sine_q[1]_6_s9  (
    .F(\sine_q[1]_6_15 ),
    .I0(\sine_q[1]_6_17 ),
    .I1(n687_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[1]_6_s9 .INIT=16'hCA00;
  LUT4 \sine_q[1]_7_s9  (
    .F(\sine_q[1]_7_15 ),
    .I0(\sine_q[1]_7_17 ),
    .I1(n686_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[1]_7_s9 .INIT=16'hCA00;
  LUT4 \sine_q[1]_8_s9  (
    .F(\sine_q[1]_8_15 ),
    .I0(\sine_q[1]_8_17 ),
    .I1(n685_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[1]_8_s9 .INIT=16'hCA00;
  LUT4 \sine_q[1]_9_s9  (
    .F(\sine_q[1]_9_15 ),
    .I0(\sine_q[1]_9_17 ),
    .I1(n684_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[1]_9_s9 .INIT=16'hCA00;
  LUT4 \sine_q[1]_10_s9  (
    .F(\sine_q[1]_10_15 ),
    .I0(\sine_q[1]_10_17 ),
    .I1(n683_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[1]_10_s9 .INIT=16'hCA00;
  LUT4 \sine_q[1]_11_s9  (
    .F(\sine_q[1]_11_15 ),
    .I0(\sine_q[1]_11_17 ),
    .I1(n682_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[1]_11_s9 .INIT=16'hCA00;
  LUT4 \sine_q[1]_12_s9  (
    .F(\sine_q[1]_12_15 ),
    .I0(\sine_q[1]_12_17 ),
    .I1(n681_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[1]_12_s9 .INIT=16'hCA00;
  LUT4 \sine_q[1]_13_s9  (
    .F(\sine_q[1]_13_15 ),
    .I0(\sine_q[1]_13_17 ),
    .I1(n680_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[1]_13_s9 .INIT=16'hCA00;
  LUT4 \sine_q[1]_14_s9  (
    .F(\sine_q[1]_14_15 ),
    .I0(\sine_q[1]_14_17 ),
    .I1(n679_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[1]_14_s9 .INIT=16'hCA00;
  LUT4 \sine_q[1]_15_s9  (
    .F(\sine_q[1]_15_15 ),
    .I0(\sine_q[1]_15_17 ),
    .I1(n678_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[1]_15_s9 .INIT=16'hCA00;
  LUT4 \sine_q[0]_0_s9  (
    .F(\sine_q[0]_0_15 ),
    .I0(\sine_q[0]_0_17 ),
    .I1(n596_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[0]_0_s9 .INIT=16'hCA00;
  LUT4 \sine_q[0]_1_s9  (
    .F(\sine_q[0]_1_15 ),
    .I0(\sine_q[0]_1_17 ),
    .I1(n595_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[0]_1_s9 .INIT=16'hCA00;
  LUT4 \sine_q[0]_2_s9  (
    .F(\sine_q[0]_2_15 ),
    .I0(\sine_q[0]_2_17 ),
    .I1(n594_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[0]_2_s9 .INIT=16'hCA00;
  LUT4 \sine_q[0]_3_s9  (
    .F(\sine_q[0]_3_15 ),
    .I0(\sine_q[0]_3_17 ),
    .I1(n593_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[0]_3_s9 .INIT=16'hCA00;
  LUT4 \sine_q[0]_4_s9  (
    .F(\sine_q[0]_4_15 ),
    .I0(\sine_q[0]_4_17 ),
    .I1(n592_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[0]_4_s9 .INIT=16'hCA00;
  LUT4 \sine_q[0]_5_s9  (
    .F(\sine_q[0]_5_15 ),
    .I0(\sine_q[0]_5_17 ),
    .I1(n591_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[0]_5_s9 .INIT=16'hCA00;
  LUT4 \sine_q[0]_6_s9  (
    .F(\sine_q[0]_6_15 ),
    .I0(\sine_q[0]_6_17 ),
    .I1(n590_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[0]_6_s9 .INIT=16'hCA00;
  LUT4 \sine_q[0]_7_s9  (
    .F(\sine_q[0]_7_15 ),
    .I0(\sine_q[0]_7_17 ),
    .I1(n589_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[0]_7_s9 .INIT=16'hCA00;
  LUT4 \sine_q[0]_8_s9  (
    .F(\sine_q[0]_8_15 ),
    .I0(\sine_q[0]_8_17 ),
    .I1(n588_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[0]_8_s9 .INIT=16'hCA00;
  LUT4 \sine_q[0]_9_s9  (
    .F(\sine_q[0]_9_15 ),
    .I0(\sine_q[0]_9_17 ),
    .I1(n587_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[0]_9_s9 .INIT=16'hCA00;
  LUT4 \sine_q[0]_10_s9  (
    .F(\sine_q[0]_10_15 ),
    .I0(\sine_q[0]_10_17 ),
    .I1(n586_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[0]_10_s9 .INIT=16'hCA00;
  LUT4 \sine_q[0]_11_s9  (
    .F(\sine_q[0]_11_15 ),
    .I0(\sine_q[0]_11_17 ),
    .I1(n585_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[0]_11_s9 .INIT=16'hCA00;
  LUT4 \sine_q[0]_12_s9  (
    .F(\sine_q[0]_12_15 ),
    .I0(\sine_q[0]_12_17 ),
    .I1(n584_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[0]_12_s9 .INIT=16'hCA00;
  LUT4 \sine_q[0]_13_s9  (
    .F(\sine_q[0]_13_15 ),
    .I0(\sine_q[0]_13_17 ),
    .I1(n583_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[0]_13_s9 .INIT=16'hCA00;
  LUT4 \sine_q[0]_14_s9  (
    .F(\sine_q[0]_14_15 ),
    .I0(\sine_q[0]_14_17 ),
    .I1(n582_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[0]_14_s9 .INIT=16'hCA00;
  LUT4 \sine_q[0]_15_s9  (
    .F(\sine_q[0]_15_15 ),
    .I0(\sine_q[0]_15_17 ),
    .I1(n581_6),
    .I2(\sine_q[3]_0_21 ),
    .I3(\sine_q[3]_0_6 ) 
);
defparam \sine_q[0]_15_s9 .INIT=16'hCA00;
  LUT2 n331_s3 (
    .F(n331_8),
    .I0(timer[0]),
    .I1(start_event_d) 
);
defparam n331_s3.INIT=4'h1;
  LUT3 n330_s2 (
    .F(n330_7),
    .I0(start_event_d),
    .I1(timer[0]),
    .I2(timer[1]) 
);
defparam n330_s2.INIT=8'h14;
  LUT4 n329_s2 (
    .F(n329_7),
    .I0(timer[0]),
    .I1(timer[1]),
    .I2(start_event_d),
    .I3(timer[2]) 
);
defparam n329_s2.INIT=16'h0708;
  LUT2 n328_s2 (
    .F(n328_7),
    .I0(n328_8),
    .I1(start_event_d) 
);
defparam n328_s2.INIT=4'h2;
  LUT3 n327_s2 (
    .F(n327_7),
    .I0(start_event_d),
    .I1(n327_8),
    .I2(timer[4]) 
);
defparam n327_s2.INIT=8'h14;
  LUT4 n326_s2 (
    .F(n326_7),
    .I0(n327_8),
    .I1(timer[4]),
    .I2(start_event_d),
    .I3(timer[5]) 
);
defparam n326_s2.INIT=16'h0708;
  LUT2 n325_s2 (
    .F(n325_7),
    .I0(n325_8),
    .I1(start_event_d) 
);
defparam n325_s2.INIT=4'h2;
  LUT3 n324_s2 (
    .F(n324_7),
    .I0(start_event_d),
    .I1(n324_8),
    .I2(timer[7]) 
);
defparam n324_s2.INIT=8'h14;
  LUT4 n322_s2 (
    .F(n322_7),
    .I0(n323_8),
    .I1(timer[8]),
    .I2(start_event_d),
    .I3(timer[9]) 
);
defparam n322_s2.INIT=16'h0708;
  LUT4 n321_s2 (
    .F(n321_7),
    .I0(n323_8),
    .I1(n321_8),
    .I2(start_event_d),
    .I3(timer[10]) 
);
defparam n321_s2.INIT=16'h0708;
  LUT3 n320_s2 (
    .F(n320_7),
    .I0(start_event_d),
    .I1(n320_10),
    .I2(timer[11]) 
);
defparam n320_s2.INIT=8'h14;
  LUT4 n319_s2 (
    .F(n319_7),
    .I0(n320_10),
    .I1(timer[11]),
    .I2(start_event_d),
    .I3(timer[12]) 
);
defparam n319_s2.INIT=16'h0708;
  LUT3 n318_s2 (
    .F(n318_7),
    .I0(start_event_d),
    .I1(n318_8),
    .I2(timer[13]) 
);
defparam n318_s2.INIT=8'h14;
  LUT4 n317_s2 (
    .F(n317_7),
    .I0(n318_8),
    .I1(timer[13]),
    .I2(start_event_d),
    .I3(timer[14]) 
);
defparam n317_s2.INIT=16'h0708;
  LUT4 n316_s2 (
    .F(n316_7),
    .I0(n318_8),
    .I1(n316_8),
    .I2(start_event_d),
    .I3(timer[15]) 
);
defparam n316_s2.INIT=16'h0708;
  LUT3 n315_s2 (
    .F(n315_7),
    .I0(start_event_d),
    .I1(n315_10),
    .I2(timer[16]) 
);
defparam n315_s2.INIT=8'h14;
  LUT4 n314_s2 (
    .F(n314_7),
    .I0(n315_10),
    .I1(timer[16]),
    .I2(start_event_d),
    .I3(timer[17]) 
);
defparam n314_s2.INIT=16'h0708;
  LUT4 n313_s2 (
    .F(n313_7),
    .I0(n313_8),
    .I1(n318_8),
    .I2(start_event_d),
    .I3(timer[18]) 
);
defparam n313_s2.INIT=16'h0708;
  LUT3 n312_s2 (
    .F(n312_7),
    .I0(start_event_d),
    .I1(n312_8),
    .I2(timer[19]) 
);
defparam n312_s2.INIT=8'h14;
  LUT3 n311_s2 (
    .F(n311_7),
    .I0(start_event_d),
    .I1(n311_8),
    .I2(timer[20]) 
);
defparam n311_s2.INIT=8'h14;
  LUT4 n310_s2 (
    .F(n310_7),
    .I0(n311_8),
    .I1(timer[20]),
    .I2(start_event_d),
    .I3(timer[21]) 
);
defparam n310_s2.INIT=16'h0708;
  LUT4 n309_s2 (
    .F(n309_7),
    .I0(n311_8),
    .I1(n309_8),
    .I2(start_event_d),
    .I3(timer[22]) 
);
defparam n309_s2.INIT=16'h0708;
  LUT3 n308_s2 (
    .F(n308_7),
    .I0(start_event_d),
    .I1(n308_8),
    .I2(timer[23]) 
);
defparam n308_s2.INIT=8'h14;
  LUT3 n307_s2 (
    .F(n307_7),
    .I0(start_event_d),
    .I1(n307_8),
    .I2(timer[24]) 
);
defparam n307_s2.INIT=8'h14;
  LUT4 n306_s2 (
    .F(n306_7),
    .I0(n307_8),
    .I1(timer[24]),
    .I2(start_event_d),
    .I3(timer[25]) 
);
defparam n306_s2.INIT=16'h0708;
  LUT4 n305_s2 (
    .F(n305_7),
    .I0(n307_8),
    .I1(n305_8),
    .I2(start_event_d),
    .I3(timer[26]) 
);
defparam n305_s2.INIT=16'h0708;
  LUT4 n304_s2 (
    .F(n304_7),
    .I0(n307_8),
    .I1(n304_10),
    .I2(start_event_d),
    .I3(timer[27]) 
);
defparam n304_s2.INIT=16'h0708;
  LUT3 n303_s2 (
    .F(n303_7),
    .I0(start_event_d),
    .I1(timer_31_10),
    .I2(timer[28]) 
);
defparam n303_s2.INIT=8'h14;
  LUT4 n302_s2 (
    .F(n302_7),
    .I0(timer_31_10),
    .I1(timer[28]),
    .I2(start_event_d),
    .I3(timer[29]) 
);
defparam n302_s2.INIT=16'h0708;
  LUT4 n301_s2 (
    .F(n301_7),
    .I0(timer_31_10),
    .I1(n301_8),
    .I2(start_event_d),
    .I3(timer[30]) 
);
defparam n301_s2.INIT=16'h0708;
  LUT4 n300_s2 (
    .F(n300_7),
    .I0(timer_31_10),
    .I1(n300_10),
    .I2(start_event_d),
    .I3(timer[31]) 
);
defparam n300_s2.INIT=16'h0708;
  LUT2 active_count_d_2_s (
    .F(active_count_d[2]),
    .I0(active_count_d_2_5),
    .I1(running_d) 
);
defparam active_count_d_2_s.INIT=4'h8;
  LUT3 active_count_d_1_s (
    .F(active_count_d[1]),
    .I0(active_count_d_1_5),
    .I1(active_count_d_1_6),
    .I2(running_d) 
);
defparam active_count_d_1_s.INIT=8'h60;
  LUT4 active_count_d_0_s (
    .F(active_count_d[0]),
    .I0(active_count_d_0_5),
    .I1(active_count_d_0_6),
    .I2(active_count_d_0_7),
    .I3(running_d) 
);
defparam active_count_d_0_s.INIT=16'h6900;
  LUT2 n533_s1 (
    .F(n533_6),
    .I0(running_d),
    .I1(n501_1) 
);
defparam n533_s1.INIT=4'h8;
  LUT2 n534_s1 (
    .F(n534_6),
    .I0(running_d),
    .I1(n502_1) 
);
defparam n534_s1.INIT=4'h8;
  LUT2 n535_s1 (
    .F(n535_6),
    .I0(running_d),
    .I1(n503_1) 
);
defparam n535_s1.INIT=4'h8;
  LUT2 n536_s1 (
    .F(n536_6),
    .I0(running_d),
    .I1(n504_1) 
);
defparam n536_s1.INIT=4'h8;
  LUT2 n537_s1 (
    .F(n537_6),
    .I0(running_d),
    .I1(n505_1) 
);
defparam n537_s1.INIT=4'h8;
  LUT2 n538_s1 (
    .F(n538_6),
    .I0(running_d),
    .I1(n506_1) 
);
defparam n538_s1.INIT=4'h8;
  LUT2 n539_s1 (
    .F(n539_6),
    .I0(running_d),
    .I1(n507_1) 
);
defparam n539_s1.INIT=4'h8;
  LUT2 n540_s1 (
    .F(n540_6),
    .I0(running_d),
    .I1(n508_1) 
);
defparam n540_s1.INIT=4'h8;
  LUT2 n541_s1 (
    .F(n541_6),
    .I0(running_d),
    .I1(n509_1) 
);
defparam n541_s1.INIT=4'h8;
  LUT2 n542_s1 (
    .F(n542_6),
    .I0(running_d),
    .I1(n510_1) 
);
defparam n542_s1.INIT=4'h8;
  LUT2 n543_s1 (
    .F(n543_6),
    .I0(running_d),
    .I1(n511_1) 
);
defparam n543_s1.INIT=4'h8;
  LUT2 n544_s1 (
    .F(n544_6),
    .I0(running_d),
    .I1(n512_1) 
);
defparam n544_s1.INIT=4'h8;
  LUT2 n545_s1 (
    .F(n545_6),
    .I0(running_d),
    .I1(n513_1) 
);
defparam n545_s1.INIT=4'h8;
  LUT2 n546_s1 (
    .F(n546_6),
    .I0(running_d),
    .I1(n514_1) 
);
defparam n546_s1.INIT=4'h8;
  LUT2 n547_s1 (
    .F(n547_6),
    .I0(running_d),
    .I1(n515_1) 
);
defparam n547_s1.INIT=4'h8;
  LUT2 n548_s1 (
    .F(n548_6),
    .I0(running_d),
    .I1(n516_1) 
);
defparam n548_s1.INIT=4'h8;
  LUT2 n549_s1 (
    .F(n549_6),
    .I0(running_d),
    .I1(n517_1) 
);
defparam n549_s1.INIT=4'h8;
  LUT2 n550_s1 (
    .F(n550_6),
    .I0(running_d),
    .I1(n518_1) 
);
defparam n550_s1.INIT=4'h8;
  LUT2 n551_s1 (
    .F(n551_6),
    .I0(running_d),
    .I1(n519_1) 
);
defparam n551_s1.INIT=4'h8;
  LUT2 n552_s1 (
    .F(n552_6),
    .I0(running_d),
    .I1(n520_1) 
);
defparam n552_s1.INIT=4'h8;
  LUT2 n553_s1 (
    .F(n553_6),
    .I0(running_d),
    .I1(n521_1) 
);
defparam n553_s1.INIT=4'h8;
  LUT2 n554_s1 (
    .F(n554_6),
    .I0(running_d),
    .I1(n522_1) 
);
defparam n554_s1.INIT=4'h8;
  LUT2 n555_s1 (
    .F(n555_6),
    .I0(running_d),
    .I1(n523_1) 
);
defparam n555_s1.INIT=4'h8;
  LUT2 n556_s1 (
    .F(n556_6),
    .I0(running_d),
    .I1(n524_1) 
);
defparam n556_s1.INIT=4'h8;
  LUT2 n557_s1 (
    .F(n557_6),
    .I0(running_d),
    .I1(n525_1) 
);
defparam n557_s1.INIT=4'h8;
  LUT2 n558_s1 (
    .F(n558_6),
    .I0(running_d),
    .I1(n526_1) 
);
defparam n558_s1.INIT=4'h8;
  LUT2 n559_s1 (
    .F(n559_6),
    .I0(running_d),
    .I1(n527_1) 
);
defparam n559_s1.INIT=4'h8;
  LUT2 n560_s1 (
    .F(n560_6),
    .I0(running_d),
    .I1(n528_1) 
);
defparam n560_s1.INIT=4'h8;
  LUT2 n561_s1 (
    .F(n561_6),
    .I0(running_d),
    .I1(n529_1) 
);
defparam n561_s1.INIT=4'h8;
  LUT2 n562_s1 (
    .F(n562_6),
    .I0(running_d),
    .I1(n530_1) 
);
defparam n562_s1.INIT=4'h8;
  LUT2 n563_s1 (
    .F(n563_6),
    .I0(running_d),
    .I1(n531_1) 
);
defparam n563_s1.INIT=4'h8;
  LUT2 n564_s1 (
    .F(n564_6),
    .I0(running_d),
    .I1(n532_1) 
);
defparam n564_s1.INIT=4'h8;
  LUT2 n630_s1 (
    .F(n630_6),
    .I0(running_d),
    .I1(n598_1) 
);
defparam n630_s1.INIT=4'h8;
  LUT2 n631_s1 (
    .F(n631_6),
    .I0(running_d),
    .I1(n599_1) 
);
defparam n631_s1.INIT=4'h8;
  LUT2 n632_s1 (
    .F(n632_6),
    .I0(running_d),
    .I1(n600_1) 
);
defparam n632_s1.INIT=4'h8;
  LUT2 n633_s1 (
    .F(n633_6),
    .I0(running_d),
    .I1(n601_1) 
);
defparam n633_s1.INIT=4'h8;
  LUT2 n634_s1 (
    .F(n634_6),
    .I0(running_d),
    .I1(n602_1) 
);
defparam n634_s1.INIT=4'h8;
  LUT2 n635_s1 (
    .F(n635_6),
    .I0(running_d),
    .I1(n603_1) 
);
defparam n635_s1.INIT=4'h8;
  LUT2 n636_s1 (
    .F(n636_6),
    .I0(running_d),
    .I1(n604_1) 
);
defparam n636_s1.INIT=4'h8;
  LUT2 n637_s1 (
    .F(n637_6),
    .I0(running_d),
    .I1(n605_1) 
);
defparam n637_s1.INIT=4'h8;
  LUT2 n638_s1 (
    .F(n638_6),
    .I0(running_d),
    .I1(n606_1) 
);
defparam n638_s1.INIT=4'h8;
  LUT2 n639_s1 (
    .F(n639_6),
    .I0(running_d),
    .I1(n607_1) 
);
defparam n639_s1.INIT=4'h8;
  LUT2 n640_s1 (
    .F(n640_6),
    .I0(running_d),
    .I1(n608_1) 
);
defparam n640_s1.INIT=4'h8;
  LUT2 n641_s1 (
    .F(n641_6),
    .I0(running_d),
    .I1(n609_1) 
);
defparam n641_s1.INIT=4'h8;
  LUT2 n642_s1 (
    .F(n642_6),
    .I0(running_d),
    .I1(n610_1) 
);
defparam n642_s1.INIT=4'h8;
  LUT2 n643_s1 (
    .F(n643_6),
    .I0(running_d),
    .I1(n611_1) 
);
defparam n643_s1.INIT=4'h8;
  LUT2 n644_s1 (
    .F(n644_6),
    .I0(running_d),
    .I1(n612_1) 
);
defparam n644_s1.INIT=4'h8;
  LUT2 n645_s1 (
    .F(n645_6),
    .I0(running_d),
    .I1(n613_1) 
);
defparam n645_s1.INIT=4'h8;
  LUT2 n646_s1 (
    .F(n646_6),
    .I0(running_d),
    .I1(n614_1) 
);
defparam n646_s1.INIT=4'h8;
  LUT2 n647_s1 (
    .F(n647_6),
    .I0(running_d),
    .I1(n615_1) 
);
defparam n647_s1.INIT=4'h8;
  LUT2 n648_s1 (
    .F(n648_6),
    .I0(running_d),
    .I1(n616_1) 
);
defparam n648_s1.INIT=4'h8;
  LUT2 n649_s1 (
    .F(n649_6),
    .I0(running_d),
    .I1(n617_1) 
);
defparam n649_s1.INIT=4'h8;
  LUT2 n650_s1 (
    .F(n650_6),
    .I0(running_d),
    .I1(n618_1) 
);
defparam n650_s1.INIT=4'h8;
  LUT2 n651_s1 (
    .F(n651_6),
    .I0(running_d),
    .I1(n619_1) 
);
defparam n651_s1.INIT=4'h8;
  LUT2 n652_s1 (
    .F(n652_6),
    .I0(running_d),
    .I1(n620_1) 
);
defparam n652_s1.INIT=4'h8;
  LUT2 n653_s1 (
    .F(n653_6),
    .I0(running_d),
    .I1(n621_1) 
);
defparam n653_s1.INIT=4'h8;
  LUT2 n654_s1 (
    .F(n654_6),
    .I0(running_d),
    .I1(n622_1) 
);
defparam n654_s1.INIT=4'h8;
  LUT2 n655_s1 (
    .F(n655_6),
    .I0(running_d),
    .I1(n623_1) 
);
defparam n655_s1.INIT=4'h8;
  LUT2 n656_s1 (
    .F(n656_6),
    .I0(running_d),
    .I1(n624_1) 
);
defparam n656_s1.INIT=4'h8;
  LUT2 n657_s1 (
    .F(n657_6),
    .I0(running_d),
    .I1(n625_1) 
);
defparam n657_s1.INIT=4'h8;
  LUT2 n658_s1 (
    .F(n658_6),
    .I0(running_d),
    .I1(n626_1) 
);
defparam n658_s1.INIT=4'h8;
  LUT2 n659_s1 (
    .F(n659_6),
    .I0(running_d),
    .I1(n627_1) 
);
defparam n659_s1.INIT=4'h8;
  LUT2 n660_s1 (
    .F(n660_6),
    .I0(running_d),
    .I1(n628_1) 
);
defparam n660_s1.INIT=4'h8;
  LUT2 n661_s1 (
    .F(n661_6),
    .I0(running_d),
    .I1(n629_1) 
);
defparam n661_s1.INIT=4'h8;
  LUT2 n727_s1 (
    .F(n727_6),
    .I0(running_d),
    .I1(n695_1) 
);
defparam n727_s1.INIT=4'h8;
  LUT2 n728_s1 (
    .F(n728_6),
    .I0(running_d),
    .I1(n696_1) 
);
defparam n728_s1.INIT=4'h8;
  LUT2 n729_s1 (
    .F(n729_6),
    .I0(running_d),
    .I1(n697_1) 
);
defparam n729_s1.INIT=4'h8;
  LUT2 n730_s1 (
    .F(n730_6),
    .I0(running_d),
    .I1(n698_1) 
);
defparam n730_s1.INIT=4'h8;
  LUT2 n731_s1 (
    .F(n731_6),
    .I0(running_d),
    .I1(n699_1) 
);
defparam n731_s1.INIT=4'h8;
  LUT2 n732_s1 (
    .F(n732_6),
    .I0(running_d),
    .I1(n700_1) 
);
defparam n732_s1.INIT=4'h8;
  LUT2 n733_s1 (
    .F(n733_6),
    .I0(running_d),
    .I1(n701_1) 
);
defparam n733_s1.INIT=4'h8;
  LUT2 n734_s1 (
    .F(n734_6),
    .I0(running_d),
    .I1(n702_1) 
);
defparam n734_s1.INIT=4'h8;
  LUT2 n735_s1 (
    .F(n735_6),
    .I0(running_d),
    .I1(n703_1) 
);
defparam n735_s1.INIT=4'h8;
  LUT2 n736_s1 (
    .F(n736_6),
    .I0(running_d),
    .I1(n704_1) 
);
defparam n736_s1.INIT=4'h8;
  LUT2 n737_s1 (
    .F(n737_6),
    .I0(running_d),
    .I1(n705_1) 
);
defparam n737_s1.INIT=4'h8;
  LUT2 n738_s1 (
    .F(n738_6),
    .I0(running_d),
    .I1(n706_1) 
);
defparam n738_s1.INIT=4'h8;
  LUT2 n739_s1 (
    .F(n739_6),
    .I0(running_d),
    .I1(n707_1) 
);
defparam n739_s1.INIT=4'h8;
  LUT2 n740_s1 (
    .F(n740_6),
    .I0(running_d),
    .I1(n708_1) 
);
defparam n740_s1.INIT=4'h8;
  LUT2 n741_s1 (
    .F(n741_6),
    .I0(running_d),
    .I1(n709_1) 
);
defparam n741_s1.INIT=4'h8;
  LUT2 n742_s1 (
    .F(n742_6),
    .I0(running_d),
    .I1(n710_1) 
);
defparam n742_s1.INIT=4'h8;
  LUT2 n743_s1 (
    .F(n743_6),
    .I0(running_d),
    .I1(n711_1) 
);
defparam n743_s1.INIT=4'h8;
  LUT2 n744_s1 (
    .F(n744_6),
    .I0(running_d),
    .I1(n712_1) 
);
defparam n744_s1.INIT=4'h8;
  LUT2 n745_s1 (
    .F(n745_6),
    .I0(running_d),
    .I1(n713_1) 
);
defparam n745_s1.INIT=4'h8;
  LUT2 n746_s1 (
    .F(n746_6),
    .I0(running_d),
    .I1(n714_1) 
);
defparam n746_s1.INIT=4'h8;
  LUT2 n747_s1 (
    .F(n747_6),
    .I0(running_d),
    .I1(n715_1) 
);
defparam n747_s1.INIT=4'h8;
  LUT2 n748_s1 (
    .F(n748_6),
    .I0(running_d),
    .I1(n716_1) 
);
defparam n748_s1.INIT=4'h8;
  LUT2 n749_s1 (
    .F(n749_6),
    .I0(running_d),
    .I1(n717_1) 
);
defparam n749_s1.INIT=4'h8;
  LUT2 n750_s1 (
    .F(n750_6),
    .I0(running_d),
    .I1(n718_1) 
);
defparam n750_s1.INIT=4'h8;
  LUT2 n751_s1 (
    .F(n751_6),
    .I0(running_d),
    .I1(n719_1) 
);
defparam n751_s1.INIT=4'h8;
  LUT2 n752_s1 (
    .F(n752_6),
    .I0(running_d),
    .I1(n720_1) 
);
defparam n752_s1.INIT=4'h8;
  LUT2 n753_s1 (
    .F(n753_6),
    .I0(running_d),
    .I1(n721_1) 
);
defparam n753_s1.INIT=4'h8;
  LUT2 n754_s1 (
    .F(n754_6),
    .I0(running_d),
    .I1(n722_1) 
);
defparam n754_s1.INIT=4'h8;
  LUT2 n755_s1 (
    .F(n755_6),
    .I0(running_d),
    .I1(n723_1) 
);
defparam n755_s1.INIT=4'h8;
  LUT2 n756_s1 (
    .F(n756_6),
    .I0(running_d),
    .I1(n724_1) 
);
defparam n756_s1.INIT=4'h8;
  LUT2 n757_s1 (
    .F(n757_6),
    .I0(running_d),
    .I1(n725_1) 
);
defparam n757_s1.INIT=4'h8;
  LUT2 n758_s1 (
    .F(n758_6),
    .I0(running_d),
    .I1(n726_1) 
);
defparam n758_s1.INIT=4'h8;
  LUT2 n824_s1 (
    .F(n824_6),
    .I0(running_d),
    .I1(n792_1) 
);
defparam n824_s1.INIT=4'h8;
  LUT2 n825_s1 (
    .F(n825_6),
    .I0(running_d),
    .I1(n793_1) 
);
defparam n825_s1.INIT=4'h8;
  LUT2 n826_s1 (
    .F(n826_6),
    .I0(running_d),
    .I1(n794_1) 
);
defparam n826_s1.INIT=4'h8;
  LUT2 n827_s1 (
    .F(n827_6),
    .I0(running_d),
    .I1(n795_1) 
);
defparam n827_s1.INIT=4'h8;
  LUT2 n828_s1 (
    .F(n828_6),
    .I0(running_d),
    .I1(n796_1) 
);
defparam n828_s1.INIT=4'h8;
  LUT2 n829_s1 (
    .F(n829_6),
    .I0(running_d),
    .I1(n797_1) 
);
defparam n829_s1.INIT=4'h8;
  LUT2 n830_s1 (
    .F(n830_6),
    .I0(running_d),
    .I1(n798_1) 
);
defparam n830_s1.INIT=4'h8;
  LUT2 n831_s1 (
    .F(n831_6),
    .I0(running_d),
    .I1(n799_1) 
);
defparam n831_s1.INIT=4'h8;
  LUT2 n832_s1 (
    .F(n832_6),
    .I0(running_d),
    .I1(n800_1) 
);
defparam n832_s1.INIT=4'h8;
  LUT2 n833_s1 (
    .F(n833_6),
    .I0(running_d),
    .I1(n801_1) 
);
defparam n833_s1.INIT=4'h8;
  LUT2 n834_s1 (
    .F(n834_6),
    .I0(running_d),
    .I1(n802_1) 
);
defparam n834_s1.INIT=4'h8;
  LUT2 n835_s1 (
    .F(n835_6),
    .I0(running_d),
    .I1(n803_1) 
);
defparam n835_s1.INIT=4'h8;
  LUT2 n836_s1 (
    .F(n836_6),
    .I0(running_d),
    .I1(n804_1) 
);
defparam n836_s1.INIT=4'h8;
  LUT2 n837_s1 (
    .F(n837_6),
    .I0(running_d),
    .I1(n805_1) 
);
defparam n837_s1.INIT=4'h8;
  LUT2 n838_s1 (
    .F(n838_6),
    .I0(running_d),
    .I1(n806_1) 
);
defparam n838_s1.INIT=4'h8;
  LUT2 n839_s1 (
    .F(n839_6),
    .I0(running_d),
    .I1(n807_1) 
);
defparam n839_s1.INIT=4'h8;
  LUT2 n840_s1 (
    .F(n840_6),
    .I0(running_d),
    .I1(n808_1) 
);
defparam n840_s1.INIT=4'h8;
  LUT2 n841_s1 (
    .F(n841_6),
    .I0(running_d),
    .I1(n809_1) 
);
defparam n841_s1.INIT=4'h8;
  LUT2 n842_s1 (
    .F(n842_6),
    .I0(running_d),
    .I1(n810_1) 
);
defparam n842_s1.INIT=4'h8;
  LUT2 n843_s1 (
    .F(n843_6),
    .I0(running_d),
    .I1(n811_1) 
);
defparam n843_s1.INIT=4'h8;
  LUT2 n844_s1 (
    .F(n844_6),
    .I0(running_d),
    .I1(n812_1) 
);
defparam n844_s1.INIT=4'h8;
  LUT2 n845_s1 (
    .F(n845_6),
    .I0(running_d),
    .I1(n813_1) 
);
defparam n845_s1.INIT=4'h8;
  LUT2 n846_s1 (
    .F(n846_6),
    .I0(running_d),
    .I1(n814_1) 
);
defparam n846_s1.INIT=4'h8;
  LUT2 n847_s1 (
    .F(n847_6),
    .I0(running_d),
    .I1(n815_1) 
);
defparam n847_s1.INIT=4'h8;
  LUT2 n848_s1 (
    .F(n848_6),
    .I0(running_d),
    .I1(n816_1) 
);
defparam n848_s1.INIT=4'h8;
  LUT2 n849_s1 (
    .F(n849_6),
    .I0(running_d),
    .I1(n817_1) 
);
defparam n849_s1.INIT=4'h8;
  LUT2 n850_s1 (
    .F(n850_6),
    .I0(running_d),
    .I1(n818_1) 
);
defparam n850_s1.INIT=4'h8;
  LUT2 n851_s1 (
    .F(n851_6),
    .I0(running_d),
    .I1(n819_1) 
);
defparam n851_s1.INIT=4'h8;
  LUT2 n852_s1 (
    .F(n852_6),
    .I0(running_d),
    .I1(n820_1) 
);
defparam n852_s1.INIT=4'h8;
  LUT2 n853_s1 (
    .F(n853_6),
    .I0(running_d),
    .I1(n821_1) 
);
defparam n853_s1.INIT=4'h8;
  LUT2 n854_s1 (
    .F(n854_6),
    .I0(running_d),
    .I1(n822_1) 
);
defparam n854_s1.INIT=4'h8;
  LUT2 n855_s1 (
    .F(n855_6),
    .I0(running_d),
    .I1(n823_1) 
);
defparam n855_s1.INIT=4'h8;
  LUT2 n887_s1 (
    .F(n887_6),
    .I0(n871_3),
    .I1(\sine_q[3] [0]) 
);
defparam n887_s1.INIT=4'h8;
  LUT2 n886_s1 (
    .F(n886_6),
    .I0(n871_3),
    .I1(\sine_q[3] [1]) 
);
defparam n886_s1.INIT=4'h8;
  LUT2 n885_s1 (
    .F(n885_6),
    .I0(n871_3),
    .I1(\sine_q[3] [2]) 
);
defparam n885_s1.INIT=4'h8;
  LUT2 n884_s1 (
    .F(n884_6),
    .I0(n871_3),
    .I1(\sine_q[3] [3]) 
);
defparam n884_s1.INIT=4'h8;
  LUT2 n883_s1 (
    .F(n883_6),
    .I0(n871_3),
    .I1(\sine_q[3] [4]) 
);
defparam n883_s1.INIT=4'h8;
  LUT2 n882_s1 (
    .F(n882_6),
    .I0(n871_3),
    .I1(\sine_q[3] [5]) 
);
defparam n882_s1.INIT=4'h8;
  LUT2 n881_s1 (
    .F(n881_6),
    .I0(n871_3),
    .I1(\sine_q[3] [6]) 
);
defparam n881_s1.INIT=4'h8;
  LUT2 n880_s1 (
    .F(n880_6),
    .I0(n871_3),
    .I1(\sine_q[3] [7]) 
);
defparam n880_s1.INIT=4'h8;
  LUT2 n879_s1 (
    .F(n879_6),
    .I0(n871_3),
    .I1(\sine_q[3] [8]) 
);
defparam n879_s1.INIT=4'h8;
  LUT2 n878_s1 (
    .F(n878_6),
    .I0(n871_3),
    .I1(\sine_q[3] [9]) 
);
defparam n878_s1.INIT=4'h8;
  LUT2 n877_s1 (
    .F(n877_6),
    .I0(n871_3),
    .I1(\sine_q[3] [10]) 
);
defparam n877_s1.INIT=4'h8;
  LUT2 n876_s1 (
    .F(n876_6),
    .I0(n871_3),
    .I1(\sine_q[3] [11]) 
);
defparam n876_s1.INIT=4'h8;
  LUT2 n875_s1 (
    .F(n875_6),
    .I0(n871_3),
    .I1(\sine_q[3] [12]) 
);
defparam n875_s1.INIT=4'h8;
  LUT2 n874_s1 (
    .F(n874_6),
    .I0(n871_3),
    .I1(\sine_q[3] [13]) 
);
defparam n874_s1.INIT=4'h8;
  LUT2 n873_s1 (
    .F(n873_6),
    .I0(n871_3),
    .I1(\sine_q[3] [14]) 
);
defparam n873_s1.INIT=4'h8;
  LUT2 n872_s1 (
    .F(n872_6),
    .I0(n871_3),
    .I1(\sine_q[3] [15]) 
);
defparam n872_s1.INIT=4'h8;
  LUT2 n790_s1 (
    .F(n790_6),
    .I0(n871_3),
    .I1(\sine_q[2] [0]) 
);
defparam n790_s1.INIT=4'h8;
  LUT2 n789_s1 (
    .F(n789_6),
    .I0(n871_3),
    .I1(\sine_q[2] [1]) 
);
defparam n789_s1.INIT=4'h8;
  LUT2 n788_s1 (
    .F(n788_6),
    .I0(n871_3),
    .I1(\sine_q[2] [2]) 
);
defparam n788_s1.INIT=4'h8;
  LUT2 n787_s1 (
    .F(n787_6),
    .I0(n871_3),
    .I1(\sine_q[2] [3]) 
);
defparam n787_s1.INIT=4'h8;
  LUT2 n786_s1 (
    .F(n786_6),
    .I0(n871_3),
    .I1(\sine_q[2] [4]) 
);
defparam n786_s1.INIT=4'h8;
  LUT2 n785_s1 (
    .F(n785_6),
    .I0(n871_3),
    .I1(\sine_q[2] [5]) 
);
defparam n785_s1.INIT=4'h8;
  LUT2 n784_s1 (
    .F(n784_6),
    .I0(n871_3),
    .I1(\sine_q[2] [6]) 
);
defparam n784_s1.INIT=4'h8;
  LUT2 n783_s1 (
    .F(n783_6),
    .I0(n871_3),
    .I1(\sine_q[2] [7]) 
);
defparam n783_s1.INIT=4'h8;
  LUT2 n782_s1 (
    .F(n782_6),
    .I0(n871_3),
    .I1(\sine_q[2] [8]) 
);
defparam n782_s1.INIT=4'h8;
  LUT2 n781_s1 (
    .F(n781_6),
    .I0(n871_3),
    .I1(\sine_q[2] [9]) 
);
defparam n781_s1.INIT=4'h8;
  LUT2 n780_s1 (
    .F(n780_6),
    .I0(n871_3),
    .I1(\sine_q[2] [10]) 
);
defparam n780_s1.INIT=4'h8;
  LUT2 n779_s1 (
    .F(n779_6),
    .I0(n871_3),
    .I1(\sine_q[2] [11]) 
);
defparam n779_s1.INIT=4'h8;
  LUT2 n778_s1 (
    .F(n778_6),
    .I0(n871_3),
    .I1(\sine_q[2] [12]) 
);
defparam n778_s1.INIT=4'h8;
  LUT2 n777_s1 (
    .F(n777_6),
    .I0(n871_3),
    .I1(\sine_q[2] [13]) 
);
defparam n777_s1.INIT=4'h8;
  LUT2 n776_s1 (
    .F(n776_6),
    .I0(n871_3),
    .I1(\sine_q[2] [14]) 
);
defparam n776_s1.INIT=4'h8;
  LUT2 n775_s1 (
    .F(n775_6),
    .I0(n871_3),
    .I1(\sine_q[2] [15]) 
);
defparam n775_s1.INIT=4'h8;
  LUT2 n693_s1 (
    .F(n693_6),
    .I0(n871_3),
    .I1(\sine_q[1] [0]) 
);
defparam n693_s1.INIT=4'h8;
  LUT2 n692_s1 (
    .F(n692_6),
    .I0(n871_3),
    .I1(\sine_q[1] [1]) 
);
defparam n692_s1.INIT=4'h8;
  LUT2 n691_s1 (
    .F(n691_6),
    .I0(n871_3),
    .I1(\sine_q[1] [2]) 
);
defparam n691_s1.INIT=4'h8;
  LUT2 n690_s1 (
    .F(n690_6),
    .I0(n871_3),
    .I1(\sine_q[1] [3]) 
);
defparam n690_s1.INIT=4'h8;
  LUT2 n689_s1 (
    .F(n689_6),
    .I0(n871_3),
    .I1(\sine_q[1] [4]) 
);
defparam n689_s1.INIT=4'h8;
  LUT2 n688_s1 (
    .F(n688_6),
    .I0(n871_3),
    .I1(\sine_q[1] [5]) 
);
defparam n688_s1.INIT=4'h8;
  LUT2 n687_s1 (
    .F(n687_6),
    .I0(n871_3),
    .I1(\sine_q[1] [6]) 
);
defparam n687_s1.INIT=4'h8;
  LUT2 n686_s1 (
    .F(n686_6),
    .I0(n871_3),
    .I1(\sine_q[1] [7]) 
);
defparam n686_s1.INIT=4'h8;
  LUT2 n685_s1 (
    .F(n685_6),
    .I0(n871_3),
    .I1(\sine_q[1] [8]) 
);
defparam n685_s1.INIT=4'h8;
  LUT2 n684_s1 (
    .F(n684_6),
    .I0(n871_3),
    .I1(\sine_q[1] [9]) 
);
defparam n684_s1.INIT=4'h8;
  LUT2 n683_s1 (
    .F(n683_6),
    .I0(n871_3),
    .I1(\sine_q[1] [10]) 
);
defparam n683_s1.INIT=4'h8;
  LUT2 n682_s1 (
    .F(n682_6),
    .I0(n871_3),
    .I1(\sine_q[1] [11]) 
);
defparam n682_s1.INIT=4'h8;
  LUT2 n681_s1 (
    .F(n681_6),
    .I0(n871_3),
    .I1(\sine_q[1] [12]) 
);
defparam n681_s1.INIT=4'h8;
  LUT2 n680_s1 (
    .F(n680_6),
    .I0(n871_3),
    .I1(\sine_q[1] [13]) 
);
defparam n680_s1.INIT=4'h8;
  LUT2 n679_s1 (
    .F(n679_6),
    .I0(n871_3),
    .I1(\sine_q[1] [14]) 
);
defparam n679_s1.INIT=4'h8;
  LUT2 n678_s1 (
    .F(n678_6),
    .I0(n871_3),
    .I1(\sine_q[1] [15]) 
);
defparam n678_s1.INIT=4'h8;
  LUT2 n596_s1 (
    .F(n596_6),
    .I0(n871_3),
    .I1(\sine_q[0] [0]) 
);
defparam n596_s1.INIT=4'h8;
  LUT2 n595_s1 (
    .F(n595_6),
    .I0(n871_3),
    .I1(\sine_q[0] [1]) 
);
defparam n595_s1.INIT=4'h8;
  LUT2 n594_s1 (
    .F(n594_6),
    .I0(n871_3),
    .I1(\sine_q[0] [2]) 
);
defparam n594_s1.INIT=4'h8;
  LUT2 n593_s1 (
    .F(n593_6),
    .I0(n871_3),
    .I1(\sine_q[0] [3]) 
);
defparam n593_s1.INIT=4'h8;
  LUT2 n592_s1 (
    .F(n592_6),
    .I0(n871_3),
    .I1(\sine_q[0] [4]) 
);
defparam n592_s1.INIT=4'h8;
  LUT2 n591_s1 (
    .F(n591_6),
    .I0(n871_3),
    .I1(\sine_q[0] [5]) 
);
defparam n591_s1.INIT=4'h8;
  LUT2 n590_s1 (
    .F(n590_6),
    .I0(n871_3),
    .I1(\sine_q[0] [6]) 
);
defparam n590_s1.INIT=4'h8;
  LUT2 n589_s1 (
    .F(n589_6),
    .I0(n871_3),
    .I1(\sine_q[0] [7]) 
);
defparam n589_s1.INIT=4'h8;
  LUT2 n588_s1 (
    .F(n588_6),
    .I0(n871_3),
    .I1(\sine_q[0] [8]) 
);
defparam n588_s1.INIT=4'h8;
  LUT2 n587_s1 (
    .F(n587_6),
    .I0(n871_3),
    .I1(\sine_q[0] [9]) 
);
defparam n587_s1.INIT=4'h8;
  LUT2 n586_s1 (
    .F(n586_6),
    .I0(n871_3),
    .I1(\sine_q[0] [10]) 
);
defparam n586_s1.INIT=4'h8;
  LUT2 n585_s1 (
    .F(n585_6),
    .I0(n871_3),
    .I1(\sine_q[0] [11]) 
);
defparam n585_s1.INIT=4'h8;
  LUT2 n584_s1 (
    .F(n584_6),
    .I0(n871_3),
    .I1(\sine_q[0] [12]) 
);
defparam n584_s1.INIT=4'h8;
  LUT2 n583_s1 (
    .F(n583_6),
    .I0(n871_3),
    .I1(\sine_q[0] [13]) 
);
defparam n583_s1.INIT=4'h8;
  LUT2 n582_s1 (
    .F(n582_6),
    .I0(n871_3),
    .I1(\sine_q[0] [14]) 
);
defparam n582_s1.INIT=4'h8;
  LUT2 n581_s1 (
    .F(n581_6),
    .I0(n871_3),
    .I1(\sine_q[0] [15]) 
);
defparam n581_s1.INIT=4'h8;
  LUT4 n3584_s1 (
    .F(n3584_5),
    .I0(n3584_9),
    .I1(n3584_10),
    .I2(n3584_11),
    .I3(n3584_12) 
);
defparam n3584_s1.INIT=16'h8000;
  LUT4 n3584_s2 (
    .F(n3584_6),
    .I0(n3584_13),
    .I1(n3584_14),
    .I2(n3584_15),
    .I3(n3584_16) 
);
defparam n3584_s2.INIT=16'h8000;
  LUT3 n3584_s3 (
    .F(n3584_7),
    .I0(n3584_17),
    .I1(n3584_18),
    .I2(n3584_19) 
);
defparam n3584_s3.INIT=8'h80;
  LUT3 n3584_s4 (
    .F(n3584_8),
    .I0(measuring),
    .I1(valid_pipe[2]),
    .I2(running_d) 
);
defparam n3584_s4.INIT=8'h80;
  LUT4 n3583_s1 (
    .F(n3583_4),
    .I0(valid_pipe[0]),
    .I1(valid_pipe[1]),
    .I2(valid_pipe[2]),
    .I3(sample_valid_d) 
);
defparam n3583_s1.INIT=16'h0001;
  LUT4 timer_31_s5 (
    .F(timer_31_10),
    .I0(timer_31_11),
    .I1(timer_31_12),
    .I2(n313_8),
    .I3(n318_8) 
);
defparam timer_31_s5.INIT=16'h8000;
  LUT4 n328_s3 (
    .F(n328_8),
    .I0(timer[0]),
    .I1(timer[1]),
    .I2(timer[2]),
    .I3(timer[3]) 
);
defparam n328_s3.INIT=16'h7F80;
  LUT4 n327_s3 (
    .F(n327_8),
    .I0(timer[0]),
    .I1(timer[1]),
    .I2(timer[2]),
    .I3(timer[3]) 
);
defparam n327_s3.INIT=16'h8000;
  LUT4 n325_s3 (
    .F(n325_8),
    .I0(n327_8),
    .I1(timer[4]),
    .I2(timer[5]),
    .I3(timer[6]) 
);
defparam n325_s3.INIT=16'h7F80;
  LUT4 n324_s3 (
    .F(n324_8),
    .I0(n327_8),
    .I1(timer[4]),
    .I2(timer[5]),
    .I3(timer[6]) 
);
defparam n324_s3.INIT=16'h8000;
  LUT2 n323_s3 (
    .F(n323_8),
    .I0(n327_8),
    .I1(n323_9) 
);
defparam n323_s3.INIT=4'h8;
  LUT2 n321_s3 (
    .F(n321_8),
    .I0(timer[8]),
    .I1(timer[9]) 
);
defparam n321_s3.INIT=4'h8;
  LUT4 n318_s3 (
    .F(n318_8),
    .I0(n327_8),
    .I1(n318_9),
    .I2(n323_9),
    .I3(timer[8]) 
);
defparam n318_s3.INIT=16'h8000;
  LUT2 n316_s3 (
    .F(n316_8),
    .I0(timer[13]),
    .I1(timer[14]) 
);
defparam n316_s3.INIT=4'h8;
  LUT4 n313_s3 (
    .F(n313_8),
    .I0(n316_8),
    .I1(timer[15]),
    .I2(timer[16]),
    .I3(timer[17]) 
);
defparam n313_s3.INIT=16'h8000;
  LUT3 n312_s3 (
    .F(n312_8),
    .I0(n313_8),
    .I1(n318_8),
    .I2(timer[18]) 
);
defparam n312_s3.INIT=8'h80;
  LUT4 n311_s3 (
    .F(n311_8),
    .I0(n313_8),
    .I1(n318_8),
    .I2(timer[18]),
    .I3(timer[19]) 
);
defparam n311_s3.INIT=16'h8000;
  LUT2 n309_s3 (
    .F(n309_8),
    .I0(timer[20]),
    .I1(timer[21]) 
);
defparam n309_s3.INIT=4'h8;
  LUT3 n308_s3 (
    .F(n308_8),
    .I0(timer_31_12),
    .I1(n313_8),
    .I2(n318_8) 
);
defparam n308_s3.INIT=8'h80;
  LUT4 n307_s3 (
    .F(n307_8),
    .I0(timer_31_12),
    .I1(n313_8),
    .I2(n318_8),
    .I3(timer[23]) 
);
defparam n307_s3.INIT=16'h8000;
  LUT2 n305_s3 (
    .F(n305_8),
    .I0(timer[24]),
    .I1(timer[25]) 
);
defparam n305_s3.INIT=4'h8;
  LUT2 n301_s3 (
    .F(n301_8),
    .I0(timer[28]),
    .I1(timer[29]) 
);
defparam n301_s3.INIT=4'h8;
  LUT4 active_count_d_2_s0 (
    .F(active_count_d_2_5),
    .I0(active_count_d_2_6),
    .I1(active_count_d_2_7),
    .I2(active_count_d_0_6),
    .I3(active_count_d_0_7) 
);
defparam active_count_d_2_s0.INIT=16'h0001;
  LUT3 active_count_d_1_s0 (
    .F(active_count_d_1_5),
    .I0(active_count_d_2_6),
    .I1(active_count_d_2_7),
    .I2(active_count_d_0_6) 
);
defparam active_count_d_1_s0.INIT=8'h17;
  LUT4 active_count_d_1_s1 (
    .F(active_count_d_1_6),
    .I0(active_count_d_0_7),
    .I1(active_count_d_2_6),
    .I2(active_count_d_2_7),
    .I3(active_count_d_0_6) 
);
defparam active_count_d_1_s1.INIT=16'h1441;
  LUT2 active_count_d_0_s0 (
    .F(active_count_d_0_5),
    .I0(active_count_d_2_6),
    .I1(active_count_d_2_7) 
);
defparam active_count_d_0_s0.INIT=4'h9;
  LUT4 active_count_d_0_s1 (
    .F(active_count_d_0_6),
    .I0(gains_d[18]),
    .I1(gains_d[19]),
    .I2(gains_d[20]),
    .I3(active_count_d_0_8) 
);
defparam active_count_d_0_s1.INIT=16'h0100;
  LUT4 active_count_d_0_s2 (
    .F(active_count_d_0_7),
    .I0(gains_d[25]),
    .I1(gains_d[26]),
    .I2(gains_d[27]),
    .I3(active_count_d_0_9) 
);
defparam active_count_d_0_s2.INIT=16'h0100;
  LUT4 n3584_s5 (
    .F(n3584_9),
    .I0(mix_l[18]),
    .I1(mix_l[19]),
    .I2(mix_l[33]),
    .I3(mix_r[0]) 
);
defparam n3584_s5.INIT=16'h0001;
  LUT4 n3584_s6 (
    .F(n3584_10),
    .I0(mix_l[14]),
    .I1(mix_l[15]),
    .I2(mix_l[16]),
    .I3(mix_l[17]) 
);
defparam n3584_s6.INIT=16'h0001;
  LUT4 n3584_s7 (
    .F(n3584_11),
    .I0(mix_r[5]),
    .I1(mix_r[6]),
    .I2(mix_r[7]),
    .I3(mix_r[8]) 
);
defparam n3584_s7.INIT=16'h0001;
  LUT4 n3584_s8 (
    .F(n3584_12),
    .I0(mix_r[1]),
    .I1(mix_r[2]),
    .I2(mix_r[3]),
    .I3(mix_r[4]) 
);
defparam n3584_s8.INIT=16'h0001;
  LUT2 n3584_s9 (
    .F(n3584_13),
    .I0(mix_l[0]),
    .I1(mix_l[1]) 
);
defparam n3584_s9.INIT=4'h1;
  LUT4 n3584_s10 (
    .F(n3584_14),
    .I0(mix_l[2]),
    .I1(mix_l[3]),
    .I2(mix_l[4]),
    .I3(mix_l[5]) 
);
defparam n3584_s10.INIT=16'h0001;
  LUT4 n3584_s11 (
    .F(n3584_15),
    .I0(mix_l[10]),
    .I1(mix_l[11]),
    .I2(mix_l[12]),
    .I3(mix_l[13]) 
);
defparam n3584_s11.INIT=16'h0001;
  LUT4 n3584_s12 (
    .F(n3584_16),
    .I0(mix_l[6]),
    .I1(mix_l[7]),
    .I2(mix_l[8]),
    .I3(mix_l[9]) 
);
defparam n3584_s12.INIT=16'h0001;
  LUT4 n3584_s13 (
    .F(n3584_17),
    .I0(mix_r[17]),
    .I1(mix_r[18]),
    .I2(mix_r[19]),
    .I3(mix_r[33]) 
);
defparam n3584_s13.INIT=16'h0001;
  LUT4 n3584_s14 (
    .F(n3584_18),
    .I0(mix_r[13]),
    .I1(mix_r[14]),
    .I2(mix_r[15]),
    .I3(mix_r[16]) 
);
defparam n3584_s14.INIT=16'h0001;
  LUT4 n3584_s15 (
    .F(n3584_19),
    .I0(mix_r[9]),
    .I1(mix_r[10]),
    .I2(mix_r[11]),
    .I3(mix_r[12]) 
);
defparam n3584_s15.INIT=16'h0001;
  LUT4 timer_31_s6 (
    .F(timer_31_11),
    .I0(n305_8),
    .I1(timer[23]),
    .I2(timer[26]),
    .I3(timer[27]) 
);
defparam timer_31_s6.INIT=16'h8000;
  LUT4 timer_31_s7 (
    .F(timer_31_12),
    .I0(n309_8),
    .I1(timer[18]),
    .I2(timer[19]),
    .I3(timer[22]) 
);
defparam timer_31_s7.INIT=16'h8000;
  LUT4 n323_s4 (
    .F(n323_9),
    .I0(timer[4]),
    .I1(timer[5]),
    .I2(timer[6]),
    .I3(timer[7]) 
);
defparam n323_s4.INIT=16'h8000;
  LUT4 n318_s4 (
    .F(n318_9),
    .I0(timer[9]),
    .I1(timer[10]),
    .I2(timer[11]),
    .I3(timer[12]) 
);
defparam n318_s4.INIT=16'h8000;
  LUT4 active_count_d_2_s1 (
    .F(active_count_d_2_6),
    .I0(gains_d[4]),
    .I1(gains_d[5]),
    .I2(gains_d[6]),
    .I3(active_count_d_2_8) 
);
defparam active_count_d_2_s1.INIT=16'h0100;
  LUT4 active_count_d_2_s2 (
    .F(active_count_d_2_7),
    .I0(gains_d[11]),
    .I1(gains_d[12]),
    .I2(gains_d[13]),
    .I3(active_count_d_2_9) 
);
defparam active_count_d_2_s2.INIT=16'h0100;
  LUT4 active_count_d_0_s3 (
    .F(active_count_d_0_8),
    .I0(gains_d[14]),
    .I1(gains_d[15]),
    .I2(gains_d[16]),
    .I3(gains_d[17]) 
);
defparam active_count_d_0_s3.INIT=16'h0001;
  LUT4 active_count_d_0_s4 (
    .F(active_count_d_0_9),
    .I0(gains_d[21]),
    .I1(gains_d[22]),
    .I2(gains_d[23]),
    .I3(gains_d[24]) 
);
defparam active_count_d_0_s4.INIT=16'h0001;
  LUT4 active_count_d_2_s3 (
    .F(active_count_d_2_8),
    .I0(gains_d[0]),
    .I1(gains_d[1]),
    .I2(gains_d[2]),
    .I3(gains_d[3]) 
);
defparam active_count_d_2_s3.INIT=16'h0001;
  LUT4 active_count_d_2_s4 (
    .F(active_count_d_2_9),
    .I0(gains_d[7]),
    .I1(gains_d[8]),
    .I2(gains_d[9]),
    .I3(gains_d[10]) 
);
defparam active_count_d_2_s4.INIT=16'h0001;
  LUT4 n320_s4 (
    .F(n320_10),
    .I0(n323_8),
    .I1(timer[8]),
    .I2(timer[9]),
    .I3(timer[10]) 
);
defparam n320_s4.INIT=16'h8000;
  LUT3 n300_s4 (
    .F(n300_10),
    .I0(timer[28]),
    .I1(timer[29]),
    .I2(timer[30]) 
);
defparam n300_s4.INIT=8'h80;
  LUT4 timer_31_s8 (
    .F(timer_31_14),
    .I0(timer[28]),
    .I1(timer[29]),
    .I2(timer[30]),
    .I3(timer[31]) 
);
defparam timer_31_s8.INIT=16'h8000;
  LUT3 n304_s4 (
    .F(n304_10),
    .I0(timer[24]),
    .I1(timer[25]),
    .I2(timer[26]) 
);
defparam n304_s4.INIT=8'h80;
  LUT4 n315_s4 (
    .F(n315_10),
    .I0(n318_8),
    .I1(timer[13]),
    .I2(timer[14]),
    .I3(timer[15]) 
);
defparam n315_s4.INIT=16'h8000;
  LUT4 n323_s5 (
    .F(n323_11),
    .I0(start_event_d),
    .I1(n327_8),
    .I2(n323_9),
    .I3(timer[8]) 
);
defparam n323_s5.INIT=16'h1540;
  LUT4 n364_s3 (
    .F(n364_9),
    .I0(n3584_5),
    .I1(n3584_6),
    .I2(n3584_7),
    .I3(n3584_8) 
);
defparam n364_s3.INIT=16'h80FF;
  DFFCE sample_l_22_s1 (
    .Q(sample_l_d[22]),
    .D(mix_l[16]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(valid_pipe[2]) 
);
  DFFCE sample_l_21_s1 (
    .Q(sample_l_d[21]),
    .D(mix_l[15]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(valid_pipe[2]) 
);
  DFFCE sample_l_20_s1 (
    .Q(sample_l_d[20]),
    .D(mix_l[14]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(valid_pipe[2]) 
);
  DFFCE sample_l_19_s1 (
    .Q(sample_l_d[19]),
    .D(mix_l[13]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(valid_pipe[2]) 
);
  DFFCE sample_l_18_s1 (
    .Q(sample_l_d[18]),
    .D(mix_l[12]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(valid_pipe[2]) 
);
  DFFCE sample_l_17_s1 (
    .Q(sample_l_d[17]),
    .D(mix_l[11]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(valid_pipe[2]) 
);
  DFFCE sample_l_16_s1 (
    .Q(sample_l_d[16]),
    .D(mix_l[10]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(valid_pipe[2]) 
);
  DFFCE sample_l_15_s1 (
    .Q(sample_l_d[15]),
    .D(mix_l[9]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(valid_pipe[2]) 
);
  DFFCE sample_l_14_s1 (
    .Q(sample_l_d[14]),
    .D(mix_l[8]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(valid_pipe[2]) 
);
  DFFCE sample_l_13_s1 (
    .Q(sample_l_d[13]),
    .D(mix_l[7]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(valid_pipe[2]) 
);
  DFFCE sample_l_12_s1 (
    .Q(sample_l_d[12]),
    .D(mix_l[6]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(valid_pipe[2]) 
);
  DFFCE sample_l_11_s1 (
    .Q(sample_l_d[11]),
    .D(mix_l[5]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(valid_pipe[2]) 
);
  DFFCE sample_l_10_s1 (
    .Q(sample_l_d[10]),
    .D(mix_l[4]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(valid_pipe[2]) 
);
  DFFCE sample_l_9_s1 (
    .Q(sample_l_d[9]),
    .D(mix_l[3]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(valid_pipe[2]) 
);
  DFFCE sample_l_8_s1 (
    .Q(sample_l_d[8]),
    .D(mix_l[2]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(valid_pipe[2]) 
);
  DFFCE sample_r_23_s2 (
    .Q(sample_r_d[23]),
    .D(mix_r[17]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(valid_pipe[2]) 
);
  DFFCE sample_r_22_s1 (
    .Q(sample_r_d[22]),
    .D(mix_r[16]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(valid_pipe[2]) 
);
  DFFCE sample_r_21_s1 (
    .Q(sample_r_d[21]),
    .D(mix_r[15]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(valid_pipe[2]) 
);
  DFFCE sample_r_20_s1 (
    .Q(sample_r_d[20]),
    .D(mix_r[14]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(valid_pipe[2]) 
);
  DFFCE sample_r_19_s1 (
    .Q(sample_r_d[19]),
    .D(mix_r[13]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(valid_pipe[2]) 
);
  DFFCE sample_r_18_s1 (
    .Q(sample_r_d[18]),
    .D(mix_r[12]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(valid_pipe[2]) 
);
  DFFCE sample_r_17_s1 (
    .Q(sample_r_d[17]),
    .D(mix_r[11]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(valid_pipe[2]) 
);
  DFFCE sample_r_16_s1 (
    .Q(sample_r_d[16]),
    .D(mix_r[10]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(valid_pipe[2]) 
);
  DFFCE sample_r_15_s1 (
    .Q(sample_r_d[15]),
    .D(mix_r[9]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(valid_pipe[2]) 
);
  DFFCE sample_r_14_s1 (
    .Q(sample_r_d[14]),
    .D(mix_r[8]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(valid_pipe[2]) 
);
  DFFCE sample_r_13_s1 (
    .Q(sample_r_d[13]),
    .D(mix_r[7]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(valid_pipe[2]) 
);
  DFFCE sample_r_12_s1 (
    .Q(sample_r_d[12]),
    .D(mix_r[6]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(valid_pipe[2]) 
);
  DFFCE sample_r_11_s1 (
    .Q(sample_r_d[11]),
    .D(mix_r[5]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(valid_pipe[2]) 
);
  DFFCE sample_r_10_s1 (
    .Q(sample_r_d[10]),
    .D(mix_r[4]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(valid_pipe[2]) 
);
  DFFCE sample_r_9_s1 (
    .Q(sample_r_d[9]),
    .D(mix_r[3]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(valid_pipe[2]) 
);
  DFFCE sample_r_8_s1 (
    .Q(sample_r_d[8]),
    .D(mix_r[2]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(valid_pipe[2]) 
);
  DFFCE sample_valid_s2 (
    .Q(sample_valid_d),
    .D(valid_pipe[2]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(VCC) 
);
defparam sample_valid_s2.INIT=1'b0;
  DFFCE valid_pipe_2_s0 (
    .Q(valid_pipe[2]),
    .D(valid_pipe[1]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(VCC) 
);
defparam valid_pipe_2_s0.INIT=1'b0;
  DFFCE valid_pipe_1_s0 (
    .Q(valid_pipe[1]),
    .D(valid_pipe[0]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(VCC) 
);
defparam valid_pipe_1_s0.INIT=1'b0;
  DFFCE valid_pipe_0_s0 (
    .Q(valid_pipe[0]),
    .D(sample_tick_d),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(VCC) 
);
defparam valid_pipe_0_s0.INIT=1'b0;
  DFFCE latency_cycles_31_s2 (
    .Q(latency_cycles_d[31]),
    .D(timer[31]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3584_4) 
);
  DFFCE latency_cycles_30_s1 (
    .Q(latency_cycles_d[30]),
    .D(timer[30]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3584_4) 
);
  DFFCE latency_cycles_29_s1 (
    .Q(latency_cycles_d[29]),
    .D(timer[29]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3584_4) 
);
  DFFCE latency_cycles_28_s1 (
    .Q(latency_cycles_d[28]),
    .D(timer[28]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3584_4) 
);
  DFFCE latency_cycles_27_s1 (
    .Q(latency_cycles_d[27]),
    .D(timer[27]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3584_4) 
);
  DFFCE latency_cycles_26_s1 (
    .Q(latency_cycles_d[26]),
    .D(timer[26]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3584_4) 
);
  DFFCE latency_cycles_25_s1 (
    .Q(latency_cycles_d[25]),
    .D(timer[25]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3584_4) 
);
  DFFCE latency_cycles_24_s1 (
    .Q(latency_cycles_d[24]),
    .D(timer[24]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3584_4) 
);
  DFFCE latency_cycles_23_s1 (
    .Q(latency_cycles_d[23]),
    .D(timer[23]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3584_4) 
);
  DFFCE latency_cycles_22_s1 (
    .Q(latency_cycles_d[22]),
    .D(timer[22]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3584_4) 
);
  DFFCE latency_cycles_21_s1 (
    .Q(latency_cycles_d[21]),
    .D(timer[21]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3584_4) 
);
  DFFCE latency_cycles_20_s1 (
    .Q(latency_cycles_d[20]),
    .D(timer[20]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3584_4) 
);
  DFFCE latency_cycles_19_s1 (
    .Q(latency_cycles_d[19]),
    .D(timer[19]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3584_4) 
);
  DFFCE latency_cycles_18_s1 (
    .Q(latency_cycles_d[18]),
    .D(timer[18]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3584_4) 
);
  DFFCE latency_cycles_17_s1 (
    .Q(latency_cycles_d[17]),
    .D(timer[17]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3584_4) 
);
  DFFCE latency_cycles_16_s1 (
    .Q(latency_cycles_d[16]),
    .D(timer[16]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3584_4) 
);
  DFFCE latency_cycles_15_s1 (
    .Q(latency_cycles_d[15]),
    .D(timer[15]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3584_4) 
);
  DFFCE latency_cycles_14_s1 (
    .Q(latency_cycles_d[14]),
    .D(timer[14]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3584_4) 
);
  DFFCE latency_cycles_13_s1 (
    .Q(latency_cycles_d[13]),
    .D(timer[13]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3584_4) 
);
  DFFCE latency_cycles_12_s1 (
    .Q(latency_cycles_d[12]),
    .D(timer[12]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3584_4) 
);
  DFFCE latency_cycles_11_s1 (
    .Q(latency_cycles_d[11]),
    .D(timer[11]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3584_4) 
);
  DFFCE latency_cycles_10_s1 (
    .Q(latency_cycles_d[10]),
    .D(timer[10]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3584_4) 
);
  DFFCE latency_cycles_9_s1 (
    .Q(latency_cycles_d[9]),
    .D(timer[9]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3584_4) 
);
  DFFCE latency_cycles_8_s1 (
    .Q(latency_cycles_d[8]),
    .D(timer[8]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3584_4) 
);
  DFFCE latency_cycles_7_s1 (
    .Q(latency_cycles_d[7]),
    .D(timer[7]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3584_4) 
);
  DFFCE latency_cycles_6_s1 (
    .Q(latency_cycles_d[6]),
    .D(timer[6]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3584_4) 
);
  DFFCE latency_cycles_5_s1 (
    .Q(latency_cycles_d[5]),
    .D(timer[5]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3584_4) 
);
  DFFCE latency_cycles_4_s1 (
    .Q(latency_cycles_d[4]),
    .D(timer[4]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3584_4) 
);
  DFFCE latency_cycles_3_s1 (
    .Q(latency_cycles_d[3]),
    .D(timer[3]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3584_4) 
);
  DFFCE latency_cycles_2_s1 (
    .Q(latency_cycles_d[2]),
    .D(timer[2]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3584_4) 
);
  DFFCE latency_cycles_1_s1 (
    .Q(latency_cycles_d[1]),
    .D(timer[1]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3584_4) 
);
  DFFCE latency_cycles_0_s1 (
    .Q(latency_cycles_d[0]),
    .D(timer[0]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3584_4) 
);
  DFFCE deadline_miss_s2 (
    .Q(deadline_miss_d),
    .D(VCC),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(n3583_3) 
);
  DFFCE \phase[0]_31_s0  (
    .Q(\phase[0] [31]),
    .D(n533_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[0]_30_s0  (
    .Q(\phase[0] [30]),
    .D(n534_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[0]_29_s0  (
    .Q(\phase[0] [29]),
    .D(n535_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[0]_28_s0  (
    .Q(\phase[0] [28]),
    .D(n536_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[0]_27_s0  (
    .Q(\phase[0] [27]),
    .D(n537_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[0]_26_s0  (
    .Q(\phase[0] [26]),
    .D(n538_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[0]_25_s0  (
    .Q(\phase[0] [25]),
    .D(n539_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[0]_24_s0  (
    .Q(\phase[0] [24]),
    .D(n540_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[0]_23_s0  (
    .Q(\phase[0] [23]),
    .D(n541_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[0]_22_s0  (
    .Q(\phase[0] [22]),
    .D(n542_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[1]_31_s0  (
    .Q(\phase[1] [31]),
    .D(n630_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[1]_30_s0  (
    .Q(\phase[1] [30]),
    .D(n631_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[1]_29_s0  (
    .Q(\phase[1] [29]),
    .D(n632_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[1]_28_s0  (
    .Q(\phase[1] [28]),
    .D(n633_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[1]_27_s0  (
    .Q(\phase[1] [27]),
    .D(n634_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[1]_26_s0  (
    .Q(\phase[1] [26]),
    .D(n635_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[1]_25_s0  (
    .Q(\phase[1] [25]),
    .D(n636_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[1]_24_s0  (
    .Q(\phase[1] [24]),
    .D(n637_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[1]_23_s0  (
    .Q(\phase[1] [23]),
    .D(n638_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[1]_22_s0  (
    .Q(\phase[1] [22]),
    .D(n639_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[2]_31_s0  (
    .Q(\phase[2] [31]),
    .D(n727_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[2]_30_s0  (
    .Q(\phase[2] [30]),
    .D(n728_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[2]_29_s0  (
    .Q(\phase[2] [29]),
    .D(n729_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[2]_28_s0  (
    .Q(\phase[2] [28]),
    .D(n730_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[2]_27_s0  (
    .Q(\phase[2] [27]),
    .D(n731_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[2]_26_s0  (
    .Q(\phase[2] [26]),
    .D(n732_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[2]_25_s0  (
    .Q(\phase[2] [25]),
    .D(n733_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[2]_24_s0  (
    .Q(\phase[2] [24]),
    .D(n734_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[2]_23_s0  (
    .Q(\phase[2] [23]),
    .D(n735_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[2]_22_s0  (
    .Q(\phase[2] [22]),
    .D(n736_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[3]_31_s0  (
    .Q(\phase[3] [31]),
    .D(n824_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[3]_30_s0  (
    .Q(\phase[3] [30]),
    .D(n825_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[3]_29_s0  (
    .Q(\phase[3] [29]),
    .D(n826_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[3]_28_s0  (
    .Q(\phase[3] [28]),
    .D(n827_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[3]_27_s0  (
    .Q(\phase[3] [27]),
    .D(n828_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[3]_26_s0  (
    .Q(\phase[3] [26]),
    .D(n829_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[3]_25_s0  (
    .Q(\phase[3] [25]),
    .D(n830_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[3]_24_s0  (
    .Q(\phase[3] [24]),
    .D(n831_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[3]_23_s0  (
    .Q(\phase[3] [23]),
    .D(n832_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \phase[3]_22_s0  (
    .Q(\phase[3] [22]),
    .D(n833_6),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE sample_l_23_s2 (
    .Q(sample_l_d[23]),
    .D(mix_l[17]),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(valid_pipe[2]) 
);
  DFFCE latency_valid_s3 (
    .Q(latency_valid_d),
    .D(n3584_4),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(latency_valid_7) 
);
defparam latency_valid_s3.INIT=1'b0;
  DFFCE timer_31_s1 (
    .Q(timer[31]),
    .D(n300_7),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(timer_31_8) 
);
defparam timer_31_s1.INIT=1'b0;
  DFFCE timer_30_s1 (
    .Q(timer[30]),
    .D(n301_7),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(timer_31_8) 
);
defparam timer_30_s1.INIT=1'b0;
  DFFCE timer_29_s1 (
    .Q(timer[29]),
    .D(n302_7),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(timer_31_8) 
);
defparam timer_29_s1.INIT=1'b0;
  DFFCE timer_28_s1 (
    .Q(timer[28]),
    .D(n303_7),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(timer_31_8) 
);
defparam timer_28_s1.INIT=1'b0;
  DFFCE timer_27_s1 (
    .Q(timer[27]),
    .D(n304_7),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(timer_31_8) 
);
defparam timer_27_s1.INIT=1'b0;
  DFFCE timer_26_s1 (
    .Q(timer[26]),
    .D(n305_7),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(timer_31_8) 
);
defparam timer_26_s1.INIT=1'b0;
  DFFCE timer_25_s1 (
    .Q(timer[25]),
    .D(n306_7),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(timer_31_8) 
);
defparam timer_25_s1.INIT=1'b0;
  DFFCE timer_24_s1 (
    .Q(timer[24]),
    .D(n307_7),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(timer_31_8) 
);
defparam timer_24_s1.INIT=1'b0;
  DFFCE timer_23_s1 (
    .Q(timer[23]),
    .D(n308_7),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(timer_31_8) 
);
defparam timer_23_s1.INIT=1'b0;
  DFFCE timer_22_s1 (
    .Q(timer[22]),
    .D(n309_7),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(timer_31_8) 
);
defparam timer_22_s1.INIT=1'b0;
  DFFCE timer_21_s1 (
    .Q(timer[21]),
    .D(n310_7),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(timer_31_8) 
);
defparam timer_21_s1.INIT=1'b0;
  DFFCE timer_20_s1 (
    .Q(timer[20]),
    .D(n311_7),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(timer_31_8) 
);
defparam timer_20_s1.INIT=1'b0;
  DFFCE timer_19_s1 (
    .Q(timer[19]),
    .D(n312_7),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(timer_31_8) 
);
defparam timer_19_s1.INIT=1'b0;
  DFFCE timer_18_s1 (
    .Q(timer[18]),
    .D(n313_7),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(timer_31_8) 
);
defparam timer_18_s1.INIT=1'b0;
  DFFCE timer_17_s1 (
    .Q(timer[17]),
    .D(n314_7),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(timer_31_8) 
);
defparam timer_17_s1.INIT=1'b0;
  DFFCE timer_16_s1 (
    .Q(timer[16]),
    .D(n315_7),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(timer_31_8) 
);
defparam timer_16_s1.INIT=1'b0;
  DFFCE timer_15_s1 (
    .Q(timer[15]),
    .D(n316_7),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(timer_31_8) 
);
defparam timer_15_s1.INIT=1'b0;
  DFFCE timer_14_s1 (
    .Q(timer[14]),
    .D(n317_7),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(timer_31_8) 
);
defparam timer_14_s1.INIT=1'b0;
  DFFCE timer_13_s1 (
    .Q(timer[13]),
    .D(n318_7),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(timer_31_8) 
);
defparam timer_13_s1.INIT=1'b0;
  DFFCE timer_12_s1 (
    .Q(timer[12]),
    .D(n319_7),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(timer_31_8) 
);
defparam timer_12_s1.INIT=1'b0;
  DFFCE timer_11_s1 (
    .Q(timer[11]),
    .D(n320_7),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(timer_31_8) 
);
defparam timer_11_s1.INIT=1'b0;
  DFFCE timer_10_s1 (
    .Q(timer[10]),
    .D(n321_7),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(timer_31_8) 
);
defparam timer_10_s1.INIT=1'b0;
  DFFCE timer_9_s1 (
    .Q(timer[9]),
    .D(n322_7),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(timer_31_8) 
);
defparam timer_9_s1.INIT=1'b0;
  DFFCE timer_8_s1 (
    .Q(timer[8]),
    .D(n323_11),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(timer_31_8) 
);
defparam timer_8_s1.INIT=1'b0;
  DFFCE timer_7_s1 (
    .Q(timer[7]),
    .D(n324_7),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(timer_31_8) 
);
defparam timer_7_s1.INIT=1'b0;
  DFFCE timer_6_s1 (
    .Q(timer[6]),
    .D(n325_7),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(timer_31_8) 
);
defparam timer_6_s1.INIT=1'b0;
  DFFCE timer_5_s1 (
    .Q(timer[5]),
    .D(n326_7),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(timer_31_8) 
);
defparam timer_5_s1.INIT=1'b0;
  DFFCE timer_4_s1 (
    .Q(timer[4]),
    .D(n327_7),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(timer_31_8) 
);
defparam timer_4_s1.INIT=1'b0;
  DFFCE timer_3_s1 (
    .Q(timer[3]),
    .D(n328_7),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(timer_31_8) 
);
defparam timer_3_s1.INIT=1'b0;
  DFFCE timer_2_s1 (
    .Q(timer[2]),
    .D(n329_7),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(timer_31_8) 
);
defparam timer_2_s1.INIT=1'b0;
  DFFCE timer_1_s1 (
    .Q(timer[1]),
    .D(n330_7),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(timer_31_8) 
);
defparam timer_1_s1.INIT=1'b0;
  DFFCE timer_0_s1 (
    .Q(timer[0]),
    .D(n331_8),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(timer_31_8) 
);
defparam timer_0_s1.INIT=1'b0;
  DFFCE measuring_s1 (
    .Q(measuring),
    .D(n364_9),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(latency_valid_7) 
);
defparam measuring_s1.INIT=1'b0;
  DFFCE \sine_q[3]_0_s3  (
    .Q(\sine_q[3]_0_6 ),
    .D(VCC),
    .CLK(clk_d),
    .CLEAR(n232_6),
    .CE(sample_tick_d) 
);
  DFFCE \sine_q[3]_0_s4  (
    .Q(\sine_q[3]_0_21 ),
    .D(sample_tick_d),
    .CLK(clk_d),
    .CLEAR(GND),
    .CE(VCC) 
);
defparam \sine_q[3]_0_s4 .INIT=1'b0;
  DFFRE \sine_q[3]_0_s6  (
    .Q(\sine_q[3]_0_19 ),
    .D(n887_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[3]_0_s6 .INIT=1'b0;
  DFFCE n871_s (
    .Q(n871_3),
    .D(running_d),
    .CLK(clk_d),
    .CLEAR(GND),
    .CE(VCC) 
);
defparam n871_s.INIT=1'b0;
  DFFRE \sine_q[3]_1_s4  (
    .Q(\sine_q[3]_1_17 ),
    .D(n886_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[3]_1_s4 .INIT=1'b0;
  DFFRE \sine_q[3]_2_s4  (
    .Q(\sine_q[3]_2_17 ),
    .D(n885_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[3]_2_s4 .INIT=1'b0;
  DFFRE \sine_q[3]_3_s4  (
    .Q(\sine_q[3]_3_17 ),
    .D(n884_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[3]_3_s4 .INIT=1'b0;
  DFFRE \sine_q[3]_4_s4  (
    .Q(\sine_q[3]_4_17 ),
    .D(n883_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[3]_4_s4 .INIT=1'b0;
  DFFRE \sine_q[3]_5_s4  (
    .Q(\sine_q[3]_5_17 ),
    .D(n882_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[3]_5_s4 .INIT=1'b0;
  DFFRE \sine_q[3]_6_s4  (
    .Q(\sine_q[3]_6_17 ),
    .D(n881_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[3]_6_s4 .INIT=1'b0;
  DFFRE \sine_q[3]_7_s4  (
    .Q(\sine_q[3]_7_17 ),
    .D(n880_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[3]_7_s4 .INIT=1'b0;
  DFFRE \sine_q[3]_8_s4  (
    .Q(\sine_q[3]_8_17 ),
    .D(n879_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[3]_8_s4 .INIT=1'b0;
  DFFRE \sine_q[3]_9_s4  (
    .Q(\sine_q[3]_9_17 ),
    .D(n878_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[3]_9_s4 .INIT=1'b0;
  DFFRE \sine_q[3]_10_s4  (
    .Q(\sine_q[3]_10_17 ),
    .D(n877_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[3]_10_s4 .INIT=1'b0;
  DFFRE \sine_q[3]_11_s4  (
    .Q(\sine_q[3]_11_17 ),
    .D(n876_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[3]_11_s4 .INIT=1'b0;
  DFFRE \sine_q[3]_12_s4  (
    .Q(\sine_q[3]_12_17 ),
    .D(n875_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[3]_12_s4 .INIT=1'b0;
  DFFRE \sine_q[3]_13_s4  (
    .Q(\sine_q[3]_13_17 ),
    .D(n874_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[3]_13_s4 .INIT=1'b0;
  DFFRE \sine_q[3]_14_s4  (
    .Q(\sine_q[3]_14_17 ),
    .D(n873_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[3]_14_s4 .INIT=1'b0;
  DFFRE \sine_q[3]_15_s4  (
    .Q(\sine_q[3]_15_17 ),
    .D(n872_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[3]_15_s4 .INIT=1'b0;
  DFFRE \sine_q[2]_0_s4  (
    .Q(\sine_q[2]_0_17 ),
    .D(n790_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[2]_0_s4 .INIT=1'b0;
  DFFRE \sine_q[2]_1_s4  (
    .Q(\sine_q[2]_1_17 ),
    .D(n789_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[2]_1_s4 .INIT=1'b0;
  DFFRE \sine_q[2]_2_s4  (
    .Q(\sine_q[2]_2_17 ),
    .D(n788_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[2]_2_s4 .INIT=1'b0;
  DFFRE \sine_q[2]_3_s4  (
    .Q(\sine_q[2]_3_17 ),
    .D(n787_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[2]_3_s4 .INIT=1'b0;
  DFFRE \sine_q[2]_4_s4  (
    .Q(\sine_q[2]_4_17 ),
    .D(n786_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[2]_4_s4 .INIT=1'b0;
  DFFRE \sine_q[2]_5_s4  (
    .Q(\sine_q[2]_5_17 ),
    .D(n785_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[2]_5_s4 .INIT=1'b0;
  DFFRE \sine_q[2]_6_s4  (
    .Q(\sine_q[2]_6_17 ),
    .D(n784_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[2]_6_s4 .INIT=1'b0;
  DFFRE \sine_q[2]_7_s4  (
    .Q(\sine_q[2]_7_17 ),
    .D(n783_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[2]_7_s4 .INIT=1'b0;
  DFFRE \sine_q[2]_8_s4  (
    .Q(\sine_q[2]_8_17 ),
    .D(n782_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[2]_8_s4 .INIT=1'b0;
  DFFRE \sine_q[2]_9_s4  (
    .Q(\sine_q[2]_9_17 ),
    .D(n781_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[2]_9_s4 .INIT=1'b0;
  DFFRE \sine_q[2]_10_s4  (
    .Q(\sine_q[2]_10_17 ),
    .D(n780_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[2]_10_s4 .INIT=1'b0;
  DFFRE \sine_q[2]_11_s4  (
    .Q(\sine_q[2]_11_17 ),
    .D(n779_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[2]_11_s4 .INIT=1'b0;
  DFFRE \sine_q[2]_12_s4  (
    .Q(\sine_q[2]_12_17 ),
    .D(n778_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[2]_12_s4 .INIT=1'b0;
  DFFRE \sine_q[2]_13_s4  (
    .Q(\sine_q[2]_13_17 ),
    .D(n777_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[2]_13_s4 .INIT=1'b0;
  DFFRE \sine_q[2]_14_s4  (
    .Q(\sine_q[2]_14_17 ),
    .D(n776_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[2]_14_s4 .INIT=1'b0;
  DFFRE \sine_q[2]_15_s4  (
    .Q(\sine_q[2]_15_17 ),
    .D(n775_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[2]_15_s4 .INIT=1'b0;
  DFFRE \sine_q[1]_0_s4  (
    .Q(\sine_q[1]_0_17 ),
    .D(n693_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[1]_0_s4 .INIT=1'b0;
  DFFRE \sine_q[1]_1_s4  (
    .Q(\sine_q[1]_1_17 ),
    .D(n692_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[1]_1_s4 .INIT=1'b0;
  DFFRE \sine_q[1]_2_s4  (
    .Q(\sine_q[1]_2_17 ),
    .D(n691_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[1]_2_s4 .INIT=1'b0;
  DFFRE \sine_q[1]_3_s4  (
    .Q(\sine_q[1]_3_17 ),
    .D(n690_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[1]_3_s4 .INIT=1'b0;
  DFFRE \sine_q[1]_4_s4  (
    .Q(\sine_q[1]_4_17 ),
    .D(n689_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[1]_4_s4 .INIT=1'b0;
  DFFRE \sine_q[1]_5_s4  (
    .Q(\sine_q[1]_5_17 ),
    .D(n688_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[1]_5_s4 .INIT=1'b0;
  DFFRE \sine_q[1]_6_s4  (
    .Q(\sine_q[1]_6_17 ),
    .D(n687_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[1]_6_s4 .INIT=1'b0;
  DFFRE \sine_q[1]_7_s4  (
    .Q(\sine_q[1]_7_17 ),
    .D(n686_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[1]_7_s4 .INIT=1'b0;
  DFFRE \sine_q[1]_8_s4  (
    .Q(\sine_q[1]_8_17 ),
    .D(n685_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[1]_8_s4 .INIT=1'b0;
  DFFRE \sine_q[1]_9_s4  (
    .Q(\sine_q[1]_9_17 ),
    .D(n684_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[1]_9_s4 .INIT=1'b0;
  DFFRE \sine_q[1]_10_s4  (
    .Q(\sine_q[1]_10_17 ),
    .D(n683_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[1]_10_s4 .INIT=1'b0;
  DFFRE \sine_q[1]_11_s4  (
    .Q(\sine_q[1]_11_17 ),
    .D(n682_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[1]_11_s4 .INIT=1'b0;
  DFFRE \sine_q[1]_12_s4  (
    .Q(\sine_q[1]_12_17 ),
    .D(n681_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[1]_12_s4 .INIT=1'b0;
  DFFRE \sine_q[1]_13_s4  (
    .Q(\sine_q[1]_13_17 ),
    .D(n680_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[1]_13_s4 .INIT=1'b0;
  DFFRE \sine_q[1]_14_s4  (
    .Q(\sine_q[1]_14_17 ),
    .D(n679_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[1]_14_s4 .INIT=1'b0;
  DFFRE \sine_q[1]_15_s4  (
    .Q(\sine_q[1]_15_17 ),
    .D(n678_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[1]_15_s4 .INIT=1'b0;
  DFFRE \sine_q[0]_0_s4  (
    .Q(\sine_q[0]_0_17 ),
    .D(n596_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[0]_0_s4 .INIT=1'b0;
  DFFRE \sine_q[0]_1_s4  (
    .Q(\sine_q[0]_1_17 ),
    .D(n595_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[0]_1_s4 .INIT=1'b0;
  DFFRE \sine_q[0]_2_s4  (
    .Q(\sine_q[0]_2_17 ),
    .D(n594_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[0]_2_s4 .INIT=1'b0;
  DFFRE \sine_q[0]_3_s4  (
    .Q(\sine_q[0]_3_17 ),
    .D(n593_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[0]_3_s4 .INIT=1'b0;
  DFFRE \sine_q[0]_4_s4  (
    .Q(\sine_q[0]_4_17 ),
    .D(n592_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[0]_4_s4 .INIT=1'b0;
  DFFRE \sine_q[0]_5_s4  (
    .Q(\sine_q[0]_5_17 ),
    .D(n591_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[0]_5_s4 .INIT=1'b0;
  DFFRE \sine_q[0]_6_s4  (
    .Q(\sine_q[0]_6_17 ),
    .D(n590_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[0]_6_s4 .INIT=1'b0;
  DFFRE \sine_q[0]_7_s4  (
    .Q(\sine_q[0]_7_17 ),
    .D(n589_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[0]_7_s4 .INIT=1'b0;
  DFFRE \sine_q[0]_8_s4  (
    .Q(\sine_q[0]_8_17 ),
    .D(n588_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[0]_8_s4 .INIT=1'b0;
  DFFRE \sine_q[0]_9_s4  (
    .Q(\sine_q[0]_9_17 ),
    .D(n587_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[0]_9_s4 .INIT=1'b0;
  DFFRE \sine_q[0]_10_s4  (
    .Q(\sine_q[0]_10_17 ),
    .D(n586_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[0]_10_s4 .INIT=1'b0;
  DFFRE \sine_q[0]_11_s4  (
    .Q(\sine_q[0]_11_17 ),
    .D(n585_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[0]_11_s4 .INIT=1'b0;
  DFFRE \sine_q[0]_12_s4  (
    .Q(\sine_q[0]_12_17 ),
    .D(n584_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[0]_12_s4 .INIT=1'b0;
  DFFRE \sine_q[0]_13_s4  (
    .Q(\sine_q[0]_13_17 ),
    .D(n583_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[0]_13_s4 .INIT=1'b0;
  DFFRE \sine_q[0]_14_s4  (
    .Q(\sine_q[0]_14_17 ),
    .D(n582_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[0]_14_s4 .INIT=1'b0;
  DFFRE \sine_q[0]_15_s4  (
    .Q(\sine_q[0]_15_17 ),
    .D(n581_6),
    .CLK(clk_d),
    .RESET(GND),
    .CE(\sine_q[3]_0_21 ) 
);
defparam \sine_q[0]_15_s4 .INIT=1'b0;
  pROM sine_rom_sine_rom_0_0_s (
    .DO({DO[31:16],\sine_q[0] [15:0]}),
    .CLK(clk_d),
    .CE(VCC),
    .OCE(GND),
    .RESET(GND),
    .AD({\phase[0] [31:22],GND,GND,VCC,VCC}) 
);
defparam sine_rom_sine_rom_0_0_s.BIT_WIDTH=16;
defparam sine_rom_sine_rom_0_0_s.READ_MODE=1'b0;
defparam sine_rom_sine_rom_0_0_s.RESET_MODE="SYNC";
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_00=256'h0BC40AFB0A33096A08A207D907110648057F04B603ED0324025B019200C90000;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_01=256'h1833176E16A815E2151C1455138F12C81201113A10720FAB0EE30E1C0D540C8C;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_02=256'h246723A622E522232161209F1FDD1F1A1E571D931CCF1C0B1B471A8219BE18F9;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_03=256'h30412F872ECC2E112D552C992BDC2B1F2A6129A328E52826276726A825E82528;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_04=256'h3BA53AF23A40398C38D93824376F36BA3604354D349633DF3326326E31B530FB;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_05=256'h467545CD4524447A43D04325427A41CE412140733FC53F173E683DB83D073C56;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_06=256'h50974FFB4F5D4EBF4E204D814CE04C3F4B9D4AFB4A5849B4490F486947C3471C;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_07=256'h59F3596458D3584257B0571D568A55F5556054C95432539B5302526851CE5133;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_08=256'h627161F0616E60EB60685FE35F5D5ED75E4F5DC75D3E5CB35C285B9C5B0F5A82;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_09=256'h69FD698B691968A6683267BC674666CF665665DD656364E8646C63EE637062F1;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_0A=256'h708370226FC16F5E6EFB6E966E306DC96D616CF86C8E6C236BB76B4A6ADC6A6D;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_0B=256'h75F375A57555750474B2745F740A73B5735E730772AE725471F9719D714070E2;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_0C=256'h7A417A0579C87989794A790978C77884783F77FA77B3776B772276D8768D7641;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_0D=256'h7D627D397D0E7CE37CB67C887C597C297BF87BC57B917B5C7B267AEE7AB67A7C;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_0E=256'h7F4D7F377F217F097EEF7ED57EB97E9C7E7E7E5F7E3E7E1D7DFA7DD57DB07D89;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_0F=256'h7FFE7FFD7FF97FF57FF07FE97FE17FD87FCD7FC17FB47FA67F977F867F747F61;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_10=256'h7F747F867F977FA67FB47FC17FCD7FD87FE17FE97FF07FF57FF97FFD7FFE7FFF;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_11=256'h7DB07DD57DFA7E1D7E3E7E5F7E7E7E9C7EB97ED57EEF7F097F217F377F4D7F61;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_12=256'h7AB67AEE7B267B5C7B917BC57BF87C297C597C887CB67CE37D0E7D397D627D89;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_13=256'h768D76D87722776B77B377FA783F788478C77909794A798979C87A057A417A7C;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_14=256'h7140719D71F9725472AE7307735E73B5740A745F74B27504755575A575F37641;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_15=256'h6ADC6B4A6BB76C236C8E6CF86D616DC96E306E966EFB6F5E6FC17022708370E2;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_16=256'h637063EE646C64E8656365DD665666CF674667BC683268A66919698B69FD6A6D;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_17=256'h5B0F5B9C5C285CB35D3E5DC75E4F5ED75F5D5FE3606860EB616E61F0627162F1;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_18=256'h51CE52685302539B543254C9556055F5568A571D57B0584258D3596459F35A82;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_19=256'h47C34869490F49B44A584AFB4B9D4C3F4CE04D814E204EBF4F5D4FFB50975133;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_1A=256'h3D073DB83E683F173FC54073412141CE427A432543D0447A452445CD4675471C;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_1B=256'h31B5326E332633DF3496354D360436BA376F382438D9398C3A403AF23BA53C56;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_1C=256'h25E826A82767282628E529A32A612B1F2BDC2C992D552E112ECC2F87304130FB;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_1D=256'h19BE1A821B471C0B1CCF1D931E571F1A1FDD209F2161222322E523A624672528;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_1E=256'h0D540E1C0EE30FAB1072113A120112C8138F1455151C15E216A8176E183318F9;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_1F=256'h00C90192025B032403ED04B6057F0648071107D908A2096A0A330AFB0BC40C8C;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_20=256'hF43CF505F5CDF696F75EF827F8EFF9B8FA81FB4AFC13FCDCFDA5FE6EFF370000;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_21=256'hE7CDE892E958EA1EEAE4EBABEC71ED38EDFFEEC6EF8EF055F11DF1E4F2ACF374;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_22=256'hDB99DC5ADD1BDDDDDE9FDF61E023E0E6E1A9E26DE331E3F5E4B9E57EE642E707;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_23=256'hCFBFD079D134D1EFD2ABD367D424D4E1D59FD65DD71BD7DAD899D958DA18DAD8;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_24=256'hC45BC50EC5C0C674C727C7DCC891C946C9FCCAB3CB6ACC21CCDACD92CE4BCF05;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_25=256'hB98BBA33BADCBB86BC30BCDBBD86BE32BEDFBF8DC03BC0E9C198C248C2F9C3AA;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_26=256'hAF69B005B0A3B141B1E0B27FB320B3C1B463B505B5A8B64CB6F1B797B83DB8E4;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_27=256'hA60DA69CA72DA7BEA850A8E3A976AA0BAAA0AB37ABCEAC65ACFEAD98AE32AECD;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_28=256'h9D8F9E109E929F159F98A01DA0A3A129A1B1A239A2C2A34DA3D8A464A4F1A57E;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_29=256'h9603967596E7975A97CE984498BA993199AA9A239A9D9B189B949C129C909D0F;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_2A=256'h8F7D8FDE903F90A29105916A91D09237929F9308937293DD944994B695249593;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_2B=256'h8A0D8A5B8AAB8AFC8B4E8BA18BF68C4B8CA28CF98D528DAC8E078E638EC08F1E;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_2C=256'h85BF85FB8638867786B686F78739877C87C18806884D889588DE8928897389BF;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_2D=256'h829E82C782F2831D834A837883A783D78408843B846F84A484DA8512854A8584;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_2E=256'h80B380C980DF80F78111812B81478164818281A181C281E38206822B82508277;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_2F=256'h800280038007800B80108017801F80288033803F804C805A8069807A808C809F;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_30=256'h808C807A8069805A804C803F80338028801F80178010800B8007800380028001;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_31=256'h8250822B820681E381C281A1818281648147812B811180F780DF80C980B3809F;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_32=256'h854A851284DA84A4846F843B840883D783A78378834A831D82F282C7829E8277;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_33=256'h8973892888DE8895884D880687C1877C873986F786B68677863885FB85BF8584;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_34=256'h8EC08E638E078DAC8D528CF98CA28C4B8BF68BA18B4E8AFC8AAB8A5B8A0D89BF;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_35=256'h952494B6944993DD93729308929F923791D0916A910590A2903F8FDE8F7D8F1E;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_36=256'h9C909C129B949B189A9D9A2399AA993198BA984497CE975A96E7967596039593;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_37=256'hA4F1A464A3D8A34DA2C2A239A1B1A129A0A3A01D9F989F159E929E109D8F9D0F;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_38=256'hAE32AD98ACFEAC65ABCEAB37AAA0AA0BA976A8E3A850A7BEA72DA69CA60DA57E;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_39=256'hB83DB797B6F1B64CB5A8B505B463B3C1B320B27FB1E0B141B0A3B005AF69AECD;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_3A=256'hC2F9C248C198C0E9C03BBF8DBEDFBE32BD86BCDBBC30BB86BADCBA33B98BB8E4;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_3B=256'hCE4BCD92CCDACC21CB6ACAB3C9FCC946C891C7DCC727C674C5C0C50EC45BC3AA;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_3C=256'hDA18D958D899D7DAD71BD65DD59FD4E1D424D367D2ABD1EFD134D079CFBFCF05;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_3D=256'hE642E57EE4B9E3F5E331E26DE1A9E0E6E023DF61DE9FDDDDDD1BDC5ADB99DAD8;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_3E=256'hF2ACF1E4F11DF055EF8EEEC6EDFFED38EC71EBABEAE4EA1EE958E892E7CDE707;
defparam sine_rom_sine_rom_0_0_s.INIT_RAM_3F=256'hFF37FE6EFDA5FCDCFC13FB4AFA81F9B8F8EFF827F75EF696F5CDF505F43CF374;
  pROM sine_rom_sine_rom_0_0_s0 (
    .DO({DO_0[31:16],\sine_q[1] [15:0]}),
    .CLK(clk_d),
    .CE(VCC),
    .OCE(GND),
    .RESET(GND),
    .AD({\phase[1] [31:22],GND,GND,VCC,VCC}) 
);
defparam sine_rom_sine_rom_0_0_s0.BIT_WIDTH=16;
defparam sine_rom_sine_rom_0_0_s0.READ_MODE=1'b0;
defparam sine_rom_sine_rom_0_0_s0.RESET_MODE="SYNC";
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_00=256'h0BC40AFB0A33096A08A207D907110648057F04B603ED0324025B019200C90000;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_01=256'h1833176E16A815E2151C1455138F12C81201113A10720FAB0EE30E1C0D540C8C;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_02=256'h246723A622E522232161209F1FDD1F1A1E571D931CCF1C0B1B471A8219BE18F9;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_03=256'h30412F872ECC2E112D552C992BDC2B1F2A6129A328E52826276726A825E82528;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_04=256'h3BA53AF23A40398C38D93824376F36BA3604354D349633DF3326326E31B530FB;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_05=256'h467545CD4524447A43D04325427A41CE412140733FC53F173E683DB83D073C56;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_06=256'h50974FFB4F5D4EBF4E204D814CE04C3F4B9D4AFB4A5849B4490F486947C3471C;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_07=256'h59F3596458D3584257B0571D568A55F5556054C95432539B5302526851CE5133;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_08=256'h627161F0616E60EB60685FE35F5D5ED75E4F5DC75D3E5CB35C285B9C5B0F5A82;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_09=256'h69FD698B691968A6683267BC674666CF665665DD656364E8646C63EE637062F1;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_0A=256'h708370226FC16F5E6EFB6E966E306DC96D616CF86C8E6C236BB76B4A6ADC6A6D;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_0B=256'h75F375A57555750474B2745F740A73B5735E730772AE725471F9719D714070E2;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_0C=256'h7A417A0579C87989794A790978C77884783F77FA77B3776B772276D8768D7641;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_0D=256'h7D627D397D0E7CE37CB67C887C597C297BF87BC57B917B5C7B267AEE7AB67A7C;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_0E=256'h7F4D7F377F217F097EEF7ED57EB97E9C7E7E7E5F7E3E7E1D7DFA7DD57DB07D89;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_0F=256'h7FFE7FFD7FF97FF57FF07FE97FE17FD87FCD7FC17FB47FA67F977F867F747F61;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_10=256'h7F747F867F977FA67FB47FC17FCD7FD87FE17FE97FF07FF57FF97FFD7FFE7FFF;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_11=256'h7DB07DD57DFA7E1D7E3E7E5F7E7E7E9C7EB97ED57EEF7F097F217F377F4D7F61;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_12=256'h7AB67AEE7B267B5C7B917BC57BF87C297C597C887CB67CE37D0E7D397D627D89;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_13=256'h768D76D87722776B77B377FA783F788478C77909794A798979C87A057A417A7C;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_14=256'h7140719D71F9725472AE7307735E73B5740A745F74B27504755575A575F37641;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_15=256'h6ADC6B4A6BB76C236C8E6CF86D616DC96E306E966EFB6F5E6FC17022708370E2;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_16=256'h637063EE646C64E8656365DD665666CF674667BC683268A66919698B69FD6A6D;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_17=256'h5B0F5B9C5C285CB35D3E5DC75E4F5ED75F5D5FE3606860EB616E61F0627162F1;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_18=256'h51CE52685302539B543254C9556055F5568A571D57B0584258D3596459F35A82;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_19=256'h47C34869490F49B44A584AFB4B9D4C3F4CE04D814E204EBF4F5D4FFB50975133;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_1A=256'h3D073DB83E683F173FC54073412141CE427A432543D0447A452445CD4675471C;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_1B=256'h31B5326E332633DF3496354D360436BA376F382438D9398C3A403AF23BA53C56;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_1C=256'h25E826A82767282628E529A32A612B1F2BDC2C992D552E112ECC2F87304130FB;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_1D=256'h19BE1A821B471C0B1CCF1D931E571F1A1FDD209F2161222322E523A624672528;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_1E=256'h0D540E1C0EE30FAB1072113A120112C8138F1455151C15E216A8176E183318F9;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_1F=256'h00C90192025B032403ED04B6057F0648071107D908A2096A0A330AFB0BC40C8C;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_20=256'hF43CF505F5CDF696F75EF827F8EFF9B8FA81FB4AFC13FCDCFDA5FE6EFF370000;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_21=256'hE7CDE892E958EA1EEAE4EBABEC71ED38EDFFEEC6EF8EF055F11DF1E4F2ACF374;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_22=256'hDB99DC5ADD1BDDDDDE9FDF61E023E0E6E1A9E26DE331E3F5E4B9E57EE642E707;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_23=256'hCFBFD079D134D1EFD2ABD367D424D4E1D59FD65DD71BD7DAD899D958DA18DAD8;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_24=256'hC45BC50EC5C0C674C727C7DCC891C946C9FCCAB3CB6ACC21CCDACD92CE4BCF05;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_25=256'hB98BBA33BADCBB86BC30BCDBBD86BE32BEDFBF8DC03BC0E9C198C248C2F9C3AA;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_26=256'hAF69B005B0A3B141B1E0B27FB320B3C1B463B505B5A8B64CB6F1B797B83DB8E4;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_27=256'hA60DA69CA72DA7BEA850A8E3A976AA0BAAA0AB37ABCEAC65ACFEAD98AE32AECD;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_28=256'h9D8F9E109E929F159F98A01DA0A3A129A1B1A239A2C2A34DA3D8A464A4F1A57E;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_29=256'h9603967596E7975A97CE984498BA993199AA9A239A9D9B189B949C129C909D0F;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_2A=256'h8F7D8FDE903F90A29105916A91D09237929F9308937293DD944994B695249593;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_2B=256'h8A0D8A5B8AAB8AFC8B4E8BA18BF68C4B8CA28CF98D528DAC8E078E638EC08F1E;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_2C=256'h85BF85FB8638867786B686F78739877C87C18806884D889588DE8928897389BF;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_2D=256'h829E82C782F2831D834A837883A783D78408843B846F84A484DA8512854A8584;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_2E=256'h80B380C980DF80F78111812B81478164818281A181C281E38206822B82508277;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_2F=256'h800280038007800B80108017801F80288033803F804C805A8069807A808C809F;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_30=256'h808C807A8069805A804C803F80338028801F80178010800B8007800380028001;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_31=256'h8250822B820681E381C281A1818281648147812B811180F780DF80C980B3809F;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_32=256'h854A851284DA84A4846F843B840883D783A78378834A831D82F282C7829E8277;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_33=256'h8973892888DE8895884D880687C1877C873986F786B68677863885FB85BF8584;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_34=256'h8EC08E638E078DAC8D528CF98CA28C4B8BF68BA18B4E8AFC8AAB8A5B8A0D89BF;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_35=256'h952494B6944993DD93729308929F923791D0916A910590A2903F8FDE8F7D8F1E;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_36=256'h9C909C129B949B189A9D9A2399AA993198BA984497CE975A96E7967596039593;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_37=256'hA4F1A464A3D8A34DA2C2A239A1B1A129A0A3A01D9F989F159E929E109D8F9D0F;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_38=256'hAE32AD98ACFEAC65ABCEAB37AAA0AA0BA976A8E3A850A7BEA72DA69CA60DA57E;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_39=256'hB83DB797B6F1B64CB5A8B505B463B3C1B320B27FB1E0B141B0A3B005AF69AECD;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_3A=256'hC2F9C248C198C0E9C03BBF8DBEDFBE32BD86BCDBBC30BB86BADCBA33B98BB8E4;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_3B=256'hCE4BCD92CCDACC21CB6ACAB3C9FCC946C891C7DCC727C674C5C0C50EC45BC3AA;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_3C=256'hDA18D958D899D7DAD71BD65DD59FD4E1D424D367D2ABD1EFD134D079CFBFCF05;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_3D=256'hE642E57EE4B9E3F5E331E26DE1A9E0E6E023DF61DE9FDDDDDD1BDC5ADB99DAD8;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_3E=256'hF2ACF1E4F11DF055EF8EEEC6EDFFED38EC71EBABEAE4EA1EE958E892E7CDE707;
defparam sine_rom_sine_rom_0_0_s0.INIT_RAM_3F=256'hFF37FE6EFDA5FCDCFC13FB4AFA81F9B8F8EFF827F75EF696F5CDF505F43CF374;
  pROM sine_rom_sine_rom_0_0_s1 (
    .DO({DO_1[31:16],\sine_q[2] [15:0]}),
    .CLK(clk_d),
    .CE(VCC),
    .OCE(GND),
    .RESET(GND),
    .AD({\phase[2] [31:22],GND,GND,VCC,VCC}) 
);
defparam sine_rom_sine_rom_0_0_s1.BIT_WIDTH=16;
defparam sine_rom_sine_rom_0_0_s1.READ_MODE=1'b0;
defparam sine_rom_sine_rom_0_0_s1.RESET_MODE="SYNC";
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_00=256'h0BC40AFB0A33096A08A207D907110648057F04B603ED0324025B019200C90000;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_01=256'h1833176E16A815E2151C1455138F12C81201113A10720FAB0EE30E1C0D540C8C;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_02=256'h246723A622E522232161209F1FDD1F1A1E571D931CCF1C0B1B471A8219BE18F9;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_03=256'h30412F872ECC2E112D552C992BDC2B1F2A6129A328E52826276726A825E82528;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_04=256'h3BA53AF23A40398C38D93824376F36BA3604354D349633DF3326326E31B530FB;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_05=256'h467545CD4524447A43D04325427A41CE412140733FC53F173E683DB83D073C56;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_06=256'h50974FFB4F5D4EBF4E204D814CE04C3F4B9D4AFB4A5849B4490F486947C3471C;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_07=256'h59F3596458D3584257B0571D568A55F5556054C95432539B5302526851CE5133;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_08=256'h627161F0616E60EB60685FE35F5D5ED75E4F5DC75D3E5CB35C285B9C5B0F5A82;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_09=256'h69FD698B691968A6683267BC674666CF665665DD656364E8646C63EE637062F1;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_0A=256'h708370226FC16F5E6EFB6E966E306DC96D616CF86C8E6C236BB76B4A6ADC6A6D;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_0B=256'h75F375A57555750474B2745F740A73B5735E730772AE725471F9719D714070E2;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_0C=256'h7A417A0579C87989794A790978C77884783F77FA77B3776B772276D8768D7641;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_0D=256'h7D627D397D0E7CE37CB67C887C597C297BF87BC57B917B5C7B267AEE7AB67A7C;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_0E=256'h7F4D7F377F217F097EEF7ED57EB97E9C7E7E7E5F7E3E7E1D7DFA7DD57DB07D89;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_0F=256'h7FFE7FFD7FF97FF57FF07FE97FE17FD87FCD7FC17FB47FA67F977F867F747F61;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_10=256'h7F747F867F977FA67FB47FC17FCD7FD87FE17FE97FF07FF57FF97FFD7FFE7FFF;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_11=256'h7DB07DD57DFA7E1D7E3E7E5F7E7E7E9C7EB97ED57EEF7F097F217F377F4D7F61;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_12=256'h7AB67AEE7B267B5C7B917BC57BF87C297C597C887CB67CE37D0E7D397D627D89;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_13=256'h768D76D87722776B77B377FA783F788478C77909794A798979C87A057A417A7C;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_14=256'h7140719D71F9725472AE7307735E73B5740A745F74B27504755575A575F37641;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_15=256'h6ADC6B4A6BB76C236C8E6CF86D616DC96E306E966EFB6F5E6FC17022708370E2;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_16=256'h637063EE646C64E8656365DD665666CF674667BC683268A66919698B69FD6A6D;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_17=256'h5B0F5B9C5C285CB35D3E5DC75E4F5ED75F5D5FE3606860EB616E61F0627162F1;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_18=256'h51CE52685302539B543254C9556055F5568A571D57B0584258D3596459F35A82;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_19=256'h47C34869490F49B44A584AFB4B9D4C3F4CE04D814E204EBF4F5D4FFB50975133;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_1A=256'h3D073DB83E683F173FC54073412141CE427A432543D0447A452445CD4675471C;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_1B=256'h31B5326E332633DF3496354D360436BA376F382438D9398C3A403AF23BA53C56;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_1C=256'h25E826A82767282628E529A32A612B1F2BDC2C992D552E112ECC2F87304130FB;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_1D=256'h19BE1A821B471C0B1CCF1D931E571F1A1FDD209F2161222322E523A624672528;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_1E=256'h0D540E1C0EE30FAB1072113A120112C8138F1455151C15E216A8176E183318F9;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_1F=256'h00C90192025B032403ED04B6057F0648071107D908A2096A0A330AFB0BC40C8C;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_20=256'hF43CF505F5CDF696F75EF827F8EFF9B8FA81FB4AFC13FCDCFDA5FE6EFF370000;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_21=256'hE7CDE892E958EA1EEAE4EBABEC71ED38EDFFEEC6EF8EF055F11DF1E4F2ACF374;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_22=256'hDB99DC5ADD1BDDDDDE9FDF61E023E0E6E1A9E26DE331E3F5E4B9E57EE642E707;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_23=256'hCFBFD079D134D1EFD2ABD367D424D4E1D59FD65DD71BD7DAD899D958DA18DAD8;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_24=256'hC45BC50EC5C0C674C727C7DCC891C946C9FCCAB3CB6ACC21CCDACD92CE4BCF05;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_25=256'hB98BBA33BADCBB86BC30BCDBBD86BE32BEDFBF8DC03BC0E9C198C248C2F9C3AA;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_26=256'hAF69B005B0A3B141B1E0B27FB320B3C1B463B505B5A8B64CB6F1B797B83DB8E4;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_27=256'hA60DA69CA72DA7BEA850A8E3A976AA0BAAA0AB37ABCEAC65ACFEAD98AE32AECD;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_28=256'h9D8F9E109E929F159F98A01DA0A3A129A1B1A239A2C2A34DA3D8A464A4F1A57E;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_29=256'h9603967596E7975A97CE984498BA993199AA9A239A9D9B189B949C129C909D0F;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_2A=256'h8F7D8FDE903F90A29105916A91D09237929F9308937293DD944994B695249593;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_2B=256'h8A0D8A5B8AAB8AFC8B4E8BA18BF68C4B8CA28CF98D528DAC8E078E638EC08F1E;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_2C=256'h85BF85FB8638867786B686F78739877C87C18806884D889588DE8928897389BF;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_2D=256'h829E82C782F2831D834A837883A783D78408843B846F84A484DA8512854A8584;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_2E=256'h80B380C980DF80F78111812B81478164818281A181C281E38206822B82508277;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_2F=256'h800280038007800B80108017801F80288033803F804C805A8069807A808C809F;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_30=256'h808C807A8069805A804C803F80338028801F80178010800B8007800380028001;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_31=256'h8250822B820681E381C281A1818281648147812B811180F780DF80C980B3809F;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_32=256'h854A851284DA84A4846F843B840883D783A78378834A831D82F282C7829E8277;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_33=256'h8973892888DE8895884D880687C1877C873986F786B68677863885FB85BF8584;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_34=256'h8EC08E638E078DAC8D528CF98CA28C4B8BF68BA18B4E8AFC8AAB8A5B8A0D89BF;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_35=256'h952494B6944993DD93729308929F923791D0916A910590A2903F8FDE8F7D8F1E;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_36=256'h9C909C129B949B189A9D9A2399AA993198BA984497CE975A96E7967596039593;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_37=256'hA4F1A464A3D8A34DA2C2A239A1B1A129A0A3A01D9F989F159E929E109D8F9D0F;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_38=256'hAE32AD98ACFEAC65ABCEAB37AAA0AA0BA976A8E3A850A7BEA72DA69CA60DA57E;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_39=256'hB83DB797B6F1B64CB5A8B505B463B3C1B320B27FB1E0B141B0A3B005AF69AECD;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_3A=256'hC2F9C248C198C0E9C03BBF8DBEDFBE32BD86BCDBBC30BB86BADCBA33B98BB8E4;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_3B=256'hCE4BCD92CCDACC21CB6ACAB3C9FCC946C891C7DCC727C674C5C0C50EC45BC3AA;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_3C=256'hDA18D958D899D7DAD71BD65DD59FD4E1D424D367D2ABD1EFD134D079CFBFCF05;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_3D=256'hE642E57EE4B9E3F5E331E26DE1A9E0E6E023DF61DE9FDDDDDD1BDC5ADB99DAD8;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_3E=256'hF2ACF1E4F11DF055EF8EEEC6EDFFED38EC71EBABEAE4EA1EE958E892E7CDE707;
defparam sine_rom_sine_rom_0_0_s1.INIT_RAM_3F=256'hFF37FE6EFDA5FCDCFC13FB4AFA81F9B8F8EFF827F75EF696F5CDF505F43CF374;
  pROM sine_rom_sine_rom_0_0_s2 (
    .DO({DO_2[31:16],\sine_q[3] [15:0]}),
    .CLK(clk_d),
    .CE(VCC),
    .OCE(GND),
    .RESET(GND),
    .AD({\phase[3] [31:22],GND,GND,VCC,VCC}) 
);
defparam sine_rom_sine_rom_0_0_s2.BIT_WIDTH=16;
defparam sine_rom_sine_rom_0_0_s2.READ_MODE=1'b0;
defparam sine_rom_sine_rom_0_0_s2.RESET_MODE="SYNC";
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_00=256'h0BC40AFB0A33096A08A207D907110648057F04B603ED0324025B019200C90000;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_01=256'h1833176E16A815E2151C1455138F12C81201113A10720FAB0EE30E1C0D540C8C;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_02=256'h246723A622E522232161209F1FDD1F1A1E571D931CCF1C0B1B471A8219BE18F9;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_03=256'h30412F872ECC2E112D552C992BDC2B1F2A6129A328E52826276726A825E82528;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_04=256'h3BA53AF23A40398C38D93824376F36BA3604354D349633DF3326326E31B530FB;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_05=256'h467545CD4524447A43D04325427A41CE412140733FC53F173E683DB83D073C56;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_06=256'h50974FFB4F5D4EBF4E204D814CE04C3F4B9D4AFB4A5849B4490F486947C3471C;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_07=256'h59F3596458D3584257B0571D568A55F5556054C95432539B5302526851CE5133;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_08=256'h627161F0616E60EB60685FE35F5D5ED75E4F5DC75D3E5CB35C285B9C5B0F5A82;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_09=256'h69FD698B691968A6683267BC674666CF665665DD656364E8646C63EE637062F1;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_0A=256'h708370226FC16F5E6EFB6E966E306DC96D616CF86C8E6C236BB76B4A6ADC6A6D;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_0B=256'h75F375A57555750474B2745F740A73B5735E730772AE725471F9719D714070E2;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_0C=256'h7A417A0579C87989794A790978C77884783F77FA77B3776B772276D8768D7641;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_0D=256'h7D627D397D0E7CE37CB67C887C597C297BF87BC57B917B5C7B267AEE7AB67A7C;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_0E=256'h7F4D7F377F217F097EEF7ED57EB97E9C7E7E7E5F7E3E7E1D7DFA7DD57DB07D89;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_0F=256'h7FFE7FFD7FF97FF57FF07FE97FE17FD87FCD7FC17FB47FA67F977F867F747F61;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_10=256'h7F747F867F977FA67FB47FC17FCD7FD87FE17FE97FF07FF57FF97FFD7FFE7FFF;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_11=256'h7DB07DD57DFA7E1D7E3E7E5F7E7E7E9C7EB97ED57EEF7F097F217F377F4D7F61;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_12=256'h7AB67AEE7B267B5C7B917BC57BF87C297C597C887CB67CE37D0E7D397D627D89;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_13=256'h768D76D87722776B77B377FA783F788478C77909794A798979C87A057A417A7C;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_14=256'h7140719D71F9725472AE7307735E73B5740A745F74B27504755575A575F37641;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_15=256'h6ADC6B4A6BB76C236C8E6CF86D616DC96E306E966EFB6F5E6FC17022708370E2;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_16=256'h637063EE646C64E8656365DD665666CF674667BC683268A66919698B69FD6A6D;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_17=256'h5B0F5B9C5C285CB35D3E5DC75E4F5ED75F5D5FE3606860EB616E61F0627162F1;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_18=256'h51CE52685302539B543254C9556055F5568A571D57B0584258D3596459F35A82;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_19=256'h47C34869490F49B44A584AFB4B9D4C3F4CE04D814E204EBF4F5D4FFB50975133;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_1A=256'h3D073DB83E683F173FC54073412141CE427A432543D0447A452445CD4675471C;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_1B=256'h31B5326E332633DF3496354D360436BA376F382438D9398C3A403AF23BA53C56;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_1C=256'h25E826A82767282628E529A32A612B1F2BDC2C992D552E112ECC2F87304130FB;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_1D=256'h19BE1A821B471C0B1CCF1D931E571F1A1FDD209F2161222322E523A624672528;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_1E=256'h0D540E1C0EE30FAB1072113A120112C8138F1455151C15E216A8176E183318F9;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_1F=256'h00C90192025B032403ED04B6057F0648071107D908A2096A0A330AFB0BC40C8C;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_20=256'hF43CF505F5CDF696F75EF827F8EFF9B8FA81FB4AFC13FCDCFDA5FE6EFF370000;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_21=256'hE7CDE892E958EA1EEAE4EBABEC71ED38EDFFEEC6EF8EF055F11DF1E4F2ACF374;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_22=256'hDB99DC5ADD1BDDDDDE9FDF61E023E0E6E1A9E26DE331E3F5E4B9E57EE642E707;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_23=256'hCFBFD079D134D1EFD2ABD367D424D4E1D59FD65DD71BD7DAD899D958DA18DAD8;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_24=256'hC45BC50EC5C0C674C727C7DCC891C946C9FCCAB3CB6ACC21CCDACD92CE4BCF05;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_25=256'hB98BBA33BADCBB86BC30BCDBBD86BE32BEDFBF8DC03BC0E9C198C248C2F9C3AA;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_26=256'hAF69B005B0A3B141B1E0B27FB320B3C1B463B505B5A8B64CB6F1B797B83DB8E4;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_27=256'hA60DA69CA72DA7BEA850A8E3A976AA0BAAA0AB37ABCEAC65ACFEAD98AE32AECD;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_28=256'h9D8F9E109E929F159F98A01DA0A3A129A1B1A239A2C2A34DA3D8A464A4F1A57E;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_29=256'h9603967596E7975A97CE984498BA993199AA9A239A9D9B189B949C129C909D0F;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_2A=256'h8F7D8FDE903F90A29105916A91D09237929F9308937293DD944994B695249593;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_2B=256'h8A0D8A5B8AAB8AFC8B4E8BA18BF68C4B8CA28CF98D528DAC8E078E638EC08F1E;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_2C=256'h85BF85FB8638867786B686F78739877C87C18806884D889588DE8928897389BF;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_2D=256'h829E82C782F2831D834A837883A783D78408843B846F84A484DA8512854A8584;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_2E=256'h80B380C980DF80F78111812B81478164818281A181C281E38206822B82508277;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_2F=256'h800280038007800B80108017801F80288033803F804C805A8069807A808C809F;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_30=256'h808C807A8069805A804C803F80338028801F80178010800B8007800380028001;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_31=256'h8250822B820681E381C281A1818281648147812B811180F780DF80C980B3809F;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_32=256'h854A851284DA84A4846F843B840883D783A78378834A831D82F282C7829E8277;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_33=256'h8973892888DE8895884D880687C1877C873986F786B68677863885FB85BF8584;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_34=256'h8EC08E638E078DAC8D528CF98CA28C4B8BF68BA18B4E8AFC8AAB8A5B8A0D89BF;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_35=256'h952494B6944993DD93729308929F923791D0916A910590A2903F8FDE8F7D8F1E;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_36=256'h9C909C129B949B189A9D9A2399AA993198BA984497CE975A96E7967596039593;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_37=256'hA4F1A464A3D8A34DA2C2A239A1B1A129A0A3A01D9F989F159E929E109D8F9D0F;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_38=256'hAE32AD98ACFEAC65ABCEAB37AAA0AA0BA976A8E3A850A7BEA72DA69CA60DA57E;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_39=256'hB83DB797B6F1B64CB5A8B505B463B3C1B320B27FB1E0B141B0A3B005AF69AECD;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_3A=256'hC2F9C248C198C0E9C03BBF8DBEDFBE32BD86BCDBBC30BB86BADCBA33B98BB8E4;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_3B=256'hCE4BCD92CCDACC21CB6ACAB3C9FCC946C891C7DCC727C674C5C0C50EC45BC3AA;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_3C=256'hDA18D958D899D7DAD71BD65DD59FD4E1D424D367D2ABD1EFD134D079CFBFCF05;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_3D=256'hE642E57EE4B9E3F5E331E26DE1A9E0E6E023DF61DE9FDDDDDD1BDC5ADB99DAD8;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_3E=256'hF2ACF1E4F11DF055EF8EEEC6EDFFED38EC71EBABEAE4EA1EE958E892E7CDE707;
defparam sine_rom_sine_rom_0_0_s2.INIT_RAM_3F=256'hFF37FE6EFDA5FCDCFC13FB4AFA81F9B8F8EFF827F75EF696F5CDF505F43CF374;
  MULTALU27X18 n1104_s (
    .DOUT({DOUT[47:24],n1081_2,n1082_1,n1083_1,n1084_1,n1085_1,n1086_1,n1087_1,n1088_1,n1089_1,n1090_1,n1091_1,n1092_1,n1093_1,n1094_1,n1095_1,n1096_1,n1097_1,n1098_1,n1099_1,n1100_1,n1101_1,n1102_1,n1103_1,n1104_2}),
    .CASO(CASO[47:0]),
    .SOA(SOA[26:0]),
    .A({\sine_q[0]_15_15 ,\sine_q[0]_15_15 ,\sine_q[0]_15_15 ,\sine_q[0]_15_15 ,\sine_q[0]_15_15 ,\sine_q[0]_15_15 ,\sine_q[0]_15_15 ,\sine_q[0]_15_15 ,\sine_q[0]_15_15 ,\sine_q[0]_15_15 ,\sine_q[0]_15_15 ,\sine_q[0]_15_15 ,\sine_q[0]_14_15 ,\sine_q[0]_13_15 ,\sine_q[0]_12_15 ,\sine_q[0]_11_15 ,\sine_q[0]_10_15 ,\sine_q[0]_9_15 ,\sine_q[0]_8_15 ,\sine_q[0]_7_15 ,\sine_q[0]_6_15 ,\sine_q[0]_5_15 ,\sine_q[0]_4_15 ,\sine_q[0]_3_15 ,\sine_q[0]_2_15 ,\sine_q[0]_1_15 ,\sine_q[0]_0_15 }),
    .SIA({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .B({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,gains_d[6:0]}),
    .C({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .D({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .CASI({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .ACCSEL(GND),
    .PSEL(GND),
    .ASEL(GND),
    .PADDSUB(GND),
    .CSEL(GND),
    .CASISEL(GND),
    .ADDSUB({GND,GND}),
    .CLK({GND,GND}),
    .CE({VCC,VCC}),
    .RESET({GND,GND}) 
);
defparam n1104_s.MULT_RESET_MODE="SYNC";
defparam n1104_s.ACCSEL_IREG_CLK="BYPASS";
defparam n1104_s.ACCSEL_IREG_CE="CE0";
defparam n1104_s.ACCSEL_IREG_RESET="RESET0";
defparam n1104_s.ADDSUB0_IREG_CLK="BYPASS";
defparam n1104_s.ADDSUB0_IREG_CE="CE0";
defparam n1104_s.ADDSUB0_IREG_RESET="RESET0";
defparam n1104_s.ADDSUB1_IREG_CLK="BYPASS";
defparam n1104_s.ADDSUB1_IREG_CE="CE0";
defparam n1104_s.ADDSUB1_IREG_RESET="RESET0";
defparam n1104_s.FB_PREG_EN="FALSE";
defparam n1104_s.ACCSEL_PREG_CLK="BYPASS";
defparam n1104_s.ACCSEL_PREG_CE="CE0";
defparam n1104_s.ACCSEL_PREG_RESET="RESET0";
defparam n1104_s.ADDSUB0_PREG_CLK="BYPASS";
defparam n1104_s.ADDSUB0_PREG_CE="CE0";
defparam n1104_s.ADDSUB0_PREG_RESET="RESET0";
defparam n1104_s.ADDSUB1_PREG_CLK="BYPASS";
defparam n1104_s.ADDSUB1_PREG_CE="CE0";
defparam n1104_s.ADDSUB1_PREG_RESET="RESET0";
defparam n1104_s.OREG_CLK="BYPASS";
defparam n1104_s.OREG_CE="CE0";
defparam n1104_s.OREG_RESET="RESET0";
defparam n1104_s.PRE_LOAD=48'h000000000000;
defparam n1104_s.CASI_SEL=1'b0;
defparam n1104_s.AREG_CLK="BYPASS";
defparam n1104_s.AREG_CE="CE0";
defparam n1104_s.AREG_RESET="RESET0";
defparam n1104_s.BREG_CLK="BYPASS";
defparam n1104_s.BREG_CE="CE0";
defparam n1104_s.BREG_RESET="RESET0";
defparam n1104_s.DREG_CLK="BYPASS";
defparam n1104_s.DREG_CE="CE0";
defparam n1104_s.DREG_RESET="RESET0";
defparam n1104_s.PREG_CLK="BYPASS";
defparam n1104_s.PREG_CE="CE0";
defparam n1104_s.PREG_RESET="RESET0";
defparam n1104_s.SOA_PREG_EN="FALSE";
defparam n1104_s.DYN_P_SEL="FALSE";
defparam n1104_s.P_SEL=1'b0;
defparam n1104_s.DYN_P_ADDSUB="FALSE";
defparam n1104_s.P_ADDSUB=1'b0;
defparam n1104_s.ACC_SEL=1'b0;
defparam n1104_s.ADD_SUB_0=1'b0;
defparam n1104_s.ADD_SUB_1=1'b0;
defparam n1104_s.A_SEL=1'b0;
defparam n1104_s.CASISEL_IREG_CE="CE0";
defparam n1104_s.CASISEL_IREG_CLK="BYPASS";
defparam n1104_s.CASISEL_IREG_RESET="RESET0";
defparam n1104_s.CASISEL_PREG_CE="CE0";
defparam n1104_s.CASISEL_PREG_CLK="BYPASS";
defparam n1104_s.CASISEL_PREG_RESET="RESET0";
defparam n1104_s.CSEL_IREG_CE="CE0";
defparam n1104_s.CSEL_IREG_CLK="BYPASS";
defparam n1104_s.CSEL_IREG_RESET="RESET0";
defparam n1104_s.CSEL_PREG_CE="CE0";
defparam n1104_s.CSEL_PREG_CLK="BYPASS";
defparam n1104_s.CSEL_PREG_RESET="RESET0";
defparam n1104_s.C_IREG_CE="CE0";
defparam n1104_s.C_IREG_CLK="BYPASS";
defparam n1104_s.C_IREG_RESET="RESET0";
defparam n1104_s.C_PREG_CE="CE0";
defparam n1104_s.C_PREG_CLK="BYPASS";
defparam n1104_s.C_PREG_RESET="RESET0";
defparam n1104_s.C_SEL=1'b0;
defparam n1104_s.DYN_ACC_SEL="FALSE";
defparam n1104_s.DYN_ADD_SUB_0="FALSE";
defparam n1104_s.DYN_ADD_SUB_1="FALSE";
defparam n1104_s.DYN_A_SEL="FALSE";
defparam n1104_s.DYN_CASI_SEL="FALSE";
defparam n1104_s.DYN_C_SEL="FALSE";
defparam n1104_s.MULT12X12_EN="FALSE";
defparam n1104_s.PADDSUB_IREG_CE="CE0";
defparam n1104_s.PADDSUB_IREG_CLK="BYPASS";
defparam n1104_s.PADDSUB_IREG_RESET="RESET0";
defparam n1104_s.PSEL_IREG_CE="CE0";
defparam n1104_s.PSEL_IREG_CLK="BYPASS";
defparam n1104_s.PSEL_IREG_RESET="RESET0";
  MULTALU27X18 n1128_s (
    .DOUT({DOUT_0[47:24],n1105_2,n1106_1,n1107_1,n1108_1,n1109_1,n1110_1,n1111_1,n1112_1,n1113_1,n1114_1,n1115_1,n1116_1,n1117_1,n1118_1,n1119_1,n1120_1,n1121_1,n1122_1,n1123_1,n1124_1,n1125_1,n1126_1,n1127_1,n1128_2}),
    .CASO(CASO_0[47:0]),
    .SOA(SOA_0[26:0]),
    .A({\sine_q[1]_15_15 ,\sine_q[1]_15_15 ,\sine_q[1]_15_15 ,\sine_q[1]_15_15 ,\sine_q[1]_15_15 ,\sine_q[1]_15_15 ,\sine_q[1]_15_15 ,\sine_q[1]_15_15 ,\sine_q[1]_15_15 ,\sine_q[1]_15_15 ,\sine_q[1]_15_15 ,\sine_q[1]_15_15 ,\sine_q[1]_14_15 ,\sine_q[1]_13_15 ,\sine_q[1]_12_15 ,\sine_q[1]_11_15 ,\sine_q[1]_10_15 ,\sine_q[1]_9_15 ,\sine_q[1]_8_15 ,\sine_q[1]_7_15 ,\sine_q[1]_6_15 ,\sine_q[1]_5_15 ,\sine_q[1]_4_15 ,\sine_q[1]_3_15 ,\sine_q[1]_2_15 ,\sine_q[1]_1_15 ,\sine_q[1]_0_15 }),
    .SIA({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .B({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,gains_d[13:7]}),
    .C({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .D({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .CASI({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .ACCSEL(GND),
    .PSEL(GND),
    .ASEL(GND),
    .PADDSUB(GND),
    .CSEL(GND),
    .CASISEL(GND),
    .ADDSUB({GND,GND}),
    .CLK({GND,GND}),
    .CE({VCC,VCC}),
    .RESET({GND,GND}) 
);
defparam n1128_s.MULT_RESET_MODE="SYNC";
defparam n1128_s.ACCSEL_IREG_CLK="BYPASS";
defparam n1128_s.ACCSEL_IREG_CE="CE0";
defparam n1128_s.ACCSEL_IREG_RESET="RESET0";
defparam n1128_s.ADDSUB0_IREG_CLK="BYPASS";
defparam n1128_s.ADDSUB0_IREG_CE="CE0";
defparam n1128_s.ADDSUB0_IREG_RESET="RESET0";
defparam n1128_s.ADDSUB1_IREG_CLK="BYPASS";
defparam n1128_s.ADDSUB1_IREG_CE="CE0";
defparam n1128_s.ADDSUB1_IREG_RESET="RESET0";
defparam n1128_s.FB_PREG_EN="FALSE";
defparam n1128_s.ACCSEL_PREG_CLK="BYPASS";
defparam n1128_s.ACCSEL_PREG_CE="CE0";
defparam n1128_s.ACCSEL_PREG_RESET="RESET0";
defparam n1128_s.ADDSUB0_PREG_CLK="BYPASS";
defparam n1128_s.ADDSUB0_PREG_CE="CE0";
defparam n1128_s.ADDSUB0_PREG_RESET="RESET0";
defparam n1128_s.ADDSUB1_PREG_CLK="BYPASS";
defparam n1128_s.ADDSUB1_PREG_CE="CE0";
defparam n1128_s.ADDSUB1_PREG_RESET="RESET0";
defparam n1128_s.OREG_CLK="BYPASS";
defparam n1128_s.OREG_CE="CE0";
defparam n1128_s.OREG_RESET="RESET0";
defparam n1128_s.PRE_LOAD=48'h000000000000;
defparam n1128_s.CASI_SEL=1'b0;
defparam n1128_s.AREG_CLK="BYPASS";
defparam n1128_s.AREG_CE="CE0";
defparam n1128_s.AREG_RESET="RESET0";
defparam n1128_s.BREG_CLK="BYPASS";
defparam n1128_s.BREG_CE="CE0";
defparam n1128_s.BREG_RESET="RESET0";
defparam n1128_s.DREG_CLK="BYPASS";
defparam n1128_s.DREG_CE="CE0";
defparam n1128_s.DREG_RESET="RESET0";
defparam n1128_s.PREG_CLK="BYPASS";
defparam n1128_s.PREG_CE="CE0";
defparam n1128_s.PREG_RESET="RESET0";
defparam n1128_s.SOA_PREG_EN="FALSE";
defparam n1128_s.DYN_P_SEL="FALSE";
defparam n1128_s.P_SEL=1'b0;
defparam n1128_s.DYN_P_ADDSUB="FALSE";
defparam n1128_s.P_ADDSUB=1'b0;
defparam n1128_s.ACC_SEL=1'b0;
defparam n1128_s.ADD_SUB_0=1'b0;
defparam n1128_s.ADD_SUB_1=1'b0;
defparam n1128_s.A_SEL=1'b0;
defparam n1128_s.CASISEL_IREG_CE="CE0";
defparam n1128_s.CASISEL_IREG_CLK="BYPASS";
defparam n1128_s.CASISEL_IREG_RESET="RESET0";
defparam n1128_s.CASISEL_PREG_CE="CE0";
defparam n1128_s.CASISEL_PREG_CLK="BYPASS";
defparam n1128_s.CASISEL_PREG_RESET="RESET0";
defparam n1128_s.CSEL_IREG_CE="CE0";
defparam n1128_s.CSEL_IREG_CLK="BYPASS";
defparam n1128_s.CSEL_IREG_RESET="RESET0";
defparam n1128_s.CSEL_PREG_CE="CE0";
defparam n1128_s.CSEL_PREG_CLK="BYPASS";
defparam n1128_s.CSEL_PREG_RESET="RESET0";
defparam n1128_s.C_IREG_CE="CE0";
defparam n1128_s.C_IREG_CLK="BYPASS";
defparam n1128_s.C_IREG_RESET="RESET0";
defparam n1128_s.C_PREG_CE="CE0";
defparam n1128_s.C_PREG_CLK="BYPASS";
defparam n1128_s.C_PREG_RESET="RESET0";
defparam n1128_s.C_SEL=1'b0;
defparam n1128_s.DYN_ACC_SEL="FALSE";
defparam n1128_s.DYN_ADD_SUB_0="FALSE";
defparam n1128_s.DYN_ADD_SUB_1="FALSE";
defparam n1128_s.DYN_A_SEL="FALSE";
defparam n1128_s.DYN_CASI_SEL="FALSE";
defparam n1128_s.DYN_C_SEL="FALSE";
defparam n1128_s.MULT12X12_EN="FALSE";
defparam n1128_s.PADDSUB_IREG_CE="CE0";
defparam n1128_s.PADDSUB_IREG_CLK="BYPASS";
defparam n1128_s.PADDSUB_IREG_RESET="RESET0";
defparam n1128_s.PSEL_IREG_CE="CE0";
defparam n1128_s.PSEL_IREG_CLK="BYPASS";
defparam n1128_s.PSEL_IREG_RESET="RESET0";
  MULTALU27X18 n1152_s (
    .DOUT({DOUT_1[47:24],n1129_2,n1130_1,n1131_1,n1132_1,n1133_1,n1134_1,n1135_1,n1136_1,n1137_1,n1138_1,n1139_1,n1140_1,n1141_1,n1142_1,n1143_1,n1144_1,n1145_1,n1146_1,n1147_1,n1148_1,n1149_1,n1150_1,n1151_1,n1152_2}),
    .CASO(CASO_1[47:0]),
    .SOA(SOA_1[26:0]),
    .A({\sine_q[2]_15_15 ,\sine_q[2]_15_15 ,\sine_q[2]_15_15 ,\sine_q[2]_15_15 ,\sine_q[2]_15_15 ,\sine_q[2]_15_15 ,\sine_q[2]_15_15 ,\sine_q[2]_15_15 ,\sine_q[2]_15_15 ,\sine_q[2]_15_15 ,\sine_q[2]_15_15 ,\sine_q[2]_15_15 ,\sine_q[2]_14_15 ,\sine_q[2]_13_15 ,\sine_q[2]_12_15 ,\sine_q[2]_11_15 ,\sine_q[2]_10_15 ,\sine_q[2]_9_15 ,\sine_q[2]_8_15 ,\sine_q[2]_7_15 ,\sine_q[2]_6_15 ,\sine_q[2]_5_15 ,\sine_q[2]_4_15 ,\sine_q[2]_3_15 ,\sine_q[2]_2_15 ,\sine_q[2]_1_15 ,\sine_q[2]_0_15 }),
    .SIA({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .B({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,gains_d[20:14]}),
    .C({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .D({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .CASI({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .ACCSEL(GND),
    .PSEL(GND),
    .ASEL(GND),
    .PADDSUB(GND),
    .CSEL(GND),
    .CASISEL(GND),
    .ADDSUB({GND,GND}),
    .CLK({GND,GND}),
    .CE({VCC,VCC}),
    .RESET({GND,GND}) 
);
defparam n1152_s.MULT_RESET_MODE="SYNC";
defparam n1152_s.ACCSEL_IREG_CLK="BYPASS";
defparam n1152_s.ACCSEL_IREG_CE="CE0";
defparam n1152_s.ACCSEL_IREG_RESET="RESET0";
defparam n1152_s.ADDSUB0_IREG_CLK="BYPASS";
defparam n1152_s.ADDSUB0_IREG_CE="CE0";
defparam n1152_s.ADDSUB0_IREG_RESET="RESET0";
defparam n1152_s.ADDSUB1_IREG_CLK="BYPASS";
defparam n1152_s.ADDSUB1_IREG_CE="CE0";
defparam n1152_s.ADDSUB1_IREG_RESET="RESET0";
defparam n1152_s.FB_PREG_EN="FALSE";
defparam n1152_s.ACCSEL_PREG_CLK="BYPASS";
defparam n1152_s.ACCSEL_PREG_CE="CE0";
defparam n1152_s.ACCSEL_PREG_RESET="RESET0";
defparam n1152_s.ADDSUB0_PREG_CLK="BYPASS";
defparam n1152_s.ADDSUB0_PREG_CE="CE0";
defparam n1152_s.ADDSUB0_PREG_RESET="RESET0";
defparam n1152_s.ADDSUB1_PREG_CLK="BYPASS";
defparam n1152_s.ADDSUB1_PREG_CE="CE0";
defparam n1152_s.ADDSUB1_PREG_RESET="RESET0";
defparam n1152_s.OREG_CLK="BYPASS";
defparam n1152_s.OREG_CE="CE0";
defparam n1152_s.OREG_RESET="RESET0";
defparam n1152_s.PRE_LOAD=48'h000000000000;
defparam n1152_s.CASI_SEL=1'b0;
defparam n1152_s.AREG_CLK="BYPASS";
defparam n1152_s.AREG_CE="CE0";
defparam n1152_s.AREG_RESET="RESET0";
defparam n1152_s.BREG_CLK="BYPASS";
defparam n1152_s.BREG_CE="CE0";
defparam n1152_s.BREG_RESET="RESET0";
defparam n1152_s.DREG_CLK="BYPASS";
defparam n1152_s.DREG_CE="CE0";
defparam n1152_s.DREG_RESET="RESET0";
defparam n1152_s.PREG_CLK="BYPASS";
defparam n1152_s.PREG_CE="CE0";
defparam n1152_s.PREG_RESET="RESET0";
defparam n1152_s.SOA_PREG_EN="FALSE";
defparam n1152_s.DYN_P_SEL="FALSE";
defparam n1152_s.P_SEL=1'b0;
defparam n1152_s.DYN_P_ADDSUB="FALSE";
defparam n1152_s.P_ADDSUB=1'b0;
defparam n1152_s.ACC_SEL=1'b0;
defparam n1152_s.ADD_SUB_0=1'b0;
defparam n1152_s.ADD_SUB_1=1'b0;
defparam n1152_s.A_SEL=1'b0;
defparam n1152_s.CASISEL_IREG_CE="CE0";
defparam n1152_s.CASISEL_IREG_CLK="BYPASS";
defparam n1152_s.CASISEL_IREG_RESET="RESET0";
defparam n1152_s.CASISEL_PREG_CE="CE0";
defparam n1152_s.CASISEL_PREG_CLK="BYPASS";
defparam n1152_s.CASISEL_PREG_RESET="RESET0";
defparam n1152_s.CSEL_IREG_CE="CE0";
defparam n1152_s.CSEL_IREG_CLK="BYPASS";
defparam n1152_s.CSEL_IREG_RESET="RESET0";
defparam n1152_s.CSEL_PREG_CE="CE0";
defparam n1152_s.CSEL_PREG_CLK="BYPASS";
defparam n1152_s.CSEL_PREG_RESET="RESET0";
defparam n1152_s.C_IREG_CE="CE0";
defparam n1152_s.C_IREG_CLK="BYPASS";
defparam n1152_s.C_IREG_RESET="RESET0";
defparam n1152_s.C_PREG_CE="CE0";
defparam n1152_s.C_PREG_CLK="BYPASS";
defparam n1152_s.C_PREG_RESET="RESET0";
defparam n1152_s.C_SEL=1'b0;
defparam n1152_s.DYN_ACC_SEL="FALSE";
defparam n1152_s.DYN_ADD_SUB_0="FALSE";
defparam n1152_s.DYN_ADD_SUB_1="FALSE";
defparam n1152_s.DYN_A_SEL="FALSE";
defparam n1152_s.DYN_CASI_SEL="FALSE";
defparam n1152_s.DYN_C_SEL="FALSE";
defparam n1152_s.MULT12X12_EN="FALSE";
defparam n1152_s.PADDSUB_IREG_CE="CE0";
defparam n1152_s.PADDSUB_IREG_CLK="BYPASS";
defparam n1152_s.PADDSUB_IREG_RESET="RESET0";
defparam n1152_s.PSEL_IREG_CE="CE0";
defparam n1152_s.PSEL_IREG_CLK="BYPASS";
defparam n1152_s.PSEL_IREG_RESET="RESET0";
  MULTALU27X18 n1176_s (
    .DOUT({DOUT_2[47:24],n1153_2,n1154_1,n1155_1,n1156_1,n1157_1,n1158_1,n1159_1,n1160_1,n1161_1,n1162_1,n1163_1,n1164_1,n1165_1,n1166_1,n1167_1,n1168_1,n1169_1,n1170_1,n1171_1,n1172_1,n1173_1,n1174_1,n1175_1,n1176_2}),
    .CASO(CASO_2[47:0]),
    .SOA(SOA_2[26:0]),
    .A({\sine_q[3]_15_15 ,\sine_q[3]_15_15 ,\sine_q[3]_15_15 ,\sine_q[3]_15_15 ,\sine_q[3]_15_15 ,\sine_q[3]_15_15 ,\sine_q[3]_15_15 ,\sine_q[3]_15_15 ,\sine_q[3]_15_15 ,\sine_q[3]_15_15 ,\sine_q[3]_15_15 ,\sine_q[3]_15_15 ,\sine_q[3]_14_15 ,\sine_q[3]_13_15 ,\sine_q[3]_12_15 ,\sine_q[3]_11_15 ,\sine_q[3]_10_15 ,\sine_q[3]_9_15 ,\sine_q[3]_8_15 ,\sine_q[3]_7_15 ,\sine_q[3]_6_15 ,\sine_q[3]_5_15 ,\sine_q[3]_4_15 ,\sine_q[3]_3_15 ,\sine_q[3]_2_15 ,\sine_q[3]_1_15 ,\sine_q[3]_0_17 }),
    .SIA({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .B({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,gains_d[27:21]}),
    .C({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .D({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .CASI({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .ACCSEL(GND),
    .PSEL(GND),
    .ASEL(GND),
    .PADDSUB(GND),
    .CSEL(GND),
    .CASISEL(GND),
    .ADDSUB({GND,GND}),
    .CLK({GND,GND}),
    .CE({VCC,VCC}),
    .RESET({GND,GND}) 
);
defparam n1176_s.MULT_RESET_MODE="SYNC";
defparam n1176_s.ACCSEL_IREG_CLK="BYPASS";
defparam n1176_s.ACCSEL_IREG_CE="CE0";
defparam n1176_s.ACCSEL_IREG_RESET="RESET0";
defparam n1176_s.ADDSUB0_IREG_CLK="BYPASS";
defparam n1176_s.ADDSUB0_IREG_CE="CE0";
defparam n1176_s.ADDSUB0_IREG_RESET="RESET0";
defparam n1176_s.ADDSUB1_IREG_CLK="BYPASS";
defparam n1176_s.ADDSUB1_IREG_CE="CE0";
defparam n1176_s.ADDSUB1_IREG_RESET="RESET0";
defparam n1176_s.FB_PREG_EN="FALSE";
defparam n1176_s.ACCSEL_PREG_CLK="BYPASS";
defparam n1176_s.ACCSEL_PREG_CE="CE0";
defparam n1176_s.ACCSEL_PREG_RESET="RESET0";
defparam n1176_s.ADDSUB0_PREG_CLK="BYPASS";
defparam n1176_s.ADDSUB0_PREG_CE="CE0";
defparam n1176_s.ADDSUB0_PREG_RESET="RESET0";
defparam n1176_s.ADDSUB1_PREG_CLK="BYPASS";
defparam n1176_s.ADDSUB1_PREG_CE="CE0";
defparam n1176_s.ADDSUB1_PREG_RESET="RESET0";
defparam n1176_s.OREG_CLK="BYPASS";
defparam n1176_s.OREG_CE="CE0";
defparam n1176_s.OREG_RESET="RESET0";
defparam n1176_s.PRE_LOAD=48'h000000000000;
defparam n1176_s.CASI_SEL=1'b0;
defparam n1176_s.AREG_CLK="BYPASS";
defparam n1176_s.AREG_CE="CE0";
defparam n1176_s.AREG_RESET="RESET0";
defparam n1176_s.BREG_CLK="BYPASS";
defparam n1176_s.BREG_CE="CE0";
defparam n1176_s.BREG_RESET="RESET0";
defparam n1176_s.DREG_CLK="BYPASS";
defparam n1176_s.DREG_CE="CE0";
defparam n1176_s.DREG_RESET="RESET0";
defparam n1176_s.PREG_CLK="BYPASS";
defparam n1176_s.PREG_CE="CE0";
defparam n1176_s.PREG_RESET="RESET0";
defparam n1176_s.SOA_PREG_EN="FALSE";
defparam n1176_s.DYN_P_SEL="FALSE";
defparam n1176_s.P_SEL=1'b0;
defparam n1176_s.DYN_P_ADDSUB="FALSE";
defparam n1176_s.P_ADDSUB=1'b0;
defparam n1176_s.ACC_SEL=1'b0;
defparam n1176_s.ADD_SUB_0=1'b0;
defparam n1176_s.ADD_SUB_1=1'b0;
defparam n1176_s.A_SEL=1'b0;
defparam n1176_s.CASISEL_IREG_CE="CE0";
defparam n1176_s.CASISEL_IREG_CLK="BYPASS";
defparam n1176_s.CASISEL_IREG_RESET="RESET0";
defparam n1176_s.CASISEL_PREG_CE="CE0";
defparam n1176_s.CASISEL_PREG_CLK="BYPASS";
defparam n1176_s.CASISEL_PREG_RESET="RESET0";
defparam n1176_s.CSEL_IREG_CE="CE0";
defparam n1176_s.CSEL_IREG_CLK="BYPASS";
defparam n1176_s.CSEL_IREG_RESET="RESET0";
defparam n1176_s.CSEL_PREG_CE="CE0";
defparam n1176_s.CSEL_PREG_CLK="BYPASS";
defparam n1176_s.CSEL_PREG_RESET="RESET0";
defparam n1176_s.C_IREG_CE="CE0";
defparam n1176_s.C_IREG_CLK="BYPASS";
defparam n1176_s.C_IREG_RESET="RESET0";
defparam n1176_s.C_PREG_CE="CE0";
defparam n1176_s.C_PREG_CLK="BYPASS";
defparam n1176_s.C_PREG_RESET="RESET0";
defparam n1176_s.C_SEL=1'b0;
defparam n1176_s.DYN_ACC_SEL="FALSE";
defparam n1176_s.DYN_ADD_SUB_0="FALSE";
defparam n1176_s.DYN_ADD_SUB_1="FALSE";
defparam n1176_s.DYN_A_SEL="FALSE";
defparam n1176_s.DYN_CASI_SEL="FALSE";
defparam n1176_s.DYN_C_SEL="FALSE";
defparam n1176_s.MULT12X12_EN="FALSE";
defparam n1176_s.PADDSUB_IREG_CE="CE0";
defparam n1176_s.PADDSUB_IREG_CLK="BYPASS";
defparam n1176_s.PADDSUB_IREG_RESET="RESET0";
defparam n1176_s.PSEL_IREG_CE="CE0";
defparam n1176_s.PSEL_IREG_CLK="BYPASS";
defparam n1176_s.PSEL_IREG_RESET="RESET0";
  MULTALU27X18 n1311_s (
    .DOUT({DOUT_3[47:32],\left_q[0] [31:14],DOUT_3[13:0]}),
    .CASO(CASO_3[47:0]),
    .SOA(n13110[26:0]),
    .A({n1081_2,n1081_2,n1081_2,n1081_2,n1082_1,n1083_1,n1084_1,n1085_1,n1086_1,n1087_1,n1088_1,n1089_1,n1090_1,n1091_1,n1092_1,n1093_1,n1094_1,n1095_1,n1096_1,n1097_1,n1098_1,n1099_1,n1100_1,n1101_1,n1102_1,n1103_1,n1104_2}),
    .SIA({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .B({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,n1273_6,n1274_6,n1275_6,n1276_6,n1277_6,n1278_6,n1279_6}),
    .C({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .D({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .CASI({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .ACCSEL(GND),
    .PSEL(GND),
    .ASEL(GND),
    .PADDSUB(GND),
    .CSEL(GND),
    .CASISEL(GND),
    .ADDSUB({GND,GND}),
    .CLK({GND,clk_d}),
    .CE(valid_pipe[1:0]),
    .RESET({GND,n232_6}) 
);
defparam n1311_s.MULT_RESET_MODE="ASYNC";
defparam n1311_s.ACCSEL_IREG_CLK="BYPASS";
defparam n1311_s.ACCSEL_IREG_CE="CE0";
defparam n1311_s.ACCSEL_IREG_RESET="RESET0";
defparam n1311_s.ADDSUB0_IREG_CLK="BYPASS";
defparam n1311_s.ADDSUB0_IREG_CE="CE0";
defparam n1311_s.ADDSUB0_IREG_RESET="RESET0";
defparam n1311_s.ADDSUB1_IREG_CLK="BYPASS";
defparam n1311_s.ADDSUB1_IREG_CE="CE0";
defparam n1311_s.ADDSUB1_IREG_RESET="RESET0";
defparam n1311_s.FB_PREG_EN="FALSE";
defparam n1311_s.ACCSEL_PREG_CLK="BYPASS";
defparam n1311_s.ACCSEL_PREG_CE="CE0";
defparam n1311_s.ACCSEL_PREG_RESET="RESET0";
defparam n1311_s.ADDSUB0_PREG_CLK="BYPASS";
defparam n1311_s.ADDSUB0_PREG_CE="CE0";
defparam n1311_s.ADDSUB0_PREG_RESET="RESET0";
defparam n1311_s.ADDSUB1_PREG_CLK="BYPASS";
defparam n1311_s.ADDSUB1_PREG_CE="CE0";
defparam n1311_s.ADDSUB1_PREG_RESET="RESET0";
defparam n1311_s.OREG_CLK="CLK0";
defparam n1311_s.OREG_CE="CE1";
defparam n1311_s.OREG_RESET="RESET0";
defparam n1311_s.PRE_LOAD=48'h000000000000;
defparam n1311_s.CASI_SEL=1'b0;
defparam n1311_s.AREG_CLK="CLK0";
defparam n1311_s.AREG_CE="CE0";
defparam n1311_s.AREG_RESET="RESET0";
defparam n1311_s.BREG_CLK="BYPASS";
defparam n1311_s.BREG_CE="CE0";
defparam n1311_s.BREG_RESET="RESET0";
defparam n1311_s.DREG_CLK="BYPASS";
defparam n1311_s.DREG_CE="CE0";
defparam n1311_s.DREG_RESET="RESET0";
defparam n1311_s.PREG_CLK="BYPASS";
defparam n1311_s.PREG_CE="CE0";
defparam n1311_s.PREG_RESET="RESET0";
defparam n1311_s.SOA_PREG_EN="FALSE";
defparam n1311_s.DYN_P_SEL="FALSE";
defparam n1311_s.P_SEL=1'b0;
defparam n1311_s.DYN_P_ADDSUB="FALSE";
defparam n1311_s.P_ADDSUB=1'b0;
defparam n1311_s.ACC_SEL=1'b0;
defparam n1311_s.ADD_SUB_0=1'b0;
defparam n1311_s.ADD_SUB_1=1'b0;
defparam n1311_s.A_SEL=1'b0;
defparam n1311_s.CASISEL_IREG_CE="CE0";
defparam n1311_s.CASISEL_IREG_CLK="BYPASS";
defparam n1311_s.CASISEL_IREG_RESET="RESET0";
defparam n1311_s.CASISEL_PREG_CE="CE0";
defparam n1311_s.CASISEL_PREG_CLK="BYPASS";
defparam n1311_s.CASISEL_PREG_RESET="RESET0";
defparam n1311_s.CSEL_IREG_CE="CE0";
defparam n1311_s.CSEL_IREG_CLK="BYPASS";
defparam n1311_s.CSEL_IREG_RESET="RESET0";
defparam n1311_s.CSEL_PREG_CE="CE0";
defparam n1311_s.CSEL_PREG_CLK="BYPASS";
defparam n1311_s.CSEL_PREG_RESET="RESET0";
defparam n1311_s.C_IREG_CE="CE0";
defparam n1311_s.C_IREG_CLK="BYPASS";
defparam n1311_s.C_IREG_RESET="RESET0";
defparam n1311_s.C_PREG_CE="CE0";
defparam n1311_s.C_PREG_CLK="BYPASS";
defparam n1311_s.C_PREG_RESET="RESET0";
defparam n1311_s.C_SEL=1'b0;
defparam n1311_s.DYN_ACC_SEL="FALSE";
defparam n1311_s.DYN_ADD_SUB_0="FALSE";
defparam n1311_s.DYN_ADD_SUB_1="FALSE";
defparam n1311_s.DYN_A_SEL="FALSE";
defparam n1311_s.DYN_CASI_SEL="FALSE";
defparam n1311_s.DYN_C_SEL="FALSE";
defparam n1311_s.MULT12X12_EN="FALSE";
defparam n1311_s.PADDSUB_IREG_CE="CE0";
defparam n1311_s.PADDSUB_IREG_CLK="BYPASS";
defparam n1311_s.PADDSUB_IREG_RESET="RESET0";
defparam n1311_s.PSEL_IREG_CE="CE0";
defparam n1311_s.PSEL_IREG_CLK="BYPASS";
defparam n1311_s.PSEL_IREG_RESET="RESET0";
  MULTALU27X18 n1343_s (
    .DOUT({DOUT_4[47:32],\right_q[0] [31:14],DOUT_4[13:0]}),
    .CASO(CASO_4[47:0]),
    .SOA(SOA_3[26:0]),
    .A({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .SIA(n13110[26:0]),
    .B({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,pans_d[6:0]}),
    .C({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .D({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .CASI({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .ACCSEL(GND),
    .PSEL(GND),
    .ASEL(GND),
    .PADDSUB(GND),
    .CSEL(GND),
    .CASISEL(GND),
    .ADDSUB({GND,GND}),
    .CLK({GND,clk_d}),
    .CE({valid_pipe[1],VCC}),
    .RESET({GND,n232_6}) 
);
defparam n1343_s.MULT_RESET_MODE="ASYNC";
defparam n1343_s.ACCSEL_IREG_CLK="BYPASS";
defparam n1343_s.ACCSEL_IREG_CE="CE0";
defparam n1343_s.ACCSEL_IREG_RESET="RESET0";
defparam n1343_s.ADDSUB0_IREG_CLK="BYPASS";
defparam n1343_s.ADDSUB0_IREG_CE="CE0";
defparam n1343_s.ADDSUB0_IREG_RESET="RESET0";
defparam n1343_s.ADDSUB1_IREG_CLK="BYPASS";
defparam n1343_s.ADDSUB1_IREG_CE="CE0";
defparam n1343_s.ADDSUB1_IREG_RESET="RESET0";
defparam n1343_s.FB_PREG_EN="FALSE";
defparam n1343_s.ACCSEL_PREG_CLK="BYPASS";
defparam n1343_s.ACCSEL_PREG_CE="CE0";
defparam n1343_s.ACCSEL_PREG_RESET="RESET0";
defparam n1343_s.ADDSUB0_PREG_CLK="BYPASS";
defparam n1343_s.ADDSUB0_PREG_CE="CE0";
defparam n1343_s.ADDSUB0_PREG_RESET="RESET0";
defparam n1343_s.ADDSUB1_PREG_CLK="BYPASS";
defparam n1343_s.ADDSUB1_PREG_CE="CE0";
defparam n1343_s.ADDSUB1_PREG_RESET="RESET0";
defparam n1343_s.OREG_CLK="CLK0";
defparam n1343_s.OREG_CE="CE1";
defparam n1343_s.OREG_RESET="RESET0";
defparam n1343_s.PRE_LOAD=48'h000000000000;
defparam n1343_s.CASI_SEL=1'b0;
defparam n1343_s.AREG_CLK="BYPASS";
defparam n1343_s.AREG_CE="CE0";
defparam n1343_s.AREG_RESET="RESET0";
defparam n1343_s.BREG_CLK="BYPASS";
defparam n1343_s.BREG_CE="CE0";
defparam n1343_s.BREG_RESET="RESET0";
defparam n1343_s.DREG_CLK="BYPASS";
defparam n1343_s.DREG_CE="CE0";
defparam n1343_s.DREG_RESET="RESET0";
defparam n1343_s.PREG_CLK="BYPASS";
defparam n1343_s.PREG_CE="CE0";
defparam n1343_s.PREG_RESET="RESET0";
defparam n1343_s.SOA_PREG_EN="FALSE";
defparam n1343_s.DYN_P_SEL="FALSE";
defparam n1343_s.P_SEL=1'b0;
defparam n1343_s.DYN_P_ADDSUB="FALSE";
defparam n1343_s.P_ADDSUB=1'b0;
defparam n1343_s.ACC_SEL=1'b0;
defparam n1343_s.ADD_SUB_0=1'b0;
defparam n1343_s.ADD_SUB_1=1'b0;
defparam n1343_s.A_SEL=1'b1;
defparam n1343_s.CASISEL_IREG_CE="CE0";
defparam n1343_s.CASISEL_IREG_CLK="BYPASS";
defparam n1343_s.CASISEL_IREG_RESET="RESET0";
defparam n1343_s.CASISEL_PREG_CE="CE0";
defparam n1343_s.CASISEL_PREG_CLK="BYPASS";
defparam n1343_s.CASISEL_PREG_RESET="RESET0";
defparam n1343_s.CSEL_IREG_CE="CE0";
defparam n1343_s.CSEL_IREG_CLK="BYPASS";
defparam n1343_s.CSEL_IREG_RESET="RESET0";
defparam n1343_s.CSEL_PREG_CE="CE0";
defparam n1343_s.CSEL_PREG_CLK="BYPASS";
defparam n1343_s.CSEL_PREG_RESET="RESET0";
defparam n1343_s.C_IREG_CE="CE0";
defparam n1343_s.C_IREG_CLK="BYPASS";
defparam n1343_s.C_IREG_RESET="RESET0";
defparam n1343_s.C_PREG_CE="CE0";
defparam n1343_s.C_PREG_CLK="BYPASS";
defparam n1343_s.C_PREG_RESET="RESET0";
defparam n1343_s.C_SEL=1'b0;
defparam n1343_s.DYN_ACC_SEL="FALSE";
defparam n1343_s.DYN_ADD_SUB_0="FALSE";
defparam n1343_s.DYN_ADD_SUB_1="FALSE";
defparam n1343_s.DYN_A_SEL="FALSE";
defparam n1343_s.DYN_CASI_SEL="FALSE";
defparam n1343_s.DYN_C_SEL="FALSE";
defparam n1343_s.MULT12X12_EN="FALSE";
defparam n1343_s.PADDSUB_IREG_CE="CE0";
defparam n1343_s.PADDSUB_IREG_CLK="BYPASS";
defparam n1343_s.PADDSUB_IREG_RESET="RESET0";
defparam n1343_s.PSEL_IREG_CE="CE0";
defparam n1343_s.PSEL_IREG_CLK="BYPASS";
defparam n1343_s.PSEL_IREG_RESET="RESET0";
  MULTALU27X18 n1382_s (
    .DOUT({DOUT_5[47:32],\left_q[1] [31:14],DOUT_5[13:0]}),
    .CASO(CASO_5[47:0]),
    .SOA(n13820[26:0]),
    .A({n1105_2,n1105_2,n1105_2,n1105_2,n1106_1,n1107_1,n1108_1,n1109_1,n1110_1,n1111_1,n1112_1,n1113_1,n1114_1,n1115_1,n1116_1,n1117_1,n1118_1,n1119_1,n1120_1,n1121_1,n1122_1,n1123_1,n1124_1,n1125_1,n1126_1,n1127_1,n1128_2}),
    .SIA({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .B({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,n1344_6,n1345_6,n1346_6,n1347_6,n1348_6,n1349_6,n1350_6}),
    .C({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .D({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .CASI({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .ACCSEL(GND),
    .PSEL(GND),
    .ASEL(GND),
    .PADDSUB(GND),
    .CSEL(GND),
    .CASISEL(GND),
    .ADDSUB({GND,GND}),
    .CLK({GND,clk_d}),
    .CE(valid_pipe[1:0]),
    .RESET({GND,n232_6}) 
);
defparam n1382_s.MULT_RESET_MODE="ASYNC";
defparam n1382_s.ACCSEL_IREG_CLK="BYPASS";
defparam n1382_s.ACCSEL_IREG_CE="CE0";
defparam n1382_s.ACCSEL_IREG_RESET="RESET0";
defparam n1382_s.ADDSUB0_IREG_CLK="BYPASS";
defparam n1382_s.ADDSUB0_IREG_CE="CE0";
defparam n1382_s.ADDSUB0_IREG_RESET="RESET0";
defparam n1382_s.ADDSUB1_IREG_CLK="BYPASS";
defparam n1382_s.ADDSUB1_IREG_CE="CE0";
defparam n1382_s.ADDSUB1_IREG_RESET="RESET0";
defparam n1382_s.FB_PREG_EN="FALSE";
defparam n1382_s.ACCSEL_PREG_CLK="BYPASS";
defparam n1382_s.ACCSEL_PREG_CE="CE0";
defparam n1382_s.ACCSEL_PREG_RESET="RESET0";
defparam n1382_s.ADDSUB0_PREG_CLK="BYPASS";
defparam n1382_s.ADDSUB0_PREG_CE="CE0";
defparam n1382_s.ADDSUB0_PREG_RESET="RESET0";
defparam n1382_s.ADDSUB1_PREG_CLK="BYPASS";
defparam n1382_s.ADDSUB1_PREG_CE="CE0";
defparam n1382_s.ADDSUB1_PREG_RESET="RESET0";
defparam n1382_s.OREG_CLK="CLK0";
defparam n1382_s.OREG_CE="CE1";
defparam n1382_s.OREG_RESET="RESET0";
defparam n1382_s.PRE_LOAD=48'h000000000000;
defparam n1382_s.CASI_SEL=1'b0;
defparam n1382_s.AREG_CLK="CLK0";
defparam n1382_s.AREG_CE="CE0";
defparam n1382_s.AREG_RESET="RESET0";
defparam n1382_s.BREG_CLK="BYPASS";
defparam n1382_s.BREG_CE="CE0";
defparam n1382_s.BREG_RESET="RESET0";
defparam n1382_s.DREG_CLK="BYPASS";
defparam n1382_s.DREG_CE="CE0";
defparam n1382_s.DREG_RESET="RESET0";
defparam n1382_s.PREG_CLK="BYPASS";
defparam n1382_s.PREG_CE="CE0";
defparam n1382_s.PREG_RESET="RESET0";
defparam n1382_s.SOA_PREG_EN="FALSE";
defparam n1382_s.DYN_P_SEL="FALSE";
defparam n1382_s.P_SEL=1'b0;
defparam n1382_s.DYN_P_ADDSUB="FALSE";
defparam n1382_s.P_ADDSUB=1'b0;
defparam n1382_s.ACC_SEL=1'b0;
defparam n1382_s.ADD_SUB_0=1'b0;
defparam n1382_s.ADD_SUB_1=1'b0;
defparam n1382_s.A_SEL=1'b0;
defparam n1382_s.CASISEL_IREG_CE="CE0";
defparam n1382_s.CASISEL_IREG_CLK="BYPASS";
defparam n1382_s.CASISEL_IREG_RESET="RESET0";
defparam n1382_s.CASISEL_PREG_CE="CE0";
defparam n1382_s.CASISEL_PREG_CLK="BYPASS";
defparam n1382_s.CASISEL_PREG_RESET="RESET0";
defparam n1382_s.CSEL_IREG_CE="CE0";
defparam n1382_s.CSEL_IREG_CLK="BYPASS";
defparam n1382_s.CSEL_IREG_RESET="RESET0";
defparam n1382_s.CSEL_PREG_CE="CE0";
defparam n1382_s.CSEL_PREG_CLK="BYPASS";
defparam n1382_s.CSEL_PREG_RESET="RESET0";
defparam n1382_s.C_IREG_CE="CE0";
defparam n1382_s.C_IREG_CLK="BYPASS";
defparam n1382_s.C_IREG_RESET="RESET0";
defparam n1382_s.C_PREG_CE="CE0";
defparam n1382_s.C_PREG_CLK="BYPASS";
defparam n1382_s.C_PREG_RESET="RESET0";
defparam n1382_s.C_SEL=1'b0;
defparam n1382_s.DYN_ACC_SEL="FALSE";
defparam n1382_s.DYN_ADD_SUB_0="FALSE";
defparam n1382_s.DYN_ADD_SUB_1="FALSE";
defparam n1382_s.DYN_A_SEL="FALSE";
defparam n1382_s.DYN_CASI_SEL="FALSE";
defparam n1382_s.DYN_C_SEL="FALSE";
defparam n1382_s.MULT12X12_EN="FALSE";
defparam n1382_s.PADDSUB_IREG_CE="CE0";
defparam n1382_s.PADDSUB_IREG_CLK="BYPASS";
defparam n1382_s.PADDSUB_IREG_RESET="RESET0";
defparam n1382_s.PSEL_IREG_CE="CE0";
defparam n1382_s.PSEL_IREG_CLK="BYPASS";
defparam n1382_s.PSEL_IREG_RESET="RESET0";
  MULTALU27X18 n1414_s (
    .DOUT({DOUT_6[47:32],\right_q[1] [31:14],DOUT_6[13:0]}),
    .CASO(CASO_6[47:0]),
    .SOA(SOA_4[26:0]),
    .A({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .SIA(n13820[26:0]),
    .B({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,pans_d[13:7]}),
    .C({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .D({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .CASI({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .ACCSEL(GND),
    .PSEL(GND),
    .ASEL(GND),
    .PADDSUB(GND),
    .CSEL(GND),
    .CASISEL(GND),
    .ADDSUB({GND,GND}),
    .CLK({GND,clk_d}),
    .CE({valid_pipe[1],VCC}),
    .RESET({GND,n232_6}) 
);
defparam n1414_s.MULT_RESET_MODE="ASYNC";
defparam n1414_s.ACCSEL_IREG_CLK="BYPASS";
defparam n1414_s.ACCSEL_IREG_CE="CE0";
defparam n1414_s.ACCSEL_IREG_RESET="RESET0";
defparam n1414_s.ADDSUB0_IREG_CLK="BYPASS";
defparam n1414_s.ADDSUB0_IREG_CE="CE0";
defparam n1414_s.ADDSUB0_IREG_RESET="RESET0";
defparam n1414_s.ADDSUB1_IREG_CLK="BYPASS";
defparam n1414_s.ADDSUB1_IREG_CE="CE0";
defparam n1414_s.ADDSUB1_IREG_RESET="RESET0";
defparam n1414_s.FB_PREG_EN="FALSE";
defparam n1414_s.ACCSEL_PREG_CLK="BYPASS";
defparam n1414_s.ACCSEL_PREG_CE="CE0";
defparam n1414_s.ACCSEL_PREG_RESET="RESET0";
defparam n1414_s.ADDSUB0_PREG_CLK="BYPASS";
defparam n1414_s.ADDSUB0_PREG_CE="CE0";
defparam n1414_s.ADDSUB0_PREG_RESET="RESET0";
defparam n1414_s.ADDSUB1_PREG_CLK="BYPASS";
defparam n1414_s.ADDSUB1_PREG_CE="CE0";
defparam n1414_s.ADDSUB1_PREG_RESET="RESET0";
defparam n1414_s.OREG_CLK="CLK0";
defparam n1414_s.OREG_CE="CE1";
defparam n1414_s.OREG_RESET="RESET0";
defparam n1414_s.PRE_LOAD=48'h000000000000;
defparam n1414_s.CASI_SEL=1'b0;
defparam n1414_s.AREG_CLK="BYPASS";
defparam n1414_s.AREG_CE="CE0";
defparam n1414_s.AREG_RESET="RESET0";
defparam n1414_s.BREG_CLK="BYPASS";
defparam n1414_s.BREG_CE="CE0";
defparam n1414_s.BREG_RESET="RESET0";
defparam n1414_s.DREG_CLK="BYPASS";
defparam n1414_s.DREG_CE="CE0";
defparam n1414_s.DREG_RESET="RESET0";
defparam n1414_s.PREG_CLK="BYPASS";
defparam n1414_s.PREG_CE="CE0";
defparam n1414_s.PREG_RESET="RESET0";
defparam n1414_s.SOA_PREG_EN="FALSE";
defparam n1414_s.DYN_P_SEL="FALSE";
defparam n1414_s.P_SEL=1'b0;
defparam n1414_s.DYN_P_ADDSUB="FALSE";
defparam n1414_s.P_ADDSUB=1'b0;
defparam n1414_s.ACC_SEL=1'b0;
defparam n1414_s.ADD_SUB_0=1'b0;
defparam n1414_s.ADD_SUB_1=1'b0;
defparam n1414_s.A_SEL=1'b1;
defparam n1414_s.CASISEL_IREG_CE="CE0";
defparam n1414_s.CASISEL_IREG_CLK="BYPASS";
defparam n1414_s.CASISEL_IREG_RESET="RESET0";
defparam n1414_s.CASISEL_PREG_CE="CE0";
defparam n1414_s.CASISEL_PREG_CLK="BYPASS";
defparam n1414_s.CASISEL_PREG_RESET="RESET0";
defparam n1414_s.CSEL_IREG_CE="CE0";
defparam n1414_s.CSEL_IREG_CLK="BYPASS";
defparam n1414_s.CSEL_IREG_RESET="RESET0";
defparam n1414_s.CSEL_PREG_CE="CE0";
defparam n1414_s.CSEL_PREG_CLK="BYPASS";
defparam n1414_s.CSEL_PREG_RESET="RESET0";
defparam n1414_s.C_IREG_CE="CE0";
defparam n1414_s.C_IREG_CLK="BYPASS";
defparam n1414_s.C_IREG_RESET="RESET0";
defparam n1414_s.C_PREG_CE="CE0";
defparam n1414_s.C_PREG_CLK="BYPASS";
defparam n1414_s.C_PREG_RESET="RESET0";
defparam n1414_s.C_SEL=1'b0;
defparam n1414_s.DYN_ACC_SEL="FALSE";
defparam n1414_s.DYN_ADD_SUB_0="FALSE";
defparam n1414_s.DYN_ADD_SUB_1="FALSE";
defparam n1414_s.DYN_A_SEL="FALSE";
defparam n1414_s.DYN_CASI_SEL="FALSE";
defparam n1414_s.DYN_C_SEL="FALSE";
defparam n1414_s.MULT12X12_EN="FALSE";
defparam n1414_s.PADDSUB_IREG_CE="CE0";
defparam n1414_s.PADDSUB_IREG_CLK="BYPASS";
defparam n1414_s.PADDSUB_IREG_RESET="RESET0";
defparam n1414_s.PSEL_IREG_CE="CE0";
defparam n1414_s.PSEL_IREG_CLK="BYPASS";
defparam n1414_s.PSEL_IREG_RESET="RESET0";
  MULTALU27X18 n1453_s (
    .DOUT({DOUT_7[47:32],\left_q[2] [31:14],DOUT_7[13:0]}),
    .CASO(CASO_7[47:0]),
    .SOA(n14530[26:0]),
    .A({n1129_2,n1129_2,n1129_2,n1129_2,n1130_1,n1131_1,n1132_1,n1133_1,n1134_1,n1135_1,n1136_1,n1137_1,n1138_1,n1139_1,n1140_1,n1141_1,n1142_1,n1143_1,n1144_1,n1145_1,n1146_1,n1147_1,n1148_1,n1149_1,n1150_1,n1151_1,n1152_2}),
    .SIA({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .B({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,n1415_6,n1416_6,n1417_6,n1418_6,n1419_6,n1420_6,n1421_6}),
    .C({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .D({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .CASI({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .ACCSEL(GND),
    .PSEL(GND),
    .ASEL(GND),
    .PADDSUB(GND),
    .CSEL(GND),
    .CASISEL(GND),
    .ADDSUB({GND,GND}),
    .CLK({GND,clk_d}),
    .CE(valid_pipe[1:0]),
    .RESET({GND,n232_6}) 
);
defparam n1453_s.MULT_RESET_MODE="ASYNC";
defparam n1453_s.ACCSEL_IREG_CLK="BYPASS";
defparam n1453_s.ACCSEL_IREG_CE="CE0";
defparam n1453_s.ACCSEL_IREG_RESET="RESET0";
defparam n1453_s.ADDSUB0_IREG_CLK="BYPASS";
defparam n1453_s.ADDSUB0_IREG_CE="CE0";
defparam n1453_s.ADDSUB0_IREG_RESET="RESET0";
defparam n1453_s.ADDSUB1_IREG_CLK="BYPASS";
defparam n1453_s.ADDSUB1_IREG_CE="CE0";
defparam n1453_s.ADDSUB1_IREG_RESET="RESET0";
defparam n1453_s.FB_PREG_EN="FALSE";
defparam n1453_s.ACCSEL_PREG_CLK="BYPASS";
defparam n1453_s.ACCSEL_PREG_CE="CE0";
defparam n1453_s.ACCSEL_PREG_RESET="RESET0";
defparam n1453_s.ADDSUB0_PREG_CLK="BYPASS";
defparam n1453_s.ADDSUB0_PREG_CE="CE0";
defparam n1453_s.ADDSUB0_PREG_RESET="RESET0";
defparam n1453_s.ADDSUB1_PREG_CLK="BYPASS";
defparam n1453_s.ADDSUB1_PREG_CE="CE0";
defparam n1453_s.ADDSUB1_PREG_RESET="RESET0";
defparam n1453_s.OREG_CLK="CLK0";
defparam n1453_s.OREG_CE="CE1";
defparam n1453_s.OREG_RESET="RESET0";
defparam n1453_s.PRE_LOAD=48'h000000000000;
defparam n1453_s.CASI_SEL=1'b0;
defparam n1453_s.AREG_CLK="CLK0";
defparam n1453_s.AREG_CE="CE0";
defparam n1453_s.AREG_RESET="RESET0";
defparam n1453_s.BREG_CLK="BYPASS";
defparam n1453_s.BREG_CE="CE0";
defparam n1453_s.BREG_RESET="RESET0";
defparam n1453_s.DREG_CLK="BYPASS";
defparam n1453_s.DREG_CE="CE0";
defparam n1453_s.DREG_RESET="RESET0";
defparam n1453_s.PREG_CLK="BYPASS";
defparam n1453_s.PREG_CE="CE0";
defparam n1453_s.PREG_RESET="RESET0";
defparam n1453_s.SOA_PREG_EN="FALSE";
defparam n1453_s.DYN_P_SEL="FALSE";
defparam n1453_s.P_SEL=1'b0;
defparam n1453_s.DYN_P_ADDSUB="FALSE";
defparam n1453_s.P_ADDSUB=1'b0;
defparam n1453_s.ACC_SEL=1'b0;
defparam n1453_s.ADD_SUB_0=1'b0;
defparam n1453_s.ADD_SUB_1=1'b0;
defparam n1453_s.A_SEL=1'b0;
defparam n1453_s.CASISEL_IREG_CE="CE0";
defparam n1453_s.CASISEL_IREG_CLK="BYPASS";
defparam n1453_s.CASISEL_IREG_RESET="RESET0";
defparam n1453_s.CASISEL_PREG_CE="CE0";
defparam n1453_s.CASISEL_PREG_CLK="BYPASS";
defparam n1453_s.CASISEL_PREG_RESET="RESET0";
defparam n1453_s.CSEL_IREG_CE="CE0";
defparam n1453_s.CSEL_IREG_CLK="BYPASS";
defparam n1453_s.CSEL_IREG_RESET="RESET0";
defparam n1453_s.CSEL_PREG_CE="CE0";
defparam n1453_s.CSEL_PREG_CLK="BYPASS";
defparam n1453_s.CSEL_PREG_RESET="RESET0";
defparam n1453_s.C_IREG_CE="CE0";
defparam n1453_s.C_IREG_CLK="BYPASS";
defparam n1453_s.C_IREG_RESET="RESET0";
defparam n1453_s.C_PREG_CE="CE0";
defparam n1453_s.C_PREG_CLK="BYPASS";
defparam n1453_s.C_PREG_RESET="RESET0";
defparam n1453_s.C_SEL=1'b0;
defparam n1453_s.DYN_ACC_SEL="FALSE";
defparam n1453_s.DYN_ADD_SUB_0="FALSE";
defparam n1453_s.DYN_ADD_SUB_1="FALSE";
defparam n1453_s.DYN_A_SEL="FALSE";
defparam n1453_s.DYN_CASI_SEL="FALSE";
defparam n1453_s.DYN_C_SEL="FALSE";
defparam n1453_s.MULT12X12_EN="FALSE";
defparam n1453_s.PADDSUB_IREG_CE="CE0";
defparam n1453_s.PADDSUB_IREG_CLK="BYPASS";
defparam n1453_s.PADDSUB_IREG_RESET="RESET0";
defparam n1453_s.PSEL_IREG_CE="CE0";
defparam n1453_s.PSEL_IREG_CLK="BYPASS";
defparam n1453_s.PSEL_IREG_RESET="RESET0";
  MULTALU27X18 n1485_s (
    .DOUT({DOUT_8[47:32],\right_q[2] [31:14],DOUT_8[13:0]}),
    .CASO(CASO_8[47:0]),
    .SOA(SOA_5[26:0]),
    .A({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .SIA(n14530[26:0]),
    .B({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,pans_d[20:14]}),
    .C({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .D({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .CASI({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .ACCSEL(GND),
    .PSEL(GND),
    .ASEL(GND),
    .PADDSUB(GND),
    .CSEL(GND),
    .CASISEL(GND),
    .ADDSUB({GND,GND}),
    .CLK({GND,clk_d}),
    .CE({valid_pipe[1],VCC}),
    .RESET({GND,n232_6}) 
);
defparam n1485_s.MULT_RESET_MODE="ASYNC";
defparam n1485_s.ACCSEL_IREG_CLK="BYPASS";
defparam n1485_s.ACCSEL_IREG_CE="CE0";
defparam n1485_s.ACCSEL_IREG_RESET="RESET0";
defparam n1485_s.ADDSUB0_IREG_CLK="BYPASS";
defparam n1485_s.ADDSUB0_IREG_CE="CE0";
defparam n1485_s.ADDSUB0_IREG_RESET="RESET0";
defparam n1485_s.ADDSUB1_IREG_CLK="BYPASS";
defparam n1485_s.ADDSUB1_IREG_CE="CE0";
defparam n1485_s.ADDSUB1_IREG_RESET="RESET0";
defparam n1485_s.FB_PREG_EN="FALSE";
defparam n1485_s.ACCSEL_PREG_CLK="BYPASS";
defparam n1485_s.ACCSEL_PREG_CE="CE0";
defparam n1485_s.ACCSEL_PREG_RESET="RESET0";
defparam n1485_s.ADDSUB0_PREG_CLK="BYPASS";
defparam n1485_s.ADDSUB0_PREG_CE="CE0";
defparam n1485_s.ADDSUB0_PREG_RESET="RESET0";
defparam n1485_s.ADDSUB1_PREG_CLK="BYPASS";
defparam n1485_s.ADDSUB1_PREG_CE="CE0";
defparam n1485_s.ADDSUB1_PREG_RESET="RESET0";
defparam n1485_s.OREG_CLK="CLK0";
defparam n1485_s.OREG_CE="CE1";
defparam n1485_s.OREG_RESET="RESET0";
defparam n1485_s.PRE_LOAD=48'h000000000000;
defparam n1485_s.CASI_SEL=1'b0;
defparam n1485_s.AREG_CLK="BYPASS";
defparam n1485_s.AREG_CE="CE0";
defparam n1485_s.AREG_RESET="RESET0";
defparam n1485_s.BREG_CLK="BYPASS";
defparam n1485_s.BREG_CE="CE0";
defparam n1485_s.BREG_RESET="RESET0";
defparam n1485_s.DREG_CLK="BYPASS";
defparam n1485_s.DREG_CE="CE0";
defparam n1485_s.DREG_RESET="RESET0";
defparam n1485_s.PREG_CLK="BYPASS";
defparam n1485_s.PREG_CE="CE0";
defparam n1485_s.PREG_RESET="RESET0";
defparam n1485_s.SOA_PREG_EN="FALSE";
defparam n1485_s.DYN_P_SEL="FALSE";
defparam n1485_s.P_SEL=1'b0;
defparam n1485_s.DYN_P_ADDSUB="FALSE";
defparam n1485_s.P_ADDSUB=1'b0;
defparam n1485_s.ACC_SEL=1'b0;
defparam n1485_s.ADD_SUB_0=1'b0;
defparam n1485_s.ADD_SUB_1=1'b0;
defparam n1485_s.A_SEL=1'b1;
defparam n1485_s.CASISEL_IREG_CE="CE0";
defparam n1485_s.CASISEL_IREG_CLK="BYPASS";
defparam n1485_s.CASISEL_IREG_RESET="RESET0";
defparam n1485_s.CASISEL_PREG_CE="CE0";
defparam n1485_s.CASISEL_PREG_CLK="BYPASS";
defparam n1485_s.CASISEL_PREG_RESET="RESET0";
defparam n1485_s.CSEL_IREG_CE="CE0";
defparam n1485_s.CSEL_IREG_CLK="BYPASS";
defparam n1485_s.CSEL_IREG_RESET="RESET0";
defparam n1485_s.CSEL_PREG_CE="CE0";
defparam n1485_s.CSEL_PREG_CLK="BYPASS";
defparam n1485_s.CSEL_PREG_RESET="RESET0";
defparam n1485_s.C_IREG_CE="CE0";
defparam n1485_s.C_IREG_CLK="BYPASS";
defparam n1485_s.C_IREG_RESET="RESET0";
defparam n1485_s.C_PREG_CE="CE0";
defparam n1485_s.C_PREG_CLK="BYPASS";
defparam n1485_s.C_PREG_RESET="RESET0";
defparam n1485_s.C_SEL=1'b0;
defparam n1485_s.DYN_ACC_SEL="FALSE";
defparam n1485_s.DYN_ADD_SUB_0="FALSE";
defparam n1485_s.DYN_ADD_SUB_1="FALSE";
defparam n1485_s.DYN_A_SEL="FALSE";
defparam n1485_s.DYN_CASI_SEL="FALSE";
defparam n1485_s.DYN_C_SEL="FALSE";
defparam n1485_s.MULT12X12_EN="FALSE";
defparam n1485_s.PADDSUB_IREG_CE="CE0";
defparam n1485_s.PADDSUB_IREG_CLK="BYPASS";
defparam n1485_s.PADDSUB_IREG_RESET="RESET0";
defparam n1485_s.PSEL_IREG_CE="CE0";
defparam n1485_s.PSEL_IREG_CLK="BYPASS";
defparam n1485_s.PSEL_IREG_RESET="RESET0";
  MULTALU27X18 n1524_s (
    .DOUT({DOUT_9[47:32],\left_q[3] [31:14],DOUT_9[13:0]}),
    .CASO(CASO_9[47:0]),
    .SOA(n15240[26:0]),
    .A({n1153_2,n1153_2,n1153_2,n1153_2,n1154_1,n1155_1,n1156_1,n1157_1,n1158_1,n1159_1,n1160_1,n1161_1,n1162_1,n1163_1,n1164_1,n1165_1,n1166_1,n1167_1,n1168_1,n1169_1,n1170_1,n1171_1,n1172_1,n1173_1,n1174_1,n1175_1,n1176_2}),
    .SIA({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .B({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,n1486_6,n1487_6,n1488_6,n1489_6,n1490_6,n1491_6,n1492_6}),
    .C({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .D({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .CASI({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .ACCSEL(GND),
    .PSEL(GND),
    .ASEL(GND),
    .PADDSUB(GND),
    .CSEL(GND),
    .CASISEL(GND),
    .ADDSUB({GND,GND}),
    .CLK({GND,clk_d}),
    .CE(valid_pipe[1:0]),
    .RESET({GND,n232_6}) 
);
defparam n1524_s.MULT_RESET_MODE="ASYNC";
defparam n1524_s.ACCSEL_IREG_CLK="BYPASS";
defparam n1524_s.ACCSEL_IREG_CE="CE0";
defparam n1524_s.ACCSEL_IREG_RESET="RESET0";
defparam n1524_s.ADDSUB0_IREG_CLK="BYPASS";
defparam n1524_s.ADDSUB0_IREG_CE="CE0";
defparam n1524_s.ADDSUB0_IREG_RESET="RESET0";
defparam n1524_s.ADDSUB1_IREG_CLK="BYPASS";
defparam n1524_s.ADDSUB1_IREG_CE="CE0";
defparam n1524_s.ADDSUB1_IREG_RESET="RESET0";
defparam n1524_s.FB_PREG_EN="FALSE";
defparam n1524_s.ACCSEL_PREG_CLK="BYPASS";
defparam n1524_s.ACCSEL_PREG_CE="CE0";
defparam n1524_s.ACCSEL_PREG_RESET="RESET0";
defparam n1524_s.ADDSUB0_PREG_CLK="BYPASS";
defparam n1524_s.ADDSUB0_PREG_CE="CE0";
defparam n1524_s.ADDSUB0_PREG_RESET="RESET0";
defparam n1524_s.ADDSUB1_PREG_CLK="BYPASS";
defparam n1524_s.ADDSUB1_PREG_CE="CE0";
defparam n1524_s.ADDSUB1_PREG_RESET="RESET0";
defparam n1524_s.OREG_CLK="CLK0";
defparam n1524_s.OREG_CE="CE1";
defparam n1524_s.OREG_RESET="RESET0";
defparam n1524_s.PRE_LOAD=48'h000000000000;
defparam n1524_s.CASI_SEL=1'b0;
defparam n1524_s.AREG_CLK="CLK0";
defparam n1524_s.AREG_CE="CE0";
defparam n1524_s.AREG_RESET="RESET0";
defparam n1524_s.BREG_CLK="BYPASS";
defparam n1524_s.BREG_CE="CE0";
defparam n1524_s.BREG_RESET="RESET0";
defparam n1524_s.DREG_CLK="BYPASS";
defparam n1524_s.DREG_CE="CE0";
defparam n1524_s.DREG_RESET="RESET0";
defparam n1524_s.PREG_CLK="BYPASS";
defparam n1524_s.PREG_CE="CE0";
defparam n1524_s.PREG_RESET="RESET0";
defparam n1524_s.SOA_PREG_EN="FALSE";
defparam n1524_s.DYN_P_SEL="FALSE";
defparam n1524_s.P_SEL=1'b0;
defparam n1524_s.DYN_P_ADDSUB="FALSE";
defparam n1524_s.P_ADDSUB=1'b0;
defparam n1524_s.ACC_SEL=1'b0;
defparam n1524_s.ADD_SUB_0=1'b0;
defparam n1524_s.ADD_SUB_1=1'b0;
defparam n1524_s.A_SEL=1'b0;
defparam n1524_s.CASISEL_IREG_CE="CE0";
defparam n1524_s.CASISEL_IREG_CLK="BYPASS";
defparam n1524_s.CASISEL_IREG_RESET="RESET0";
defparam n1524_s.CASISEL_PREG_CE="CE0";
defparam n1524_s.CASISEL_PREG_CLK="BYPASS";
defparam n1524_s.CASISEL_PREG_RESET="RESET0";
defparam n1524_s.CSEL_IREG_CE="CE0";
defparam n1524_s.CSEL_IREG_CLK="BYPASS";
defparam n1524_s.CSEL_IREG_RESET="RESET0";
defparam n1524_s.CSEL_PREG_CE="CE0";
defparam n1524_s.CSEL_PREG_CLK="BYPASS";
defparam n1524_s.CSEL_PREG_RESET="RESET0";
defparam n1524_s.C_IREG_CE="CE0";
defparam n1524_s.C_IREG_CLK="BYPASS";
defparam n1524_s.C_IREG_RESET="RESET0";
defparam n1524_s.C_PREG_CE="CE0";
defparam n1524_s.C_PREG_CLK="BYPASS";
defparam n1524_s.C_PREG_RESET="RESET0";
defparam n1524_s.C_SEL=1'b0;
defparam n1524_s.DYN_ACC_SEL="FALSE";
defparam n1524_s.DYN_ADD_SUB_0="FALSE";
defparam n1524_s.DYN_ADD_SUB_1="FALSE";
defparam n1524_s.DYN_A_SEL="FALSE";
defparam n1524_s.DYN_CASI_SEL="FALSE";
defparam n1524_s.DYN_C_SEL="FALSE";
defparam n1524_s.MULT12X12_EN="FALSE";
defparam n1524_s.PADDSUB_IREG_CE="CE0";
defparam n1524_s.PADDSUB_IREG_CLK="BYPASS";
defparam n1524_s.PADDSUB_IREG_RESET="RESET0";
defparam n1524_s.PSEL_IREG_CE="CE0";
defparam n1524_s.PSEL_IREG_CLK="BYPASS";
defparam n1524_s.PSEL_IREG_RESET="RESET0";
  MULTALU27X18 n1556_s (
    .DOUT({DOUT_10[47:32],\right_q[3] [31:14],DOUT_10[13:0]}),
    .CASO(CASO_10[47:0]),
    .SOA(SOA_6[26:0]),
    .A({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .SIA(n15240[26:0]),
    .B({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,pans_d[27:21]}),
    .C({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .D({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .CASI({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .ACCSEL(GND),
    .PSEL(GND),
    .ASEL(GND),
    .PADDSUB(GND),
    .CSEL(GND),
    .CASISEL(GND),
    .ADDSUB({GND,GND}),
    .CLK({GND,clk_d}),
    .CE({valid_pipe[1],VCC}),
    .RESET({GND,n232_6}) 
);
defparam n1556_s.MULT_RESET_MODE="ASYNC";
defparam n1556_s.ACCSEL_IREG_CLK="BYPASS";
defparam n1556_s.ACCSEL_IREG_CE="CE0";
defparam n1556_s.ACCSEL_IREG_RESET="RESET0";
defparam n1556_s.ADDSUB0_IREG_CLK="BYPASS";
defparam n1556_s.ADDSUB0_IREG_CE="CE0";
defparam n1556_s.ADDSUB0_IREG_RESET="RESET0";
defparam n1556_s.ADDSUB1_IREG_CLK="BYPASS";
defparam n1556_s.ADDSUB1_IREG_CE="CE0";
defparam n1556_s.ADDSUB1_IREG_RESET="RESET0";
defparam n1556_s.FB_PREG_EN="FALSE";
defparam n1556_s.ACCSEL_PREG_CLK="BYPASS";
defparam n1556_s.ACCSEL_PREG_CE="CE0";
defparam n1556_s.ACCSEL_PREG_RESET="RESET0";
defparam n1556_s.ADDSUB0_PREG_CLK="BYPASS";
defparam n1556_s.ADDSUB0_PREG_CE="CE0";
defparam n1556_s.ADDSUB0_PREG_RESET="RESET0";
defparam n1556_s.ADDSUB1_PREG_CLK="BYPASS";
defparam n1556_s.ADDSUB1_PREG_CE="CE0";
defparam n1556_s.ADDSUB1_PREG_RESET="RESET0";
defparam n1556_s.OREG_CLK="CLK0";
defparam n1556_s.OREG_CE="CE1";
defparam n1556_s.OREG_RESET="RESET0";
defparam n1556_s.PRE_LOAD=48'h000000000000;
defparam n1556_s.CASI_SEL=1'b0;
defparam n1556_s.AREG_CLK="BYPASS";
defparam n1556_s.AREG_CE="CE0";
defparam n1556_s.AREG_RESET="RESET0";
defparam n1556_s.BREG_CLK="BYPASS";
defparam n1556_s.BREG_CE="CE0";
defparam n1556_s.BREG_RESET="RESET0";
defparam n1556_s.DREG_CLK="BYPASS";
defparam n1556_s.DREG_CE="CE0";
defparam n1556_s.DREG_RESET="RESET0";
defparam n1556_s.PREG_CLK="BYPASS";
defparam n1556_s.PREG_CE="CE0";
defparam n1556_s.PREG_RESET="RESET0";
defparam n1556_s.SOA_PREG_EN="FALSE";
defparam n1556_s.DYN_P_SEL="FALSE";
defparam n1556_s.P_SEL=1'b0;
defparam n1556_s.DYN_P_ADDSUB="FALSE";
defparam n1556_s.P_ADDSUB=1'b0;
defparam n1556_s.ACC_SEL=1'b0;
defparam n1556_s.ADD_SUB_0=1'b0;
defparam n1556_s.ADD_SUB_1=1'b0;
defparam n1556_s.A_SEL=1'b1;
defparam n1556_s.CASISEL_IREG_CE="CE0";
defparam n1556_s.CASISEL_IREG_CLK="BYPASS";
defparam n1556_s.CASISEL_IREG_RESET="RESET0";
defparam n1556_s.CASISEL_PREG_CE="CE0";
defparam n1556_s.CASISEL_PREG_CLK="BYPASS";
defparam n1556_s.CASISEL_PREG_RESET="RESET0";
defparam n1556_s.CSEL_IREG_CE="CE0";
defparam n1556_s.CSEL_IREG_CLK="BYPASS";
defparam n1556_s.CSEL_IREG_RESET="RESET0";
defparam n1556_s.CSEL_PREG_CE="CE0";
defparam n1556_s.CSEL_PREG_CLK="BYPASS";
defparam n1556_s.CSEL_PREG_RESET="RESET0";
defparam n1556_s.C_IREG_CE="CE0";
defparam n1556_s.C_IREG_CLK="BYPASS";
defparam n1556_s.C_IREG_RESET="RESET0";
defparam n1556_s.C_PREG_CE="CE0";
defparam n1556_s.C_PREG_CLK="BYPASS";
defparam n1556_s.C_PREG_RESET="RESET0";
defparam n1556_s.C_SEL=1'b0;
defparam n1556_s.DYN_ACC_SEL="FALSE";
defparam n1556_s.DYN_ADD_SUB_0="FALSE";
defparam n1556_s.DYN_ADD_SUB_1="FALSE";
defparam n1556_s.DYN_A_SEL="FALSE";
defparam n1556_s.DYN_CASI_SEL="FALSE";
defparam n1556_s.DYN_C_SEL="FALSE";
defparam n1556_s.MULT12X12_EN="FALSE";
defparam n1556_s.PADDSUB_IREG_CE="CE0";
defparam n1556_s.PADDSUB_IREG_CLK="BYPASS";
defparam n1556_s.PADDSUB_IREG_RESET="RESET0";
defparam n1556_s.PSEL_IREG_CE="CE0";
defparam n1556_s.PSEL_IREG_CLK="BYPASS";
defparam n1556_s.PSEL_IREG_RESET="RESET0";
  MULTALU27X18 n398_s (
    .DOUT({DOUT_11[47:32],n501_1,n502_1,n503_1,n504_1,n505_1,n506_1,n507_1,n508_1,n509_1,n510_1,n511_1,n512_1,n513_1,n514_1,n515_1,n516_1,n517_1,n518_1,n519_1,n520_1,n521_1,n522_1,n523_1,n524_1,n525_1,n526_1,n527_1,n528_1,n529_1,n530_1,n531_1,n532_1}),
    .CASO(CASO_11[47:0]),
    .SOA(SOA_7[26:0]),
    .A({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,frequencies_d[15:0]}),
    .SIA({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .B({GND,VCC,GND,VCC,GND,VCC,VCC,VCC,GND,VCC,VCC,GND,GND,GND,GND,VCC,VCC,GND}),
    .C({n533_6,n533_6,n533_6,n533_6,n533_6,n533_6,n533_6,n533_6,n533_6,n533_6,n533_6,n533_6,n533_6,n533_6,n533_6,n533_6,n533_6,n534_6,n535_6,n536_6,n537_6,n538_6,n539_6,n540_6,n541_6,n542_6,n543_6,n544_6,n545_6,n546_6,n547_6,n548_6,n549_6,n550_6,n551_6,n552_6,n553_6,n554_6,n555_6,n556_6,n557_6,n558_6,n559_6,n560_6,n561_6,n562_6,n563_6,n564_6}),
    .D({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .CASI({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .ACCSEL(GND),
    .PSEL(GND),
    .ASEL(GND),
    .PADDSUB(GND),
    .CSEL(GND),
    .CASISEL(GND),
    .ADDSUB({GND,GND}),
    .CLK({GND,clk_d}),
    .CE({sample_tick_d,VCC}),
    .RESET({GND,n232_6}) 
);
defparam n398_s.MULT_RESET_MODE="ASYNC";
defparam n398_s.ACCSEL_IREG_CLK="BYPASS";
defparam n398_s.ACCSEL_IREG_CE="CE0";
defparam n398_s.ACCSEL_IREG_RESET="RESET0";
defparam n398_s.ADDSUB0_IREG_CLK="BYPASS";
defparam n398_s.ADDSUB0_IREG_CE="CE0";
defparam n398_s.ADDSUB0_IREG_RESET="RESET0";
defparam n398_s.ADDSUB1_IREG_CLK="BYPASS";
defparam n398_s.ADDSUB1_IREG_CE="CE0";
defparam n398_s.ADDSUB1_IREG_RESET="RESET0";
defparam n398_s.FB_PREG_EN="FALSE";
defparam n398_s.ACCSEL_PREG_CLK="BYPASS";
defparam n398_s.ACCSEL_PREG_CE="CE0";
defparam n398_s.ACCSEL_PREG_RESET="RESET0";
defparam n398_s.ADDSUB0_PREG_CLK="BYPASS";
defparam n398_s.ADDSUB0_PREG_CE="CE0";
defparam n398_s.ADDSUB0_PREG_RESET="RESET0";
defparam n398_s.ADDSUB1_PREG_CLK="BYPASS";
defparam n398_s.ADDSUB1_PREG_CE="CE0";
defparam n398_s.ADDSUB1_PREG_RESET="RESET0";
defparam n398_s.OREG_CLK="BYPASS";
defparam n398_s.OREG_CE="CE0";
defparam n398_s.OREG_RESET="RESET0";
defparam n398_s.PRE_LOAD=48'h000000000000;
defparam n398_s.CASI_SEL=1'b0;
defparam n398_s.AREG_CLK="BYPASS";
defparam n398_s.AREG_CE="CE0";
defparam n398_s.AREG_RESET="RESET0";
defparam n398_s.BREG_CLK="BYPASS";
defparam n398_s.BREG_CE="CE0";
defparam n398_s.BREG_RESET="RESET0";
defparam n398_s.DREG_CLK="BYPASS";
defparam n398_s.DREG_CE="CE0";
defparam n398_s.DREG_RESET="RESET0";
defparam n398_s.PREG_CLK="CLK0";
defparam n398_s.PREG_CE="CE0";
defparam n398_s.PREG_RESET="RESET0";
defparam n398_s.SOA_PREG_EN="FALSE";
defparam n398_s.DYN_P_SEL="FALSE";
defparam n398_s.P_SEL=1'b0;
defparam n398_s.DYN_P_ADDSUB="FALSE";
defparam n398_s.P_ADDSUB=1'b0;
defparam n398_s.ACC_SEL=1'b0;
defparam n398_s.ADD_SUB_0=1'b0;
defparam n398_s.ADD_SUB_1=1'b0;
defparam n398_s.A_SEL=1'b0;
defparam n398_s.CASISEL_IREG_CE="CE0";
defparam n398_s.CASISEL_IREG_CLK="BYPASS";
defparam n398_s.CASISEL_IREG_RESET="RESET0";
defparam n398_s.CASISEL_PREG_CE="CE0";
defparam n398_s.CASISEL_PREG_CLK="BYPASS";
defparam n398_s.CASISEL_PREG_RESET="RESET0";
defparam n398_s.CSEL_IREG_CE="CE0";
defparam n398_s.CSEL_IREG_CLK="BYPASS";
defparam n398_s.CSEL_IREG_RESET="RESET0";
defparam n398_s.CSEL_PREG_CE="CE0";
defparam n398_s.CSEL_PREG_CLK="BYPASS";
defparam n398_s.CSEL_PREG_RESET="RESET0";
defparam n398_s.C_IREG_CE="CE1";
defparam n398_s.C_IREG_CLK="CLK0";
defparam n398_s.C_IREG_RESET="RESET0";
defparam n398_s.C_PREG_CE="CE0";
defparam n398_s.C_PREG_CLK="BYPASS";
defparam n398_s.C_PREG_RESET="RESET0";
defparam n398_s.C_SEL=1'b1;
defparam n398_s.DYN_ACC_SEL="FALSE";
defparam n398_s.DYN_ADD_SUB_0="FALSE";
defparam n398_s.DYN_ADD_SUB_1="FALSE";
defparam n398_s.DYN_A_SEL="FALSE";
defparam n398_s.DYN_CASI_SEL="FALSE";
defparam n398_s.DYN_C_SEL="FALSE";
defparam n398_s.MULT12X12_EN="FALSE";
defparam n398_s.PADDSUB_IREG_CE="CE0";
defparam n398_s.PADDSUB_IREG_CLK="BYPASS";
defparam n398_s.PADDSUB_IREG_RESET="RESET0";
defparam n398_s.PSEL_IREG_CE="CE0";
defparam n398_s.PSEL_IREG_CLK="BYPASS";
defparam n398_s.PSEL_IREG_RESET="RESET0";
  MULTALU27X18 n431_s (
    .DOUT({DOUT_12[47:32],n598_1,n599_1,n600_1,n601_1,n602_1,n603_1,n604_1,n605_1,n606_1,n607_1,n608_1,n609_1,n610_1,n611_1,n612_1,n613_1,n614_1,n615_1,n616_1,n617_1,n618_1,n619_1,n620_1,n621_1,n622_1,n623_1,n624_1,n625_1,n626_1,n627_1,n628_1,n629_1}),
    .CASO(CASO_12[47:0]),
    .SOA(SOA_8[26:0]),
    .A({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,frequencies_d[31:16]}),
    .SIA({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .B({GND,VCC,GND,VCC,GND,VCC,VCC,VCC,GND,VCC,VCC,GND,GND,GND,GND,VCC,VCC,GND}),
    .C({n630_6,n630_6,n630_6,n630_6,n630_6,n630_6,n630_6,n630_6,n630_6,n630_6,n630_6,n630_6,n630_6,n630_6,n630_6,n630_6,n630_6,n631_6,n632_6,n633_6,n634_6,n635_6,n636_6,n637_6,n638_6,n639_6,n640_6,n641_6,n642_6,n643_6,n644_6,n645_6,n646_6,n647_6,n648_6,n649_6,n650_6,n651_6,n652_6,n653_6,n654_6,n655_6,n656_6,n657_6,n658_6,n659_6,n660_6,n661_6}),
    .D({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .CASI({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .ACCSEL(GND),
    .PSEL(GND),
    .ASEL(GND),
    .PADDSUB(GND),
    .CSEL(GND),
    .CASISEL(GND),
    .ADDSUB({GND,GND}),
    .CLK({GND,clk_d}),
    .CE({sample_tick_d,VCC}),
    .RESET({GND,n232_6}) 
);
defparam n431_s.MULT_RESET_MODE="ASYNC";
defparam n431_s.ACCSEL_IREG_CLK="BYPASS";
defparam n431_s.ACCSEL_IREG_CE="CE0";
defparam n431_s.ACCSEL_IREG_RESET="RESET0";
defparam n431_s.ADDSUB0_IREG_CLK="BYPASS";
defparam n431_s.ADDSUB0_IREG_CE="CE0";
defparam n431_s.ADDSUB0_IREG_RESET="RESET0";
defparam n431_s.ADDSUB1_IREG_CLK="BYPASS";
defparam n431_s.ADDSUB1_IREG_CE="CE0";
defparam n431_s.ADDSUB1_IREG_RESET="RESET0";
defparam n431_s.FB_PREG_EN="FALSE";
defparam n431_s.ACCSEL_PREG_CLK="BYPASS";
defparam n431_s.ACCSEL_PREG_CE="CE0";
defparam n431_s.ACCSEL_PREG_RESET="RESET0";
defparam n431_s.ADDSUB0_PREG_CLK="BYPASS";
defparam n431_s.ADDSUB0_PREG_CE="CE0";
defparam n431_s.ADDSUB0_PREG_RESET="RESET0";
defparam n431_s.ADDSUB1_PREG_CLK="BYPASS";
defparam n431_s.ADDSUB1_PREG_CE="CE0";
defparam n431_s.ADDSUB1_PREG_RESET="RESET0";
defparam n431_s.OREG_CLK="BYPASS";
defparam n431_s.OREG_CE="CE0";
defparam n431_s.OREG_RESET="RESET0";
defparam n431_s.PRE_LOAD=48'h000000000000;
defparam n431_s.CASI_SEL=1'b0;
defparam n431_s.AREG_CLK="BYPASS";
defparam n431_s.AREG_CE="CE0";
defparam n431_s.AREG_RESET="RESET0";
defparam n431_s.BREG_CLK="BYPASS";
defparam n431_s.BREG_CE="CE0";
defparam n431_s.BREG_RESET="RESET0";
defparam n431_s.DREG_CLK="BYPASS";
defparam n431_s.DREG_CE="CE0";
defparam n431_s.DREG_RESET="RESET0";
defparam n431_s.PREG_CLK="CLK0";
defparam n431_s.PREG_CE="CE0";
defparam n431_s.PREG_RESET="RESET0";
defparam n431_s.SOA_PREG_EN="FALSE";
defparam n431_s.DYN_P_SEL="FALSE";
defparam n431_s.P_SEL=1'b0;
defparam n431_s.DYN_P_ADDSUB="FALSE";
defparam n431_s.P_ADDSUB=1'b0;
defparam n431_s.ACC_SEL=1'b0;
defparam n431_s.ADD_SUB_0=1'b0;
defparam n431_s.ADD_SUB_1=1'b0;
defparam n431_s.A_SEL=1'b0;
defparam n431_s.CASISEL_IREG_CE="CE0";
defparam n431_s.CASISEL_IREG_CLK="BYPASS";
defparam n431_s.CASISEL_IREG_RESET="RESET0";
defparam n431_s.CASISEL_PREG_CE="CE0";
defparam n431_s.CASISEL_PREG_CLK="BYPASS";
defparam n431_s.CASISEL_PREG_RESET="RESET0";
defparam n431_s.CSEL_IREG_CE="CE0";
defparam n431_s.CSEL_IREG_CLK="BYPASS";
defparam n431_s.CSEL_IREG_RESET="RESET0";
defparam n431_s.CSEL_PREG_CE="CE0";
defparam n431_s.CSEL_PREG_CLK="BYPASS";
defparam n431_s.CSEL_PREG_RESET="RESET0";
defparam n431_s.C_IREG_CE="CE1";
defparam n431_s.C_IREG_CLK="CLK0";
defparam n431_s.C_IREG_RESET="RESET0";
defparam n431_s.C_PREG_CE="CE0";
defparam n431_s.C_PREG_CLK="BYPASS";
defparam n431_s.C_PREG_RESET="RESET0";
defparam n431_s.C_SEL=1'b1;
defparam n431_s.DYN_ACC_SEL="FALSE";
defparam n431_s.DYN_ADD_SUB_0="FALSE";
defparam n431_s.DYN_ADD_SUB_1="FALSE";
defparam n431_s.DYN_A_SEL="FALSE";
defparam n431_s.DYN_CASI_SEL="FALSE";
defparam n431_s.DYN_C_SEL="FALSE";
defparam n431_s.MULT12X12_EN="FALSE";
defparam n431_s.PADDSUB_IREG_CE="CE0";
defparam n431_s.PADDSUB_IREG_CLK="BYPASS";
defparam n431_s.PADDSUB_IREG_RESET="RESET0";
defparam n431_s.PSEL_IREG_CE="CE0";
defparam n431_s.PSEL_IREG_CLK="BYPASS";
defparam n431_s.PSEL_IREG_RESET="RESET0";
  MULTALU27X18 n464_s (
    .DOUT({DOUT_13[47:32],n695_1,n696_1,n697_1,n698_1,n699_1,n700_1,n701_1,n702_1,n703_1,n704_1,n705_1,n706_1,n707_1,n708_1,n709_1,n710_1,n711_1,n712_1,n713_1,n714_1,n715_1,n716_1,n717_1,n718_1,n719_1,n720_1,n721_1,n722_1,n723_1,n724_1,n725_1,n726_1}),
    .CASO(CASO_13[47:0]),
    .SOA(SOA_9[26:0]),
    .A({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,frequencies_d[47:32]}),
    .SIA({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .B({GND,VCC,GND,VCC,GND,VCC,VCC,VCC,GND,VCC,VCC,GND,GND,GND,GND,VCC,VCC,GND}),
    .C({n727_6,n727_6,n727_6,n727_6,n727_6,n727_6,n727_6,n727_6,n727_6,n727_6,n727_6,n727_6,n727_6,n727_6,n727_6,n727_6,n727_6,n728_6,n729_6,n730_6,n731_6,n732_6,n733_6,n734_6,n735_6,n736_6,n737_6,n738_6,n739_6,n740_6,n741_6,n742_6,n743_6,n744_6,n745_6,n746_6,n747_6,n748_6,n749_6,n750_6,n751_6,n752_6,n753_6,n754_6,n755_6,n756_6,n757_6,n758_6}),
    .D({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .CASI({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .ACCSEL(GND),
    .PSEL(GND),
    .ASEL(GND),
    .PADDSUB(GND),
    .CSEL(GND),
    .CASISEL(GND),
    .ADDSUB({GND,GND}),
    .CLK({GND,clk_d}),
    .CE({sample_tick_d,VCC}),
    .RESET({GND,n232_6}) 
);
defparam n464_s.MULT_RESET_MODE="ASYNC";
defparam n464_s.ACCSEL_IREG_CLK="BYPASS";
defparam n464_s.ACCSEL_IREG_CE="CE0";
defparam n464_s.ACCSEL_IREG_RESET="RESET0";
defparam n464_s.ADDSUB0_IREG_CLK="BYPASS";
defparam n464_s.ADDSUB0_IREG_CE="CE0";
defparam n464_s.ADDSUB0_IREG_RESET="RESET0";
defparam n464_s.ADDSUB1_IREG_CLK="BYPASS";
defparam n464_s.ADDSUB1_IREG_CE="CE0";
defparam n464_s.ADDSUB1_IREG_RESET="RESET0";
defparam n464_s.FB_PREG_EN="FALSE";
defparam n464_s.ACCSEL_PREG_CLK="BYPASS";
defparam n464_s.ACCSEL_PREG_CE="CE0";
defparam n464_s.ACCSEL_PREG_RESET="RESET0";
defparam n464_s.ADDSUB0_PREG_CLK="BYPASS";
defparam n464_s.ADDSUB0_PREG_CE="CE0";
defparam n464_s.ADDSUB0_PREG_RESET="RESET0";
defparam n464_s.ADDSUB1_PREG_CLK="BYPASS";
defparam n464_s.ADDSUB1_PREG_CE="CE0";
defparam n464_s.ADDSUB1_PREG_RESET="RESET0";
defparam n464_s.OREG_CLK="BYPASS";
defparam n464_s.OREG_CE="CE0";
defparam n464_s.OREG_RESET="RESET0";
defparam n464_s.PRE_LOAD=48'h000000000000;
defparam n464_s.CASI_SEL=1'b0;
defparam n464_s.AREG_CLK="BYPASS";
defparam n464_s.AREG_CE="CE0";
defparam n464_s.AREG_RESET="RESET0";
defparam n464_s.BREG_CLK="BYPASS";
defparam n464_s.BREG_CE="CE0";
defparam n464_s.BREG_RESET="RESET0";
defparam n464_s.DREG_CLK="BYPASS";
defparam n464_s.DREG_CE="CE0";
defparam n464_s.DREG_RESET="RESET0";
defparam n464_s.PREG_CLK="CLK0";
defparam n464_s.PREG_CE="CE0";
defparam n464_s.PREG_RESET="RESET0";
defparam n464_s.SOA_PREG_EN="FALSE";
defparam n464_s.DYN_P_SEL="FALSE";
defparam n464_s.P_SEL=1'b0;
defparam n464_s.DYN_P_ADDSUB="FALSE";
defparam n464_s.P_ADDSUB=1'b0;
defparam n464_s.ACC_SEL=1'b0;
defparam n464_s.ADD_SUB_0=1'b0;
defparam n464_s.ADD_SUB_1=1'b0;
defparam n464_s.A_SEL=1'b0;
defparam n464_s.CASISEL_IREG_CE="CE0";
defparam n464_s.CASISEL_IREG_CLK="BYPASS";
defparam n464_s.CASISEL_IREG_RESET="RESET0";
defparam n464_s.CASISEL_PREG_CE="CE0";
defparam n464_s.CASISEL_PREG_CLK="BYPASS";
defparam n464_s.CASISEL_PREG_RESET="RESET0";
defparam n464_s.CSEL_IREG_CE="CE0";
defparam n464_s.CSEL_IREG_CLK="BYPASS";
defparam n464_s.CSEL_IREG_RESET="RESET0";
defparam n464_s.CSEL_PREG_CE="CE0";
defparam n464_s.CSEL_PREG_CLK="BYPASS";
defparam n464_s.CSEL_PREG_RESET="RESET0";
defparam n464_s.C_IREG_CE="CE1";
defparam n464_s.C_IREG_CLK="CLK0";
defparam n464_s.C_IREG_RESET="RESET0";
defparam n464_s.C_PREG_CE="CE0";
defparam n464_s.C_PREG_CLK="BYPASS";
defparam n464_s.C_PREG_RESET="RESET0";
defparam n464_s.C_SEL=1'b1;
defparam n464_s.DYN_ACC_SEL="FALSE";
defparam n464_s.DYN_ADD_SUB_0="FALSE";
defparam n464_s.DYN_ADD_SUB_1="FALSE";
defparam n464_s.DYN_A_SEL="FALSE";
defparam n464_s.DYN_CASI_SEL="FALSE";
defparam n464_s.DYN_C_SEL="FALSE";
defparam n464_s.MULT12X12_EN="FALSE";
defparam n464_s.PADDSUB_IREG_CE="CE0";
defparam n464_s.PADDSUB_IREG_CLK="BYPASS";
defparam n464_s.PADDSUB_IREG_RESET="RESET0";
defparam n464_s.PSEL_IREG_CE="CE0";
defparam n464_s.PSEL_IREG_CLK="BYPASS";
defparam n464_s.PSEL_IREG_RESET="RESET0";
  MULTALU27X18 n497_s (
    .DOUT({DOUT_14[47:32],n792_1,n793_1,n794_1,n795_1,n796_1,n797_1,n798_1,n799_1,n800_1,n801_1,n802_1,n803_1,n804_1,n805_1,n806_1,n807_1,n808_1,n809_1,n810_1,n811_1,n812_1,n813_1,n814_1,n815_1,n816_1,n817_1,n818_1,n819_1,n820_1,n821_1,n822_1,n823_1}),
    .CASO(CASO_14[47:0]),
    .SOA(SOA_10[26:0]),
    .A({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,frequencies_d[63:48]}),
    .SIA({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .B({GND,VCC,GND,VCC,GND,VCC,VCC,VCC,GND,VCC,VCC,GND,GND,GND,GND,VCC,VCC,GND}),
    .C({n824_6,n824_6,n824_6,n824_6,n824_6,n824_6,n824_6,n824_6,n824_6,n824_6,n824_6,n824_6,n824_6,n824_6,n824_6,n824_6,n824_6,n825_6,n826_6,n827_6,n828_6,n829_6,n830_6,n831_6,n832_6,n833_6,n834_6,n835_6,n836_6,n837_6,n838_6,n839_6,n840_6,n841_6,n842_6,n843_6,n844_6,n845_6,n846_6,n847_6,n848_6,n849_6,n850_6,n851_6,n852_6,n853_6,n854_6,n855_6}),
    .D({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .CASI({GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND,GND}),
    .ACCSEL(GND),
    .PSEL(GND),
    .ASEL(GND),
    .PADDSUB(GND),
    .CSEL(GND),
    .CASISEL(GND),
    .ADDSUB({GND,GND}),
    .CLK({GND,clk_d}),
    .CE({sample_tick_d,VCC}),
    .RESET({GND,n232_6}) 
);
defparam n497_s.MULT_RESET_MODE="ASYNC";
defparam n497_s.ACCSEL_IREG_CLK="BYPASS";
defparam n497_s.ACCSEL_IREG_CE="CE0";
defparam n497_s.ACCSEL_IREG_RESET="RESET0";
defparam n497_s.ADDSUB0_IREG_CLK="BYPASS";
defparam n497_s.ADDSUB0_IREG_CE="CE0";
defparam n497_s.ADDSUB0_IREG_RESET="RESET0";
defparam n497_s.ADDSUB1_IREG_CLK="BYPASS";
defparam n497_s.ADDSUB1_IREG_CE="CE0";
defparam n497_s.ADDSUB1_IREG_RESET="RESET0";
defparam n497_s.FB_PREG_EN="FALSE";
defparam n497_s.ACCSEL_PREG_CLK="BYPASS";
defparam n497_s.ACCSEL_PREG_CE="CE0";
defparam n497_s.ACCSEL_PREG_RESET="RESET0";
defparam n497_s.ADDSUB0_PREG_CLK="BYPASS";
defparam n497_s.ADDSUB0_PREG_CE="CE0";
defparam n497_s.ADDSUB0_PREG_RESET="RESET0";
defparam n497_s.ADDSUB1_PREG_CLK="BYPASS";
defparam n497_s.ADDSUB1_PREG_CE="CE0";
defparam n497_s.ADDSUB1_PREG_RESET="RESET0";
defparam n497_s.OREG_CLK="BYPASS";
defparam n497_s.OREG_CE="CE0";
defparam n497_s.OREG_RESET="RESET0";
defparam n497_s.PRE_LOAD=48'h000000000000;
defparam n497_s.CASI_SEL=1'b0;
defparam n497_s.AREG_CLK="BYPASS";
defparam n497_s.AREG_CE="CE0";
defparam n497_s.AREG_RESET="RESET0";
defparam n497_s.BREG_CLK="BYPASS";
defparam n497_s.BREG_CE="CE0";
defparam n497_s.BREG_RESET="RESET0";
defparam n497_s.DREG_CLK="BYPASS";
defparam n497_s.DREG_CE="CE0";
defparam n497_s.DREG_RESET="RESET0";
defparam n497_s.PREG_CLK="CLK0";
defparam n497_s.PREG_CE="CE0";
defparam n497_s.PREG_RESET="RESET0";
defparam n497_s.SOA_PREG_EN="FALSE";
defparam n497_s.DYN_P_SEL="FALSE";
defparam n497_s.P_SEL=1'b0;
defparam n497_s.DYN_P_ADDSUB="FALSE";
defparam n497_s.P_ADDSUB=1'b0;
defparam n497_s.ACC_SEL=1'b0;
defparam n497_s.ADD_SUB_0=1'b0;
defparam n497_s.ADD_SUB_1=1'b0;
defparam n497_s.A_SEL=1'b0;
defparam n497_s.CASISEL_IREG_CE="CE0";
defparam n497_s.CASISEL_IREG_CLK="BYPASS";
defparam n497_s.CASISEL_IREG_RESET="RESET0";
defparam n497_s.CASISEL_PREG_CE="CE0";
defparam n497_s.CASISEL_PREG_CLK="BYPASS";
defparam n497_s.CASISEL_PREG_RESET="RESET0";
defparam n497_s.CSEL_IREG_CE="CE0";
defparam n497_s.CSEL_IREG_CLK="BYPASS";
defparam n497_s.CSEL_IREG_RESET="RESET0";
defparam n497_s.CSEL_PREG_CE="CE0";
defparam n497_s.CSEL_PREG_CLK="BYPASS";
defparam n497_s.CSEL_PREG_RESET="RESET0";
defparam n497_s.C_IREG_CE="CE1";
defparam n497_s.C_IREG_CLK="CLK0";
defparam n497_s.C_IREG_RESET="RESET0";
defparam n497_s.C_PREG_CE="CE0";
defparam n497_s.C_PREG_CLK="BYPASS";
defparam n497_s.C_PREG_RESET="RESET0";
defparam n497_s.C_SEL=1'b1;
defparam n497_s.DYN_ACC_SEL="FALSE";
defparam n497_s.DYN_ADD_SUB_0="FALSE";
defparam n497_s.DYN_ADD_SUB_1="FALSE";
defparam n497_s.DYN_A_SEL="FALSE";
defparam n497_s.DYN_CASI_SEL="FALSE";
defparam n497_s.DYN_C_SEL="FALSE";
defparam n497_s.MULT12X12_EN="FALSE";
defparam n497_s.PADDSUB_IREG_CE="CE0";
defparam n497_s.PADDSUB_IREG_CLK="BYPASS";
defparam n497_s.PADDSUB_IREG_RESET="RESET0";
defparam n497_s.PSEL_IREG_CE="CE0";
defparam n497_s.PSEL_IREG_CLK="BYPASS";
defparam n497_s.PSEL_IREG_RESET="RESET0";
  ALU mix_l_0_s (
    .SUM(mix_l_0_2),
    .COUT(mix_l_0_3),
    .I0(\left_q[0] [14]),
    .I1(\left_q[1] [14]),
    .I3(VCC),
    .CIN(GND) 
);
defparam mix_l_0_s.ALU_MODE=0;
  ALU mix_l_1_s (
    .SUM(mix_l_1_2),
    .COUT(mix_l_1_3),
    .I0(\left_q[0] [15]),
    .I1(\left_q[1] [15]),
    .I3(VCC),
    .CIN(mix_l_0_3) 
);
defparam mix_l_1_s.ALU_MODE=0;
  ALU mix_l_2_s (
    .SUM(mix_l_2_2),
    .COUT(mix_l_2_3),
    .I0(\left_q[0] [16]),
    .I1(\left_q[1] [16]),
    .I3(VCC),
    .CIN(mix_l_1_3) 
);
defparam mix_l_2_s.ALU_MODE=0;
  ALU mix_l_3_s (
    .SUM(mix_l_3_2),
    .COUT(mix_l_3_3),
    .I0(\left_q[0] [17]),
    .I1(\left_q[1] [17]),
    .I3(VCC),
    .CIN(mix_l_2_3) 
);
defparam mix_l_3_s.ALU_MODE=0;
  ALU mix_l_4_s (
    .SUM(mix_l_4_2),
    .COUT(mix_l_4_3),
    .I0(\left_q[0] [18]),
    .I1(\left_q[1] [18]),
    .I3(VCC),
    .CIN(mix_l_3_3) 
);
defparam mix_l_4_s.ALU_MODE=0;
  ALU mix_l_5_s (
    .SUM(mix_l_5_2),
    .COUT(mix_l_5_3),
    .I0(\left_q[0] [19]),
    .I1(\left_q[1] [19]),
    .I3(VCC),
    .CIN(mix_l_4_3) 
);
defparam mix_l_5_s.ALU_MODE=0;
  ALU mix_l_6_s (
    .SUM(mix_l_6_2),
    .COUT(mix_l_6_3),
    .I0(\left_q[0] [20]),
    .I1(\left_q[1] [20]),
    .I3(VCC),
    .CIN(mix_l_5_3) 
);
defparam mix_l_6_s.ALU_MODE=0;
  ALU mix_l_7_s (
    .SUM(mix_l_7_2),
    .COUT(mix_l_7_3),
    .I0(\left_q[0] [21]),
    .I1(\left_q[1] [21]),
    .I3(VCC),
    .CIN(mix_l_6_3) 
);
defparam mix_l_7_s.ALU_MODE=0;
  ALU mix_l_8_s (
    .SUM(mix_l_8_2),
    .COUT(mix_l_8_3),
    .I0(\left_q[0] [22]),
    .I1(\left_q[1] [22]),
    .I3(VCC),
    .CIN(mix_l_7_3) 
);
defparam mix_l_8_s.ALU_MODE=0;
  ALU mix_l_9_s (
    .SUM(mix_l_9_2),
    .COUT(mix_l_9_3),
    .I0(\left_q[0] [23]),
    .I1(\left_q[1] [23]),
    .I3(VCC),
    .CIN(mix_l_8_3) 
);
defparam mix_l_9_s.ALU_MODE=0;
  ALU mix_l_10_s (
    .SUM(mix_l_10_2),
    .COUT(mix_l_10_3),
    .I0(\left_q[0] [24]),
    .I1(\left_q[1] [24]),
    .I3(VCC),
    .CIN(mix_l_9_3) 
);
defparam mix_l_10_s.ALU_MODE=0;
  ALU mix_l_11_s (
    .SUM(mix_l_11_2),
    .COUT(mix_l_11_3),
    .I0(\left_q[0] [25]),
    .I1(\left_q[1] [25]),
    .I3(VCC),
    .CIN(mix_l_10_3) 
);
defparam mix_l_11_s.ALU_MODE=0;
  ALU mix_l_12_s (
    .SUM(mix_l_12_2),
    .COUT(mix_l_12_3),
    .I0(\left_q[0] [26]),
    .I1(\left_q[1] [26]),
    .I3(VCC),
    .CIN(mix_l_11_3) 
);
defparam mix_l_12_s.ALU_MODE=0;
  ALU mix_l_13_s (
    .SUM(mix_l_13_2),
    .COUT(mix_l_13_3),
    .I0(\left_q[0] [27]),
    .I1(\left_q[1] [27]),
    .I3(VCC),
    .CIN(mix_l_12_3) 
);
defparam mix_l_13_s.ALU_MODE=0;
  ALU mix_l_14_s (
    .SUM(mix_l_14_2),
    .COUT(mix_l_14_3),
    .I0(\left_q[0] [28]),
    .I1(\left_q[1] [28]),
    .I3(VCC),
    .CIN(mix_l_13_3) 
);
defparam mix_l_14_s.ALU_MODE=0;
  ALU mix_l_15_s (
    .SUM(mix_l_15_2),
    .COUT(mix_l_15_3),
    .I0(\left_q[0] [29]),
    .I1(\left_q[1] [29]),
    .I3(VCC),
    .CIN(mix_l_14_3) 
);
defparam mix_l_15_s.ALU_MODE=0;
  ALU mix_l_16_s (
    .SUM(mix_l_16_2),
    .COUT(mix_l_16_3),
    .I0(\left_q[0] [30]),
    .I1(\left_q[1] [30]),
    .I3(VCC),
    .CIN(mix_l_15_3) 
);
defparam mix_l_16_s.ALU_MODE=0;
  ALU mix_l_17_s (
    .SUM(mix_l_17_2),
    .COUT(mix_l_17_3),
    .I0(\left_q[0] [31]),
    .I1(\left_q[1] [31]),
    .I3(VCC),
    .CIN(mix_l_16_3) 
);
defparam mix_l_17_s.ALU_MODE=0;
  ALU mix_l_18_s (
    .SUM(mix_l_18_2),
    .COUT(mix_l_18_3),
    .I0(\left_q[0] [31]),
    .I1(\left_q[1] [31]),
    .I3(VCC),
    .CIN(mix_l_17_3) 
);
defparam mix_l_18_s.ALU_MODE=0;
  ALU mix_l_19_s (
    .SUM(mix_l_19_2),
    .COUT(mix_l_19_3),
    .I0(\left_q[0] [31]),
    .I1(\left_q[1] [31]),
    .I3(VCC),
    .CIN(mix_l_18_3) 
);
defparam mix_l_19_s.ALU_MODE=0;
  ALU mix_l_33_s (
    .SUM(mix_l_33_2),
    .COUT(mix_l_33_0_COUT),
    .I0(\left_q[0] [31]),
    .I1(\left_q[1] [31]),
    .I3(VCC),
    .CIN(mix_l_19_3) 
);
defparam mix_l_33_s.ALU_MODE=0;
  ALU mix_l_0_s0 (
    .SUM(mix_l_0_4),
    .COUT(mix_l_0_5),
    .I0(\left_q[2] [14]),
    .I1(\left_q[3] [14]),
    .I3(VCC),
    .CIN(GND) 
);
defparam mix_l_0_s0.ALU_MODE=0;
  ALU mix_l_1_s0 (
    .SUM(mix_l_1_4),
    .COUT(mix_l_1_5),
    .I0(\left_q[2] [15]),
    .I1(\left_q[3] [15]),
    .I3(VCC),
    .CIN(mix_l_0_5) 
);
defparam mix_l_1_s0.ALU_MODE=0;
  ALU mix_l_2_s0 (
    .SUM(mix_l_2_4),
    .COUT(mix_l_2_5),
    .I0(\left_q[2] [16]),
    .I1(\left_q[3] [16]),
    .I3(VCC),
    .CIN(mix_l_1_5) 
);
defparam mix_l_2_s0.ALU_MODE=0;
  ALU mix_l_3_s0 (
    .SUM(mix_l_3_4),
    .COUT(mix_l_3_5),
    .I0(\left_q[2] [17]),
    .I1(\left_q[3] [17]),
    .I3(VCC),
    .CIN(mix_l_2_5) 
);
defparam mix_l_3_s0.ALU_MODE=0;
  ALU mix_l_4_s0 (
    .SUM(mix_l_4_4),
    .COUT(mix_l_4_5),
    .I0(\left_q[2] [18]),
    .I1(\left_q[3] [18]),
    .I3(VCC),
    .CIN(mix_l_3_5) 
);
defparam mix_l_4_s0.ALU_MODE=0;
  ALU mix_l_5_s0 (
    .SUM(mix_l_5_4),
    .COUT(mix_l_5_5),
    .I0(\left_q[2] [19]),
    .I1(\left_q[3] [19]),
    .I3(VCC),
    .CIN(mix_l_4_5) 
);
defparam mix_l_5_s0.ALU_MODE=0;
  ALU mix_l_6_s0 (
    .SUM(mix_l_6_4),
    .COUT(mix_l_6_5),
    .I0(\left_q[2] [20]),
    .I1(\left_q[3] [20]),
    .I3(VCC),
    .CIN(mix_l_5_5) 
);
defparam mix_l_6_s0.ALU_MODE=0;
  ALU mix_l_7_s0 (
    .SUM(mix_l_7_4),
    .COUT(mix_l_7_5),
    .I0(\left_q[2] [21]),
    .I1(\left_q[3] [21]),
    .I3(VCC),
    .CIN(mix_l_6_5) 
);
defparam mix_l_7_s0.ALU_MODE=0;
  ALU mix_l_8_s0 (
    .SUM(mix_l_8_4),
    .COUT(mix_l_8_5),
    .I0(\left_q[2] [22]),
    .I1(\left_q[3] [22]),
    .I3(VCC),
    .CIN(mix_l_7_5) 
);
defparam mix_l_8_s0.ALU_MODE=0;
  ALU mix_l_9_s0 (
    .SUM(mix_l_9_4),
    .COUT(mix_l_9_5),
    .I0(\left_q[2] [23]),
    .I1(\left_q[3] [23]),
    .I3(VCC),
    .CIN(mix_l_8_5) 
);
defparam mix_l_9_s0.ALU_MODE=0;
  ALU mix_l_10_s0 (
    .SUM(mix_l_10_4),
    .COUT(mix_l_10_5),
    .I0(\left_q[2] [24]),
    .I1(\left_q[3] [24]),
    .I3(VCC),
    .CIN(mix_l_9_5) 
);
defparam mix_l_10_s0.ALU_MODE=0;
  ALU mix_l_11_s0 (
    .SUM(mix_l_11_4),
    .COUT(mix_l_11_5),
    .I0(\left_q[2] [25]),
    .I1(\left_q[3] [25]),
    .I3(VCC),
    .CIN(mix_l_10_5) 
);
defparam mix_l_11_s0.ALU_MODE=0;
  ALU mix_l_12_s0 (
    .SUM(mix_l_12_4),
    .COUT(mix_l_12_5),
    .I0(\left_q[2] [26]),
    .I1(\left_q[3] [26]),
    .I3(VCC),
    .CIN(mix_l_11_5) 
);
defparam mix_l_12_s0.ALU_MODE=0;
  ALU mix_l_13_s0 (
    .SUM(mix_l_13_4),
    .COUT(mix_l_13_5),
    .I0(\left_q[2] [27]),
    .I1(\left_q[3] [27]),
    .I3(VCC),
    .CIN(mix_l_12_5) 
);
defparam mix_l_13_s0.ALU_MODE=0;
  ALU mix_l_14_s0 (
    .SUM(mix_l_14_4),
    .COUT(mix_l_14_5),
    .I0(\left_q[2] [28]),
    .I1(\left_q[3] [28]),
    .I3(VCC),
    .CIN(mix_l_13_5) 
);
defparam mix_l_14_s0.ALU_MODE=0;
  ALU mix_l_15_s0 (
    .SUM(mix_l_15_4),
    .COUT(mix_l_15_5),
    .I0(\left_q[2] [29]),
    .I1(\left_q[3] [29]),
    .I3(VCC),
    .CIN(mix_l_14_5) 
);
defparam mix_l_15_s0.ALU_MODE=0;
  ALU mix_l_16_s0 (
    .SUM(mix_l_16_4),
    .COUT(mix_l_16_5),
    .I0(\left_q[2] [30]),
    .I1(\left_q[3] [30]),
    .I3(VCC),
    .CIN(mix_l_15_5) 
);
defparam mix_l_16_s0.ALU_MODE=0;
  ALU mix_l_17_s0 (
    .SUM(mix_l_17_4),
    .COUT(mix_l_17_5),
    .I0(\left_q[2] [31]),
    .I1(\left_q[3] [31]),
    .I3(VCC),
    .CIN(mix_l_16_5) 
);
defparam mix_l_17_s0.ALU_MODE=0;
  ALU mix_l_18_s0 (
    .SUM(mix_l_18_4),
    .COUT(mix_l_18_5),
    .I0(\left_q[2] [31]),
    .I1(\left_q[3] [31]),
    .I3(VCC),
    .CIN(mix_l_17_5) 
);
defparam mix_l_18_s0.ALU_MODE=0;
  ALU mix_l_19_s0 (
    .SUM(mix_l_19_4),
    .COUT(mix_l_19_5),
    .I0(\left_q[2] [31]),
    .I1(\left_q[3] [31]),
    .I3(VCC),
    .CIN(mix_l_18_5) 
);
defparam mix_l_19_s0.ALU_MODE=0;
  ALU mix_l_33_s0 (
    .SUM(mix_l_33_4),
    .COUT(mix_l_33_1_COUT),
    .I0(\left_q[2] [31]),
    .I1(\left_q[3] [31]),
    .I3(VCC),
    .CIN(mix_l_19_5) 
);
defparam mix_l_33_s0.ALU_MODE=0;
  ALU mix_l_0_s1 (
    .SUM(mix_l[0]),
    .COUT(mix_l_0_7),
    .I0(mix_l_0_2),
    .I1(mix_l_0_4),
    .I3(VCC),
    .CIN(GND) 
);
defparam mix_l_0_s1.ALU_MODE=0;
  ALU mix_l_1_s1 (
    .SUM(mix_l[1]),
    .COUT(mix_l_1_7),
    .I0(mix_l_1_2),
    .I1(mix_l_1_4),
    .I3(VCC),
    .CIN(mix_l_0_7) 
);
defparam mix_l_1_s1.ALU_MODE=0;
  ALU mix_l_2_s1 (
    .SUM(mix_l[2]),
    .COUT(mix_l_2_7),
    .I0(mix_l_2_2),
    .I1(mix_l_2_4),
    .I3(VCC),
    .CIN(mix_l_1_7) 
);
defparam mix_l_2_s1.ALU_MODE=0;
  ALU mix_l_3_s1 (
    .SUM(mix_l[3]),
    .COUT(mix_l_3_7),
    .I0(mix_l_3_2),
    .I1(mix_l_3_4),
    .I3(VCC),
    .CIN(mix_l_2_7) 
);
defparam mix_l_3_s1.ALU_MODE=0;
  ALU mix_l_4_s1 (
    .SUM(mix_l[4]),
    .COUT(mix_l_4_7),
    .I0(mix_l_4_2),
    .I1(mix_l_4_4),
    .I3(VCC),
    .CIN(mix_l_3_7) 
);
defparam mix_l_4_s1.ALU_MODE=0;
  ALU mix_l_5_s1 (
    .SUM(mix_l[5]),
    .COUT(mix_l_5_7),
    .I0(mix_l_5_2),
    .I1(mix_l_5_4),
    .I3(VCC),
    .CIN(mix_l_4_7) 
);
defparam mix_l_5_s1.ALU_MODE=0;
  ALU mix_l_6_s1 (
    .SUM(mix_l[6]),
    .COUT(mix_l_6_7),
    .I0(mix_l_6_2),
    .I1(mix_l_6_4),
    .I3(VCC),
    .CIN(mix_l_5_7) 
);
defparam mix_l_6_s1.ALU_MODE=0;
  ALU mix_l_7_s1 (
    .SUM(mix_l[7]),
    .COUT(mix_l_7_7),
    .I0(mix_l_7_2),
    .I1(mix_l_7_4),
    .I3(VCC),
    .CIN(mix_l_6_7) 
);
defparam mix_l_7_s1.ALU_MODE=0;
  ALU mix_l_8_s1 (
    .SUM(mix_l[8]),
    .COUT(mix_l_8_7),
    .I0(mix_l_8_2),
    .I1(mix_l_8_4),
    .I3(VCC),
    .CIN(mix_l_7_7) 
);
defparam mix_l_8_s1.ALU_MODE=0;
  ALU mix_l_9_s1 (
    .SUM(mix_l[9]),
    .COUT(mix_l_9_7),
    .I0(mix_l_9_2),
    .I1(mix_l_9_4),
    .I3(VCC),
    .CIN(mix_l_8_7) 
);
defparam mix_l_9_s1.ALU_MODE=0;
  ALU mix_l_10_s1 (
    .SUM(mix_l[10]),
    .COUT(mix_l_10_7),
    .I0(mix_l_10_2),
    .I1(mix_l_10_4),
    .I3(VCC),
    .CIN(mix_l_9_7) 
);
defparam mix_l_10_s1.ALU_MODE=0;
  ALU mix_l_11_s1 (
    .SUM(mix_l[11]),
    .COUT(mix_l_11_7),
    .I0(mix_l_11_2),
    .I1(mix_l_11_4),
    .I3(VCC),
    .CIN(mix_l_10_7) 
);
defparam mix_l_11_s1.ALU_MODE=0;
  ALU mix_l_12_s1 (
    .SUM(mix_l[12]),
    .COUT(mix_l_12_7),
    .I0(mix_l_12_2),
    .I1(mix_l_12_4),
    .I3(VCC),
    .CIN(mix_l_11_7) 
);
defparam mix_l_12_s1.ALU_MODE=0;
  ALU mix_l_13_s1 (
    .SUM(mix_l[13]),
    .COUT(mix_l_13_7),
    .I0(mix_l_13_2),
    .I1(mix_l_13_4),
    .I3(VCC),
    .CIN(mix_l_12_7) 
);
defparam mix_l_13_s1.ALU_MODE=0;
  ALU mix_l_14_s1 (
    .SUM(mix_l[14]),
    .COUT(mix_l_14_7),
    .I0(mix_l_14_2),
    .I1(mix_l_14_4),
    .I3(VCC),
    .CIN(mix_l_13_7) 
);
defparam mix_l_14_s1.ALU_MODE=0;
  ALU mix_l_15_s1 (
    .SUM(mix_l[15]),
    .COUT(mix_l_15_7),
    .I0(mix_l_15_2),
    .I1(mix_l_15_4),
    .I3(VCC),
    .CIN(mix_l_14_7) 
);
defparam mix_l_15_s1.ALU_MODE=0;
  ALU mix_l_16_s1 (
    .SUM(mix_l[16]),
    .COUT(mix_l_16_7),
    .I0(mix_l_16_2),
    .I1(mix_l_16_4),
    .I3(VCC),
    .CIN(mix_l_15_7) 
);
defparam mix_l_16_s1.ALU_MODE=0;
  ALU mix_l_17_s1 (
    .SUM(mix_l[17]),
    .COUT(mix_l_17_7),
    .I0(mix_l_17_2),
    .I1(mix_l_17_4),
    .I3(VCC),
    .CIN(mix_l_16_7) 
);
defparam mix_l_17_s1.ALU_MODE=0;
  ALU mix_l_18_s1 (
    .SUM(mix_l[18]),
    .COUT(mix_l_18_7),
    .I0(mix_l_18_2),
    .I1(mix_l_18_4),
    .I3(VCC),
    .CIN(mix_l_17_7) 
);
defparam mix_l_18_s1.ALU_MODE=0;
  ALU mix_l_19_s1 (
    .SUM(mix_l[19]),
    .COUT(mix_l_19_7),
    .I0(mix_l_19_2),
    .I1(mix_l_19_4),
    .I3(VCC),
    .CIN(mix_l_18_7) 
);
defparam mix_l_19_s1.ALU_MODE=0;
  ALU mix_l_33_s1 (
    .SUM(mix_l[33]),
    .COUT(mix_l_33_2_COUT),
    .I0(mix_l_33_2),
    .I1(mix_l_33_4),
    .I3(VCC),
    .CIN(mix_l_19_7) 
);
defparam mix_l_33_s1.ALU_MODE=0;
  ALU mix_r_0_s (
    .SUM(mix_r_0_2),
    .COUT(mix_r_0_3),
    .I0(\right_q[0] [14]),
    .I1(\right_q[1] [14]),
    .I3(VCC),
    .CIN(GND) 
);
defparam mix_r_0_s.ALU_MODE=0;
  ALU mix_r_1_s (
    .SUM(mix_r_1_2),
    .COUT(mix_r_1_3),
    .I0(\right_q[0] [15]),
    .I1(\right_q[1] [15]),
    .I3(VCC),
    .CIN(mix_r_0_3) 
);
defparam mix_r_1_s.ALU_MODE=0;
  ALU mix_r_2_s (
    .SUM(mix_r_2_2),
    .COUT(mix_r_2_3),
    .I0(\right_q[0] [16]),
    .I1(\right_q[1] [16]),
    .I3(VCC),
    .CIN(mix_r_1_3) 
);
defparam mix_r_2_s.ALU_MODE=0;
  ALU mix_r_3_s (
    .SUM(mix_r_3_2),
    .COUT(mix_r_3_3),
    .I0(\right_q[0] [17]),
    .I1(\right_q[1] [17]),
    .I3(VCC),
    .CIN(mix_r_2_3) 
);
defparam mix_r_3_s.ALU_MODE=0;
  ALU mix_r_4_s (
    .SUM(mix_r_4_2),
    .COUT(mix_r_4_3),
    .I0(\right_q[0] [18]),
    .I1(\right_q[1] [18]),
    .I3(VCC),
    .CIN(mix_r_3_3) 
);
defparam mix_r_4_s.ALU_MODE=0;
  ALU mix_r_5_s (
    .SUM(mix_r_5_2),
    .COUT(mix_r_5_3),
    .I0(\right_q[0] [19]),
    .I1(\right_q[1] [19]),
    .I3(VCC),
    .CIN(mix_r_4_3) 
);
defparam mix_r_5_s.ALU_MODE=0;
  ALU mix_r_6_s (
    .SUM(mix_r_6_2),
    .COUT(mix_r_6_3),
    .I0(\right_q[0] [20]),
    .I1(\right_q[1] [20]),
    .I3(VCC),
    .CIN(mix_r_5_3) 
);
defparam mix_r_6_s.ALU_MODE=0;
  ALU mix_r_7_s (
    .SUM(mix_r_7_2),
    .COUT(mix_r_7_3),
    .I0(\right_q[0] [21]),
    .I1(\right_q[1] [21]),
    .I3(VCC),
    .CIN(mix_r_6_3) 
);
defparam mix_r_7_s.ALU_MODE=0;
  ALU mix_r_8_s (
    .SUM(mix_r_8_2),
    .COUT(mix_r_8_3),
    .I0(\right_q[0] [22]),
    .I1(\right_q[1] [22]),
    .I3(VCC),
    .CIN(mix_r_7_3) 
);
defparam mix_r_8_s.ALU_MODE=0;
  ALU mix_r_9_s (
    .SUM(mix_r_9_2),
    .COUT(mix_r_9_3),
    .I0(\right_q[0] [23]),
    .I1(\right_q[1] [23]),
    .I3(VCC),
    .CIN(mix_r_8_3) 
);
defparam mix_r_9_s.ALU_MODE=0;
  ALU mix_r_10_s (
    .SUM(mix_r_10_2),
    .COUT(mix_r_10_3),
    .I0(\right_q[0] [24]),
    .I1(\right_q[1] [24]),
    .I3(VCC),
    .CIN(mix_r_9_3) 
);
defparam mix_r_10_s.ALU_MODE=0;
  ALU mix_r_11_s (
    .SUM(mix_r_11_2),
    .COUT(mix_r_11_3),
    .I0(\right_q[0] [25]),
    .I1(\right_q[1] [25]),
    .I3(VCC),
    .CIN(mix_r_10_3) 
);
defparam mix_r_11_s.ALU_MODE=0;
  ALU mix_r_12_s (
    .SUM(mix_r_12_2),
    .COUT(mix_r_12_3),
    .I0(\right_q[0] [26]),
    .I1(\right_q[1] [26]),
    .I3(VCC),
    .CIN(mix_r_11_3) 
);
defparam mix_r_12_s.ALU_MODE=0;
  ALU mix_r_13_s (
    .SUM(mix_r_13_2),
    .COUT(mix_r_13_3),
    .I0(\right_q[0] [27]),
    .I1(\right_q[1] [27]),
    .I3(VCC),
    .CIN(mix_r_12_3) 
);
defparam mix_r_13_s.ALU_MODE=0;
  ALU mix_r_14_s (
    .SUM(mix_r_14_2),
    .COUT(mix_r_14_3),
    .I0(\right_q[0] [28]),
    .I1(\right_q[1] [28]),
    .I3(VCC),
    .CIN(mix_r_13_3) 
);
defparam mix_r_14_s.ALU_MODE=0;
  ALU mix_r_15_s (
    .SUM(mix_r_15_2),
    .COUT(mix_r_15_3),
    .I0(\right_q[0] [29]),
    .I1(\right_q[1] [29]),
    .I3(VCC),
    .CIN(mix_r_14_3) 
);
defparam mix_r_15_s.ALU_MODE=0;
  ALU mix_r_16_s (
    .SUM(mix_r_16_2),
    .COUT(mix_r_16_3),
    .I0(\right_q[0] [30]),
    .I1(\right_q[1] [30]),
    .I3(VCC),
    .CIN(mix_r_15_3) 
);
defparam mix_r_16_s.ALU_MODE=0;
  ALU mix_r_17_s (
    .SUM(mix_r_17_2),
    .COUT(mix_r_17_3),
    .I0(\right_q[0] [31]),
    .I1(\right_q[1] [31]),
    .I3(VCC),
    .CIN(mix_r_16_3) 
);
defparam mix_r_17_s.ALU_MODE=0;
  ALU mix_r_18_s (
    .SUM(mix_r_18_2),
    .COUT(mix_r_18_3),
    .I0(\right_q[0] [31]),
    .I1(\right_q[1] [31]),
    .I3(VCC),
    .CIN(mix_r_17_3) 
);
defparam mix_r_18_s.ALU_MODE=0;
  ALU mix_r_19_s (
    .SUM(mix_r_19_2),
    .COUT(mix_r_19_3),
    .I0(\right_q[0] [31]),
    .I1(\right_q[1] [31]),
    .I3(VCC),
    .CIN(mix_r_18_3) 
);
defparam mix_r_19_s.ALU_MODE=0;
  ALU mix_r_33_s (
    .SUM(mix_r_33_2),
    .COUT(mix_r_33_0_COUT),
    .I0(\right_q[0] [31]),
    .I1(\right_q[1] [31]),
    .I3(VCC),
    .CIN(mix_r_19_3) 
);
defparam mix_r_33_s.ALU_MODE=0;
  ALU mix_r_0_s0 (
    .SUM(mix_r_0_4),
    .COUT(mix_r_0_5),
    .I0(\right_q[2] [14]),
    .I1(\right_q[3] [14]),
    .I3(VCC),
    .CIN(GND) 
);
defparam mix_r_0_s0.ALU_MODE=0;
  ALU mix_r_1_s0 (
    .SUM(mix_r_1_4),
    .COUT(mix_r_1_5),
    .I0(\right_q[2] [15]),
    .I1(\right_q[3] [15]),
    .I3(VCC),
    .CIN(mix_r_0_5) 
);
defparam mix_r_1_s0.ALU_MODE=0;
  ALU mix_r_2_s0 (
    .SUM(mix_r_2_4),
    .COUT(mix_r_2_5),
    .I0(\right_q[2] [16]),
    .I1(\right_q[3] [16]),
    .I3(VCC),
    .CIN(mix_r_1_5) 
);
defparam mix_r_2_s0.ALU_MODE=0;
  ALU mix_r_3_s0 (
    .SUM(mix_r_3_4),
    .COUT(mix_r_3_5),
    .I0(\right_q[2] [17]),
    .I1(\right_q[3] [17]),
    .I3(VCC),
    .CIN(mix_r_2_5) 
);
defparam mix_r_3_s0.ALU_MODE=0;
  ALU mix_r_4_s0 (
    .SUM(mix_r_4_4),
    .COUT(mix_r_4_5),
    .I0(\right_q[2] [18]),
    .I1(\right_q[3] [18]),
    .I3(VCC),
    .CIN(mix_r_3_5) 
);
defparam mix_r_4_s0.ALU_MODE=0;
  ALU mix_r_5_s0 (
    .SUM(mix_r_5_4),
    .COUT(mix_r_5_5),
    .I0(\right_q[2] [19]),
    .I1(\right_q[3] [19]),
    .I3(VCC),
    .CIN(mix_r_4_5) 
);
defparam mix_r_5_s0.ALU_MODE=0;
  ALU mix_r_6_s0 (
    .SUM(mix_r_6_4),
    .COUT(mix_r_6_5),
    .I0(\right_q[2] [20]),
    .I1(\right_q[3] [20]),
    .I3(VCC),
    .CIN(mix_r_5_5) 
);
defparam mix_r_6_s0.ALU_MODE=0;
  ALU mix_r_7_s0 (
    .SUM(mix_r_7_4),
    .COUT(mix_r_7_5),
    .I0(\right_q[2] [21]),
    .I1(\right_q[3] [21]),
    .I3(VCC),
    .CIN(mix_r_6_5) 
);
defparam mix_r_7_s0.ALU_MODE=0;
  ALU mix_r_8_s0 (
    .SUM(mix_r_8_4),
    .COUT(mix_r_8_5),
    .I0(\right_q[2] [22]),
    .I1(\right_q[3] [22]),
    .I3(VCC),
    .CIN(mix_r_7_5) 
);
defparam mix_r_8_s0.ALU_MODE=0;
  ALU mix_r_9_s0 (
    .SUM(mix_r_9_4),
    .COUT(mix_r_9_5),
    .I0(\right_q[2] [23]),
    .I1(\right_q[3] [23]),
    .I3(VCC),
    .CIN(mix_r_8_5) 
);
defparam mix_r_9_s0.ALU_MODE=0;
  ALU mix_r_10_s0 (
    .SUM(mix_r_10_4),
    .COUT(mix_r_10_5),
    .I0(\right_q[2] [24]),
    .I1(\right_q[3] [24]),
    .I3(VCC),
    .CIN(mix_r_9_5) 
);
defparam mix_r_10_s0.ALU_MODE=0;
  ALU mix_r_11_s0 (
    .SUM(mix_r_11_4),
    .COUT(mix_r_11_5),
    .I0(\right_q[2] [25]),
    .I1(\right_q[3] [25]),
    .I3(VCC),
    .CIN(mix_r_10_5) 
);
defparam mix_r_11_s0.ALU_MODE=0;
  ALU mix_r_12_s0 (
    .SUM(mix_r_12_4),
    .COUT(mix_r_12_5),
    .I0(\right_q[2] [26]),
    .I1(\right_q[3] [26]),
    .I3(VCC),
    .CIN(mix_r_11_5) 
);
defparam mix_r_12_s0.ALU_MODE=0;
  ALU mix_r_13_s0 (
    .SUM(mix_r_13_4),
    .COUT(mix_r_13_5),
    .I0(\right_q[2] [27]),
    .I1(\right_q[3] [27]),
    .I3(VCC),
    .CIN(mix_r_12_5) 
);
defparam mix_r_13_s0.ALU_MODE=0;
  ALU mix_r_14_s0 (
    .SUM(mix_r_14_4),
    .COUT(mix_r_14_5),
    .I0(\right_q[2] [28]),
    .I1(\right_q[3] [28]),
    .I3(VCC),
    .CIN(mix_r_13_5) 
);
defparam mix_r_14_s0.ALU_MODE=0;
  ALU mix_r_15_s0 (
    .SUM(mix_r_15_4),
    .COUT(mix_r_15_5),
    .I0(\right_q[2] [29]),
    .I1(\right_q[3] [29]),
    .I3(VCC),
    .CIN(mix_r_14_5) 
);
defparam mix_r_15_s0.ALU_MODE=0;
  ALU mix_r_16_s0 (
    .SUM(mix_r_16_4),
    .COUT(mix_r_16_5),
    .I0(\right_q[2] [30]),
    .I1(\right_q[3] [30]),
    .I3(VCC),
    .CIN(mix_r_15_5) 
);
defparam mix_r_16_s0.ALU_MODE=0;
  ALU mix_r_17_s0 (
    .SUM(mix_r_17_4),
    .COUT(mix_r_17_5),
    .I0(\right_q[2] [31]),
    .I1(\right_q[3] [31]),
    .I3(VCC),
    .CIN(mix_r_16_5) 
);
defparam mix_r_17_s0.ALU_MODE=0;
  ALU mix_r_18_s0 (
    .SUM(mix_r_18_4),
    .COUT(mix_r_18_5),
    .I0(\right_q[2] [31]),
    .I1(\right_q[3] [31]),
    .I3(VCC),
    .CIN(mix_r_17_5) 
);
defparam mix_r_18_s0.ALU_MODE=0;
  ALU mix_r_19_s0 (
    .SUM(mix_r_19_4),
    .COUT(mix_r_19_5),
    .I0(\right_q[2] [31]),
    .I1(\right_q[3] [31]),
    .I3(VCC),
    .CIN(mix_r_18_5) 
);
defparam mix_r_19_s0.ALU_MODE=0;
  ALU mix_r_33_s0 (
    .SUM(mix_r_33_4),
    .COUT(mix_r_33_1_COUT),
    .I0(\right_q[2] [31]),
    .I1(\right_q[3] [31]),
    .I3(VCC),
    .CIN(mix_r_19_5) 
);
defparam mix_r_33_s0.ALU_MODE=0;
  ALU mix_r_0_s1 (
    .SUM(mix_r[0]),
    .COUT(mix_r_0_7),
    .I0(mix_r_0_2),
    .I1(mix_r_0_4),
    .I3(VCC),
    .CIN(GND) 
);
defparam mix_r_0_s1.ALU_MODE=0;
  ALU mix_r_1_s1 (
    .SUM(mix_r[1]),
    .COUT(mix_r_1_7),
    .I0(mix_r_1_2),
    .I1(mix_r_1_4),
    .I3(VCC),
    .CIN(mix_r_0_7) 
);
defparam mix_r_1_s1.ALU_MODE=0;
  ALU mix_r_2_s1 (
    .SUM(mix_r[2]),
    .COUT(mix_r_2_7),
    .I0(mix_r_2_2),
    .I1(mix_r_2_4),
    .I3(VCC),
    .CIN(mix_r_1_7) 
);
defparam mix_r_2_s1.ALU_MODE=0;
  ALU mix_r_3_s1 (
    .SUM(mix_r[3]),
    .COUT(mix_r_3_7),
    .I0(mix_r_3_2),
    .I1(mix_r_3_4),
    .I3(VCC),
    .CIN(mix_r_2_7) 
);
defparam mix_r_3_s1.ALU_MODE=0;
  ALU mix_r_4_s1 (
    .SUM(mix_r[4]),
    .COUT(mix_r_4_7),
    .I0(mix_r_4_2),
    .I1(mix_r_4_4),
    .I3(VCC),
    .CIN(mix_r_3_7) 
);
defparam mix_r_4_s1.ALU_MODE=0;
  ALU mix_r_5_s1 (
    .SUM(mix_r[5]),
    .COUT(mix_r_5_7),
    .I0(mix_r_5_2),
    .I1(mix_r_5_4),
    .I3(VCC),
    .CIN(mix_r_4_7) 
);
defparam mix_r_5_s1.ALU_MODE=0;
  ALU mix_r_6_s1 (
    .SUM(mix_r[6]),
    .COUT(mix_r_6_7),
    .I0(mix_r_6_2),
    .I1(mix_r_6_4),
    .I3(VCC),
    .CIN(mix_r_5_7) 
);
defparam mix_r_6_s1.ALU_MODE=0;
  ALU mix_r_7_s1 (
    .SUM(mix_r[7]),
    .COUT(mix_r_7_7),
    .I0(mix_r_7_2),
    .I1(mix_r_7_4),
    .I3(VCC),
    .CIN(mix_r_6_7) 
);
defparam mix_r_7_s1.ALU_MODE=0;
  ALU mix_r_8_s1 (
    .SUM(mix_r[8]),
    .COUT(mix_r_8_7),
    .I0(mix_r_8_2),
    .I1(mix_r_8_4),
    .I3(VCC),
    .CIN(mix_r_7_7) 
);
defparam mix_r_8_s1.ALU_MODE=0;
  ALU mix_r_9_s1 (
    .SUM(mix_r[9]),
    .COUT(mix_r_9_7),
    .I0(mix_r_9_2),
    .I1(mix_r_9_4),
    .I3(VCC),
    .CIN(mix_r_8_7) 
);
defparam mix_r_9_s1.ALU_MODE=0;
  ALU mix_r_10_s1 (
    .SUM(mix_r[10]),
    .COUT(mix_r_10_7),
    .I0(mix_r_10_2),
    .I1(mix_r_10_4),
    .I3(VCC),
    .CIN(mix_r_9_7) 
);
defparam mix_r_10_s1.ALU_MODE=0;
  ALU mix_r_11_s1 (
    .SUM(mix_r[11]),
    .COUT(mix_r_11_7),
    .I0(mix_r_11_2),
    .I1(mix_r_11_4),
    .I3(VCC),
    .CIN(mix_r_10_7) 
);
defparam mix_r_11_s1.ALU_MODE=0;
  ALU mix_r_12_s1 (
    .SUM(mix_r[12]),
    .COUT(mix_r_12_7),
    .I0(mix_r_12_2),
    .I1(mix_r_12_4),
    .I3(VCC),
    .CIN(mix_r_11_7) 
);
defparam mix_r_12_s1.ALU_MODE=0;
  ALU mix_r_13_s1 (
    .SUM(mix_r[13]),
    .COUT(mix_r_13_7),
    .I0(mix_r_13_2),
    .I1(mix_r_13_4),
    .I3(VCC),
    .CIN(mix_r_12_7) 
);
defparam mix_r_13_s1.ALU_MODE=0;
  ALU mix_r_14_s1 (
    .SUM(mix_r[14]),
    .COUT(mix_r_14_7),
    .I0(mix_r_14_2),
    .I1(mix_r_14_4),
    .I3(VCC),
    .CIN(mix_r_13_7) 
);
defparam mix_r_14_s1.ALU_MODE=0;
  ALU mix_r_15_s1 (
    .SUM(mix_r[15]),
    .COUT(mix_r_15_7),
    .I0(mix_r_15_2),
    .I1(mix_r_15_4),
    .I3(VCC),
    .CIN(mix_r_14_7) 
);
defparam mix_r_15_s1.ALU_MODE=0;
  ALU mix_r_16_s1 (
    .SUM(mix_r[16]),
    .COUT(mix_r_16_7),
    .I0(mix_r_16_2),
    .I1(mix_r_16_4),
    .I3(VCC),
    .CIN(mix_r_15_7) 
);
defparam mix_r_16_s1.ALU_MODE=0;
  ALU mix_r_17_s1 (
    .SUM(mix_r[17]),
    .COUT(mix_r_17_7),
    .I0(mix_r_17_2),
    .I1(mix_r_17_4),
    .I3(VCC),
    .CIN(mix_r_16_7) 
);
defparam mix_r_17_s1.ALU_MODE=0;
  ALU mix_r_18_s1 (
    .SUM(mix_r[18]),
    .COUT(mix_r_18_7),
    .I0(mix_r_18_2),
    .I1(mix_r_18_4),
    .I3(VCC),
    .CIN(mix_r_17_7) 
);
defparam mix_r_18_s1.ALU_MODE=0;
  ALU mix_r_19_s1 (
    .SUM(mix_r[19]),
    .COUT(mix_r_19_7),
    .I0(mix_r_19_2),
    .I1(mix_r_19_4),
    .I3(VCC),
    .CIN(mix_r_18_7) 
);
defparam mix_r_19_s1.ALU_MODE=0;
  ALU mix_r_33_s1 (
    .SUM(mix_r[33]),
    .COUT(mix_r_33_2_COUT),
    .I0(mix_r_33_2),
    .I1(mix_r_33_4),
    .I3(VCC),
    .CIN(mix_r_19_7) 
);
defparam mix_r_33_s1.ALU_MODE=0;
  INV n232_s2 (
    .O(n232_6),
    .I(rst_n_d) 
);
  INV n1273_s2 (
    .O(n1273_6),
    .I(pans_d[6]) 
);
  INV n1274_s2 (
    .O(n1274_6),
    .I(pans_d[5]) 
);
  INV n1275_s2 (
    .O(n1275_6),
    .I(pans_d[4]) 
);
  INV n1276_s2 (
    .O(n1276_6),
    .I(pans_d[3]) 
);
  INV n1277_s2 (
    .O(n1277_6),
    .I(pans_d[2]) 
);
  INV n1278_s2 (
    .O(n1278_6),
    .I(pans_d[1]) 
);
  INV n1279_s2 (
    .O(n1279_6),
    .I(pans_d[0]) 
);
  INV n1344_s2 (
    .O(n1344_6),
    .I(pans_d[13]) 
);
  INV n1345_s2 (
    .O(n1345_6),
    .I(pans_d[12]) 
);
  INV n1346_s2 (
    .O(n1346_6),
    .I(pans_d[11]) 
);
  INV n1347_s2 (
    .O(n1347_6),
    .I(pans_d[10]) 
);
  INV n1348_s2 (
    .O(n1348_6),
    .I(pans_d[9]) 
);
  INV n1349_s2 (
    .O(n1349_6),
    .I(pans_d[8]) 
);
  INV n1350_s2 (
    .O(n1350_6),
    .I(pans_d[7]) 
);
  INV n1415_s2 (
    .O(n1415_6),
    .I(pans_d[20]) 
);
  INV n1416_s2 (
    .O(n1416_6),
    .I(pans_d[19]) 
);
  INV n1417_s2 (
    .O(n1417_6),
    .I(pans_d[18]) 
);
  INV n1418_s2 (
    .O(n1418_6),
    .I(pans_d[17]) 
);
  INV n1419_s2 (
    .O(n1419_6),
    .I(pans_d[16]) 
);
  INV n1420_s2 (
    .O(n1420_6),
    .I(pans_d[15]) 
);
  INV n1421_s2 (
    .O(n1421_6),
    .I(pans_d[14]) 
);
  INV n1486_s2 (
    .O(n1486_6),
    .I(pans_d[27]) 
);
  INV n1487_s2 (
    .O(n1487_6),
    .I(pans_d[26]) 
);
  INV n1488_s2 (
    .O(n1488_6),
    .I(pans_d[25]) 
);
  INV n1489_s2 (
    .O(n1489_6),
    .I(pans_d[24]) 
);
  INV n1490_s2 (
    .O(n1490_6),
    .I(pans_d[23]) 
);
  INV n1491_s2 (
    .O(n1491_6),
    .I(pans_d[22]) 
);
  INV n1492_s2 (
    .O(n1492_6),
    .I(pans_d[21]) 
);
  VCC VCC_cZ (
    .V(VCC)
);
  GND GND_cZ (
    .G(GND)
);
  GSR GSR (
    .GSRI(VCC) 
);
endmodule /* verification_dds */

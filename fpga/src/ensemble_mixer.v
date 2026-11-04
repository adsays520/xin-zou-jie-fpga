module ensemble_mixer(
 input wire clk,rst_n,sample_tick,clear,ensemble_mode,
 input wire signed [23:0] legacy_l,legacy_r,guitar_sample,bass_sample,piano_l,piano_r,violin_sample,drum_l,drum_r,
 input wire [6:0] legacy_target,guitar_target,bass_target,piano_target,violin_target,drum_target,
 output wire signed [23:0] mix_l,mix_r,
 output reg deadline_miss
);
 reg [6:0] legacy_level,guitar_level,bass_level,piano_level,violin_level,drum_level;
 reg signed [23:0] captured[0:7];
 reg [6:0] gains[0:7];
 reg [2:0] slot,state;
 reg signed [31:0] product,scaled,accum_l,accum_r,total_l,total_r;
 reg signed [23:0] operand;
 reg [6:0] gain;
 reg peak_start;
 wire peak_valid;
 reg peak_wait;
 function [6:0] ramp;
  input [6:0] current,target;
  begin ramp=current<target?current+1'b1:current>target?current-1'b1:current;end
 endfunction
 performance_peak_control u_peak(.clk(clk),.rst_n(rst_n),.start(peak_start),.clear(clear),
  .sample_l(total_l),.sample_r(total_r),.out_l(mix_l),.out_r(mix_r),.valid(peak_valid),.safety_hit());
 always @(posedge clk or negedge rst_n)begin
  if(!rst_n)begin
   legacy_level<=127;guitar_level<=127;bass_level<=127;piano_level<=127;violin_level<=127;drum_level<=127;
   slot<=0;state<=0;product<=0;scaled<=0;accum_l<=0;accum_r<=0;total_l<=0;total_r<=0;
   operand<=0;gain<=0;peak_start<=0;peak_wait<=0;deadline_miss<=0;
  end else if(clear)begin
   slot<=0;state<=0;accum_l<=0;accum_r<=0;total_l<=0;total_r<=0;peak_start<=0;peak_wait<=0;
  end else begin
   peak_start<=0;
   if(peak_valid)peak_wait<=0;
   if(sample_tick)begin
    if(state!=0||peak_wait)deadline_miss<=1;
    else begin
     captured[0]<=ensemble_mode?guitar_sample:legacy_l;captured[1]<=ensemble_mode?guitar_sample:legacy_r;
     captured[2]<=ensemble_mode?piano_l:24'sd0;captured[3]<=ensemble_mode?piano_r:24'sd0;
     captured[4]<=ensemble_mode?bass_sample:24'sd0;captured[5]<=ensemble_mode?violin_sample:24'sd0;
     captured[6]<=drum_l;captured[7]<=drum_r;
     gains[0]<=ensemble_mode?guitar_level:legacy_level;gains[1]<=ensemble_mode?guitar_level:legacy_level;
     gains[2]<=piano_level;gains[3]<=piano_level;gains[4]<=bass_level;gains[5]<=violin_level;
     gains[6]<=drum_level;gains[7]<=drum_level;
     legacy_level<=ramp(legacy_level,legacy_target);guitar_level<=ramp(guitar_level,guitar_target);
     bass_level<=ramp(bass_level,bass_target);piano_level<=ramp(piano_level,piano_target);
     violin_level<=ramp(violin_level,violin_target);drum_level<=ramp(drum_level,drum_target);
     slot<=0;accum_l<=0;accum_r<=0;state<=1;
    end
   end
   case(state)
    1:begin operand<=captured[slot];gain<=gains[slot];state<=2;end
    2:begin product<=operand*$signed({1'b0,gain});state<=3;end
    3:begin if(gain==127)scaled<=operand;else scaled<=product>>>7;state<=4;end
    4:begin
     if(slot==0||slot==2||slot==4||slot==5||slot==6)accum_l<=accum_l+scaled;
     if(slot==1||slot==3||slot==4||slot==5||slot==7)accum_r<=accum_r+scaled;
     if(slot==7)state<=5;else begin slot<=slot+1'b1;state<=1;end
    end
    5:begin total_l<=accum_l;total_r<=accum_r;peak_start<=1;peak_wait<=1;state<=0;end
    default:begin end
   endcase
  end
 end
endmodule

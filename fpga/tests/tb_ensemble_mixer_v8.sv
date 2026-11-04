`timescale 1ns/1ps
module tb_ensemble_mixer_v8;
 reg clk=0,rst_n=0,sample_tick=0,clear=0,ensemble_mode=1;
 always #10 clk=~clk;
 reg signed [23:0] legacy_l=12345,legacy_r=-23456,guitar_sample=10000,bass_sample=20000;
 reg signed [23:0] piano_l=30000,piano_r=-35000,violin_sample=40000,drum_l=50000,drum_r=-60000;
 reg [6:0] guitar_target=127,bass_target=127,piano_target=127,violin_target=127,drum_target=127;
 wire signed [23:0] mixed_l,mixed_r;
 wire deadline;
 integer frame;
 ensemble_mixer dut(.clk(clk),.rst_n(rst_n),.sample_tick(sample_tick),.clear(clear),.ensemble_mode(ensemble_mode),
  .legacy_l(legacy_l),.legacy_r(legacy_r),.guitar_sample(guitar_sample),.bass_sample(bass_sample),
  .piano_l(piano_l),.piano_r(piano_r),.violin_sample(violin_sample),.drum_l(drum_l),.drum_r(drum_r),
  .legacy_target(7'd127),.guitar_target(guitar_target),.bass_target(bass_target),.piano_target(piano_target),
  .violin_target(violin_target),.drum_target(drum_target),.mix_l(mixed_l),.mix_r(mixed_r),.deadline_miss(deadline));
 task step;
  begin @(negedge clk);sample_tick=1;@(negedge clk);sample_tick=0;repeat(1040)@(negedge clk);end
 endtask
 initial begin
  repeat(5)@(negedge clk);rst_n=1;
  for(frame=0;frame<40;frame++)step();
  if(mixed_l!==150000||mixed_r!==-25000||deadline)$fatal(1,"ensemble sum L=%0d R=%0d",mixed_l,mixed_r);
  bass_target=0;for(frame=0;frame<170;frame++)step();
  if(mixed_l!==130000||mixed_r!==-45000)$fatal(1,"Bass independent mute");
  guitar_target=0;piano_target=0;violin_target=0;drum_target=0;
  for(frame=0;frame<170;frame++)step();
  if(mixed_l!==0||mixed_r!==0)$fatal(1,"all bus mute");
  ensemble_mode=0;drum_target=127;
  for(frame=0;frame<170;frame++)step();
  if(mixed_l!==62345||mixed_r!==-83456)$fatal(1,"legacy stereo route L=%0d R=%0d accum=%0d/%0d gains=%0d/%0d",mixed_l,mixed_r,dut.total_l,dut.total_r,dut.legacy_level,dut.drum_level);
  ensemble_mode=1;guitar_target=127;bass_target=127;piano_target=127;violin_target=127;
  guitar_sample=8388607;bass_sample=8388607;piano_l=8388607;piano_r=8388607;violin_sample=8388607;drum_l=8388607;drum_r=8388607;
  for(frame=0;frame<200;frame++)begin
   step();
   if(frame>35&&(mixed_l<0||mixed_r<0||mixed_l>7864320||mixed_r>7864320))$fatal(1,"sum overflow/safety");
  end
  @(negedge clk);clear=1;@(negedge clk);clear=0;
  if(mixed_l!==0||mixed_r!==0||deadline)$fatal(1,"clear/deadline");
  $display("PASS ENSEMBLE MIXER V8: five simultaneous buses, independent Bass mute, stereo legacy, headroom/safety and clear; one shared gain multiplier");
  $finish;
 end
endmodule

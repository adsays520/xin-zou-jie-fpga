`timescale 1ns/1ps
module tb_pitch_core;
 reg clk=0,rst_n=0,tick=0,note=0,enabled=0;reg [23:0] ratio=1048576;
 always #10 clk=~clk;
 integer frame=0,cycles=0,file,scenario=0;reg [2:0] string_sel=0;reg [4:0] fret=0;
 wire [9:0] delay_len,pick;wire [15:0] loop_gain,scrape,noise_mix;
 wire [23:0] damp,allpass;wire [31:0] init_phase;wire [1:0] smooth;
 guitar_note_params params(.string_sel(string_sel),.fret_sel(fret),.delay_len(delay_len),
 .loop_gain_q15(loop_gain),.pick_offset(pick),.scrape_q15(scrape),.damping_q23(damp),
 .allpass_q23(allpass),.init_phase_step(init_phase),.noise_mix_q15(noise_mix),.excitation_smooth(smooth));
 wire valid,old_valid,active;wire signed [23:0] sample,old_sample;
 guitar_voice_tdm_core #(.ENABLE_TAIL_HF_DAMPING(0)) dut(.clk(clk),.rst_n(rst_n),.enable(1'b1),.context_load(1'b0),.context_save(1'b0),
.context_new(1'b0),.context_id(5'd0),.context_prefetch_id(5'd0),.auxiliary_context_in(139'd0),
.sample_tick(tick),.note_on(note),.requested_delay_len(delay_len),.requested_loop_gain_q15(loop_gain),
.requested_pick_offset(pick),.requested_scrape_q15(scrape),.requested_damping_q23(damp),
.requested_allpass_q23(allpass),.requested_init_phase_step(init_phase),.requested_noise_mix_q15(noise_mix),
.requested_excitation_smooth(smooth),.velocity(7'd110),
 .pitch_enabled(enabled),.pitch_ratio_q20(ratio),.sample_valid(valid),.sample_out(sample),.active(active));
 pitch_legacy_core #(.ENABLE_TAIL_HF_DAMPING(0)) legacy(.clk(clk),.rst_n(rst_n),.enable(1'b1),.context_load(1'b0),.context_save(1'b0),
.context_new(1'b0),.context_id(5'd0),.context_prefetch_id(5'd0),.auxiliary_context_in(139'd0),
.sample_tick(tick),.note_on(note),.requested_delay_len(delay_len),.requested_loop_gain_q15(loop_gain),
.requested_pick_offset(pick),.requested_scrape_q15(scrape),.requested_damping_q23(damp),
.requested_allpass_q23(allpass),.requested_init_phase_step(init_phase),.requested_noise_mix_q15(noise_mix),
.requested_excitation_smooth(smooth),.velocity(7'd110),.sample_valid(old_valid),.sample_out(old_sample));
 always @(posedge clk)if(valid)begin
  if(scenario==0&&(sample!==old_sample||valid!==old_valid))$fatal(1,"Bypass mismatch frame=%0d",frame);
  if(^sample===1'bx)$fatal(1,"Undefined pitch audio");
  $fdisplay(file,"%0d %0d %0d %0d",frame,sample,old_sample,ratio);
 end
 reg [23:0] trajectory [0:35999];
 initial begin
  if($value$plusargs("SCENARIO=%d",scenario))begin end
  if($value$plusargs("STRING=%d",string_sel))begin end
  if($value$plusargs("FRET=%d",fret))begin end
  if(scenario==2)$readmemh("tests/ratio_slide_q20.mem",trajectory);
  if(scenario==3)$readmemh("tests/ratio_vibrato_q20.mem",trajectory);
  file=$fopen("tests/results/pitch_core_samples.txt","w");
  repeat(30)@(negedge clk);rst_n=1;repeat(5)@(negedge clk);note=1;
  @(negedge clk);note=0;
  for(frame=0;frame<36000;frame=frame+1)begin
   if(scenario==1&&frame>=6000)begin enabled=1;ratio=1176987;end
   if(scenario==4&&frame>=6000)begin enabled=1;ratio=934175;end
   if((scenario==2||scenario==3)&&frame>=6000)begin enabled=1;ratio=trajectory[frame];end
   @(negedge clk);tick=1;@(negedge clk);tick=0;repeat(22)@(negedge clk);
  end
  $fclose(file);$display("PASS pitch core scenario=%0d: finite audio, one Note-On",scenario);$finish;
 end
endmodule

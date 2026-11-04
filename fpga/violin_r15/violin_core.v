`timescale 1ns/1ps
`default_nettype none
// V16 SMS: spectral parameters, sine oscillators and generated bow noise.
// No instrument audio waveforms, sample loops or PCM playback memories.
module violin_core #(parameter ROM_ROOT="violin_r15/sms_rom",parameter PANEL_PITCH=0)(
 input wire clk,rst_n,sample_tick,
 input wire [23:0] panel_inverse_q20,panel_ratio_q20,
 input wire command_valid,output wire command_ready,
 input wire command_on,command_legato,command_force_off,
 input wire [6:0] command_key,command_velocity,
 output wire active_o,output reg ready_o,output reg signed [23:0] sample_o,
 output reg sample_valid_o,produced_o,internal_valid_o,
 output reg signed [23:0] internal_sample_o,
 output reg deadline_miss_o,overflow_o,invalid_event_o,
 output reg [15:0] last_cycles_o
);
reg [16:0] fifo[0:7];reg [2:0] wr,rd;reg [3:0] count;
reg [5:0] state;reg [6:0] boot;
wire push=command_valid&&command_ready;
wire pop=ready_o&&state==0&&!sample_tick&&count!=0;
assign command_ready=ready_o&&count<8;
always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin wr<=0;rd<=0;count<=0;end
 else begin
  if(push)begin fifo[wr]<={command_force_off,command_legato,command_on,command_key,command_velocity};wr<=wr+1'b1;end
  if(pop)rd<=rd+1'b1;
  case({push,pop})2'b10:count<=count+1'b1;2'b01:count<=count-1'b1;default:;endcase
 end
end
reg [15:0] amplitude_rom[0:23551];reg [15:0] phase_rom[0:2943];
reg [7:0] release_rom[0:2943];reg signed [15:0] sine_rom[0:4095];
(* syn_romstyle="logic" *)reg [31:0] frequency_rom[0:45];
initial begin
 $readmemh({ROM_ROOT,"/amplitude.hex"},amplitude_rom);
 $readmemh({ROM_ROOT,"/phase.hex"},phase_rom);
 $readmemh({ROM_ROOT,"/release.hex"},release_rom);
 $readmemh({ROM_ROOT,"/sine.hex"},sine_rom);
 $readmemh({ROM_ROOT,"/frequency.hex"},frequency_rom);
end
reg [23:0] amplitudes[0:63];reg [15:0] offsets[0:63];
reg [5:0] note_index,partial;reg [6:0] current_key;
reg gate,tone_active,fast_release,phase_snap;
reg [17:0] note_age;reg [16:0] env_age;reg [15:0] release_age;
reg [31:0] target_increment,current_increment,render_increment,phase_base;
reg [15:0] velocity_target,velocity_gain,bow_env;
reg [2:0] knot;reg [15:0] fraction;
reg [16:0] env_start;reg [13:0] env_recip;
reg [2:0] env_knot;
always @*begin
 env_start=0;env_recip=13981;env_knot=0;
 if(env_age>=110400)begin env_start=110400;env_recip=0;env_knot=7;end
 else if(env_age>=62400)begin env_start=62400;env_recip=350;env_knot=6;end
 else if(env_age>=31200)begin env_start=31200;env_recip=538;env_knot=5;end
 else if(env_age>=16800)begin env_start=16800;env_recip=1165;env_knot=4;end
 else if(env_age>=7680)begin env_start=7680;env_recip=1840;env_knot=3;end
 else if(env_age>=3600)begin env_start=3600;env_recip=4112;env_knot=2;end
 else if(env_age>=1200)begin env_start=1200;env_recip=6991;env_knot=1;end

end
wire [2:0] next_knot=knot==7?3'd7:knot+1'b1;
wire [14:0] amp_address={note_index,knot,partial};
wire [14:0] amp_next_address={note_index,next_knot,partial};
wire [11:0] part_address={note_index,partial};
reg [15:0] amp_a,amp_b,phase_target;reg [7:0] release_coefficient;
reg signed [63:0] product,release_product,panel_product;
reg [31:0] interpolation_left,interpolation_right;
wire [16:0] weight_left={1'b0,~fraction}+17'd1;
wire [32:0] interpolation_sum={1'b0,interpolation_left}+{1'b0,interpolation_right};
reg signed [15:0] sine_value;
reg [31:0] harmonic_phase;reg [37:0] harmonic_step;
reg [23:0] next_amplitude;reg signed [31:0] interpolated;
reg signed [47:0] accumulator;reg signed [63:0] voice_product;
reg signed [23:0] pending_output;reg pending_valid;
reg [15:0] cycles;
reg [8:0] motion_counter;reg signed [15:0] bow_motion[0:3];
wire signed [15:0] spectral_motion=bow_motion[partial[5:4]]>>>3;
reg [31:0] noise_lfsr;reg signed [23:0] noise_low,noise_slow;
wire signed [24:0] noise_error=$signed(noise_lfsr[23:0])-$signed(noise_low);
reg signed [47:0] noise_product;
reg signed [47:0] noise_velocity;reg signed [23:0] voice_scaled;
wire signed [23:0] noise_scaled=noise_product>>>20;
// Explicit-width subtraction boundaries: prevent carry/borrow widening in synthesis.
wire [16:0] env_elapsed=env_age-env_start;
wire [31:0] env_fraction_product=env_elapsed*env_recip;
wire signed [15:0] amp_delta=$signed(amp_b)-$signed(amp_a);
wire signed [15:0] interp_sum=$signed(amp_a)+$signed(product[31:16]);
wire signed [24:0] adjusted_amplitude=$signed({1'b0,next_amplitude})+$signed(product[39:15]);
wire signed [24:0] noise_band=$signed({noise_low[23],noise_low})-$signed({noise_slow[23],noise_slow});
wire signed [15:0] offset_difference=phase_target-offsets[partial];
wire [31:0] oscillator_phase=harmonic_phase+{offsets[partial],16'b0};
wire signed [24:0] amplitude_difference=$signed({1'b0,interpolated[15:0],8'b0})-$signed({1'b0,amplitudes[partial]});
wire signed [32:0] frequency_difference=$signed({1'b0,target_increment})-$signed({1'b0,current_increment});
wire signed [16:0] velocity_difference=$signed({1'b0,velocity_target})-$signed({1'b0,velocity_gain});
assign active_o=tone_active;
function signed [31:0] smooth_step;
 input signed [31:0] d;input [4:0] shift;
 begin if(d>0)smooth_step=(d+(32'sd1<<shift)-1)>>>shift;else if(d<0)smooth_step=-(((-d)+(32'sd1<<shift)-1)>>>shift);else smooth_step=0;end
endfunction
function signed [23:0] saturate;
 input signed [63:0] x;
 begin if(x>8388607)saturate=24'sh7fffff;else if(x< -8388608)saturate=-24'sh800000;else saturate=x[23:0];end
endfunction
always @(posedge clk or negedge rst_n)begin
 if(!rst_n)begin
  ready_o<=0;state<=63;boot<=0;sample_o<=0;sample_valid_o<=0;produced_o<=0;internal_valid_o<=0;internal_sample_o<=0;
  deadline_miss_o<=0;overflow_o<=0;invalid_event_o<=0;last_cycles_o<=0;
  note_index<=0;partial<=0;current_key<=55;gate<=0;tone_active<=0;fast_release<=0;phase_snap<=1;
  note_age<=0;env_age<=0;release_age<=48000;target_increment<=17538956;current_increment<=17538956;
  render_increment<=17538956;phase_base<=0;velocity_target<=0;velocity_gain<=0;bow_env<=0;
  knot<=0;fraction<=0;pending_output<=0;pending_valid<=0;cycles<=0;
  motion_counter<=0;bow_motion[0]<=0;bow_motion[1]<=0;bow_motion[2]<=0;bow_motion[3]<=0;
  noise_lfsr<=32'h4f329a17;noise_low<=0;noise_slow<=0;
  interpolation_left<=0;interpolation_right<=0;amp_a<=0;amp_b<=0;phase_target<=0;release_coefficient<=1;product<=0;release_product<=0;panel_product<=0;
  sine_value<=0;harmonic_phase<=0;harmonic_step<=0;
  next_amplitude<=0;interpolated<=0;accumulator<=0;voice_product<=0;noise_product<=0;noise_velocity<=0;voice_scaled<=0;
 end else begin
  sample_valid_o<=0;produced_o<=0;internal_valid_o<=0;
  if(state!=0&&state!=63)cycles<=cycles+1'b1;
  if(command_valid&&!command_ready&&ready_o)overflow_o<=1;
  if(sample_tick&&ready_o)begin
   sample_o<=pending_valid?pending_output:24'sd0;sample_valid_o<=1;pending_valid<=0;
   if(state!=0)deadline_miss_o<=1;
  end
  case(state)
   63:begin amplitudes[boot[5:0]]<=0;offsets[boot[5:0]]<=0;if(boot==63)begin ready_o<=1;state<=0;end else boot<=boot+1'b1;end
   0:begin
    if(pop)begin
     if(fifo[rd][16])begin gate<=0;fast_release<=1;release_age<=0;end
     else if(fifo[rd][14])begin
      if(fifo[rd][13:7]<55||fifo[rd][13:7]>100||fifo[rd][6:0]==0)invalid_event_o<=1;
      else begin
       note_index<=fifo[rd][13:7]-7'd55;current_key<=fifo[rd][13:7];
       target_increment<=frequency_rom[fifo[rd][13:7]-7'd55];
       if(!tone_active)begin current_increment<=frequency_rom[fifo[rd][13:7]-7'd55];phase_snap<=1;end
       // A legato change keeps the bow envelope and all oscillator phase state.
       if(!fifo[rd][15]||!gate)env_age<=0;
       note_age<=0;gate<=1;tone_active<=1;fast_release<=0;release_age<=0;
       velocity_target<={fifo[rd][6:0],8'b0};
      end
     end else if(fifo[rd][13:7]==current_key)begin gate<=0;release_age<=0;end
    end
    if(sample_tick)begin cycles<=0;state<=20;end
   end
   20:begin
    knot<=env_knot;if(env_fraction_product>=32'd16776960)fraction<=16'hffff;else fraction<=env_fraction_product[23:8];
    if(gate)begin
     if(env_age<110400)env_age<=env_age+1'b1;
     if(note_age<200000)note_age<=note_age+1'b1;
     if(bow_env<32735)bow_env<=bow_env+32;else bow_env<=32767;
    end else begin
     if(release_age<48000)release_age<=release_age+1'b1;
     if(release_age>=47999||(fast_release&&release_age>=383))tone_active<=0;
     if(bow_env!=0)bow_env<=bow_env-((bow_env>>9)+1'b1);
    end
    current_increment<=current_increment+smooth_step(frequency_difference,8);
    velocity_gain<=velocity_gain+smooth_step(velocity_difference,8);
    state<=24;
   end
   24:begin panel_product<=current_increment*(PANEL_PITCH?panel_ratio_q20:24'd1048576);state<=25;end
   25:begin render_increment<=panel_product>>20;state<=26;end
   26:begin
    phase_base<=phase_base+render_increment;harmonic_phase<=phase_base+render_increment;harmonic_step<={6'b0,render_increment};
    accumulator<=0;partial<=0;state<=1;
    motion_counter<=motion_counter+1'b1;
    if(motion_counter==511)begin
     bow_motion[0]<=bow_motion[0]+(($signed(noise_lfsr[15:0])-bow_motion[0])>>>5);
     bow_motion[1]<=bow_motion[1]+(($signed(noise_lfsr[23:8])-bow_motion[1])>>>5);
     bow_motion[2]<=bow_motion[2]+(($signed(noise_lfsr[31:16])-bow_motion[2])>>>5);
     bow_motion[3]<=bow_motion[3]+(($signed({noise_lfsr[7:0],noise_lfsr[31:24]})-bow_motion[3])>>>5);
    end
    noise_lfsr<={noise_lfsr[30:0],noise_lfsr[31]^noise_lfsr[21]^noise_lfsr[1]^noise_lfsr[0]};
    noise_low<=noise_low+(noise_error>>>2);
    noise_slow<=noise_slow+((noise_low-noise_slow)>>>6);
   end
   1:begin amp_a<=amplitude_rom[amp_address];phase_target<=phase_rom[part_address];release_coefficient<=release_rom[part_address];state<=2;end
   2:begin amp_b<=amplitude_rom[amp_next_address];state<=3;end
   3:begin interpolation_left<=amp_a*weight_left;interpolation_right<=amp_b*fraction;state<=4;end
   4:begin interpolated<=interpolation_sum[31:16];release_product<=amplitudes[partial]*release_coefficient;state<=5;end
   5:begin
    if(!tone_active)next_amplitude<=0;
    else if(!gate)begin
     if(fast_release)next_amplitude<=amplitudes[partial]-((amplitudes[partial]>>5)+(amplitudes[partial]!=0));
     else if(amplitudes[partial]>(release_product>>16))next_amplitude<=amplitudes[partial]-((release_product>>16)+1'b1);else next_amplitude<=0;
    end else if(harmonic_step>=38'h0078000000)next_amplitude<=0;
    else next_amplitude<=amplitudes[partial]+smooth_step(amplitude_difference,6);
    state<=6;
   end
   6:begin
    amplitudes[partial]<=next_amplitude;
    if(phase_snap)offsets[partial]<=phase_target;
    else offsets[partial]<=offsets[partial]+smooth_step(offset_difference,9);
    sine_value<=sine_rom[oscillator_phase[31:20]];product<=$signed({1'b0,next_amplitude})*$signed(spectral_motion);state<=7;
   end
   7:begin product<=$signed(adjusted_amplitude)*$signed(sine_value);state<=8;end
   8:begin
    if(harmonic_step<38'h0078000000)accumulator<=accumulator+(product>>>16);
    harmonic_phase<=harmonic_phase+phase_base;harmonic_step<=harmonic_step+render_increment;
    if(partial==63)state<=9;else begin partial<=partial+1'b1;state<=1;end
   end
   9:begin voice_product<=accumulator*$signed({1'b0,velocity_gain});noise_product<=$signed(noise_band)*$signed({1'b0,bow_env});state<=10;end
   10:begin noise_velocity<=noise_scaled*$signed({1'b0,velocity_gain});voice_scaled<=saturate(voice_product>>>15);state<=11;end
   11:begin
    if(tone_active)pending_output<=saturate($signed(voice_scaled)+(noise_velocity>>>15));else pending_output<=0;
    pending_valid<=1;produced_o<=1;internal_valid_o<=1;internal_sample_o<=saturate(voice_product>>>15);
    last_cycles_o<=cycles;phase_snap<=0;state<=0;
   end
   default:state<=0;
  endcase
 end
end
endmodule
`default_nettype wire

// Measured SMS piano. The historical name preserves the existing interface.
// Sixteen harmonic partials with twelve temporal bases, eight hammer modes, and four
// newly generated noise bands per voice. No recorded waveform playback.
module piano_wavetable16_tdm #(parameter PANEL_PITCH=0)(
 input wire clk,rst_n,sample_tick,note_on,note_off,poly_mode,
 input wire [23:0] panel_ratio_q20,
 input wire [6:0] requested_key,velocity,input wire [2:0] pedal_level,
 output reg sample_valid,output reg signed [23:0] sample_out,
 output wire active,output reg deadline_miss,output wire [31:0] requested_phase_step,
 input wire memory_rst_n,memory_ready,transport_fault,
 output wire bank_ready,memory_fault,
 input wire upload_begin,upload_valid,upload_commit,upload_error,
 input wire [10:0] upload_index,input wire [2047:0] upload_data,
 output wire upload_ready,output wire [10:0] upload_count,
 output wire [2:0] bank_status,output wire [7:0] status_error,
 output wire req_valid,input wire req_ready,output wire [63:0] req_data,
 input wire rsp_valid,output wire rsp_ready,input wire [63:0] rsp_data
);
 localparam IDLE=0,PREP=1,CURVE_WAIT=2,CURVE=3,TONAL=4,TWAIT=5,
            TRANS=6,XWAIT=7,SCALE=8,ADD=9,GAIN=10,OUTPUT=11,CONTROL=12,FRAME=13;
 reg [3:0] state,voice,allocation_slot,mode;
 reg [15:0] voice_active,key_down;
 reg [6:0] voice_key[0:15];reg [1:0] layer[0:15];
 reg [7:0] epoch[0:15];reg [19:0] age[0:15];
 reg [15:0] strike_gain[0:15],rise_gain[0:15];
 reg [31:0] damper_gain[0:15],noise_gain[0:15],level_bound[0:15];
 reg signed [23:0] previous_output[0:15],retrigger_offset[0:15];
 reg [6:0] retrigger_left[0:15];
 wire [6:0] safe_key=requested_key<21?7'd21:(requested_key>108?7'd108:requested_key);
 wire [3:0] new_slot=poly_mode?allocation_slot:4'd0;
 // Decode note writes once, then distribute a registered per-voice enable.
 (* syn_preserve=1 *) reg [15:0] note_write_mask;
 reg release_pending;reg [3:0] event_slot;reg [6:0] event_key;
 reg [1:0] event_layer;reg [15:0] event_gain;
 // Read the voice context before arithmetic; no mux/shift/subtract/write chain.
 reg [6:0] context_key;reg [1:0] context_layer;reg [7:0] context_epoch;
 reg [19:0] context_age;reg [15:0] context_strike,context_rise;
 reg [31:0] context_damper,context_noise,context_bound;
 reg [31:0] gain_product_q,bound_product_q,rise_product_q;
 reg [31:0] bound_loss_q,noise_loss_q,damper_loss_q[0:3];
 reg [31:0] bound_next_q,noise_next_q,damper_next_q[0:3];reg [15:0] rise_next_q;
 assign active=|voice_active;
 reg [55:0] tuning[0:87];reg [15:0] velocity_rom[0:127],headroom_rom[0:256];
 reg [143:0] curve_rom[0:1023];
 reg signed [17:0] sine_rom[0:1023];
 initial begin
  $readmemh("src/piano/wavetable/piano_keys.hex",tuning);
  $readmemh("src/piano/wavetable/piano_headroom.hex",headroom_rom);
  $readmemh("src/piano/sms/velocity.hex",velocity_rom);
  $readmemh("src/piano/sms/curves.hex",curve_rom);
  $readmemh("src/piano/sms/sine.hex",sine_rom);
 end
 wire [55:0] requested_tuning=tuning[safe_key-21];
 assign requested_phase_step=requested_tuning[31:0];
 reg [8:0] frame_bank;reg [7:0] frame_epoch;reg [19:0] frame_age;
 reg [15:0] frame_gain,frame_noise,frame_rise;reg [4:0] frame_weight;
 reg [8:0] total_weight;reg [15:0] mix_gain,headroom_gain;
 reg signed [47:0] voice_sum,mix_sum,scaled_voice;
 reg signed [64:0] scale_product;reg physics_clip;
 reg [3:0] curve_number;reg signed [11:0] basis_value[0:11];
 reg [143:0] curve0,curve_read;reg [63:0] frame_noise_word;
 reg [31:0] random_state;
 wire frame_matches=epoch[voice]==frame_epoch;
 wire [8:0] voice_bank={(context_key-7'd21),context_layer};
 wire [31:0] frame_gain_product=context_damper[31:16]*context_strike;
 wire [31:0] bound_product=context_bound[31:16]*context_strike;
 wire [15:0] bound0=bound_product_q>>15;
 wire [15:0] effective_bound=bound0<context_damper[31:16]?bound0:context_damper[31:16];
 wire [4:0] weight_now={1'b0,effective_bound[14:11]}+(|effective_bound[10:0]);
 wire [31:0] bound_loss=(context_key<48?(context_bound>>17):(context_key<84?(context_bound>>16):(context_bound>>15)))+1'b1;
 wire [31:0] noise_loss=(context_noise>>11)+1'b1;
 wire [31:0] rise_product=(16'd65535-context_rise)*16'd3787;
 reg [8:0] curve_index;reg [10:0] curve_fraction;
 reg [19:0] curve_time;
 always @* begin
  curve_index=511;curve_fraction=0;curve_time=context_age;
  if(context_age<2048)begin curve_index=context_age>>5;curve_fraction={context_age[4:0],6'b0};end
  else if(context_age<10240)begin
   curve_time=context_age-2048;curve_index=64+(curve_time>>7);curve_fraction={curve_time[6:0],4'b0};end
  else if(context_age<75776)begin
   curve_time=context_age-10240;curve_index=128+(curve_time>>9);curve_fraction={curve_time[8:0],2'b0};end
  else if(context_age<598016)begin
   curve_time=context_age-75776;curve_index=256+(curve_time>>11);curve_fraction=curve_time[10:0];end
 end
 reg [10:0] frame_fraction;
 wire signed [11:0] curve_a=curve0[curve_number*12+:12],curve_b=curve_read[curve_number*12+:12];
 wire signed [12:0] curve_delta=$signed({curve_b[11],curve_b})-$signed({curve_a[11],curve_a});
 wire signed [24:0] curve_product=curve_delta*$signed({1'b0,frame_fraction});
 wire signed [24:0] curve_interp=$signed(curve_a)+(curve_product>>>11);
 wire tonal_issue=state==TONAL;
 wire [7:0] tonal_address={voice,mode};
 wire [7:0] phase_address={voice,mode};
 reg [26:0] phase_ram[0:255];
 reg t1,t2,t3,t4,t5,t6,tl1,tl2,tl3,tl4,tl5,tl6;
 reg [7:0] ta1;reg [7:0] te1;
 wire [191:0] weights1;
 wire [31:0] frequency1;
 reg [191:0] weights2;
 reg [26:0] phase1;reg [4:0] sh2,sh3,sh4,sh5;
 reg signed [17:0] sin2,cos2,sin3,cos3,sin4,cos4,sin5,cos5;
 reg signed [19:0] real_product3[0:11],imag_product3[0:11];
 reg signed [23:0] real_dot4,imag_dot4;
 reg signed [31:0] real_amp5,imag_amp5;
 reg signed [49:0] real_carrier6,imag_carrier6;
 wire signed [63:0] shifted_real4=$signed({{40{real_dot4[23]}},real_dot4})<<<sh4;
 wire signed [63:0] shifted_imag4=$signed({{40{imag_dot4[23]}},imag_dot4})<<<sh4;
 wire signed [50:0] tonal_difference=$signed({real_carrier6[49],real_carrier6})-$signed({imag_carrier6[49],imag_carrier6});
 wire signed [47:0] tonal_value=tonal_difference>>>17;
 reg signed [23:0] real_sum3,imag_sum3;integer j;
 always @* begin
  real_sum3=0;imag_sum3=0;
  real_sum3=((($signed(real_product3[0])+$signed(real_product3[1]))+($signed(real_product3[2])+$signed(real_product3[3])))+(($signed(real_product3[4])+$signed(real_product3[5]))+($signed(real_product3[6])+$signed(real_product3[7]))))+(($signed(real_product3[8])+$signed(real_product3[9]))+($signed(real_product3[10])+$signed(real_product3[11])));
  imag_sum3=((($signed(imag_product3[0])+$signed(imag_product3[1]))+($signed(imag_product3[2])+$signed(imag_product3[3])))+(($signed(imag_product3[4])+$signed(imag_product3[5]))+($signed(imag_product3[6])+$signed(imag_product3[7]))))+(($signed(imag_product3[8])+$signed(imag_product3[9]))+($signed(imag_product3[10])+$signed(imag_product3[11])));
 end
 // Hammer and stochastic resonator state RAM. No reset fanout to RAM cells;
 // a note's first frame explicitly supplies its initial states instead.
 reg signed [31:0] xr_ram[0:191],xi_ram[0:191];
 wire transient_issue=state==TRANS;
 wire [7:0] x_address=voice*12+mode;
 wire [6:0] transient_address={voice,mode[2:0]};
 reg x1,x2,x3,x4,xl1,xl2,xl3,xl4;
 reg [7:0] xa1,xa2,xa3,xa4,xe1,xe2,xe3,xe4;
 reg [3:0] xm1;
 wire [63:0] transient1;
 reg signed [31:0] xr1,xi1;
 reg signed [16:0] pole_a1,pole_b1;
 reg signed [48:0] xrr2,xii2,xri2,xir2;
 reg signed [31:0] random_product2;reg [15:0] noise_level2;
 reg xn2,xn3;reg signed [50:0] real_next3,imag_next3;
 reg signed [31:0] real_state4,imag_state4;reg signed [48:0] x_output4;
 wire signed [31:0] init_real={{18{transient1[29]}},transient1[29:16]}<<<(10+{transient1[1:0],1'b0});
 wire signed [31:0] init_imag={{18{transient1[15]}},transient1[15:2]}<<<(10+{transient1[1:0],1'b0});
 wire signed [31:0] x_real=frame_age==0?(xm1<8?init_real:32'sd0):xr1;
 wire signed [31:0] x_imag=frame_age==0?(xm1<8?init_imag:32'sd0):xi1;
 wire signed [15:0] noise_amplitude=frame_noise_word[(xm1-8)*16+:16];
 wire signed [48:0] stochastic_product=random_product2*$signed({1'b0,noise_level2});
 wire signed [50:0] stochastic_wide={{2{stochastic_product[48]}},stochastic_product};
 wire signed [34:0] next_real=(real_next3+51'sd32768)>>>16;
 wire signed [34:0] next_imag=(imag_next3+51'sd32768)>>>16;
 wire signed [47:0] transient_value=x_output4>>>16;
 wire [15:0] headroom_target=headroom_rom[total_weight];
 wire signed [64:0] mix_product=mix_sum*$signed({1'b0,mix_gain});
 function signed [23:0] clip24;
  input signed [64:0] v;
  begin if(v>8388607)clip24=24'sh7fffff;else if(v< -8388608)clip24=24'sh800000;else clip24=v[23:0];end
 endfunction
 reg signed [31:0] offset_product;
 wire signed [47:0] corrected_voice=scaled_voice+(offset_product>>>6);
 wire parameters_loaded;
 wire [3:0] loaded_voice;
 wire [7:0] loaded_epoch;
 wire [63:0] cached_noise;
 wire [1:0] requested_layer=velocity<48?0:(velocity<80?1:(velocity<112?2:3));
 piano_ddr_bank u_parameters(
  .clk(clk),.rst_n(memory_rst_n),.flush(!rst_n),.memory_ready(memory_ready),.transport_fault(transport_fault),
  .initialized(bank_ready),.fault(memory_fault),
  .upload_begin(upload_begin),.upload_valid(upload_valid),.upload_commit(upload_commit),.upload_error(upload_error),
  .upload_index(upload_index),.upload_data(upload_data),.upload_ready(upload_ready),.upload_count(upload_count),
  .bank_status(bank_status),.status_error(status_error),
  .load_valid(|note_write_mask),.load_voice(event_slot),
  .load_bank({(event_key-7'd21),event_layer}),.load_epoch(epoch[event_slot]+8'd1),
  .loaded(parameters_loaded),.loaded_voice(loaded_voice),.loaded_epoch(loaded_epoch),
  .tonal_enable(tonal_issue),.tonal_address(tonal_address),
  .tonal_weights(weights1),.tonal_frequency(frequency1),
  .transient_enable(transient_issue),.transient_address(transient_address),
  .transient_parameters(transient1),.noise_voice(voice),.noise_parameters(cached_noise),
  .req_valid(req_valid),.req_ready(req_ready),.req_data(req_data),
  .rsp_valid(rsp_valid),.rsp_ready(rsp_ready),.rsp_data(rsp_data));
 reg [50:0] panel_step_product;
 reg [26:0] panel_phase_base;reg [7:0] panel_phase_address,panel_phase_epoch;
 reg panel_mute3,panel_mute4;
 always @(posedge clk)begin
  if(t1&&PANEL_PITCH)begin
   panel_step_product<=frequency1[26:0]*panel_ratio_q20;
   panel_phase_base<=phase1;panel_phase_address<=ta1;panel_phase_epoch<=te1;
  end
  if(t2&&PANEL_PITCH)begin
   if(epoch[panel_phase_address[7:4]]==panel_phase_epoch)
    phase_ram[panel_phase_address]<=panel_phase_base+panel_step_product[46:20];
   panel_mute3<=panel_step_product[50:20]>=31'd67108864;
  end
  if(t3&&PANEL_PITCH)panel_mute4<=panel_mute3;
  if(state==FRAME||state==CURVE_WAIT)begin
   curve_read<=curve_rom[{(context_key>=72),(state==FRAME?curve_index:(curve_index==511?9'd511:curve_index+1'b1))}];
  end
  if(state==FRAME)begin
   frame_noise_word<=cached_noise;
  end
  if(tonal_issue)begin
   phase1<=frame_age==0?27'd0:phase_ram[phase_address];
  end
  if(t1)begin
   sin2<=sine_rom[phase1[26:17]];cos2<=sine_rom[phase1[26:17]+10'd256];
   if(!PANEL_PITCH&&epoch[ta1[7:4]]==te1)phase_ram[ta1]<=phase1+frequency1[26:0];
  end
  if(transient_issue)begin
   xr1<=xr_ram[x_address];xi1<=xi_ram[x_address];
  end
  if(x4&&epoch[voice]==xe4)begin xr_ram[xa4]<=real_state4;xi_ram[xa4]<=imag_state4;end
 end
 integer i;
 always @(posedge clk or negedge rst_n)begin
  if(!rst_n)begin
   state<=IDLE;voice<=0;allocation_slot<=0;mode<=0;voice_active<=0;key_down<=0;
   note_write_mask<=0;release_pending<=0;event_slot<=0;event_key<=60;event_layer<=0;event_gain<=0;
   context_key<=60;context_layer<=0;context_epoch<=0;context_age<=0;context_strike<=0;context_rise<=0;
   context_damper<=0;context_noise<=0;context_bound<=0;gain_product_q<=0;bound_product_q<=0;rise_product_q<=0;
   bound_loss_q<=0;noise_loss_q<=0;bound_next_q<=0;noise_next_q<=0;rise_next_q<=0;
   for(i=0;i<4;i=i+1)begin damper_loss_q[i]<=0;damper_next_q[i]<=0;end
   frame_bank<=0;frame_epoch<=0;frame_age<=0;frame_gain<=0;frame_noise<=0;frame_rise<=0;frame_weight<=0;
   total_weight<=0;mix_gain<=32768;headroom_gain<=32768;
   voice_sum<=0;mix_sum<=0;scaled_voice<=0;scale_product<=0;offset_product<=0;
   physics_clip<=0;sample_valid<=0;sample_out<=0;deadline_miss<=0;
   curve_number<=0;frame_fraction<=0;random_state<=32'h51a73b19;
   t1<=0;t2<=0;t3<=0;t4<=0;t5<=0;t6<=0;tl1<=0;tl2<=0;tl3<=0;tl4<=0;tl5<=0;tl6<=0;
   ta1<=0;te1<=0;weights2<=0;sh2<=0;sh3<=0;sh4<=0;sh5<=0;
   sin3<=0;cos3<=0;sin4<=0;cos4<=0;sin5<=0;cos5<=0;
   real_dot4<=0;imag_dot4<=0;real_amp5<=0;imag_amp5<=0;real_carrier6<=0;imag_carrier6<=0;
   x1<=0;x2<=0;x3<=0;x4<=0;xl1<=0;xl2<=0;xl3<=0;xl4<=0;
   xa1<=0;xa2<=0;xa3<=0;xa4<=0;xe1<=0;xe2<=0;xe3<=0;xe4<=0;xm1<=0;
   pole_a1<=0;pole_b1<=0;xrr2<=0;xii2<=0;xri2<=0;xir2<=0;
   random_product2<=0;noise_level2<=0;xn2<=0;xn3<=0;real_next3<=0;imag_next3<=0;
   real_state4<=0;imag_state4<=0;x_output4<=0;
   for(i=0;i<12;i=i+1)begin basis_value[i]<=0;real_product3[i]<=0;imag_product3[i]<=0;end
   for(i=0;i<16;i=i+1)begin
    voice_key[i]<=60;layer[i]<=0;epoch[i]<=0;age[i]<=0;strike_gain[i]<=0;rise_gain[i]<=0;
    damper_gain[i]<=32'hffffffff;noise_gain[i]<=32'hffffffff;level_bound[i]<=0;
    previous_output[i]<=0;retrigger_offset[i]<=0;retrigger_left[i]<=0;
   end
  end else begin
   sample_valid<=0;if(sample_tick&&state!=IDLE)deadline_miss<=1;
   t1<=tonal_issue;t2<=t1;t3<=t2;t4<=t3;t5<=t4;t6<=t5;
   tl2<=tl1;tl3<=tl2;tl4<=tl3;tl5<=tl4;tl6<=tl5;
   if(tonal_issue)begin ta1<=phase_address;te1<=frame_epoch;tl1<=mode==15;end
   if(t1)begin weights2<=weights1;sh2<=frequency1[31:27];end
   if(t2)begin
    for(j=0;j<12;j=j+1)begin
     real_product3[j]<=$signed(weights2[j*8+:8])*basis_value[j];
     imag_product3[j]<=$signed(weights2[(j+12)*8+:8])*basis_value[j];
    end
    sh3<=sh2;sin3<=sin2;cos3<=cos2;
   end
   if(t3)begin real_dot4<=real_sum3;imag_dot4<=imag_sum3;sh4<=sh3;sin4<=sin3;cos4<=cos3;end
   if(t4)begin real_amp5<=(PANEL_PITCH&&panel_mute4)?32'sd0:shifted_real4>>>11;imag_amp5<=(PANEL_PITCH&&panel_mute4)?32'sd0:shifted_imag4>>>11;sin5<=sin4;cos5<=cos4;sh5<=sh4;end
   if(t5)begin real_carrier6<=real_amp5*cos5;imag_carrier6<=imag_amp5*sin5;end
   if(t6)begin
    voice_sum<=voice_sum+tonal_value;
    if(tl6)begin mode<=0;state<=TRANS;end
   end
   x1<=transient_issue;x2<=x1;x3<=x2;x4<=x3;
   if(transient_issue)begin
    xa1<=x_address;xe1<=frame_epoch;xm1<=mode;xl1<=mode==11;
    case(mode)
     8:begin pole_a1<=58036;pole_b1<=6869;end
     9:begin pole_a1<=51789;pole_b1<=21452;end
     10:begin pole_a1<=31071;pole_b1<=40493;end
     11:begin pole_a1<= -23480;pole_b1<=40668;end
     default:begin pole_a1<=0;pole_b1<=0;end
    endcase
    random_state<={random_state[30:0],random_state[31]^random_state[21]^random_state[1]^random_state[0]};
   end
   if(x1)begin
    xa2<=xa1;xe2<=xe1;xl2<=xl1;
    xrr2<=x_real*(xm1<8?$signed(transient1[63:47]):pole_a1);
    xii2<=x_imag*(xm1<8?$signed(transient1[46:30]):pole_b1);
    xri2<=x_real*(xm1<8?$signed(transient1[46:30]):pole_b1);
    xir2<=x_imag*(xm1<8?$signed(transient1[63:47]):pole_a1);
    random_product2<=noise_amplitude*$signed(random_state[31:16]);noise_level2<=frame_noise;xn2<=xm1>=8;
   end
   if(x2)begin
    xa3<=xa2;xe3<=xe2;xl3<=xl2;xn3<=xn2;
    real_next3<=$signed({{2{xrr2[48]}},xrr2})-$signed({{2{xii2[48]}},xii2})+(xn2?(stochastic_wide>>>7):51'sd0);
    imag_next3<=$signed({{2{xri2[48]}},xri2})+$signed({{2{xir2[48]}},xir2});
   end
   if(x3)begin
    xa4<=xa3;xe4<=xe3;xl4<=xl3;
    real_state4<=next_real[31:0];imag_state4<=next_imag[31:0];
    if(next_real>35'sd2147483647||next_real< -35'sd2147483648||next_imag>35'sd2147483647||next_imag< -35'sd2147483648)physics_clip<=1;
    x_output4<=$signed(next_real[31:0])*$signed({1'b0,(xn3?16'd65535:frame_rise)});
   end
   if(x4)begin voice_sum<=voice_sum+transient_value;if(xl4)state<=SCALE;end
   case(state)
    IDLE:if(sample_tick)begin voice<=0;mix_sum<=0;total_weight<=0;state<=PREP;end
    PREP:begin
     context_key<=voice_key[voice];context_layer<=layer[voice];context_epoch<=epoch[voice];context_age<=age[voice];
     context_strike<=strike_gain[voice];context_rise<=rise_gain[voice];
     context_damper<=damper_gain[voice];context_noise<=noise_gain[voice];context_bound<=level_bound[voice];
     state<=CONTROL;
    end
    CONTROL:begin
     gain_product_q<=frame_gain_product;bound_product_q<=bound_product;rise_product_q<=rise_product;
     bound_loss_q<=bound_loss;noise_loss_q<=noise_loss;
     damper_loss_q[0]<=(context_damper>>10)+1'b1;damper_loss_q[1]<=(context_damper>>11)+1'b1;
     damper_loss_q[2]<=(context_damper>>12)+1'b1;damper_loss_q[3]<=(context_damper>>13)+1'b1;
     state<=FRAME;
    end
    FRAME:begin
     bound_next_q<=context_bound>bound_loss_q?context_bound-bound_loss_q:32'd0;
     noise_next_q<=context_noise>noise_loss_q?context_noise-noise_loss_q:32'd0;
     for(i=0;i<4;i=i+1)damper_next_q[i]<=context_damper>damper_loss_q[i]?context_damper-damper_loss_q[i]:32'd0;
     rise_next_q<=context_rise>=65512?16'd65535:context_rise+(rise_product_q>>16)+1'b1;
     frame_bank<=voice_bank;frame_epoch<=context_epoch;frame_age<=context_age;
     frame_gain<=gain_product_q>>15;frame_noise<=context_noise[31:16];frame_rise<=context_rise;
     frame_weight<=voice_active[voice]?weight_now:5'd0;frame_fraction<=curve_fraction;
     voice_sum<=0;curve_number<=0;mode<=0;
     if(voice_active[voice])state<=CURVE_WAIT;
     else begin scaled_voice<=0;offset_product<=0;state<=ADD;end
    end
    CURVE_WAIT:begin curve0<=curve_read;state<=CURVE;end
    CURVE:begin
     basis_value[curve_number]<=curve_interp[11:0];
     if(curve_number==11)state<=TONAL;else curve_number<=curve_number+1'b1;
    end
    TONAL:if(mode==15)state<=TWAIT;else mode<=mode+1'b1;
    TWAIT:begin end
    TRANS:if(mode==11)state<=XWAIT;else mode<=mode+1'b1;
    XWAIT:begin end
    SCALE:begin
     scale_product<=voice_sum*$signed({1'b0,frame_gain});
     offset_product<=retrigger_offset[voice]*$signed({1'b0,retrigger_left[voice]});
     state<=ADD;
     scaled_voice<=0;
    end
    ADD:begin
     if(voice_active[voice]&&frame_matches)begin
      mix_sum<=mix_sum+(scale_product>>>16)+(offset_product>>>6);
      previous_output[voice]<=clip24((scale_product>>>16)+(offset_product>>>6));
      total_weight<=total_weight+frame_weight;age[voice]<=frame_age+1'b1;
      if(retrigger_left[voice]!=0)retrigger_left[voice]<=retrigger_left[voice]-1'b1;
      noise_gain[voice]<=noise_next_q;rise_gain[voice]<=rise_next_q;level_bound[voice]<=bound_next_q;
      if(context_key<90&&pedal_level<4&&!key_down[voice])damper_gain[voice]<=damper_next_q[pedal_level[1:0]];
      if(frame_age>=598016||context_damper<65536||context_bound<65536)voice_active[voice]<=0;
     end else if(voice_active[voice]&&!frame_matches)begin
      mix_sum<=mix_sum+$signed(previous_output[voice]);total_weight<=total_weight+frame_weight;
     end
     if(voice==15)state<=GAIN;else begin voice<=voice+1'b1;state<=PREP;end
    end
    GAIN:begin
     mix_gain<=headroom_gain<headroom_target?headroom_gain:headroom_target;
     if(headroom_gain>headroom_target)headroom_gain<=headroom_target;
     else if(headroom_gain<headroom_target)headroom_gain<=headroom_gain+(((headroom_target-headroom_gain)>>10)+1'b1);
     state<=OUTPUT;
    end
    OUTPUT:begin sample_out<=clip24(mix_product>>>15);sample_valid<=1;state<=IDLE;end
    default:state<=IDLE;
   endcase
   if(parameters_loaded&&epoch[loaded_voice]==loaded_epoch&&(key_down[loaded_voice]||pedal_level==4||voice_key[loaded_voice]>=90))voice_active[loaded_voice]<=1;
   // One cycle of event decode isolates UART/poly-mode fanout from voice CEs.
   release_pending<=note_off||(note_on&&velocity==0);
   event_key<=safe_key;event_slot<=new_slot;
   event_layer<=velocity<48?0:(velocity<80?1:(velocity<112?2:3));event_gain<=velocity_rom[velocity];
   note_write_mask<=0;
   if(note_on&&velocity!=0&&!memory_fault)begin
    note_write_mask<=16'b1<<new_slot;
    allocation_slot<=poly_mode?allocation_slot+1'b1:4'd0;
   end
   for(i=0;i<16;i=i+1)begin
    if(release_pending&&voice_active[i]&&voice_key[i]==event_key)key_down[i]<=0;
    if(note_write_mask[i])begin
     voice_active[i]<=0;key_down[i]<=1;voice_key[i]<=event_key;layer[i]<=event_layer;
     epoch[i]<=epoch[i]+1'b1;age[i]<=0;strike_gain[i]<=event_gain;
     damper_gain[i]<=32'hffffffff;noise_gain[i]<=32'hffffffff;level_bound[i]<=32'h7fffffff;rise_gain[i]<=0;
     retrigger_offset[i]<=voice_active[i]?previous_output[i]:24'sd0;
     retrigger_left[i]<=voice_active[i]?7'd64:7'd0;
    end
   end
   if(memory_fault||!bank_ready)begin voice_active<=0;end
  end
 end
endmodule

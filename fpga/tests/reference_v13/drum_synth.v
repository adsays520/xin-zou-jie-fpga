// Algorithmic percussion. No recorded samples, one-shot ROM or PCM playback.
// A shared mathematical sine ROM evaluates six phase oscillators per voice.
// Modal shell + filtered PRNG noise + independent exponential envelopes.
`include "src/drums/drum_parameter_bank.v"
module drum_synth_v13_reference(
    input wire clk,rst_n,sample_tick,panic,
    input wire hit,input wire [3:0] hit_voice,input wire [6:0] hit_velocity,
    input wire hit2,input wire [3:0] hit2_voice,input wire [6:0] hit2_velocity,
    input wire [1:0] kit,
    input wire level_we,input wire [3:0] level_voice,input wire [6:0] level_value,
    output reg sample_valid,output wire signed [23:0] sample_l,sample_r,
    output wire active,output reg deadline_miss,output reg clipped,
    input wire parameter_load_begin,parameter_byte_valid,parameter_chunk_valid,parameter_load_commit,parameter_load_error,
    input wire [7:0] parameter_byte_data,input wire [10:0] parameter_chunk_index,
    output wire parameter_load_ready,output wire [10:0] parameter_chunk_count,
    output wire parameter_initialized,parameter_fault,parameter_active_bank
);
    reg signed [15:0] sine[0:1023];
    initial begin
        $readmemh("src/drums/rom/sine.hex",sine);
    end
    (* syn_ramstyle="block_ram" *) reg [31:0] phase[0:71];
    reg [31:0] phase_ram_read;
    reg [23:0] body_env[0:11],noise_env[0:11];
    reg [31:0] pitch_env[0:11],rng[0:11];
    reg signed [19:0] low[0:11],dc[0:11];
    reg signed [28:0] previous_voice[0:11],strike_origin[0:11];
    reg signed [28:0] start_sample;
    reg signed [35:0] attack_product,origin_product;
    reg striking;
    reg [16:0] age[0:11];
    reg [6:0] levels[0:11],pending_velocity[0:11];
    reg [11:0] pending;
    reg hat_choked;
    reg [3:0] voice,osc;
    reg [4:0] state;
    reg [6:0] phase_base;
    reg [8:0] param_base;
    reg [23:0] env_b,env_n;
    reg [31:0] pitch,random;
    reg [16:0] voice_age;
    reg signed [19:0] lp,hp,wave_b,wave_n,tone_sum,metal_sum,noise_exciter;
    reg [31:0] config_word;
    reg signed [15:0] sine_data;
    wire [31:0] phase_read_reg=striking?32'd0:phase_ram_read;
    reg [31:0] phase_step_reg,phase_next_reg;
    reg signed [43:0] product;
    reg signed [28:0] body_sample,voice_sample;
    reg signed [36:0] level_product;
    reg signed [31:0] mix_l,mix_r;
    reg [6:0] voice_level;
    wire kick_valid,kick_active;
    wire signed [31:0] kick_sample;
    wire kick_parameter_enable;
    wire [9:0] kick_parameter_address;
    wire [31:0] parameter_read_data;
    kick_modal #(.EXTERNAL_PARAMETERS(1)) u_kick(.clk(clk),.rst_n(rst_n),.clear(panic),
        .start(state==1&&voice==0),.strike(pending[0]),.velocity(pending_velocity[0]),
        .kit(kit),.valid(kick_valid),.sample(kick_sample),.active(kick_active),
        .parameter_read_enable(kick_parameter_enable),.parameter_address(kick_parameter_address),.parameter_data(parameter_read_data));
    reg drum_parameter_enable;
    reg [9:0] drum_parameter_address;
    always @*begin
        drum_parameter_enable=0;drum_parameter_address=0;
        case(state)
            24:begin drum_parameter_enable=1;drum_parameter_address={1'b0,kit,voice,3'b110};end
            1:if(voice!=0)begin drum_parameter_enable=1;drum_parameter_address={1'b0,kit,voice,3'b111};end
            2:begin drum_parameter_enable=1;drum_parameter_address={1'b0,param_base};end
            4:if(osc<5)begin drum_parameter_enable=1;drum_parameter_address={1'b0,param_base}+{6'd0,osc}+10'd1;end
            default:begin end
        endcase
    end
    drum_parameter_bank u_parameters(.clk(clk),.rst_n(rst_n),.boundary(sample_tick&&state==0),
        .read_enable(drum_parameter_enable||kick_parameter_enable),
        .read_address(kick_parameter_enable?kick_parameter_address:drum_parameter_address),.read_data(parameter_read_data),
        .load_begin(parameter_load_begin),.byte_valid(parameter_byte_valid),.chunk_valid(parameter_chunk_valid),
        .load_commit(parameter_load_commit),.load_error(parameter_load_error),.byte_data(parameter_byte_data),
        .chunk_index(parameter_chunk_index),.load_ready(parameter_load_ready),.chunk_count(parameter_chunk_count),
        .initialized(parameter_initialized),.fault(parameter_fault),.active_bank(parameter_active_bank));
    wire peak_valid,peak_safety;
    performance_peak_control u_peak(.clk(clk),.rst_n(rst_n),.clear(panic),
        .start(state==12),.sample_l(mix_l),.sample_r(mix_r),
        .valid(peak_valid),.safety_hit(peak_safety),.out_l(sample_l),.out_r(sample_r));
    integer i;
    wire [31:0] rng_x1=random^(random<<13);
    wire [31:0] rng_x2=rng_x1^(rng_x1>>17);
    wire [31:0] next_rng=rng_x2^(rng_x2<<5);
    wire signed [19:0] raw_noise={{4{random[31]}},random[31:16]};
    // The six non-harmonic square modes share the high-pass path with the
    // noise. Sending their low fundamentals straight to the bus sounded like
    // a pitched pipe, especially on hats. Each voice retains its own filter.
    wire cymbal_voice=(voice==2||voice==3||voice==5||voice==6);
    // Start cymbals with noise, then bring in metallic modes gradually. The
    // tail keeps the established high-pass texture and decay.
    wire signed [19:0] exciter_next=cymbal_voice?
        raw_noise+((voice_age<17'd960) ? 20'sd0 :
                   (voice_age<17'd1920) ? (metal_sum>>>3) : (metal_sum>>>1)):
        raw_noise;
    wire signed [19:0] lp_next=lp+((noise_exciter-lp)>>>config_word[15:12]);
    // Separate clock cycles for the two poles. Preserve each 20-bit rounding
    // boundary, while avoiding two variable shifts and subtracts in one path.
    wire signed [19:0] hp_next=hp+((lp-hp)>>>config_word[19:16]);
    wire signed [19:0] band_noise=lp-hp;
    wire signed [19:0] bright_noise=noise_exciter-lp;
    wire [31:0] oscillator_step=parameter_read_data+((osc==0)?pitch:32'd0);
    wire signed [19:0] modal_term={{4{sine_data[15]}},sine_data};
    // The kick has its own impulse-excited resonator core. These modes serve other drums.
    wire signed [19:0] weighted_mode=(osc==0)?modal_term:(osc==1)?(modal_term>>>1):(modal_term>>>3);
    wire signed [19:0] square_term=phase_next_reg[31]?-20'sd8192:20'sd8192;
    wire signed [31:0] scaled_voice=$signed(level_product>>>10);
    // Kick +7.04 dB, snare +4.86 dB, other voices +1.94 dB over v5.
    // Wide arithmetic is retained through the stereo accumulation.
    wire signed [31:0] balanced_voice=(voice==0)?
        (scaled_voice<<<1)+(scaled_voice>>>2):
        (voice==1)?scaled_voice+(scaled_voice>>>1)+(scaled_voice>>>2):scaled_voice+(scaled_voice>>>2);
    wire [5:0] attack_fraction=(voice_age<32)?voice_age[5:0]:6'd32;
    function [23:0] leak;
        input [23:0] e;input [3:0] shift;
        begin leak=(e<256||shift==0)?24'd0:e-((e>>shift)+24'd1);end
    endfunction
    wire [11:0] live;
    genvar g;
    generate for(g=0;g<12;g=g+1)begin: live_voices
        assign live[g]=(g==0)?kick_active:((body_env[g]!=0)||(noise_env[g]!=0));
    end endgenerate
    assign active=|live;
    always @(posedge clk)begin
        if(rst_n&&!panic)begin
            if(state==3)phase_ram_read<=phase[phase_base+osc];
            if(state==17)phase[phase_base+osc]<=phase_next_reg;
        end
    end
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin
            state<=0;voice<=0;osc<=0;phase_base<=0;param_base<=0;
            pending<=0;hat_choked<=0;sample_valid<=0;
            deadline_miss<=0;clipped<=0;mix_l<=0;mix_r<=0;
            env_b<=0;env_n<=0;pitch<=0;random<=1;voice_age<=0;lp<=0;hp<=0;
            wave_b<=0;wave_n<=0;tone_sum<=0;metal_sum<=0;noise_exciter<=0;config_word<=0;
            sine_data<=0;phase_step_reg<=0;phase_next_reg<=0;
            product<=0;body_sample<=0;voice_sample<=0;level_product<=0;voice_level<=0;
            start_sample<=0;attack_product<=0;origin_product<=0;striking<=0;
            for(i=0;i<12;i=i+1)begin
                body_env[i]<=0;noise_env[i]<=0;pitch_env[i]<=0;
                rng[i]<=32'h13579bdf+i*32'h193875ad;
                low[i]<=0;dc[i]<=0;age[i]<=0;levels[i]<=100;pending_velocity[i]<=0;
                previous_voice[i]<=0;strike_origin[i]<=0;
            end
        end else begin
            sample_valid<=0;
            if(peak_safety)clipped<=1;
            if(hit&&hit_voice<12&&hit_velocity!=0)begin
                pending[hit_voice]<=1;pending_velocity[hit_voice]<=hit_velocity;
                // Closed hat chokes the open hat, including a queued hit.
                if(hit_voice==3)hat_choked<=0;
                if(hit_voice==2)begin pending[3]<=0;hat_choked<=1;end
            end
            if(hit2&&hit2_voice<12&&hit2_velocity!=0)begin
                pending[hit2_voice]<=1;pending_velocity[hit2_voice]<=hit2_velocity;
                if(hit2_voice==3)hat_choked<=0;
                if(hit2_voice==2)begin pending[3]<=0;hat_choked<=1;end
            end
            if(level_we&&level_voice<12)levels[level_voice]<=level_value;
            if(panic)begin
                pending<=0;hat_choked<=0;state<=0;sample_valid<=1;
                for(i=0;i<12;i=i+1)begin body_env[i]<=0;noise_env[i]<=0;previous_voice[i]<=0;strike_origin[i]<=0;end
            end else begin
                if(sample_tick&&state!=0)deadline_miss<=1;
                case(state)
                    0:if(sample_tick)begin voice<=0;mix_l<=0;mix_r<=0;state<=24;end
                    24:state<=1;
                    1:begin
                        phase_base<=voice*6;param_base<={kit,voice,3'b000};
                        random<=rng[voice];voice_level<=levels[voice];
                        lp<=low[voice];hp<=dc[voice];voice_age<=age[voice];
                        striking<=0;start_sample<=strike_origin[voice];
                        if(voice==3&&hat_choked)begin env_b<=body_env[voice]>>1;env_n<=noise_env[voice]>>1;pitch<=0;pending[3]<=0;end
                        else if(pending[voice])begin
                            env_b<={pending_velocity[voice],16'd0};
                            env_n<={pending_velocity[voice],16'd0};
                            pitch<=parameter_read_data;
                            voice_age<=0;lp<=0;hp<=0;
                            // Reset modes at the strike and crossfade from the exact
                            // preceding output; initial hits start at zero, retriggers stay continuous.
                            striking<=1;start_sample<=previous_voice[voice];
                            strike_origin[voice]<=previous_voice[voice];
                            if(!(hit&&hit_voice==voice)&&!(hit2&&hit2_voice==voice))pending[voice]<=0;
                        end else begin env_b<=body_env[voice];env_n<=noise_env[voice];pitch<=pitch_env[voice];end
                        state<=2;
                        if(!pending[voice]&&body_env[voice]==0&&noise_env[voice]==0)state<=20;
                        if(voice==0)state<=23;
                    end
                    2:begin config_word<=parameter_read_data;osc<=0;tone_sum<=0;metal_sum<=0;state<=3;end
                    // The dynamic phase-bank read, frequency lookup, addition
                    // and write are split across clocks. Six oscillators per
                    // voice still complete well before the next 48 kHz tick.
                    3:begin
                        phase_step_reg<=oscillator_step;
                        state<=16;
                    end
                    16:begin phase_next_reg<=phase_read_reg+phase_step_reg;state<=17;end
                    17:begin
                        sine_data<=sine[phase_next_reg[31:22]];
                        state<=4;
                    end
                    4:begin
                        tone_sum<=tone_sum+weighted_mode;
                        metal_sum<=metal_sum+square_term;
                        if(osc==5)state<=5;else begin osc<=osc+1'b1;state<=3;end
                    end
                    5:begin noise_exciter<=exciter_next;random<=next_rng;state<=13;end
                    13:begin lp<=lp_next;state<=14;end
                    14:begin hp<=hp_next;state<=15;end
                    15:begin
                        case(voice)
                            0:begin wave_b<=0;wave_n<=0;end // handled by u_kick
                            1:begin wave_b<=tone_sum>>>1;wave_n<=band_noise;end
                            2,3:begin
                                wave_b<=0;
                                wave_n<=voice_age<17'd480 ? (hp+(lp>>>1)) :
                                    voice_age<17'd960 ? lp :
                                    voice_age<17'd1440 ? band_noise :
                                    voice_age<17'd1920 ? ((band_noise+bright_noise)>>>1) : bright_noise;
                            end
                            4:begin wave_b<=0;wave_n<=band_noise;end
                            5:begin
                                wave_b<=voice_age<17'd960 ? 20'sd0 :
                                    voice_age<17'd1920 ? (tone_sum>>>7) : (tone_sum>>>6);
                                wave_n<=voice_age<17'd480 ? (hp+(lp>>>1)) :
                                    voice_age<17'd960 ? lp :
                                    voice_age<17'd1440 ? band_noise :
                                    voice_age<17'd1920 ? ((band_noise+bright_noise)>>>1) :
                                    bright_noise+(band_noise>>>1);
                            end
                            6:begin
                                wave_b<=voice_age<17'd960 ? 20'sd0 :
                                    voice_age<17'd1920 ? (tone_sum>>>6) : (tone_sum>>>5);
                                wave_n<=voice_age<17'd480 ? (hp+(lp>>>1)) :
                                    voice_age<17'd960 ? lp :
                                    voice_age<17'd1440 ? band_noise :
                                    voice_age<17'd1920 ? ((band_noise+bright_noise)>>>1) :
                                    bright_noise+(band_noise>>>1);
                            end
                            7,8,9:begin wave_b<=tone_sum;wave_n<=band_noise>>>2;end
                            10:begin wave_b<=tone_sum;wave_n<=band_noise>>>1;end
                            11:begin wave_b<=tone_sum>>>1;wave_n<=band_noise>>>3;end
                            default:begin wave_b<=0;wave_n<=0;end
                        endcase
                        // Independent clap bursts at 0/10/20/30 ms, then noise tail.
                        if(voice==4&&voice_age<1440)begin
                            if(voice_age==480||voice_age==960)env_n<=env_b;
                            else env_n<=leak(env_n,4'd7);
                        end
                        state<=6;
                    end
                    6:begin product<=wave_b*$signed({1'b0,env_b});state<=7;end
                    7:begin body_sample<=product>>>15;product<=wave_n*$signed({1'b0,env_n});state<=8;end
                    8:begin voice_sample<=body_sample+(product>>>15);state<=9;end
                    9:begin
                        // Smooth 0.67 ms strike transition, without staircase gain jumps.
                        attack_product<=voice_sample*$signed({1'b0,attack_fraction});
                        state<=18;
                    end
                    18:begin origin_product<=start_sample*$signed(7'd32-{1'b0,attack_fraction});state<=19;end
                    19:begin voice_sample<=(attack_product+origin_product)>>>5;state<=10;end
                    10:begin level_product<=voice_sample*$signed({1'b0,voice_level});state<=11;end
                    11:begin
                        // Keep wide sums; linked lookahead gain protects simultaneous strikes.
                        mix_l<=mix_l+((voice==3||voice==6||voice==9)?(balanced_voice>>>1):balanced_voice);
                        mix_r<=mix_r+((voice==2||voice==5||voice==7)?(balanced_voice>>>1):balanced_voice);
                        previous_voice[voice]<=voice_sample;
                        body_env[voice]<=leak(env_b,config_word[3:0]);
                        noise_env[voice]<=leak(env_n,config_word[7:4]);
                        pitch_env[voice]<=pitch-(pitch>>config_word[11:8]);
                        rng[voice]<=random;low[voice]<=lp;dc[voice]<=hp;
                        if(voice_age<131071)age[voice]<=voice_age+1'b1;
                        if(voice==11)state<=12;else begin voice<=voice+1'b1;state<=24;end
                    end
                    20:begin
                        previous_voice[voice]<=0;
                        if(voice==11)state<=12;else begin voice<=voice+1'b1;state<=24;end
                    end
                    12:begin
                        state<=21;
                    end
                    23:if(kick_valid)begin voice_sample<=kick_sample;state<=10;end
                    21:if(peak_valid)begin sample_valid<=1;state<=0;end
                    default:state<=0;
                endcase
            end
        end
    end
endmodule

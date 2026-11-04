// Shared post-mix guitar effects, 50 MHz / 48 kHz. Never in a string feedback
// loop. Clean/disabled top-level mux remains bit-exact to the success_v4 path.
module guitar_fx(
    input wire clk,rst_n,sample_tick,history_clear,input wire signed [23:0] sample_in,
    input wire [4:0] amp,input wire [6:0] drive,tone,level,mix,rate,depth,threshold,
    input wire [2:0] modulation,flags,input wire changed,
    output reg output_valid,output reg signed [23:0] sample_out,
    output wire bypass,electric_source,output reg deadline_miss
);
    reg [4:0] a;reg [6:0] dr,to,le,mi,ra,de,th;reg [2:0] mo,fl;
    reg pending,clearing;
    reg [1:0] transition;
    reg [8:0] fade;
    reg [6:0] warmup;
    reg [5:0] state;
    reg signed [23:0] x,raw,dry,wet;
    reg signed [23:0] dry_history[0:31];
    reg [4:0] dry_wp;
    reg [5:0] dry_filled;
    reg [23:0] envelope,peak,gate_threshold;
    reg [10:0] gate_hold;
    reg [15:0] gate_gain,comp_gain;
    reg [17:0] level_gain,level_rom[0:2047];
    reg [15:0] comp_rom[0:1023];
    reg [23:0] gate_rom[0:127];
    initial begin
        $readmemh("src/effects/rom/fx_level.hex",level_rom);
        $readmemh("src/effects/rom/fx_gate.hex",gate_rom);
        $readmemh("src/effects/rom/fx_compressor.hex",comp_rom);
    end
    reg signed [47:0] p,pdry,pwet;
    reg [30:0] wah_motion;
    reg bq_start,os_start,mod_start,lim_start;
    reg [3:0] section;
    reg [11:0] bq_address;
    wire bq_done,os_done,mod_done,lim_done;
    wire signed [23:0] bq_out,os_out,mod_out,lim_out;
    wire [7:0] mix_gain=mi==127?8'd128:{1'b0,mi};
    assign bypass=(a==0&&mo==0&&!fl[1]&&!fl[2]&&transition==0&&!pending);
    assign electric_source=(a!=0);
    wire processing_clear=clearing||history_clear;
    guitar_fx_biquad u_eq(.clk(clk),.rst_n(rst_n),.clear(processing_clear),.start(bq_start),
        .section(section),.coefficient_base(bq_address),.sample_in(x),.done(bq_done),.sample_out(bq_out));
    guitar_fx_oversample u_os(.clk(clk),.rst_n(rst_n),.clear(processing_clear),.start(os_start),
        .amp(a),.drive(dr),.sample_in(x),.done(os_done),.sample_out(os_out));
    guitar_fx_modulation u_mod(.clk(clk),.rst_n(rst_n),.clear(processing_clear),.start(mod_start),
        .mode(mo),.rate(ra),.depth(de),.sample_in(x),.done(mod_done),.sample_out(mod_out));
    wire signed [31:0] level_sample=$signed(p)>>>15;
    guitar_fx_peak_control u_peak(.clk(clk),.rst_n(rst_n),.clear(processing_clear),.start(lim_start),
        .sample_in(level_sample),.done(lim_done),.sample_out(lim_out));
    function signed [23:0] sat24;
        input signed [51:0] v;
        begin sat24=v>8388607?24'sh7fffff:v< -8388608?24'sh800000:v[23:0];end
    endfunction
    wire [9:0] comp_index=envelope>=1048576?10'd1023:envelope[19:10];
    wire [15:0] comp_target=comp_rom[comp_index];
    wire signed [17:0] comp_delta=$signed({1'b0,comp_target})-$signed({1'b0,comp_gain});
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin
            a<=0;dr<=64;to<=64;le<=80;mi<=127;ra<=40;de<=64;th<=32;mo<=0;fl<=0;
            pending<=0;clearing<=0;transition<=0;fade<=256;warmup<=0;state<=0;
            x<=0;raw<=0;dry<=0;wet<=0;dry_wp<=0;dry_filled<=0;envelope<=0;peak<=0;
            gate_threshold<=0;gate_hold<=0;gate_gain<=0;comp_gain<=32768;level_gain<=0;
            p<=0;pdry<=0;pwet<=0;wah_motion<=0;bq_start<=0;os_start<=0;mod_start<=0;lim_start<=0;section<=0;bq_address<=0;
            output_valid<=0;sample_out<=0;deadline_miss<=0;
        end else begin
            output_valid<=0;bq_start<=0;os_start<=0;mod_start<=0;lim_start<=0;clearing<=0;
            if(changed)pending<=1;
            if(sample_tick&&state!=0)deadline_miss<=1;
            if(history_clear)begin
                state<=0;sample_out<=0;dry_filled<=0;envelope<=0;gate_gain<=0;gate_hold<=0;
                if(!bypass)begin transition<=2;fade<=0;warmup<=64;end
            end else case(state)
                0:if(sample_tick)begin
                    raw<=sample_in>>>3;x<=sample_in>>>3;
                    peak<=sample_in[23]?(-$signed({sample_in[23],sample_in})>>>3):($signed(sample_in)>>>3);
                    dry<=dry_filled==32?dry_history[dry_wp]:24'sd0;
                    dry_history[dry_wp]<=sample_in>>>3;dry_wp<=dry_wp+1'b1;
                    if(dry_filled<32)dry_filled<=dry_filled+1'b1;
                    gate_threshold<=gate_rom[th];level_gain<=level_rom[{a[3:0],le}];
                    if(pending&&transition==0)begin transition<=1;pending<=0;end
                    if(transition==1)begin
                        if(fade!=0)fade<=fade-1'b1;
                        else begin
                            a<=amp;dr<=drive;to<=tone;le<=level;mi<=mix;ra<=rate;de<=depth;th<=threshold;mo<=modulation;fl<=flags;
                            clearing<=1;transition<=2;warmup<=64;
                            envelope<=0;gate_gain<=0;gate_hold<=0;comp_gain<=32768;dry_filled<=0;
                        end
                    end else if(transition==2)begin
                        if(warmup!=0)warmup<=warmup-1'b1;
                        else if(fade<256)fade<=fade+1'b1;
                        else transition<=0;
                    end
                    if((transition==1&&fade==0)||warmup!=0)begin sample_out<=0;output_valid<=1;end
                    else if(bypass)begin sample_out<=sample_in;output_valid<=1;end
                    else if(a==0&&mo==0&&!fl[1]&&!fl[2])begin
                        p<=sample_in*$signed({1'b0,fade});state<=21;
                    end
                    else state<=1;
                end
                1:begin
                    if(peak>envelope)envelope<=envelope+((peak-envelope+7)>>3);
                    else envelope<=envelope-((envelope-peak+2047)>>11);
                    if(!fl[1])gate_gain<=32768;
                    else if(peak>gate_threshold)begin gate_hold<=960;gate_gain<=gate_gain>=30720?16'd32768:gate_gain+16'd2048;end
                    else if(gate_hold!=0)gate_hold<=gate_hold-1'b1;
                    else if(envelope<(gate_threshold>>1))gate_gain<=gate_gain>16?gate_gain-16'd16:16'd0;
                    if(!fl[2])comp_gain<=32768;
                    else comp_gain<=$signed({1'b0,comp_gain})+(comp_delta>>>6);
                    state<=2;
                end
                2:begin p<=x*$signed({1'b0,gate_gain});state<=3;end
                3:begin x<=sat24(p>>>15);section<=0;state<=4;end
                4:begin
                    if(a!=0)begin
                        bq_address<={1'd0,a[3:0],7'd0}+(section==10?12'd72:{5'd0,section,3'd0});
                        bq_start<=1;state<=5;
                    end
                    else begin state<=10;end
                end
                5:if(bq_done)begin
                    x<=bq_out;
                    if(section==10)state<=6;
                    else begin section<=section==2?4'd10:section+1'b1;state<=4;end
                end
                6:begin os_start<=1;state<=7;end
                7:if(os_done)begin x<=os_out;section<=3;state<=8;end
                8:begin
                    if(section==8)bq_address<=12'd2048+{6'd0,to[6:4],3'd0};
                    else bq_address<={1'd0,a[3:0],7'd0}+(section==11?12'd80:{5'd0,section,3'd0});
                    bq_start<=1;state<=9;
                end
                9:if(bq_done)begin
                    x<=bq_out;
                    if(section==8)state<=10;
                    else if(section==4)begin section<=fl[0]?4'd11:4'd8;state<=8;end
                    else if(section==11)begin section<=5;state<=8;end
                    else begin section<=section+1'b1;state<=8;end
                end
                10:begin
                    if(mo==5)begin
                        wah_motion<=envelope*de;state<=22;
                    end else state<=12;
                end
                11:if(bq_done)begin x<=bq_out;state<=12;end
                12:begin
                    // Align dry and wet before modulation. No comb from mismatched
                    // FIR delay; frequency-dependent pre/post EQ phase remains.
                    pdry<=(a==0?raw:dry)*$signed({1'b0,8'd128-mix_gain});
                    pwet<=x*$signed({1'b0,mix_gain});state<=13;
                end
                13:begin x<=sat24(($signed(pdry)+$signed(pwet))>>>7);state<=14;end
                14:begin mod_start<=1;state<=15;end
                15:if(mod_done)begin x<=mod_out;state<=16;end
                16:begin p<=x*$signed({1'b0,comp_gain});state<=17;end
                17:begin x<=sat24(p>>>15);state<=18;end
                18:begin p<=x*$signed({1'b0,level_gain});state<=19;end
                19:begin lim_start<=1;state<=23;end
                23:if(lim_done)begin p<=lim_out*$signed({1'b0,fade});state<=20;end
                20:begin sample_out<=sat24(p>>>5);output_valid<=1;state<=0;end
                21:begin sample_out<=sat24(p>>>8);output_valid<=1;state<=0;end
                22:begin
                    section<=9;
                    bq_address<=12'd2112+{5'd0,(wah_motion>=67108864?4'd15:wah_motion[25:22]),3'd0};
                    bq_start<=1;state<=11;
                end
                default:state<=0;
            endcase
        end
    end
endmodule

// 32-frame lookahead peak control. Q11.20 input retains Level/EQ headroom;
// a held peak controls a smooth gain instead of hard-clipping each audio peak
// at 48 kHz (which generated new, unfiltered high-frequency harmonics).
// Serial division reuses one subtractor, 35 clocks per audio frame.
module guitar_fx_peak_control(
    input wire clk,rst_n,clear,start,input wire signed [31:0] sample_in,
    output reg done,output reg signed [23:0] sample_out
);
    // Different read/write addresses force supported simple-dual-port RAM.
    // A 32-entry same-address ring inferred unsupported GW5A SP READ_FIRST.
    reg signed [31:0] history[0:63],delayed;
    reg [5:0] wp;
    reg [5:0] filled,state,step;
    reg [31:0] peak,divisor;
    reg signed [31:0] input_q;
    reg [31:0] magnitude_q,decay_q,next_peak_q;
    reg [32:0] falling_difference;
    reg [34:0] dividend,quotient;
    reg [32:0] remainder;
    reg [15:0] gain;
    reg signed [48:0] product;
    reg safety_hit;
    wire [31:0] magnitude=sample_in[31]?-sample_in:sample_in;
    wire [31:0] decay=(peak>>12)+1'b1;
    wire [31:0] falling=peak>decay?peak-decay:32'd0;
    wire [31:0] next_peak=magnitude>falling?magnitude:falling;
    wire [33:0] trial={remainder,dividend[34]};
    wire hit=trial>={2'd0,divisor};
    wire [15:0] target=quotient[15:0];
    wire [16:0] closing={1'b0,gain}-{1'b0,target};
    wire [16:0] opening={1'b0,target}-{1'b0,gain};
    wire [15:0] next_gain=target<gain ? gain-((closing+17'd3)>>2)
        :gain+((opening+17'd4095)>>12);
    wire signed [48:0] rounded=product+(product[48]?49'sd16383:49'sd16384);
    wire signed [48:0] scaled=rounded>>>15;
    // Single synchronous RAM read/write; filled prevents stale data after clear.
    always @(posedge clk)if(start&&state==0&&!clear)begin
        history[wp]<=sample_in;
        delayed<=filled==32?history[wp-6'd32]:32'sd0;
    end
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin
            wp<=0;filled<=0;state<=0;step<=0;peak<=0;divisor<=1;
            input_q<=0;magnitude_q<=0;decay_q<=0;next_peak_q<=0;falling_difference<=0;
            dividend<=0;quotient<=0;remainder<=0;gain<=32768;
            product<=0;done<=0;sample_out<=0;safety_hit<=0;
        end else begin
            done<=0;safety_hit<=0;
            if(clear)begin
                wp<=0;filled<=0;state<=0;peak<=0;gain<=32768;sample_out<=0;
            end else case(state)
                0:if(start)begin
                    wp<=wp+1'b1;if(filled<32)filled<=filled+1'b1;
                    input_q<=sample_in;
                    // (0.75 * 2^20) * 2^15, hence target <= unity Q15.
                    dividend<=35'd25769803776;quotient<=0;remainder<=0;step<=0;state<=4;
                end
                4:begin magnitude_q<=input_q[31]?-input_q:input_q;decay_q<=(peak>>12)+1'b1;state<=5;end
                5:begin falling_difference<={1'b0,peak}-{1'b0,decay_q};state<=6;end
                6:begin next_peak_q<=falling_difference[32]||magnitude_q>falling_difference[31:0]?magnitude_q:falling_difference[31:0];state<=7;end
                7:begin peak<=next_peak_q;divisor<=next_peak_q<786432?32'd786432:next_peak_q;state<=1;end
                1:begin
                    remainder<=hit?trial-{2'd0,divisor}:trial;
                    dividend<={dividend[33:0],1'b0};quotient<={quotient[33:0],hit};
                    if(step==34)state<=2;else step<=step+1'b1;
                end
                2:begin gain<=next_gain;product<=delayed*$signed({1'b0,next_gain});state<=3;end
                3:begin
                    sample_out<=scaled>943718?24'sd943718:scaled< -943718?-24'sd943718:scaled[23:0];
                    safety_hit<=scaled>943718||scaled< -943718;
                    done<=1;state<=0;
                end
                default:state<=0;
            endcase
        end
    end
endmodule

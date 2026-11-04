// Stereo post-mix chorus and feedback delay. The memories hold live audio;
// they contain no recorded sound or drum samples. Both effects default off.
module master_space_fx_pre_ddr(
    input wire clk,rst_n,sample_tick,changed,
    input wire signed [23:0] sample_l,sample_r,
    input wire [6:0] chorus_mix,chorus_rate,chorus_depth,
    input wire [6:0] delay_mix,delay_time,delay_feedback,
    output wire bypass,
    output reg output_valid,output reg signed [23:0] output_l,output_r,
    output reg deadline_miss
);
    reg signed [15:0] sine[0:1023];
    initial $readmemh("src/effects/rom/fx_lfo.hex",sine);
    reg signed [15:0] chorus_line_l[0:2047],chorus_line_r[0:2047];
    reg signed [15:0] delay_line_l[0:32767],delay_line_r[0:32767];
    reg [10:0] chorus_wp,chorus_filled;
    reg [14:0] delay_wp,delay_filled,delay_samples;
    reg [31:0] phase;
    reg signed [15:0] lfo;
    reg signed [31:0] motion,offset_l_q8,offset_r_q8;
    reg signed [23:0] dry_l,dry_r,chorused_l,chorused_r;
    reg signed [15:0] ch0_l,ch0_r,ch1_l,ch1_r,delayed_l,delayed_r;
    reg signed [23:0] chorus_wet_l,chorus_wet_r,delay_wet_l,delay_wet_r;
    reg signed [33:0] mix_product_l,mix_product_r,feedback_product_l,feedback_product_r;
    reg [3:0] state;
    wire [14:0] selected_delay=15'd2400+({8'd0,delay_time}<<8)-({8'd0,delay_time}<<5);
    wire [6:0] safe_feedback=delay_feedback>7'd96 ? 7'd96 : delay_feedback;
    assign bypass=(chorus_mix==0&&delay_mix==0);

    function signed [23:0] sat24;
        input signed [34:0] x;
        begin
            if(x>35'sd8388607)sat24=24'sh7fffff;
            else if(x< -35'sd8388608)sat24=24'sh800000;
            else sat24=x[23:0];
        end
    endfunction

    // The two stereo memories infer simple dual-port BSRAM. Each channel has
    // one read and one write port; no whole-array reset or PCM initialization.
    always @(posedge clk)begin
        if(rst_n&&state==1)begin
            chorus_line_l[chorus_wp]<=dry_l[23:8];
            chorus_line_r[chorus_wp]<=dry_r[23:8];
        end
        if(state==3)begin
            ch0_l<=chorus_line_l[chorus_wp-offset_l_q8[18:8]];
            ch0_r<=chorus_line_r[chorus_wp-offset_r_q8[18:8]];
        end
        if(state==4)begin
            ch1_l<=chorus_line_l[chorus_wp-offset_l_q8[18:8]-11'd1];
            ch1_r<=chorus_line_r[chorus_wp-offset_r_q8[18:8]-11'd1];
        end
        if(state==7)begin
            delayed_l<=delay_line_l[delay_wp-delay_samples];
            delayed_r<=delay_line_r[delay_wp-delay_samples];
        end
        if(rst_n&&state==10)begin
            delay_line_l[delay_wp]<=sat24(feedback_product_l>>>7)>>>8;
            delay_line_r[delay_wp]<=sat24(feedback_product_r>>>7)>>>8;
        end
    end

    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin
            chorus_wp<=0;chorus_filled<=0;delay_wp<=0;delay_filled<=0;
            delay_samples<=2400;phase<=0;lfo<=0;motion<=0;
            offset_l_q8<=0;offset_r_q8<=0;dry_l<=0;dry_r<=0;
            chorused_l<=0;chorused_r<=0;chorus_wet_l<=0;chorus_wet_r<=0;
            delay_wet_l<=0;delay_wet_r<=0;mix_product_l<=0;mix_product_r<=0;
            feedback_product_l<=0;feedback_product_r<=0;
            output_l<=0;output_r<=0;output_valid<=0;deadline_miss<=0;state<=0;
        end else begin
            output_valid<=0;
            if(sample_tick&&state!=0)deadline_miss<=1;
            if(changed)begin
                chorus_filled<=0;delay_filled<=0;
            end
            case(state)
                0:if(sample_tick)begin
                    dry_l<=sample_l;dry_r<=sample_r;
                    lfo<=sine[phase[31:22]];
                    phase<=phase+32'd17896+chorus_rate*32'd5495;
                    delay_samples<=selected_delay;
                    state<=1;
                end
                1:begin
                    motion<=lfo*$signed({1'b0,chorus_depth});
                    chorus_wp<=chorus_wp+1'b1;
                    if(chorus_filled<2047)chorus_filled<=chorus_filled+1'b1;
                    state<=2;
                end
                2:begin
                    // 16 ms center, at most +/-2.65 ms; opposite stereo
                    // excursions preserve movement without mono pitch wobble.
                    offset_l_q8<=32'sd196608+(motion>>>7);
                    offset_r_q8<=32'sd196608-(motion>>>7);
                    state<=3;
                end
                3:state<=4;
                4:state<=5;
                5:begin
                    chorus_wet_l<=chorus_filled>=offset_l_q8[18:8] ?
                        ($signed(ch0_l)+((($signed(ch1_l)-$signed(ch0_l))*$signed({1'b0,offset_l_q8[7:0]}))>>>8))<<<8 : 24'sd0;
                    chorus_wet_r<=chorus_filled>=offset_r_q8[18:8] ?
                        ($signed(ch0_r)+((($signed(ch1_r)-$signed(ch0_r))*$signed({1'b0,offset_r_q8[7:0]}))>>>8))<<<8 : 24'sd0;
                    state<=6;
                end
                6:begin
                    chorused_l<=sat24((($signed(dry_l)*$signed({1'b0,8'd128-{1'b0,chorus_mix}}))+
                        ($signed(chorus_wet_l)*$signed({1'b0,chorus_mix})))>>>7);
                    chorused_r<=sat24((($signed(dry_r)*$signed({1'b0,8'd128-{1'b0,chorus_mix}}))+
                        ($signed(chorus_wet_r)*$signed({1'b0,chorus_mix})))>>>7);
                    state<=7;
                end
                7:state<=8;
                8:begin
                    delay_wet_l<=delay_filled>=delay_samples ? $signed(delayed_l)<<<8 : 24'sd0;
                    delay_wet_r<=delay_filled>=delay_samples ? $signed(delayed_r)<<<8 : 24'sd0;
                    state<=9;
                end
                9:begin
                    mix_product_l<=$signed(chorused_l)*$signed({1'b0,8'd128-{1'b0,delay_mix}})+
                        $signed(delay_wet_l)*$signed({1'b0,delay_mix});
                    mix_product_r<=$signed(chorused_r)*$signed({1'b0,8'd128-{1'b0,delay_mix}})+
                        $signed(delay_wet_r)*$signed({1'b0,delay_mix});
                    feedback_product_l<=($signed(chorused_l)<<<7)+
                        $signed(delay_wet_l)*$signed({1'b0,safe_feedback});
                    feedback_product_r<=($signed(chorused_r)<<<7)+
                        $signed(delay_wet_r)*$signed({1'b0,safe_feedback});
                    state<=10;
                end
                10:begin
                    output_l<=sat24(mix_product_l>>>7);
                    output_r<=sat24(mix_product_r>>>7);
                    output_valid<=1;
                    delay_wp<=delay_wp+1'b1;
                    if(delay_filled<32767)delay_filled<=delay_filled+1'b1;
                    state<=0;
                end
                default:state<=0;
            endcase
        end
    end
endmodule

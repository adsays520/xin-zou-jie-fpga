// 4x polyphase bandlimited interpolation, two nonlinear stages at 192 kHz,
// 129-tap anti-alias FIR then decimation. This is NOT linear interpolation or
// a post-clip lowpass masquerading as oversampling. One MAC reused for FIRs.
// Q3.20 signals; FIR Q1.17, drive Q7.10; 48-bit MAC, rounded on reduction.
module guitar_fx_oversample(
    input wire clk,rst_n,clear,start,input wire [4:0] amp,input wire [6:0] drive,
    input wire signed [23:0] sample_in,
    output reg done,output reg signed [23:0] sample_out
);
    reg signed [17:0] up_rom[0:128],down_rom[0:128],tanh_rom[0:512];
    reg [17:0] gain_rom[0:2047];
    initial begin
        $readmemh("src/effects/rom/fx_fir_up.hex",up_rom);
        $readmemh("src/effects/rom/fx_fir_down.hex",down_rom);
        $readmemh("src/effects/rom/fx_gain.hex",gain_rom);
        $readmemh("src/effects/rom/fx_tanh.hex",tanh_rom);
    end
    reg signed [23:0] history[0:63],out_history[0:255];
    reg [5:0] wp,read_pos;
    reg [7:0] op,out_pos,tap;
    reg [1:0] phase;
    reg [4:0] state,amp_q;
    reg down,second,negative;
    reg [8:0] init_count;
    reg [9:0] table_index;
    reg [12:0] fraction;
    reg signed [23:0] x,operand;
    // Q3.28 histories: a Q20 /256 snap formerly changed the high-pass
    // into a differentiator during quiet tails, with a large gain discontinuity.
    reg signed [31:0] inter_low,inter_high;
    reg signed [17:0] coefficient,v0,v1;
    reg signed [41:0] product,drive_product;
    reg signed [47:0] accumulator;
    reg signed [31:0] interpolation;
    reg [17:0] gain1,gain2;
    reg signed [23:0] bias,bias_dc;
    wire signed [47:0] mac=accumulator+$signed(product);
    wire signed [47:0] fir_rounded=mac[47]?mac+48'sd65535:mac+48'sd65536;
    wire signed [31:0] driven=($signed(drive_product)>>>10)+$signed(bias);
    wire [31:0] magnitude=driven[31]?-driven:driven;
    wire signed [31:0] interpolated=($signed(v0)<<<13)+interpolation;
    wire signed [23:0] curve_value=interpolated>>>9; // Q16 + 13 -> Q20
    wire signed [23:0] shaped=(negative?-curve_value:curve_value)-bias_dc;
    wire signed [31:0] inter_input={x,8'd0};
    wire signed [32:0] high_delta=$signed(inter_input)-$signed(inter_high);
    wire signed [33:0] low_delta=$signed(inter_input)-$signed(inter_high)-$signed(inter_low);
    wire signed [32:0] inter_rounded=$signed(inter_low)+(inter_low[31]?33'sd127:33'sd128);
    function signed [23:0] sat24;
        input signed [47:0] value;
        begin sat24=value>8388607?24'sh7fffff:value< -8388608?24'sh800000:value[23:0];end
    endfunction
    function [17:0] stage_gain;
        input [4:0] a;
        begin case(a)
            1:stage_gain=1126;2:stage_gain=1843;3:stage_gain=2867;4:stage_gain=3584;
            5:stage_gain=4096;6:stage_gain=3072;7:stage_gain=1024;8:stage_gain=1331;
            9:stage_gain=4096;10:stage_gain=4608;default:stage_gain=1024;
        endcase end
    endfunction
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin
            state<=20;init_count<=0;wp<=0;op<=0;read_pos<=0;out_pos<=0;tap<=0;phase<=0;
            down<=0;second<=0;negative<=0;done<=0;sample_out<=0;
            x<=0;operand<=0;inter_low<=0;inter_high<=0;coefficient<=0;v0<=0;v1<=0;
            product<=0;drive_product<=0;accumulator<=0;interpolation<=0;
            gain1<=1024;gain2<=1024;bias<=0;bias_dc<=0;table_index<=0;fraction<=0;amp_q<=0;
        end else begin
            done<=0;
            if(clear)begin state<=20;init_count<=0;wp<=0;op<=0;inter_low<=0;inter_high<=0;end
            else case(state)
                20:begin
                    out_history[init_count[7:0]]<=0;
                    if(init_count<64)history[init_count[5:0]]<=0;
                    if(init_count==255)state<=0;else init_count<=init_count+1'b1;
                end
                0:if(start)begin
                    history[wp]<=sample_in;read_pos<=wp;wp<=wp+1'b1;
                    amp_q<=amp;gain1<=gain_rom[{amp[3:0],drive}];gain2<=stage_gain(amp);
                    phase<=0;tap<=0;accumulator<=0;down<=0;state<=1;
                end
                1:begin
                    operand<=down?out_history[out_pos]:history[read_pos];
                    coefficient<=down?down_rom[tap]:up_rom[tap];state<=2;
                end
                2:begin product<=operand*coefficient;state<=3;end
                3:begin
                    accumulator<=mac;
                    if((down&&tap==128)||(!down&&tap>=125))begin
                        x<=sat24(fir_rounded>>>17);
                        if(down)begin sample_out<=sat24(fir_rounded>>>17);done<=1;state<=0;end
                        else begin second<=0;state<=4;end
                    end else begin
                        tap<=tap+(down?8'd1:8'd4);read_pos<=read_pos-1'b1;out_pos<=out_pos-1'b1;state<=1;
                    end
                end
                4:begin
                    // Offset tanh adds even harmonics. Subtract f(b), followed by
                    // interstage/output DC filtering. Fuzz intentionally stronger.
                    bias<=amp_q==5?24'sd262144:((amp_q==3||amp_q==4)?24'sd131072:24'sd0);
                    bias_dc<=amp_q==5?24'sd256816:((amp_q==3||amp_q==4)?24'sd130400:24'sd0);
                    drive_product<=x*$signed(second?gain2:gain1);state<=5;
                end
                5:begin
                    negative<=driven[31];
                    table_index<=magnitude>=4194304?10'd512:{1'b0,magnitude[21:13]};
                    fraction<=magnitude>=4194304?13'd0:magnitude[12:0];state<=6;
                end
                6:begin
                    v0<=tanh_rom[table_index];v1<=tanh_rom[table_index==512?table_index:table_index+1'b1];state<=7;
                end
                7:begin interpolation<=($signed(v1)-$signed(v0))*$signed({1'b0,fraction});state<=8;end
                8:begin
                    if(!second)begin
                        // Octave rectification takes place BEFORE the anti-alias FIR.
                        x<=amp_q==6?(shaped[23]?-shaped:shaped):shaped;state<=9;
                    end else begin out_history[op]<=shaped;op<=op+1'b1;state<=11;end
                end
                9:begin
                    // ~60 Hz coupling HP and ~4.1 kHz interstage LP at 192 kHz.
                    // Tiny-delta handling is below the external signal LSB now.
                    inter_high<=high_delta<512&&high_delta> -512?inter_input:
                        inter_high+((high_delta+(high_delta[32]?33'sd511:33'sd0))>>>9);
                    inter_low<=low_delta<8&&low_delta> -8?inter_input-inter_high:
                        inter_low+((low_delta+(low_delta[33]?34'sd7:34'sd0))>>>3);state<=10;
                end
                10:begin x<=inter_rounded>>>8;second<=1;state<=4;end
                11:begin
                    if(phase==3)begin
                        // Decimate phase zero, matching exactly 32 base-rate frames
                        // of FIR group delay (64+64)/4. Dry mix uses the same delay.
                        out_pos<=op-4;tap<=0;down<=1;accumulator<=0;state<=1;
                    end else begin
                        phase<=phase+1'b1;tap<={6'd0,phase}+1'b1;
                        read_pos<=wp-1'b1;accumulator<=0;state<=1;
                    end
                end
                default:state<=0;
            endcase
        end
    end
endmodule

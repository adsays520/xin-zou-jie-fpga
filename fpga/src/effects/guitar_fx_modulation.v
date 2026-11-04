// Rate 0.2..8 Hz; true sine LFO, fractional-delay vibrato/flanger, 4 allpasses.
// Auto-wah itself uses section 9 of the shared biquad in the parent engine.
module guitar_fx_modulation(
    input wire clk,rst_n,clear,start,input wire [2:0] mode,
    input wire [6:0] rate,depth,input wire signed [23:0] sample_in,
    output reg done,output reg signed [23:0] sample_out
);
    reg signed [15:0] sine[0:1023];
    initial $readmemh("src/effects/rom/fx_lfo.hex",sine);
    reg signed [23:0] delay_line[0:2047];
    reg signed [23:0] ap_x[0:3],ap_y[0:3];
    reg [10:0] wp,rp,filled;
    reg [31:0] phase;
    reg signed [15:0] lfo;
    reg signed [23:0] x,delayed,d0,d1;
    reg signed [31:0] motion,delay_q8;
    reg signed [47:0] product;
    reg [7:0] fraction;
    reg signed [17:0] gain,ap_a;
    reg [1:0] section;
    reg [4:0] state;
    integer i;
    wire [10:0] read_address=state==5 ? wp-delay_q8[18:8] : rp-11'd1;
    reg signed [23:0] delay_read;
    // One synchronous read port + one write port. Two neighboring samples are
    // fetched on successive clocks; never infer a 2-read 49152-flop delay mux.
    always @(posedge clk)begin
        if(rst_n&&!clear&&state==2&&(mode==2||mode==4))
            delay_line[wp]<=mode==4?sat24($signed(x)+($signed(delayed)>>>2)):x;
        delay_read<=delay_line[read_address];
    end
    wire signed [48:0] mod_result=$signed(d0)+($signed(product)>>>8);
    function signed [23:0] sat24;
        input signed [48:0] v;
        begin sat24=v>8388607?24'sh7fffff:v< -8388608?24'sh800000:v[23:0];end
    endfunction
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin
            wp<=0;rp<=0;filled<=0;phase<=0;lfo<=0;x<=0;delayed<=0;d0<=0;d1<=0;
            motion<=0;delay_q8<=0;product<=0;fraction<=0;gain<=0;ap_a<=0;section<=0;state<=0;done<=0;sample_out<=0;
            for(i=0;i<4;i=i+1)begin ap_x[i]<=0;ap_y[i]<=0;end
        end else begin
            done<=0;
            if(clear)begin
                state<=0;wp<=0;filled<=0;phase<=0;delayed<=0;
                for(i=0;i<4;i=i+1)begin ap_x[i]<=0;ap_y[i]<=0;end
            end else case(state)
                0:if(start)begin
                    x<=sample_in;lfo<=sine[phase[31:22]];
                    phase<=phase+32'd17896+rate*32'd5495;state<=1;
                end
                1:begin motion<=$signed(lfo)*$signed({1'b0,depth});state<=2;end
                2:begin
                    if(mode==1)begin gain<=32768-({11'd0,depth}<<7)+(motion>>>8);state<=3;end
                    else if(mode==2||mode==4)begin
                        delay_q8<=mode==2?32'sd122880+(motion>>>7):32'sd28672+(motion>>>8);
                        if(filled<2047)filled<=filled+1'b1;
                        state<=5;
                    end else if(mode==3)begin
                        ap_a<=22000+(motion>>>9);section<=0;state<=11;
                    end else begin sample_out<=x;done<=1;state<=0;end
                end
                3:begin product<=x*gain;state<=4;end
                4:begin sample_out<=sat24(product>>>15);done<=1;state<=0;end
                5:begin rp<=wp-delay_q8[18:8];fraction<=delay_q8[7:0];state<=6;end
                6:begin d0<=filled>delay_q8[18:8]+1?delay_read:24'sd0;state<=7;end
                7:begin d1<=filled>delay_q8[18:8]+1?delay_read:24'sd0;state<=8;end
                8:begin product<=($signed(d1)-$signed(d0))*$signed({1'b0,fraction});state<=9;end
                9:begin delayed<=sat24(mod_result);state<=10;end
                10:begin
                    sample_out<=mode==2?delayed:sat24(($signed(x)+$signed(delayed))>>>1);
                    done<=1;state<=0;wp<=wp+1'b1;
                end
                11:begin product<=($signed(ap_y[section])-$signed(x))*$signed(ap_a);state<=12;end
                12:begin d0<=sat24($signed(ap_x[section])+($signed(product)>>>15));state<=13;end
                13:begin
                    ap_x[section]<=x;ap_y[section]<=d0;x<=d0;
                    if(section==3)begin sample_out<=sat24(($signed(sample_in)+$signed(d0))>>>1);done<=1;state<=0;end
                    else begin section<=section+1'b1;state<=11;end
                end
                default:state<=0;
            endcase
        end
    end
endmodule

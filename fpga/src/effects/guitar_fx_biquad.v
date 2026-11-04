// Shared direct-form I biquad. Q3.20 signal and Q3.20 coefficients; 52-bit sum.
// Five parallel pipelined multipliers, only ONE section evaluated at a time.
module guitar_fx_biquad(
    input wire clk,rst_n,clear,start,input wire [3:0] section,
    input wire [11:0] coefficient_base,input wire signed [23:0] sample_in,
    output reg done,output reg signed [23:0] sample_out
);
    reg [119:0] rom[0:287];
    initial $readmemh("src/effects/rom/fx_biquad_packed.hex",rom);
    // Eight fractional guard bits on feedback state avoid low-frequency
    // fixed-point idle tones/DC (rounding a 65 Hz HP at Q20 is insufficient).
    reg signed [31:0] x1[0:11],x2[0:11],y1[0:11],y2[0:11];
    reg signed [31:0] x;
    reg signed [23:0] b0,b1,b2,a1,a2;
    reg signed [55:0] p0,p1,p2,p3,p4;
    reg signed [59:0] total;
    reg [3:0] s;reg [2:0] state;integer i;
    wire signed [59:0] rounded=total[59]?total+60'sd524287:total+60'sd524288;
    wire signed [59:0] shifted=rounded>>>20;
    wire signed [31:0] result=shifted>60'sd2147483647 ? 32'sh7fffffff:
        shifted< -60'sd2147483648 ? 32'sh80000000:shifted[31:0];
    wire signed [32:0] final_round=$signed(result)+(result[31]?33'sd127:33'sd128);
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin
            state<=0;done<=0;sample_out<=0;s<=0;x<=0;
            b0<=0;b1<=0;b2<=0;a1<=0;a2<=0;p0<=0;p1<=0;p2<=0;p3<=0;p4<=0;total<=0;
            for(i=0;i<12;i=i+1)begin x1[i]<=0;x2[i]<=0;y1[i]<=0;y2[i]<=0;end
        end else begin
            done<=0;
            if(clear)begin
                state<=0;sample_out<=0;
                for(i=0;i<12;i=i+1)begin x1[i]<=0;x2[i]<=0;y1[i]<=0;y2[i]<=0;end
            end else case(state)
                0:if(start)begin
                    x<={sample_in,8'd0};s<=section;
                    {a2,a1,b2,b1,b0}<=rom[coefficient_base[11:3]];state<=1;
                end
                1:begin p0<=x*b0;p1<=x1[s]*b1;p2<=x2[s]*b2;p3<=y1[s]*a1;p4<=y2[s]*a2;state<=2;end
                2:begin total<=$signed(p0)+$signed(p1)+$signed(p2)+$signed(p3)+$signed(p4);state<=3;end
                3:begin
                    sample_out<=final_round>33'sd2147483647 ? 24'sh7fffff:final_round>>>8;done<=1;state<=0;
                    x2[s]<=x1[s];x1[s]<=x;y2[s]<=y1[s];y1[s]<=result;
                end
                default:state<=0;
            endcase
        end
    end
endmodule

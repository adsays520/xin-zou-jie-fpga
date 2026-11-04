// Atomic guitar FX configuration. A5 40..43 stage; A5 44 00 00 00 XOR commits.
// Never interpret SOF-like audio/table payload bytes as control frames.
module guitar_fx_control #(parameter integer PACKET_IDLE_CLKS=2500000)(
    input wire clk,rst_n,byte_valid,input wire [7:0] byte_data,
    output reg [4:0] amp,output reg [6:0] drive,tone,level,mix,rate,depth,threshold,
    output reg [2:0] modulation,flags,output reg changed
);
    reg [2:0] state;
    reg [7:0] cmd,p0,p1,p2,check;
    reg [5:0] count;
    reg [$clog2(PACKET_IDLE_CLKS+1)-1:0] idle;
    reg [20:0] a,b,c;
    reg [6:0] d;
    reg [3:0] seen;
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin
            state<=0;cmd<=0;p0<=0;p1<=0;p2<=0;check<=0;count<=0;idle<=0;
            amp<=0;drive<=64;tone<=64;level<=80;mix<=127;rate<=40;depth<=64;
            threshold<=32;modulation<=0;flags<=0;changed<=0;
            a<=0;b<=0;c<=0;d<=0;seen<=0;
        end else begin
            changed<=0;
            if(byte_valid||state==0)idle<=0;
            else if(idle<PACKET_IDLE_CLKS)idle<=idle+1'b1;
            if(!byte_valid&&state!=0&&idle==PACKET_IDLE_CLKS)begin state<=0;seen<=0;end
            else if(byte_valid)case(state)
                0:if(byte_data==8'ha5)begin check<=8'ha5;state<=1;end
                1:begin
                    cmd<=byte_data;check<=check^byte_data;count<=0;
                    if(byte_data==8'h11||byte_data==8'h21||byte_data==8'h31)begin
                        count<=36;state<=4;
                    end else state<=2;
                end
                2:begin
                    if(count==0)p0<=byte_data;
                    if(count==1)p1<=byte_data;
                    if(count==2)p2<=byte_data;
                    check<=check^byte_data;
                    if(count==2)state<=3;else count<=count+1'b1;
                end
                3:begin
                    state<=0;
                    if(byte_data==check)case(cmd)
                        8'h40:begin
                            seen<=0;
                            if(p0<=10&&p1<128&&p2<128)begin a<={p0[6:0],p1[6:0],p2[6:0]};seen<=1;end
                        end
                        8'h41:if(seen==1&&p0<128&&p1<128&&p2<8)begin b<={p0[6:0],p1[6:0],p2[6:0]};seen<=3;end else seen<=0;
                        8'h42:if(seen==3&&p0<=5&&p1<128&&p2<128)begin c<={p0[6:0],p1[6:0],p2[6:0]};seen<=7;end else seen<=0;
                        8'h43:if(seen==7&&p0<128&&p1==0&&p2==0)begin d<=p0[6:0];seen<=15;end else seen<=0;
                        8'h44:begin
                            if(seen==15&&{p0,p1,p2}==0)begin
                                amp<=a[18:14];drive<=a[13:7];tone<=a[6:0];
                                level<=b[20:14];mix<=b[13:7];flags<=b[2:0];
                                modulation<=c[16:14];rate<=c[13:7];depth<=c[6:0];threshold<=d;
                                changed<=1;
                            end
                            seen<=0;
                        end
                        default:begin end
                    endcase
                    else if(cmd>=8'h40&&cmd<=8'h44)seen<=0;
                end
                4:if(count==1)state<=0;else count<=count-1'b1;
                default:state<=0;
            endcase
        end
    end
endmodule

// Atomic stereo bus effects control: A5 60/61/62, three payload bytes + XOR.
// Both stages must arrive in order before commit. The effects default to off.
module master_space_fx_control #(parameter integer PACKET_IDLE_CLKS=2500000)(
    input wire clk,rst_n,byte_valid,input wire [7:0] byte_data,
    output reg [6:0] chorus_mix,chorus_rate,chorus_depth,
    output reg [6:0] delay_mix,delay_time,delay_feedback,
    output reg changed
);
    reg [2:0] state;
    reg [7:0] cmd,p0,p1,p2,check;
    reg [5:0] count;
    reg [$clog2(PACKET_IDLE_CLKS+1)-1:0] idle;
    reg [20:0] staged_chorus,staged_delay;
    reg [1:0] seen;
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n)begin
            state<=0;cmd<=0;p0<=0;p1<=0;p2<=0;check<=0;count<=0;idle<=0;
            staged_chorus<=0;staged_delay<=0;seen<=0;
            chorus_mix<=0;chorus_rate<=40;chorus_depth<=40;
            delay_mix<=0;delay_time<=42;delay_feedback<=35;changed<=0;
        end else begin
            changed<=0;
            if(byte_valid||state==0)idle<=0;
            else if(idle<PACKET_IDLE_CLKS)idle<=idle+1'b1;
            if(!byte_valid&&state!=0&&idle==PACKET_IDLE_CLKS)begin state<=0;seen<=0;end
            else if(byte_valid)case(state)
                0:if(byte_data==8'ha5)begin check<=8'ha5;state<=1;end
                1:begin
                    cmd<=byte_data;check<=check^byte_data;count<=0;
                    // ROM/envelope uploads may contain apparent control bytes.
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
                        8'h60:begin
                            seen<=0;
                            if(p0<128&&p1<128&&p2<128)begin
                                staged_chorus<={p0[6:0],p1[6:0],p2[6:0]};seen<=1;
                            end
                        end
                        8'h61:begin
                            if(seen==1&&p0<128&&p1<128&&p2<128)begin
                                staged_delay<={p0[6:0],p1[6:0],p2[6:0]};seen<=2;
                            end else seen<=0;
                        end
                        8'h62:begin
                            if(seen==2&&{p0,p1,p2}==0)begin
                                chorus_mix<=staged_chorus[20:14];
                                chorus_rate<=staged_chorus[13:7];
                                chorus_depth<=staged_chorus[6:0];
                                delay_mix<=staged_delay[20:14];
                                delay_time<=staged_delay[13:7];
                                delay_feedback<=staged_delay[6:0];changed<=1;
                            end
                            seen<=0;
                        end
                        default:begin end
                    endcase
                    else if(cmd>=8'h60&&cmd<=8'h62)seen<=0;
                end
                4:if(count==1)state<=0;else count<=count-1'b1;
                default:state<=0;
            endcase
        end
    end
endmodule

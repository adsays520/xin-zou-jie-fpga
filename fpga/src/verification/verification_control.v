// Compatible A5 six-byte commands. Bulk waveform/envelope payloads are skipped
// in full so embedded A5/82 byte patterns cannot accidentally start a test.
module verification_control #(
    parameter CLOCK_HZ=50000000
)(
    input wire clk,rst_n,byte_valid,input wire [7:0] byte_data,
    input wire sample_tick,
    output reg running,visual_enable,capture_request,start_event,fast_key_enable,
    output reg [63:0] frequencies,
    output reg [27:0] gains,pans
);
    reg [2:0] state;
    reg [7:0] cmd,p0,p1,p2,check;
    reg [5:0] skip;
    reg [21:0] idle_count;
    reg [15:0] staged_freq[0:3];
    reg [6:0] staged_gain[0:3],staged_pan[0:3];
    reg pending,pending_run;
    integer i;
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            state<=0;cmd<=0;p0<=0;p1<=0;p2<=0;check<=0;skip<=0;
            idle_count<=0;running<=0;visual_enable<=0;capture_request<=0;start_event<=0;fast_key_enable<=0;
            frequencies<=0;gains<=0;pans<=0;pending<=0;pending_run<=0;
            for(i=0;i<4;i=i+1)begin
                staged_freq[i]<=16'd375*(i+1);staged_gain[i]<=0;staged_pan[i]<=64;
            end
        end else begin
            capture_request<=0;start_event<=0;
            if(sample_tick && pending)begin
                running<=pending_run;pending<=0;
                for(i=0;i<4;i=i+1)begin
                    frequencies[i*16+:16]<=staged_freq[i];
                    gains[i*7+:7]<=staged_gain[i];pans[i*7+:7]<=staged_pan[i];
                end
            end
            if(byte_valid || state==0)idle_count<=0;
            else if(idle_count<CLOCK_HZ/20)idle_count<=idle_count+1'b1;
            if(!byte_valid && state!=0 && idle_count==CLOCK_HZ/20)state<=0;
            else if(byte_valid) case(state)
                0:if(byte_data==8'hA5)begin check<=8'hA5;state<=1;end
                1:begin
                    cmd<=byte_data;check<=check^byte_data;
                    if(byte_data==8'h11 || byte_data==8'h21 || byte_data==8'h31)begin skip<=36;state<=7;end
                    else state<=2;
                end
                2:begin p0<=byte_data;check<=check^byte_data;state<=3;end
                3:begin p1<=byte_data;check<=check^byte_data;state<=4;end
                4:begin p2<=byte_data;check<=check^byte_data;state<=5;end
                5:begin
                    state<=0;
                    if(byte_data==check)case(cmd)
                        8'h80:if(p0<4 && {p2,p1}>=50 && {p2,p1}<=5000)staged_freq[p0]<= {p2,p1};
                        8'h81:if(p0<4 && p1<128 && p2<128)begin staged_gain[p0]<=p1[6:0];staged_pan[p0]<=p2[6:0];end
                        8'h82:if(p0<2 && p1==0 && p2==0)begin
                            pending<=1;pending_run<=p0[0];start_event<=p0[0];
                        end
                        8'h83:if(p0==0 && p1==0 && p2==0)capture_request<=1;
                        8'h84:if(p0<2 && p1==0 && p2==0)visual_enable<=p0[0];
                        8'h85:if(p0<2 && p1==0 && p2==0)fast_key_enable<=p0[0];
                    endcase
                end
                7:if(skip==1)state<=0;else skip<=skip-1'b1;
                default:state<=0;
            endcase
        end
    end
endmodule

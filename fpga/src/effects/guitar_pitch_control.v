// Host pitch ratio Q20 (90) and effect enable (91), fixed six-byte XOR frames.
// Control is independent of note/mode flushes, so Riff keeps its modulation.
module guitar_pitch_control(input wire clk,rst_n,byte_valid,
 input wire [7:0] byte_data,output reg [23:0] ratio_q20,output reg enabled);
 reg [2:0] state; reg [7:0] cmd,p0,p1,p2,checksum; reg [5:0] skip;
 reg [21:0] idle;
 wire [23:0] payload={p0,p1,p2};
 always @(posedge clk or negedge rst_n) begin
  if(!rst_n)begin state<=0;cmd<=0;p0<=0;p1<=0;p2<=0;checksum<=0;skip<=0;idle<=0;
   ratio_q20<=24'd1048576;enabled<=0;end
  else begin
   if(byte_valid||state==0)idle<=0;else if(idle<2500000)idle<=idle+1'b1;
   if(!byte_valid&&state!=0&&idle==2500000)state<=0;
   else if(byte_valid)case(state)
    0:if(byte_data==8'ha5)begin checksum<=8'ha5;state<=1;end
    1:begin cmd<=byte_data;checksum<=checksum^byte_data;
      if(byte_data==8'h11||byte_data==8'h21||byte_data==8'h31)begin skip<=36;state<=6;end
      else state<=2;end
    2:begin p0<=byte_data;checksum<=checksum^byte_data;state<=3;end
    3:begin p1<=byte_data;checksum<=checksum^byte_data;state<=4;end
    4:begin p2<=byte_data;checksum<=checksum^byte_data;state<=5;end
    5:begin state<=0;if(byte_data==checksum)begin
      if(cmd==8'h90&&payload>=24'd262144&&payload<=24'd4194304)ratio_q20<=payload;
      if(cmd==8'h91&&p0<=1&&p1==0&&p2==0)enabled<=p0[0];
      if(cmd==8'h04&&(p0==1||p0==2)&&p1==0&&p2==0)begin enabled<=0;ratio_q20<=1048576;end
     end end
    6:if(skip==1)state<=0;else skip<=skip-1'b1;
    default:state<=0;
   endcase
  end
 end
endmodule

// CRC-protected SPI fragments -> one validated packet -> original byte parsers.
// One synchronous RAM read port keeps the 266-byte buffer local to one BSRAM.
module s3_bulk_buffer #(parameter TIMEOUT=50000000)(
 input wire clk,rst_n,input wire [383:0] fragment_data,
 input wire [5:0] fragment_length,input wire [1:0] fragment_flags,
 input wire fragment_valid,output wire fragment_ready,
 output wire request,input wire grant,output wire busy,
 output reg [7:0] data,output reg valid,output wire replaying,
 output reg error
);
 localparam IDLE=0,COPY=1,HEADER=2,CHECK=3,WAIT=4,PLAY=5;
 reg [2:0] state;reg [7:0] memory[0:511];reg [7:0] ram_q,first_byte,opcode,crc_high;
 reg [383:0] fragment;reg [5:0] left;reg last;
 reg [8:0] count,index,expected;reg collecting;
 reg [15:0] crc;reg [31:0] crc32;reg [7:0] parity;reg [1:0] phase;reg [2:0] frame_index;
 reg [$clog2(TIMEOUT+1)-1:0] age;
 wire timed_out=busy&&age==TIMEOUT-1;
 always @(posedge clk)begin
  if(rst_n&&state==COPY&&count<266&&!timed_out)memory[count]<=fragment[383:376];
  ram_q<=memory[index];
 end
 function [15:0] crc_byte;
 input [15:0] c;input [7:0] b;reg [15:0] v;integer k;
 begin v=c^{b,8'd0};for(k=0;k<8;k=k+1)v=v[15]?(v<<1)^16'h1021:v<<1;crc_byte=v;end
 endfunction
 function [31:0] crc32_byte;
 input [31:0] c;input [7:0] b;reg [31:0] v;integer k;
 begin v=c^{24'd0,b};for(k=0;k<8;k=k+1)v=v[0]?(v>>1)^32'hedb88320:v>>1;crc32_byte=v;end
 endfunction
 assign fragment_ready=state==IDLE;
 assign busy=collecting||state!=IDLE;
 assign request=state==WAIT;
 assign replaying=state==PLAY;
 always @(posedge clk or negedge rst_n)begin
  if(!rst_n)begin
   state<=IDLE;count<=0;index<=0;expected<=0;collecting<=0;error<=0;valid<=0;data<=0;phase<=0;age<=0;
   fragment<=0;left<=0;last<=0;crc<=16'hffff;crc32<=32'hffffffff;parity<=0;first_byte<=0;opcode<=0;crc_high<=0;frame_index<=0;
  end else begin
   valid<=0;
   if(busy)begin
    if(timed_out)begin state<=IDLE;collecting<=0;count<=0;error<=1;age<=0;end
    else age<=age+1'b1;
   end else age<=0;
   if(!timed_out)case(state)
    IDLE:if(fragment_valid)begin
     if(fragment_length==0||fragment_length>48||(!fragment_flags[0]&&!collecting))begin error<=1;collecting<=0;count<=0;end
     else begin
      if(fragment_flags[0])begin count<=0;error<=0;end
      collecting<=1;fragment<=fragment_data;left<=fragment_length;last<=fragment_flags[1];state<=COPY;age<=0;
     end
    end
    COPY:begin
     if(count>=266)begin error<=1;state<=IDLE;collecting<=0;count<=0;end
     else begin
      if(count==0)first_byte<=fragment[383:376];
      if(count==1)opcode<=fragment[383:376];
      fragment<={fragment[375:0],8'd0};count<=count+1'b1;left<=left-1'b1;
      if(left==1)state<=last?HEADER:IDLE;
     end
    end
    HEADER:begin
     collecting<=0;index<=0;frame_index<=0;phase<=0;crc<=16'hffff;crc32<=32'hffffffff;parity<=0;
     expected<=opcode==8'hb0 ? 266:(opcode==8'h11||opcode==8'h21||opcode==8'h31) ? 38:count;
     if(first_byte!=8'ha5||count<6)begin error<=1;state<=IDLE;count<=0;end
     else if(opcode!=8'hb0&&opcode!=8'h11&&opcode!=8'h21&&opcode!=8'h31&&
       count!=6&&count!=12&&count!=18&&count!=24&&count!=30&&count!=36)begin error<=1;state<=IDLE;end
     else state<=CHECK;
    end
    CHECK:begin
     phase<=phase==0?1:0;
     if(phase==1)begin
      index<=index+1'b1;
      if(count!=expected)begin error<=1;state<=IDLE;end
      else if(expected==266)begin
       if(index<6)begin
        parity<=parity^ram_q;
        if(index==5&&(parity^ram_q)!=0)begin error<=1;state<=IDLE;end
       end else if(index<262)crc32<=crc32_byte(crc32,ram_q);
       else case(index)
        262:if(ram_q!=(crc32[7:0]^8'hff))begin error<=1;state<=IDLE;end
        263:if(ram_q!=(crc32[15:8]^8'hff))begin error<=1;state<=IDLE;end
        264:if(ram_q!=(crc32[23:16]^8'hff))begin error<=1;state<=IDLE;end
        265:if(ram_q!=(crc32[31:24]^8'hff))begin error<=1;state<=IDLE;end else state<=WAIT;
        default:begin error<=1;state<=IDLE;end
       endcase
      end else if(expected==38)begin
       if(index<36)crc<=crc_byte(crc,ram_q);
       else if(index==36)crc_high<=ram_q;
       else if({crc_high,ram_q}==crc)state<=WAIT;
       else begin error<=1;state<=IDLE;end
      end else begin
       if((frame_index==0&&ram_q!=8'ha5)||(frame_index==1&&(ram_q==8'h11||ram_q==8'h21||ram_q==8'h31||ram_q==8'hb0)))begin error<=1;state<=IDLE;end
       else if(frame_index==5)begin
        frame_index<=0;parity<=0;
        if((parity^ram_q)!=0)begin error<=1;state<=IDLE;end
        else if(index==count-1)state<=WAIT;
       end else begin frame_index<=frame_index+1'b1;parity<=parity^ram_q;end
      end
     end
    end
    WAIT:if(grant)begin state<=PLAY;index<=0;phase<=0;end
    PLAY:begin
     phase<=phase+1'b1;
     // One warm-up cycle for the synchronous read, then one byte per 4 clocks.
     if(phase==1)begin data<=ram_q;valid<=1;index<=index+1'b1;if(index==count-1)begin state<=IDLE;count<=0;end end
    end
    default:state<=IDLE;
   endcase
  end
 end
endmodule


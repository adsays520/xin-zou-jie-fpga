// 32768 stereo S16 frames in DDR. One 256-bit burst stores eight frames.
// A write-combining line and one read line replace 64 blocks of audio RAM.
module stereo_ddr_delay(
 input wire clk,rst_n,memory_ready,transport_fault,clear,
 input wire read_start,read_needed,input wire [14:0] read_addr,
 output reg read_done,output reg signed [15:0] read_l,read_r,
 input wire write_start,input wire [14:0] write_addr,input wire signed [15:0] write_l,write_r,
 output reg write_done,output reg fault,
 output wire req_valid,input wire req_ready,output wire [63:0] req_data,
 input wire rsp_valid,output wire rsp_ready,input wire [63:0] rsp_data
);
 localparam IDLE=0,READ_HEADER=1,READ_DATA=2,READ_RETURN=3,WRITE_HEADER=4,WRITE_DATA=5,WRITE_ACK=6,STOP=7;
 localparam [28:0] BASE=29'h0200000;
 reg [2:0] state;
 reg [255:0] read_line,write_line,payload;
 reg [11:0] read_tag,write_tag;
 reg read_valid;
 reg [7:0] write_mask;
 reg [2:0] read_offset;
 reg [1:0] beat;
 reg [28:0] address;
 wire [31:0] cached_word=read_line[read_addr[2:0]*32+:32];
 wire [31:0] recent_word=write_line[read_addr[2:0]*32+:32];
 wire [31:0] returned_word=read_line[read_offset*32+:32];
 assign req_valid=memory_ready&&!fault&&(state==READ_HEADER||state==WRITE_HEADER||state==WRITE_DATA);
 assign req_data=state==WRITE_DATA?payload[beat*64+:64]:{(state==WRITE_HEADER),34'd0,address};
 assign rsp_ready=state==READ_DATA||state==WRITE_ACK;
 always @(posedge clk or negedge rst_n)begin
  if(!rst_n)begin
   state<=IDLE;read_line<=0;write_line<=0;payload<=0;read_tag<=0;write_tag<=0;
   read_valid<=0;write_mask<=0;read_offset<=0;beat<=0;address<=0;
   read_done<=0;write_done<=0;read_l<=0;read_r<=0;fault<=0;
  end else begin
   read_done<=0;write_done<=0;
   if(transport_fault)begin fault<=1;state<=STOP;read_done<=1;write_done<=1;read_l<=0;read_r<=0;end
   else case(state)
    IDLE:begin
     if(read_start)begin
      if(!memory_ready||fault||!read_needed)begin read_l<=0;read_r<=0;read_done<=1;end
      else if(write_tag==read_addr[14:3]&&write_mask[read_addr[2:0]])begin read_l<=recent_word[15:0];read_r<=recent_word[31:16];read_done<=1;end
      else if(read_valid&&read_tag==read_addr[14:3])begin read_l<=cached_word[15:0];read_r<=cached_word[31:16];read_done<=1;end
      else begin
       read_tag<=read_addr[14:3];read_offset<=read_addr[2:0];
       address<=BASE+{14'd0,read_addr[14:3],3'd0};state<=READ_HEADER;
      end
     end else if(write_start)begin
      if(!memory_ready||fault)write_done<=1;
      else begin
       if(write_tag!=write_addr[14:3])begin
        write_line<=0;write_mask<=8'd1<<write_addr[2:0];
       end else write_mask<=write_mask|(8'd1<<write_addr[2:0]);
       write_tag<=write_addr[14:3];write_line[write_addr[2:0]*32+:32]<={write_r,write_l};
       if(read_tag==write_addr[14:3])read_valid<=0;
       if(write_addr[2:0]==7)begin
        payload<={write_r,write_l,write_line[223:0]};
        address<=BASE+{14'd0,write_addr[14:3],3'd0};state<=WRITE_HEADER;
       end else write_done<=1;
      end
     end
    end
    READ_HEADER:if(req_valid&&req_ready)begin beat<=0;state<=READ_DATA;end
    READ_DATA:if(rsp_valid&&rsp_ready)begin
     read_line[beat*64+:64]<=rsp_data;
     if(beat==3)state<=READ_RETURN;else beat<=beat+1'b1;
    end
    READ_RETURN:begin read_l<=returned_word[15:0];read_r<=returned_word[31:16];read_valid<=1;read_done<=1;state<=IDLE;end
    WRITE_HEADER:if(req_valid&&req_ready)begin beat<=0;state<=WRITE_DATA;end
    WRITE_DATA:if(req_valid&&req_ready)begin if(beat==3)state<=WRITE_ACK;else beat<=beat+1'b1;end
    WRITE_ACK:if(rsp_valid&&rsp_ready)begin
     if(rsp_data!=64'h5049414e4f5f4f4b)begin fault<=1;state<=STOP;write_done<=1;end
     else begin write_done<=1;state<=IDLE;end
    end
    STOP:begin
     if(read_start)begin read_l<=0;read_r<=0;read_done<=1;end
     if(write_start)write_done<=1;
    end
   endcase
   if(clear||!memory_ready)read_valid<=0;
  end
 end
endmodule

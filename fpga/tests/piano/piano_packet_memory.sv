// Test-only external storage model at the ordered 64-bit packet boundary.
// The transport's clock crossing and native DDR handshakes have a separate test.
module piano_packet_memory(
 input wire clk,rst_n,input wire req_valid,output wire req_ready,input wire [63:0] req_data,
 output reg rsp_valid,input wire rsp_ready,output reg [63:0] rsp_data
);
 reg [255:0] memory[0:8799];
 reg [255:0] payload;
 reg [2:0] state;
 reg [1:0] beat;
 reg [13:0] index;
 integer writes=0,reads=0;
 assign req_ready=state==0||state==1;
 always @(posedge clk or negedge rst_n)begin
  if(!rst_n)begin state<=0;beat<=0;index<=0;payload<=0;rsp_valid<=0;rsp_data<=0;end
  else begin
   if(rsp_valid&&rsp_ready)rsp_valid<=0;
   case(state)
    0:if(req_valid&&req_ready)begin
     if(req_data[28:0]<29'h100000||req_data[28:0]>=29'h111300||req_data[2:0]!=0)
      $fatal(1,"parameter DDR address %h",req_data[28:0]);
     index<=(req_data[28:0]-29'h100000)>>3;beat<=0;
     if(req_data[63])state<=1;else begin state<=3;reads<=reads+1;end
    end
    1:if(req_valid&&req_ready)begin
     payload[beat*64+:64]<=req_data;
     if(beat==3)state<=2;else beat<=beat+1'b1;
    end
    2:begin memory[index]<=payload;writes<=writes+1;rsp_data<=64'h5049414e4f5f4f4b;rsp_valid<=1;state<=5;end
    3:begin payload<=memory[index];state<=4;end
    4:if(!rsp_valid||rsp_ready)begin
     rsp_data<=payload[beat*64+:64];rsp_valid<=1;
     if(beat==3)state<=5;else beat<=beat+1'b1;
    end
    5:if(rsp_valid&&rsp_ready)state<=0;
   endcase
  end
 end
endmodule

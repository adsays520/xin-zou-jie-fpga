// Complete piano parameters reside in DDR. The host uploads the bank once;
// every byte is read back through DDR and checked before piano is enabled.
`include "src/piano/sms_ddr/bank_config.vh"
module piano_ddr_bank(
 input wire clk,rst_n,flush,memory_ready,transport_fault,
 output reg initialized,output reg fault,
 input wire upload_begin,upload_valid,upload_commit,upload_error,
 input wire [10:0] upload_index,input wire [2047:0] upload_data,
 output wire upload_ready,output reg [10:0] upload_count,
 output wire [2:0] bank_status,output reg [7:0] status_error,
 input wire load_valid,input wire [3:0] load_voice,
 input wire [8:0] load_bank,input wire [7:0] load_epoch,
 output reg loaded,output reg [3:0] loaded_voice,output reg [7:0] loaded_epoch,
 input wire tonal_enable,input wire [7:0] tonal_address,
 output reg [191:0] tonal_weights,output reg [31:0] tonal_frequency,
 input wire transient_enable,input wire [6:0] transient_address,
 output reg [63:0] transient_parameters,
 input wire [3:0] noise_voice,output wire [63:0] noise_parameters,
 output wire req_valid,input wire req_ready,output wire [63:0] req_data,
 input wire rsp_valid,output wire rsp_ready,input wire [63:0] rsp_data
);
 localparam [28:0] BASE=29'h0100000;
 localparam WAIT_UPLOAD=0,WRITE_HEADER=1,WRITE_DATA=2,WRITE_ACK=3,
  VERIFY_HEADER=4,VERIFY_DATA=5,VERIFY_CRC=6,IDLE=7,CACHE_ADDRESS=8,
  CACHE_HEADER=9,CACHE_DATA=10,CACHE_WRITE=11,STOP=12;
 reg [3:0] state;
 reg [223:0] tonal_cache[0:255];
 reg [63:0] transient_cache[0:127],noise_cache[0:15];
 assign noise_parameters=noise_cache[noise_voice];
 reg [15:0] pending;
 reg [8:0] pending_bank[0:15];reg [7:0] pending_epoch[0:15];
 reg [3:0] selected;
 integer j;
 always @*begin selected=0;for(j=15;j>=0;j=j-1)if(pending[j])selected=j;end
 reg [255:0] payload;
 reg [2047:0] upload_packet;
 reg [2:0] upload_record;
 reg [28:0] upload_address,read_address,cache_base;
 reg [13:0] verify_index;
 reg [1:0] beat;
 reg [2:0] crc_byte_index;
 reg [31:0] crc;
 reg [63:0] crc_word;
 reg session_active,restart_pending,cache_cancelled;
 reg [3:0] cache_voice;reg [7:0] cache_epoch;reg [4:0] cache_block;
 wire verifying=state==VERIFY_HEADER||state==VERIFY_DATA||state==VERIFY_CRC;
 assign bank_status=!memory_ready?3'd5:fault?3'd4:initialized?3'd3:verifying?3'd2:session_active?3'd1:3'd0;
 assign upload_ready=memory_ready&&!fault&&session_active&&state==WAIT_UPLOAD&&upload_count<1100&&!restart_pending;
 assign req_valid=memory_ready&&!fault&&(state==WRITE_HEADER||state==WRITE_DATA||state==VERIFY_HEADER||state==CACHE_HEADER);
 wire [28:0] verify_address=BASE+{12'd0,verify_index,3'd0};
 assign req_data=state==WRITE_DATA?payload[beat*64+:64]:state==WRITE_HEADER?{1'b1,34'd0,upload_address}:
   {35'd0,(state==VERIFY_HEADER?verify_address:read_address)};
 assign rsp_ready=state==WRITE_ACK||state==VERIFY_DATA||state==CACHE_DATA;
 function [31:0] crc_byte;
  input [31:0] c0;input [7:0] b;
  reg [31:0] c;integer k;
  begin c=c0^{24'd0,b};for(k=0;k<8;k=k+1)c=c[0]?(c>>1)^32'hedb88320:(c>>1);crc_byte=c;end
 endfunction
 wire [31:0] crc_next=crc_byte(crc,crc_word[7:0]);
 always @(posedge clk)begin
  if(tonal_enable)begin tonal_weights<=tonal_cache[tonal_address][191:0];tonal_frequency<=tonal_cache[tonal_address][223:192];end
  if(transient_enable)transient_parameters<=transient_cache[transient_address];
  if(state==CACHE_WRITE)begin
   if(cache_block<16)tonal_cache[{cache_voice,cache_block[3:0]}]<=payload[223:0];
   else if(cache_block<24)transient_cache[{cache_voice,cache_block[2:0]}]<=payload[63:0];
   else noise_cache[cache_voice]<=payload[63:0];
  end
 end
 integer i;
 always @(posedge clk or negedge rst_n)begin
  if(!rst_n)begin
   state<=WAIT_UPLOAD;initialized<=0;fault<=0;status_error<=0;upload_count<=0;
   pending<=0;loaded<=0;loaded_voice<=0;loaded_epoch<=0;
   payload<=0;upload_packet<=0;upload_record<=0;upload_address<=0;read_address<=0;cache_base<=0;
   verify_index<=0;beat<=0;crc_byte_index<=0;crc<=32'hffffffff;crc_word<=0;
   session_active<=0;restart_pending<=0;cache_cancelled<=0;
   cache_voice<=0;cache_epoch<=0;cache_block<=0;
   for(i=0;i<16;i=i+1)begin pending_bank[i]<=0;pending_epoch[i]<=0;end
  end else begin
   loaded<=0;
   if(transport_fault||(initialized&&!memory_ready))begin
    fault<=1;status_error<=5;initialized<=0;state<=STOP;
   end else if(upload_error)begin
    fault<=1;status_error<=1;initialized<=0;state<=STOP;
   end else if(!fault)case(state)
    WAIT_UPLOAD:begin
     if(upload_valid)begin
      if(!upload_ready||upload_index!=upload_count)begin fault<=1;status_error<=2;state<=STOP;end
      else begin
       upload_packet<=upload_data;payload<=upload_data[255:0];upload_record<=0;
       upload_address<=BASE+{12'd0,upload_index,6'd0};state<=WRITE_HEADER;
      end
     end else if(upload_commit)begin
      if(upload_count!=1100||!session_active)begin fault<=1;status_error<=2;state<=STOP;end
      else begin verify_index<=0;crc<=32'hffffffff;state<=VERIFY_HEADER;end
     end
    end
    WRITE_HEADER:if(req_valid&&req_ready)begin beat<=0;state<=WRITE_DATA;end
    WRITE_DATA:if(req_valid&&req_ready)begin if(beat==3)state<=WRITE_ACK;else beat<=beat+1'b1;end
    WRITE_ACK:if(rsp_valid&&rsp_ready)begin
     if(rsp_data!=64'h5049414e4f5f4f4b)begin fault<=1;status_error<=3;state<=STOP;end
     else if(upload_record==7)begin upload_count<=upload_count+1'b1;state<=WAIT_UPLOAD;end
     else begin
      upload_packet<=upload_packet>>256;payload<=upload_packet[511:256];
      upload_address<=upload_address+29'd8;upload_record<=upload_record+1'b1;state<=WRITE_HEADER;
     end
    end
    VERIFY_HEADER:if(req_valid&&req_ready)begin beat<=0;state<=VERIFY_DATA;end
    VERIFY_DATA:if(rsp_valid&&rsp_ready)begin crc_word<=rsp_data;crc_byte_index<=0;state<=VERIFY_CRC;end
    VERIFY_CRC:begin
     crc<=crc_next;crc_word<=crc_word>>8;
     if(crc_byte_index==7)begin
      if(beat==3)begin
       if(restart_pending)state<=IDLE;
       else if(verify_index==8799)begin
        if((crc_next^32'hffffffff)==`PIANO_BANK_CRC32)begin initialized<=1;session_active<=0;state<=IDLE;end
        else begin fault<=1;status_error<=4;state<=STOP;end
       end else begin verify_index<=verify_index+1'b1;state<=VERIFY_HEADER;end
      end else begin beat<=beat+1'b1;state<=VERIFY_DATA;end
     end else crc_byte_index<=crc_byte_index+1'b1;
    end
    IDLE:if(|pending&&!flush&&!restart_pending)begin
     cache_voice<=selected;cache_epoch<=pending_epoch[selected];cache_block<=0;
     cache_base<=BASE+pending_bank[selected]*29'd200;
     pending[selected]<=0;cache_cancelled<=0;state<=CACHE_ADDRESS;
    end
    CACHE_ADDRESS:begin read_address<=cache_base+{21'd0,cache_block,3'd0};state<=CACHE_HEADER;end
    CACHE_HEADER:if(req_valid&&req_ready)begin beat<=0;state<=CACHE_DATA;end
    CACHE_DATA:if(rsp_valid&&rsp_ready)begin payload[beat*64+:64]<=rsp_data;if(beat==3)state<=CACHE_WRITE;else beat<=beat+1'b1;end
    CACHE_WRITE:begin
     if(cache_block==24)begin loaded<=!cache_cancelled&&!flush&&!restart_pending;loaded_voice<=cache_voice;loaded_epoch<=cache_epoch;state<=IDLE;end
     else begin cache_block<=cache_block+1'b1;state<=CACHE_ADDRESS;end
    end
    default:begin end
   endcase
   if(restart_pending&&(state==WAIT_UPLOAD||state==IDLE||state==STOP)&&!transport_fault)begin
    restart_pending<=0;initialized<=0;fault<=0;status_error<=0;upload_count<=0;session_active<=1;
    pending<=0;loaded<=0;state<=WAIT_UPLOAD;
   end
   if(upload_begin)begin restart_pending<=1;initialized<=0;pending<=0;cache_cancelled<=1;end
   if(load_valid&&initialized)begin pending[load_voice]<=1;pending_bank[load_voice]<=load_bank;pending_epoch[load_voice]<=load_epoch;end
   if(flush)begin pending<=0;cache_cancelled<=1;loaded<=0;end
  end
 end
endmodule

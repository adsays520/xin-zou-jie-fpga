// Grant complete transactions. Live delay traffic has priority at a boundary;
// an in-flight piano/cache/CRC transaction always finishes without interleaving.
module piano_audio_ddr_arbiter(
 input wire clk,rst_n,
 input wire piano_req_valid,output wire piano_req_ready,input wire [63:0] piano_req_data,
 output wire piano_rsp_valid,input wire piano_rsp_ready,output wire [63:0] piano_rsp_data,
 input wire audio_req_valid,output wire audio_req_ready,input wire [63:0] audio_req_data,
 output wire audio_rsp_valid,input wire audio_rsp_ready,output wire [63:0] audio_rsp_data,
 output wire req_valid,input wire req_ready,output wire [63:0] req_data,
 input wire rsp_valid,output wire rsp_ready,input wire [63:0] rsp_data
);
 reg locked,owner,writing;
 reg [1:0] response_beat;
 wire selected=locked?owner:audio_req_valid;
 assign req_valid=selected?audio_req_valid:piano_req_valid;
 assign req_data=selected?audio_req_data:piano_req_data;
 assign audio_req_ready=req_ready&&selected;
 assign piano_req_ready=req_ready&&!selected;
 assign audio_rsp_valid=rsp_valid&&locked&&owner;
 assign piano_rsp_valid=rsp_valid&&locked&&!owner;
 assign audio_rsp_data=rsp_data;
 assign piano_rsp_data=rsp_data;
 assign rsp_ready=locked&&(owner?audio_rsp_ready:piano_rsp_ready);
 always @(posedge clk or negedge rst_n)begin
  if(!rst_n)begin locked<=0;owner<=0;writing<=0;response_beat<=0;end
  else begin
   if(!locked&&req_valid&&req_ready)begin
    locked<=1;owner<=selected;writing<=req_data[63];response_beat<=0;
   end
   if(locked&&rsp_valid&&rsp_ready)begin
    if(writing||response_beat==3)locked<=0;else response_beat<=response_beat+1'b1;
   end
  end
 end
endmodule

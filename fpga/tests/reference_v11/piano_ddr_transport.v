// One ordered stream through dual-clock RAM FIFOs. Header: bit63=write,
// address[28:0] in native x32 units; writes have four following data words.
// Reads return four 64-bit words; writes return one acknowledgement.
module piano_ddr_transport_v11_reference #(parameter integer TIMEOUT=100000)(
 input wire clk,sys_rst_n,mem_clk,mem_rst_n,calibrated,
 input wire req_valid,output wire req_ready,input wire [63:0] req_data,
 output wire rsp_valid,input wire rsp_ready,output wire [63:0] rsp_data,
 output reg fault,
 input wire cmd_ready,wr_data_rdy,
 output wire [2:0] cmd,output wire cmd_en,output wire [28:0] addr,
 output wire [255:0] wr_data,output wire [31:0] wr_data_mask,
 output wire wr_data_en,wr_data_end,
 input wire [255:0] rd_data,input wire rd_data_valid,rd_data_end
);
 wire live_rst_n=mem_rst_n&&calibrated;
 wire in_valid,in_ready,out_valid,out_ready;
 wire [63:0] in_data,out_data;
 excitation_async_fifo64 u_requests(
  .wclk(clk),.wrst_n(sys_rst_n),.wvalid(req_valid),.wready(req_ready),.wdata(req_data),
  .rclk(mem_clk),.rrst_n(live_rst_n),.rvalid(in_valid),.rready(in_ready),.rdata(in_data));
 excitation_async_fifo64 u_responses(
  .wclk(mem_clk),.wrst_n(live_rst_n),.wvalid(out_valid),.wready(out_ready),.wdata(out_data),
  .rclk(clk),.rrst_n(sys_rst_n),.rvalid(rsp_valid),.rready(rsp_ready),.rdata(rsp_data));
 localparam IDLE=0,GATHER=1,SEND=2,WAIT_READ=3,REPLY=4,ACK=5,STOP=6;
 reg [2:0] state;
 reg writing,command_sent,data_sent;
 reg [1:0] beat;
 reg [28:0] address;
 reg [255:0] payload;
 reg [31:0] timer;
 reg [255:0] read_pipe;
 reg read_valid_pipe,read_end_pipe;
 assign in_ready=!fault&&(state==IDLE||state==GATHER);
 assign cmd=writing?3'b000:3'b001;
 assign cmd_en=state==SEND&&!command_sent&&!fault;
 assign addr=address;
 assign wr_data=payload;
 assign wr_data_mask=32'd0;
 assign wr_data_en=state==SEND&&writing&&!data_sent&&!fault;
 assign wr_data_end=wr_data_en;
 assign out_valid=!fault&&(state==REPLY||state==ACK);
 assign out_data=state==ACK?64'h5049414e4f5f4f4b:payload[beat*64+:64];
 wire command_done=command_sent||(cmd_en&&cmd_ready);
 wire data_done=data_sent||(wr_data_en&&wr_data_rdy);
 always @(posedge mem_clk)read_pipe<=rd_data;
 always @(posedge mem_clk or negedge live_rst_n)begin
  if(!live_rst_n)begin read_valid_pipe<=0;read_end_pipe<=0;end
  else begin read_valid_pipe<=rd_data_valid;read_end_pipe<=rd_data_end;end
 end
 always @(posedge mem_clk or negedge live_rst_n)begin
  if(!live_rst_n)begin
   state<=IDLE;writing<=0;command_sent<=0;data_sent<=0;beat<=0;
   address<=0;payload<=0;timer<=0;fault<=0;
  end else begin
   if(state==IDLE)timer<=0;
   else if(timer>=TIMEOUT-1)begin fault<=1;state<=STOP;end
   else timer<=timer+1'b1;
   if(!fault&&timer<TIMEOUT-1)case(state)
    IDLE:if(in_valid&&in_ready)begin
     writing<=in_data[63];address<=in_data[28:0];beat<=0;
     command_sent<=0;data_sent<=0;
     if(in_data[2:0]!=0)begin fault<=1;state<=STOP;end
     else state<=in_data[63]?GATHER:SEND;
    end
    GATHER:if(in_valid&&in_ready)begin
     payload[beat*64+:64]<=in_data;
     if(beat==3)state<=SEND;else beat<=beat+1'b1;
    end
    SEND:begin
     if(cmd_en&&cmd_ready)command_sent<=1;
     if(wr_data_en&&wr_data_rdy)data_sent<=1;
     if(command_done&&(!writing||data_done))state<=writing?ACK:WAIT_READ;
    end
    WAIT_READ:if(read_valid_pipe)begin
     if(!read_end_pipe)begin fault<=1;state<=STOP;end
     else begin payload<=read_pipe;beat<=0;state<=REPLY;end
    end
    REPLY:if(out_valid&&out_ready)begin
     if(beat==3)state<=IDLE;else beat<=beat+1'b1;
    end
    ACK:if(out_valid&&out_ready)state<=IDLE;
    default:begin end
   endcase
  end
 end
endmodule

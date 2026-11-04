// Behavioral native DDR application port; no PHY/calibration is simulated here.
module ddr_parameter_app_model(
 input wire clk,rst_n,freeze,corrupt,
 input wire [2:0] cmd,input wire cmd_en,input wire [28:0] addr,
 output wire cmd_ready,
 input wire [255:0] wr_data,input wire [31:0] wr_data_mask,
 input wire wr_data_en,wr_data_end,output wire wr_data_rdy,
 output reg [255:0] rd_data,output reg rd_data_valid,output wire rd_data_end
);
 reg [255:0] memory[0:12895];
 reg [31:0] random_state;
 reg have_command,have_data;
 reg [2:0] saved_cmd;
 reg [28:0] saved_addr;
 reg [255:0] saved_data;
 reg [31:0] saved_mask;
 reg [4:0] read_count;
 reg [13:0] read_index;
 function [13:0] record_index;
  input [28:0] a;
  begin record_index=a>=29'h200000 ? 14'd8800+((a-29'h200000)>>3):((a-29'h100000)>>3);end
 endfunction
 integer b,writes=0,reads=0;
 assign cmd_ready=rst_n&&!freeze&&!have_command&&random_state[0];
 assign wr_data_rdy=rst_n&&!freeze&&!have_data&&random_state[1];
 assign rd_data_end=rd_data_valid;
 always @(posedge clk or negedge rst_n)begin
  if(!rst_n)begin
   random_state<=32'h193a5f27;have_command<=0;have_data<=0;
   saved_cmd<=0;saved_addr<=0;saved_data<=0;saved_mask<=0;
   read_count<=0;read_index<=0;rd_data<=0;rd_data_valid<=0;
  end else begin
   random_state<={random_state[30:0],random_state[31]^random_state[21]^random_state[1]^random_state[0]};
   rd_data_valid<=0;
   if(cmd_en&&cmd_ready)begin
    if(addr[2:0]!=0||!((addr>=29'h100000&&addr<29'h111300)||(addr>=29'h200000&&addr<29'h208000)))$fatal(1,"DDR native address/alignment %h",addr);
    if(cmd!=0&&cmd!=1)$fatal(1,"DDR command");
    have_command<=1;saved_cmd<=cmd;saved_addr<=addr;
   end
   if(wr_data_en&&wr_data_rdy)begin
    if(!wr_data_end)$fatal(1,"DDR BL8 write missing end");
    have_data<=1;saved_data<=wr_data;saved_mask<=wr_data_mask;
   end
   if(have_command&&!freeze)begin
    if(saved_cmd==0&&have_data)begin
     for(b=0;b<32;b=b+1)if(!saved_mask[b])memory[record_index(saved_addr)][b*8+:8]<=saved_data[b*8+:8];
     writes<=writes+1;have_command<=0;have_data<=0;
    end else if(saved_cmd==1&&read_count==0)begin
     reads<=reads+1;read_count<=1+random_state[7:4];
     read_index<=record_index(saved_addr);have_command<=0;
    end
   end
   if(read_count!=0&&!freeze)begin
    read_count<=read_count-1'b1;
    if(read_count==1)begin
     rd_data<=memory[read_index]^(corrupt?256'd1:256'd0);rd_data_valid<=1;
    end
   end
  end
 end
endmodule

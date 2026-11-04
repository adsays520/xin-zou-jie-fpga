`include "src/piano/sms_ddr/bank_config.vh"
module piano_bank_status_tx(
 input wire clk,rst_n,query,input wire [7:0] query_sequence,
 input wire [2:0] bank_status,input wire [10:0] upload_count,input wire [7:0] status_error,
 input wire verification_busy,output wire hold_verification,
 output wire tx,output wire busy
);
 reg pending;
 reg [7:0] request_id;
 reg [1:0] state;
 reg [3:0] index;
 reg [7:0] packet[0:11];
 reg start;
 wire uart_busy,done;
 assign busy=state!=0;
 assign hold_verification=pending||busy||query;
 verification_uart_tx u_tx(.clk(clk),.rst_n(rst_n),.start(start),.data(packet[index]),.tx(tx),.busy(uart_busy),.done(done));
 wire [31:0] bank_crc=`PIANO_BANK_CRC32;
 always @(posedge clk or negedge rst_n)begin
  if(!rst_n)begin pending<=0;request_id<=0;state<=0;index<=0;start<=0;end
  else begin
   start<=0;
   case(state)
    0:if(pending&&!verification_busy)begin
     packet[0]<=8'hb7;packet[1]<=8'h53;packet[2]<=request_id;packet[3]<={5'd0,bank_status};
     packet[4]<=upload_count[7:0];packet[5]<={5'd0,upload_count[10:8]};
     packet[6]<=bank_crc[7:0];packet[7]<=bank_crc[15:8];packet[8]<=bank_crc[23:16];packet[9]<=bank_crc[31:24];
     packet[10]<=status_error;
     packet[11]<=8'hb7^8'h53^request_id^{5'd0,bank_status}^upload_count[7:0]^{5'd0,upload_count[10:8]}^
                  bank_crc[7:0]^bank_crc[15:8]^bank_crc[23:16]^bank_crc[31:24]^status_error;
     index<=0;pending<=0;state<=1;
    end
    1:if(!uart_busy)begin start<=1;state<=2;end
    2:if(done)begin if(index==11)state<=0;else begin index<=index+1'b1;state<=1;end end
   endcase
   if(query)begin pending<=1;request_id<=query_sequence;end
  end
 end
endmodule

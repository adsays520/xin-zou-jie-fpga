module ensemble_capabilities(
 input wire clk,rst_n,query,input wire [7:0] query_sequence,
 input wire ensemble_mode,piano_ready,other_busy,
 output wire tx,output wire busy,hold_other
);
 reg pending,start;
 reg [7:0] request_id,flags,checksum;
 reg [2:0] index;
 reg [1:0] state;
 wire uart_busy,done;
 reg [7:0] data;
 assign busy=state!=0;
 assign hold_other=pending||busy||query;
 always @*begin
  case(index)
   0:data=8'hd8;1:data=8'h45;2:data=request_id;3:data=8'h08;4:data=flags;default:data=checksum;
  endcase
 end
 verification_uart_tx u_tx(.clk(clk),.rst_n(rst_n),.start(start),.data(data),.tx(tx),.busy(uart_busy),.done(done));
 always @(posedge clk or negedge rst_n)begin
  if(!rst_n)begin pending<=0;start<=0;request_id<=0;flags<=0;checksum<=0;index<=0;state<=0;end
  else begin
   start<=0;
   if(query&&!pending&&!busy)begin pending<=1;request_id<=query_sequence;end
   case(state)
    0:if(pending&&!other_busy)begin
     pending<=0;flags<={3'd0,ensemble_mode,1'b0,piano_ready,2'b11};
     checksum<=8'hd8^8'h45^request_id^8'h08^{3'd0,ensemble_mode,1'b0,piano_ready,2'b11};
     index<=0;state<=1;
    end
    1:if(!uart_busy)begin start<=1;state<=2;end
    2:if(done)begin if(index==5)state<=0;else begin index<=index+1'b1;state<=1;end end
    default:begin end
   endcase
  end
 end
endmodule

// Two RKJXT encoders. SW1 direction contacts are separate from its encoder.
// RKJXT1F42001: 30 detents / 15 pulses -> TWO Gray transitions per detent.
// Reversals cancel contact bounce; illegal two-bit jumps discard partial travel.
module panel_encoder #(parameter REVERSE=0,parameter TRANSITIONS_PER_DETENT=2)(
 input wire clk,rst_n,input wire a,b,output reg cw,ccw
);
 reg [1:0] a_sync,b_sync,previous;reg signed [3:0] travel;
 reg signed [2:0] step;
 always @*begin
  case({previous,a_sync[1],b_sync[1]})
   4'b1101,4'b0100,4'b0010,4'b1011:step=1;
   4'b1110,4'b1000,4'b0001,4'b0111:step=-1;
   default:step=0;
  endcase
 end
 always @(posedge clk or negedge rst_n)begin
  if(!rst_n)begin a_sync<=3;b_sync<=3;previous<=3;travel<=0;cw<=0;ccw<=0;end
  else begin
   a_sync<={a_sync[0],a};b_sync<={b_sync[0],b};previous<={a_sync[1],b_sync[1]};cw<=0;ccw<=0;
   if((previous^{a_sync[1],b_sync[1]})==2'b11)travel<=0;
   else if(step==1)begin
    if(travel==TRANSITIONS_PER_DETENT-1)begin travel<=0;if(REVERSE)ccw<=1;else cw<=1;end
    else travel<=travel+1'b1;
   end else if(step==-1)begin
    if(travel==1-TRANSITIONS_PER_DETENT)begin travel<=0;if(REVERSE)cw<=1;else ccw<=1;end
    else travel<=travel-1'b1;
   end
  end
 end
endmodule

module panel_button #(parameter integer STABLE_CLKS=250000,parameter REPEAT=0,
 parameter integer HOLD_CLKS=17500000,REPEAT_CLKS=2000000)(
 input wire clk,rst_n,n,output reg pressed
);
 localparam integer W=$clog2(STABLE_CLKS+1);
 reg [1:0] sync;reg stable;reg [W-1:0] count;
 reg [$clog2(HOLD_CLKS+1)-1:0] held;
 always @(posedge clk or negedge rst_n)begin
  if(!rst_n)begin sync<=3;stable<=1;count<=0;pressed<=0;held<=0;end
  else begin
   sync<={sync[0],n};pressed<=0;
   if(REPEAT&&!stable&&!sync[1])begin
    if(held==HOLD_CLKS-1)begin pressed<=1;held<=HOLD_CLKS-REPEAT_CLKS;end
    else held<=held+1'b1;
   end else held<=0;
   if(sync[1]==stable)count<=0;
   else if(count==STABLE_CLKS-1)begin stable<=sync[1];count<=0;if(!sync[1])pressed<=1;end
   else count<=count+1'b1;
  end
 end
endmodule

module panel_inputs #(parameter integer STABLE_CLKS=250000,
 parameter SW1_REVERSE=0,SW2_REVERSE=0)(
 input wire clk,rst_n,sw1_a,sw1_b,sw2_a,sw2_b,
 input wire up_n,right_n,down_n,left_n,
 output wire row_next,col_next,slide_step,vibrato_step,
 output wire up,right,down,left
);
 panel_encoder #(.REVERSE(SW1_REVERSE)) e1(.clk(clk),.rst_n(rst_n),.a(sw1_a),.b(sw1_b),.cw(col_next),.ccw(row_next));
 panel_encoder #(.REVERSE(SW2_REVERSE)) e2(.clk(clk),.rst_n(rst_n),.a(sw2_a),.b(sw2_b),.cw(slide_step),.ccw(vibrato_step));
 panel_button #(.STABLE_CLKS(STABLE_CLKS)) u(.clk(clk),.rst_n(rst_n),.n(up_n),.pressed(up));
 panel_button #(.STABLE_CLKS(STABLE_CLKS),.REPEAT(1)) r(.clk(clk),.rst_n(rst_n),.n(right_n),.pressed(right));
 panel_button #(.STABLE_CLKS(STABLE_CLKS)) d(.clk(clk),.rst_n(rst_n),.n(down_n),.pressed(down));
 panel_button #(.STABLE_CLKS(STABLE_CLKS),.REPEAT(1)) l(.clk(clk),.rst_n(rst_n),.n(left_n),.pressed(left));
endmodule

// Real-time impulse-excited modal drum. Tables contain equations/coefficients,
// never recorded sound. Each mode stores its own two live displacement states.
module kick_modal #(parameter EXTERNAL_PARAMETERS=0)(
 input wire clk,rst_n,start,clear,strike,
 input wire [6:0] velocity,input wire [1:0] kit,
 output reg valid,output reg signed [31:0] sample,
 output wire active,
 output reg parameter_read_enable,output reg [9:0] parameter_address,
 input wire [31:0] parameter_data
);
 wire signed [31:0] coefficient_first,coefficient_second,coefficient_third;
 wire [23:0] force_default;
 generate if(!EXTERNAL_PARAMETERS)begin:g_internal_parameters
  reg signed [31:0] coefficients[0:107] /* synthesis syn_romstyle="logic" */;
  reg [23:0] force_shape[0:119] /* synthesis syn_romstyle="logic" */;
  initial begin
   $readmemh("src/drums/rom/kick_modal_coeffs.hex",coefficients);
   $readmemh("src/drums/rom/kick_force.hex",force_shape);
  end
  assign coefficient_first=coefficients[base];
  assign coefficient_second=coefficients[base+1'b1];
  assign coefficient_third=coefficients[base+7'd2];
  assign force_default=strike?force_shape[0]:(position<120?force_shape[position]:24'd0);
 end else begin:g_external_parameters
  assign coefficient_first=parameter_data;
  assign coefficient_second=parameter_data;
  assign coefficient_third=parameter_data;
  assign force_default=24'd0;
 end endgenerate
 reg signed [31:0] y1[0:11],y2[0:11];
 reg [15:0] age;
 reg [6:0] position,strike_velocity,frame_velocity;
 reg [3:0] state,mode;
 reg [6:0] base;
 reg [23:0] force_read;
 reg force_enabled;
 reg signed [31:0] force_value,coefficient,operand,old_y,new_y,total;
 reg signed [63:0] product,partial,sum;
 integer i;
 assign active=age<48000;
 always @*begin
  parameter_read_enable=0;parameter_address=0;
  if(EXTERNAL_PARAMETERS)case(state)
   0:if(start&&(active||strike))begin
    parameter_read_enable=1;parameter_address=10'd640+(strike?10'd0:{3'd0,position});
   end
   11:begin parameter_read_enable=1;parameter_address=10'd512+{3'd0,base};end
   2:begin parameter_read_enable=1;parameter_address=10'd513+{3'd0,base};end
   4:begin parameter_read_enable=1;parameter_address=10'd514+{3'd0,base};end
   9:if(mode!=11)begin parameter_read_enable=1;parameter_address=10'd515+{3'd0,base};end
   default:begin end
  endcase
 end
 wire [23:0] force_input=EXTERNAL_PARAMETERS?(force_enabled?parameter_data[23:0]:24'd0):force_read;
 always @(posedge clk or negedge rst_n)begin
  if(!rst_n)begin
   state<=0;mode<=0;base<=0;age<=48000;position<=120;strike_velocity<=0;frame_velocity<=0;
   valid<=0;sample<=0;force_read<=0;force_enabled<=0;force_value<=0;coefficient<=0;operand<=0;
   old_y<=0;new_y<=0;total<=0;product<=0;partial<=0;sum<=0;
   for(i=0;i<12;i=i+1)begin y1[i]<=0;y2[i]<=0;end
  end else if(clear)begin
   state<=0;age<=48000;position<=120;sample<=0;valid<=0;
   for(i=0;i<12;i=i+1)begin y1[i]<=0;y2[i]<=0;end
  end else begin
   valid<=0;
   case(state)
    0:if(start)begin
     if(!active&&!strike)begin sample<=0;valid<=1;end
     else begin
      mode<=0;total<=0;base<=kit==2?7'd72:kit==1?7'd36:7'd0;
      force_enabled<=strike||position<120;
      if(strike)begin age<=0;position<=1;strike_velocity<=velocity;frame_velocity<=velocity;force_read<=force_default;end
      else begin
       age<=age+1'b1;frame_velocity<=strike_velocity;
       force_read<=force_default;
       if(position<120)position<=position+1'b1;
      end
      state<=11;
     end
    end
    11:begin force_value<=($signed({1'b0,force_input})*$signed({1'b0,frame_velocity}))>>>7;state<=1;end
    1:begin coefficient<=coefficient_first;operand<=y1[mode];old_y<=y1[mode];state<=2;end
    2:begin product<=coefficient*operand;state<=3;end
    3:begin partial<=product;coefficient<=coefficient_second;operand<=y2[mode];state<=4;end
    4:begin product<=coefficient*operand;state<=5;end
    5:begin partial<=partial+product;coefficient<=coefficient_third;operand<=force_value;state<=6;end
    6:begin product<=coefficient*operand;state<=7;end
    7:begin sum<=partial+product;state<=8;end
    8:begin new_y<=age>=48000?32'sd0:(sum+64'sd536870912)>>>30;state<=9;end
    9:begin
     y1[mode]<=new_y;y2[mode]<=age>=48000?32'sd0:old_y;
     total<=total+new_y;
     if(mode==11)state<=10;
     else begin mode<=mode+1'b1;base<=base+7'd3;state<=1;end
    end
    10:begin sample<=total;valid<=1;state<=0;end
    default:state<=0;
   endcase
  end
 end
endmodule

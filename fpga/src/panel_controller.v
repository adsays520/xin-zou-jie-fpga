// Navigation and local edits use the same atomic commands as the host.
module panel_controller(
 input wire clk,rst_n,row_next,col_next,up,right,down,left,
 input wire [255:0] values,input wire command_ready,
 output wire [47:0] command_data,output wire command_valid,
 output reg [3:0] page,focus_row,focus_col,output reg editing,
 output reg [7:0] slide_semi,vibrato_cents,vibrato_hz,return_10ms,
 output reg reset_pitch
);
 `include "src/panel_menu.vh"
 reg [255:0] frozen;reg [2:0] kind,packet,last_packet;
 reg pending;
 wire [5:0] field=menu_field(page,focus_row,focus_col[0]);
 reg [7:0] current_value;reg [5:0] field_q;
 always @(posedge clk)begin current_value<=values[field*8+:8];field_q<=field;end
 reg [7:0] lower,upper,new_value;
 always @*begin
  lower=0;upper=127;
  case(field_q)
   0:upper=4;1:upper=10;18:upper=96;6:upper=5;9,10,11,30:upper=1;19:upper=4;
   25:begin lower=1;upper=4;end
   26:begin lower=1;upper=20;end
   27:begin lower=1;upper=10;end
   28:begin lower=10;upper=50;end
   29:upper=0;
   default:;
  endcase
  new_value=current_value;
  if(right||(down&&(field==9||field==10||field==11||field==30)))begin
   if(current_value<upper)new_value=current_value+1'b1;else if(upper==1)new_value=0;
  end else if(left&&current_value>lower)new_value=current_value-1'b1;
 end
 reg[7:0]op,a,b,c;
 always @*begin
  op=0;a=0;b=0;c=0;
  case(kind)
   1:if(packet==0)begin op=8'h04;a=frozen[7:0]<2?0:frozen[7:0]-1'b1;end
     else case(packet)
      1:begin op=8'h40;a=frozen[15:8];b=frozen[23:16];c=frozen[31:24];end
      2:begin op=8'h41;a=frozen[39:32];b=frozen[47:40];c={5'd0,frozen[88],frozen[80],frozen[72]};end
      3:begin op=8'h42;a=frozen[55:48];b=frozen[63:56];c=frozen[71:64];end
      4:begin op=8'h43;a=frozen[103:96];end
      default:op=8'h44;
     endcase
   2:case(packet)
      0:begin op=8'h40;a=frozen[15:8];b=frozen[23:16];c=frozen[31:24];end
      1:begin op=8'h41;a=frozen[39:32];b=frozen[47:40];c={5'd0,frozen[88],frozen[80],frozen[72]};end
      2:begin op=8'h42;a=frozen[55:48];b=frozen[63:56];c=frozen[71:64];end
      3:begin op=8'h43;a=frozen[103:96];end
      default:op=8'h44;
     endcase
   3:case(packet)
      0:begin op=8'h60;a=frozen[111:104];b=frozen[119:112];c=frozen[127:120];end
      1:begin op=8'h61;a=frozen[135:128];b=frozen[143:136];c=frozen[151:144];end
      default:op=8'h62;
     endcase
   4:begin op=8'h70;a=frozen[255:248];b=frozen[247:240];end
   5:begin op=8'h06;a=frozen[159:152];end
   6:begin op=8'h03;a=frozen[247:240];end
   default:;
  endcase
 end
 assign command_data={8'ha5,op,a,b,c,(8'ha5^op^a^b^c)};
 assign command_valid=pending;
 always @(posedge clk or negedge rst_n)begin
  if(!rst_n)begin
   page<=0;focus_row<=0;focus_col<=0;editing<=0;pending<=0;kind<=0;packet<=0;last_packet<=0;frozen<=0;
   slide_semi<=1;vibrato_cents<=5;vibrato_hz<=5;return_10ms<=25;reset_pitch<=0;
  end else begin
   reset_pitch<=0;
   if(pending&&command_ready)begin
    if(packet==last_packet)pending<=0;else packet<=packet+1'b1;
   end
   if(up)begin
    if(editing)editing<=0;else begin focus_row<=0;focus_col<=page;end
   end else if(row_next&&!editing)begin
    if(focus_row==menu_rows(page))begin focus_row<=0;focus_col<=page;end
    else begin focus_row<=focus_row+1'b1;focus_col<=0;end
   end else if(col_next&&!editing)begin
    if(focus_row==0)focus_col<=focus_col==7?0:focus_col+1'b1;
    else if(focus_col==0&&menu_field(page,focus_row,1)!=63)focus_col<=1;else focus_col<=0;
   end else if(focus_row==0)begin
    if(left)focus_col<=focus_col==0?7:focus_col-1'b1;
    if(right)focus_col<=focus_col==7?0:focus_col+1'b1;
    if(down)begin page<=focus_col;focus_row<=focus_col>=5?0:1;if(focus_col<5)focus_col<=0;end
   end else if(down&&!editing&&field!=29)editing<=1;
   else if(down&&editing)editing<=0;
   if(focus_row!=0&&!pending&&field_q!=63&&field==field_q&&((editing&&(left||right))||(down&&field_q==29)))begin
    if(field_q==29)reset_pitch<=1;
    else if(field_q>=25&&field_q<=28)case(field_q)
     25:slide_semi<=new_value;26:vibrato_cents<=new_value;27:vibrato_hz<=new_value;28:return_10ms<=new_value;
    endcase
    else if(new_value!=current_value)begin
     frozen<=values;frozen[field_q*8+:8]<=new_value;pending<=1;packet<=0;
     if(field_q==0)begin
      kind<=1;last_packet<=new_value<2?5:0;
      if(new_value==0)frozen[15:8]<=0;
      else if(new_value==1&&values[15:8]==0)frozen[15:8]<=1;
     end else if(field_q<=12)begin kind<=2;last_packet<=4;end
     else if(field_q<=18)begin kind<=3;last_packet<=2;end
     else if(field_q==19)begin kind<=5;last_packet<=0;end
     else if(field_q<=24)begin
      kind<=4;last_packet<=0;frozen[247:240]<=new_value;
      case(field_q)20:frozen[255:248]<=0;21:frozen[255:248]<=1;22:frozen[255:248]<=4;23:frozen[255:248]<=3;default:frozen[255:248]<=2;endcase
     end else if(field_q==30)begin kind<=6;last_packet<=0;frozen[247:240]<=new_value;end
    end
   end
  end
 end
endmodule

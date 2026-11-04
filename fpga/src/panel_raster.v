// Pipelined 128x160 menu raster: warm charcoal, cream, mint and amber.
// No framebuffer or screen clear; captures actual control-register values.
module panel_raster(
 input wire clk,input wire [7:0] x,y,input wire [15:0] plot_rgb,
 input wire [3:0] page,row,col,input wire editing,input wire [255:0] values,
 output reg [15:0] pixel_rgb
);
 `include "src/panel_menu.vh"
 reg [7:0] xd,yd,x_decode,y_decode,ly_decode;
 reg [3:0] page_decode,row_decode,col_decode,grid_decode;
 reg editing_decode;
 reg [15:0] plot_decode,plot_q;
 reg [5:0] field_decode;
 reg [3:0] page_q,row_q,col_q;
 reg editing_q;
 wire [3:0] input_grid=y<44?1:y<64?2:y<84?3:y<104?4:y<124?5:6;
 wire [7:0] input_top=24+(input_grid-1)*20;
 reg [39:0] font[0:127],font_bits;
 initial $readmemh("src/panel_font.hex",font);
 reg [7:0] ch,ch1;
 reg [5:0] bit_index,bit_index1,bit_index2;
 reg [15:0] background,ink,background1,ink1,background2,ink2;
 reg [3:0] grid_row,title_page,char_index;
 reg [7:0] ly,lx,value;
 reg [5:0] field;
 reg [63:0] word;
 reg [6:0] rem10;
 reg numeric;
 function [63:0] enum_text;
  input[5:0] f;input[7:0]v;
  begin
   enum_text="        ";
   case(f)
    0:case(v)0:enum_text="ACOUSTIC";1:enum_text="E.GUITAR";2:enum_text="PIANO   ";3:enum_text="BASS    ";default:enum_text="VIOLIN  ";endcase
    1:case(v)0:enum_text="CLEAN   ";1:enum_text="TS808   ";2:enum_text="PLEXI   ";3:enum_text="JCM800  ";4:enum_text="JUBILEE ";5:enum_text="FUZZ    ";6:enum_text="OCT FUZZ";7:enum_text="BOOST   ";8:enum_text="BLUES   ";9:enum_text="MESA    ";default:enum_text="RECTIFY ";endcase
    6:case(v)0:enum_text="OFF     ";1:enum_text="TREMOLO ";2:enum_text="VIBRATO ";3:enum_text="PHASER  ";4:enum_text="FLANGER ";default:enum_text="AUTO WAH";endcase
    9,10,11,30:enum_text=v==0?"OFF     ":"ON      ";
    19:case(v)0:enum_text="UP      ";1:enum_text="HALF 1  ";2:enum_text="HALF 2  ";3:enum_text="HALF 3  ";default:enum_text="FULL    ";endcase
    29:enum_text="RESET   ";
    default:;
   endcase
  end
 endfunction
 always @*begin
  background=page_q>=5?plot_q:16'h10c3;ink=16'hf7bc;ch=" ";bit_index=0;
  title_page=row_q==0?col_q:page_q;
  lx={2'b0,xd[5:0]};
  word=enum_text(field,value);numeric=!(field==0||field==1||field==6||field==9||field==10||field==11||field==19||field==29||field==30);
  char_index=0;rem10=value>=100?value-100:value;
  if(yd<22)begin
   background=row_q==0?16'hfc86:16'h21a5;ink=row_q==0?16'h10c3:16'hf7bc;
   if(xd>=6&&xd<54&&yd>=6&&yd<13)begin
    char_index=(xd-6)/6;ch=menu_title(title_page,char_index);
    if((xd-6)%6<5)bit_index=(4-((xd-6)%6))*8+(yd-6);else ch=" ";
   end
   if(xd>=105&&xd<123&&yd>=6&&yd<13)begin
    char_index=(xd-105)/6;ch=char_index==0?"1"+title_page:char_index==1?"/":"8";
    if((xd-105)%6<5)bit_index=(4-((xd-105)%6))*8+(yd-6);else ch=" ";
   end
  end else if(yd<24)background=16'h5d95;
  else if(yd<144&&page_q<5&&field!=63)begin
   if(lx>=1&&lx<63&&ly>=1&&ly<19)background=16'h1944;
   if(row_q==grid_row&&col_q[0]==xd[6])begin
    if(lx<2||lx>=62||ly<1||ly>=19)background=editing_q?16'hfc86:16'h6ef9;
    else background=editing_q?16'h29c5:16'h21a5;
   end
   if(lx>=4&&lx<52&&ly>=2&&ly<9)begin
    char_index=(lx-4)/6;ch=menu_label(field,char_index);ink=16'hbdf6;
    if((lx-4)%6<5)bit_index=(4-((lx-4)%6))*8+(ly-2);else ch=" ";
   end
   if(lx>=4&&lx<52&&ly>=10&&ly<17)begin
    char_index=(lx-4)/6;
    if(!numeric)ch=word[63-char_index*8-:8];
    else case(char_index)
     0:ch=value>=100?"1":" ";
     1:ch=value>=10?"0"+rem10/10:" ";
     2:ch="0"+rem10%10;
     default:ch=" ";
    endcase
    if((lx-4)%6<5)bit_index=(4-((lx-4)%6))*8+(ly-10);else ch=" ";
   end
   if(numeric&&field<25&&ly==18&&lx>=4&&lx<59)background=(lx-4<(value*55)>>7)?16'hfc86:16'h3186;
  end else if(yd>=144)begin
   background=16'h10c3;ink=16'hbdf6;
   word=editing_q?"L-R EDIT":"DN OK UP";
   if(xd>=8&&xd<56&&yd>=149&&yd<156)begin
    char_index=(xd-8)/6;ch=word[63-char_index*8-:8];
    if((xd-8)%6<5)bit_index=(4-((xd-8)%6))*8+(yd-149);else ch=" ";
   end
   word=editing_q?"DN DONE ":"CCW ROW ";
   if(xd>=68&&xd<116&&yd>=149&&yd<156)begin
    char_index=(xd-68)/6;ch=word[63-char_index*8-:8];
    if((xd-68)%6<5)bit_index=(4-((xd-68)%6))*8+(yd-149);else ch=" ";
   end
  end
 end
 always @(posedge clk)begin
  x_decode<=x;y_decode<=y;ly_decode<=y-input_top;grid_decode<=input_grid;
  field_decode<=menu_field(page,input_grid,x[6]);
  page_decode<=page;row_decode<=row;col_decode<=col;editing_decode<=editing;plot_decode<=plot_rgb;
  xd<=x_decode;yd<=y_decode;ly<=ly_decode;grid_row<=grid_decode;field<=field_decode;
  value<=values[field_decode*8+:8];
  page_q<=page_decode;row_q<=row_decode;col_q<=col_decode;editing_q<=editing_decode;plot_q<=plot_decode;
  ch1<=ch;bit_index1<=bit_index;background1<=background;ink1<=ink;
  font_bits<=font[ch1[6:0]];bit_index2<=bit_index1;background2<=background1;ink2<=ink1;
  pixel_rgb<=font_bits[bit_index2]?ink2:background2;
 end
endmodule

// ST7735S 128x160, 4-wire SPI mode 0, RGB565 status screen.
// No framebuffer: pixels are generated while scanning, about 10 frames/s.
module st7735_status #(parameter PANEL_UI=0) (
    input wire clk,
    input wire rst_n,
    input wire [255:0] panel_values,input wire [3:0] panel_page,panel_row,panel_col,input wire panel_editing,
    input wire [6:0] guitar_level,piano_level,drum_level,
    input wire [1:0] selected_bus,
    input wire [1:0] page,
    input wire [1:0] visual_page_select,
    output wire [1:0] visual_page,
    input wire [15:0] visual_pixel_rgb,
    output wire [7:0] visual_pixel_x,visual_pixel_y,
    input wire [6:0] fx_drive,fx_tone,fx_mix,
    input wire [4:0] fx_amp,
    input wire [2:0] fx_modulation,
    input wire [6:0] chorus_mix,delay_mix,chorus_depth,
    input wire drum_playing,
    output reg lcd_sck,lcd_sda,lcd_cs_n,lcd_dc,lcd_rst_n,
    output wire lcd_led
);
    assign lcd_led = 1'b1;
    localparam RESET_LOW=0, RESET_HIGH=1, INIT_SEND=2, INIT_WAIT=3,
        INIT_PAUSE=4, HEADER_SEND=5, HEADER_WAIT=6,
        PIXEL_HIGH=7, PIXEL_HIGH_WAIT=8, PIXEL_LOW=9,
        PIXEL_LOW_WAIT=10, FRAME_PAUSE=11, PIXEL_PREP_A=12, PIXEL_PREP_B=13, PIXEL_RAM_WAIT=14;
    reg [4:0] state;
    reg [23:0] delay_count;
    reg [3:0] init_index,header_index;
    reg [7:0] px;
    reg [7:0] py;
    reg [7:0] render_x,render_y,render_top;
    assign visual_pixel_x=render_x;
    assign visual_pixel_y=render_y;
    reg [1:0] render_row;
    reg [6:0] render_level;
    reg [15:0] pixel_rgb_q;
    reg [7:0] tx_byte;
    reg tx_dc,byte_start;
    reg byte_busy,byte_done;
    reg [2:0] bit_index;
    reg [1:0] spi_div;
    reg spi_phase;
    reg [6:0] frame_guitar,frame_piano,frame_drum;
    reg [1:0] frame_selected;
    reg [1:0] frame_page;
    reg [1:0] frame_visual_page;
    assign visual_page=frame_visual_page;
    reg [6:0] frame_drive,frame_tone,frame_fx_mix;
    reg [4:0] frame_amp;
    reg [2:0] frame_modulation;
    reg [6:0] frame_chorus,frame_delay,frame_depth;
    reg frame_drum_playing;

    function [7:0] init_byte;
        input [3:0] index;
        begin case(index)
            0:init_byte=8'h01; // software reset
            1:init_byte=8'h11; // sleep out
            2:init_byte=8'h3a; // RGB565
            3:init_byte=8'h05;
            4:init_byte=8'h36; // normal scan direction
            5:init_byte=8'h00;
            default:init_byte=8'h29; // display on
        endcase end
    endfunction
    function [7:0] header_byte;
        input [3:0] index;
        begin case(index)
            0:header_byte=8'h2a; 1:header_byte=0; 2:header_byte=0;
            3:header_byte=0; 4:header_byte=8'd127;
            5:header_byte=8'h2b; 6:header_byte=0; 7:header_byte=0;
            8:header_byte=0; 9:header_byte=8'd159;
            default:header_byte=8'h2c;
        endcase end
    endfunction

    // Common 5x7 column-major glyphs. Bit 0 is the top pixel.
    function [39:0] glyph;
        input [7:0] ch;
        begin case(ch)
            "0":glyph=40'h3e4549513e; "1":glyph=40'h00427f4000;
            "2":glyph=40'h4261514946; "3":glyph=40'h2141494d33;
            "4":glyph=40'h1814127f10; "5":glyph=40'h2745454539;
            "6":glyph=40'h3c4a494930; "7":glyph=40'h0171090503;
            "8":glyph=40'h3649494936; "9":glyph=40'h064949291e;
            "A":glyph=40'h7e1111117e; "B":glyph=40'h7f49494936;
            "C":glyph=40'h3e41414122; "F":glyph=40'h7f09090901;
            "D":glyph=40'h7f4141413e; "E":glyph=40'h7f49494941;
            "G":glyph=40'h3e41495173; "I":glyph=40'h00417f4100;
            "H":glyph=40'h7f0808087f; "S":glyph=40'h2649494932;
            "Y":glyph=40'h0304780403;
            "L":glyph=40'h7f40404040; "M":glyph=40'h7f020c027f;
            "N":glyph=40'h7f0408107f; "O":glyph=40'h3e4141413e;
            "P":glyph=40'h7f09090906; "R":glyph=40'h7f09192946;
            "T":glyph=40'h01017f0101; "V":glyph=40'h1f2040201f;
            "X":glyph=40'h6314081463;
            "W":glyph=40'h3f4038403f; "U":glyph=40'h3f4040403f;
            default:glyph=40'h0000000000;
        endcase end
    endfunction
    function glyph_pixel;
        input [7:0] ch;
        input [3:0] x,y;
        reg [39:0] bits;
        begin
            bits=glyph(ch);
            glyph_pixel=(x<10 && y<14) && ((bits >> (((4-(x>>1))*8)+(y>>1))) & 1'b1);
        end
    endfunction
    function small_glyph_pixel;
        input [7:0] ch;
        input [3:0] x,y;
        reg [39:0] bits;
        begin
            bits=glyph(ch);
            small_glyph_pixel=(x<5 && y<7) && ((bits >> ((4-x)*8+y)) & 1'b1);
        end
    endfunction
    function [7:0] plot_title;
        input [1:0] p;input [3:0] n;
        begin
            case(p)
                0:case(n) 2:plot_title="W";3:plot_title="A";4:plot_title="V";5:plot_title="E";default:plot_title=" ";endcase
                1:case(n) 0:plot_title="S";1:plot_title="P";2:plot_title="E";3:plot_title="C";4:plot_title="T";5:plot_title="R";6:plot_title="U";7:plot_title="M";default:plot_title=" ";endcase
                default:case(n) 3:plot_title="X";4:plot_title="Y";default:plot_title=" ";endcase
            endcase
        end
    endfunction
    function [7:0] header_char;
        input [1:0] page_index;
        input [3:0] index;
        begin case(page_index)
            0:case(index)
                0:header_char="L";1:header_char="I";2:header_char="V";
                3:header_char="E";4:header_char=" ";5:header_char="M";
                6:header_char="I";default:header_char="X";
            endcase
            1:case(index)
                0:header_char="G";1:header_char="T";2:header_char="R";
                3:header_char=" ";4:header_char="F";5:header_char="X";
                default:header_char=" ";
            endcase
            default:case(index)
                0:header_char="S";1:header_char="P";2:header_char="A";
                3:header_char="C";4:header_char="E";5:header_char=" ";
                6:header_char="F";default:header_char="X";
            endcase
        endcase end
    endfunction
    function [7:0] row_char;
        input [1:0] page_index;
        input [1:0] row;
        input [1:0] index;
        begin case(page_index)
            0:case(row)
                0:case(index) 0:row_char="G";1:row_char="T";default:row_char="R";endcase
                1:case(index) 0:row_char="P";1:row_char="N";default:row_char="O";endcase
                default:case(index) 0:row_char="D";1:row_char="R";default:row_char="M";endcase
            endcase
            1:case(row)
                0:case(index) 0:row_char="D";1:row_char="R";default:row_char="V";endcase
                1:case(index) 0:row_char="T";1:row_char="O";default:row_char="N";endcase
                default:case(index) 0:row_char="M";1:row_char="I";default:row_char="X";endcase
            endcase
            default:case(row)
                0:case(index) 0:row_char="C";1:row_char="H";default:row_char="O";endcase
                1:case(index) 0:row_char="D";1:row_char="L";default:row_char="Y";endcase
                default:case(index) 0:row_char="D";1:row_char="E";default:row_char="P";endcase
            endcase
        endcase end
    endfunction
    function [7:0] decimal_char;
        input [6:0] value;
        input [1:0] index;
        reg [6:0] remainder;
        begin
            remainder=value>=100 ? value-100 : value;
            if(index==0) decimal_char=value>=100 ? "1" : " ";
            else if(index==1) decimal_char=(value>=100 || remainder>=10)
                ? ("0" + remainder/10) : " ";
            else decimal_char="0" + remainder%10;
        end
    endfunction
    reg [15:0] legacy_pixel_rgb;
    reg [255:0] frame_panel_values;reg [3:0] frame_panel_page,frame_panel_row,frame_panel_col;reg frame_panel_editing;
    wire [15:0] panel_pixel;
    panel_raster panel_view(.clk(clk),.x(render_x),.y(render_y),.plot_rgb(visual_pixel_rgb),
      .values(frame_panel_values),.page(frame_panel_page),.row(frame_panel_row),.col(frame_panel_col),.editing(frame_panel_editing),.pixel_rgb(panel_pixel));
    wire [15:0] pixel_rgb=PANEL_UI?panel_pixel:legacy_pixel_rgb;
    reg [6:0] row_level;
    reg [1:0] row_number;
    reg [7:0] row_top;
    integer i;
    always @* begin
        legacy_pixel_rgb=16'h0810; // dark background
        row_number=render_row;
        row_top=render_top;
        row_level=render_level;
        if(render_y<28) legacy_pixel_rgb=16'h1030;
        if(render_x>=7 && render_x<121 && render_y>=row_top+20 && render_y<row_top+28)
            legacy_pixel_rgb=(render_x-7 < ((row_level*7)>>3)) ?
                (row_number==frame_selected ? 16'h07ff : 16'h4a69) : 16'h2124;
        if(render_x>=6 && render_x<123 && render_y>=row_top-3 && render_y<row_top+17 &&
            frame_page==0 && row_number==frame_selected &&
            (render_x<8 || render_x>=121 || render_y<row_top-1 || render_y>=row_top+15))
            legacy_pixel_rgb=16'hffe0;
        for(i=0;i<8;i=i+1)
            if(render_x>=16+i*12 && render_x<26+i*12 && render_y>=7 && render_y<21 &&
                glyph_pixel(header_char(frame_page,i[3:0]),render_x-(16+i*12),render_y-7))
                legacy_pixel_rgb=16'hffff;
        for(i=0;i<3;i=i+1) begin
            if(render_x>=9+i*12 && render_x<19+i*12 && render_y>=row_top && render_y<row_top+14 &&
                glyph_pixel(row_char(frame_page,row_number,i[1:0]),render_x-(9+i*12),render_y-row_top))
                legacy_pixel_rgb=16'hffff;
            if(render_x>=83+i*12 && render_x<93+i*12 && render_y>=row_top && render_y<row_top+14 &&
                glyph_pixel(decimal_char(row_level,i[1:0]),render_x-(83+i*12),render_y-row_top))
                legacy_pixel_rgb=16'hffff;
        end
        // Green dot means drum machine loop is running; gray means stopped.
        if(frame_page==0 && render_x>=113 && render_x<121 && render_y>=10 && render_y<18)
            legacy_pixel_rgb=frame_drum_playing ? 16'h07e0 : 16'h4208;
        // Top-right number: guitar amp preset slot, or modulation slot.
        if(frame_page==1 && render_x>=88 && render_x<98 && render_y>=7 && render_y<21 &&
            glyph_pixel(decimal_char({2'b00,frame_amp},1),render_x-88,render_y-7)) legacy_pixel_rgb=16'hffe0;
        if(frame_page==1 && render_x>=100 && render_x<110 && render_y>=7 && render_y<21 &&
            glyph_pixel(decimal_char({2'b00,frame_amp},2),render_x-100,render_y-7)) legacy_pixel_rgb=16'hffe0;
        if(frame_page==1 && render_y>=146 && render_y<160) begin
            if(render_x>=9 && render_x<19 && glyph_pixel("M",render_x-9,render_y-146)) legacy_pixel_rgb=16'hffe0;
            if(render_x>=21 && render_x<31 && glyph_pixel("O",render_x-21,render_y-146)) legacy_pixel_rgb=16'hffe0;
            if(render_x>=33 && render_x<43 && glyph_pixel("D",render_x-33,render_y-146)) legacy_pixel_rgb=16'hffe0;
            if(render_x>=83 && render_x<93 &&
                glyph_pixel(decimal_char({4'b0000,frame_modulation},2),render_x-83,render_y-146))
                legacy_pixel_rgb=16'hffe0;
        end
        if(frame_page==3)begin
            legacy_pixel_rgb=visual_pixel_rgb;
            for(i=0;i<8;i=i+1)begin
                if(render_x>=12+i*12 && render_x<22+i*12 && render_y>=5 && render_y<19 &&
                   glyph_pixel(plot_title(frame_visual_page,i[3:0]),render_x-(12+i*12),render_y-5))
                    legacy_pixel_rgb=frame_visual_page==0 ? 16'h07ff : frame_visual_page==1 ? 16'h07e0 : 16'hf81f;
                if(render_x>=37+i*6 && render_x<42+i*6 && render_y>=153 &&
                   small_glyph_pixel(i==0 ? "G" : i==1 ? "1" : i==2 ? "5" : i==3 ? " " : i==4 ? "N" : i==5 ? "E" : i==6 ? "X" : "T",
                                     render_x-(37+i*6),render_y-153))legacy_pixel_rgb=16'hbdf7;
            end
        end
    end

    // One byte sender, CPOL=CPHA=0. 50 MHz / 8 = 6.25 MHz SPI.
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            byte_busy<=0;byte_done<=0;bit_index<=0;spi_div<=0;spi_phase<=0;
            lcd_sck<=0;lcd_sda<=0;lcd_cs_n<=1;lcd_dc<=0;
        end else begin
            byte_done<=0;
            if(byte_start && !byte_busy) begin
                byte_busy<=1;bit_index<=7;spi_div<=0;spi_phase<=0;
                lcd_cs_n<=0;lcd_dc<=tx_dc;lcd_sda<=tx_byte[7];lcd_sck<=0;
            end else if(byte_busy) begin
                if(spi_div==3) begin
                    spi_div<=0;
                    if(!spi_phase) begin lcd_sck<=1;spi_phase<=1;end
                    else begin
                        lcd_sck<=0;spi_phase<=0;
                        // Keep CS asserted across the RGB565 stream so RAMWR
                        // cannot be terminated between high/low pixel bytes.
                        if(bit_index==0) begin byte_busy<=0;byte_done<=1;end
                        else begin bit_index<=bit_index-1'b1;lcd_sda<=tx_byte[bit_index-1'b1];end
                    end
                end else spi_div<=spi_div+1'b1;
            end
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            frame_panel_values<=0;frame_panel_page<=0;frame_panel_row<=0;frame_panel_col<=0;frame_panel_editing<=0;
            state<=RESET_LOW;delay_count<=0;init_index<=0;header_index<=0;
            px<=0;py<=0;render_x<=0;render_y<=0;render_row<=0;
            render_top<=0;render_level<=0;pixel_rgb_q<=0;
            tx_byte<=0;tx_dc<=0;byte_start<=0;
            lcd_rst_n<=0;frame_guitar<=127;frame_piano<=127;frame_drum<=127;
            frame_selected<=0;frame_page<=3;frame_visual_page<=0;frame_drum_playing<=0;
            frame_drive<=0;frame_tone<=0;frame_fx_mix<=0;frame_amp<=0;
            frame_modulation<=0;frame_chorus<=0;frame_delay<=0;frame_depth<=0;
        end else begin
            byte_start<=0;
            case(state)
                RESET_LOW: if(delay_count==24'd499999) begin delay_count<=0;lcd_rst_n<=1;state<=RESET_HIGH;end
                    else delay_count<=delay_count+1'b1;
                RESET_HIGH: if(delay_count==24'd4999999) begin delay_count<=0;state<=INIT_SEND;end
                    else delay_count<=delay_count+1'b1;
                INIT_SEND: if(!byte_busy) begin
                    tx_byte<=init_byte(init_index);tx_dc<=(init_index==3 || init_index==5);
                    byte_start<=1;state<=INIT_WAIT;
                end
                INIT_WAIT: if(byte_done) begin
                    if(init_index==0 || init_index==1) begin delay_count<=0;state<=INIT_PAUSE;end
                    else if(init_index==6) begin header_index<=0;state<=HEADER_SEND;end
                    else begin init_index<=init_index+1'b1;state<=INIT_SEND;end
                end
                INIT_PAUSE: if(delay_count==24'd5999999) begin
                    init_index<=init_index+1'b1;state<=INIT_SEND;
                end else delay_count<=delay_count+1'b1;
                HEADER_SEND: if(!byte_busy) begin
                    tx_byte<=header_byte(header_index);
                    tx_dc<=!(header_index==0 || header_index==5 || header_index==10);
                    byte_start<=1;state<=HEADER_WAIT;
                end
                HEADER_WAIT: if(byte_done) begin
                    if(header_index==10) begin px<=0;py<=0;state<=PIXEL_PREP_A;end
                    else begin header_index<=header_index+1'b1;state<=HEADER_SEND;end
                end
                PIXEL_PREP_A: begin
                    render_x<=px;render_y<=py;
                    render_row<=py<69 ? 2'd0 : (py<110 ? 2'd1 : 2'd2);
                    render_top<=py<69 ? 8'd36 : (py<110 ? 8'd77 : 8'd118);
                    render_level<=frame_page==0
                        ? (py<69 ? frame_guitar : (py<110 ? frame_piano : frame_drum))
                        : frame_page==1
                            ? (py<69 ? frame_drive : (py<110 ? frame_tone : frame_fx_mix))
                            : (py<69 ? frame_chorus : (py<110 ? frame_delay : frame_depth));
                    state<=PIXEL_RAM_WAIT;
                end
                PIXEL_RAM_WAIT: state<=PANEL_UI?5'd15:PIXEL_PREP_B;
                15:state<=16;16:state<=17;17:state<=18;18:state<=PIXEL_PREP_B;
                PIXEL_PREP_B: begin pixel_rgb_q<=pixel_rgb;state<=PIXEL_HIGH;end
                PIXEL_HIGH: if(!byte_busy) begin
                    tx_byte<=pixel_rgb_q[15:8];tx_dc<=1;byte_start<=1;state<=PIXEL_HIGH_WAIT;
                end
                PIXEL_HIGH_WAIT: if(byte_done) state<=PIXEL_LOW;
                PIXEL_LOW: if(!byte_busy) begin
                    tx_byte<=pixel_rgb_q[7:0];tx_dc<=1;byte_start<=1;state<=PIXEL_LOW_WAIT;
                end
                PIXEL_LOW_WAIT: if(byte_done) begin
                    if(px==127) begin
                        px<=0;
                        if(py==159) begin delay_count<=0;state<=FRAME_PAUSE;end
                        else begin py<=py+1'b1;state<=PIXEL_PREP_A;end
                    end else begin px<=px+1'b1;state<=PIXEL_PREP_A;end
                end
                FRAME_PAUSE: if(delay_count==(PANEL_UI?24'd0:24'd1499999)) begin
                    delay_count<=0;header_index<=0;
                    frame_panel_values<=panel_values;frame_panel_page<=panel_page;frame_panel_row<=panel_row;frame_panel_col<=panel_col;frame_panel_editing<=panel_editing;
                    frame_guitar<=guitar_level;frame_piano<=piano_level;frame_drum<=drum_level;
                    frame_selected<=selected_bus;frame_drum_playing<=drum_playing;
                    frame_page<=page;frame_visual_page<=visual_page_select;frame_drive<=fx_drive;frame_tone<=fx_tone;
                    frame_fx_mix<=fx_mix;frame_amp<=fx_amp;frame_modulation<=fx_modulation;
                    frame_chorus<=chorus_mix;frame_delay<=delay_mix;frame_depth<=chorus_depth;
                    state<=HEADER_SEND;
                end else delay_count<=delay_count+1'b1;
                default:state<=RESET_LOW;
            endcase
        end
    end
endmodule

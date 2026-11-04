// Mode 0 / MSB first, 64-byte full-duplex, <=1 MHz with 50 MHz clk.
// All logic is clocked by clk: external SPI signals are synchronized.
// CRC is sequential over bytes; there is no 62-byte combinational CRC path.
module s3_spi_link #(
    parameter integer TOUCH_TIMEOUT_CLKS=25000000,parameter PANEL_TELEMETRY=0
)(
    input wire clk, input wire rst_n,
    input wire [255:0] panel_values,input wire [3:0] panel_ui_page,input wire [6:0] panel_motion,
    input wire spi_sclk, input wire spi_cs_n, input wire spi_mosi,
    output wire spi_miso, output reg fpga_irq, output wire fpga_ready,
    output reg [127:0] touch_keys, output reg [7:0] touch_online,
    output reg touch_enabled,
    output reg [5:0] hall_mask,output reg [47:0] hall_velocity,
    output reg [29:0] hall_frets,
    output reg hall_valid,input wire hall_ready,
    output reg [47:0] command_data, output reg command_valid,
    input wire command_ready,
    output reg [383:0] bulk_data,output reg [5:0] bulk_length,output reg [1:0] bulk_flags,
    output reg bulk_valid,input wire bulk_ready,input wire bulk_busy,input wire bulk_error,
    input wire [23:0] rgb24, input wire [7:0] pixel_x, input wire [7:0] pixel_y,
    input wire [1:0] display_page,input wire [1:0] instrument,
    input wire hall_mode,input wire [29:0] selected_frets,input wire [1:0] trigger_mode
);
    reg [2:0] sclk_sync,cs_sync,mosi_sync;
    wire sclk_rise=sclk_sync[2:1]==2'b01;
    wire sclk_fall=sclk_sync[2:1]==2'b10;
    wire cs_fall=cs_sync[2:1]==2'b10;
    wire cs_rise=cs_sync[2:1]==2'b01;
    reg [9:0] bit_count;
    reg [7:0] rx_byte;
    reg [7:0] rx_bytes[0:63];
    reg [15:0] rx_crc;
    reg [511:0] tx_shift,reply_frame;
    reg [15:0] last_sequence;
    reg [31:0] last_session,good_frames,bad_frames;
    reg have_sequence;
    reg [125:0] hall_scan_keys;
    reg [4:0] hall_scan_row;
    reg hall_scan_busy;
    reg [7:0] reply_bytes[0:63];
    reg [1:0] reply_state;reg [2:0] panel_bank;
    reg [5:0] reply_index;
    reg [15:0] reply_crc;
    reg reply_valid;
    reg [$clog2(TOUCH_TIMEOUT_CLKS+1)-1:0] touch_age;
    integer i;
    integer j;

    function [15:0] crc_byte;
        input [15:0] crc_in; input [7:0] data_in;
        reg [15:0] work; integer b;
        begin
            work=crc_in^{data_in,8'h00};
            for(b=0;b<8;b=b+1)
                work=work[15] ? (work<<1)^16'h1021 : work<<1;
            crc_byte=work;
        end
    endfunction
    function fixed_opcode;
        input [7:0] op;
        begin
            fixed_opcode=(op>=8'h02&&op<=8'h06)||op==8'h08||op==8'h09||op==8'h23||op==8'h24||
                (op>=8'h40&&op<=8'h44)||(op>=8'h50&&op<=8'h52)||
                op==8'h90||op==8'h91||op==8'h56||op==8'h57||(op>=8'h60&&op<=8'h62)||op==8'h70;
        end
    endfunction
    wire [15:0] incoming_seq={rx_bytes[5],rx_bytes[4]};
    wire [31:0] incoming_session={rx_bytes[59],rx_bytes[58],rx_bytes[57],rx_bytes[56]};
    wire duplicate=have_sequence&&incoming_seq==last_sequence&&incoming_session==last_session;
    wire fixed_ok=rx_bytes[24]==8'ha5&&fixed_opcode(rx_bytes[25])&&
        (rx_bytes[24]^rx_bytes[25]^rx_bytes[26]^rx_bytes[27]^rx_bytes[28]^rx_bytes[29])==0;
    wire hall_snapshot=rx_bytes[38]==8'hc1;
    wire hall_slot_ready=!hall_valid&&!hall_scan_busy;
    wire hall_ok=rx_bytes[31]!=0&&rx_bytes[31][7:6]==0&&
        (!hall_snapshot||rx_bytes[55][7:6]==0)&&
        (!rx_bytes[31][0]||(rx_bytes[32]>0&&rx_bytes[32]<128))&&
        (!rx_bytes[31][1]||(rx_bytes[33]>0&&rx_bytes[33]<128))&&
        (!rx_bytes[31][2]||(rx_bytes[34]>0&&rx_bytes[34]<128))&&
        (!rx_bytes[31][3]||(rx_bytes[35]>0&&rx_bytes[35]<128))&&
        (!rx_bytes[31][4]||(rx_bytes[36]>0&&rx_bytes[36]<128))&&
        (!rx_bytes[31][5]||(rx_bytes[37]>0&&rx_bytes[37]<128));
    wire packet_ok=bit_count==512&&rx_bytes[0]==8'ha5&&rx_bytes[1]==8'h53&&
        rx_bytes[2]==1&&(rx_bytes[3]==3||rx_bytes[23][7:6]==0)&&
        ((rx_bytes[3]==0&&rx_bytes[7]==16)||(rx_bytes[3]==1&&rx_bytes[7]==6&&fixed_ok)||
         (rx_bytes[3]==2&&rx_bytes[7]==7&&hall_ok)||
         (rx_bytes[3]==3&&rx_bytes[7]>0&&rx_bytes[7]<=48&&rx_bytes[6][7:2]==0))&&
        {rx_bytes[62],rx_bytes[63]}==rx_crc;
    wire [15:0] reply_crc_next=crc_byte(reply_crc,reply_bytes[reply_index]);
    // The physical select deasserts MISO immediately, not after CDC latency.
    assign spi_miso=spi_cs_n ? 1'bz : tx_shift[511];
    assign fpga_ready=reply_valid&&rst_n;

    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            sclk_sync<=0;cs_sync<=3'b111;mosi_sync<=0;
        end else begin
            sclk_sync<={sclk_sync[1:0],spi_sclk};
            cs_sync<={cs_sync[1:0],spi_cs_n};
            mosi_sync<={mosi_sync[1:0],spi_mosi};
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            bit_count<=0;rx_byte<=0;rx_crc<=16'hffff;tx_shift<=0;
            touch_keys<=0;touch_online<=0;command_data<=0;command_valid<=0;bulk_valid<=0;bulk_data<=0;bulk_length<=0;bulk_flags<=0;
            touch_enabled<=0;touch_age<=0;
            hall_mask<=0;hall_velocity<=0;hall_valid<=0;
            hall_frets<=0;hall_scan_keys<=0;hall_scan_row<=0;hall_scan_busy<=0;
            last_sequence<=0;last_session<=0;have_sequence<=0;
            good_frames<=0;bad_frames<=0;fpga_irq<=0;panel_bank<=0;
        end else begin
            if(touch_age<TOUCH_TIMEOUT_CLKS-1)touch_age<=touch_age+1'b1;
            else begin touch_keys<=0;touch_online<=0;touch_enabled<=0;end
            if(command_valid&&command_ready)command_valid<=0;
            if(bulk_valid&&bulk_ready)bulk_valid<=0;
            if(hall_valid&&hall_ready)hall_valid<=0;
            if(hall_scan_busy)begin
                hall_scan_keys<={6'd0,hall_scan_keys[125:6]};
                for(i=0;i<6;i=i+1)
                    if(hall_scan_keys[i])hall_frets[i*5+:5]<=hall_scan_row;
                if(hall_scan_row==20)begin hall_scan_busy<=0;hall_valid<=1;end
                else hall_scan_row<=hall_scan_row+1'b1;
            end
            if(cs_fall)begin
                bit_count<=0;rx_byte<=0;rx_crc<=16'hffff;
                tx_shift<=reply_frame;fpga_irq<=0;
            end else if(!cs_sync[2])begin
                if(sclk_rise)begin
                    rx_byte<={rx_byte[6:0],mosi_sync[2]};
                    if(bit_count<513)bit_count<=bit_count+1'b1;
                    if(bit_count<512&&bit_count[2:0]==7)begin
                        rx_bytes[bit_count[8:3]]<={rx_byte[6:0],mosi_sync[2]};
                        if(bit_count<496)rx_crc<=crc_byte(rx_crc,{rx_byte[6:0],mosi_sync[2]});
                    end
                end
                if(sclk_fall)tx_shift<={tx_shift[510:0],1'b0};
            end
            if(cs_rise)begin
                if(packet_ok)begin
                    good_frames<=good_frames+1'b1;if(PANEL_TELEMETRY)panel_bank<=panel_bank==5?0:panel_bank+1'b1;
                    if(!duplicate&&((rx_bytes[3]==0)||(rx_bytes[3]==1&&!command_valid)||(rx_bytes[3]==2&&hall_slot_ready)||(rx_bytes[3]==3&&!bulk_valid)))begin
                        last_sequence<=incoming_seq;last_session<=incoming_session;have_sequence<=1;
                        if(rx_bytes[3]!=3)begin
                        touch_online<=rx_bytes[6];
                        touch_enabled<=rx_bytes[30][0];touch_age<=0;
                        for(i=0;i<16;i=i+1)touch_keys[i*8+:8]<=rx_bytes[8+i];
                        end
                        if(rx_bytes[3]==3)begin
                            for(i=0;i<48;i=i+1)bulk_data[383-i*8-:8]<=rx_bytes[8+i];
                            bulk_length<=rx_bytes[7][5:0];bulk_flags<=rx_bytes[6][1:0];bulk_valid<=1;
                        end
                        if(rx_bytes[3]==1)begin
                            command_data<={rx_bytes[24],rx_bytes[25],rx_bytes[26],rx_bytes[27],rx_bytes[28],rx_bytes[29]};
                            command_valid<=1;
                        end
                        if(rx_bytes[3]==2)begin
                            hall_mask<=rx_bytes[31][5:0];hall_frets<=0;hall_scan_busy<=1;hall_scan_row<=0;
                            for(i=0;i<15;i=i+1)
                                hall_scan_keys[i*8+:8]<=hall_snapshot?rx_bytes[40+i]:rx_bytes[8+i];
                            hall_scan_keys[125:120]<=hall_snapshot?rx_bytes[55][5:0]:rx_bytes[23][5:0];
                            for(i=0;i<6;i=i+1)hall_velocity[i*8+:8]<=rx_bytes[32+i];
                        end
                        fpga_irq<=1;
                    end
                end else begin
                    bad_frames<=bad_frames+1'b1;fpga_irq<=1;
                end
            end
        end
    end

    // Coherent response snapshot. ACK describes an earlier complete request,
    // never the MOSI bytes currently being shifted in.
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin
            reply_state<=0;reply_index<=0;reply_crc<=16'hffff;
            reply_frame<=0;reply_valid<=0;
        end else case(reply_state)
            0:begin
                for(j=0;j<64;j=j+1)reply_bytes[j]<=0;
                reply_bytes[0]<=8'h5a;reply_bytes[1]<=8'h53;reply_bytes[2]<=1;
                reply_bytes[3]<={bulk_error,bulk_busy,!bulk_valid,1'b1,1'b0,fpga_irq,!command_valid,1'b1};
                reply_bytes[4]<=last_sequence[7:0];reply_bytes[5]<=last_sequence[15:8];
                reply_bytes[6]<=touch_online;
                reply_bytes[7]<={6'b0,instrument};
                for(j=0;j<4;j=j+1)begin
                    reply_bytes[8+j]<=good_frames[j*8+:8];
                    reply_bytes[12+j]<=bad_frames[j*8+:8];
                    reply_bytes[56+j]<=last_session[j*8+:8];
                end
                for(j=0;j<16;j=j+1)reply_bytes[16+j]<=touch_keys[j*8+:8];
                reply_bytes[32]<=rgb24[23:16];reply_bytes[33]<=rgb24[15:8];reply_bytes[34]<=rgb24[7:0];
                reply_bytes[35]<=pixel_x;reply_bytes[36]<=pixel_y;reply_bytes[37]<={6'b0,display_page};
                reply_bytes[38]<={7'b0,hall_mode};
                reply_bytes[39]<=8'ha0|{6'd0,trigger_mode};
                for(j=0;j<6;j=j+1)reply_bytes[40+j]<={3'b0,selected_frets[j*5+:5]};
                reply_bytes[46]<=8'hc1;
                reply_bytes[47]<={6'd0,hall_slot_ready,!command_valid};
                if(PANEL_TELEMETRY)begin
                 reply_bytes[48]<=8'hd0|{5'd0,panel_bank};reply_bytes[49]<=8'd8;
                 for(j=0;j<6;j=j+1)reply_bytes[50+j]<=(panel_bank==5&&j>=2)?8'd0:panel_values[(panel_bank*6+j)*8+:8];
                 reply_bytes[60]<={4'd0,panel_ui_page};reply_bytes[61]<={1'b0,panel_motion};
                end
                reply_index<=0;reply_crc<=16'hffff;reply_state<=1;
            end
            1:begin
                reply_crc<=reply_crc_next;
                if(reply_index==61)begin
                    reply_bytes[62]<=reply_crc_next[15:8];reply_bytes[63]<=reply_crc_next[7:0];reply_state<=2;
                end else reply_index<=reply_index+1'b1;
            end
            default:begin
                for(j=0;j<64;j=j+1)reply_frame[511-j*8-:8]<=reply_bytes[j];
                reply_valid<=1;reply_state<=0;
            end
        endcase
    end
endmodule

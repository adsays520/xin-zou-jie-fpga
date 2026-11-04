// Low-speed trigger receiver for the Tang Mega 138K Pro onboard BL616 bridge.
//
// Serial format: 115200 baud, 8 data bits, no parity, 1 stop bit.
// Trigger frame: A5 02 STRING FRET VELOCITY XOR
//   STRING   = 1..6
//   FRET     = 0..20
//   VELOCITY = 1..127 (forwarded to the selected instrument)
// Mode frame:    A5 03 MODE 00 00 XOR
//   MODE     = 0 for monophonic comparison, 1 for polyphonic operation
//   XOR      = XOR of the preceding five bytes
// Timbre frame:  A5 04 TIMBRE 00 00 XOR
//   TIMBRE   = 0 guitar, 1 piano, 2 independent Bass; top clears old voices
// Piano key:     A5 05 KEY VELOCITY ACTION XOR
//   KEY      = MIDI 21..108, ACTION=1 Note-On, ACTION=0 Note-Off
// Piano pedal:   A5 06 LEVEL 00 00 XOR
//   LEVEL    = 0 up, 1..3 half-pedal depths, 4 full sustain
//
// This module only emits control pulses. There is no audio data, clock, gain,
// pitch, damping or envelope connection here.
module guitar_uart_trigger #(
    parameter integer CLOCK_HZ = 50000000,
    parameter integer BAUD = 115200,
    parameter EXTERNAL_BYTES = 1'b0,
    parameter EXTERNAL_STAGE = 1'b0
)(
    input  wire       clk,
    input  wire       rst_n,
    input  wire       uart_rx_i,
    input wire [7:0] external_byte_data,input wire external_byte_valid,
    input wire stage_active,stage_valid,input wire [7:0] stage_index,stage_data,
    output wire upload_session,output reg bank_upload_cancel,
    input  wire       local_level_step,
    input  wire [1:0] local_level_bus,
    output reg  [2:0] trigger_string_sel,
    output reg  [4:0] trigger_fret_sel,
    output reg  [6:0] trigger_velocity,
    output reg        trigger,
    output reg        mode_set,
    output reg        mode_poly4,
    output reg        timbre_set,
    output reg        timbre_piano,
    output reg        timbre_bass,
    output reg timbre_violin,violin_note_on,violin_note_off,violin_legato,
    output reg [6:0] violin_key,violin_velocity,violin_bus_level,
    output reg hall_mode,trigger_mode_changed,
    output reg        piano_note_on,
    output reg        piano_note_off,
    output reg [6:0]  piano_key,
    output reg [6:0]  piano_velocity,
    output reg [2:0]  piano_pedal_level,
    output reg [6:0]  guitar_bus_level,
    output reg [6:0]  piano_bus_level,
    output reg [6:0]  drum_bus_level,
    input  wire       envelope_write_allowed,
    output reg        custom_envelope_mode,
    output reg        envelope_ram_we,
    output reg [11:0] envelope_ram_addr,
    output reg [15:0] envelope_ram_data,
    output reg        envelope_loaded,
    output reg        envelope_upload_error,
    output reg        envelope_command,
    output wire [7:0] uart_byte_data,
    output wire       uart_byte_valid,
    input wire bank_upload_ready,
    output reg bank_upload_begin,bank_upload_valid,bank_upload_commit,bank_upload_error,bank_query,
    output reg [10:0] bank_upload_index,output reg [2047:0] bank_upload_data,
    output reg [7:0] bank_query_sequence
    ,output reg ensemble_mode,ensemble_changed,ensemble_valid,ensemble_query
    ,output reg [1:0] ensemble_target
    ,output reg [7:0] ensemble_a,ensemble_b,ensemble_c,ensemble_sequence
    ,output reg [6:0] bass_bus_level
);
    localparam [7:0] SOF_COMMAND = 8'hA5;
    localparam [7:0] CMD_PLUCK = 8'h02;
    localparam [7:0] CMD_MODE = 8'h03;
    localparam [7:0] CMD_TIMBRE = 8'h04;
    localparam [7:0] CMD_PIANO_KEY = 8'h05;
    localparam [7:0] CMD_PIANO_PEDAL = 8'h06;
    // A5 70 BUS LEVEL 00 XOR; BUS=0 guitar, 1 piano/drawn, 2 drums.
    localparam [7:0] CMD_BUS_LEVEL = 8'h70;

    // Custom-envelope protocol.  Control frames keep the original six-byte
    // XOR format.  Data frames carry sixteen Q1.15 words and CRC16-CCITT:
    //   A5 11 ADDR_H ADDR_L DATA[32] CRC_H CRC_L
    // BEGIN invalidates the old custom table; COMMIT succeeds only after all
    // 4096 words have arrived in strictly increasing sixteen-word blocks.
    localparam [7:0] CMD_ENV_BEGIN  = 8'h10;
    localparam [7:0] CMD_ENV_DATA   = 8'h11;
    localparam [7:0] CMD_ENV_COMMIT = 8'h12;
    localparam [7:0] CMD_ENV_SELECT = 8'h13;

    localparam [3:0] PARSE_SOF       = 4'd0;
    localparam [3:0] PARSE_COMMAND   = 4'd1;
    localparam [3:0] PARSE_FIXED     = 4'd2;
    localparam [3:0] PARSE_FIXED_XOR = 4'd3;
    localparam [3:0] PARSE_ENV_AH    = 4'd4;
    localparam [3:0] PARSE_ENV_AL    = 4'd5;
    localparam [3:0] PARSE_ENV_DATA  = 4'd6;
    localparam [3:0] PARSE_ENV_CRCH  = 4'd7;
    localparam [3:0] PARSE_ENV_CRCL  = 4'd8;
    localparam [3:0] PARSE_ENV_WRITE = 4'd9;
    localparam [3:0] PARSE_DRAW_SKIP = 4'd10;

    wire [7:0] rx_data;
    wire rx_valid;
    wire [7:0] physical_rx_data;wire physical_rx_valid;
    wire stage_owner=EXTERNAL_STAGE&&stage_active;
    assign rx_data=EXTERNAL_BYTES?external_byte_data:physical_rx_data;
    assign rx_valid=EXTERNAL_BYTES?external_byte_valid:physical_rx_valid;
    reg bank_upload_active;
    assign upload_session=bank_upload_active;
    assign uart_byte_data=rx_data;
    reg [7:0] bank_byte_index;reg [1:0] bank_crc_index;
    reg [31:0] bank_crc,bank_received_crc;
    localparam [3:0] PARSE_BANK_DATA=11,PARSE_BANK_CRC=12,PARSE_BANK_SKIP=13;
    reg [5:0] draw_skip_count;reg [8:0] bank_skip_count;
    reg [3:0] parser_state;
    assign uart_byte_valid=rx_valid&&!bank_upload_active&&parser_state!=PARSE_BANK_DATA&&
        parser_state!=PARSE_BANK_CRC&&parser_state!=PARSE_BANK_SKIP;
    reg [7:0] frame_command;
    reg [7:0] frame_payload0;
    reg [7:0] frame_payload1;
    reg [7:0] frame_payload2;
    reg [7:0] frame_xor;
    reg [1:0] fixed_index;
    reg [15:0] frame_crc;
    reg [7:0] received_crc_high;
    reg [7:0] envelope_data_high;
    reg [5:0] envelope_data_index;
    reg [11:0] envelope_packet_addr;
    reg [15:0] envelope_packet_words [0:15];
    reg [3:0] envelope_write_index;
    reg [12:0] envelope_expected_addr;
    reg envelope_upload_active;
    localparam integer PACKET_IDLE_CLKS=CLOCK_HZ/20;
    reg [$clog2(PACKET_IDLE_CLKS+1)-1:0] packet_idle_clocks;

    function [15:0] crc16_ccitt_byte;
        input [15:0] crc_in;
        input [7:0] data_in;
        integer bit_index;
        reg [15:0] crc_work;
        begin
            crc_work = crc_in ^ {data_in, 8'h00};
            for (bit_index = 0; bit_index < 8; bit_index = bit_index + 1)
                if (crc_work[15])
                    crc_work = (crc_work << 1) ^ 16'h1021;
                else
                    crc_work = crc_work << 1;
            crc16_ccitt_byte = crc_work;
        end
    endfunction

    function [31:0] bank_crc_byte;
        input [31:0] c0;input [7:0] b;reg [31:0] c;integer k;
        begin c=c0^{24'd0,b};for(k=0;k<8;k=k+1)c=c[0]?(c>>1)^32'hedb88320:(c>>1);bank_crc_byte=c;end
    endfunction
    uart_rx_8n1 #(
        .CLOCK_HZ(CLOCK_HZ),
        .BAUD(BAUD)
    ) u_uart_rx (
        .clk(clk),
        .rst_n(rst_n),
        .rx_i(uart_rx_i),
        .data_o(physical_rx_data),
        .data_valid_o(physical_rx_valid)
    );

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            ensemble_mode<=0;ensemble_changed<=0;ensemble_valid<=0;ensemble_query<=0;
            ensemble_target<=0;ensemble_a<=0;ensemble_b<=0;ensemble_c<=0;ensemble_sequence<=0;bass_bus_level<=127;
            parser_state <= PARSE_SOF;
            bank_upload_active<=0;bank_byte_index<=0;bank_crc_index<=0;bank_crc<=32'hffffffff;bank_received_crc<=0;
            bank_upload_cancel<=0;bank_upload_begin<=0;bank_upload_valid<=0;bank_upload_commit<=0;bank_upload_error<=0;bank_query<=0;
            bank_upload_index<=0;bank_upload_data<=0;bank_query_sequence<=0;
            packet_idle_clocks <= 0;
            frame_command <= 8'd0;
            frame_payload0 <= 8'd0;
            frame_payload1 <= 8'd0;
            frame_payload2 <= 8'd0;
            frame_xor <= 8'd0;
            fixed_index <= 2'd0;
            frame_crc <= 16'hffff;
            received_crc_high <= 8'd0;
            envelope_data_high <= 8'd0;
            envelope_data_index <= 6'd0;
            envelope_packet_addr <= 12'd0;
            envelope_write_index <= 4'd0;
            envelope_expected_addr <= 13'd0;
            envelope_upload_active <= 1'b0;
            draw_skip_count <= 0;bank_skip_count<=0;
            trigger_string_sel <= 3'd5;
            trigger_fret_sel <= 5'd0;
            trigger_velocity <= 7'd110;
            bank_upload_cancel<=0;bank_upload_begin<=0;bank_upload_valid<=0;bank_upload_commit<=0;bank_upload_error<=0;bank_query<=0;
            trigger <= 1'b0;
            mode_set <= 1'b0;
            mode_poly4 <= 1'b0;
            timbre_set <= 1'b0;
            timbre_piano <= 1'b0;
            timbre_bass <= 1'b0;
            timbre_violin<=0;violin_note_on<=0;violin_note_off<=0;violin_legato<=0;
            violin_key<=69;violin_velocity<=100;violin_bus_level<=127;hall_mode<=0;trigger_mode_changed<=0;
            piano_note_on <= 1'b0;
            piano_note_off <= 1'b0;
            piano_key <= 7'd60;
            piano_velocity <= 7'd96;
            piano_pedal_level <= 3'd0;
            guitar_bus_level <= 7'd127;
            piano_bus_level <= 7'd127;
            drum_bus_level <= 7'd127;
            custom_envelope_mode <= 1'b0;
            envelope_ram_we <= 1'b0;
            envelope_ram_addr <= 12'd0;
            envelope_ram_data <= 16'd0;
            envelope_loaded <= 1'b0;
            envelope_upload_error <= 1'b0;
            envelope_command <= 1'b0;
        end else begin
            ensemble_changed<=0;ensemble_valid<=0;ensemble_query<=0;
            violin_note_on<=0;violin_note_off<=0;trigger_mode_changed<=0;
            bank_upload_cancel<=0;bank_upload_begin<=0;bank_upload_valid<=0;bank_upload_commit<=0;bank_upload_error<=0;bank_query<=0;
            trigger <= 1'b0;
            mode_set <= 1'b0;
            timbre_set <= 1'b0;
            piano_note_on <= 1'b0;
            piano_note_off <= 1'b0;
            envelope_ram_we <= 1'b0;
            envelope_command <= 1'b0;
            if((stage_owner&&stage_valid)||(!stage_owner&&rx_valid&&parser_state==PARSE_BANK_DATA))
                bank_upload_data[(stage_owner?stage_index:bank_byte_index)*8+:8]<=stage_owner?stage_data:rx_data;
            if (local_level_step) begin
                case (local_level_bus)
                    2'd0: guitar_bus_level <= guitar_bus_level >= 7'd120 ? 7'd0 : guitar_bus_level + 7'd8;
                    2'd1: piano_bus_level <= piano_bus_level >= 7'd120 ? 7'd0 : piano_bus_level + 7'd8;
                    2'd3: violin_bus_level<=violin_bus_level>=120?0:violin_bus_level+8;
                    2'd2: drum_bus_level <= drum_bus_level >= 7'd120 ? 7'd0 : drum_bus_level + 7'd8;
                endcase
            end

            if(rx_valid||parser_state==PARSE_SOF||parser_state==PARSE_ENV_WRITE)
                packet_idle_clocks<=0;
            else if(packet_idle_clocks<PACKET_IDLE_CLKS)
                packet_idle_clocks<=packet_idle_clocks+1'b1;
            // A valid sixteen-word packet is drained into the RAM in sixteen
            // 50 MHz clocks (0.32 us), far below the 86.8 us UART byte time.
            // This packet buffer is therefore sufficient; a stream FIFO is
            // not required at 115200 baud.
            if(!rx_valid&&parser_state!=PARSE_SOF&&parser_state!=PARSE_ENV_WRITE&&
                packet_idle_clocks==PACKET_IDLE_CLKS)begin
                parser_state<=PARSE_SOF;
                if(parser_state==PARSE_BANK_DATA||parser_state==PARSE_BANK_CRC)bank_upload_error<=1;
                if(parser_state>=PARSE_ENV_AH&&parser_state<=PARSE_ENV_CRCL)
                    envelope_upload_error<=1;
            end else if (parser_state == PARSE_ENV_WRITE) begin
                envelope_ram_we <= 1'b1;
                envelope_ram_addr <= envelope_packet_addr
                    + envelope_write_index;
                envelope_ram_data <= envelope_packet_words[envelope_write_index];
                if (envelope_write_index == 4'd15) begin
                    envelope_expected_addr <= envelope_expected_addr + 13'd16;
                    envelope_write_index <= 4'd0;
                    parser_state <= PARSE_SOF;
                end else begin
                    envelope_write_index <= envelope_write_index + 1'b1;
                end
            end else if (rx_valid) begin
                case (parser_state)
                    PARSE_SOF: begin
                        if (rx_data == SOF_COMMAND) begin
                            frame_xor <= SOF_COMMAND;
                            frame_crc <= crc16_ccitt_byte(16'hffff,
                                SOF_COMMAND);
                            parser_state <= PARSE_COMMAND;
                        end
                    end
                    PARSE_COMMAND: begin
                        frame_command <= rx_data;
                        frame_xor <= frame_xor ^ rx_data;
                        frame_crc <= crc16_ccitt_byte(frame_crc, rx_data);
                        if (rx_data == CMD_ENV_DATA)
                            parser_state <= PARSE_ENV_AH;
                        else if (rx_data == 8'h21 || rx_data == 8'h31) begin
                            // Skip the entire new 38-byte packet. Embedded
                            // A5 bytes must never masquerade as guitar notes.
                            draw_skip_count <= 6'd36;
                            parser_state <= PARSE_DRAW_SKIP;
                        end
                        else begin
                            fixed_index <= 2'd0;
                            parser_state <= PARSE_FIXED;
                        end
                    end
                    PARSE_BANK_DATA:begin
                        // Parameter bytes are written by the shared staging port below.
                        bank_crc<=bank_crc_byte(bank_crc,rx_data);
                        if(bank_byte_index==255)begin parser_state<=PARSE_BANK_CRC;bank_crc_index<=0;end
                        else bank_byte_index<=bank_byte_index+1'b1;
                    end
                    PARSE_BANK_CRC:begin
                        bank_received_crc[bank_crc_index*8+:8]<=rx_data;
                        if(bank_crc_index==3)begin
                            parser_state<=PARSE_SOF;
                            if({rx_data,bank_received_crc[23:0]}==(bank_crc^32'hffffffff)&&bank_upload_ready&&!stage_owner)bank_upload_valid<=1;
                            else if(!stage_owner)bank_upload_error<=1;
                        end else bank_crc_index<=bank_crc_index+1'b1;
                    end
                    PARSE_BANK_SKIP:begin
                        if(bank_skip_count==1)parser_state<=PARSE_SOF;
                        else bank_skip_count<=bank_skip_count-1'b1;
                    end
                    PARSE_DRAW_SKIP: begin
                        if(draw_skip_count==1)parser_state<=PARSE_SOF;
                        else draw_skip_count<=draw_skip_count-1'b1;
                    end
                    PARSE_FIXED: begin
                        case (fixed_index)
                            2'd0: frame_payload0 <= rx_data;
                            2'd1: frame_payload1 <= rx_data;
                            default: frame_payload2 <= rx_data;
                        endcase
                        frame_xor <= frame_xor ^ rx_data;
                        if (fixed_index == 2'd2)
                            parser_state <= PARSE_FIXED_XOR;
                        else
                            fixed_index <= fixed_index + 1'b1;
                    end
                    PARSE_FIXED_XOR: begin
                        parser_state <= PARSE_SOF;
                        if(frame_command==8'hb0)begin
                            // B0 always occupies 266 bytes, even if its header
                            // is invalid or SD currently owns the staging RAM.
                            if(rx_data==frame_xor&&frame_payload2==1&&{frame_payload1,frame_payload0}<1100&&bank_upload_active&&!stage_owner)begin
                                bank_upload_index<={frame_payload1[2:0],frame_payload0};bank_byte_index<=0;bank_crc<=32'hffffffff;parser_state<=PARSE_BANK_DATA;
                            end else begin
                                bank_skip_count<=260;parser_state<=PARSE_BANK_SKIP;
                                if(bank_upload_active&&!stage_owner)bank_upload_error<=1;
                            end
                        end else if(rx_data==frame_xor&&frame_command==8'hb1&&!stage_owner&&frame_payload0==0&&frame_payload1==0&&frame_payload2==0)begin
                            bank_upload_active<=1;bank_upload_begin<=1;
                        end else if(rx_data==frame_xor&&frame_command==8'hb2&&frame_payload0==0&&frame_payload1==0&&frame_payload2==0)begin
                            bank_upload_active<=0;bank_upload_commit<=1;
                        end else if(rx_data==frame_xor&&frame_command==8'hb3&&frame_payload1==0&&frame_payload2==0)begin
                            bank_query<=1;bank_query_sequence<=frame_payload0;
                        end else if(rx_data==frame_xor&&frame_command==8'hb4&&frame_payload0==0&&frame_payload1==0&&frame_payload2==0)begin
                            bank_upload_active<=0;bank_upload_cancel<=1;
                        end else if ((!bank_upload_active && rx_data == frame_xor) &&
                            (frame_command == CMD_PLUCK) &&
                            (frame_payload0 >= 8'd1) &&
                            (frame_payload0 <= 8'd6) &&
                            (frame_payload1 <= 8'd20) &&
                            (frame_payload2 >= 8'd1) &&
                            (frame_payload2 <= 8'd127)) begin
                            trigger_string_sel <= frame_payload0[2:0] - 1'b1;
                            trigger_fret_sel <= frame_payload1[4:0];
                            trigger_velocity <= frame_payload2[6:0];
                            trigger <= 1'b1;
                        end else if ((!bank_upload_active && rx_data == frame_xor) &&
                            (frame_command == CMD_MODE) &&
                            (frame_payload0 <= 8'd1) &&
                            (frame_payload1 == 8'd0) &&
                            (frame_payload2 == 8'd0)) begin
                            mode_poly4 <= frame_payload0[0];
                            mode_set <= 1'b1;
                            if(ensemble_mode)begin ensemble_mode<=0;ensemble_changed<=1;end
                        end else if ((!bank_upload_active && rx_data == frame_xor) &&
                            (frame_command == CMD_TIMBRE) &&
                            (frame_payload0 <= 8'd3) &&
                            (frame_payload1 == 8'd0) &&
                            (frame_payload2 == 8'd0)) begin
                            timbre_piano <= frame_payload0==8'd1;
                            timbre_bass <= frame_payload0==8'd2;
                            timbre_violin <= frame_payload0==8'd3;
                            timbre_set <= 1'b1;
                            if(ensemble_mode)begin ensemble_mode<=0;ensemble_changed<=1;end
                        end else if(!bank_upload_active&&rx_data==frame_xor&&frame_command==8'h0e&&
                            frame_payload0<=1&&frame_payload1==0&&frame_payload2==0)begin
                            ensemble_mode<=frame_payload0[0];ensemble_changed<=1;
                        end else if(!bank_upload_active&&rx_data==frame_xor&&frame_command==8'h0f&&
                            frame_payload1==0&&frame_payload2==0)begin
                            ensemble_query<=1;ensemble_sequence<=frame_payload0;
                        end else if(!bank_upload_active&&rx_data==frame_xor&&ensemble_mode&&
                            ((frame_command==8'h0a&&frame_payload0>=1&&frame_payload0<=6&&frame_payload1<=20&&frame_payload2>=1&&frame_payload2<=127)||
                             (frame_command==8'h0b&&frame_payload0>=3&&frame_payload0<=6&&frame_payload1<=20&&frame_payload2>=1&&frame_payload2<=127)||
                             (frame_command==8'h0c&&frame_payload0>=21&&frame_payload0<=108&&frame_payload1>=1&&frame_payload1<=127&&frame_payload2<=1)||
                             (frame_command==8'h0d&&frame_payload0>=55&&frame_payload0<=100&&frame_payload1>=1&&frame_payload1<=127&&
                              (frame_payload2==0||frame_payload2==1||frame_payload2==3))))begin
                            ensemble_valid<=1;ensemble_target<=frame_command[1:0]-2'd2;
                            ensemble_a<=frame_payload0;ensemble_b<=frame_payload1;ensemble_c<=frame_payload2;
                        end else if ((!bank_upload_active && rx_data == frame_xor) &&
                            (frame_command == 8'h09) && frame_payload0<=2 && frame_payload1==0 && frame_payload2==0) begin
                            // Preserve R15 ESP numbering: 0=default, 1=direct, 2=Hall.
                            // The unsoldered physical switch is not consulted; default is direct.
                            hall_mode<=frame_payload0==2;trigger_mode_changed<=1;
                        end else if ((!bank_upload_active && rx_data == frame_xor) &&
                            frame_command==8'h08 && frame_payload0>=55 && frame_payload0<=100 &&
                            frame_payload1>=1 && frame_payload1<=127 &&
                            (frame_payload2==0 || frame_payload2==1 || frame_payload2==3)) begin
                            violin_key<=frame_payload0[6:0];violin_velocity<=frame_payload1[6:0];
                            violin_legato<=frame_payload2[1];violin_note_on<=frame_payload2[0];violin_note_off<=!frame_payload2[0];
                        end else if ((!bank_upload_active && rx_data == frame_xor) &&
                            (frame_command == CMD_PIANO_KEY) &&
                            (frame_payload0 >= 8'd21) &&
                            (frame_payload0 <= 8'd108) &&
                            (frame_payload1 >= 8'd1) &&
                            (frame_payload1 <= 8'd127) &&
                            (frame_payload2 <= 8'd1)) begin
                            piano_key <= frame_payload0[6:0];
                            piano_velocity <= frame_payload1[6:0];
                            if (frame_payload2[0]) piano_note_on <= 1'b1;
                            else piano_note_off <= 1'b1;
                        end else if ((!bank_upload_active && rx_data == frame_xor) &&
                            (frame_command == CMD_PIANO_PEDAL) &&
                            (frame_payload0 <= 8'd4) &&
                            (frame_payload1 == 8'd0) &&
                            (frame_payload2 == 8'd0)) begin
                            piano_pedal_level <= frame_payload0[2:0];
                        end else if ((!bank_upload_active && rx_data == frame_xor) &&
                            (frame_command == CMD_BUS_LEVEL) &&
                            (frame_payload0 <= 8'd4) &&
                            (frame_payload1 <= 8'd127) &&
                            (frame_payload2 == 8'd0)) begin
                            case (frame_payload0)
                                8'd0: guitar_bus_level <= frame_payload1[6:0];
                                8'd1: piano_bus_level <= frame_payload1[6:0];
                                8'd3: violin_bus_level<=frame_payload1[6:0];
                                8'd2: drum_bus_level <= frame_payload1[6:0];
                                8'd4: bass_bus_level <= frame_payload1[6:0];
                            endcase
                        end else if ((!bank_upload_active && rx_data == frame_xor) &&
                            (frame_command == CMD_ENV_BEGIN) &&
                            (frame_payload0 == 8'd0) &&
                            (frame_payload1 == 8'd0) &&
                            (frame_payload2 == 8'd0)) begin
                            envelope_command <= 1'b1;
                            if (envelope_write_allowed) begin
                                envelope_expected_addr <= 13'd0;
                                envelope_upload_active <= 1'b1;
                                envelope_loaded <= 1'b0;
                                envelope_upload_error <= 1'b0;
                                custom_envelope_mode <= 1'b0;
                            end else begin
                                envelope_upload_error <= 1'b1;
                            end
                        end else if ((!bank_upload_active && rx_data == frame_xor) &&
                            (frame_command == CMD_ENV_COMMIT) &&
                            (frame_payload0 == 8'd0) &&
                            (frame_payload1 == 8'd0) &&
                            (frame_payload2 == 8'd0)) begin
                            envelope_command <= 1'b1;
                            if (envelope_upload_active &&
                                envelope_expected_addr == 13'd4096) begin
                                envelope_loaded <= 1'b1;
                                envelope_upload_active <= 1'b0;
                            end else begin
                                envelope_upload_error <= 1'b1;
                            end
                        end else if ((!bank_upload_active && rx_data == frame_xor) &&
                            (frame_command == CMD_ENV_SELECT) &&
                            (frame_payload0 <= 8'd1) &&
                            (frame_payload1 == 8'd0) &&
                            (frame_payload2 == 8'd0)) begin
                            envelope_command <= 1'b1;
                            if (!frame_payload0[0])
                                custom_envelope_mode <= 1'b0;
                            else if (envelope_loaded)
                                custom_envelope_mode <= 1'b1;
                        end
                    end

                    PARSE_ENV_AH: begin
                        envelope_packet_addr[11:8] <= rx_data[3:0];
                        frame_crc <= crc16_ccitt_byte(frame_crc, rx_data);
                        parser_state <= PARSE_ENV_AL;
                    end
                    PARSE_ENV_AL: begin
                        envelope_packet_addr[7:0] <= rx_data;
                        frame_crc <= crc16_ccitt_byte(frame_crc, rx_data);
                        envelope_data_index <= 6'd0;
                        parser_state <= PARSE_ENV_DATA;
                    end
                    PARSE_ENV_DATA: begin
                        frame_crc <= crc16_ccitt_byte(frame_crc, rx_data);
                        if (!envelope_data_index[0])
                            envelope_data_high <= rx_data;
                        else
                            envelope_packet_words[envelope_data_index[5:1]]
                                <= {envelope_data_high, rx_data};
                        if (envelope_data_index == 6'd31)
                            parser_state <= PARSE_ENV_CRCH;
                        else
                            envelope_data_index <= envelope_data_index + 1'b1;
                    end
                    PARSE_ENV_CRCH: begin
                        received_crc_high <= rx_data;
                        parser_state <= PARSE_ENV_CRCL;
                    end
                    PARSE_ENV_CRCL: begin
                        if ({received_crc_high, rx_data} == frame_crc &&
                            envelope_upload_active &&
                            envelope_write_allowed &&
                            {1'b0, envelope_packet_addr}
                                == envelope_expected_addr &&
                            !envelope_packet_addr[3:0]) begin
                            envelope_write_index <= 4'd0;
                            parser_state <= PARSE_ENV_WRITE;
                        end else begin
                            envelope_upload_error <= 1'b1;
                            parser_state <= PARSE_SOF;
                        end
                    end
                    default: parser_state <= PARSE_SOF;
                endcase
            end
        end
    end
endmodule


module uart_rx_8n1 #(
    parameter integer CLOCK_HZ = 50000000,
    parameter integer BAUD = 115200
)(
    input  wire       clk,
    input  wire       rst_n,
    input  wire       rx_i,
    output reg  [7:0] data_o,
    output reg        data_valid_o
);
    localparam integer CLKS_PER_BIT = (CLOCK_HZ + (BAUD / 2)) / BAUD;
    localparam integer HALF_CLKS = CLKS_PER_BIT / 2;
    localparam [1:0] RX_IDLE = 2'd0;
    localparam [1:0] RX_START = 2'd1;
    localparam [1:0] RX_DATA = 2'd2;
    localparam [1:0] RX_STOP = 2'd3;

    reg rx_meta;
    reg rx_sync;
    reg [1:0] state;
    reg [15:0] clock_count;
    reg [2:0] bit_index;
    reg [7:0] data_shift;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rx_meta <= 1'b1;
            rx_sync <= 1'b1;
        end else begin
            rx_meta <= rx_i;
            rx_sync <= rx_meta;
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= RX_IDLE;
            clock_count <= 16'd0;
            bit_index <= 3'd0;
            data_shift <= 8'd0;
            data_o <= 8'd0;
            data_valid_o <= 1'b0;
        end else begin
            data_valid_o <= 1'b0;
            case (state)
                RX_IDLE: begin
                    clock_count <= 16'd0;
                    bit_index <= 3'd0;
                    if (!rx_sync)
                        state <= RX_START;
                end
                RX_START: begin
                    if (clock_count == HALF_CLKS - 1) begin
                        clock_count <= 16'd0;
                        if (!rx_sync)
                            state <= RX_DATA;
                        else
                            state <= RX_IDLE;
                    end else begin
                        clock_count <= clock_count + 1'b1;
                    end
                end
                RX_DATA: begin
                    if (clock_count == CLKS_PER_BIT - 1) begin
                        clock_count <= 16'd0;
                        data_shift[bit_index] <= rx_sync;
                        if (bit_index == 3'd7) begin
                            bit_index <= 3'd0;
                            state <= RX_STOP;
                        end else begin
                            bit_index <= bit_index + 1'b1;
                        end
                    end else begin
                        clock_count <= clock_count + 1'b1;
                    end
                end
                default: begin
                    if (clock_count == CLKS_PER_BIT - 1) begin
                        clock_count <= 16'd0;
                        state <= RX_IDLE;
                        if (rx_sync) begin
                            data_o <= data_shift;
                            data_valid_o <= 1'b1;
                        end
                    end else begin
                        clock_count <= clock_count + 1'b1;
                    end
                end
            endcase
        end
    end
endmodule

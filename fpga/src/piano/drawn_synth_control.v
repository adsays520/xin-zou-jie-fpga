// Independent drawn-synth upload decoder. Old guitar envelope commands are
// untouched. Only complete, CRC-checked wave+envelope pairs may be selected.
module drawn_synth_control #(
    parameter integer PACKET_IDLE_CLKS=2500000 // 50 ms at the board's 50 MHz.
)(
    input wire clk,input wire rst_n,input wire byte_valid,input wire [7:0] byte_data,
    input wire write_allowed,
    output reg mode,output reg mode_event,
    output reg [23:0] envelope_step,
    output reg ram_we,output reg [13:0] ram_addr,output reg [15:0] ram_data,
    output reg wave_loaded,output reg envelope_loaded,output reg upload_error
);
    localparam [3:0] SOF=0,CMD=1,FIXED=2,CHECK=3,AH=4,AL=5,
        DATA=6,CRCH=7,CRCL=8,WRITE=9,SKIP=10;
    reg [3:0] state;
    reg [7:0] command,p0,p1,p2,checksum,high_byte,crc_high;
    reg [1:0] fixed_index;
    reg [5:0] data_index,skip_count;
    reg [15:0] packet_address,crc;
    reg [15:0] words[0:15];
    reg [3:0] write_index;
    reg [13:0] wave_expected,envelope_expected;
    reg wave_upload,envelope_upload;
    reg [$clog2(PACKET_IDLE_CLKS+1)-1:0] idle_clocks;
    wire wave_packet=command==8'h21;
    wire [23:0] requested_step={p0,p1,p2};
    function [15:0] crc_byte;
        input [15:0] previous;input [7:0] value;
        reg [15:0] result;integer i;
        begin
            result=previous^{value,8'd0};
            for(i=0;i<8;i=i+1)
                result=result[15]?(result<<1)^16'h1021:(result<<1);
            crc_byte=result;
        end
    endfunction
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin
            state<=SOF;command<=0;p0<=0;p1<=0;p2<=0;checksum<=0;
            high_byte<=0;crc_high<=0;fixed_index<=0;data_index<=0;skip_count<=0;
            packet_address<=0;crc<=16'hffff;write_index<=0;
            wave_expected<=0;envelope_expected<=0;wave_upload<=0;envelope_upload<=0;
            idle_clocks<=0;
            mode<=0;mode_event<=0;envelope_step<=24'd3994;
            ram_we<=0;ram_addr<=0;ram_data<=0;
            wave_loaded<=0;envelope_loaded<=0;upload_error<=0;
        end else begin
            ram_we<=0;mode_event<=0;
            if(byte_valid||state==SOF||state==WRITE)idle_clocks<=0;
            else if(idle_clocks<PACKET_IDLE_CLKS)idle_clocks<=idle_clocks+1'b1;
            if(!byte_valid&&state!=SOF&&state!=WRITE&&idle_clocks==PACKET_IDLE_CLKS)begin
                state<=SOF;
                if((command>=8'h20&&command<=8'h24)||(command>=8'h30&&command<=8'h32))
                    upload_error<=1;
            end else if(state==WRITE)begin
                ram_we<=1;
                ram_addr<=(wave_packet?14'd0:14'd8192)+packet_address[13:0]+write_index;
                ram_data<=words[write_index];
                if(write_index==15)begin
                    if(wave_packet)wave_expected<=wave_expected+14'd16;
                    else envelope_expected<=envelope_expected+14'd16;
                    state<=SOF;
                end else write_index<=write_index+1'b1;
            end else if(byte_valid)begin
                case(state)
                    SOF:if(byte_data==8'ha5)begin
                        checksum<=8'ha5;crc<=crc_byte(16'hffff,8'ha5);state<=CMD;
                    end
                    CMD:begin
                        command<=byte_data;checksum<=checksum^byte_data;
                        crc<=crc_byte(crc,byte_data);fixed_index<=0;
                        if(byte_data==8'h21||byte_data==8'h31)state<=AH;
                        else if(byte_data==8'h11)begin skip_count<=36;state<=SKIP;end
                        else state<=FIXED;
                    end
                    SKIP:if(skip_count==1)state<=SOF;else skip_count<=skip_count-1'b1;
                    FIXED:begin
                        if(fixed_index==0)p0<=byte_data;
                        else if(fixed_index==1)p1<=byte_data;
                        else p2<=byte_data;
                        checksum<=checksum^byte_data;
                        if(fixed_index==2)state<=CHECK;else fixed_index<=fixed_index+1'b1;
                    end
                    CHECK:begin
                        state<=SOF;
                        if(byte_data==checksum)begin
                            case(command)
                                8'h20:if({p0,p1,p2}==0)begin
                                    if(write_allowed)begin
                                        wave_expected<=0;wave_upload<=1;
                                        envelope_upload<=0;wave_loaded<=0;envelope_loaded<=0;
                                        upload_error<=0;mode<=0;mode_event<=1;
                                    end else upload_error<=1;
                                end
                                8'h22:if({p0,p1,p2}==0)begin
                                    if(wave_upload&&wave_expected==8192&&!upload_error)begin
                                        wave_loaded<=1;wave_upload<=0;
                                    end else upload_error<=1;
                                end
                                8'h30:if({p0,p1,p2}==0)begin
                                    if(write_allowed&&wave_loaded)begin
                                        envelope_expected<=0;envelope_upload<=1;
                                        envelope_loaded<=0;upload_error<=0;mode<=0;mode_event<=1;
                                    end else upload_error<=1;
                                end
                                8'h32:if({p0,p1,p2}==0)begin
                                    if(envelope_upload&&envelope_expected==4096&&!upload_error)begin
                                        envelope_loaded<=1;envelope_upload<=0;
                                    end else upload_error<=1;
                                end
                                8'h23:if(p0<=1&&p1==0&&p2==0)begin
                                    if(!p0[0])begin mode<=0;mode_event<=1;end
                                    else if(wave_loaded&&envelope_loaded&&!upload_error)begin
                                        mode<=1;mode_event<=1;
                                    end else upload_error<=1;
                                end
                                8'h24:if(requested_step>=698&&requested_step<=111821)
                                    envelope_step<=requested_step;
                                default:begin end
                            endcase
                        end
                    end
                    AH:begin packet_address[15:8]<=byte_data;crc<=crc_byte(crc,byte_data);state<=AL;end
                    AL:begin packet_address[7:0]<=byte_data;crc<=crc_byte(crc,byte_data);data_index<=0;state<=DATA;end
                    DATA:begin
                        crc<=crc_byte(crc,byte_data);
                        if(!data_index[0])high_byte<=byte_data;
                        else words[data_index[5:1]]<={high_byte,byte_data};
                        if(data_index==31)state<=CRCH;else data_index<=data_index+1'b1;
                    end
                    CRCH:begin crc_high<=byte_data;state<=CRCL;end
                    CRCL:begin
                        if({crc_high,byte_data}==crc&&write_allowed&&!mode&&
                            !packet_address[3:0]&&
                            ((wave_packet&&wave_upload&&packet_address==wave_expected&&packet_address<=8176)
                            ||(!wave_packet&&envelope_upload&&packet_address==envelope_expected&&packet_address<=4080)))begin
                            write_index<=0;state<=WRITE;
                        end else begin upload_error<=1;state<=SOF;end
                    end
                    default:state<=SOF;
                endcase
            end
        end
    end
endmodule

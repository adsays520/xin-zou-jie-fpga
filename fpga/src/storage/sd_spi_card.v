// Read-only SDHC/SDXC SPI block transport. The caller sees a sector only
// after its CRC16 has been checked; timeouts also cover an absent card.
module sd_spi_card #(
    parameter integer CLOCK_HZ=50000000,
    parameter integer POWERUP_CLKS=CLOCK_HZ/10,
    parameter integer SLOW_HALF=64,FAST_HALF=4,
    parameter integer TOKEN_MAX_BYTES=8192
)(
    input wire clk,rst_n,read_start,input wire [31:0] read_lba,
    output reg initialized,output wire read_ready,
    output reg [7:0] error,data_byte,output reg data_valid,sector_done,
    output wire sd_clk,sd_mosi,input wire sd_miso,output reg sd_cs
);
    localparam POWER=0,CLOCK_START=1,CLOCK_WAIT=2,CMD_START=3,CMD_WAIT=4,
        R1_START=5,R1_WAIT=6,EXTRA_START=7,EXTRA_WAIT=8,DESELECT_START=9,
        DESELECT_WAIT=10,DISPATCH=11,IDLE=12,TOKEN_START=13,TOKEN_WAIT=14,
        DATA_START=15,DATA_WAIT=16,CRC_START=17,CRC_WAIT=18,FAILED=19;
    reg [4:0] state;
    reg fast,spi_start;
    reg [7:0] spi_tx;
    wire spi_busy,spi_done;wire [7:0] spi_rx;
    reg [31:0] power_count,watchdog;
    reg [47:0] command_shift;
    reg [5:0] command;
    reg [2:0] command_bytes,extra_remaining;
    reg [7:0] response;
    reg [4:0] response_polls;
    reg [3:0] clock_bytes;
    reg [12:0] init_attempts;
    reg [31:0] extra_value;
    reg [13:0] token_count;
    reg [8:0] data_index;
    reg [15:0] data_crc;
    reg [7:0] crc_high;
    reg crc_second;
    sd_spi_byte #(.SLOW_HALF(SLOW_HALF),.FAST_HALF(FAST_HALF)) u_byte(
        .clk(clk),.rst_n(rst_n),.slow(!fast),.start(spi_start),.tx_data(spi_tx),
        .miso(sd_miso),.sclk(sd_clk),.mosi(sd_mosi),.busy(spi_busy),.done(spi_done),.rx_data(spi_rx));
    assign read_ready=initialized&&state==IDLE;
    function [15:0] crc16;
        input [15:0] old;input [7:0] value;
        reg [15:0] c;integer b;
        begin c=old^{value,8'd0};for(b=0;b<8;b=b+1)c=c[15]?(c<<1)^16'h1021:(c<<1);crc16=c;end
    endfunction
    task send_command;
        input [5:0] code;input [31:0] argument;input [7:0] crc;input [2:0] extra;
        begin
            command<=code;command_shift<={2'b01,code,argument,crc};command_bytes<=6;
            extra_remaining<=extra;extra_value<=0;response_polls<=0;response<=8'hff;
            sd_cs<=0;state<=CMD_START;
        end
    endtask
    task fail;
        input [7:0] code;
        begin error<=code;initialized<=0;sd_cs<=1;state<=FAILED;end
    endtask
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin
            state<=POWER;fast<=0;spi_start<=0;spi_tx<=8'hff;sd_cs<=1;
            initialized<=0;error<=0;data_byte<=0;data_valid<=0;sector_done<=0;
            power_count<=0;watchdog<=0;command_shift<=0;command<=0;command_bytes<=0;
            extra_remaining<=0;response<=8'hff;response_polls<=0;clock_bytes<=0;
            init_attempts<=0;extra_value<=0;token_count<=0;data_index<=0;
            data_crc<=0;crc_high<=0;crc_second<=0;
        end else begin
            spi_start<=0;data_valid<=0;sector_done<=0;
            if(state==IDLE||state==FAILED)watchdog<=0;
            else if(watchdog<CLOCK_HZ*5)watchdog<=watchdog+1'b1;
            case(state)
                POWER:if(power_count==POWERUP_CLKS-1)begin clock_bytes<=0;state<=CLOCK_START;end
                      else power_count<=power_count+1'b1;
                CLOCK_START:if(!spi_busy)begin spi_tx<=8'hff;spi_start<=1;state<=CLOCK_WAIT;end
                CLOCK_WAIT:if(spi_done)begin
                    if(clock_bytes==9)send_command(0,0,8'h95,0);
                    else begin clock_bytes<=clock_bytes+1'b1;state<=CLOCK_START;end
                end
                CMD_START:if(!spi_busy)begin spi_tx<=command_shift[47:40];spi_start<=1;state<=CMD_WAIT;end
                CMD_WAIT:if(spi_done)begin
                    command_shift<=command_shift<<8;
                    if(command_bytes==1)state<=R1_START;
                    else begin command_bytes<=command_bytes-1'b1;state<=CMD_START;end
                end
                R1_START:if(!spi_busy)begin spi_tx<=8'hff;spi_start<=1;state<=R1_WAIT;end
                R1_WAIT:if(spi_done)begin
                    if(!spi_rx[7])begin
                        response<=spi_rx;
                        if(command==17)begin
                            if(spi_rx!=0)fail(7);
                            else begin token_count<=0;state<=TOKEN_START;end
                        end else if(extra_remaining!=0)state<=EXTRA_START;
                        else begin sd_cs<=1;state<=DESELECT_START;end
                    end else if(response_polls==15)fail(1);
                    else begin response_polls<=response_polls+1'b1;state<=R1_START;end
                end
                EXTRA_START:if(!spi_busy)begin spi_tx<=8'hff;spi_start<=1;state<=EXTRA_WAIT;end
                EXTRA_WAIT:if(spi_done)begin
                    extra_value<={extra_value[23:0],spi_rx};extra_remaining<=extra_remaining-1'b1;
                    if(extra_remaining==1)begin sd_cs<=1;state<=DESELECT_START;end
                    else state<=EXTRA_START;
                end
                DESELECT_START:if(!spi_busy)begin spi_tx<=8'hff;spi_start<=1;state<=DESELECT_WAIT;end
                DESELECT_WAIT:if(spi_done)state<=DISPATCH;
                DISPATCH:case(command)
                    0:if(response!=1)fail(2);else send_command(8,32'h000001aa,8'h87,4);
                    8:if(response!=1||extra_value[11:0]!=12'h1aa)fail(3);else send_command(55,0,8'h01,0);
                    55:if(response!=1&&response!=0)fail(4);else send_command(41,32'h40000000,8'h01,0);
                    41:if(response==0)send_command(58,0,8'h01,4);
                       else if(response!=1||init_attempts==8191)fail(5);
                       else begin init_attempts<=init_attempts+1'b1;send_command(55,0,8'h01,0);end
                    58:if(response!=0||extra_value[31:30]!=2'b11||!(|extra_value[23:15]))fail(6);
                       else begin fast<=1;initialized<=1;watchdog<=0;state<=IDLE;end
                    17:begin sector_done<=1;state<=IDLE;end
                    default:fail(10);
                endcase
                IDLE:if(read_start)begin watchdog<=0;send_command(17,read_lba,8'h01,0);end
                TOKEN_START:if(!spi_busy)begin spi_tx<=8'hff;spi_start<=1;state<=TOKEN_WAIT;end
                TOKEN_WAIT:if(spi_done)begin
                    if(spi_rx==8'hfe)begin data_index<=0;data_crc<=0;state<=DATA_START;end
                    else if(spi_rx!=8'hff||token_count==TOKEN_MAX_BYTES-1)fail(8);
                    else begin token_count<=token_count+1'b1;state<=TOKEN_START;end
                end
                DATA_START:if(!spi_busy)begin spi_tx<=8'hff;spi_start<=1;state<=DATA_WAIT;end
                DATA_WAIT:if(spi_done)begin
                    data_byte<=spi_rx;data_valid<=1;data_crc<=crc16(data_crc,spi_rx);
                    if(data_index==511)begin crc_second<=0;state<=CRC_START;end
                    else begin data_index<=data_index+1'b1;state<=DATA_START;end
                end
                CRC_START:if(!spi_busy)begin spi_tx<=8'hff;spi_start<=1;state<=CRC_WAIT;end
                CRC_WAIT:if(spi_done)begin
                    if(!crc_second)begin crc_high<=spi_rx;crc_second<=1;state<=CRC_START;end
                    else if({crc_high,spi_rx}!=data_crc)fail(9);
                    else begin sd_cs<=1;state<=DESELECT_START;end
                end
                default:begin end
            endcase
            if(state!=IDLE&&state!=FAILED&&watchdog==CLOCK_HZ*5)fail(11);
        end
    end
endmodule

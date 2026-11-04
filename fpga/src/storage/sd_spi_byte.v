// Mode-0 SPI, entirely clock-enabled in the 50 MHz domain. Fast mode is
// 6.25 MHz so the two-stage MISO synchronizer settles before each sample.
module sd_spi_byte #(
    parameter integer SLOW_HALF=64,FAST_HALF=4
)(
    input wire clk,rst_n,slow,start,input wire [7:0] tx_data,
    input wire miso,output reg sclk,mosi,busy,done,output reg [7:0] rx_data
);
    (* async_reg="true",syn_preserve=1 *) reg miso_meta,miso_sync;
    reg [7:0] tx_shift,rx_shift;
    reg [2:0] bit_number;
    reg [7:0] divider;
    wire [7:0] half_period=slow?SLOW_HALF:FAST_HALF;
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin miso_meta<=1; miso_sync<=1;end
        else begin miso_meta<=miso;miso_sync<=miso_meta;end
    end
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin
            sclk<=0;mosi<=1;busy<=0;done<=0;rx_data<=0;
            tx_shift<=0;rx_shift<=0;bit_number<=7;divider<=0;
        end else begin
            done<=0;
            if(!busy)begin
                sclk<=0;divider<=0;
                if(start)begin
                    busy<=1;tx_shift<=tx_data;mosi<=tx_data[7];
                    rx_shift<=0;bit_number<=7;
                end
            end else if(divider==half_period-1)begin
                divider<=0;
                if(!sclk)begin sclk<=1;rx_shift<={rx_shift[6:0],miso_sync};end
                else begin
                    sclk<=0;
                    if(bit_number==0)begin busy<=0;done<=1;rx_data<=rx_shift;mosi<=1;end
                    else begin bit_number<=bit_number-1'b1;tx_shift<=tx_shift<<1;mosi<=tx_shift[6];end
                end
            end else divider<=divider+1'b1;
        end
    end
endmodule

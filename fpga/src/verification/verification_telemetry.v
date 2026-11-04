// Request-driven 512 stereo samples at Fs/4, from the actual I2S word tap.
// Capture is frozen before transmission. UART backpressure never stalls audio.
module verification_telemetry #(
    parameter CLOCK_HZ=50000000,parameter BAUD=115200
)(
    input wire clk,rst_n,sample_tick,request,
    input wire [15:0] sample_l,sample_r,
    input wire [7:0] flags,input wire [2:0] active_count,
    input wire [31:0] latency_cycles,
    output wire uart_tx,output wire busy
);
    reg [31:0] memory[0:511];
    reg [2:0] state;
    reg [1:0] decim;
    reg [8:0] write_index;
    reg [11:0] byte_index;
    reg [15:0] packet_sequence,block_sequence,crc;
    reg [7:0] block_flags,block_count,tx_data;
    reg [31:0] block_latency,read_word;
    reg tx_start;
    wire tx_busy,tx_done;
    assign busy=state!=0;
    verification_uart_tx #(.CLOCK_HZ(CLOCK_HZ),.BAUD(BAUD)) u_tx(
        .clk(clk),.rst_n(rst_n),.start(tx_start),.data(tx_data),.tx(uart_tx),.busy(tx_busy),.done(tx_done));
    function [15:0] crc_byte;
        input [15:0] value;input [7:0] b;
        reg [15:0] c;integer k;
        begin c=value^{b,8'h00};for(k=0;k<8;k=k+1)c=c[15]?(c<<1)^16'h1021:(c<<1);crc_byte=c;end
    endfunction
    function [7:0] header;
        input [3:0] index;
        begin case(index)
            0:header=8'hD3;1:header=8'h91;2:header=1;3:header=block_flags;
            4:header=block_sequence[7:0];5:header=block_sequence[15:8];
            6:header=8'he0;7:header=8'h2e; // 12000 Hz
            8:header=0;9:header=2; // 512 samples
            10:header=block_latency[7:0];11:header=block_latency[15:8];
            12:header=block_latency[23:16];13:header=block_latency[31:24];
            14:header=block_count;default:header=0;
        endcase end
    endfunction
    reg [7:0] next_byte;
    always @*begin
        if(byte_index<16)next_byte=header(byte_index[3:0]);
        else if(byte_index<2064)case(byte_index[1:0])
            0:next_byte=read_word[7:0];1:next_byte=read_word[15:8];
            2:next_byte=read_word[23:16];default:next_byte=read_word[31:24];
        endcase
        else if(byte_index==2064)next_byte=crc[15:8];else next_byte=crc[7:0];
    end
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin
            state<=0;decim<=0;write_index<=0;byte_index<=0;packet_sequence<=0;block_sequence<=0;
            block_flags<=0;block_count<=0;block_latency<=0;read_word<=0;
            crc<=16'hffff;tx_start<=0;tx_data<=0;
        end else begin
            tx_start<=0;
            case(state)
                0:if(request)begin
                    state<=1;write_index<=0;decim<=0;packet_sequence<=packet_sequence+1'b1;block_sequence<=packet_sequence+1'b1;
                    block_flags<=flags;block_count<={5'd0,active_count};block_latency<=latency_cycles;
                end
                1:if(sample_tick)begin
                    decim<=decim+1'b1;
                    if(decim==3)begin
                        memory[write_index]<={sample_r,sample_l};
                        if(write_index==511)begin state<=2;byte_index<=0;crc<=16'hffff;end
                        else write_index<=write_index+1'b1;
                    end
                end
                2:begin
                    if(byte_index>=16 && byte_index<2064)read_word<=memory[(byte_index-16)>>2];
                    state<=3;
                end
                3:if(!tx_busy)begin
                    tx_data<=next_byte;tx_start<=1;state<=4;
                    if(byte_index>=2 && byte_index<2064)crc<=crc_byte(crc,next_byte);
                end
                4:if(tx_done)begin
                    if(byte_index==2065)state<=0;
                    else begin byte_index<=byte_index+1'b1;state<=2;end
                end
            endcase
        end
    end
endmodule

module verification_uart_tx #(parameter CLOCK_HZ=50000000,parameter BAUD=115200)(
    input wire clk,rst_n,start,input wire [7:0] data,
    output reg tx,busy,done
);
    localparam DIV=(CLOCK_HZ+BAUD/2)/BAUD;
    reg [$clog2(DIV)-1:0] count;
    reg [3:0] bit_index;
    reg [9:0] shift;
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin tx<=1;busy<=0;done<=0;count<=0;bit_index<=0;shift<=10'h3ff;end
        else begin
            done<=0;
            if(start&&!busy)begin
                shift<={1'b1,data,1'b0};tx<=0;busy<=1;count<=DIV-1;bit_index<=0;
            end else if(busy)begin
                if(count==0)begin
                    if(bit_index==9)begin tx<=1;busy<=0;done<=1;end
                    else begin shift<={1'b1,shift[9:1]};tx<=shift[1];bit_index<=bit_index+1'b1;count<=DIV-1;end
                end else count<=count-1'b1;
            end
        end
    end
endmodule

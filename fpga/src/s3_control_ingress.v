// Preserve PC UART as the original byte stream. A buffered SPI command is
// replayed atomically in 24 clk cycles only after UART has been quiet 1 ms.
// 24/50MHz < 1 UART bit (8.68us), so a new UART start cannot interleave bytes.
module s3_control_ingress #(
    parameter integer CLOCK_HZ=50000000,
    parameter integer BAUD=115200
)(
    input wire clk,input wire rst_n,input wire uart_rx_i,
    input wire [47:0] command_data,input wire command_valid,
    output wire command_ready,input wire commands_enabled,
    input wire bulk_request,bulk_busy,bulk_replaying,input wire [7:0] bulk_data,input wire bulk_valid,output wire bulk_grant, input wire bulk_allowed,
    output reg [7:0] byte_data,output reg byte_valid
);
    wire [7:0] uart_data;
    wire uart_valid;
    reg [1:0] uart_sync;
    localparam integer QUIET_CLKS=CLOCK_HZ/1000;
    reg [$clog2(QUIET_CLKS+1)-1:0] quiet_count;
    reg [47:0] replay;
    reg active;
    reg [2:0] index;
    reg [1:0] phase;
    reg [8:0] uart_remaining;
    reg uart_expect_command;
    localparam integer PACKET_TIMEOUT=CLOCK_HZ/20+1000;
    reg [$clog2(PACKET_TIMEOUT+1)-1:0] uart_packet_age;
    uart_rx_8n1 #(.CLOCK_HZ(CLOCK_HZ),.BAUD(BAUD)) u_rx(
        .clk(clk),.rst_n(rst_n),.rx_i(uart_rx_i),.data_o(uart_data),.data_valid_o(uart_valid));
    assign bulk_grant=bulk_request&&bulk_allowed&&!active&&quiet_count==QUIET_CLKS&&uart_sync[1]&&!uart_valid&&uart_remaining==0;
    assign command_ready=commands_enabled&&!bulk_busy&&!active&&quiet_count==QUIET_CLKS&&uart_sync[1]&&!uart_valid&&uart_remaining==0;
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin
            uart_sync<=2'b11;quiet_count<=0;replay<=0;active<=0;index<=0;phase<=0;
            byte_data<=0;byte_valid<=0;
            uart_remaining<=0;uart_expect_command<=0;uart_packet_age<=0;
        end else begin
            uart_sync<={uart_sync[0],uart_rx_i};
            if(!uart_sync[1]||uart_valid)quiet_count<=0;
            else if(quiet_count<QUIET_CLKS)quiet_count<=quiet_count+1'b1;
            byte_valid<=0;
            // UART may pause between USB packets. Do not inject into a
            // partial fixed (6-byte) or upload (38-byte) frame, even when the
            // line has been idle for >1ms. Timeout is longer than the parsers'.
            if(uart_valid)begin
                uart_packet_age<=0;
                if(uart_remaining==0)begin
                    if(uart_data==8'ha5)begin uart_remaining<=1;uart_expect_command<=1;end
                end else if(uart_expect_command)begin
                    uart_expect_command<=0;
                    uart_remaining<=uart_data==8'hb0 ? 9'd264:(uart_data==8'h11||uart_data==8'h21||uart_data==8'h31) ? 9'd36:9'd4;
                end else uart_remaining<=uart_remaining-1'b1;
            end else if(uart_remaining!=0)begin
                if(uart_packet_age==PACKET_TIMEOUT-1)begin uart_remaining<=0;uart_expect_command<=0;end
                else uart_packet_age<=uart_packet_age+1'b1;
            end
            if(command_valid&&command_ready)begin
                replay<=command_data;active<=1;index<=0;phase<=0;
            end
            if(bulk_replaying||bulk_valid)begin
                byte_data<=bulk_data;byte_valid<=bulk_valid;
            end else if(active)begin
                phase<=phase+1'b1;
                if(phase==0)begin
                    byte_data<=replay[47:40];byte_valid<=1;replay<={replay[39:0],8'd0};
                    if(index==5)active<=0;
                    else index<=index+1'b1;
                end
            end else if(uart_valid)begin
                byte_data<=uart_data;byte_valid<=1;
            end
        end
    end
endmodule

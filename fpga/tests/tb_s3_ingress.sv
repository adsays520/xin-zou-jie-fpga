`timescale 1ns/1ps
module tb_s3_ingress;
    reg clk=0;always #10 clk=~clk;
    reg rst_n=0,uart=1,cmd_valid=0;
    reg[47:0]cmd=48'ha502060864cd;
    wire cmd_ready;wire[7:0]data;wire valid;
    integer bytes=0,triggers=0;
    reg[7:0]seen[0:31];
    wire trigger;
    s3_control_ingress dut(.clk(clk),.rst_n(rst_n),.uart_rx_i(uart),
        .command_data(cmd),.command_valid(cmd_valid),.command_ready(cmd_ready),.commands_enabled(1'b1),.byte_data(data),.byte_valid(valid));
    guitar_uart_trigger #(.EXTERNAL_BYTES(1)) parser(
        .clk(clk),.rst_n(rst_n),.uart_rx_i(1'b1),.external_byte_data(data),.external_byte_valid(valid),
        .local_level_step(1'b0),.local_level_bus(2'd0),.envelope_write_allowed(1'b1),.trigger(trigger));
    always @(posedge clk)begin
        if(valid)begin seen[bytes]<=data;bytes<=bytes+1;end
        if(trigger)triggers<=triggers+1;
    end
    task send_byte(input [7:0]b);
        begin uart=0;#8680;for(integer j=0;j<8;j=j+1)begin uart=b[j];#8680;end uart=1;#8680;end
    endtask
    initial begin
        #100;rst_n=1;#10000;
        fork
            begin
                send_byte(8'ha5);send_byte(8'h02);send_byte(8'h02);
                // More than the line-idle guard, less than parser timeout.
                #1500000;
                send_byte(8'h03);send_byte(8'h5a);send_byte(8'hfc);
            end
            begin
                #150000;cmd_valid=1;
                wait(cmd_ready);@(posedge clk);#1;cmd_valid=0;
            end
        join
        #1200000;
        if(bytes!=12||triggers!=2)$fatal(1,"UART/SPI merge failed bytes=%d triggers=%d",bytes,triggers);
        if({seen[0],seen[1],seen[2],seen[3],seen[4],seen[5]}!==48'ha50202035afc)$fatal(1,"UART frame corrupted");
        if({seen[6],seen[7],seen[8],seen[9],seen[10],seen[11]}!==48'ha502060864cd)$fatal(1,"SPI frame interleaved");
        $display("PASS ingress: concurrent pending SPI waits for UART packet, atomic replay, real parser triggers");$finish;
    end
    initial begin #10000000;$fatal(1,"Ingress timeout");end
endmodule

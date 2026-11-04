`timescale 1ns/1ps
module tb_s3_link;
    reg clk=0; always #10 clk=~clk;
    reg rst_n=0,sclk=0,cs=1,mosi=0;
    wire miso,irq,ready,touch_enabled,command_valid;
    wire [127:0] keys;wire [7:0] online;wire [47:0] command_data;
    reg command_ready=0;
    wire [5:0] hall_mask;wire [47:0]hall_velocity;wire hall_valid;
    reg [7:0] tx[0:64],rx[0:64];
    integer i,b,accepted=0,hall_accepted=0;
    s3_spi_link #(.TOUCH_TIMEOUT_CLKS(1000000)) dut(
        .clk(clk),.rst_n(rst_n),.spi_sclk(sclk),.spi_cs_n(cs),.spi_mosi(mosi),
        .spi_miso(miso),.fpga_irq(irq),.fpga_ready(ready),
        .touch_keys(keys),.touch_online(online),.touch_enabled(touch_enabled),
        .hall_mask(hall_mask),.hall_velocity(hall_velocity),.hall_valid(hall_valid),.hall_ready(1'b1),
        .command_data(command_data),.command_valid(command_valid),.command_ready(command_ready),
        .rgb24(24'h123456),.pixel_x(8'd12),.pixel_y(8'd34),.display_page(2'd2),.instrument(2'd1),
        .hall_mode(1'b1),.selected_frets(30'd8),.trigger_mode(2'd2));
    always @(posedge clk)if(command_valid&&command_ready)accepted<=accepted+1;
    always @(posedge clk)if(hall_valid)hall_accepted<=hall_accepted+1;
    function [15:0] crc_byte(input [15:0] c,input [7:0] d);
        reg [15:0] x;integer k;
        begin x=c^{d,8'h00};for(k=0;k<8;k=k+1)x=x[15]?(x<<1)^16'h1021:x<<1;crc_byte=x;end
    endfunction
    task crc;
        reg [15:0] c;
        begin c=16'hffff;for(integer k=0;k<62;k=k+1)c=crc_byte(c,tx[k]);tx[62]=c[15:8];tx[63]=c[7:0];end
    endtask
    task packet(input integer seq,input integer kind);
        begin
            for(integer k=0;k<65;k=k+1)tx[k]=0;
            tx[0]=8'ha5;tx[1]=8'h53;tx[2]=1;tx[3]=kind;tx[4]=seq;tx[5]=seq>>8;
            tx[6]=8'hff;tx[7]=kind==0?16:6;tx[8]=1;tx[23]=8'h20;tx[30]=1;
            tx[56]=8'h78;tx[57]=8'h56;tx[58]=8'h34;tx[59]=8'h12;
            tx[24]=8'ha5;tx[25]=2;tx[26]=6;tx[27]=8;tx[28]=100;
            tx[29]=tx[24]^tx[25]^tx[26]^tx[27]^tx[28];crc;
        end
    endtask
    task exchange(input integer length);
        begin
            cs=0;#2000;
            for(integer k=0;k<length;k=k+1)begin
                rx[k]=0;
                for(integer q=7;q>=0;q=q-1)begin
                    mosi=tx[k][q];#500;sclk=1;rx[k][q]=miso;#500;sclk=0;
                end
            end
            #2000;cs=1;#4000;
        end
    endtask
    task response;
        reg [15:0] c;
        begin
            if(rx[0]!==8'h5a||rx[1]!==8'h53||rx[2]!==1)$fatal(1,"Bad reply header");
            c=16'hffff;for(integer k=0;k<62;k=k+1)c=crc_byte(c,rx[k]);
            if({rx[62],rx[63]}!==c)$fatal(1,"Bad reply CRC");
        end
    endtask
    initial begin
        #200;rst_n=1;#5000;
        if(!ready||miso!==1'bz)$fatal(1,"Idle/READY failure");
        packet(1,0);exchange(64);response;
        if(rx[4]!==0)$fatal(1,"ACK must be delayed, not same-frame");
        if(keys!==128'h20000000000000000000000000000001||online!==8'hff||!touch_enabled)$fatal(1,"Snapshot mismatch");
        exchange(64);response;
        if(rx[4]!==1||{rx[59],rx[58],rx[57],rx[56]}!==32'h12345678)$fatal(1,"Session/ACK mismatch");
        if({rx[32],rx[33],rx[34]}!==24'h123456||rx[35]!==12||rx[36]!==34||rx[37]!==2||rx[7]!==1)$fatal(1,"RGB/status mismatch");
        if(rx[39]!==8'ha2)$fatal(1,"Trigger capability/override mismatch");
        packet(2,1);exchange(64);
        if(!command_valid||command_data!==48'ha502060864cd)$fatal(1,"Fixed command mismatch %h",command_data);
        command_ready=1;#100;command_ready=0;#100;
        exchange(64);if(accepted!==1||command_valid)$fatal(1,"Duplicate command retriggered");
        packet(3,0);tx[62]=tx[62]^1;exchange(64);
        if(dut.last_sequence!==2)$fatal(1,"Bad CRC accepted");
        packet(3,0);exchange(63);if(dut.last_sequence!==2)$fatal(1,"Short frame accepted");
        packet(3,0);exchange(65);if(dut.last_sequence!==2)$fatal(1,"Long frame accepted");
        packet(3,0);tx[2]=2;crc;exchange(64);if(dut.last_sequence!==2)$fatal(1,"Wrong version accepted");
        packet(3,0);exchange(64);if(dut.last_sequence!==3)$fatal(1,"Recovery failed");
        packet(4,1);exchange(64);if(!command_valid)$fatal(1,"Command not queued");
        packet(5,1);exchange(64);if(dut.last_sequence!==4)$fatal(1,"Busy command falsely ACKed");
        command_ready=1;#100;command_ready=0;#100;
        exchange(64);if(dut.last_sequence!==5)$fatal(1,"Busy retry not accepted");
        command_ready=1;#100;command_ready=0;#100;
        packet(5,1);tx[56]=8'h79;crc;exchange(64);
        if(!command_valid||dut.last_session!==32'h12345679)$fatal(1,"New session suppressed as duplicate");
        command_ready=1;#100;command_ready=0;#100;
        packet(6,2);tx[7]=7;tx[31]=1;tx[32]=126;crc;exchange(64);exchange(64);
        if(hall_accepted!=1||hall_mask!==1||hall_velocity[7:0]!==126)$fatal(1,"Hall event lost/duplicated");
        packet(7,2);tx[7]=7;tx[31]=1;tx[32]=255;crc;exchange(64);
        if(dut.last_sequence!==6||hall_accepted!=1)$fatal(1,"Invalid Hall velocity accepted");
        packet(7,1);tx[25]=9;tx[26]=2;tx[27]=0;tx[28]=0;tx[29]=8'ha5^9^2;crc;exchange(64);
        if(!command_valid||command_data!=={8'ha5,8'h09,8'h02,8'h00,8'h00,8'hae})$fatal(1,"Trigger mode not forwarded");
        command_ready=1;#100;command_ready=0;#100;
        #20001000;
        if(keys!==0||online!==0||touch_enabled)$fatal(1,"Link watchdog did not clear stale touch");
        $display("PASS S3 SPI: full duplex CRC, delayed ACK, duplicate/session, malformed/busy recovery, RGB, watchdog");
        $finish;
    end
    initial begin #100000000;$fatal(1,"Timeout");end
endmodule

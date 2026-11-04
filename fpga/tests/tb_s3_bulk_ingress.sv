`timescale 1ns/1ps
module tb_s3_bulk_ingress;
 reg clk=0,rst_n=0,rx=1,cmd_valid=0;always #10 clk=~clk;
 wire ready,valid,session,trigger;wire [7:0] data;integer triggers=0,replayed=0;
 s3_control_ingress ingress(.clk(clk),.rst_n(rst_n),.uart_rx_i(rx),.command_data(48'ha502060864cd),
 .command_valid(cmd_valid),.command_ready(ready),.commands_enabled(!session),.byte_data(data),.byte_valid(valid));
 guitar_uart_trigger #(.EXTERNAL_BYTES(1)) parser(.clk(clk),.rst_n(rst_n),.uart_rx_i(1'b1),
 .external_byte_data(data),.external_byte_valid(valid),.local_level_step(1'b0),.local_level_bus(2'd0),
 .envelope_write_allowed(1'b1),.bank_upload_ready(1'b1),.upload_session(session),.trigger(trigger));
 always @(posedge clk)if(trigger)triggers++;
 task byte_tx(input [7:0] b);
 integer n;begin @(negedge clk);rx=0;repeat(434)@(negedge clk);
 for(n=0;n<8;n++)begin rx=b[n];repeat(434)@(negedge clk);end rx=1;repeat(450)@(negedge clk);end endtask
 task control(input [7:0] op);begin byte_tx(8'ha5);byte_tx(op);byte_tx(0);byte_tx(0);byte_tx(0);byte_tx(8'ha5^op);end endtask
 integer i;
 initial begin
 repeat(8)@(negedge clk);rst_n=1;control(8'hb1);
 if(!session)$fatal(1,"PC upload session missing");
 cmd_valid=1;byte_tx(8'ha5);byte_tx(8'hb0);
 for(i=0;i<264;i++)begin
   byte_tx(i%6==0?8'ha5:i%6==1?8'h02:i%6==2?8'h06:i%6==3?8'h08:i%6==4?8'h64:8'hcd);
   if(i==129)repeat(100000)@(negedge clk); // 2 ms USB pause in bulk payload
   if(ready||triggers)$fatal(1,"SPI injected into bulk upload or payload spoofed a pluck");
 end
 repeat(100000)@(negedge clk);if(ready||triggers)$fatal(1,"failed bulk session accepted normal command");
 control(8'hb4);wait(ready);@(posedge clk);#1;cmd_valid=0;
 repeat(1000)@(negedge clk);
 if(triggers!=1||session)$fatal(1,"cancel did not restore one atomic replay %0d",triggers);
 $display("PASS S3 BULK INGRESS: actual 115200 UART, 266-byte frame, embedded valid commands, 2ms pause, queued SPI isolated until explicit cancel");$finish;
 end
 initial begin #100000000;$fatal(1,"bulk ingress timeout");end
endmodule

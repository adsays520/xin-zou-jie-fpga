`timescale 1ns/1ps
module tb_sd_card;
 reg clk=0,rst_n=0,start=0,miso=1;reg [31:0] lba=32'h12345678;
 wire ready,initialized,cs,sck,mosi,dv,done;wire [7:0] error,data;
 always #10 clk=~clk;
 sd_spi_card #(.CLOCK_HZ(1000000),.POWERUP_CLKS(10),.SLOW_HALF(8),.FAST_HALF(4),.TOKEN_MAX_BYTES(8)) dut
 (clk,rst_n,start,lba,initialized,ready,error,data,dv,done,sck,mosi,miso,cs);
 integer scenario,bitnum=0,cmdn=0,head=0,tail=0,attempts=0,received=0,commands=0;
 reg [7:0] rx=0,tx=8'hff,cmd[0:5],q[0:599];reg [15:0] crc;integer k;
 function [15:0] crc16(input [15:0] old,input [7:0] value);
 reg [15:0] c;integer b;begin c=old^{value,8'd0};for(b=0;b<8;b++)c=c[15]?(c<<1)^16'h1021:c<<1;crc16=c;end endfunction
 function [7:0] payload(input integer index);payload=(index*37+(index>>3))&255;endfunction
 task put(input [7:0] b);begin q[tail]=b;tail=tail+1;end endtask
 always @(negedge cs)begin bitnum=0;cmdn=0;head=0;tail=0;tx=8'hff;miso=1;end
 always @(posedge cs)begin miso=1;end
 always @(posedge sck)if(!cs&&scenario!=1)begin
   rx={rx[6:0],mosi};bitnum=(bitnum+1)%8;
   if(bitnum==0)begin
     if(cmdn!=0||rx[7:6]==2'b01)begin
       cmd[cmdn]=rx;cmdn=cmdn+1;
       if(cmdn==6)begin
         commands=commands+1;cmdn=0;put(8'hff);
         case(cmd[0][5:0])
         0:begin if(cmd[5]!=8'h95)$fatal(1,"CMD0 CRC");put(1);end
         8:begin if(cmd[5]!=8'h87||{cmd[1],cmd[2],cmd[3],cmd[4]}!=32'h1aa)$fatal(1,"CMD8");put(1);put(0);put(0);put(1);put(8'haa);end
         55:put(1);
         41:begin if(!cmd[1][6])$fatal(1,"ACMD41 HCS missing");attempts=attempts+1;put(attempts<3?1:0);end
         58:begin put(0);put(scenario==4?8'h80:8'hc0);put(8'hff);put(8'h80);put(0);end
         17:begin
           if({cmd[1],cmd[2],cmd[3],cmd[4]}!==lba)$fatal(1,"SDHC addressing shifted");
           put(0);put(8'hff);
           if(scenario==3)for(k=0;k<12;k++)put(8'hff);
           else begin put(8'hfe);crc=0;for(k=0;k<512;k++)begin put(payload(k));crc=crc16(crc,payload(k));end put(crc[15:8]);put(crc[7:0]^(scenario==2));end
         end
         default:$fatal(1,"Unexpected command %d",cmd[0]);
         endcase
       end
     end
   end
 end
 always @(negedge sck)if(!cs&&scenario!=1)begin
   if(bitnum==0)begin if(head<tail)begin tx=q[head];head=head+1;end else tx=8'hff;end
   miso=tx[7-bitnum];
 end
 always @(posedge clk)if(rst_n&&dv)begin
   if(data!==payload(received))$fatal(1,"SPI payload bit/byte mismatch index=%0d actual=%h",received,data);
   received=received+1;
 end
 initial begin
   if(!$value$plusargs("CASE=%d",scenario))scenario=0;
   repeat(6)@(negedge clk);rst_n=1;
   if(scenario!=1&&scenario!=4)begin wait(ready);@(negedge clk);start=1;@(negedge clk);start=0;end
   wait(done||error!=0);repeat(4)@(negedge clk);
   case(scenario)
     0:if(error||!done&&received!=512||received!=512||attempts!=3||!initialized)$fatal(1,"good card failed %h",error);
     1:if(error!=1||received||initialized)$fatal(1,"no card");
     2:if(error!=9||received!=512||initialized)$fatal(1,"CRC16 corruption not rejected");
     3:if(error!=8||received||initialized)$fatal(1,"missing data token unbounded");
     4:if(error!=6||received||initialized)$fatal(1,"SDSC falsely accepted");
   endcase
   $display("PASS SD SPI case=%0d commands=%0d init retries=%0d bytes=%0d error=%h",scenario,commands,attempts,received,error);$finish;
 end
 initial begin #100000000;$fatal(1,"SD SPI timeout state=%0d cmd=%0d",dut.state,dut.command);end
endmodule

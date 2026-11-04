// Behavioral card on the physical mode-0 SPI pads, using fragmented FAT32 media.
module sd_media_model(input wire sck,cs,mosi,output reg miso=1);
 reg [31:0] addresses[0:799];reg [7:0] bytes[0:409599];
 reg [7:0] rx=0,tx=8'hff,cmd[0:5],q[0:599];
 integer bitnum=0,cmdn=0,head=0,tail=0,attempts=0,reads=0,k,slot;
 reg [15:0] crc;reg [31:0] address;
 initial begin
   $readmemh("tests/runtime_temp/sd0_lba.hex",addresses);
   $readmemh("tests/runtime_temp/sd0_data.hex",bytes);
 end
 function [15:0] crc16(input [15:0] old,input [7:0] value);
 reg [15:0] c;integer b;begin c=old^{value,8'd0};for(b=0;b<8;b++)c=c[15]?(c<<1)^16'h1021:c<<1;crc16=c;end endfunction
 task put(input [7:0] b);begin q[tail]=b;tail=tail+1;end endtask
 always @(negedge cs)begin bitnum=0;cmdn=0;head=0;tail=0;tx=8'hff;miso=1;end
 always @(posedge cs)miso=1;
 always @(posedge sck)if(!cs)begin
   rx={rx[6:0],mosi};bitnum=(bitnum+1)%8;
   if(bitnum==0&&(cmdn!=0||rx[7:6]==2'b01))begin
     cmd[cmdn]=rx;cmdn=cmdn+1;
     if(cmdn==6)begin
       cmdn=0;put(8'hff);
       case(cmd[0][5:0])
       0:put(1);
       8:begin put(1);put(0);put(0);put(1);put(8'haa);end
       55:put(1);
       41:begin attempts=attempts+1;put(attempts<2?1:0);end
       58:begin put(0);put(8'hc0);put(8'hff);put(8'h80);put(0);end
       17:begin
         address={cmd[1],cmd[2],cmd[3],cmd[4]};slot=-1;
         for(k=0;k<800;k++)if(addresses[k]==address)slot=k;
         if(slot<0)$fatal(1,"SD physical out-of-image read %0d",address);
         reads=reads+1;if(reads%220==0)$display("BOARD SD sectors=%0d",reads);
         put(0);put(8'hff);put(8'hfe);crc=0;
         for(k=0;k<512;k++)begin put(bytes[slot*512+k]);crc=crc16(crc,bytes[slot*512+k]);end
         put(crc[15:8]);put(crc[7:0]);
       end
       default:$fatal(1,"SD unexpected command %0d",cmd[0]);
       endcase
     end
   end
 end
 always @(negedge sck)if(!cs)begin
   if(bitnum==0)begin if(head<tail)begin tx=q[head];head=head+1;end else tx=8'hff;end
   miso=tx[7-bitnum];
 end
endmodule

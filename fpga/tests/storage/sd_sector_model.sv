// Test-only sector provider. Physical SPI/CRC/init is verified separately in tb_sd_card.
module sd_sector_model(input wire clk,rst_n,start,input wire [31:0] lba,
 output reg ready=1,output reg [7:0] data=0,output reg valid=0,done=0);
 reg [31:0] addresses[0:799];reg [7:0] bytes[0:409599];
 integer reads=0,index=0,slot,j;reg sending=0;
 initial begin
  $readmemh("tests/runtime_temp/sd0_lba.hex",addresses);
  $readmemh("tests/runtime_temp/sd0_data.hex",bytes);
 end
 always @(negedge clk)begin
  valid=0;done=0;
  if(!rst_n)begin ready=1;sending=0;index=0;end
  else if(start)begin
   if(sending)$fatal(1,"SD sector overlap");
   slot=-1;for(j=0;j<800;j++)if(addresses[j]==lba)slot=j;
   if(slot<0)$fatal(1,"SD sector out of image %0d",lba);
   sending=1;index=0;ready=0;reads++;
   if(reads%220==0)begin $display("BOARD FAT sectors=%0d",reads);$fflush();end
  end else if(sending)begin
   if(index<512)begin data=bytes[slot*512+index];valid=1;index++;end
   else begin done=1;ready=1;sending=0;end
  end
 end
endmodule

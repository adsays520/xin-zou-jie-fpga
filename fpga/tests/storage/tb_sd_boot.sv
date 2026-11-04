`timescale 1ns/1ps
module tb_sd_boot;
 reg clk=0,rst_n=0,cancel=0,card_ready=1,cv=0,done=0;
 reg [7:0] cb=0;wire read_start;wire [31:0] lba;
 wire ub,uv,uc,ue,ur,initialized,fault,active,finished,loading;
 wire [7:0] error,bank_error;wire [2:0] bank_status;
 wire [10:0] ui,count;wire [2047:0] ud;
 always #10 clk=~clk;
 wire stage_valid;wire [7:0] stage_index,stage_data;wire [2047:0] unused_data;
 piano_sd_boot #(.CLOCK_HZ(1000000),.KEEP_STAGE(0)) dut(.clk(clk),.rst_n(rst_n),.cancel(cancel),.memory_ready(1'b1),
 .card_ready(card_ready),.card_error(8'd0),.card_byte(cb),.card_byte_valid(cv),.card_sector_done(done),.card_read_start(read_start),.card_read_lba(lba),
 .upload_begin(ub),.upload_valid(uv),.upload_commit(uc),.upload_error(ue),.upload_index(ui),.upload_data(unused_data),
 .upload_ready(ur),.upload_count(count),.bank_initialized(initialized),.bank_fault(fault),.active(active),.finished(finished),.error(error),.loading(loading),
 .stage_valid(stage_valid),.stage_index(stage_index),.stage_data(stage_data));
 guitar_uart_trigger #(.EXTERNAL_BYTES(1),.EXTERNAL_STAGE(1)) staging(.clk(clk),.rst_n(rst_n),.uart_rx_i(1'b1),
 .external_byte_data(8'd0),.external_byte_valid(1'b0),.stage_active(active),.stage_valid(stage_valid),.stage_index(stage_index),.stage_data(stage_data),
 .local_level_step(1'b0),.local_level_bus(2'd0),.envelope_write_allowed(1'b1),.bank_upload_ready(ur),.bank_upload_data(ud));
 wire req_valid,req_ready,rsp_valid,rsp_ready;wire [63:0] req_data,rsp_data;
 piano_ddr_bank bank(.clk(clk),.rst_n(rst_n),.flush(1'b0),.memory_ready(1'b1),.transport_fault(1'b0),
 .initialized(initialized),.fault(fault),.upload_begin(ub),.upload_valid(uv),.upload_commit(uc),.upload_error(ue),
 .upload_index(ui),.upload_data(ud),.upload_ready(ur),.upload_count(count),.bank_status(bank_status),.status_error(bank_error),
 .load_valid(1'b0),.load_voice(4'd0),.load_bank(9'd0),.load_epoch(8'd0),.tonal_enable(1'b0),.tonal_address(8'd0),
 .transient_enable(1'b0),.transient_address(7'd0),.noise_voice(4'd0),
 .req_valid(req_valid),.req_ready(req_ready),.req_data(req_data),.rsp_valid(rsp_valid),.rsp_ready(rsp_ready),.rsp_data(rsp_data));
 piano_packet_memory memory(clk,rst_n,req_valid,req_ready,req_data,rsp_valid,rsp_ready,rsp_data);
 reg [31:0] addresses[0:799];reg [7:0] bytes[0:409599];reg [7:0] expected[0:281599];
 integer scenario,i,j,slot,n=0,sectors=0,chunks=0;reg [31:0] saved_lba;reg sending=0;reg [9:0] index=0;
 always @(negedge clk)if(rst_n)begin
   cv=0;done=0;
   if(read_start)begin
     if(sending)$fatal(1,"overlapping card request");
     slot=-1;for(j=0;j<800;j=j+1)if(addresses[j]==lba)slot=j;
     if(slot<0)$fatal(1,"out-of-image read %0d",lba);
     sending=1;index=0;card_ready=0;sectors=sectors+1;
   end else if(sending)begin
     if(index<512)begin cb=bytes[slot*512+index];cv=1;index=index+1;end
     else begin done=1;card_ready=1;sending=0;end
   end
 end
 always @(posedge clk)if(rst_n)begin
   if(uv)begin
     if(!ur||ui!=chunks)$fatal(1,"upload handshake/order");
     for(n=0;n<256;n=n+1)if(ud[n*8+:8]!==expected[ui*256+n]&&scenario!=5)$fatal(1,"payload byte %0d",ui*256+n);
     chunks=chunks+1;
   end
   if(ue&&(memory.state==1||memory.state==2||memory.state==3||memory.state==4))$fatal(1,"cancel stranded DDR packet");
   if(finished&&error==0&&!initialized)$fatal(1,"published ready before full DDR readback");
 end
 initial begin
   if(!$value$plusargs("CASE=%d",scenario))scenario=0;
   $readmemh($sformatf("tests/runtime_temp/sd%0d_lba.hex",scenario),addresses);
   $readmemh($sformatf("tests/runtime_temp/sd%0d_data.hex",scenario),bytes);
   $readmemh("tests/runtime_temp/sd_expected.hex",expected);
   repeat(8)@(negedge clk);rst_n=1;
   if(scenario==6)begin
     wait(memory.state==1);@(negedge clk);cancel=1;@(negedge clk);cancel=0;
   end
   wait(finished);repeat(6)@(negedge clk);
   case(scenario)
   0,1:begin
     if(error||fault||!initialized||count!=1100||memory.writes!=8800||memory.reads!=8800)$fatal(1,"boot/readback state err=%h count=%0d writes=%0d reads=%0d",error,count,memory.writes,memory.reads);
   end
   2:if(error!=8'h33||initialized||chunks)$fatal(1,"wrong length accepted");
   3:if(error!=8'h36||initialized||chunks!=2)$fatal(1,"early EOC accepted");
   4:if(error!=8'h32||initialized||chunks)$fatal(1,"missing file accepted");
   5:if(error!=8'h40||initialized||bank_error!=4||memory.reads!=8800)$fatal(1,"full DDR CRC did not reject corruption %h/%h",error,bank_error);
   6:if(error!=8'h7f||initialized||memory.writes!=8||count!=1)$fatal(1,"mid-packet cancel unsafe %h writes=%0d",error,memory.writes);
   7:if(error!=8'h30||initialized||chunks)$fatal(1,"undersized FAT accepted");
   endcase
   $display("PASS SD BOOT case=%0d sectors=%0d chunks=%0d DDR writes/reads=%0d/%0d error=%h",scenario,sectors,chunks,memory.writes,memory.reads,error);$finish;
 end
 initial begin #250000000;$fatal(1,"SD boot timeout state=%0d err=%h count=%0d",dut.state,error,count);end
endmodule

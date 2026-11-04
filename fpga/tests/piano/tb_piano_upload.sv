`timescale 1ns/1ps
module tb_piano_upload;
 reg clk=0,rst_n=0,stim_valid=0;
 reg [7:0] stim_data=0;reg shared_owner=0,shared_valid=0;reg [7:0] shared_index=0,shared_byte=0;
 always #10 clk=~clk;
 wire upload_begin,upload_valid,upload_commit,upload_error,upload_ready,query;
 wire [10:0] upload_index,upload_count;wire [2047:0] upload_data;wire [7:0] query_id;
 wire trigger,raw_valid;wire [7:0] raw_data;
 guitar_uart_trigger #(.EXTERNAL_STAGE(1)) uart(.stage_active(shared_owner),.stage_valid(shared_valid),.stage_index(shared_index),.stage_data(shared_byte),.clk(clk),.rst_n(rst_n),.uart_rx_i(1'b1),.local_level_step(1'b0),.local_level_bus(2'd0),
  .envelope_write_allowed(1'b1),.trigger(trigger),.uart_byte_data(raw_data),.uart_byte_valid(raw_valid),
  .bank_upload_ready(upload_ready),.bank_upload_begin(upload_begin),.bank_upload_valid(upload_valid),
  .bank_upload_commit(upload_commit),.bank_upload_error(upload_error),.bank_query(query),.bank_query_sequence(query_id),
  .bank_upload_index(upload_index),.bank_upload_data(upload_data));
 wire initialized,fault,req_valid,req_ready,rsp_valid,rsp_ready;
 wire [63:0] req_data,rsp_data;
 wire [2:0] status;wire [7:0] error;
 reg flush=0,load_valid=0;reg [3:0] load_voice=0;reg [8:0] load_bank=0;reg [7:0] load_epoch=0;
 wire loaded;wire [3:0] loaded_voice;wire [7:0] loaded_epoch;
 reg tonal_enable=0;reg [7:0] tonal_address=0;wire [191:0] weights;wire [31:0] frequency;
 piano_ddr_bank bank(.clk(clk),.rst_n(rst_n),.flush(flush),.memory_ready(1'b1),.transport_fault(1'b0),
  .initialized(initialized),.fault(fault),.upload_begin(upload_begin),.upload_valid(upload_valid),
  .upload_commit(upload_commit),.upload_error(upload_error),.upload_index(upload_index),.upload_data(upload_data),
  .upload_ready(upload_ready),.upload_count(upload_count),.bank_status(status),.status_error(error),
  .load_valid(load_valid),.load_voice(load_voice),.load_bank(load_bank),.load_epoch(load_epoch),
  .loaded(loaded),.loaded_voice(loaded_voice),.loaded_epoch(loaded_epoch),
  .tonal_enable(tonal_enable),.tonal_address(tonal_address),.tonal_weights(weights),.tonal_frequency(frequency),
  .transient_enable(1'b0),.transient_address(7'd0),.transient_parameters(),.noise_voice(4'd0),.noise_parameters(),
  .req_valid(req_valid),.req_ready(req_ready),.req_data(req_data),.rsp_valid(rsp_valid),.rsp_ready(rsp_ready),.rsp_data(rsp_data));
 piano_packet_memory memory(clk,rst_n,req_valid,req_ready,req_data,rsp_valid,rsp_ready,rsp_data);
 integer triggers=0,accepted=0;
 reg [7:0] last_epoch[0:15];
 always @(posedge clk)if(rst_n)begin
  if(trigger)triggers=triggers+1;
  if(upload_valid)accepted=accepted+1;
  if((uart.bank_upload_active||uart.parser_state==uart.PARSE_BANK_SKIP||uart.parser_state==uart.PARSE_BANK_DATA||uart.parser_state==uart.PARSE_BANK_CRC)&&raw_valid)$fatal(1,"parameter bytes leaked to instrument parsers");
  if(loaded)last_epoch[loaded_voice]=loaded_epoch;
 end
 task byte_in(input [7:0] b);
  begin stim_data=b;stim_valid=1;@(negedge clk);stim_valid=0;repeat(2)@(negedge clk);end
 endtask
 task control(input [7:0] op,a,b,c);
  begin byte_in(8'ha5);byte_in(op);byte_in(a);byte_in(b);byte_in(c);byte_in(8'ha5^op^a^b^c);end
 endtask
 reg [7:0] packets[0:292599],evil[0:531];
 reg [255:0] image[0:8799];
 integer i,v,m,k;
 task begin_session;
  begin control(8'hb1,0,0,0);repeat(8)@(negedge clk);while(!upload_ready)@(negedge clk);end
 endtask
 task upload_all;
  begin
   for(i=0;i<292600;i=i+1)byte_in(packets[i]);
   while(upload_count!=1100)begin @(negedge clk);if(fault)$fatal(1,"valid upload failed");end
  end
 endtask
 initial begin
  force uart.rx_data=stim_data;force uart.rx_valid=stim_valid;
  $readmemh("tests/runtime_temp/piano_upload_packets.hex",packets);
  $readmemh("tests/runtime_temp/piano_upload_evil.hex",evil);
  $readmemh("src/piano/sms_ddr/bank_image.hex",image);
  for(v=0;v<16;v=v+1)last_epoch[v]=0;
  repeat(5)@(negedge clk);rst_n=1;
  shared_owner=1;
  for(k=0;k<256;k++)begin shared_index=k;shared_byte=k^8'ha5;shared_valid=1;@(negedge clk);end
  shared_valid=0;control(8'hb1,0,0,0);
  if(uart.upload_session)$fatal(1,"PC begin stole active SD staging owner");
  for(i=0;i<266;i++)byte_in(evil[i]);
  for(k=0;k<256;k++)if(upload_data[k*8+:8]!==((k^8'ha5)&255))$fatal(1,"PC payload overwrote SD shared staging");
  shared_owner=0;begin_session;
  for(i=0;i<266;i=i+1)byte_in(evil[i]);
  while(upload_count!=1)@(negedge clk);
  if(triggers!=0||accepted!=1)$fatal(1,"embedded valid A5 commands escaped bulk parser");
  for(i=266;i<532;i=i+1)byte_in(evil[i]);repeat(4)@(negedge clk);
  if(!fault||error!=1||initialized||accepted!=1)$fatal(1,"bad chunk CRC enabled piano");
  control(2,6,0,127);if(triggers!=0)$fatal(1,"normal triggers accepted in failed upload session");
  begin_session;upload_all;control(8'hb2,0,0,0);
  while(!initialized)begin @(negedge clk);if(fault)$fatal(1,"DDR global CRC %d",error);end
  if(upload_count!=1100||memory.reads!=8800||status!=3)$fatal(1,"complete readback/status");
  control(2,6,0,127);repeat(2)@(negedge clk);if(triggers!=1)$fatal(1,"normal control not restored");
  for(v=0;v<16;v=v+1)begin
   load_voice=v;load_bank=v*22+17;load_epoch=32+v;load_valid=1;@(negedge clk);load_valid=0;repeat(2)@(negedge clk);
  end
  for(v=0;v<16;v=v+1)while(last_epoch[v]!=(32+v))@(negedge clk);
  for(v=0;v<16;v=v+1)for(m=0;m<16;m=m+1)begin
   tonal_address={v[3:0],m[3:0]};tonal_enable=1;@(negedge clk);tonal_enable=0;@(negedge clk);
   k=(v*22+17)*25+m;
   if(weights!==image[k][191:0]||frequency!==image[k][223:192])$fatal(1,"DDR voice cache address/data");
  end
  load_voice=0;load_bank=0;load_epoch=100;load_valid=1;@(negedge clk);load_valid=0;repeat(6)@(negedge clk);
  flush=1;@(negedge clk);flush=0;load_bank=351;load_epoch=101;load_valid=1;@(negedge clk);load_valid=0;
  while(last_epoch[0]!=101)begin @(negedge clk);if(last_epoch[0]==100)$fatal(1,"cancelled cache fill emitted completion");end
  // A valid per-packet CRC cannot hide corruption from full-bank readback.
  begin_session;upload_all;
  memory.memory[0]=memory.memory[0]^256'd1;
  control(8'hb2,0,0,0);while(!fault)@(negedge clk);
  if(error!=4||initialized)$fatal(1,"DDR corruption not rejected");
  $display("PASS piano upload: 1100 host packets, shared SD staging owner isolation, CRC32, embedded-command isolation, retry, all 8800 DDR records read back, 16 caches, epoch/flush, global corruption rejection");
  $finish;
 end
 initial begin #2000000000;$fatal(1,"timeout");end
endmodule

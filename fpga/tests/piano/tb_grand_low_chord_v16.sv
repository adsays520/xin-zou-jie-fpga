`timescale 1ns/1ps
module tb_grand_low_chord_v16;
 reg clk=0,rst_n=0,tick=0,on=0,off=0,poly=1;
 reg [6:0] key=60,velocity=110;reg [2:0] pedal=4;
 reg memory_rst_n=0;
 reg upload_begin=0,upload_valid=0,upload_commit=0;
 reg [10:0] upload_index=0;reg [2047:0] upload_data=0;
 wire upload_ready;wire [10:0] upload_count;
 reg [255:0] bank_image[0:8799];integer chunk,k;
 wire req_valid,req_ready,rsp_valid,rsp_ready,bank_ready,memory_fault;
 wire [63:0] req_data,rsp_data;
 wire valid,active,miss;wire signed [23:0] pcm;wire [31:0] step;
 piano_wavetable16_tdm dut(.clk(clk),.rst_n(rst_n),.sample_tick(tick),.note_on(on),.note_off(off),.poly_mode(poly),
 .requested_key(key),.velocity(velocity),.pedal_level(pedal),.sample_valid(valid),.sample_out(pcm),.active(active),.deadline_miss(miss),.requested_phase_step(step),
 .upload_begin(upload_begin),.upload_valid(upload_valid),.upload_commit(upload_commit),.upload_error(1'b0),
 .upload_index(upload_index),.upload_data(upload_data),.upload_ready(upload_ready),.upload_count(upload_count),.bank_status(),.status_error(),
 .memory_rst_n(memory_rst_n),.memory_ready(1'b1),.transport_fault(1'b0),.bank_ready(bank_ready),.memory_fault(memory_fault),
 .req_valid(req_valid),.req_ready(req_ready),.req_data(req_data),.rsp_valid(rsp_valid),.rsp_ready(rsp_ready),.rsp_data(rsp_data));
 piano_packet_memory memory(.clk(clk),.rst_n(memory_rst_n),.req_valid(req_valid),.req_ready(req_ready),.req_data(req_data),.rsp_valid(rsp_valid),.rsp_ready(rsp_ready),.rsp_data(rsp_data));
 wire board_valid;wire signed [23:0] board_l,board_r;
 piano_soundboard board(clk,rst_n,valid,pcm,pedal,board_valid,board_l,board_r);
 integer board_fd;
 always #10 clk=~clk;
 integer cycle_count=0,maximum_latency=0,received=0,fd,frames=24000,key_arg=96,vel_arg=110;
 string filename="work/piano.raw";integer n,previous,first_sample;
 always @(posedge clk)cycle_count<=cycle_count+1;
 task reset_core;
  begin rst_n=0;repeat(3)@(negedge clk);rst_n=1;repeat(2)@(negedge clk);end
 endtask
 task note(input integer k,input integer v);
  begin key=k;velocity=v;on=1;@(negedge clk);on=0;repeat(3)@(negedge clk);
   while(dut.u_parameters.pending!=0||dut.u_parameters.state!=7)@(negedge clk);repeat(2)@(negedge clk);end
 endtask
 task frame;
  integer started,elapsed;
  begin
   started=cycle_count;tick=1;@(negedge clk);tick=0;
   while(!valid)begin @(negedge clk);if(cycle_count-started>1040)$fatal(1,"deadline");end
   elapsed=cycle_count-started;if(elapsed>maximum_latency)maximum_latency=elapsed;
   if(^pcm===1'bx)$fatal(1,"unknown PCM");
   if(miss)$fatal(1,"deadline flag");
`ifndef LEGACY
   if(dut.physics_clip)$fatal(1,"internal modal overflow");
`endif
   while(!board_valid)begin @(negedge clk);if(cycle_count-started>1040)$fatal(1,"combined piano/body deadline");end
   if(^board_l===1'bx||^board_r===1'bx)$fatal(1,"unknown board PCM");
   received++;
   @(negedge clk);
  end
 endtask
 initial begin
  if($value$plusargs("KEY=%d",key_arg))begin end
  if($value$plusargs("VEL=%d",vel_arg))begin end
  if($value$plusargs("FRAMES=%d",frames))begin end
  if($value$plusargs("OUT=%s",filename))begin end
  repeat(3)@(negedge clk);memory_rst_n=1;
  $readmemh("src/piano/sms_ddr/bank_image.hex",bank_image);
  upload_begin=1;@(negedge clk);upload_begin=0;
  repeat(3)@(negedge clk);
  for(chunk=0;chunk<1100;chunk=chunk+1)begin
   while(!upload_ready)@(negedge clk);
   upload_index=chunk;
   for(k=0;k<8;k=k+1)upload_data[k*256+:256]=bank_image[chunk*8+k];
   upload_valid=1;@(negedge clk);upload_valid=0;repeat(2)@(negedge clk);
  end
  while(upload_count!=1100)@(negedge clk);
  upload_commit=1;@(negedge clk);upload_commit=0;
  while(!bank_ready)begin @(negedge clk);if(memory_fault)$fatal(1,"DDR initialization verification");end
  if(memory.writes!=8800||memory.reads!=8800)$fatal(1,"DDR full-bank bootstrap/readback");
  reset_core;note(key_arg,vel_arg);fd=$fopen(filename,"wb");
  board_fd=$fopen({filename,".board"},"wb");
  if(fd==0)$fatal(1,"output file");
  for(n=0;n<frames;n=n+1)begin
   frame;
   $fwrite(board_fd,"%c%c%c%c%c%c",board_l[7:0],board_l[15:8],board_l[23:16],board_r[7:0],board_r[15:8],board_r[23:16]);
   $fwrite(fd,"%c%c%c",pcm[7:0],pcm[15:8],pcm[23:16]);
  end
  $fclose(fd);$fclose(board_fd);
  // Note-off, full-pedal release, rapid voice stealing and mid-frame events.
  off=1;@(negedge clk);off=0;pedal=0;repeat(128)frame;
  for(n=0;n<20;n=n+1)begin note(48+n*3,127);frame;end
  repeat(64)frame;
  reset_core;
  for(n=0;n<16;n=n+1)note(24,127);
  repeat(1024)begin frame;if(pcm==24'sh7fffff||pcm==24'sh800000)$fatal(1,"coherent low C1 chord clipping");end
  // Replace a voice while a sample is being evaluated, not only at idle.
  tick=1;@(negedge clk);tick=0;repeat(9)@(negedge clk);key=96;velocity=100;on=1;@(negedge clk);on=0;
  while(!valid)@(negedge clk);
  if(^pcm===1'bx||miss)$fatal(1,"mid-frame steal");
  @(negedge clk);repeat(8)frame;
  // Concurrent notes must fit the actual 50 MHz/48 kHz cycle budget.
  if(maximum_latency>=1041)$fatal(1,"polyphonic budget");
  reset_core;repeat(8)begin frame;if(pcm!==0)$fatal(1,"reset silence");end
  $display("PASS DDR piano key=%0d velocity=%0d frames=%0d max_latency=%0d cycles",key_arg,vel_arg,received,maximum_latency);
  $finish;
 end
 initial begin #2000000000;$fatal(1,"timeout");end
endmodule

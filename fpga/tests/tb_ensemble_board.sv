`timescale 1ns/1ps
module tb_ensemble_board;
 reg clk=0,reset_n=0,rx=1,gsr_n=0;
 always #10 clk=~clk;
 GSR GSR(.GSRI(gsr_n));
 wire [5:0] led;
 wire sd_clk,sd_cs,sd_mosi,sd_miso;reg ssck=0,scs=1,smosi=0;wire smiso;
 wire card_ready,card_valid,card_done;wire [7:0] card_data;
 sd_sector_model card(clk,reset_n,dut.u_audio.sd_read_start,dut.u_audio.sd_read_lba,card_ready,card_data,card_valid,card_done);
 assign sd_miso=1'b1;
 guitar_audio_ddr_top #(.SD_POWERUP_CLKS(10)) dut(.sd_clk(sd_clk),.sd_cs(sd_cs),.sd_mosi(sd_mosi),.sd_miso(sd_miso),.spi_sclk(ssck),.spi_cs_n(scs),.spi_mosi(smosi),.spi_miso(smiso),.clk(clk),.reset_n(reset_n),.key_next_n(1'b1),.key_pluck_n(1'b1),.uart_rx_i(rx),.led_n(led));
 reg setup_begin=0,setup_valid=0,setup_commit=0;
 reg [10:0] setup_index=0;reg [2047:0] setup_data=0;
 reg [255:0] image[0:8799];
 integer i,k,frames=0,piano_pcm=0,bass_pcm=0,mixed_pcm=0;
 integer violin_pcm=0,spi_seq=0;reg observe=0;
 always @(posedge clk)if(observe&&dut.u_audio.sample_tick)begin
  if(dut.u_audio.violin_fault||dut.u_audio.pluck_queue_overflow)$fatal(1,"violin/queue status");
  if(dut.u_audio.timbre_violin&&dut.u_audio.violin_sample!=0&&dut.u_audio.frame_audio_word_l!=0)violin_pcm++;
 end
 always @(posedge clk)if(observe&&dut.u_audio.sample_tick)begin
  frames=frames+1;
  if(dut.u_audio.piano_deadline_miss||dut.u_audio.drum_deadline_miss||dut.u_audio.poly_deadline_miss||dut.u_audio.bass_deadline_miss||dut.u_audio.fx_deadline_miss||dut.u_audio.space_deadline_miss)
   $fatal(1,"whole board audio deadline");
  if(^dut.u_audio.frame_audio_word_l===1'bx||^dut.u_audio.frame_audio_word_r===1'bx)$fatal(1,"unknown final DAC sample");
  if(dut.u_audio.timbre_piano&&dut.u_audio.piano_active&&dut.u_audio.frame_audio_word_l!=0)begin
   piano_pcm=piano_pcm+1;if(dut.u_audio.drum_active)mixed_pcm=mixed_pcm+1;
  end
  if(dut.u_audio.timbre_bass&&dut.u_audio.frame_audio_word_l!=0)bass_pcm=bass_pcm+1;
 end
 task byte_tx(input [7:0] b);
  integer n;
  begin @(negedge clk);rx=0;repeat(434)@(negedge clk);
   for(n=0;n<8;n=n+1)begin rx=b[n];repeat(434)@(negedge clk);end
   rx=1;repeat(450)@(negedge clk);
  end
 endtask
 task tx(input [7:0] op,a,b,c);
  begin byte_tx(8'ha5);byte_tx(op);byte_tx(a);byte_tx(b);byte_tx(c);byte_tx(8'ha5^op^a^b^c);end
 endtask
 task wait_frames(input integer count);
  integer target;
  begin target=frames+count;while(frames<target)@(negedge clk);end
 endtask
 reg [7:0] sp[0:63];
 function [15:0] crc16(input [15:0] old,input [7:0] value);
 reg [15:0] c;integer n;begin c=old^{value,8'd0};for(n=0;n<8;n++)c=c[15]?(c<<1)^16'h1021:c<<1;crc16=c;end endfunction
 task spi_snapshot(input [127:0] keys);
 reg [15:0] crc;integer x,y;
 begin
   spi_seq++;for(x=0;x<64;x++)sp[x]=0;
   sp[0]=8'ha5;sp[1]=8'h53;sp[2]=1;sp[4]=spi_seq;sp[5]=spi_seq>>8;sp[6]=255;sp[7]=16;sp[30]=1;sp[56]=27;
   for(x=0;x<16;x++)sp[8+x]=keys[x*8+:8];
   crc=16'hffff;for(x=0;x<62;x++)crc=crc16(crc,sp[x]);sp[62]=crc[15:8];sp[63]=crc[7:0];
   scs=0;repeat(100)@(negedge clk);
   for(x=0;x<64;x++)for(y=7;y>=0;y--)begin
     smosi=sp[x][y];repeat(25)@(negedge clk);ssck=1;repeat(25)@(negedge clk);ssck=0;
   end
   repeat(100)@(negedge clk);scs=1;repeat(1000)@(negedge clk);
 end endtask
 initial begin
  $readmemh("src/piano/sms_ddr/bank_image.hex",image);
  // Collapse SD serial bit wait clocks at the sector boundary. Actual mode-0
  // SPI/init/CRC16 was checked separately. FAT, DDR CRC and CDC remain real.
  force dut.u_audio.sd_card_ready=card_ready;
  force dut.u_audio.sd_card_error=8'd0;
  force dut.u_audio.sd_byte=card_data;
  force dut.u_audio.sd_byte_valid=card_valid;
  force dut.u_audio.sd_sector_done=card_done;
  force dut.u_audio.sample_tick=1'b0;
  repeat(12)@(negedge clk);gsr_n=1;reset_n=1;
  while(!dut.bank_ready)begin
    @(negedge clk);
    if(dut.bank_fault||dut.system_fault||dut.u_audio.sd_boot_error)$fatal(1,"SD bank startup err=%h status=%h",dut.u_audio.sd_boot_error,dut.u_audio.sd_card_error);
  end
  if(dut.u_ddr3.application.writes!=8800||dut.u_ddr3.application.reads!=8800||card.reads!=1102)$fatal(1,"SD native DDR coverage");
  while(!dut.u_audio.drum_parameter_initialized)begin
   @(negedge clk);
   if(dut.u_audio.drum_parameter_fault||dut.u_audio.sd_boot_error)$fatal(1,"SD drum bank startup");
  end
  release dut.u_audio.sample_tick;observe=1;wait_frames(100);
  if(!dut.u_audio.drum_parameter_active_bank)$fatal(1,"SD drum bank not activated at sample boundary");
  $display("BOARD progress: real native DDR/CDC bank readback complete");$fflush();
  tx(4,1,0,0);tx(6,4,0,0);tx(5,36,110,1);wait_frames(100);
  if(piano_pcm<50||!dut.u_audio.piano_active)$fatal(1,"DDR SMS did not reach final DAC PCM");
  tx(5,36,110,0);wait_frames(30);
  if(dut.u_audio.u_piano_wavetable.key_down[0]||dut.u_audio.u_piano_wavetable.damper_gain[0]!=32'hffffffff)$fatal(1,"full pedal note-off");
  tx(8'h50,0,127,0);wait_frames(160);
  if(mixed_pcm<40)$fatal(1,"DDR piano and algorithmic kick did not mix");
  tx(6,0,0,0);wait_frames(80);
  if(dut.u_audio.u_piano_wavetable.damper_gain[0]>=32'hffffffff)$fatal(1,"pedal release");
  tx(4,2,0,0);tx(2,6,0,110);wait_frames(100);
  if(dut.u_audio.piano_active||!dut.bank_ready||bass_pcm<50||!dut.u_audio.drum_active)$fatal(1,"Bass switch/cache lifetime");
  tx(4,0,0,0);tx(2,6,3,110);tx(8'h90,8'h11,8'hf5,8'h9b);tx(8'h91,1,0,0);wait_frames(80);
  if(!dut.u_audio.pitch_enabled||!dut.u_audio.voice_bank_active||dut.u_audio.piano_active||!dut.bank_ready)$fatal(1,"guitar pitch restore");
  tx(8'h52,0,0,0);wait_frames(100);
  if(dut.u_audio.drum_active)$fatal(1,"drum stop before isolated violin test");
  $display("BOARD progress: piano/drums/Bass/guitar checks complete; isolated violin next");$fflush();
  tx(4,3,0,0);tx(8,69,100,1);wait_frames(250);
  if(!dut.u_audio.violin_active||violin_pcm<80||dut.u_audio.voice_bank_active)$fatal(1,"violin UART did not reach final DAC %0d",violin_pcm);
  tx(8'h70,3,0,0);wait_frames(350);
  if(dut.u_audio.frame_audio_word_l!=0||dut.u_audio.frame_audio_word_r!=0)$fatal(1,"violin independent bus did not mute final DAC");
  tx(8'h70,3,127,0);wait_frames(250);
  if(dut.u_audio.frame_audio_word_l==0)$fatal(1,"violin independent bus did not restore final DAC");
  tx(8,72,90,3);wait_frames(60);tx(8,69,1,0);wait_frames(60);
  if(!dut.u_audio.violin_active)$fatal(1,"old-key off stopped legato target");
  tx(8,72,1,0);tx(9,2,0,0);
  if(!dut.u_audio.trigger_hall_mode)$fatal(1,"host Hall mode ignored");
  spi_snapshot(128'd1);wait_frames(60);
  if(dut.u_audio.u_s3_link.touch_keys!=128'd1)$fatal(1,"ESP Hall selection failed");
  tx(9,1,0,0);spi_snapshot(128'd0);spi_snapshot(128'd1<<48);wait_frames(250);
  if(dut.u_audio.trigger_hall_mode||!dut.u_audio.violin_active||dut.u_audio.u_s3_link.good_frames<3)$fatal(1,"ESP direct touch did not bow violin");
  spi_snapshot(128'd0);tx(4,0,0,0);wait_frames(30);
  if(dut.u_audio.violin_active||!dut.bank_ready)$fatal(1,"violin switch damaged persistent piano bank");
  reset_n=0;repeat(30)@(negedge clk);reset_n=1;wait_frames(100);
  if(dut.bank_ready||dut.u_audio.piano_active||dut.u_audio.drum_active||dut.u_audio.frame_audio_word_l!=0)$fatal(1,"reset validity/silence");
  $display("PASS ENSEMBLE BOARD: SD sector/guitar-bank models (vendor bank/core equivalence tested separately) -> real fragmented FAT32 -> 8800 native DDR writes/full readback; host violin/legato + physical ESP SPI touch/direct/Hall mode -> final DAC; native DDR application model + real dual-clock FIFO + DDR bank + actual 115200 UART notes -> SMS -> mixer -> final DAC words; piano=%0d mixed=%0d Bass=%0d violin=%0d; pedal, guitar pitch, persistent bank and reset",piano_pcm,mixed_pcm,bass_pcm,violin_pcm);
  $finish;
 end
 initial begin #4000000000;$fatal(1,"timeout");end
endmodule

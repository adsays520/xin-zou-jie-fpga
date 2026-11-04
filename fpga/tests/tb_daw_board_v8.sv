`timescale 1ns/1ps
module tb_daw_board_v8;
 reg clk=0,reset_n=0,rx=1,gsr_n=0;
 always #10 clk=~clk;
 GSR GSR(.GSRI(gsr_n));
 wire sd_clk,sd_cs,sd_mosi,uart_tx;
 wire card_ready,card_valid,card_done;wire [7:0] card_data;
 sd_sector_model card(clk,reset_n,dut.u_audio.sd_read_start,dut.u_audio.sd_read_lba,card_ready,card_data,card_valid,card_done);
 guitar_audio_ddr_top #(.SD_POWERUP_CLKS(10)) dut(.clk(clk),.reset_n(reset_n),.key_next_n(1'b1),.key_pluck_n(1'b1),
  .sw1_enc_a(1'b1),.sw1_enc_b(1'b1),.sw2_enc_a(1'b1),.sw2_enc_b(1'b1),
  .sw1_up_n(1'b1),.sw1_right_n(1'b1),.sw1_down_n(1'b1),.sw1_left_n(1'b1),
  .uart_rx_i(rx),.uart_tx_o(uart_tx),.sd_clk(sd_clk),.sd_cs(sd_cs),.sd_mosi(sd_mosi),.sd_miso(1'b1),
  .spi_sclk(1'b0),.spi_cs_n(1'b1),.spi_mosi(1'b0));
 wire [7:0] received;wire received_valid;
 uart_rx_8n1 receive(.clk(clk),.rst_n(reset_n),.rx_i(uart_tx),.data_o(received),.data_valid_o(received_valid));
 reg [7:0] reply[0:11];integer reply_count=0;
 always @(posedge clk)if(received_valid)begin reply[reply_count%12]<=received;reply_count++;end
 integer frames=0,simultaneous=0,pcm=0;
 reg observing=0,watch_clear=0;
 reg panel_test_valid=0;
 reg [47:0] panel_test_data=48'ha570046400b5;
 always @(posedge clk)begin
  if(watch_clear&&dut.u_audio.clear_voice_bank)$fatal(1,"targeted note cleared unrelated engines");
  if(observing&&dut.u_audio.sample_tick)begin
   frames++;
   if(dut.bank_fault||dut.system_fault||dut.u_audio.violin_fault||dut.u_audio.ensemble_mix_deadline||
      dut.u_audio.poly_deadline_miss||dut.u_audio.piano_deadline_miss||dut.u_audio.bass_deadline_miss||
      dut.u_audio.drum_deadline_miss||dut.u_audio.fx_deadline_miss||dut.u_audio.space_deadline_miss)$fatal(1,"DAW deadline/storage/audio fault");
   if(^dut.u_audio.frame_audio_word_l===1'bx||^dut.u_audio.frame_audio_word_r===1'bx)$fatal(1,"unknown final DAC words");
   if(dut.u_audio.ensemble_mode&&dut.u_audio.guitar_hold!=0&&dut.u_audio.bass_hold!=0&&
      dut.u_audio.piano_hold_l!=0&&dut.u_audio.violin_sample!=0&&dut.u_audio.drum_hold_l!=0)begin
    simultaneous++;
    if(dut.u_audio.frame_audio_word_l!=0||dut.u_audio.frame_audio_word_r!=0)pcm++;
   end
  end
 end
 task byte_tx(input [7:0] value);
  integer bit_number;
  begin @(negedge clk);rx=0;repeat(434)@(negedge clk);
   for(bit_number=0;bit_number<8;bit_number++)begin rx=value[bit_number];repeat(434)@(negedge clk);end
   rx=1;repeat(450)@(negedge clk);
  end
 endtask
 task tx(input [7:0] opcode,first,second,third);
  begin byte_tx(8'ha5);byte_tx(opcode);byte_tx(first);byte_tx(second);byte_tx(third);byte_tx(8'ha5^opcode^first^second^third);end
 endtask
 task wait_frames(input integer count);
  integer ending;
  begin ending=frames+count;while(frames<ending)@(negedge clk);end
 endtask
 initial begin
  force dut.u_audio.sd_card_ready=card_ready;force dut.u_audio.sd_card_error=8'd0;
  force dut.u_audio.sd_byte=card_data;force dut.u_audio.sd_byte_valid=card_valid;force dut.u_audio.sd_sector_done=card_done;
  force dut.u_audio.sample_tick=1'b0;
  repeat(12)@(negedge clk);gsr_n=1;reset_n=1;
  while(!dut.bank_ready)begin
   @(negedge clk);if(dut.bank_fault||dut.system_fault||dut.u_audio.sd_boot_error)$fatal(1,"SD startup");
  end
  if(dut.u_ddr3.application.writes!=8800||dut.u_ddr3.application.reads!=8800)$fatal(1,"full DDR bank verification");
  while(!dut.u_audio.drum_parameter_initialized)@(negedge clk);
  release dut.u_audio.sample_tick;observing=1;wait_frames(20);
  $display("DAW progress: SD -> native DDR full bank readback passed");$fflush();
  tx(8'h0f,8'h75,0,0);while(reply_count<6)@(negedge clk);
  if(reply[0]!=8'hd8||reply[1]!=8'h45||reply[2]!=8'h75||reply[3]!=8'h08||reply[4]!=7||
     (reply[0]^reply[1]^reply[2]^reply[3]^reply[4]^reply[5])!=0)$fatal(1,"capability handshake");
  tx(8'h0e,1,0,0);wait_frames(2);watch_clear=1;
  if(!dut.u_audio.ensemble_mode)$fatal(1,"DAW mode not enabled");
  @(negedge clk);
  dut.u_audio.u_s3_link.command_data=48'ha504010000a0;
  dut.u_audio.u_s3_link.command_valid=1;
  dut.u_audio.u_s3_link.hall_valid=1;
  repeat(8)@(negedge clk);
  if(dut.u_audio.s3_command_valid||dut.u_audio.s3_hall_valid||dut.u_audio.u_control_ingress.active)
   $fatal(1,"S3 controls must be consumed without replay during DAW");
  force dut.u_audio.panel_command_valid=panel_test_valid;
  force dut.u_audio.panel_command_data=panel_test_data;
  panel_test_valid=1;
  @(posedge clk);while(!dut.u_audio.panel_command_ready)@(posedge clk);
  @(negedge clk);panel_test_valid=0;
  repeat(40)@(negedge clk);
  release dut.u_audio.panel_command_valid;
  release dut.u_audio.panel_command_data;
  if(dut.u_audio.bass_bus_level!=100||!dut.u_audio.ensemble_mode)
   $fatal(1,"Panel command lost or disabled DAW mode");
  $display("DAW progress: panel local control accepted while ensemble mode remains active");$fflush();
  tx(8'h0c,60,90,1);tx(8'h0b,6,0,90);tx(8'h0a,1,0,90);tx(8'h0d,69,90,1);tx(8'h50,0,100,0);
  wait_frames(450);
  if(simultaneous<80||pcm<70||!dut.u_audio.piano_active||!dut.u_audio.voice_bank_active||
     !dut.u_audio.bass_active||!dut.u_audio.violin_active||!dut.u_audio.drum_active)
   $fatal(1,"five instruments not simultaneously audible: all=%0d DAC=%0d",simultaneous,pcm);
  $display("DAW progress: five active audio buses simultaneously reach final DAC words frames=%0d",pcm);$fflush();
  tx(8'h70,4,0,0);wait_frames(170);
  if(dut.u_audio.u_performance_mixer.gains[4]!=0||!dut.u_audio.voice_bank_active||!dut.u_audio.piano_active||!dut.u_audio.violin_active)
   $fatal(1,"Bass mute disturbed another engine");
  tx(8'h0c,60,1,0);wait_frames(20);
  if(dut.u_audio.u_piano_wavetable.key_down[0]||!dut.u_audio.violin_active||!dut.u_audio.bass_active||!dut.u_audio.voice_bank_active)
   $fatal(1,"piano release cleared another engine");
  tx(8'h0d,72,90,3);tx(8'h0d,69,1,0);wait_frames(30);
  if(!dut.u_audio.violin_active||!dut.bank_ready)$fatal(1,"legato/persistent bank");
  watch_clear=0;tx(8'h0e,0,0,0);wait_frames(30);
  if(dut.u_audio.ensemble_mode||dut.u_audio.voice_bank_active||dut.u_audio.piano_active||dut.u_audio.bass_active)$fatal(1,"DAW stop did not clear main engines");
  tx(4,1,0,0);tx(5,64,90,1);wait_frames(100);
  if(!dut.u_audio.piano_active||dut.u_audio.ensemble_mode||!dut.bank_ready)$fatal(1,"legacy piano return");
  $display("PASS DAW BOARD V8: actual 115200 UART capability/targets -> independent guitar32/Bass8/SMS-piano16/violin plus drums -> shared serial mixer/limiter -> final stereo DAC words; concurrent=%0d DAC=%0d; independent Bass mute, piano release, legato, stop, legacy return; SD sector/guitar-bank/DDR PHY application models with real FAT/DDR transport/cache/audio RTL",simultaneous,pcm);
  $finish;
 end
 initial begin #4000000000;$fatal(1,"DAW board timeout");end
endmodule

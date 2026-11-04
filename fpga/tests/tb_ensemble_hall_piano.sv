`timescale 1ns/1ps
module tb_ensemble_hall_piano;
    reg clk=0, reset_n=0, gsr_n=0, rx=1;
    always #10 clk=~clk;
    GSR GSR(.GSRI(gsr_n));
    reg spi_clock=0, spi_select_n=1, spi_mosi=0;
    wire card_ready, card_valid, card_done;
    wire [7:0] card_data;
    sd_sector_model card(clk,reset_n,dut.u_audio.sd_read_start,dut.u_audio.sd_read_lba,
                         card_ready,card_data,card_valid,card_done);
    guitar_audio_ddr_top #(.SD_POWERUP_CLKS(10)) dut(
        .clk(clk),.reset_n(reset_n),.key_next_n(1'b1),.key_pluck_n(1'b1),.uart_rx_i(rx),
        .sd_miso(1'b1),.spi_sclk(spi_clock),.spi_cs_n(spi_select_n),.spi_mosi(spi_mosi));
    integer frames=0, events=0, sounding_frames=0, sequence_number=0;
    reg observing=0;
    reg [6:0] observed_keys[0:7], observed_velocity[0:7];
    reg [7:0] packet[0:63];
    always @(posedge clk) if(observing)begin
        if(dut.u_audio.piano_note_on_q)begin
            if(events>=8)$fatal(1,"unexpected Hall note flood");
            observed_keys[events]=dut.u_audio.piano_key_q;
            observed_velocity[events]=dut.u_audio.piano_velocity_q;
            events=events+1;
        end
        if(dut.u_audio.sample_tick)begin
            frames=frames+1;
            if(dut.u_audio.piano_deadline_miss||dut.u_audio.space_deadline_miss||dut.u_audio.pluck_queue_overflow)
                $fatal(1,"Hall DDR piano deadline or queue overflow");
            if(^dut.u_audio.frame_audio_word_l===1'bx||^dut.u_audio.frame_audio_word_r===1'bx)
                $fatal(1,"unknown final DAC words");
            if(dut.u_audio.piano_active&&dut.u_audio.frame_audio_word_l!=0)sounding_frames=sounding_frames+1;
        end
    end
    task wait_frames(input integer count);
        integer target;
        begin target=frames+count;while(frames<target)@(negedge clk);end
    endtask
    task byte_tx(input [7:0] value);
        begin
            @(negedge clk);rx=0;repeat(434)@(negedge clk);
            for(integer bit_index=0;bit_index<8;bit_index++)begin
                rx=value[bit_index];repeat(434)@(negedge clk);
            end
            rx=1;repeat(450)@(negedge clk);
        end
    endtask
    task command(input [7:0] opcode, first, second, third);
        begin
            byte_tx(8'ha5);byte_tx(opcode);byte_tx(first);byte_tx(second);byte_tx(third);
            byte_tx(8'ha5^opcode^first^second^third);
        end
    endtask
    function [15:0] crc_byte(input [15:0] previous,input [7:0] value);
        reg [15:0] checksum;
        begin
            checksum=previous^{value,8'd0};
            for(integer bit_index=0;bit_index<8;bit_index++)
                checksum=checksum[15]?(checksum<<1)^16'h1021:checksum<<1;
            crc_byte=checksum;
        end
    endfunction
    task transfer(input integer kind,input [127:0] live_keys,event_keys,input [7:0] velocity);
        reg [15:0] checksum;
        begin
            sequence_number=sequence_number+1;
            for(integer byte_index=0;byte_index<64;byte_index++)packet[byte_index]=0;
            packet[0]=8'ha5;packet[1]=8'h53;packet[2]=1;packet[3]=kind;
            packet[4]=sequence_number;packet[5]=sequence_number>>8;
            packet[6]=8'hfb;packet[7]=kind==2?7:16;packet[30]=1;packet[56]=27;
            for(integer byte_index=0;byte_index<16;byte_index++)begin
                packet[8+byte_index]=live_keys[byte_index*8+:8];
                if(kind==2)packet[40+byte_index]=event_keys[byte_index*8+:8];
            end
            if(kind==2)begin packet[31]=1;packet[32]=velocity;packet[38]=8'hc1;end
            checksum=16'hffff;
            for(integer byte_index=0;byte_index<62;byte_index++)checksum=crc_byte(checksum,packet[byte_index]);
            packet[62]=checksum[15:8];packet[63]=checksum[7:0];
            @(negedge clk);spi_select_n=0;repeat(100)@(negedge clk);
            for(integer byte_index=0;byte_index<64;byte_index++)
                for(integer bit_index=7;bit_index>=0;bit_index--)begin
                    spi_mosi=packet[byte_index][bit_index];repeat(25)@(negedge clk);
                    spi_clock=1;repeat(25)@(negedge clk);spi_clock=0;
                end
            repeat(100)@(negedge clk);spi_select_n=1;repeat(1000)@(negedge clk);
            if(dut.u_audio.u_s3_link.last_sequence!==sequence_number[15:0])$fatal(1,"SPI frame not accepted");
        end
    endtask
    initial begin
        force dut.u_audio.sd_card_ready=card_ready;
        force dut.u_audio.sd_card_error=8'd0;
        force dut.u_audio.sd_byte=card_data;
        force dut.u_audio.sd_byte_valid=card_valid;
        force dut.u_audio.sd_sector_done=card_done;
        force dut.u_audio.sample_tick=1'b0;
        repeat(12)@(negedge clk);gsr_n=1;reset_n=1;
        while(!dut.bank_ready)begin
            @(negedge clk);
            if(dut.bank_fault||dut.system_fault||dut.u_audio.sd_boot_error)$fatal(1,"SD DDR piano startup");
        end
        if(dut.u_ddr3.application.writes!=8800||dut.u_ddr3.application.reads!=8800)$fatal(1,"incomplete bank readback");
        release dut.u_audio.sample_tick;
        command(4,1,0,0);command(9,2,0,0);
        if(!dut.u_audio.trigger_hall_mode||!dut.u_audio.timbre_piano)$fatal(1,"Hall piano mode not selected");
        observing=1;wait_frames(20);
        transfer(0,128'd1<<54,0,0);
        if(events!=0)$fatal(1,"touch selection alone sounded piano");
        force dut.u_audio.pluck_ingress_ready=1'b0;
        transfer(2,128'd1<<54,128'd1<<24,104);
        transfer(2,128'd1<<54,128'd1<<48,105);
        transfer(2,128'd1<<54,128'd1<<72,106);
        transfer(0,128'd1<<90,0,0);
        if(events!=0||dut.u_audio.s3_selected_frets[4:0]!=15)$fatal(1,"backpressure/live fret update");
        release dut.u_audio.pluck_ingress_ready;
        wait_frames(160);
        if(events!=3||observed_keys[0]!=44||observed_keys[1]!=48||observed_keys[2]!=52||
           observed_velocity[0]!=104||observed_velocity[1]!=105||observed_velocity[2]!=106)
            $fatal(1,"Hall snapshot did not reach correct SMS piano notes: count=%0d keys=%0d/%0d/%0d",events,observed_keys[0],observed_keys[1],observed_keys[2]);
        if(sounding_frames<40||!dut.u_audio.piano_active||!dut.bank_ready||dut.bank_fault)
            $fatal(1,"Hall notes did not reach final DAC words");
        transfer(0,128'd1<<102,0,0);wait_frames(160);
        if(events!=3)$fatal(1,"touch fret change retriggered Hall piano");
        $display("PASS ENSEMBLE HALL PIANO: SD/DDR full readback; no touch-only note; blocked ingress preserves three event snapshots -> SMS keys 44/48/52 velocity 104/105/106, live frets 15/17; final DAC nonzero frames=%0d; no deadline/fault/retrigger",sounding_frames);
        $finish;
    end
    initial begin #4000000000;$fatal(1,"timeout");end
endmodule

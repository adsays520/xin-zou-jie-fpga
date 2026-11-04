`timescale 1ns/1ps
module tb_touch_hall_link #(parameter AUDIT_BACKPRESSURE=0,parameter TEST_INSTRUMENT=0,parameter ESP_WIRE_VECTORS=0);
    reg clock=0,reset_n=0,spi_clock=0,spi_select_n=1,spi_mosi=0;
    always #10 clock=~clock;
    wire [127:0] touch_keys;
    wire [7:0] touch_online;
    wire touch_enabled,hall_valid,hall_ready,direct_valid,direct_ready;
    wire [5:0] hall_mask;
    wire [47:0] hall_velocity,direct_data,touch_data;
    wire [29:0] selected_frets,hall_frets;
    wire touch_valid,touch_ready,ingress_ready,control_valid;
    wire [7:0] control_data;
    wire hall_mode;
    wire [1:0] trigger_mode=hall_mode?2'd2:2'd1;
    reg downstream_ready=1;
    wire trigger;
    wire [2:0] trigger_string;
    wire [4:0] trigger_fret;
    wire [6:0] trigger_velocity;
    wire piano_selected,bass_selected,violin_selected,piano_on,violin_on;
    wire [6:0] piano_key,piano_velocity,violin_key,violin_velocity;
    wire [1:0] instrument=violin_selected?3:bass_selected?2:piano_selected?1:0;
    reg [7:0] packet[0:63];
    reg [7:0] esp_vectors[0:639];
    reg [127:0] held_keys=0;
    integer sequence_number=0,event_count=0,expected_events=0;
    integer observed_string[0:31],observed_fret[0:31],observed_velocity[0:31];

    s3_spi_link link(
        .clk(clock),.rst_n(reset_n),.spi_sclk(spi_clock),.spi_cs_n(spi_select_n),.spi_mosi(spi_mosi),
        .touch_keys(touch_keys),.touch_online(touch_online),.touch_enabled(touch_enabled),
        .hall_mask(hall_mask),.hall_velocity(hall_velocity),.hall_frets(hall_frets),.hall_valid(hall_valid),.hall_ready(hall_ready),
        .command_data(direct_data),.command_valid(direct_valid),.command_ready(direct_ready),
        .rgb24(24'd0),.pixel_x(8'd0),.pixel_y(8'd0),.display_page(2'd0),.instrument(instrument),
        .hall_mode(hall_mode),.selected_frets(selected_frets),.trigger_mode(trigger_mode));
    touch_to_command touch(
        .clk(clock),.rst_n(reset_n),.enabled(touch_enabled),.keys(touch_keys),.instrument(instrument),
        .hall_mode(hall_mode),.hall_mask(hall_mask),.hall_velocity(hall_velocity),.hall_frets(hall_frets),
        .hall_valid(hall_valid),.hall_ready(hall_ready),.selected_frets(selected_frets),
        .command_data(touch_data),.command_valid(touch_valid),.command_ready(touch_ready));
    assign direct_ready=ingress_ready&&downstream_ready;
    assign touch_ready=ingress_ready&&!direct_valid&&downstream_ready;
    s3_control_ingress ingress(
        .clk(clock),.rst_n(reset_n),.uart_rx_i(1'b1),
        .command_data(direct_valid?direct_data:touch_data),
        .command_valid((direct_valid||touch_valid)&&downstream_ready),.command_ready(ingress_ready),.commands_enabled(downstream_ready),
        .byte_data(control_data),.byte_valid(control_valid));
    guitar_uart_trigger #(.EXTERNAL_BYTES(1)) parser(
        .clk(clock),.rst_n(reset_n),.uart_rx_i(1'b1),
        .external_byte_data(control_data),.external_byte_valid(control_valid),
        .local_level_step(1'b0),.local_level_bus(2'd0),.envelope_write_allowed(1'b1),
        .trigger_string_sel(trigger_string),.trigger_fret_sel(trigger_fret),
        .trigger_velocity(trigger_velocity),.trigger(trigger),.hall_mode(hall_mode),
        .timbre_piano(piano_selected),.timbre_bass(bass_selected),.timbre_violin(violin_selected),
        .piano_note_on(piano_on),.piano_key(piano_key),.piano_velocity(piano_velocity),
        .violin_note_on(violin_on),.violin_key(violin_key),.violin_velocity(violin_velocity));

    always @(posedge clock) if(trigger||piano_on||violin_on) begin
        if(event_count>=32)$fatal(1,"Unexpected event flood");
        observed_string[event_count]=trigger?trigger_string+1:6;
        observed_fret[event_count]=trigger?trigger_fret:piano_on?piano_key-40:violin_key-55;
        observed_velocity[event_count]=trigger?trigger_velocity:piano_on?piano_velocity:violin_velocity;
        event_count=event_count+1;
    end

    function [15:0] crc_byte(input [15:0] checksum,input [7:0] value);
        reg [15:0] work;
        integer bit_index;
        begin
            work=checksum^{value,8'd0};
            for(bit_index=0;bit_index<8;bit_index=bit_index+1)
                work=work[15]?(work<<1)^16'h1021:work<<1;
            crc_byte=work;
        end
    endfunction
    task seal_packet;
        reg [15:0] checksum;
        begin
            checksum=16'hffff;
            for(integer byte_index=0;byte_index<62;byte_index=byte_index+1)
                checksum=crc_byte(checksum,packet[byte_index]);
            packet[62]=checksum[15:8];packet[63]=checksum[7:0];
        end
    endtask
    task make_packet(input integer kind,input [127:0] keys,input enabled);
        begin
            sequence_number=sequence_number+1;
            for(integer byte_index=0;byte_index<64;byte_index=byte_index+1)packet[byte_index]=0;
            packet[0]=8'ha5;packet[1]=8'h53;packet[2]=1;packet[3]=kind;
            packet[4]=sequence_number;packet[5]=sequence_number>>8;
            packet[6]=8'hfb;packet[7]=kind==0?16:kind==1?6:7;
            for(integer byte_index=0;byte_index<16;byte_index=byte_index+1)
                packet[8+byte_index]=keys[byte_index*8+:8];
            packet[30]=enabled;packet[56]=1;
        end
    endtask
    task shift_packet;
        begin
            spi_select_n=0;#2000;
            for(integer byte_index=0;byte_index<64;byte_index=byte_index+1)
                for(integer bit_index=7;bit_index>=0;bit_index=bit_index-1)begin
                    spi_mosi=packet[byte_index][bit_index];#500;spi_clock=1;#500;spi_clock=0;
                end
            #2000;spi_select_n=1;#5000;
            if(link.last_sequence!==sequence_number[15:0])$fatal(1,"SPI request not accepted");
        end
    endtask
    task exchange;
        begin seal_packet();shift_packet();end
    endtask
    task send_mode(input [7:0] mode);
        begin
            make_packet(1,0,1);
            packet[24]=8'ha5;packet[25]=9;packet[26]=mode;packet[29]=8'ha5^9^mode;
            exchange();#1100000;
            if(trigger_mode!==mode[1:0])$fatal(1,"Mode command did not reach parser");
        end
    endtask
    task send_keys(input [127:0] keys);
        begin make_packet(0,keys,1);exchange();end
    endtask
    task send_pick(input [127:0] keys,input integer column,input [7:0] velocity,input enabled);
        begin
            make_packet(2,keys,enabled);
            packet[31]=1<<column;packet[32+column]=velocity;exchange();
        end
    endtask
    task expect_count(input integer count);
        begin
            #10000;
            if(event_count!=count)$fatal(1,"Expected %0d events, got %0d",count,event_count);
        end
    endtask
    task send_snapshot_pick(input [127:0] live_keys,input [127:0] event_keys,input [7:0] velocity);
        begin
            make_packet(2,live_keys,1);
            packet[31]=1;packet[32]=velocity;packet[38]=8'hc1;
            for(integer byte_index=0;byte_index<16;byte_index=byte_index+1)
                packet[40+byte_index]=event_keys[byte_index*8+:8];
            exchange();
        end
    endtask
    task expect_pick(input integer string_number,input integer fret,input integer velocity);
        begin
            expected_events=expected_events+1;expect_count(expected_events);
            if(observed_string[expected_events-1]!=string_number||observed_fret[expected_events-1]!=fret||
               observed_velocity[expected_events-1]!=velocity)
                $fatal(1,"Wrong coupled event string=%0d fret=%0d velocity=%0d",
                    observed_string[expected_events-1],observed_fret[expected_events-1],observed_velocity[expected_events-1]);
        end
    endtask

    initial begin
        #200;reset_n=1;#5000;
        send_mode(2);
        if(TEST_INSTRUMENT!=0)begin
            make_packet(1,0,1);
            packet[24]=8'ha5;packet[25]=4;packet[26]=TEST_INSTRUMENT;packet[29]=8'ha5^4^TEST_INSTRUMENT;
            exchange();#10000;
        end
        if(ESP_WIRE_VECTORS)begin
            $readmemh("tests/results/esp_hall_wire_vectors.hex",esp_vectors);
            downstream_ready=0;
            for(integer transfer=0;transfer<10;transfer=transfer+1)begin
                for(integer byte_index=0;byte_index<64;byte_index=byte_index+1)
                    packet[byte_index]=esp_vectors[transfer*64+byte_index];
                sequence_number={packet[5],packet[4]};
                shift_packet();
            end
            expect_count(0);
            if(selected_frets[4:0]!=15)$fatal(1,"ESP wire vectors did not update live fret");
            downstream_ready=1;#100000;
            if(event_count!=3||observed_fret[0]!=4||observed_fret[1]!=8||observed_fret[2]!=12||
               observed_velocity[0]!=101||observed_velocity[1]!=102||observed_velocity[2]!=103)
                $fatal(1,"Actual ESP wire snapshots did not reach the correct FPGA notes");
            $display("PASS actual ESP C task -> raw SPI vectors/duplicate ACK requests -> FPGA backpressure -> frets 4/8/12, live fret 15");
            $finish;
        end
        if(AUDIT_BACKPRESSURE)begin
            downstream_ready=0;
            held_keys=0;held_keys[4*6]=1;send_pick(held_keys,0,101,1);
            held_keys=0;held_keys[8*6]=1;send_pick(held_keys,0,102,1);
            held_keys=0;held_keys[12*6]=1;send_pick(held_keys,0,103,1);
            expect_count(0);
            downstream_ready=1;#100000;
            if(event_count!=3)$fatal(1,"Backpressure lost events expected=3 actual=%0d",event_count);
            $display("AUDIT instrument=%0d buffered picks: velocities=%0d,%0d,%0d expected_frets=4,8,12 actual_frets=%0d,%0d,%0d",
                TEST_INSTRUMENT,observed_velocity[0],observed_velocity[1],observed_velocity[2],
                observed_fret[0],observed_fret[1],observed_fret[2]);
            if(observed_fret[0]!=4||observed_fret[1]!=8||observed_fret[2]!=12)
                $fatal(1,"BACKPRESSURE_SNAPSHOT: a queued Hall event used a later touch snapshot");
            if(observed_velocity[0]!=101||observed_velocity[1]!=102||observed_velocity[2]!=103)
                $fatal(1,"Backpressure changed event velocities");
            $display("PASS instrument=%0d buffered picks retain their own touch snapshots",TEST_INSTRUMENT);
            $finish;
        end
        held_keys[5*6]=1;send_keys(held_keys);expect_count(0);
        if(selected_frets[4:0]!=5)$fatal(1,"Touch-only fret selection failed");
        $display("PASS coupled touch only: fret 5 selected, no audio trigger");
        send_pick(held_keys,0,77,1);expect_pick(6,5,77);
        send_pick(held_keys,0,78,1);expect_pick(6,5,78);
        exchange();expect_count(expected_events);
        $display("PASS coupled held fret: repeated H1 picks work, duplicate SPI request does not retrigger");

        held_keys=0;held_keys[12*6]=1;
        send_pick(held_keys,0,79,1);expect_pick(6,12,79);
        $display("PASS coupled same frame: new fret 12 and H1 pick use new fret, not previous fret 5");
        held_keys=0;held_keys[2*6]=1;held_keys[8*6]=1;held_keys[20*6]=1;
        send_pick(held_keys,0,80,1);expect_pick(6,20,80);
        held_keys[20*6]=0;
        send_pick(held_keys,0,81,1);expect_pick(6,8,81);
        send_keys(0);expect_count(expected_events);
        send_pick(0,0,82,1);expect_pick(6,0,82);
        $display("PASS coupled selection: highest fret, release fallback and open string");

        held_keys=0;
        for(integer column=0;column<6;column=column+1)
            held_keys[(column==5?20:column+3)*6+column]=1;
        send_keys(held_keys);expect_count(expected_events);
        for(integer column=0;column<6;column=column+1)begin
            send_pick(held_keys,column,90+column,1);
            expect_pick(6-column,column==5?20:column+3,90+column);
        end
        $display("PASS coupled all six strings: independent fret selection, H1..H6 mapping and velocities");

        send_pick(held_keys,0,100,0);expect_count(expected_events);
        send_pick(held_keys,0,101,1);expect_pick(6,3,101);
        send_keys(0);send_mode(1);expect_count(expected_events);
        send_pick(0,0,102,1);expect_count(expected_events);
        send_mode(2);
        $display("PASS coupled mode gates: disabled controls and DIRECT reject Hall, re-enable restores picks");

        downstream_ready=0;held_keys=0;held_keys[7*6]=1;
        send_pick(held_keys,0,103,1);expect_count(expected_events);
        exchange();expect_count(expected_events);
        downstream_ready=1;expect_pick(6,7,103);
        $display("PASS coupled backpressure: one held event survives blocked ingress without duplicate");

        downstream_ready=0;
        send_snapshot_pick(128'd1<<54,128'd1<<24,104);
        send_snapshot_pick(128'd1<<54,128'd1<<48,105);
        send_snapshot_pick(128'd1<<54,128'd1<<72,106);
        send_keys(128'd1<<90);expect_count(expected_events);
        if(selected_frets[4:0]!=15)$fatal(1,"Live touch state frozen behind Hall snapshot");
        downstream_ready=1;#100000;
        if(event_count!=expected_events+3)$fatal(1,"Bound snapshots lost events");
        if(observed_fret[expected_events]!=4||observed_fret[expected_events+1]!=8||observed_fret[expected_events+2]!=12)
            $fatal(1,"Captured event snapshot changed during transport or backpressure");
        expected_events=expected_events+3;
        $display("PASS captured S3 event snapshots: frets 4/8/12 survive live fret 9/15 changes and backpressure");
        $display("PASS touch/Hall link: SPI -> touch selection + Hall event -> arbitration -> real note parser; events=%0d",event_count);
        $finish;
    end
    initial begin #50000000;$fatal(1,"Coupled touch/Hall test timeout");end
endmodule

module tb_touch_hall_backpressure;
    tb_touch_hall_link #(.AUDIT_BACKPRESSURE(1)) audit();
endmodule

module tb_touch_hall_piano_backpressure;
    tb_touch_hall_link #(.AUDIT_BACKPRESSURE(1),.TEST_INSTRUMENT(1)) audit();
endmodule

module tb_touch_hall_bass_backpressure;
    tb_touch_hall_link #(.AUDIT_BACKPRESSURE(1),.TEST_INSTRUMENT(2)) audit();
endmodule

module tb_touch_hall_violin_backpressure;
    tb_touch_hall_link #(.AUDIT_BACKPRESSURE(1),.TEST_INSTRUMENT(3)) audit();
endmodule

module tb_touch_hall_esp_vectors;
    tb_touch_hall_link #(.ESP_WIRE_VECTORS(1)) audit();
endmodule

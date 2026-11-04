`timescale 1ns/1ps
module tb_drum_sd_v7;
    reg clk=0;always #10 clk=~clk;
    reg rst_n=0,cancel=0,next_file=0,file_select=0;
    wire card_ready,card_valid,card_done,read_start;
    reg [7:0] card_error=0;
    wire [7:0] card_byte;
    wire [31:0] read_lba;
    wire load_begin,chunk_valid,load_commit,load_error,stage_valid;
    wire [7:0] stage_index,stage_data,error;
    wire [10:0] chunk_index,chunk_count;
    wire ready,initialized,fault,active_bank,active,finished;
    reg boundary=0,read_enable=0;
    reg [9:0] read_address=0;
    wire [31:0] read_data;
    integer selected_case=0,cycles=0,word_index;
    reg [31:0] expected[0:2047];
    piano_sd_boot #(.CLOCK_HZ(1000000),.KEEP_STAGE(0),.MULTI_FILE(1)) loader(
        .clk(clk),.rst_n(rst_n),.cancel(cancel),.memory_ready(1'b1),.next_file(next_file),.file_select(file_select),
        .card_ready(card_ready),.card_error(card_error),.card_byte(card_byte),.card_byte_valid(card_valid),
        .card_sector_done(card_done),.card_read_start(read_start),.card_read_lba(read_lba),
        .upload_begin(load_begin),.upload_valid(chunk_valid),.upload_commit(load_commit),.upload_error(load_error),
        .upload_index(chunk_index),.upload_data(),.upload_ready(file_select?ready:1'b1),
        .upload_count(file_select?chunk_count:11'd0),.bank_initialized(file_select&&initialized),.bank_fault(file_select&&fault),
        .active(active),.finished(finished),.error(error),.loading(),
        .stage_valid(stage_valid),.stage_index(stage_index),.stage_data(stage_data));
    drum_parameter_bank bank(.clk(clk),.rst_n(rst_n),.boundary(boundary),.read_enable(read_enable),
        .read_address(read_address),.read_data(read_data),.load_begin(load_begin&&file_select),
        .byte_valid(stage_valid&&file_select),.byte_data(stage_data),.chunk_valid(chunk_valid&&file_select),
        .chunk_index(chunk_index),.load_commit(load_commit&&file_select),.load_error(load_error&&file_select),
        .load_ready(ready),.chunk_count(chunk_count),.initialized(initialized),.fault(fault),.active_bank(active_bank));
    drum_sd_sector_model card(.clk(clk),.rst_n(rst_n),.start(read_start),.lba(read_lba),
        .ready(card_ready),.data(card_byte),.valid(card_valid),.done(card_done));
    task step;begin @(negedge clk);#1;cycles=cycles+1;if(cycles>1000000)$fatal(1,"SD test timeout");end endtask
    initial begin
        if($value$plusargs("CASE=%d",selected_case))begin end
        $readmemh("src/drums/rom/drum_bank.hex",expected);
        repeat(6)step();rst_n=1;
        while(!finished)step();
        if(error!=8'h33)$fatal(1,"expected independent piano size failure");
        file_select=1;next_file=1;step();next_file=0;
        while(!finished)begin
            if(selected_case==5&&loader.kind==3&&chunk_count==1)card_error=1;
            if(selected_case==6&&loader.kind==3&&chunk_count==1)cancel=1;
            read_enable=cycles%3!=0;read_address=cycles%768;
            step();
        end
        read_enable=0;
        if(selected_case==0)begin
            if(error||fault||!initialized||chunk_count!=12||active_bank)$fatal(1,"valid SD bank rejected");
            boundary=1;step();boundary=0;if(!active_bank)$fatal(1,"switch missing");
        end else if(error==0||initialized||active_bank)$fatal(1,"bad file accepted case=%0d",selected_case);
        for(word_index=0;word_index<768;word_index=word_index+1)begin
            read_enable=1;read_address=word_index;step();
            if(read_data!==expected[word_index])$fatal(1,"parameter word mismatch");
        end
        $display("PASS DRUM SD V7 case=%0d error=%h initialized=%b fallback=%b chunks=%0d",selected_case,error,initialized,!active_bank,chunk_count);
        $finish;
    end
endmodule

module drum_sd_sector_model(input wire clk,rst_n,start,input wire [31:0] lba,
    output reg ready=1,output reg [7:0] data=0,output reg valid=0,done=0);
    reg [31:0] addresses[0:799];reg [7:0] bytes[0:409599];
    integer selected_case=0,index=0,slot,entry_index;
    reg sending=0;
    initial begin
        if($value$plusargs("CASE=%d",selected_case))begin end
        $readmemh($sformatf("tests/runtime_temp/drum_sd%0d_lba.hex",selected_case),addresses);
        $readmemh($sformatf("tests/runtime_temp/drum_sd%0d_data.hex",selected_case),bytes);
    end
    always @(negedge clk)begin
        valid=0;done=0;
        if(!rst_n)begin ready=1;sending=0;index=0;end
        else if(start)begin
            if(sending)$fatal(1,"sector overlap");
            slot=-1;
            for(entry_index=0;entry_index<800;entry_index=entry_index+1)
                if(addresses[entry_index]==lba)slot=entry_index;
            if(slot<0)$fatal(1,"unknown sector %0d",lba);
            sending=1;index=0;ready=0;
        end else if(sending)begin
            if(index<512)begin data=bytes[slot*512+index];valid=1;index=index+1;end
            else begin done=1;ready=1;sending=0;end
        end
    end
endmodule

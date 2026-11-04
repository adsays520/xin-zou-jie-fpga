`timescale 1ns/1ps
module tb_drum_bank_v7;
    reg clk=0;always #10 clk=~clk;
    reg rst_n=0,boundary=0,read_enable=0;
    reg [9:0] read_address=0;
    wire [31:0] read_data;
    reg load_begin=0,byte_valid=0,chunk_valid=0,load_commit=0,load_error=0;
    reg [7:0] byte_data=0;
    reg [10:0] chunk_index=0;
    wire load_ready,initialized,fault,active_bank;
    wire [10:0] chunk_count;
    reg [31:0] expected[0:2047];
    reg [7:0] payload[0:3071];
    integer word_index,byte_index,timeout_count,case_index;
    drum_parameter_bank dut(.*);
    task step;begin @(negedge clk);#1;end endtask
    task reset;
        begin rst_n=0;read_enable=0;byte_valid=0;load_begin=0;load_commit=0;chunk_valid=0;
            repeat(3)step();rst_n=1;step();end
    endtask
    task check_default;
        begin
            if(active_bank)$fatal(1,"default bank not selected");
            for(word_index=0;word_index<768;word_index=word_index+1)begin
                read_enable=1;read_address=word_index;step();
                if(read_data!==expected[word_index])$fatal(1,"default word %0d",word_index);
            end
            read_enable=0;
        end
    endtask
    task upload;
        input integer bad_byte,limit;
        begin
            load_begin=1;step();load_begin=0;
            for(byte_index=0;byte_index<limit;byte_index=byte_index+1)begin
                byte_valid=1;byte_data=payload[byte_index]^(byte_index==bad_byte?8'h01:8'h00);
                step();byte_valid=0;
                if(byte_index%13==0)step();
                if(byte_index%256==255)begin
                    chunk_index=byte_index/256;chunk_valid=1;step();chunk_valid=0;
                    if(fault)$fatal(1,"valid chunk rejected %0d",byte_index);
                end
            end
        end
    endtask
    task finish_verify;
        begin
            load_commit=1;step();load_commit=0;timeout_count=0;
            while(!initialized&&!fault)begin
                read_enable=timeout_count%3!=0;read_address=timeout_count%768;
                step();timeout_count=timeout_count+1;
                if(timeout_count>20000)$fatal(1,"readback timeout");
            end
            read_enable=0;
        end
    endtask
    initial begin
        $readmemh("src/drums/rom/drum_bank.hex",expected);
        $readmemh("tests/runtime_temp/drums_bytes.hex",payload);
        reset();check_default();upload(-1,3072);finish_verify();
        if(fault||!initialized||active_bank)$fatal(1,"bad pre-switch state");
        repeat(3)step();boundary=1;step();boundary=0;
        if(!active_bank)$fatal(1,"no atomic switch");
        for(word_index=0;word_index<768;word_index=word_index+1)begin
            read_enable=1;read_address=word_index;step();
            if(read_data!==expected[word_index])$fatal(1,"loaded word %0d",word_index);
        end
        read_enable=0;
        reset();check_default();upload(771,3072);finish_verify();
        if(!fault||initialized||active_bank)$fatal(1,"bad CRC accepted");
        reset();check_default();upload(-1,3072);
        dut.memory[1024+555]=dut.memory[1024+555]^32'h01000000;
        finish_verify();if(!fault||initialized||active_bank)$fatal(1,"RAM corruption accepted");
        reset();check_default();upload(-1,256);finish_verify();
        if(!fault||initialized||active_bank)$fatal(1,"truncated bank accepted");
        reset();check_default();upload(7,123);reset();check_default();
        $display("PASS DRUM BANK V7: 768 default/loaded words, CRC, real RAM readback, atomic boundary, truncated transfer and reset fallback");
        $finish;
    end
endmodule

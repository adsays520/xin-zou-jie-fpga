`timescale 1ns/1ps
module tb_drum_sd_gate_v7;
    reg clk=0;always #10 clk=~clk;
    GSR GSR(.GSRI(1'b1));
    reg rst_n=0,tick=0,hit=0,panic=0;
    reg [3:0] voice=0;reg [1:0] kit=0;
    reg parameter_load_begin=0,parameter_byte_valid=0,parameter_chunk_valid=0;
    reg parameter_load_commit=0,parameter_load_error=0;
    reg [7:0] parameter_byte_data=0;reg [10:0] parameter_chunk_index=0;
    wire rtl_valid,gate_valid,rtl_deadline,gate_deadline,rtl_clipped,gate_clipped;
    wire rtl_ready,gate_ready,rtl_initialized,gate_initialized,rtl_fault,gate_fault,rtl_bank,gate_bank;
    wire [10:0] rtl_count,gate_count;
    wire signed [23:0] rtl_l,rtl_r,gate_l,gate_r;
    reg [7:0] bytes[0:3071];
    integer byte_index,kit_index,voice_index,frame_index,cycles,frames=0;
    drum_synth_rtl rtl(.clk(clk),.rst_n(rst_n),.sample_tick(tick),.panic(panic),
        .hit(hit),.hit_voice(voice),.hit_velocity(7'd110),.hit2(1'b0),.hit2_voice(4'd0),.hit2_velocity(7'd0),
        .kit(kit),.level_we(1'b0),.level_voice(4'd0),.level_value(7'd0),.sample_valid(rtl_valid),
        .sample_l(rtl_l),.sample_r(rtl_r),.deadline_miss(rtl_deadline),.clipped(rtl_clipped),
        .parameter_load_begin(parameter_load_begin),.parameter_byte_valid(parameter_byte_valid),
        .parameter_chunk_valid(parameter_chunk_valid),.parameter_load_commit(parameter_load_commit),
        .parameter_load_error(parameter_load_error),.parameter_byte_data(parameter_byte_data),.parameter_chunk_index(parameter_chunk_index),
        .parameter_load_ready(rtl_ready),.parameter_chunk_count(rtl_count),.parameter_initialized(rtl_initialized),
        .parameter_fault(rtl_fault),.parameter_active_bank(rtl_bank));
    drum_synth gate(.clk(clk),.rst_n(rst_n),.sample_tick(tick),.panic(panic),
        .hit(hit),.hit_voice(voice),.hit_velocity(7'd110),.hit2(1'b0),.hit2_voice(4'd0),.hit2_velocity(7'd0),
        .kit(kit),.level_we(1'b0),.level_voice(4'd0),.level_value(7'd0),.sample_valid(gate_valid),
        .sample_l(gate_l),.sample_r(gate_r),.deadline_miss(gate_deadline),.clipped(gate_clipped),
        .parameter_load_begin(parameter_load_begin),.parameter_byte_valid(parameter_byte_valid),
        .parameter_chunk_valid(parameter_chunk_valid),.parameter_load_commit(parameter_load_commit),
        .parameter_load_error(parameter_load_error),.parameter_byte_data(parameter_byte_data),.parameter_chunk_index(parameter_chunk_index),
        .parameter_load_ready(gate_ready),.parameter_chunk_count(gate_count),.parameter_initialized(gate_initialized),
        .parameter_fault(gate_fault),.parameter_active_bank(gate_bank));
    always @(negedge clk)if(rst_n)begin
        if({rtl_valid,rtl_deadline,rtl_clipped,rtl_l,rtl_r,rtl_ready,rtl_count,rtl_initialized,rtl_fault,rtl_bank} !==
           {gate_valid,gate_deadline,gate_clipped,gate_l,gate_r,gate_ready,gate_count,gate_initialized,gate_fault,gate_bank})
            $fatal(1,"SD gate mismatch kit=%0d voice=%0d frame=%0d initialized=%b/%b fault=%b/%b",kit,voice,frames,rtl_initialized,gate_initialized,rtl_fault,gate_fault);
    end
    task step;begin @(negedge clk);#1;end endtask
    task frame;
        begin
            tick=1;step();tick=0;cycles=0;
            while(!rtl_valid)begin step();cycles=cycles+1;if(cycles>1041)$fatal(1,"deadline");end
            repeat(4)step();frames=frames+1;
        end
    endtask
    task upload;
        input integer corrupt;
        begin
            parameter_load_begin=1;step();parameter_load_begin=0;
            for(byte_index=0;byte_index<3072;byte_index=byte_index+1)begin
                parameter_byte_valid=1;parameter_byte_data=bytes[byte_index]^(corrupt&&byte_index==777?8'd1:8'd0);
                step();parameter_byte_valid=0;
                if(byte_index%256==255)begin
                    parameter_chunk_index=byte_index/256;parameter_chunk_valid=1;step();parameter_chunk_valid=0;
                end
            end
            parameter_load_commit=1;step();parameter_load_commit=0;cycles=0;
            while(!rtl_initialized&&!rtl_fault)begin step();cycles=cycles+1;if(cycles>20000)$fatal(1,"RAM verification timeout");end
        end
    endtask
    initial begin
        $readmemh("tests/runtime_temp/drums_bytes.hex",bytes);
        force GSR.GSRI=0;repeat(5)step();force GSR.GSRI=1;repeat(5)step();rst_n=1;
        upload(0);if(!rtl_initialized||rtl_fault||rtl_bank)$fatal(1,"valid bank rejected");
        frame();if(!rtl_bank||!gate_bank)$fatal(1,"boundary not committed");
        for(kit_index=0;kit_index<3;kit_index=kit_index+1)begin
            kit=kit_index;
            for(voice_index=0;voice_index<12;voice_index=voice_index+1)begin
                panic=1;step();panic=0;voice=voice_index;hit=1;step();hit=0;
                for(frame_index=0;frame_index<(voice_index==0?192:32);frame_index=frame_index+1)frame();
            end
        end
        rst_n=0;repeat(5)step();rst_n=1;upload(1);
        if(!rtl_fault||rtl_initialized||rtl_bank||gate_bank)$fatal(1,"CRC fallback failed");
        voice=0;hit=1;step();hit=0;repeat(32)frame();
        $display("PASS DRUM SD GATE V7: frames=%0d actual Gowin RAM, loaded bank, readback CRC, sample boundary, corrupt-file fallback; every cycle identical",frames);
        $finish;
    end
endmodule

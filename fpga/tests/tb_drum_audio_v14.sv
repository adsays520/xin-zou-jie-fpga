`timescale 1ns/1ps
module tb_drum_audio_v14;
    reg clk=0;always #10 clk=~clk;
    reg rst_n=0,sample_tick=0,panic=0,hit=0,hit2=0,level_we=0;
    reg [3:0] hit_voice=0,hit2_voice=0,level_voice=0;
    reg [6:0] hit_velocity=110,hit2_velocity=91,level_value=100;
    reg [1:0] kit=0;
    wire valid,reference_valid,active,reference_active,deadline,clipped;
    wire reference_deadline,reference_clipped;
    wire signed [23:0] sample_l,sample_r,reference_l,reference_r;
    integer frames=0,kit_index,voice_index,frame_index,cycles,max_cycles=0;
    reg seen_dut,seen_reference;
    reg signed [23:0] captured_l,captured_r,captured_reference_l,captured_reference_r;
    drum_synth dut(.clk(clk),.rst_n(rst_n),.sample_tick(sample_tick),.panic(panic),
        .hit(hit),.hit_voice(hit_voice),.hit_velocity(hit_velocity),.hit2(hit2),
        .hit2_voice(hit2_voice),.hit2_velocity(hit2_velocity),.kit(kit),
        .level_we(level_we),.level_voice(level_voice),.level_value(level_value),
        .sample_valid(valid),.sample_l(sample_l),.sample_r(sample_r),.active(active),
        .deadline_miss(deadline),.clipped(clipped),.parameter_load_begin(1'b0),
        .parameter_byte_valid(1'b0),.parameter_chunk_valid(1'b0),.parameter_load_commit(1'b0),
        .parameter_load_error(1'b0),.parameter_byte_data(8'd0),.parameter_chunk_index(11'd0));
    drum_synth_v13_reference baseline(.clk(clk),.rst_n(rst_n),.sample_tick(sample_tick),.panic(panic),
        .hit(hit),.hit_voice(hit_voice),.hit_velocity(hit_velocity),.hit2(hit2),
        .hit2_voice(hit2_voice),.hit2_velocity(hit2_velocity),.kit(kit),
        .level_we(level_we),.level_voice(level_voice),.level_value(level_value),
        .sample_valid(reference_valid),.sample_l(reference_l),.sample_r(reference_r),
        .active(reference_active),.deadline_miss(reference_deadline),.clipped(reference_clipped),
        .parameter_load_begin(1'b0),.parameter_byte_valid(1'b0),.parameter_chunk_valid(1'b0),
        .parameter_load_commit(1'b0),.parameter_load_error(1'b0),.parameter_byte_data(8'd0),
        .parameter_chunk_index(11'd0));
    always @(negedge clk)if(rst_n&&dut.drum_parameter_enable&&dut.kick_parameter_enable)
        $fatal(1,"parameter port collision");
    longint signed expected,operand_wave,operand_gain;
    integer checked_state,math_checks=0;
    always @(posedge clk)if(rst_n&&!panic)begin
        checked_state=dut.state;
        operand_wave=$signed(dut.product_wave);
        operand_gain=$signed(dut.product_gain);
        expected=operand_wave*operand_gain;
        if(checked_state==5||checked_state==25||checked_state==28||
           checked_state==6||checked_state==7)begin
            if(checked_state!=5||dut.cymbal_voice)begin
                #1;
                if($signed(dut.product)!==expected)$fatal(1,"shared multiplier mismatch state=%0d",checked_state);
                math_checks=math_checks+1;
            end
        end
    end
    task step;begin @(negedge clk);#1;end endtask
    task strike;
        input integer selected_voice,selected_velocity;
        begin hit=1;hit_voice=selected_voice;hit_velocity=selected_velocity;step();hit=0;end
    endtask
    task frame;
        begin
            seen_dut=0;seen_reference=0;cycles=0;sample_tick=1;step();sample_tick=0;
            while(!seen_dut||!seen_reference)begin
                if(valid)begin seen_dut=1;captured_l=sample_l;captured_r=sample_r;end
                if(reference_valid)begin seen_reference=1;captured_reference_l=reference_l;captured_reference_r=reference_r;end
                step();cycles=cycles+1;
                if(cycles>=1041)$fatal(1,"sample deadline");
            end
            for(integer checked_voice=0;checked_voice<12;checked_voice=checked_voice+1)begin
                if(dut.body_env[checked_voice]!==baseline.body_env[checked_voice]||
                   dut.noise_env[checked_voice]!==baseline.noise_env[checked_voice]||
                   dut.pitch_env[checked_voice]!==baseline.pitch_env[checked_voice]||
                   dut.age[checked_voice]!==baseline.age[checked_voice]||
                   dut.rng[checked_voice]!==baseline.rng[checked_voice])
                    $fatal(1,"drum lifecycle changed voice=%0d frame=%0d",checked_voice,frames);
                if(checked_voice!=2&&checked_voice!=3&&checked_voice!=5&&checked_voice!=6)begin
                    if(dut.previous_voice[checked_voice]!==baseline.previous_voice[checked_voice]||
                       dut.low[checked_voice]!==baseline.low[checked_voice]||
                       dut.dc[checked_voice]!==baseline.dc[checked_voice])
                        $fatal(1,"non-cymbal synthesis changed voice=%0d frame=%0d",checked_voice,frames);
                end
            end
            if(dut.kick_sample!==baseline.kick_sample)$fatal(1,"kick resonator changed");
            if(deadline||clipped||reference_deadline||reference_clipped||active!==reference_active)
                $fatal(1,"audio state mismatch");
            if(cycles>max_cycles)max_cycles=cycles;
            frames=frames+1;repeat(4)step();
        end
    endtask
    task stop;begin panic=1;step();panic=0;frame();end endtask
    initial begin
        repeat(6)step();rst_n=1;
        for(kit_index=0;kit_index<3;kit_index=kit_index+1)begin
            kit=kit_index;
            for(voice_index=0;voice_index<12;voice_index=voice_index+1)begin
                stop();strike(voice_index,110);
                repeat((voice_index==2||voice_index==3||voice_index==5||voice_index==6)?2304:512)frame();
                strike(voice_index,37);repeat(128)frame();
            end
            stop();
            for(voice_index=0;voice_index<12;voice_index=voice_index+1)strike(voice_index,127);
            for(frame_index=0;frame_index<1024;frame_index=frame_index+1)begin
                if(frame_index%37==0)begin
                    hit=1;hit2=1;hit_voice=frame_index%12;hit2_voice=(frame_index+5)%12;step();hit=0;hit2=0;
                end
                frame();
            end
            stop();strike(3,127);repeat(100)frame();strike(2,127);repeat(64)frame();
            rst_n=0;repeat(4)step();rst_n=1;repeat(3)frame();
            $display("AUDIO V14 kit=%0d passed frames=%0d",kit,frames);$fflush();
        end
        $display("PASS DRUM AUDIO V14: frames=%0d, non-cymbal bit-exact synthesis, cymbal full morph, unchanged envelopes/RNG, dual hits, choke, reset, max_cycles=%0d",frames,max_cycles);
        $finish;
    end
endmodule



`timescale 1ns/1ps
module tb_drum_headroom_v14;
    reg clk=0;
    always #10 clk=~clk;
    reg rst_n=0,tick=0,panic=0,hit=0,hit2=0,level_we=0;
    reg [3:0] hit_voice=0,hit2_voice=0,level_voice=0;
    reg [6:0] hit_velocity=127,hit2_velocity=127,level_value=127;
    reg [1:0] kit=0;
    wire valid,active,deadline,clipped;
    wire signed [23:0] sample_l,sample_r;
    drum_synth dut(.clk(clk),.rst_n(rst_n),.sample_tick(tick),.panic(panic),
        .hit(hit),.hit_voice(hit_voice),.hit_velocity(hit_velocity),
        .hit2(hit2),.hit2_voice(hit2_voice),.hit2_velocity(hit2_velocity),.kit(kit),
        .level_we(level_we),.level_voice(level_voice),.level_value(level_value),
        .sample_valid(valid),.sample_l(sample_l),.sample_r(sample_r),
        .active(active),.deadline_miss(deadline),.clipped(clipped),
        .parameter_load_begin(1'b0),.parameter_byte_valid(1'b0),
        .parameter_chunk_valid(1'b0),.parameter_load_commit(1'b0),
        .parameter_load_error(1'b0),.parameter_byte_data(8'd0),.parameter_chunk_index(11'd0));
    integer output_file,kit_index,voice_index,frame_index,cycles,maximum_cycles=0;
    integer frames_per_voice=2048,frames_per_mix=4096;
    integer output_peak,raw_peak,minimum_gain,limited_frames,safety_frames;
    reg signed [31:0] raw_l,raw_r;
    longint signed wide;
    task step;
        begin @(negedge clk);#1;end
    endtask
    function integer magnitude;
        input integer value;
        begin magnitude=value<0?-value:value;end
    endfunction
    always @(negedge clk) if(rst_n&&!panic)begin
        if(dut.state==10)begin
            wide=$signed(dut.voice_sample);
            wide=wide*$signed({1'b0,dut.voice_level});
            if(wide>64'sd68719476735||wide< -64'sd68719476736)
                $fatal(1,"level product overflow");
        end
        if(dut.state==11)begin
            wide=$signed(dut.mix_l);
            wide=wide+((dut.voice==3||dut.voice==6||dut.voice==9)?
                           ($signed(dut.balanced_voice)>>>1):$signed(dut.balanced_voice));
            if(wide>64'sd2147483647||wide< -64'sd2147483648)
                $fatal(1,"mix accumulator overflow");
        end
        if(dut.state==12)begin raw_l=dut.mix_l;raw_r=dut.mix_r;end
    end
    task frame;
        begin
            tick=1;step();tick=0;cycles=1;
            while(!valid)begin
                step();cycles=cycles+1;
                if(cycles>=1041)$fatal(1,"sample deadline");
            end
            if(deadline||^sample_l===1'bx||^sample_r===1'bx)
                $fatal(1,"invalid output");
            if(cycles>maximum_cycles)maximum_cycles=cycles;
            if(magnitude(sample_l)>output_peak)output_peak=magnitude(sample_l);
            if(magnitude(sample_r)>output_peak)output_peak=magnitude(sample_r);
            if(magnitude(raw_l)>raw_peak)raw_peak=magnitude(raw_l);
            if(magnitude(raw_r)>raw_peak)raw_peak=magnitude(raw_r);
            if(dut.u_peak.gain<minimum_gain)minimum_gain=dut.u_peak.gain;
            if(dut.u_peak.gain<32768)limited_frames=limited_frames+1;
            if(dut.peak_safety)safety_frames=safety_frames+1;
            $fwrite(output_file,"%0d %0d %0d %0d %0d %0d %0d %0d\n",kit,voice_index,
                frame_index,raw_l,raw_r,sample_l,sample_r,dut.u_peak.gain);
            repeat(3)step();
        end
    endtask
    task strike;
        input integer selected;
        begin hit=1;hit_voice=selected;step();hit=0;end
    endtask
    task begin_case;
        begin
            panic=1;step();panic=0;
            output_peak=0;raw_peak=0;minimum_gain=32768;limited_frames=0;safety_frames=0;
        end
    endtask
    task report;
        begin
            $display("DRUM k=%0d v=%0d raw_peak=%0d out_peak=%0d min_gain=%0d limited=%0d safety=%0d sticky=%0d",
                kit,voice_index,raw_peak,output_peak,minimum_gain,limited_frames,safety_frames,clipped);
            $fflush();
        end
    endtask
    initial begin
        if($value$plusargs("FRAMES=%d",frames_per_voice))begin end
        if($value$plusargs("MIX_FRAMES=%d",frames_per_mix))begin end
        output_file=$fopen("tests/results/drum_headroom_v14.txt","w");
        repeat(5)step();rst_n=1;
        for(voice_index=0;voice_index<12;voice_index=voice_index+1)begin
            level_voice=voice_index;level_we=1;step();level_we=0;step();
        end
        for(kit_index=0;kit_index<3;kit_index=kit_index+1)begin
            kit=kit_index;
            for(voice_index=0;voice_index<12;voice_index=voice_index+1)begin
                begin_case();strike(voice_index);
                for(frame_index=0;frame_index<frames_per_voice;frame_index=frame_index+1)frame();
                report();
            end
            voice_index=12;begin_case();
            for(frame_index=0;frame_index<frames_per_mix;frame_index=frame_index+1)begin
                if(frame_index%37==0)begin
                    strike(0);strike(1);strike(3);strike(2);strike(4);strike(5);
                    strike(6);strike(7);strike(8);strike(9);strike(10);strike(11);
                end
                frame();
            end
            report();
        end
        $fclose(output_file);
        $display("PASS DRUM HEADROOM V14 max_cycles=%0d",maximum_cycles);
        $finish;
    end
endmodule

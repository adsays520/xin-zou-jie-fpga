`timescale 1ns/1ps
module tb_drum_routing_v6;
    reg clk=0;
    always #10 clk=~clk;
    reg rst_n=0,sample_tick=0,panic=0,hit=0,hit2=0,level_we=0;
    reg [3:0] hit_voice=0,hit2_voice=0,level_voice=0;
    reg [6:0] hit_velocity=0,hit2_velocity=0,level_value=100;
    reg [1:0] kit=0;
    wire sample_valid,active,deadline_miss,clipped;
    wire reference_valid,reference_active,reference_deadline,reference_clipped;
    wire signed [23:0] sample_l,sample_r,reference_l,reference_r;
    integer cycles=0,frames=0,voice_index,kit_index,frame_index;
    integer frame_cycles=0,max_frame_cycles=0;
    integer reset_count=0,panic_count=0;
    reg [31:0] random_state=32'h6a43e123;
    drum_synth dut(.*);
    drum_synth_v4_reference baseline(
        .clk(clk),.rst_n(rst_n),.sample_tick(sample_tick),.panic(panic),
        .hit(hit),.hit_voice(hit_voice),.hit_velocity(hit_velocity),
        .hit2(hit2),.hit2_voice(hit2_voice),.hit2_velocity(hit2_velocity),
        .kit(kit),.level_we(level_we),.level_voice(level_voice),.level_value(level_value),
        .sample_valid(reference_valid),.sample_l(reference_l),.sample_r(reference_r),
        .active(reference_active),.deadline_miss(reference_deadline),.clipped(reference_clipped));
    always @(negedge clk)begin
        cycles=cycles+1;
        if(cycles>5)begin
            if({sample_valid,active,deadline_miss,clipped,sample_l,sample_r} !==
               {reference_valid,reference_active,reference_deadline,reference_clipped,reference_l,reference_r})
                $fatal(1,"cycle mismatch cycle=%0d kit=%0d state=%0d voice=%0d",cycles,kit,dut.state,dut.voice);
            if(dut.state!==baseline.state||dut.voice!==baseline.voice||dut.osc!==baseline.osc)
                $fatal(1,"schedule changed cycle=%0d",cycles);
            if(rst_n&&dut.state==16&&dut.phase_read_reg!==baseline.phase_read_reg)
                $fatal(1,"phase mismatch cycle=%0d",cycles);
            if(rst_n&&dut.state==4&&dut.square_term!==baseline.square_term)
                $fatal(1,"square mismatch cycle=%0d",cycles);
        end
    end
    task step;
        begin @(negedge clk);#1;end
    endtask
    task strike;
        input integer selected_voice,selected_velocity;
        begin
            hit_voice=selected_voice;hit_velocity=selected_velocity;hit=1;
            step();hit=0;
        end
    endtask
    task frame;
        begin
            sample_tick=1;step();sample_tick=0;frame_cycles=1;
            while(!sample_valid)begin
                step();frame_cycles=frame_cycles+1;
                if(frame_cycles>=1041)$fatal(1,"deadline exceeded");
            end
            if(deadline_miss||clipped||^sample_l===1'bx||^sample_r===1'bx)
                $fatal(1,"invalid PCM");
            frames=frames+1;
            if(frame_cycles>max_frame_cycles)max_frame_cycles=frame_cycles;
            repeat(4)step();
        end
    endtask
    task stop;
        begin panic=1;step();panic=0;panic_count=panic_count+1;frame();end
    endtask
    initial begin
        repeat(6)step();rst_n=1;
        repeat(8)frame();
        for(kit_index=0;kit_index<3;kit_index=kit_index+1)begin
            kit=kit_index;
            for(voice_index=0;voice_index<12;voice_index=voice_index+1)begin
                stop();strike(voice_index,110);
                repeat(512)frame();
                strike(voice_index,47);
                repeat(128)frame();
            end
            stop();
            for(voice_index=0;voice_index<12;voice_index=voice_index+1)strike(voice_index,127);
            for(frame_index=0;frame_index<2048;frame_index=frame_index+1)begin
                random_state={random_state[30:0],random_state[31]^random_state[21]^random_state[1]^random_state[0]};
                if(frame_index%29==0)begin
                    hit=1;hit2=1;hit_voice=random_state[3:0]%12;
                    hit2_voice=random_state[7:4]%12;hit_velocity=1+random_state[14:8]%127;
                    hit2_velocity=1+random_state[21:15]%127;
                    step();hit=0;hit2=0;
                end
                if(frame_index%43==0)begin
                    level_we=1;level_voice=random_state[3:0]%12;level_value=random_state[14:8];
                    step();level_we=0;
                end
                frame();
            end
            for(frame_index=0;frame_index<26;frame_index=frame_index+1)begin
                strike(2,110);sample_tick=1;step();sample_tick=0;
                repeat(frame_index*3+1)step();
                if(frame_index%2==0)begin
                    rst_n=0;repeat(3)step();rst_n=1;reset_count=reset_count+1;
                end else begin panic=1;step();panic=0;panic_count=panic_count+1;end
                repeat(2)frame();strike(3,110);repeat(3)frame();
            end
        end
        stop();strike(3,127);repeat(100)frame();strike(2,127);repeat(64)frame();stop();
        if(frames<29000||reset_count!=39||panic_count<70)$fatal(1,"insufficient coverage");
        $display("PASS DRUM ROUTING V6: cycles=%0d PCM_frames=%0d max_cycles=%0d resets=%0d panics=%0d",
                 cycles,frames,max_frame_cycles,reset_count,panic_count);
        $finish;
    end
endmodule

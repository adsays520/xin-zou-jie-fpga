`timescale 1ns/1ps
module tb_drum_morph_v14;
    reg clk=0;
    always #10 clk=~clk;
    reg rst_n=0;
    reg [4:0] control_state=0;
    reg [3:0] control_voice=2;
    reg [16:0] control_age=0;
    reg signed [19:0] control_lp=0,control_hp=0,control_exciter=0,control_tone=0,control_metal=0;
    reg [31:0] control_random=32'h12345678;
    integer voice_index,age_index,seed=975312,checks=0;
    longint signed source,target,tail,band,bright,expected,expected_body,expected_exciter;
    integer segment,fraction,metal_fraction,body_fraction;
    wire valid;
    drum_synth dut(.clk(clk),.rst_n(rst_n),.sample_tick(1'b0),.panic(1'b0),
        .hit(1'b0),.hit_voice(4'd0),.hit_velocity(7'd0),
        .hit2(1'b0),.hit2_voice(4'd0),.hit2_velocity(7'd0),.kit(2'd0),
        .level_we(1'b0),.level_voice(4'd0),.level_value(7'd0),.sample_valid(valid),
        .parameter_load_begin(1'b0),.parameter_byte_valid(1'b0),.parameter_chunk_valid(1'b0),
        .parameter_load_commit(1'b0),.parameter_load_error(1'b0),
        .parameter_byte_data(8'd0),.parameter_chunk_index(11'd0));
    task step;
        input integer selected_state;
        begin control_state=selected_state;@(negedge clk);#1;end
    endtask
    initial begin
        repeat(4)@(negedge clk);
        force dut.state=control_state;
        force dut.voice=control_voice;
        force dut.voice_age=control_age;
        force dut.lp=control_lp;
        force dut.hp=control_hp;
        force dut.noise_exciter=control_exciter;
        force dut.tone_sum=control_tone;
        force dut.metal_sum=control_metal;
        force dut.random=control_random;
        rst_n=1;
        for(voice_index=0;voice_index<4;voice_index=voice_index+1)begin
            case(voice_index)
                0:control_voice=2;
                1:control_voice=3;
                2:control_voice=5;
                3:control_voice=6;
            endcase
            for(age_index=0;age_index<=4096;age_index=age_index+1)begin
                control_age=age_index;
                control_lp=$signed($random(seed))%65536;
                control_hp=$signed($random(seed))%65536;
                control_exciter=$signed($random(seed))%65536;
                control_tone=$signed($random(seed))%65536;
                control_metal=$signed($random(seed))%49153;
                band=$signed(control_lp);band=band-$signed(control_hp);
                bright=$signed(control_exciter);bright=bright-$signed(control_lp);
                tail=control_voice==5?bright+(band>>>1):bright;
                segment=age_index/512;fraction=age_index%512;
                case(segment)
                    0:begin source=$signed(control_hp)+($signed(control_lp)>>>1);target=$signed(control_lp);end
                    1:begin source=$signed(control_lp);target=band;end
                    2:begin source=band;target=(band+bright)>>>1;end
                    3:begin source=(band+bright)>>>1;target=tail;end
                    default:begin source=tail;target=tail;end
                endcase
                expected=source+(((target-source)*fraction)>>>9);
                body_fraction=age_index<1024?0:age_index<2048?age_index-1024:1024;
                expected_body=$signed(control_tone);
                expected_body=(expected_body*body_fraction)>>>((control_voice==5)?16:15);
                step(15);step(25);step(26);
                if($signed(dut.wave_n)!==expected)
                    $fatal(1,"morph mismatch voice=%0d age=%0d got=%0d expected=%0d",control_voice,age_index,$signed(dut.wave_n),expected);
                if(control_voice==5||control_voice==6)begin
                    step(28);step(29);
                    if($signed(dut.wave_b)!==expected_body)$fatal(1,"body morph mismatch");
                end
                metal_fraction=age_index<2048?age_index:2048;
                expected_exciter=$signed(control_metal);
                expected_exciter=(expected_exciter*metal_fraction)>>>12;
                step(5);
                if(($signed(dut.product)>>>12)!==expected_exciter)$fatal(1,"metal morph mismatch");
                if(age_index>=2048&&expected!==tail)$fatal(1,"tail endpoint changed");
                checks=checks+1;
            end
        end
        $display("PASS DRUM MORPH V14: %0d signed interpolation cases, all transition boundaries and steady tails",checks);
        $finish;
    end
endmodule

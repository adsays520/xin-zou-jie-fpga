`timescale 1ns/1ps
module bass_top_tb;
    reg clk=0,rst=1,rx=1;
    GSR GSR(.GSRI(1'b1));
    always #10 clk=~clk;
    guitar_audio_top dut(.clk(clk),.rst(rst),.uart_rx_i(rx),.key_next_n(1'b1),.key_pluck_n(1'b1));
    integer bass_pcm_frames=0,combined_frames=0,pitch_pcm_frames=0,fractional_frames=0;
    always @(posedge clk)
        if(dut.sample_tick&&dut.timbre_bass&&dut.frame_audio_word_l!=0)
            bass_pcm_frames=bass_pcm_frames+1;
    always @(posedge clk)
        if(dut.sample_tick&&dut.bass_active&&dut.drum_active&&dut.frame_audio_word_l!=0)
            combined_frames=combined_frames+1;
    always @(posedge clk)begin
      if(dut.sample_tick&&dut.pitch_enabled&&dut.frame_audio_word_l!=0)pitch_pcm_frames=pitch_pcm_frames+1;
      if(dut.u_poly32.u_core.sample_valid&&dut.pitch_enabled&&dut.u_poly32.u_core.active&&dut.u_poly32.u_core.pitch_fraction!=0)
        fractional_frames=fractional_frames+1;
    end
    task byte_tx;
        input [7:0] value;
        integer b;
        begin
            @(negedge clk);rx=0;repeat(434)@(negedge clk);
            for(b=0;b<8;b=b+1)begin rx=value[b];repeat(434)@(negedge clk);end
            rx=1;repeat(450)@(negedge clk);
        end
    endtask
    task frame_tx;
        input [7:0] cmd,p0,p1,p2;
        begin byte_tx(8'ha5);byte_tx(cmd);byte_tx(p0);byte_tx(p1);byte_tx(p2);byte_tx(8'ha5^cmd^p0^p1^p2);end
    endtask
    initial begin
        repeat(30)@(negedge clk);rst=0;repeat(10000)@(negedge clk);
        frame_tx(4,2,0,0);
        if(!dut.timbre_bass||dut.timbre_piano)$fatal(1,"Bass top selection failed");
        frame_tx(2,6,0,100);repeat(500000)@(negedge clk);
        if(!dut.bass_active||dut.voice_bank_active||dut.piano_active)$fatal(1,"Bass source not exclusive");
        if(bass_pcm_frames<100)$fatal(1,"Bass did not reach final PCM output");
        if(dut.bass_deadline_miss)$fatal(1,"Bass top deadline miss");
        frame_tx(8'h50,0,127,0);repeat(80000)@(negedge clk);
        if(!dut.drum_active||!dut.bass_active||combined_frames<40)
            $fatal(1,"Acoustic drums and Bass did not mix concurrently");
        if(dut.drum_deadline_miss||dut.drum_clipped)
            $fatal(1,"Acoustic drum deadline/clipping failure");
        frame_tx(4,1,0,0);repeat(10000)@(negedge clk);
        if(dut.bass_active||dut.timbre_bass||!dut.timbre_piano)$fatal(1,"Bass tail not cleared on piano switch");
        if(!dut.drum_active)$fatal(1,"Instrument switch cleared independent acoustic drum tail");
        frame_tx(5,60,100,1);repeat(60000)@(negedge clk);
        if(!dut.piano_active||dut.bass_active||dut.voice_bank_active)$fatal(1,"Original piano path failed");
        frame_tx(4,0,0,0);frame_tx(2,6,0,100);repeat(60000)@(negedge clk);
        if(!dut.voice_bank_active||dut.bass_active||dut.piano_active)$fatal(1,"Original guitar path failed");
        frame_tx(8'h90,8'h11,8'hf5,8'h9b); // 1176987 Q20, +2 semitones
        frame_tx(8'h91,1,0,0);repeat(220000)@(negedge clk);
        if(!dut.pitch_enabled||dut.pitch_ratio_q20!=1176987)$fatal(1,"Pitch UART control not active");
        if(pitch_pcm_frames<40||fractional_frames<40)$fatal(1,"Pitch not reaching live voice/PCM");
        if(dut.poly_deadline_miss)$fatal(1,"Pitch exceeded the existing 32-voice slot budget");
        frame_tx(8'h91,0,0,0);
        frame_tx(8'h52,0,0,0);repeat(10000)@(negedge clk);
        if(dut.drum_active||!dut.voice_bank_active)$fatal(1,"Drum stop affected guitar");
        $display("PASS TOP: UART Bass -> FX bypass -> mixer -> final PCM (%0d nonzero frames); concurrent acoustic drums (%0d frames), independent tails/stop, guitar/piano restored",bass_pcm_frames,combined_frames);
        $display("PASS PITCH TOP: real UART -> per-voice fractional rate -> final PCM (%0d frames), saved fraction (%0d samples), no deadline miss",pitch_pcm_frames,fractional_frames);
        $finish;
    end
endmodule

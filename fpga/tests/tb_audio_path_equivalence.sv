`timescale 1ns/1ps
// Compare original and enhanced production output paths with identical source
// words. Sound engines are separately checked; no DDS test is enabled here.
module tb_audio_path_equivalence;
    reg clk=0;always #10 clk=~clk;
    reg rst=1;
    wire old_bck,old_ws,old_din,new_bck,new_ws,new_din;
    guitar_audio_top_original original(.clk(clk),.rst(rst),.key_next_n(1'b1),.key_pluck_n(1'b1),
        .uart_rx_i(1'b1),.HP_BCK(old_bck),.HP_WS(old_ws),.HP_DIN(old_din));
    guitar_audio_top enhanced(.clk(clk),.rst(rst),.key_next_n(1'b1),.key_pluck_n(1'b1),
        .uart_rx_i(1'b1),.HP_BCK(new_bck),.HP_WS(new_ws),.HP_DIN(new_din));
    reg signed [23:0] src_l=0,src_r=0,drum_l=0,drum_r=0;
    integer n=0,nonzero=0;reg observe=0,request=0;
    task page_tap(input [1:0] expected_page);
        begin
            @(negedge clk);force enhanced.next_pressed=1;
            @(negedge clk);force enhanced.next_pressed=0;
            repeat(3)@(negedge clk);
            if(enhanced.screen_page!==expected_page)$fatal(1,"page cycle failed");
            release enhanced.next_pressed;
        end
    endtask
    initial begin
        force GSR.GSRI=0;
        force original.instrument_source_l=src_l;force enhanced.instrument_source_l=src_l;
        force original.instrument_source_r=src_r;force enhanced.instrument_source_r=src_r;
        force original.drum_hold_l=drum_l;force enhanced.drum_hold_l=drum_l;
        force original.drum_hold_r=drum_r;force enhanced.drum_hold_r=drum_r;
        force enhanced.verification_visual_enable=observe;
        force enhanced.verification_capture_request=request;
        repeat(8)@(negedge clk);rst=0;force GSR.GSRI=1;
        repeat(4)@(negedge clk);
        if(enhanced.u_status_screen.page!==3 || enhanced.screen_page!==0)$fatal(1,"automatic startup plot absent");
        page_tap(1);page_tap(2);page_tap(0);
        if(enhanced.screen_selected_bus!==0)$fatal(1,"page tap altered bus selection");
        for(n=0;n<128;n=n+1)begin
            // Include asymmetric channels, extremes, alternating transients,
            // source+drum mixing and simultaneous observer capture traffic.
            src_l=n[0] ? 24'sh700000 : -24'sh700000;
            src_r=n[1] ? 24'sh200000 : -24'sh200000;
            drum_l=n[2] ? 24'sh300000 : 24'sh010000;
            drum_r=-drum_l;observe=n[4];request=n==8 || n==40;
            @(posedge clk);while(!enhanced.sample_tick)@(posedge clk);
            @(negedge clk);
            if(enhanced.audio_word_l!=0 || enhanced.audio_word_r!=0)nonzero=nonzero+1;
        end
        if(nonzero<64)$fatal(1,"insufficient nonzero audio comparison");
        $display("PASS original vs enhanced: 128 stereo frames, active mixer/effects, observer off/on/capture; final S16 and I2S pins bit-exact; automatic startup and page cycle 0/1/2/0 independent of monitoring");
        $finish;
    end
    always @(negedge clk)if(!rst)begin
        if({old_bck,old_ws,old_din}!=={new_bck,new_ws,new_din})$fatal(1,"I2S changed at frame %0d",n);
        if({original.audio_word_l,original.audio_word_r}!=={enhanced.audio_word_l,enhanced.audio_word_r})
            $fatal(1,"audio words changed at frame %0d old=%h/%h new=%h/%h",n,original.audio_word_l,original.audio_word_r,enhanced.audio_word_l,enhanced.audio_word_r);
    end
    initial begin #10000000;$fatal(1,"timeout");end
endmodule

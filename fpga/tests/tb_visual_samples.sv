`timescale 1ns/1ps
module tb_visual_samples;
 GSR GSR(.GSRI(1'b1));
    reg clk=0;always #10 clk=~clk;
    reg rst_n=0,tick=0;
    reg signed [15:0] l=0,r=0;
    reg [7:0] x=0,y=0;reg [1:0] page=2;
    wire [15:0] rgb;wire [5:0] leds;
    verification_visuals dut(clk,rst_n,tick,l,r,page,x,y,rgb,leds);
    integer i;
    task check_clear;
        begin
            for(i=0;i<16384;i=i+1)begin
                @(negedge clk);x=i%128;y=24+i/128;
                repeat(2)@(negedge clk);
                if(dut.xy_word[0]!==0)$fatal(1,"RAM clear failed %0d",i);
            end
        end
    endtask
    task sample(input signed [15:0] a,b);
        begin
            @(negedge clk);l=a;r=b;tick=1;
            @(negedge clk);tick=0;l=0;r=0;
            repeat(100)@(negedge clk);
        end
    endtask
    initial begin
        force GSR.GSRI=1'b0;
        repeat(4)@(negedge clk);rst_n=1;
        force GSR.GSRI=1'b1;
        repeat(16386)@(negedge clk);check_clear;
        repeat(4)sample(16'sd8192,-16'sd16384);
        // L maps to x=80, R to y=29; the XY panel begins at y=120.
        @(negedge clk);x=80;y=119;repeat(2)@(negedge clk);
        if(rgb!==16'hf81f)$fatal(1,"latched stereo XY pixel incorrect");
        page=0;x=0;y=79;repeat(2)@(negedge clk);
        if(rgb!==16'h07ff)$fatal(1,"continuous left waveform incorrect rgb=%h trace=%h mapped=%0d,%0d",rgb,dut.trace_word,dut.mapped_l,dut.mapped_r);
        y=109;repeat(2)@(negedge clk);
        if(rgb!==16'hfd20)$fatal(1,"continuous right waveform incorrect");
        if(leds!==6'b100000)$fatal(1,"sample-derived LED meter incorrect %b",leds);
        // Narrow spectral lines occupy two columns; intervening pixels remain empty.
        page=1;dut.bars[0]=127;x=3;y=80;repeat(2)@(negedge clk);
        if(rgb!==16'h07e0)$fatal(1,"spectral line absent");
        x=6;repeat(2)@(negedge clk);
        if(rgb===16'h07e0)$fatal(1,"spectrum is a filled bar instead of a line");
        // Trigger one full memory clear through the real age state transition.
        @(negedge clk);dut.xy_age=1023;
        page=2;repeat(4)sample(-16'sd8192,16'sd16384);
        repeat(16386)@(negedge clk);check_clear;
        $display("PASS captured stereo waveform lines, XY, LEDs, narrow spectral peaks; both clears cover all 16384 RAM pixels");
        $finish;
    end
    initial begin #10000000;$fatal(1,"timeout");end
endmodule

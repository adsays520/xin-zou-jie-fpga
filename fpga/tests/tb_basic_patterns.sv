`timescale 1ns/1ps
module tb_basic_patterns;
    GSR GSR(.GSRI(1'b1));
    reg clk=0;always #10 clk=~clk;
    reg rst_n=0,tick=0,bv=0;reg [7:0] byte_data=0;
    wire playing,ready,valid,deadline,clipped;wire [5:0] step;
    // Only the tempo counter is accelerated 100x. The synth still has a real
    // 50 MHz / 48 kHz sample schedule; this checks upload -> scanner -> hits.
    drum_machine #(.SAMPLE_RATE(480)) dut(.clk(clk),.rst_n(rst_n),.sample_tick(tick),
        .byte_valid(bv),.byte_data(byte_data),.playing(playing),.pattern_ready(ready),
        .current_step(step),.sample_valid(valid),.deadline_miss(deadline),.clipped(clipped));
    reg [7:0] stream[0:23579];reg [6:0] expected[0:3839];integer counts[0:767];
    integer p,i,address,steps_done=0,hits=0,period=0;
    always @(negedge clk)begin
        if(!rst_n)begin period=0;tick=0;end
        else begin tick=(period==0);period=(period==1041)?0:period+1;end
    end
    always @(posedge clk)if(rst_n && dut.seq_hit)begin
        address=dut.seq_voice*64+dut.scan_step;
        if(expected[p*768+address]!==dut.seq_velocity)$fatal(1,"pattern hit mismatch preset=%0d addr=%0d",p,address);
        counts[address]=counts[address]+1;hits=hits+1;
    end
    initial begin
        force GSR.GSRI=0;repeat(4)@(negedge clk);force GSR.GSRI=1;
        $readmemh("tests/results/basic_patterns_frames.hex",stream);
        $readmemh("tests/results/basic_patterns_cells.hex",expected);
        for(p=0;p<5;p=p+1)begin
            rst_n=0;repeat(4)@(negedge clk);rst_n=1;
            for(i=0;i<768;i=i+1)counts[i]=0;
            // 785 upload frames + explicit start frame, each six bytes.
            for(i=0;i<4716;i=i+1)begin
                @(negedge clk);byte_data=stream[p*4716+i];bv=1;
                @(negedge clk);bv=0;
            end
            repeat(40)@(negedge clk);
            if(!ready || !playing)$fatal(1,"host preset did not start");
            while(step!=63)@(negedge clk);
            repeat(40)@(negedge clk);
            for(i=0;i<768;i=i+1)
                if(counts[i]!=(expected[p*768+i]!=0))$fatal(1,"missing/duplicate beat preset=%0d addr=%0d count=%0d",p,i,counts[i]);
            if(deadline || clipped)$fatal(1,"deadline or clipping in basic groove");
            $display("PASS uploaded basic preset=%0d: all 64 steps and 12 tracks match",p);
        end
        $display("PASS five host presets -> XOR UART upload -> FPGA step scanner, %0d actual synth hits",hits);$finish;
    end
    initial begin #500000000;$fatal(1,"timeout");end
endmodule

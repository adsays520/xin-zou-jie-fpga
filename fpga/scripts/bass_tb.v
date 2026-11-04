`timescale 1ns/1ps
module bass_tb;
    reg clk=0,rst_n=0,tick=0,note=0,poly=1;
    reg [2:0] string_sel=5;
    reg [4:0] fret=0;
    reg [6:0] velocity=127;
    wire valid,active,deadline;
    wire signed [23:0] audio;
    bass_poly8 dut(clk,rst_n,tick,note,poly,string_sel,fret,velocity,valid,audio,active,deadline);
    integer output_file,frames=0,valid_count=0,max_clocks=0,clocks=0;
    integer scenario=0;
    reg started=0;
    task cycle;
        begin #10;clk=1;#10;clk=0;end
    endtask
    task pluck;
        input [2:0] s;
        input [4:0] f;
        begin
            string_sel=s;fret=f;
            repeat(4)cycle();
            note=1;cycle();note=0;repeat(4)cycle();
        end
    endtask
    task frame;
        begin
            tick=1;started=1;clocks=0;cycle();tick=0;
            repeat(199)cycle();
            // No state can change in the idle part: event/tick=0 and bus done.
            // Skip idle clock edges but retain the real 1041-clock timestamp.
            #16820;
            frames=frames+1;
        end
    endtask
    always @(posedge clk) if(started)begin
        clocks=clocks+1;
        if(valid)begin
            valid_count=valid_count+1;
            if(clocks>max_clocks)max_clocks=clocks;
            if(^audio===1'bx)$fatal(1,"Unknown sample");
            if(audio>7000000||audio< -7000000)$fatal(1,"Overflow");
            if(output_file)$fdisplay(output_file,"%d",audio);
        end
    end
    initial begin
        if(!$value$plusargs("SCENARIO=%d",scenario))scenario=0;
        output_file=$fopen($sformatf("verification/bass_rtl_%0d.txt",scenario),"w");
        repeat(10)cycle();rst_n=1;
        repeat(4)cycle();
        repeat(100)frame();
        if(active||audio!=0)$fatal(1,"Power-up not silent");
        // FPGA guard, even for an invalid raw UART caller.
        pluck(0,0);repeat(10)frame();
        if(active||audio!=0)$fatal(1,"Upper-string guard failed");
        if(scenario==0)begin
            pluck(5,0);repeat(130000)frame();
        end else if(scenario==1)begin
            pluck(5,0);frame();pluck(4,0);frame();pluck(3,0);frame();pluck(2,0);
            repeat(130000)frame();
        end else if(scenario==2)begin
            repeat(100)begin pluck(5,20);repeat(400)frame();end
            repeat(130000)frame();
        end else if(scenario==3)begin
            poly=0;
            repeat(20)begin pluck(5,0);repeat(800)frame();pluck(2,20);repeat(800)frame();end
            repeat(130000)frame();
        end else if(scenario==4)begin
            pluck(2,20);repeat(130000)frame();
        end
        repeat(100)frame();
        if(active||audio!=0)$fatal(1,"Tail did not become exact silence");
        if(deadline)$fatal(1,"Deadline miss");
        if(valid_count!=frames)$fatal(1,"Missing frame: %d vs %d",valid_count,frames);
        $fclose(output_file);
        $display("PASS scenario=%0d frames=%0d maximum_latency=%0d silence=0",scenario,frames,max_clocks);
        $finish;
    end
endmodule

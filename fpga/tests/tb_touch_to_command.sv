`timescale 1ns/1ps
module tb_touch_to_command;
    reg clk=0;always #10 clk=~clk;
    reg rst_n=0,enabled=1;reg [127:0]keys=0;reg[1:0]instrument=0;
    reg ready=1;wire valid;wire[47:0]data;
    reg hall_mode=0,hall_valid=0;reg[5:0]hall_mask=0;reg[47:0]hall_velocity=0;
    wire hall_ready;wire[29:0]frets;
    reg [29:0] hall_frets=0;
    integer count=0;reg[47:0]last;
    reg[47:0]events[0:127];
    touch_to_command #(.PIANO_GATE_CLKS(100000)) dut(.clk(clk),.rst_n(rst_n),.enabled(enabled),.keys(keys),.instrument(instrument),
        .hall_mode(hall_mode),.hall_mask(hall_mask),.hall_velocity(hall_velocity),.hall_frets(hall_frets),.hall_valid(hall_valid),.hall_ready(hall_ready),
        .selected_frets(frets),
        .command_data(data),.command_valid(valid),.command_ready(ready));
    always @(posedge clk)if(valid&&ready)begin count<=count+1;last<=data;events[count]<=data;end
    task pick(input integer col,input [7:0]velocity);
        begin
            wait(hall_ready);@(negedge clk);hall_mask=1<<col;hall_velocity=0;
            hall_velocity[col*8+:8]=velocity;hall_frets=frets;hall_valid=1;
            @(negedge clk);hall_valid=0;
        end
    endtask
    task expect_event(input integer number,input [7:0]op,input [7:0]p0,input[7:0]p1,input[7:0]p2);
        begin
            #10000;
            if(count!=number||last!=={8'ha5,op,p0,p1,p2,(8'ha5^op^p0^p1^p2)})
                $fatal(1,"Event expected count=%0d got=%0d data=%h",number,count,last);
        end
    endtask
    initial begin
        #100;rst_n=1;#100;
        keys[0]=1;expect_event(1,2,6,0,100);
        #10000;if(count!=1)$fatal(1,"Held key retrigger");
        keys[0]=0;#10000;if(count!=1)$fatal(1,"Guitar release retrigger");
        keys[48]=1;expect_event(2,2,6,8,100);
        keys[125]=1;expect_event(3,2,1,20,100);
        keys=0;#10000;
        instrument=1;#10000;keys[125]=1;expect_event(4,5,84,100,1);
        keys[125]=0;expect_event(5,5,84,100,0);
        keys[0]=1;expect_event(6,5,40,100,1);
        enabled=0;expect_event(7,5,40,100,0);
        keys=0;enabled=1;instrument=2;#10000;
        keys[5]=1;#10000;if(count!=7)$fatal(1,"Bass string 1 accepted");
        keys[2]=1;expect_event(8,2,4,0,100);
        keys=0;#10000;instrument=0;ready=0;#10000;keys[6]=1;
        #10000;if(!valid||count!=8)$fatal(1,"Backpressure failed");
        ready=1;expect_event(9,2,6,1,100);
        keys=0;hall_mode=1;#10000;keys[48]=1;#10000;
        if(count!=9||frets[4:0]!=8)$fatal(1,"Selection-only Hall mode failed");
        pick(0,64);expect_event(10,2,6,8,64);
        keys[6]=1;keys[72]=1;#10000;
        if(count!=10||frets[4:0]!=12)$fatal(1,"Highest fret selection failed");
        pick(0,127);expect_event(11,2,6,12,127);
        pick(5,88);expect_event(12,2,1,0,88);
        instrument=2;#10000;pick(5,80);#10000;
        if(count!=12)$fatal(1,"Hall Bass forbidden string accepted");
        pick(0,80);expect_event(13,2,6,12,80);
        instrument=1;#10000;pick(0,80);expect_event(14,5,52,80,1);
        pick(0,81);expect_event(16,5,52,81,1);
        if(events[14]!==48'ha50534010095)
            $fatal(1,"Old Hall piano note not released before retrigger: %h",events[14]);
        #2100000;expect_event(17,5,52,1,0);
        enabled=0;pick(0,100);#10000;if(count!=17)$fatal(1,"Disabled pick emitted event");
        $display("PASS touch/pick: direct edges, fret selection, highest/open fret, Hall velocity, Bass mask, piano retrigger/release, backpressure");
        $finish;
    end
endmodule

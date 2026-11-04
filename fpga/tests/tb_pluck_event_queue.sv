`timescale 1ns/1ps
module tb_pluck_event_queue;
    reg clk=0;
    always #10 clk=~clk;
    reg rst_n=0,clear=0,sample_tick=0,uart_valid=0,local_valid=0;
    reg [14:0] uart_event=0,local_event=0;
    wire ingress_ready,event_valid,overflow;
    wire [14:0] event_data;
    wire [4:0] occupancy;
    integer entry,cycle;
    reg [14:0] model[0:8191];
    integer model_read=0,model_write=0,model_count=0;
    integer expected_count;
    reg expected_overflow=0;
    pluck_event_queue dut(.*);

    task step;
        begin @(posedge clk);#1;@(negedge clk);end
    endtask
    task pop_expect;
        input [14:0] expected;
        begin
            sample_tick=1;#1;
            if(!event_valid||event_data!==expected)$fatal(1,"FIFO order expected=%0d actual=%0d",expected,event_data);
            step();sample_tick=0;
        end
    endtask
    task reset_queue;
        begin
            rst_n=0;clear=0;uart_valid=0;local_valid=0;sample_tick=0;
            step();rst_n=1;step();
        end
    endtask
    initial begin
        reset_queue();
        uart_valid=1;local_valid=1;uart_event=15'd101;local_event=15'd202;
        step();uart_valid=0;local_valid=0;
        if(occupancy!=2)$fatal(1,"simultaneous producers lost");
        pop_expect(101);pop_expect(202);
        for(entry=0;entry<16;entry=entry+1)begin uart_valid=1;uart_event=entry;step();end
        uart_valid=0;
        if(occupancy!=16||ingress_ready||overflow)$fatal(1,"full queue status");
        uart_valid=1;uart_event=999;
        pop_expect(0);uart_valid=0;
        if(occupancy!=16||overflow)$fatal(1,"full simultaneous pop/push failed");
        for(entry=1;entry<16;entry=entry+1)pop_expect(entry);
        pop_expect(999);
        for(entry=0;entry<16;entry=entry+1)begin uart_valid=1;uart_event=entry;step();end
        uart_event=777;step();uart_valid=0;
        if(!overflow||occupancy!=16)$fatal(1,"overflow must be visible and preserve old queue");
        pop_expect(0);
        clear=1;uart_valid=1;sample_tick=1;#1;
        if(event_valid)$fatal(1,"flush emitted old note");
        step();clear=0;uart_valid=0;sample_tick=0;
        if(occupancy!=0||!overflow)$fatal(1,"flush/count/sticky overflow");
        reset_queue();
        for(cycle=0;cycle<3000;cycle=cycle+1)begin
            uart_valid=$urandom_range(0,1);local_valid=$urandom_range(0,1);
            sample_tick=$urandom_range(0,1);clear=($urandom_range(0,40)==0);
            uart_event=$urandom;local_event=$urandom;
            #1;
            if(clear)begin model_count=0;model_read=model_write;end
            else begin
                if(sample_tick&&model_count>0)begin
                    if(!event_valid||event_data!==model[model_read])$fatal(1,"random pop mismatch");
                    model_read=model_read+1;model_count=model_count-1;
                end else if(event_valid)$fatal(1,"random spurious output");
                if(uart_valid)begin
                    if(model_count<16)begin model[model_write]=uart_event;model_write=model_write+1;model_count=model_count+1;end
                    else expected_overflow=1;
                end
                if(local_valid)begin
                    if(model_count<16)begin model[model_write]=local_event;model_write=model_write+1;model_count=model_count+1;end
                    else expected_overflow=1;
                end
            end
            expected_count=model_count;
            step();
            if(occupancy!=expected_count||overflow!=expected_overflow)$fatal(1,"random count/overflow mismatch cycle=%0d",cycle);
        end
        $display("PASS pluck_event_queue dual producers, wraparound, full pop/push, overflow, flush, 3000 random cycles");
        $finish;
    end
    initial begin #2000000;$fatal(1,"timeout");end
endmodule

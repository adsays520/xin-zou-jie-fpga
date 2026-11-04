`timescale 1ns/1ps
module tb_verification;
    reg clk=0;always #10 clk=~clk;
    reg rst_n=0,byte_valid=0;reg [7:0] byte_data=0;
    wire tick,running,visual,request,start;
    wire [63:0] frequencies;wire [27:0] gains,pans;
    wire signed [23:0] dds_l,dds_r;wire dds_valid,latency_valid,deadline;
    wire [31:0] latency;wire [2:0] active_count;
    reg signed [23:0] held_l=0,held_r=0;
    wire signed [15:0] sample_l=running ? (held_l>>>8) : 16'sd1234;
    wire signed [15:0] sample_r=running ? (held_r>>>8) : -16'sd2345;
    wire serial_tx,busy,bck,ws,din;
    audio_drive drive(.clk(clk),.rst_n(rst_n),.idata_left(sample_l),.idata_right(sample_r),
                      .sample_tick(tick),.HP_BCK(bck),.HP_WS(ws),.HP_DIN(din),.req());
    verification_control control(.clk(clk),.rst_n(rst_n),.byte_valid(byte_valid),.byte_data(byte_data),
        .sample_tick(tick),.running(running),.visual_enable(visual),.capture_request(request),.start_event(start),
        .frequencies(frequencies),.gains(gains),.pans(pans));
    verification_dds dds(.clk(clk),.rst_n(rst_n),.sample_tick(tick),.running(running),.start_event(start),
        .frequencies(frequencies),.gains(gains),.pans(pans),.sample_l(dds_l),.sample_r(dds_r),
        .sample_valid(dds_valid),.latency_valid(latency_valid),.latency_cycles(latency),
        .deadline_miss(deadline),.active_count(active_count));
    always @(posedge clk)if(dds_valid)begin held_l<=dds_l;held_r<=dds_r;end
    // UART is accelerated only for packet tests; audio runs at real 50 MHz / 48 kHz.
    verification_telemetry #(.BAUD(5000000)) telemetry(.clk(clk),.rst_n(rst_n),.sample_tick(tick),
        .request(request),.sample_l(sample_l),.sample_r(sample_r),.flags({5'd0,deadline,latency_valid,running}),
        .active_count(active_count),.latency_cycles(latency),.uart_tx(serial_tx),.busy(busy));
    reg [7:0] px=0,py=0;reg [1:0] display_page=0;wire [1:0] latched_page;wire [15:0] rgb;wire [5:0] leds;
    verification_visuals visuals(.clk(clk),.rst_n(rst_n),.sample_tick(tick),.sample_l(sample_l),.sample_r(sample_r),
        .display_page(latched_page),.pixel_x(px),.pixel_y(py),.pixel_rgb(rgb),.led_n(leds));
    st7735_status screen(.clk(clk),.rst_n(rst_n),.guitar_level(7'd0),.piano_level(7'd0),.drum_level(7'd0),
        .selected_bus(2'd0),.page(2'd3),.visual_page_select(display_page),.visual_page(latched_page),.visual_pixel_rgb(rgb),.fx_drive(7'd0),.fx_tone(7'd0),.fx_mix(7'd0),
        .fx_amp(5'd0),.fx_modulation(3'd0),.chorus_mix(7'd0),.delay_mix(7'd0),.chorus_depth(7'd0),.drum_playing(1'b0));
    integer picture,xx,yy,page_no;
    task capture_screen;
        begin
            force screen.frame_page=3;force screen.render_x=px;force screen.render_y=py;
            for(page_no=0;page_no<3;page_no=page_no+1)begin
            display_page=page_no;force screen.frame_visual_page=display_page;
            case(page_no)
                0:picture=$fopen("tests/results/lcd_page_wave.ppm","w");
                1:picture=$fopen("tests/results/lcd_page_spectrum.ppm","w");
                2:picture=$fopen("tests/results/lcd_page_xy.ppm","w");
            endcase
            $fdisplay(picture,"P3\n128 160\n255");
            for(yy=0;yy<160;yy=yy+1)for(xx=0;xx<128;xx=xx+1)begin
                @(negedge clk);px=xx;py=yy;repeat(2)@(negedge clk);
                $fdisplay(picture,"%0d %0d %0d",screen.pixel_rgb[15:11]*255/31,
                    screen.pixel_rgb[10:5]*255/63,screen.pixel_rgb[4:0]*255/31);
            end
            $fclose(picture);end
            release screen.frame_visual_page;release screen.frame_page;release screen.render_x;release screen.render_y;
        end
    endtask
    integer clock_count=0,last_tick=0,tick_count=0,min_period=9999,max_period=0;
    always @(posedge clk)begin
        clock_count<=clock_count+1;
        if(tick)begin
            if(tick_count>0)begin
                if(clock_count-last_tick<min_period)min_period<=clock_count-last_tick;
                if(clock_count-last_tick>max_period)max_period<=clock_count-last_tick;
            end
            last_tick<=clock_count;tick_count<=tick_count+1;
        end
    end
    task send_byte(input [7:0] b);
        begin @(negedge clk);byte_data=b;byte_valid=1;@(negedge clk);byte_valid=0;repeat(4)@(negedge clk);end
    endtask
    task command(input [7:0] cmd,a,b,c);
        begin send_byte(8'hA5);send_byte(cmd);send_byte(a);send_byte(b);send_byte(c);send_byte(8'hA5^cmd^a^b^c);end
    endtask
    task ticks(input integer n);
        integer j;
        begin for(j=0;j<n;j=j+1)begin
            @(posedge clk);while(!tick)@(posedge clk);@(negedge clk);
        end end
    endtask
    integer file_handle=0,wire_count=0,bitno;
    reg [7:0] wire_byte;
    // Decode the transmitted UART pin independently of the sender's byte index.
    always begin
        @(negedge serial_tx);
        repeat(15)@(negedge clk); // midpoint of bit zero: 1.5 x 10 clocks
        for(bitno=0;bitno<8;bitno=bitno+1)begin
            wire_byte[bitno]=serial_tx;
            repeat(10)@(negedge clk);
        end
        if(serial_tx!==1'b1)$fatal(1,"UART stop bit");
        if(file_handle)begin $fwrite(file_handle,"%02x\n",wire_byte);wire_count=wire_count+1;end
        repeat(5)@(negedge clk);
    end
    integer count,i,k;reg [15:0] f;
    initial begin
        force GSR.GSRI=1'b0;
        repeat(8)@(negedge clk);rst_n=1;
        force GSR.GSRI=1'b1;
        // Bad XOR and out-of-range frequency may not change settings.
        send_byte(8'hA5);send_byte(8'h82);send_byte(1);send_byte(0);send_byte(0);send_byte(0);
        repeat(1200)@(negedge clk);
        if(running)$fatal(1,"bad XOR started test");
        command(8'h80,0,1,0);
        if(control.staged_freq[0]!=375)$fatal(1,"invalid frequency accepted");
        // All three bulk formats must swallow 36 payload bytes, including a
        // checksum-valid A5 82 01 00 00 26 pattern embedded in sample data.
        for(k=0;k<3;k=k+1)begin
            send_byte(8'hA5);send_byte(k==0 ? 8'h11 : k==1 ? 8'h21 : 8'h31);
            command(8'h82,1,0,0);
            for(i=0;i<30;i=i+1)send_byte(0);
            repeat(1200)@(negedge clk);
            if(running)$fatal(1,"bulk sample bytes started test");
        end
        command(8'h84,1,0,0);if(!visual)$fatal(1,"visual mode not set");
        for(count=1;count<=4;count=count+1)begin
            command(8'h82,0,0,0);
            ticks(3);
            for(i=0;i<4;i=i+1)begin
                f=375*(i+1);command(8'h80,i,f[7:0],f[15:8]);
                command(8'h81,i,i<count ? 80 : 0,64);
            end
            command(8'h82,1,0,0);
            ticks(6);
            if(active_count!=count || !latency_valid || deadline)$fatal(1,"DDS count/timing/deadline count=%0d expected=%0d run=%b latvalid=%b deadline=%b gains=%h phase0=%h sine0=%d mixl=%d",
                active_count,count,running,latency_valid,deadline,gains,dds.phase[0],dds.sine_q[0],dds.mix_l);
            if(latency>4000)$fatal(1,"DDS control response exceeds expected ticks");
            file_handle=$fopen($sformatf("tests/results/uart_%0d.hex",count),"w");wire_count=0;
            command(8'h83,0,0,0);
            wait(busy);wait(!busy);repeat(20)@(negedge clk);
            $fclose(file_handle);file_handle=0;
            if(wire_count!=2066)$fatal(1,"packet length %0d",wire_count);
            $display("PASS voices=%0d latency_cycles=%0d bytes=%0d bins=%0d,%0d,%0d,%0d LEDs=%b",
                count,latency,wire_count,visuals.bars[0],visuals.bars[1],visuals.bars[2],visuals.bars[3],leds);
            for(i=0;i<count;i=i+1)if(visuals.bars[i]<3)$fatal(1,"missing hardware DFT bin %0d",i);
        end
        capture_screen;
        command(8'h82,0,0,0);ticks(6);
        if(running || active_count!=0)$fatal(1,"stop did not restore normal path");
        file_handle=$fopen("tests/results/uart_normal.hex","w");wire_count=0;
        command(8'h83,0,0,0);wait(busy);wait(!busy);repeat(20)@(negedge clk);
        $fclose(file_handle);file_handle=0;
        if(min_period!=1041 || max_period!=1042)$fatal(1,"sample schedule min=%0d max=%0d",min_period,max_period);
        $display("PASS sample schedule=1041/1042 clocks; normal path restored");
        $finish;
    end
    initial begin #1000000000;$fatal(1,"simulation timeout");end
endmodule

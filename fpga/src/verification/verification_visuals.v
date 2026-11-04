// Audio-derived hardware visuals. No host-drawn pixels, recordings or nominal
// frequency markers. The spectrum uses sixteen measured DFT bins, not a full FFT.
module verification_visuals (
    input wire clk,rst_n,sample_tick,
    input wire signed [15:0] sample_l,sample_r,
    input wire [1:0] display_page,
    input wire [7:0] pixel_x,pixel_y,
    output reg [15:0] pixel_rgb,
    output wire [5:0] led_n
);
    // Bound the audio tick fanout to these input registers, then use a local
    // registered enable. Both samples are captured at the original I2S tap.
    reg tick_q;
    reg signed [15:0] sample_l_q,sample_r_q;
    reg [7:0] previous_l,previous_r;
    reg [2:0] visual_shift;
    wire [31:0] trace_word;
    wire [31:0] xy_word;
    reg [6:0] bars[0:15];
    reg signed [15:0] sine_rom[0:1023];
    initial $readmemh("src/verification/sine1024.hex",sine_rom);
    reg [1:0] decim;
    reg [6:0] index;
    reg clearing;
    reg [13:0] clear_address;
    reg [9:0] xy_age;
    reg [3:0] band;
    reg [2:0] stage;
    reg signed [15:0] mono,sin_q,cos_q;
    reg signed [31:0] prod_i,prod_q;
    reg signed [38:0] acc_i[0:15],acc_q[0:15];
    reg signed [38:0] bin_i_q,bin_q_q;
    reg [38:0] bin_abs_i_q,bin_abs_q_q;
    reg [39:0] bin_magnitude_q;
    reg [14:0] level_hold;
    reg [7:0] level_div;
    wire [15:0] abs_l=sample_l_q[15] ? -sample_l_q : sample_l_q;
    wire [15:0] abs_r=sample_r_q[15] ? -sample_r_q : sample_r_q;
    wire [15:0] absolute=abs_l>abs_r ? abs_l : abs_r;
    wire signed [16:0] mono_sum={sample_l_q[15],sample_l_q}+{sample_r_q[15],sample_r_q};
    wire [9:0] phase_address=(index*({1'b0,band}+5'd1))<<5;
    wire [9:0] quadrature_address=phase_address+10'd256;
    wire [38:0] absolute_i=acc_i[band][38] ? -acc_i[band] : acc_i[band];
    wire [38:0] absolute_q=acc_q[band][38] ? -acc_q[band] : acc_q[band];
    wire [39:0] magnitude={1'b0,absolute_i}+{1'b0,absolute_q};
    wire [6:0] bin_level=(|magnitude[39:37]) ? 7'd127 : magnitude[36:30];
    // Six active-low physical LEDs are an audio peak meter with ~5 ms decay.
    assign led_n=~{(level_hold>16384),(level_hold>8192),(level_hold>4096),
                   (level_hold>2048),(level_hold>1024),(level_hold>256)};
    integer i;
    // Dedicated dual-port BSRAM: do not let the bitmap become thousands of
    // flip-flops or consume promoted global clocks. Only clk drives RAM clocks.
    function [7:0] map128;
        input [15:0] value;
        begin map128={1'b0,7'd127-(value[15:9]^7'h40)};end
    endfunction
    function [15:0] visual_zoom;
        input signed [15:0] value;
        input [2:0] amount;
        reg signed [22:0] scaled;
        begin
            scaled=$signed(value);scaled=scaled<<<amount;
            visual_zoom=scaled>32767 ? 16'h7fff : scaled< -32768 ? 16'h8000 : scaled[15:0];
        end
    endfunction
    wire [15:0] zoom_l=visual_zoom(sample_l_q,visual_shift),zoom_r=visual_zoom(sample_r_q,visual_shift);
    wire [7:0] mapped_l=map128(zoom_l),mapped_r=map128(zoom_r);
    wire [7:0] top_l=mapped_l<previous_l ? mapped_l : previous_l;
    wire [7:0] bottom_l=mapped_l>previous_l ? mapped_l : previous_l;
    wire [7:0] top_r=mapped_r<previous_r ? mapped_r : previous_r;
    wire [7:0] bottom_r=mapped_r>previous_r ? mapped_r : previous_r;
    wire [31:0] trace_input={bottom_r,top_r,bottom_l,top_l};
    wire trace_write_enable=tick_q && decim==3;
    SDPB trace_ram(.DO(trace_word),.DI(trace_input),.BLKSELA(3'd0),.BLKSELB(3'd0),
        .ADA({2'd0,index,1'b0,4'b1111}),.ADB({2'd0,pixel_x[6:0],5'd0}),
        .CLKA(clk),.CLKB(clk),.CEA(trace_write_enable),.CEB(1'b1),.OCE(1'b1),.RESET(!rst_n));
    defparam trace_ram.BIT_WIDTH_0=32,trace_ram.BIT_WIDTH_1=32,trace_ram.READ_MODE=0;
    wire xy_write_enable=clearing || (tick_q && decim==3);
    wire [13:0] xy_write_address=clearing ? clear_address : {mapped_r[6:0],(zoom_l[15:9]^7'h40)};
    wire [6:0] xy_row=pixel_y-8'd24;
    wire [13:0] xy_read_address={xy_row,pixel_x[6:0]};
    SDPB xy_ram(.DO(xy_word),.DI({31'd0,!clearing}),.BLKSELA(3'd0),.BLKSELB(3'd0),
        .ADA(xy_write_address),.ADB(xy_read_address),
        .CLKA(clk),.CLKB(clk),.CEA(xy_write_enable),.CEB(1'b1),.OCE(1'b1),.RESET(!rst_n));
    defparam xy_ram.BIT_WIDTH_0=1,xy_ram.BIT_WIDTH_1=1,xy_ram.READ_MODE=0;
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin
            tick_q<=0;sample_l_q<=0;sample_r_q<=0;
            decim<=0;index<=0;band<=0;stage<=0;mono<=0;sin_q<=0;cos_q<=0;
            prod_i<=0;prod_q<=0;bin_i_q<=0;bin_q_q<=0;bin_abs_i_q<=0;bin_abs_q_q<=0;bin_magnitude_q<=0;clearing<=1;clear_address<=0;xy_age<=0;
            level_hold<=0;level_div<=0;previous_l<=64;previous_r<=64;visual_shift<=0;
            for(i=0;i<16;i=i+1)begin acc_i[i]<=0;acc_q[i]<=0;bars[i]<=0;end
            // Trace RAM is initialised by 128 incoming samples; no FF reset tree.
        end else begin
            tick_q<=sample_tick;
            // Unconditional tap registers remove the high-fanout sample_tick
            // enable from these 32 FFs. tick_q consumes the prior tap on the
            // following edge, before the audio output words change.
            sample_l_q<=sample_l;sample_r_q<=sample_r;
            if(clearing)begin
                if(clear_address==16383)begin clearing<=0;clear_address<=0;end
                else clear_address<=clear_address+1'b1;
            end
            if(tick_q)begin
                decim<=decim+1'b1;
                level_div<=level_div+1'b1;
                if(absolute[15])level_hold<=32767;
                else if(absolute>level_hold)level_hold<=absolute[14:0];
                else if(level_div==0)level_hold<=level_hold-(level_hold>>4);
                if(decim==3)begin
                    // Shared display zoom only; never fed into any sound path.
                    if(index==0)visual_shift<=level_hold<256 ? 6 : level_hold<512 ? 5 :
                        level_hold<1024 ? 4 : level_hold<2048 ? 3 : level_hold<4096 ? 2 : level_hold<8192 ? 1 : 0;
                    // Signed full-scale fixed axis, without independent channel gain.
                    previous_l<=mapped_l;previous_r<=mapped_r;
                    if(!clearing)begin
                        xy_age<=xy_age+1'b1;
                        if(xy_age==1023)begin clearing<=1;clear_address<=0;end
                    end
                    mono<=mono_sum>>>1;band<=0;stage<=1;
                end
            end
            case(stage)
                1:begin sin_q<=sine_rom[phase_address];cos_q<=sine_rom[quadrature_address];stage<=2;end
                2:begin prod_i<=mono*cos_q;prod_q<=mono*sin_q;stage<=3;end
                3:begin
                    acc_i[band]<=acc_i[band]+prod_i;acc_q[band]<=acc_q[band]+prod_q;
                    if(index==127)stage<=4;
                    else if(band==15)begin index<=index+1'b1;stage<=0;end
                    else begin band<=band+1'b1;stage<=1;end
                end
                4:begin bin_i_q<=acc_i[band];bin_q_q<=acc_q[band];stage<=5;end
                5:begin bin_abs_i_q<=bin_i_q[38]?-bin_i_q:bin_i_q;bin_abs_q_q<=bin_q_q[38]?-bin_q_q:bin_q_q;stage<=6;end
                6:begin bin_magnitude_q<={1'b0,bin_abs_i_q}+{1'b0,bin_abs_q_q};stage<=7;end
                7:begin
                    bars[band]<=(|bin_magnitude_q[39:37])?7'd127:bin_magnitude_q[36:30];acc_i[band]<=0;acc_q[band]<=0;
                    if(band==15)begin index<=0;stage<=0;end
                    else begin band<=band+1'b1;stage<=1;end
                end
            endcase
        end
    end
    reg [3:0] draw_band;
    reg [7:0] bar_height;
    function [7:0] peak_height;
        input [6:0] value;
        begin
            if(value[6])peak_height=112+{4'd0,value[5:2]};
            else if(value[5])peak_height=96+{4'd0,value[4:1]};
            else if(value[4])peak_height=80+{4'd0,value[3:0]};
            else if(value[3])peak_height=64+{4'd0,value[2:0],1'b0};
            else if(value[2])peak_height=48+{4'd0,value[1:0],2'b0};
            else if(value[1])peak_height=32+{4'd0,value[0],3'b0};
            else peak_height=value[0] ? 16 : 0;
        end
    endfunction
    always @*begin
        draw_band=pixel_x[6:3];bar_height=peak_height(bars[draw_band]);
        pixel_rgb=16'h10c3;
        if(pixel_y>=24 && pixel_y<152)begin
            case(display_page)
                0:begin
                    if(pixel_y==88 || pixel_x[4:0]==0)pixel_rgb=16'h3186;
                    if(pixel_y-24>=trace_word[7:0] && pixel_y-24<=trace_word[15:8])pixel_rgb=16'h6ef9;
                    if(pixel_y-24>=trace_word[23:16] && pixel_y-24<=trace_word[31:24])pixel_rgb=16'hfd89;
                end
                1:begin
                    if(pixel_y==151 || pixel_y==119 || pixel_y==87 || pixel_y==55)pixel_rgb=16'h3186;
                    if((pixel_x[2:0]==3 || pixel_x[2:0]==4) && bar_height!=0 && pixel_y>=151-bar_height)pixel_rgb=16'h8ed1;
                end
                2:begin
                    if(pixel_x==64 || pixel_y==88)pixel_rgb=16'h3186;
                    if(xy_word[0])pixel_rgb=16'hdadc;
                end
                default:begin end
            endcase
        end
    end
endmodule

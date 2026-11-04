// Independent, deterministic finger/plucked electric Bass. No guitar DSP edits.
// 48 kHz, 8 overlapping voices, 12 band-limited harmonics at most.
module bass_poly8 #(parameter PANEL_PITCH=0)(
    input wire clk,rst_n,sample_tick,note_on,poly_mode,
    input wire [23:0] panel_ratio_q20,
    input wire [2:0] string_sel,
    input wire [4:0] fret_sel,
    input wire [6:0] velocity,
    output wire sample_valid,
    output wire signed [23:0] sample_out,
    output wire active,
    output reg deadline_miss
);
    reg [31:0] wave_rom [0:2047]; // {bright attack, warm sustain}, signed Q15
    reg [31:0] pitch_rom [0:127];
    initial begin
        $readmemh("src/bass/bass_wave.hex",wave_rom);
        $readmemh("src/bass/bass_pitch.hex",pitch_rom);
    end
    reg [10:0] rom_addr;
    reg [31:0] rom_data;
    always @(posedge clk) rom_data<=wave_rom[rom_addr];
    wire [6:0] pitch_addr={string_sel[1:0]-2'd2,fret_sel};
    reg [31:0] event_pitch;
    always @(posedge clk) event_pitch<=pitch_rom[pitch_addr];

    reg [31:0] phase[0:7],step[0:7],next_step[0:7];
    reg [23:0] amp[0:7],target[0:7],next_target[0:7];
    reg [15:0] brightness[0:7];
    reg [16:0] age[0:7];
    reg [6:0] fade[0:7];
    reg [2:0] voice_string[0:7];
    reg [7:0] releasing;
    reg [7:0] occupied;
    reg [2:0] allocator,index;
    reg event_pending;
    reg [31:0] pending_step;
    reg [23:0] pending_target;
    reg event_delay;
    reg [6:0] event_velocity;
    reg [2:0] event_string,pending_string;
    reg [4:0] state;
    reg signed [28:0] sum,total;
    reg sum_valid;
    wire bus_busy,bus_limited;
    poly32_bus_manager u_bass_bus(.clk(clk),.rst_n(rst_n),
        .input_valid(sum_valid),.sum_in(total),.output_valid(sample_valid),
        .sample_out(sample_out),.busy(bus_busy),.limited(bus_limited));
    assign active=|occupied;

    reg [31:0] ph,inc;reg [55:0] panel_step_product;
    reg [23:0] a,t,a_next;
    reg [15:0] bright;
    reg [16:0] note_age;
    reg [6:0] fading;
    reg released;
    reg [15:0] fraction;
    reg signed [15:0] b0,d0,b1,d1;
    reg signed [16:0] bd,dd;
    reg signed [33:0] bp,dp;
    reg signed [17:0] bi,di,blend_delta;
    reg signed [34:0] blend_product;
    reg signed [18:0] wave_value;
    reg signed [43:0] voice_product;
    reg signed [28:0] voice_value;
    integer k;
    // All multiplications are separated from the following additions.
    // One frame needs 8*15+44 clocks, well below the 1041-clock budget.
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n)begin
            occupied<=0;allocator<=0;index<=0;state<=0;
            releasing<=0;event_string<=0;pending_string<=0;released<=0;
            event_pending<=0;event_delay<=0;event_velocity<=0;
            pending_step<=0;pending_target<=0;deadline_miss<=0;
            sum<=0;total<=0;sum_valid<=0;rom_addr<=0;
            ph<=0;inc<=0;a<=0;t<=0;a_next<=0;bright<=0;
            note_age<=0;fading<=0;fraction<=0;
            b0<=0;d0<=0;b1<=0;d1<=0;bd<=0;dd<=0;
            bp<=0;dp<=0;bi<=0;di<=0;blend_delta<=0;
            blend_product<=0;wave_value<=0;voice_product<=0;voice_value<=0;
            for(k=0;k<8;k=k+1)begin
                phase[k]<=0;step[k]<=0;next_step[k]<=0;
                amp[k]<=0;target[k]<=0;next_target[k]<=0;
                brightness[k]<=0;age[k]<=0;fade[k]<=0;
                voice_string[k]<=0;
            end
        end else begin
            sum_valid<=0;
            event_delay<=note_on&&string_sel>=2&&string_sel<=5&&fret_sel<=20&&velocity!=0;
            if(note_on)begin event_velocity<=velocity;event_string<=string_sel;end
            if(event_delay)begin
                if(event_pending)deadline_miss<=1;
                pending_step<=event_pitch;
                pending_target<={1'b0,event_velocity,16'b0};
                pending_string<=event_string;
                event_pending<=1;
            end
            if(sample_tick&&(state!=0||bus_busy))deadline_miss<=1;
            case(state)
            0:begin
                if(event_pending)begin
                    event_pending<=0;
                    // A real string cannot keep two separate fretted notes ringing.
                    // Damp its old note smoothly; other strings retain polyphony.
                    for(k=0;k<8;k=k+1)
                        if(occupied[k]&&voice_string[k]==pending_string&&k!=allocator)
                            releasing[k]<=1;
                    voice_string[allocator]<=pending_string;
                    if(!occupied[allocator])begin
                        phase[allocator]<=0;step[allocator]<=pending_step;
                        target[allocator]<=pending_target;amp[allocator]<=0;
                        brightness[allocator]<=16'd32768;age[allocator]<=0;
                        fade[allocator]<=0;occupied[allocator]<=1;
                        releasing[allocator]<=0;
                    end else begin
                        // Fade the stolen voice before launching its replacement.
                        fade[allocator]<=7'd64;
                        next_step[allocator]<=pending_step;
                        next_target[allocator]<=pending_target;
                    end
                    allocator<=poly_mode?allocator+1'b1:3'd0;
                end else if(sample_tick)begin index<=0;sum<=0;state<=1;end
            end
            1:begin
                ph<=phase[index];inc<=step[index];a<=amp[index];t<=target[index];
                bright<=brightness[index];note_age<=age[index];fading<=fade[index];
                released<=releasing[index];
                rom_addr<=phase[index][31:21];fraction<=phase[index][20:5];state<=2;
            end
            2:begin rom_addr<=ph[31:21]+1'b1;if(PANEL_PITCH)panel_step_product<=inc*panel_ratio_q20;state<=3;end
            3:begin if(PANEL_PITCH)inc<=panel_step_product[51:20];b0<=$signed(rom_data[31:16]);d0<=$signed(rom_data[15:0]);state<=4;end
            4:begin b1<=$signed(rom_data[31:16]);d1<=$signed(rom_data[15:0]);state<=5;end
            5:begin bd<=$signed({b1[15],b1})-$signed({b0[15],b0});
                dd<=$signed({d1[15],d1})-$signed({d0[15],d0});state<=6;end
            6:begin bp<=bd*$signed({1'b0,fraction});dp<=dd*$signed({1'b0,fraction});state<=7;end
            7:begin bi<=b0+(bp>>>16);di<=d0+(dp>>>16);state<=8;end
            8:begin blend_delta<=bi-di;state<=9;end
            9:begin blend_product<=blend_delta*$signed({1'b0,bright});state<=10;end
            10:begin
                wave_value<=di+(blend_product>>>15);
                if(!occupied[index])a_next<=0;
                else if(fading!=0)a_next<=a-(a>>3);
                else if(released)a_next<=(a<4096)?0:a-(a>>5);
                else if(note_age<64)a_next<=(a+(t>>6)>t)?t:a+(t>>6);
                else if(note_age>=96000)a_next<=(a<4096)?0:a-(a>>10);
                else if(note_age<4800)a_next<=a-(a>>14);
                else a_next<=a-(a>>17);
                state<=11;
            end
            11:begin voice_product<=wave_value*$signed({1'b0,a_next});state<=12;end
            12:begin voice_value<=voice_product>>>17;state<=13;end
            13:begin
                sum<=sum+voice_value;
                phase[index]<=ph+inc;amp[index]<=a_next;
                brightness[index]<=bright<512?0:bright-(bright>>11);
                if(occupied[index]&&note_age<120000)age[index]<=note_age+1'b1;
                if(fading>1)fade[index]<=fading-1'b1;
                else if(fading==1)begin
                    phase[index]<=0;step[index]<=next_step[index];
                    target[index]<=next_target[index];amp[index]<=0;
                    brightness[index]<=16'd32768;age[index]<=0;fade[index]<=0;
                    releasing[index]<=0;
                end else if(note_age>=120000||(!a_next&&note_age>=64))occupied[index]<=0;
                state<=14;
            end
            14:begin
                if(index==7)begin total<=sum;sum_valid<=1;state<=0;end
                else begin index<=index+1'b1;state<=1;end
            end
            default:state<=0;
            endcase
        end
    end
endmodule

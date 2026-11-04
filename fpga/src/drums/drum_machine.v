// 4/4 x four bars = 16 beats; canonical 64 sixteenth-note positions.
// Fixed six-byte XOR frames 50..57 share the existing UART byte stream.
// Upload is sequential and only committed after all 12 x 64 cells arrive.
module drum_machine #(
    parameter integer SAMPLE_RATE=48000,
    parameter integer PACKET_IDLE_CLKS=2500000
)(
    input wire clk,rst_n,sample_tick,byte_valid,input wire [7:0] byte_data,
    output wire sample_valid,output wire signed [23:0] sample_l,sample_r,
    output reg playing,output reg pattern_ready,
    output reg [5:0] current_step,output wire active,
    output wire deadline_miss,output wire clipped,
    input wire parameter_load_begin,parameter_byte_valid,parameter_chunk_valid,parameter_load_commit,parameter_load_error,
    input wire [7:0] parameter_byte_data,input wire [10:0] parameter_chunk_index,
    output wire parameter_load_ready,output wire [10:0] parameter_chunk_count,
    output wire parameter_initialized,parameter_fault,parameter_active_bank
);
    reg [2:0] parser;
    reg [7:0] cmd,p0,p1,p2,checksum;
    reg [5:0] count;
    reg [$clog2(PACKET_IDLE_CLKS+1)-1:0] idle;
    reg [6:0] pattern[0:1023];
    reg pattern_we;
    reg [9:0] pattern_address,expected;
    reg [6:0] pattern_value,read_value;
    reg uploading,upload_error;
    reg [8:0] bpm;
    reg [5:0] swing;
    reg [1:0] kit;
    reg panic,manual_hit,level_we,start_event,stop_event;
    reg [3:0] manual_voice,level_voice;
    reg [6:0] manual_velocity,level_value;
    reg [31:0] phase;
    reg [31:0] swing_amount;
    wire [31:0] threshold=current_step[1]
        ?(SAMPLE_RATE*60-swing_amount):(SAMPLE_RATE*60+swing_amount);
    wire [31:0] phase_next=phase+{21'd0,bpm,2'b00};
    reg [2:0] scan_state;
    reg [3:0] scan_voice;
    reg [5:0] scan_step;
    reg closed_at_step;
    reg seq_hit;
    reg [3:0] seq_voice;
    reg [6:0] seq_velocity;
    wire synth_hit=manual_hit||seq_hit;
    wire [3:0] synth_voice=manual_hit?manual_voice:seq_voice;
    wire [6:0] synth_velocity=manual_hit?manual_velocity:seq_velocity;
    // Separate RAM port, with synchronous read; RAM is never bulk-reset.
    always @(posedge clk)begin
        if(pattern_we)pattern[pattern_address]<=pattern_value;
        read_value<=pattern[{scan_voice,scan_step}];
    end
    drum_synth u_synth(
        .parameter_load_begin(parameter_load_begin),.parameter_byte_valid(parameter_byte_valid),
        .parameter_chunk_valid(parameter_chunk_valid),.parameter_load_commit(parameter_load_commit),
        .parameter_load_error(parameter_load_error),.parameter_byte_data(parameter_byte_data),
        .parameter_chunk_index(parameter_chunk_index),.parameter_load_ready(parameter_load_ready),
        .parameter_chunk_count(parameter_chunk_count),.parameter_initialized(parameter_initialized),
        .parameter_fault(parameter_fault),.parameter_active_bank(parameter_active_bank),
        .clk(clk),.rst_n(rst_n),.sample_tick(sample_tick),.panic(panic),
        .hit(seq_hit),.hit_voice(seq_voice),.hit_velocity(seq_velocity),
        .hit2(manual_hit),.hit2_voice(manual_voice),.hit2_velocity(manual_velocity),
        .kit(kit),.level_we(level_we),.level_voice(level_voice),.level_value(level_value),
        .sample_valid(sample_valid),.sample_l(sample_l),.sample_r(sample_r),
        .active(active),.deadline_miss(deadline_miss),.clipped(clipped));
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin
            parser<=0;cmd<=0;p0<=0;p1<=0;p2<=0;checksum<=0;count<=0;idle<=0;
            pattern_we<=0;pattern_address<=0;pattern_value<=0;expected<=0;
            uploading<=0;upload_error<=0;pattern_ready<=0;
            bpm<=120;swing<=0;swing_amount<=0;kit<=0;panic<=0;manual_hit<=0;
            manual_voice<=0;manual_velocity<=0;level_we<=0;level_voice<=0;level_value<=0;
            start_event<=0;stop_event<=0;
        end else begin
            pattern_we<=0;panic<=0;manual_hit<=0;level_we<=0;start_event<=0;stop_event<=0;
            if(byte_valid||parser==0)idle<=0;
            else if(idle<PACKET_IDLE_CLKS)idle<=idle+1'b1;
            if(!byte_valid&&parser!=0&&idle==PACKET_IDLE_CLKS)begin
                parser<=0;
                if(cmd>=8'h53&&cmd<=8'h55)upload_error<=1;
            end else if(byte_valid)case(parser)
                0:if(byte_data==8'ha5)begin checksum<=8'ha5;parser<=1;end
                1:begin
                    cmd<=byte_data;checksum<=checksum^byte_data;count<=0;
                    // Foreign envelope/wavetable packets have 36 remaining bytes.
                    if(byte_data==8'h11||byte_data==8'h21||byte_data==8'h31)begin count<=36;parser<=4;end
                    else parser<=2;
                end
                2:begin
                    if(count==0)p0<=byte_data;
                    if(count==1)p1<=byte_data;
                    if(count==2)p2<=byte_data;
                    checksum<=checksum^byte_data;
                    if(count==2)parser<=3;else count<=count+1'b1;
                end
                3:begin
                    parser<=0;
                    if(byte_data==checksum)case(cmd)
                        8'h50:if(p0<12&&p1>0&&p1<128&&p2==0)begin manual_hit<=1;manual_voice<=p0[3:0];manual_velocity<=p1[6:0];end
                        8'h51:if({p0,p1}>=30&&{p0,p1}<=300&&p2<=50)begin
                            bpm<={p0[0],p1};swing<=p2[5:0];swing_amount<=p2*(SAMPLE_RATE*60/100);
                        end
                        8'h52:if(p1==0&&p2==0)begin
                            if(p0==1&&pattern_ready&&!uploading)start_event<=1;
                            else if(p0==0||p0==2)begin stop_event<=1;panic<=1;end
                        end
                        8'h53:if({p0,p1,p2}==0)begin
                            stop_event<=1;panic<=1;pattern_ready<=0;
                            uploading<=1;upload_error<=0;expected<=0;
                        end
                        8'h54:begin
                            if(uploading&&!upload_error&&!playing&&p0<12&&p1<64&&p2<128&&
                                {p0[3:0],p1[5:0]}==expected&&expected<768)begin
                                pattern_we<=1;pattern_address<=expected;pattern_value<=p2[6:0];expected<=expected+1'b1;
                            end else if(uploading)upload_error<=1;
                        end
                        8'h55:if({p0,p1,p2}==0)begin
                            if(uploading&&!upload_error&&expected==768)pattern_ready<=1;
                            else pattern_ready<=0;
                            uploading<=0;
                        end
                        8'h56:if(p0<3&&p1==0&&p2==0)begin kit<=p0[1:0];if(kit!=p0[1:0])panic<=1;end
                        8'h57:if(p0<12&&p1<128&&p2==0)begin level_we<=1;level_voice<=p0[3:0];level_value<=p1[6:0];end
                        default:begin end
                    endcase
                    else if(cmd>=8'h53&&cmd<=8'h55)upload_error<=1;
                end
                4:if(count==1)parser<=0;else count<=count-1'b1;
                default:parser<=0;
            endcase
        end
    end
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin
            playing<=0;current_step<=0;phase<=0;scan_state<=0;scan_voice<=0;scan_step<=0;
            seq_hit<=0;seq_voice<=0;seq_velocity<=0;closed_at_step<=0;
        end else begin
            seq_hit<=0;
            if(stop_event)begin playing<=0;phase<=0;scan_state<=0;end
            else begin
                if(start_event)begin
                    playing<=1;phase<=0;current_step<=0;
                    scan_step<=0;scan_voice<=0;scan_state<=1;closed_at_step<=0;
                end else if(sample_tick&&playing)begin
                    if(phase_next>=threshold)begin
                        phase<=phase_next-threshold;current_step<=current_step+1'b1;
                        scan_step<=current_step+1'b1;scan_voice<=0;scan_state<=1;closed_at_step<=0;
                    end else phase<=phase_next;
                end
                case(scan_state)
                    1:scan_state<=2;
                    2:begin
                        if(scan_voice==2)closed_at_step<=(read_value!=0);
                        if(read_value!=0&&!(scan_voice==3&&closed_at_step))begin
                            seq_hit<=1;seq_voice<=scan_voice;seq_velocity<=read_value;
                        end
                        if(scan_voice==11)scan_state<=0;
                        else begin scan_voice<=scan_voice+1'b1;scan_state<=1;end
                    end
                    default:begin end
                endcase
            end
        end
    end
endmodule

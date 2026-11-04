// Writable PERIODIC wavetable oscillator with an independent amplitude timeline.
// Eight octave anti-alias banks and one 4096-point envelope share a synchronous
// inferred SDP RAM. No PCM cursor, piano EQ, or second natural-decay envelope.
module drawn_synth16 #(parameter PANEL_PITCH=0)(
    input wire clk,input wire rst_n,input wire voice_rst_n,input wire sample_tick,
    input wire [23:0] panel_ratio_q20,
    input wire note_on,input wire note_off,input wire poly_mode,
    input wire [6:0] requested_key,input wire [6:0] velocity,
    input wire [31:0] requested_phase_step,input wire [23:0] envelope_step,
    input wire [2:0] pedal_level,
    input wire ram_we,input wire [13:0] ram_addr,input wire [15:0] ram_data,
    output wire sample_valid,output wire signed [23:0] sample_out,
    output wire active,output reg deadline_miss
);
    wire [15:0] ram_q;
    reg [15:0] voice_active,key_down,epoch;
    reg [6:0] key[0:15];
    reg [2:0] bank[0:15];
    reg [31:0] phase[0:15],phase_step[0:15],env_phase[0:15];
    reg [23:0] env_step[0:15];
    reg [15:0] velocity_gain[0:15],release_gain[0:15];
    // Separate the shared combinational key lookup from the indexed voice
    // register write. One control clock of latency, no change to audio math.
    reg note_on_q,poly_mode_q;
    reg [6:0] key_q;
    reg [2:0] bank_q;
    reg [31:0] phase_step_q;
    reg [23:0] env_step_q;
    reg [15:0] velocity_q;
    reg [3:0] allocation,slot,cycle;
    reg [55:0] panel_step_product;
    wire [2:0] panel_bank=(PANEL_PITCH&&panel_ratio_q20>1048576&&bank[slot]<7)?bank[slot]+1'b1:bank[slot];
    reg running,mix_start;
    reg signed [28:0] sum;
    reg work_active,work_epoch;
    reg [2:0] work_bank;
    reg [9:0] work_wave_index;
    reg [11:0] work_env_index;
    reg [15:0] wave_fraction,env_fraction,velocity_work,release_work;
    reg signed [15:0] wave0,wave1;
    reg [15:0] env0;
    reg signed [33:0] wave_product,env_product;
    reg signed [17:0] wave_interpolated,velocity_sample,envelope_sample;
    reg [15:0] envelope_interpolated;
    reg signed [34:0] velocity_product,envelope_product,release_product;
    reg signed [23:0] voice_sample;
    wire mix_busy;
    wire engine_rst_n=rst_n&&voice_rst_n;
    wire [3:0] new_slot=poly_mode_q?allocation:4'd0;
    assign active=|voice_active;

    function [2:0] octave_bank;
        input [6:0] value;
        begin
            if(value<36)octave_bank=0;else if(value<48)octave_bank=1;
            else if(value<60)octave_bank=2;else if(value<72)octave_bank=3;
            else if(value<84)octave_bank=4;else if(value<96)octave_bank=5;
            else if(value<108)octave_bank=6;else octave_bank=7;
        end
    endfunction
    function [15:0] velocity_level;
        input [6:0] value;
        reg [15:0] level;
        begin
            level=16'd650+({9'd0,value}*{9'd0,value}<<1);
            velocity_level=value==0?0:(level>32767?16'd32767:level);
        end
    endfunction
    wire [9:0] next_wave_index=work_wave_index+10'd1;
    wire [11:0] next_env_index=work_env_index==4095?12'd4095:work_env_index+12'd1;
    wire [13:0] read_address=cycle==0?{1'b0,panel_bank,phase[slot][31:22]}:
        (cycle==1?{1'b0,work_bank,next_wave_index}:
        (cycle==2?14'd8192+{2'd0,work_env_index}:14'd8192+{2'd0,next_env_index}));
    // Never reset or clear the uploaded memory when flushing playing voices.
    drawn_table_ram_pages u_table(
        .clk(clk), .write_enable(ram_we), .write_address(ram_addr), .write_data(ram_data),
        .read_enable(running&&cycle<4), .read_address(read_address), .read_data(ram_q)
    );
    wire signed [16:0] wave_delta=$signed({wave1[15],wave1})-$signed({wave0[15],wave0});
    wire signed [16:0] env_delta=$signed({1'b0,ram_q})-$signed({1'b0,env0});
    wire [16:0] interpolated_env_wide={1'b0,env0}+(env_product>>>16);
    wire [32:0] next_env_phase={1'b0,env_phase[slot]}+{9'd0,env_step[slot]};
    wire [15:0] release_decrement=pedal_level==0?16'd9:
        (pedal_level==1?16'd6:(pedal_level==2?16'd4:16'd2));
    poly32_bus_manager u_mix(
        .clk(clk),.rst_n(engine_rst_n),.input_valid(mix_start),.sum_in(sum),
        .output_valid(sample_valid),.sample_out(sample_out),.busy(mix_busy),.limited());
    integer i;
    always @(posedge clk or negedge engine_rst_n)begin
        if(!engine_rst_n)begin
            note_on_q<=0;poly_mode_q<=1;key_q<=60;bank_q<=3;
            phase_step_q<=0;env_step_q<=3994;velocity_q<=0;
            voice_active<=0;key_down<=0;epoch<=0;allocation<=0;
            slot<=0;cycle<=0;running<=0;mix_start<=0;sum<=0;deadline_miss<=0;
            work_active<=0;work_epoch<=0;work_bank<=0;work_wave_index<=0;work_env_index<=0;
            wave_fraction<=0;env_fraction<=0;velocity_work<=0;release_work<=0;
            wave0<=0;wave1<=0;env0<=0;wave_product<=0;env_product<=0;
            wave_interpolated<=0;envelope_interpolated<=0;velocity_sample<=0;
            envelope_sample<=0;velocity_product<=0;envelope_product<=0;
            release_product<=0;voice_sample<=0;
            for(i=0;i<16;i=i+1)begin
                key[i]<=60;bank[i]<=3;phase[i]<=0;phase_step[i]<=0;
                env_phase[i]<=0;env_step[i]<=3994;velocity_gain[i]<=0;release_gain[i]<=32768;
            end
        end else begin
            note_on_q<=note_on;poly_mode_q<=poly_mode;key_q<=requested_key;
            bank_q<=octave_bank(requested_key);phase_step_q<=requested_phase_step;
            env_step_q<=envelope_step;velocity_q<=velocity_level(velocity);
            mix_start<=0;
            if(sample_tick)begin
                if(running||mix_busy)deadline_miss<=1;
                else begin running<=1;slot<=0;cycle<=0;sum<=0;end
            end
            if(running)begin
                cycle<=cycle+1'b1;
                case(cycle)
                    0:begin
                        work_active<=voice_active[slot];work_epoch<=epoch[slot];
                        work_bank<=panel_bank;if(PANEL_PITCH)panel_step_product<=phase_step[slot]*panel_ratio_q20;work_wave_index<=phase[slot][31:22];
                        work_env_index<=env_phase[slot][27:16];
                        wave_fraction<=phase[slot][21:6];env_fraction<=env_phase[slot][15:0];
                        velocity_work<=velocity_gain[slot];release_work<=release_gain[slot];
                    end
                    1:wave0<=$signed(ram_q);
                    2:wave1<=$signed(ram_q);
                    3:env0<=ram_q>32768?16'd32768:ram_q;
                    4:begin
                        wave_product<=wave_delta*$signed({1'b0,wave_fraction});
                        env_product<=env_delta*$signed({1'b0,env_fraction});
                    end
                    5:begin
                        wave_interpolated<=$signed(wave0)+(wave_product>>>16);
                        envelope_interpolated<=interpolated_env_wide>32768
                            ?16'd32768:interpolated_env_wide[15:0];
                    end
                    6:velocity_product<=wave_interpolated*$signed({1'b0,velocity_work});
                    7:velocity_sample<=velocity_product>>>15;
                    8:envelope_product<=velocity_sample*$signed({1'b0,envelope_interpolated});
                    9:envelope_sample<=envelope_product>>>15;
                    10:release_product<=envelope_sample*$signed({1'b0,release_work});
                    11:voice_sample<=(release_product>>>15)<<<8;
                    12:if(work_active&&work_epoch==epoch[slot])sum<=sum+$signed(voice_sample);
                    13:if(work_active&&work_epoch==epoch[slot])begin
                        phase[slot]<=phase[slot]+(PANEL_PITCH?panel_step_product[51:20]:phase_step[slot]);
                        env_phase[slot]<=next_env_phase>=33'h00fff0000 ? 32'h0fff0000 : next_env_phase[31:0];
                        if(env_phase[slot]>=32'h0fff0000)voice_active[slot]<=0;
                        if(!key_down[slot]&&pedal_level<4)begin
                            if(release_gain[slot]<=release_decrement)begin
                                release_gain[slot]<=0;voice_active[slot]<=0;
                            end else release_gain[slot]<=release_gain[slot]-release_decrement;
                        end
                    end
                    15:begin
                        cycle<=0;
                        if(slot==15)begin running<=0;mix_start<=1;end
                        else slot<=slot+1'b1;
                    end
                    default:begin end
                endcase
            end
            if(note_off)for(i=0;i<16;i=i+1)
                if(voice_active[i]&&key[i]==requested_key)key_down[i]<=0;
            if(note_on_q)begin
                allocation<=poly_mode_q?allocation+1'b1:4'd0;
                voice_active[new_slot]<=1;
                key_down[new_slot]<=!(note_off&&requested_key==key_q);
                epoch[new_slot]<=~epoch[new_slot];
                key[new_slot]<=key_q;bank[new_slot]<=bank_q;
                phase[new_slot]<=0;phase_step[new_slot]<=phase_step_q;
                env_phase[new_slot]<=0;env_step[new_slot]<=env_step_q;
                velocity_gain[new_slot]<=velocity_q;release_gain[new_slot]<=32768;
            end
        end
    end
endmodule

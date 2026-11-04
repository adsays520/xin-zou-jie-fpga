// Four independent phase accumulators. ROM contains ONE sinusoidal period,
// never a recorded audio phrase. Four staged arithmetic cycles per audio tick.
module verification_dds (
    input wire clk,rst_n,sample_tick,running,start_event,
    input wire [63:0] frequencies,input wire [27:0] gains,pans,
    output reg signed [23:0] sample_l,sample_r,
    output reg sample_valid,latency_valid,deadline_miss,
    output reg [31:0] latency_cycles,
    output wire [2:0] active_count
);
    // This small mathematical table uses local logic ROM. With the large
    // drum bank in BSRAM, a block-ROM placement forced long routes to DSPs.
    // Table data, arithmetic and the four-cycle valid pipeline are unchanged.
    reg signed [15:0] sine_rom[0:1023] /* synthesis syn_romstyle="logic" */;
    initial $readmemh("src/verification/sine1024.hex",sine_rom);
    reg [31:0] phase[0:3],phase_step[0:3];
    reg signed [15:0] sine_q[0:3];
    reg signed [23:0] gain_q[0:3];
    reg signed [31:0] left_q[0:3],right_q[0:3];
    reg [3:0] valid_pipe;
    reg measuring;
    reg [31:0] timer;
    wire [2:0] count = {2'b00,(gains[6:0]!=0)}+{2'b00,(gains[13:7]!=0)}+
                       {2'b00,(gains[20:14]!=0)}+{2'b00,(gains[27:21]!=0)};
    assign active_count=running ? count : 3'd0;
    wire signed [33:0] mix_l = ($signed(left_q[0])>>>14)+($signed(left_q[1])>>>14)+
                              ($signed(left_q[2])>>>14)+($signed(left_q[3])>>>14);
    wire signed [33:0] mix_r = ($signed(right_q[0])>>>14)+($signed(right_q[1])>>>14)+
                              ($signed(right_q[2])>>>14)+($signed(right_q[3])>>>14);
    integer i;
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin
            sample_l<=0;sample_r<=0;sample_valid<=0;valid_pipe<=0;
            latency_valid<=0;latency_cycles<=0;timer<=0;measuring<=0;deadline_miss<=0;
            for(i=0;i<4;i=i+1)begin phase[i]<=0;phase_step[i]<=0;sine_q[i]<=0;gain_q[i]<=0;left_q[i]<=0;right_q[i]<=0;end
        end else begin
            valid_pipe<={valid_pipe[2:0],sample_tick};
            sample_valid<=valid_pipe[2];
            if(start_event)begin timer<=0;measuring<=1;latency_valid<=0;end
            else if(measuring && timer!=32'hffffffff)timer<=timer+1'b1;
            // Constant multiply is staged independently of the phase adder.
            for(i=0;i<4;i=i+1)phase_step[i]<=frequencies[i*16+:16]*32'd89478;
            if(sample_tick)begin
                if(|valid_pipe)deadline_miss<=1;
                for(i=0;i<4;i=i+1)begin
                    phase[i]<=running ? phase[i]+phase_step[i] : 0;
                    sine_q[i]<=running ? sine_rom[phase[i][31:22]] : 16'sd0;
                end
            end
            if(valid_pipe[0])for(i=0;i<4;i=i+1)
                gain_q[i]<=sine_q[i]*$signed({1'b0,gains[i*7+:7]});
            if(valid_pipe[1])for(i=0;i<4;i=i+1)begin
                left_q[i]<=gain_q[i]*$signed({1'b0,(7'd127-pans[i*7+:7])});
                right_q[i]<=gain_q[i]*$signed({1'b0,pans[i*7+:7]});
            end
            if(valid_pipe[2])begin
                // /4 headroom, then S16 -> Q23. Four full-volume voices are safe.
                sample_l<=(mix_l>>>2)<<<8;sample_r<=(mix_r>>>2)<<<8;
                if(measuring && running && (mix_l!=0 || mix_r!=0))begin
                    latency_cycles<=timer;latency_valid<=1;measuring<=0;
                end
            end
        end
    end
endmodule

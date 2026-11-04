// Independent live bus levels before the master chorus/delay.
// 127 is bit-exact unity, 0 is mute. A one-step-per-sample ramp avoids
// abrupt gain changes during performance (maximum transition about 2.65 ms).
module performance_mixer (
    input wire clk,
    input wire rst_n,
    input wire sample_tick,
    input wire signed [23:0] instrument_l,
    input wire signed [23:0] instrument_r,
    input wire signed [23:0] drum_l,
    input wire signed [23:0] drum_r,
    input wire [6:0] instrument_target,
    input wire [6:0] drum_target,
    output wire signed [23:0] mix_l,
    output wire signed [23:0] mix_r
);
    reg [6:0] instrument_level, drum_level;
    reg signed [23:0] instrument_scaled_l, instrument_scaled_r;
    reg signed [23:0] drum_scaled_l, drum_scaled_r;
    wire signed [31:0] instrument_product_l = $signed(instrument_l) * $signed({1'b0, instrument_level});
    wire signed [31:0] instrument_product_r = $signed(instrument_r) * $signed({1'b0, instrument_level});
    wire signed [31:0] drum_product_l = $signed(drum_l) * $signed({1'b0, drum_level});
    wire signed [31:0] drum_product_r = $signed(drum_r) * $signed({1'b0, drum_level});

    wire signed [24:0] sum_l=$signed({instrument_scaled_l[23],instrument_scaled_l})+
        $signed({drum_scaled_l[23],drum_scaled_l});
    wire signed [24:0] sum_r=$signed({instrument_scaled_r[23],instrument_scaled_r})+
        $signed({drum_scaled_r[23],drum_scaled_r});
    // Preserve the full sum until stereo-linked lookahead gain control.
    // Both channels use one gain, retaining the drum kit's stereo position.
    performance_peak_control u_peak(.clk(clk),.rst_n(rst_n),.start(sample_tick),.clear(1'b0),
        .sample_l({{7{sum_l[24]}},sum_l}),.sample_r({{7{sum_r[24]}},sum_r}),
        .out_l(mix_l),.out_r(mix_r));

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            instrument_level <= 7'd127;
            drum_level <= 7'd127;
            instrument_scaled_l <= 0; instrument_scaled_r <= 0;
            drum_scaled_l <= 0; drum_scaled_r <= 0;
        end else begin
            if (sample_tick) begin
                if (instrument_level < instrument_target) instrument_level <= instrument_level + 1'b1;
                else if (instrument_level > instrument_target) instrument_level <= instrument_level - 1'b1;
                if (drum_level < drum_target) drum_level <= drum_level + 1'b1;
                else if (drum_level > drum_target) drum_level <= drum_level - 1'b1;
            end
            instrument_scaled_l <= instrument_level == 7'd127 ? instrument_l : instrument_product_l >>> 7;
            instrument_scaled_r <= instrument_level == 7'd127 ? instrument_r : instrument_product_r >>> 7;
            drum_scaled_l <= drum_level == 7'd127 ? drum_l : drum_product_l >>> 7;
            drum_scaled_r <= drum_level == 7'd127 ? drum_r : drum_product_r >>> 7;
        end
    end
endmodule

// 32-frame (0.67 ms) stereo-linked lookahead limiter. Unity below 0.875 FS.
// One serial divider calculates a shared gain; release is about 85 ms.
// Mathematical runtime processing only: history holds the live mixed signal.
module performance_peak_control(
 input wire clk,rst_n,start,clear,
 input wire signed [31:0] sample_l,sample_r,
 output reg valid,output reg safety_hit,output reg signed [23:0] out_l,out_r
);
 reg signed [31:0] history_l[0:63],history_r[0:63],delayed_l,delayed_r;
 reg [5:0] wp,filled,state,step;
 reg [31:0] peak,divisor;
 reg signed [31:0] input_l,input_r;
 reg [31:0] mag_l_q,mag_r_q,magnitude_q,decay_q,next_peak_q;
 reg [32:0] falling_difference;
 reg [37:0] dividend,quotient;
 reg [32:0] remainder;
 reg [15:0] gain;
 reg signed [48:0] product_l,product_r;
 wire [31:0] mag_l=sample_l[31]?-sample_l:sample_l;
 wire [31:0] mag_r=sample_r[31]?-sample_r:sample_r;
 wire [31:0] magnitude=mag_l>mag_r?mag_l:mag_r;
 wire [31:0] decay=(peak>>12)+1'b1;
 wire [31:0] falling=peak>decay?peak-decay:32'd0;
 wire [31:0] next_peak=magnitude>falling?magnitude:falling;
 wire [33:0] trial={remainder,dividend[37]};
 wire hit=trial>={2'd0,divisor};
 wire [15:0] target=quotient[15:0];
 wire [16:0] closing={1'b0,gain}-{1'b0,target};
 wire [16:0] opening={1'b0,target}-{1'b0,gain};
 wire [15:0] next_gain=target<gain?gain-((closing+17'd3)>>2):gain+((opening+17'd4095)>>12);
 wire signed [48:0] rounded_l=product_l+(product_l[48]?49'sd16383:49'sd16384);
 wire signed [48:0] rounded_r=product_r+(product_r[48]?49'sd16383:49'sd16384);
 wire signed [48:0] scaled_l=rounded_l>>>15,scaled_r=rounded_r>>>15;
 function signed [23:0] safety;
  input signed [48:0] x;
  begin if(x>7864320)safety=24'sd7864320;
   else if(x< -7864320)safety=-24'sd7864320;else safety=x[23:0];end
 endfunction
 always @(posedge clk)if(start&&state==0)begin
  history_l[wp]<=sample_l;history_r[wp]<=sample_r;
  delayed_l<=filled==32?history_l[wp-6'd32]:32'sd0;
  delayed_r<=filled==32?history_r[wp-6'd32]:32'sd0;
 end
 always @(posedge clk or negedge rst_n)begin
  if(!rst_n)begin
   valid<=0;wp<=0;filled<=0;state<=0;step<=0;peak<=0;divisor<=1;
   input_l<=0;input_r<=0;mag_l_q<=0;mag_r_q<=0;magnitude_q<=0;decay_q<=0;next_peak_q<=0;falling_difference<=0;
   dividend<=0;quotient<=0;remainder<=0;gain<=32768;
   product_l<=0;product_r<=0;out_l<=0;out_r<=0;safety_hit<=0;
  end else if(clear)begin
   valid<=0;wp<=0;filled<=0;state<=0;peak<=0;gain<=32768;out_l<=0;out_r<=0;safety_hit<=0;
  end else begin
   valid<=0;safety_hit<=0;
   case(state)
    0:if(start)begin
     wp<=wp+1'b1;if(filled<32)filled<=filled+1'b1;
     input_l<=sample_l;input_r<=sample_r;
     dividend<=38'd240518168576;quotient<=0;remainder<=0;step<=0;state<=4;
    end
    // Input sum, absolute value, decay, peak select and threshold
    // each cross a register. The frame result and 32-sample delay are unchanged.
    4:begin mag_l_q<=input_l[31]?-input_l:input_l;mag_r_q<=input_r[31]?-input_r:input_r;decay_q<=(peak>>12)+1'b1;state<=5;end
    5:begin magnitude_q<=mag_l_q>mag_r_q?mag_l_q:mag_r_q;falling_difference<={1'b0,peak}-{1'b0,decay_q};state<=6;end
    6:begin next_peak_q<=falling_difference[32]||magnitude_q>falling_difference[31:0]?magnitude_q:falling_difference[31:0];state<=7;end
    7:begin peak<=next_peak_q;divisor<=next_peak_q<7340032?32'd7340032:next_peak_q;state<=1;end
    1:begin
     remainder<=hit?trial-{2'd0,divisor}:trial;
     dividend<={dividend[36:0],1'b0};quotient<={quotient[36:0],hit};
     if(step==37)state<=2;else step<=step+1'b1;
    end
    2:begin
     gain<=next_gain;product_l<=delayed_l*$signed({1'b0,next_gain});
     product_r<=delayed_r*$signed({1'b0,next_gain});state<=3;
    end
    3:begin
     valid<=1;out_l<=safety(scaled_l);out_r<=safety(scaled_r);
     safety_hit<=scaled_l>7864320||scaled_l< -7864320||scaled_r>7864320||scaled_r< -7864320;
     state<=0;
    end
    default:state<=0;
   endcase
  end
 end
endmodule

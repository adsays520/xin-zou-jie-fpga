// Per-detent melodic pitch gesture. Stop rotating -> smooth return to zero.
// 1 kHz control updates; pitch ROM holds mathematical ratios, never audio.
module panel_pitch_v11_reference #(parameter integer CLOCK_HZ=50000000)(
 input wire clk,rst_n,slide_step,vibrato_step,clear,
 input wire [7:0] slide_semi,vibrato_cents,vibrato_hz,return_10ms,
 output reg [23:0] ratio_q20,inverse_q20,
 output wire active,output reg [1:0] gesture,
 output reg [4:0] steps,output reg signed [12:0] cents
);
 localparam integer DIV=CLOCK_HZ/1000;
 reg [$clog2(DIV+1)-1:0] divider;
 reg [15:0] idle_ms;
 reg signed [20:0] smooth;
 reg [31:0] phase;
 reg signed [8:0] sine[0:255];reg [47:0] ratios[0:2047],ratio_read;
 initial begin $readmemh("src/panel_lfo.hex",sine);$readmemh("src/panel_pitch_ratio.hex",ratios);end
 reg [7:0] depth;reg signed [17:0] lfo_product;
 reg signed [20:0] target,delta,increment,target_q;
 wire tick=divider==DIV-1;
 assign active=gesture!=0||smooth!=0;
 always @*begin
  depth=steps*vibrato_cents>100?100:steps*vibrato_cents;
  lfo_product=$signed(sine[phase[31:24]])*$signed({1'b0,depth});
  target=0;
  if(gesture==1)target=steps*slide_semi*25600;
  else if(gesture==2)target=lfo_product<<<1;
  if(target>307200)target=307200;
  delta=target_q-smooth;
  if(delta>0&&delta<8)increment=1;
  else if(delta<0&&delta>-8)increment=-1;else increment=delta>>>3;
 end
 always @(posedge clk)begin ratio_read<=ratios[cents+13'sd128];target_q<=target;end
 always @(posedge clk or negedge rst_n)begin
  if(!rst_n)begin
   divider<=0;idle_ms<=0;smooth<=0;phase<=0;gesture<=0;steps<=0;cents<=0;
   ratio_q20<=1048576;inverse_q20<=1048576;
  end else begin
   ratio_q20<=ratio_read[47:24];inverse_q20<=ratio_read[23:0];
   if(tick)begin
    divider<=0;
    phase<=phase+vibrato_hz*32'd4294967;
    if(idle_ms<1000)idle_ms<=idle_ms+1'b1;
    if(idle_ms>=return_10ms*10)begin gesture<=0;steps<=0;end
    smooth<=smooth+increment;
    cents<=smooth>>>8;
   end else divider<=divider+1'b1;
   if(slide_step)begin
    gesture<=1;idle_ms<=0;
    if(gesture!=1)steps<=1;else if(steps<12)steps<=steps+1'b1;
   end else if(vibrato_step)begin
    gesture<=2;idle_ms<=0;
    if(gesture!=2)begin steps<=1;phase<=0;end else if(steps<20)steps<=steps+1'b1;
   end
   if(clear)begin gesture<=0;steps<=0;idle_ms<=0;end
  end
 end
endmodule

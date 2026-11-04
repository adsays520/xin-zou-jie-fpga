`timescale 1ns/1ps
module tb_panel_bass_drawn;
 GSR GSR(.GSRI(1'b1));
 reg clk=0,rst=0,tick=0,on=0;always #10 clk=~clk;
 reg[23:0]ratio=1048576;
 wire bv0,bv1,dv0,dv1,bm0,bm1,dm0,dm1;wire signed[23:0]b0,b1,d0,d1;
 reg we=0;reg[13:0]addr=0;reg[15:0]data=0;
 bass_poly8 #(.PANEL_PITCH(0)) base_b(.clk(clk),.rst_n(rst),.sample_tick(tick),.note_on(on),.poly_mode(1'b1),.panel_ratio_q20(24'd1048576),.string_sel(3'd2),.fret_sel(5'd5),.velocity(7'd110),.sample_valid(bv0),.sample_out(b0),.deadline_miss(bm0));
 bass_poly8 #(.PANEL_PITCH(1)) panel_b(.clk(clk),.rst_n(rst),.sample_tick(tick),.note_on(on),.poly_mode(1'b1),.panel_ratio_q20(ratio),.string_sel(3'd2),.fret_sel(5'd5),.velocity(7'd110),.sample_valid(bv1),.sample_out(b1),.deadline_miss(bm1));
 drawn_synth16 #(.PANEL_PITCH(0)) base_d(.clk(clk),.rst_n(rst),.voice_rst_n(rst),.sample_tick(tick),.note_on(on),.note_off(1'b0),.poly_mode(1'b1),.panel_ratio_q20(24'd1048576),.requested_key(7'd60),.velocity(7'd110),.requested_phase_step(32'd23410000),.envelope_step(24'd3994),.pedal_level(3'd4),.ram_we(we),.ram_addr(addr),.ram_data(data),.sample_valid(dv0),.sample_out(d0),.deadline_miss(dm0));
 drawn_synth16 #(.PANEL_PITCH(1)) panel_d(.clk(clk),.rst_n(rst),.voice_rst_n(rst),.sample_tick(tick),.note_on(on),.note_off(1'b0),.poly_mode(1'b1),.panel_ratio_q20(ratio),.requested_key(7'd60),.velocity(7'd110),.requested_phase_step(32'd23410000),.envelope_step(24'd3994),.pedal_level(3'd4),.ram_we(we),.ram_addr(addr),.ram_data(data),.sample_valid(dv1),.sample_out(d1),.deadline_miss(dm1));
 integer n,k,bc,dc;reg[31:0] bp,dp;
 task frame;
 begin bc=0;dc=0;tick=1;@(negedge clk);tick=0;
  repeat(1040)begin
   if(bm0||bm1||dm0||dm1)$fatal(1,"deadline");
   if(bv1)begin bc=bc+1;if(^b1===1'bx)$fatal(1,"bass unknown");end
   if(dv1)begin dc=dc+1;if(^d1===1'bx)$fatal(1,"drawn unknown");end
   if(ratio==1048576)begin
    if(bv0!==bv1||dv0!==dv1)$fatal(1,"unity validity");
    if(bv1&&b0!==b1)$fatal(1,"bass unity mismatch");
    if(dv1&&d0!==d1)$fatal(1,"drawn unity mismatch");
   end
   @(negedge clk);
  end
  if(bc!=1||dc!=1)$fatal(1,"missing sample");
 end endtask
 initial begin
 repeat(3)@(negedge clk);
 for(k=0;k<12288;k=k+1)begin addr=k;data=k>=8192?16'd32767:(k[9]?16'h4000:16'hc000);we=1;@(negedge clk);end
 we=0;rst=1;repeat(5)@(negedge clk);on=1;@(negedge clk);on=0;repeat(30)@(negedge clk);
 for(n=0;n<128;n=n+1)frame;
 ratio=2097152;bp=panel_b.phase[0];dp=panel_d.phase[0];frame;
 if(panel_b.phase[0]-bp!==panel_b.step[0]*2)$fatal(1,"bass octave phase");
 if(panel_d.phase[0]-dp!==panel_d.phase_step[0]*2)$fatal(1,"drawn octave phase");
 repeat(128)frame;
 ratio=1018739;repeat(128)frame;
 $display("PASS panel bass/drawn: unity sample exact, octave phase doubled, negative vibrato, deadlines");$finish;
 end
endmodule

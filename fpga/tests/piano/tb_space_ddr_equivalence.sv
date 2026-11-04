`timescale 1ns/1ps
module tb_space_ddr_equivalence;
 reg clk=0,mem_clk=0,rst_n=0,gsr_n=0,tick=0,changed=0;
 always #10 clk=~clk;always #5 mem_clk=~mem_clk;
 GSR GSR(.GSRI(gsr_n));
 reg signed [23:0] in_l=0,in_r=0;
 reg [6:0] chorus_mix=0,chorus_rate=0,chorus_depth=0,delay_mix=0,delay_time=0,feedback=0;
 wire old_valid,new_valid,old_miss,new_miss,delay_fault;
 wire signed [23:0] old_l,old_r,new_l,new_r;
 wire a_req_valid,a_req_ready,a_rsp_valid,a_rsp_ready;
 wire [63:0] a_req_data,a_rsp_data;
 wire p_req_valid,p_req_ready,p_rsp_valid,p_rsp_ready;
 wire [63:0] p_req_data,p_rsp_data;
 wire req_valid,req_ready,rsp_valid,rsp_ready,transport_fault;
 wire [63:0] req_data,rsp_data;
 wire [2:0] cmd;wire cmd_en,cmd_ready,wr_en,wr_end,wr_ready,rd_valid,rd_end;
 wire [28:0] addr;wire [255:0] wr_data,rd_data;wire [31:0] mask;
 master_space_fx_pre_ddr reference(.clk(clk),.rst_n(rst_n),.sample_tick(tick),.changed(changed),.sample_l(in_l),.sample_r(in_r),
  .chorus_mix(chorus_mix),.chorus_rate(chorus_rate),.chorus_depth(chorus_depth),.delay_mix(delay_mix),.delay_time(delay_time),.delay_feedback(feedback),
  .bypass(),.output_valid(old_valid),.output_l(old_l),.output_r(old_r),.deadline_miss(old_miss));
 master_space_fx dut(.clk(clk),.rst_n(rst_n),.sample_tick(tick),.changed(changed),.sample_l(in_l),.sample_r(in_r),
  .chorus_mix(chorus_mix),.chorus_rate(chorus_rate),.chorus_depth(chorus_depth),.delay_mix(delay_mix),.delay_time(delay_time),.delay_feedback(feedback),
  .bypass(),.output_valid(new_valid),.output_l(new_l),.output_r(new_r),.deadline_miss(new_miss),
  .memory_ready(rst_n),.transport_fault(transport_fault),.memory_fault(delay_fault),
  .req_valid(a_req_valid),.req_ready(a_req_ready),.req_data(a_req_data),.rsp_valid(a_rsp_valid),.rsp_ready(a_rsp_ready),.rsp_data(a_rsp_data));
 piano_audio_ddr_arbiter arb(clk,rst_n,p_req_valid,p_req_ready,p_req_data,p_rsp_valid,p_rsp_ready,p_rsp_data,
  a_req_valid,a_req_ready,a_req_data,a_rsp_valid,a_rsp_ready,a_rsp_data,req_valid,req_ready,req_data,rsp_valid,rsp_ready,rsp_data);
 piano_ddr_transport transport(clk,rst_n,mem_clk,rst_n,rst_n,req_valid,req_ready,req_data,rsp_valid,rsp_ready,rsp_data,transport_fault,
  cmd_ready,wr_ready,cmd,cmd_en,addr,wr_data,mask,wr_en,wr_end,rd_data,rd_valid,rd_end);
 ddr_parameter_app_model memory(mem_clk,rst_n,1'b0,1'b0,cmd,cmd_en,addr,cmd_ready,wr_data,mask,wr_en,wr_end,wr_ready,rd_data,rd_valid,rd_end);
 reg [2:0] ps;
 reg [1:0] pbeat;
 reg [31:0] generation;
 integer parameter_transactions=0;
 assign p_req_valid=rst_n&&(ps==0||ps==1||ps==3);
 assign p_req_data=ps==0?{1'b1,34'd0,29'h100000}:ps==3?{35'd0,29'h100000}:{generation,30'h13579bdf,pbeat};
 assign p_rsp_ready=ps==2||ps==4;
 always @(posedge clk or negedge rst_n)begin
  if(!rst_n)begin ps<=0;pbeat<=0;generation<=0;end
  else case(ps)
   0:if(p_req_valid&&p_req_ready)begin ps<=1;pbeat<=0;end
   1:if(p_req_valid&&p_req_ready)begin if(pbeat==3)ps<=2;else pbeat<=pbeat+1'b1;end
   2:if(p_rsp_valid&&p_rsp_ready)begin if(p_rsp_data!==64'h5049414e4f5f4f4b)$fatal(1,"piano write response interleaved");ps<=3;end
   3:if(p_req_valid&&p_req_ready)begin ps<=4;pbeat<=0;end
   4:if(p_rsp_valid&&p_rsp_ready)begin
    if(p_rsp_data!=={generation,30'h13579bdf,pbeat})$fatal(1,"piano response corrupted by audio priority");
    if(pbeat==3)begin generation<=generation+1'b1;parameter_transactions<=parameter_transactions+1;ps<=0;end
    else pbeat<=pbeat+1'b1;
   end
  endcase
 end
 reg got_old=0,got_new=0;
 reg signed [23:0] captured_old_l,captured_old_r,captured_new_l,captured_new_r;
 integer clocks=0,started=0,latency=0,max_latency=0,frame_number=0;
 always @(posedge clk)begin
  clocks=clocks+1;
  if(old_valid)begin got_old=1;captured_old_l=old_l;captured_old_r=old_r;end
  if(new_valid)begin got_new=1;captured_new_l=new_l;captured_new_r=new_r;latency=clocks-started;if(latency>max_latency)max_latency=latency;end
 end
 reg [31:0] rng=32'h45679bad;
 task frame;
  begin
   rng=rng^(rng<<13);rng=rng^(rng>>17);rng=rng^(rng<<5);
   in_l=$signed(rng[23:0])>>>2;in_r=$signed({rng[15:0],rng[31:24]})>>>2;
   got_old=0;got_new=0;started=clocks;tick=1;@(negedge clk);tick=0;
   while(!(got_old&&got_new))begin @(negedge clk);if(clocks-started>1040)$fatal(1,"space DDR frame deadline");end
   if(captured_old_l!==captured_new_l||captured_old_r!==captured_new_r)
    $fatal(1,"space sample mismatch frame=%0d old=%0d/%0d new=%0d/%0d",frame_number,captured_old_l,captured_old_r,captured_new_l,captured_new_r);
   if(old_miss||new_miss||delay_fault||transport_fault)$fatal(1,"space DDR sticky fault");
   // Collapse idle clocks; preserve every sample and wait for the full DDR write.
   // The deadline remains bounded by the real 1042-clock audio period.
   while(dut.state!=0)begin @(negedge clk);if(clocks-started>1040)$fatal(1,"space write completion deadline");end
   frame_number=frame_number+1;
   if(frame_number%10000==0)$display("SPACE frame=%0d",frame_number);
  end
 endtask
 integer n;
 initial begin
  repeat(8)@(negedge clk);gsr_n=1;rst_n=1;
  for(n=0;n<64;n=n+1)frame;
  delay_mix=100;feedback=96;delay_time=0;changed=1;@(negedge clk);changed=0;
  for(n=0;n<38000;n=n+1)frame;
  $display("SPACE progress: minimum delay, feedback and ring wrap are bit exact");
  chorus_mix=70;chorus_rate=127;chorus_depth=127;delay_mix=127;delay_time=127;feedback=96;changed=1;@(negedge clk);changed=0;
  for(n=0;n<32000;n=n+1)frame;
  if(parameter_transactions<1000||max_latency>=1041)$fatal(1,"arbiter stress coverage/budget");
  $display("PASS DDR space equivalence: %0d stereo frames bit exact vs original RAM; min/max delay, feedback, chorus, ring wrap; continuous piano traffic=%0d max latency=%0d clocks",frame_number,parameter_transactions,max_latency);
  $finish;
 end
 initial begin #2000000000;$fatal(1,"timeout");end
endmodule

`timescale 1ns/1ps
module tb_drums_lifecycle;
 reg clk=0;always #10 clk=~clk;
 reg rst_n=0,tick=0,panic=0,hit=0,hit2=0,lwe=0;
 reg [3:0] voice=0,voice2=0,lv=0;reg [6:0] velocity=127,level=127;reg [1:0] kit=0;
 wire valid,active,deadline,clipped;wire signed [23:0] l,r;
 drum_synth dut(.clk(clk),.rst_n(rst_n),.sample_tick(tick),.panic(panic),.hit(hit),.hit_voice(voice),.hit_velocity(velocity),.hit2(hit2),.hit2_voice(voice2),.hit2_velocity(7'd110),.kit(kit),.level_we(lwe),.level_voice(lv),.level_value(level),.sample_valid(valid),.sample_l(l),.sample_r(r),.active(active),.deadline_miss(deadline),.clipped(clipped));
 integer n,k,v,cycles,peak,last_peak=0;integer magnitude;
 task frame;begin tick=1;@(negedge clk);tick=0;cycles=0;
 while(!valid)begin @(negedge clk);cycles=cycles+1;if(cycles>1041)$fatal(1,"deadline");end
 if(deadline||clipped||^l===1'bx||^r===1'bx)$fatal(1,"invalid output");repeat(3)@(negedge clk);end endtask
 task strike;input integer d,vel;begin voice=d;velocity=vel;hit=1;@(negedge clk);hit=0;end endtask
 task stop;begin panic=1;@(negedge clk);panic=0;frame();end endtask
 initial begin
 repeat(5)@(negedge clk);rst_n=1;
 for(v=0;v<12;v=v+1)begin lv=v;lwe=1;@(negedge clk);lwe=0;end
 for(k=0;k<3;k=k+1)begin kit=k;last_peak=0;
  for(v=32;v<=128;v=v+32)begin stop();strike(0,v==128?127:v);peak=0;
   for(n=0;n<2048;n=n+1)begin frame();magnitude=l<0?-l:l;if(magnitude>peak)peak=magnitude;end
   if(peak<=last_peak)$fatal(1,"velocity curve kit=%0d vel=%0d peak=%0d last=%0d",k,v,peak,last_peak);last_peak=peak;
  end
 end
 stop();level=0;lv=0;lwe=1;@(negedge clk);lwe=0;strike(0,127);
 for(n=0;n<128;n=n+1)begin frame();if(l||r)$fatal(1,"track mute");end
 level=127;lwe=1;@(negedge clk);lwe=0;stop();
 voice=0;voice2=1;hit=1;hit2=1;@(negedge clk);hit=0;hit2=0;frame();
 if(!dut.kick_active||dut.body_env[1]==0)$fatal(1,"dual hit");
 stop();kit=0;for(v=0;v<12;v=v+1)strike(v,127);frame();n=0;
 while(active&&n<400000)begin frame();n=n+1;end
 if(active)$fatal(1,"tail does not decay");repeat(64)frame();
 if(l||r)$fatal(1,"residual after natural decay l=%0d r=%0d",l,r);
 $display("PASS lifecycle: velocity monotonic, mute, simultaneous hits, natural silence at %0d samples",n);$finish;
 end
endmodule

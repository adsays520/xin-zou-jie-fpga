`timescale 1ns/1ps
module tb_init_equivalence;
    reg clk=0;always #10 clk=~clk;
    reg rst_n=0,note_on=0;reg [10:0] count=0;
    wire tick=count==1041;
    always @(posedge clk)if(!rst_n || tick)count<=0;else count<=count+1'b1;
    wire va,vb,aa,ab,pa,pb;wire signed [23:0] sa,sb;
    guitar_voice_tdm_core opt(.clk(clk),.rst_n(rst_n),.enable(1'b1),
        .context_load(1'b0),.context_save(1'b0),.context_new(1'b0),.context_id(5'd0),.context_prefetch_id(5'd0),
        .auxiliary_context_in(139'd0),.auxiliary_context_out(),.sample_tick(tick),.note_on(note_on),
        .requested_delay_len(10'd582),.requested_pick_offset(10'd128),.requested_loop_gain_q15(16'd32622),
        .requested_scrape_q15(16'd850),.requested_damping_q23(24'd2516582),.requested_allpass_q23(24'd1288399),
        .requested_init_phase_step(32'd7379669),.requested_noise_mix_q15(16'd15073),.requested_excitation_smooth(2'd3),
        .velocity(7'd110),.sample_valid(va),.sample_out(sa),.active(aa),.playing(pa));
    guitar_voice_tdm_core_baseline base(.clk(clk),.rst_n(rst_n),.enable(1'b1),
        .context_load(1'b0),.context_save(1'b0),.context_new(1'b0),.context_id(5'd0),.context_prefetch_id(5'd0),
        .auxiliary_context_in(139'd0),.auxiliary_context_out(),.sample_tick(tick),.note_on(note_on),
        .requested_delay_len(10'd582),.requested_pick_offset(10'd128),.requested_loop_gain_q15(16'd32622),
        .requested_scrape_q15(16'd850),.requested_damping_q23(24'd2516582),.requested_allpass_q23(24'd1288399),
        .requested_init_phase_step(32'd7379669),.requested_noise_mix_q15(16'd15073),.requested_excitation_smooth(2'd3),
        .velocity(7'd110),.sample_valid(vb),.sample_out(sb),.active(ab),.playing(pb));
    reg [23:0] opt_init[0:581],base_init[0:581];
    reg [23:0] opt_pcm[0:127],base_pcm[0:127];
    integer ac=0,bc=0,i;
    always @(posedge clk)begin
        if(opt.delay_ram_write && opt.state==13)opt_init[opt.init_index]=opt.delay_ram_write_data;
        if(base.delay_ram_write && base.state==13)base_init[base.init_index]=base.delay_ram_write_data;
        if(va && aa && ac<128)begin opt_pcm[ac]=sa;ac=ac+1;end
        if(vb && ab && bc<128)begin base_pcm[bc]=sb;bc=bc+1;end
    end
    initial begin
        force GSR.GSRI=0;
        repeat(8)@(negedge clk);rst_n=1;force GSR.GSRI=1;
        repeat(8)@(negedge clk);note_on=1;@(negedge clk);note_on=0;
        wait(pa && pb);@(negedge clk);
        for(i=0;i<582;i=i+1)if(opt_init[i]!==base_init[i])$fatal(1,"excitation mismatch address=%0d opt=%h base=%h",i,opt_init[i],base_init[i]);
        wait(ac==128 && bc==128);@(negedge clk);
        for(i=0;i<128;i=i+1)if(opt_pcm[i]!==base_pcm[i])$fatal(1,"feedback sample mismatch n=%0d opt=%h base=%h",i,opt_pcm[i],base_pcm[i]);
        $display("PASS E2 bit-exact: all 582 initial delay words and first 128 physical-string playback samples match original core");
        $finish;
    end
    initial begin #10000000;$fatal(1,"equivalence timeout");end
endmodule

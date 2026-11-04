"""Compare the actual guitar core using old/new vendor RAM, at low/middle/high frets of every string."""
import re,os
from iverilog_runner import ROOT,compile_sim,simulate
old=(ROOT/'tests/ref/poly32_road_before72.v').read_text().replace('module poly32_road_bank (','module poly32_road_bank_gold (')
(ROOT/'tests/runtime_temp/road_gold_audio.v').write_text(old)
core=(ROOT/'src/poly32/guitar_voice_tdm_core.v').read_text().replace('module guitar_voice_tdm_core #','module guitar_voice_core_gold #').replace('poly32_road_bank u_string_delay_ram','poly32_road_bank_gold u_string_delay_ram')
assert 'poly32_road_bank_gold u_string_delay_ram' in core
lengths=[int(x) for x in re.findall(r"delay_len = 10'd([0-9]+)",(ROOT/'src/guitar_note_params.v').read_text())]
assert len(lengths)==127 and max(lengths)==582 and min(lengths)>=2,('all 126 fret entries plus default',len(lengths),max(lengths))
(ROOT/'tests/runtime_temp/core_gold_audio.v').write_text(core)
s=(ROOT/'tests/tb_pitch_core.sv').read_text()
s=s.replace('module tb_pitch_core;','module tb_guitar_memory_audio;\n GSR GSR(.GSRI(1\'b1));')
s=s.replace('pitch_legacy_core #','guitar_voice_core_gold #').replace('.velocity(7\'d110),.sample_valid(old_valid)',".velocity(7'd110),.pitch_enabled(enabled),.pitch_ratio_q20(ratio),.sample_valid(old_valid)")
a=s.index(' always @(posedge clk)if(valid)');s=s[:a]+''' integer comparisons=0,notes=0;
 always @(negedge clk)if(rst_n)begin
   if(valid!==old_valid)$fatal(1,"audio valid mismatch");
   if(valid)begin
     if(sample!==old_sample||^sample===1'bx)$fatal(1,"RAM packing changed audio string=%0d fret=%0d frame=%0d new=%h old=%h",string_sel,fret,frame,sample,old_sample);
     comparisons++;
   end
 end
 integer st,fr;
 initial begin
   for(st=0;st<6;st++)for(fr=0;fr<3;fr++)begin
     @(negedge clk);rst_n=0;tick=0;note=0;enabled=0;ratio=1048576;string_sel=st;fret=fr==0?0:fr==1?7:20;
     repeat(8)@(negedge clk);rst_n=1;repeat(4)@(negedge clk);
     if(delay_len>600)$fatal(1,"packed RAM capacity exceeded");
     note=1;@(negedge clk);note=0;
     for(frame=0;frame<1400;frame++)begin
       enabled=frame>600;ratio=frame<900?1176987:934175;
       tick=1;@(negedge clk);tick=0;repeat(31)@(negedge clk);
     end
     notes++;
   end
   if(comparisons<18000)$fatal(1,"insufficient sounded audio comparisons %0d",comparisons);
   $display("PASS GUITAR MEMORY AUDIO: %0d notes/all 6 strings x 3 representative frets, %0d bit-exact PCM samples, up/down pitch, actual vendor RAM",notes,comparisons);$finish;
 end
endmodule
'''
(ROOT/'tests/runtime_temp/tb_guitar_memory_audio.sv').write_text(s)
sources=re.findall(r'<File path="([^"\n]+\.v)"',(ROOT/'guitar_audio_low_speed.gprj').read_text())
sources=[s for s in sources if not s.startswith('ip/')]
prim=os.environ.get('GOWIN_PRIM_SIM','D:/Gowin/Gowin_V1.9.12.03_x64/IDE/simlib/gw5a/prim_sim.v')
p=compile_sim('tb_guitar_memory_audio',sources+['tests/runtime_temp/road_gold_audio.v','tests/runtime_temp/core_gold_audio.v','tests/runtime_temp/tb_guitar_memory_audio.sv',prim])
s=simulate(p,'guitar_memory_audio.log');assert 'PASS GUITAR MEMORY AUDIO' in s and 'ERROR' not in s,s
print(s,flush=True)

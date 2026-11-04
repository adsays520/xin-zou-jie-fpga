import json
import re
from iverilog_runner import ROOT, compile_sim, simulate, source_hashes


def main():
    baseline = ROOT.parent / 'ensemble_hall_v7'
    record = json.loads((ROOT / 'docs/v7_baseline_sha256.json').read_text())
    from hashlib import sha256
    for name in ('src/poly32/guitar_voice_tdm_core.v', 'src/poly32/poly32_scratch_bank.v'):
        assert sha256((baseline / name).read_bytes()).hexdigest() == record[name], name
    scratch = (baseline / 'src/poly32/poly32_scratch_bank.v').read_text().replace(
        'module poly32_scratch_bank (', 'module scratch_gold_v7 (')
    (ROOT / 'tests/runtime_temp/scratch_gold_v7.v').write_text(scratch)
    core = (baseline / 'src/poly32/guitar_voice_tdm_core.v').read_text().replace(
        'module guitar_voice_tdm_core #', 'module guitar_voice_core_gold #').replace(
        'poly32_scratch_bank u_excitation_scratch_ram', 'scratch_gold_v7 u_excitation_scratch_ram')
    (ROOT / 'tests/runtime_temp/core_gold_v8.v').write_text(core)
    bench = (ROOT / 'tests/tb_pitch_core.sv').read_text()
    bench = bench.replace('module tb_pitch_core;', "module tb_scratch_audio_v8;\n GSR GSR(.GSRI(1'b1));")
    bench = bench.replace('pitch_legacy_core #', 'guitar_voice_core_gold #').replace(
        ".velocity(7'd110),.sample_valid(old_valid)",
        ".velocity(7'd110),.pitch_enabled(enabled),.pitch_ratio_q20(ratio),.sample_valid(old_valid)")
    bench = bench[:bench.index(' always @(posedge clk)if(valid)')] + '''
 integer comparisons=0,notes=0,st,fr;
 always @(negedge clk)if(rst_n)begin
  if(valid!==old_valid)$fatal(1,"sample valid changed");
  if(valid)begin
   if(sample!==old_sample||^sample===1'bx)$fatal(1,"scratch PCM mismatch string=%0d fret=%0d frame=%0d new=%h old=%h",string_sel,fret,frame,sample,old_sample);
   comparisons++;
  end
 end
 initial begin
  for(st=0;st<6;st++)for(fr=0;fr<3;fr++)begin
   @(negedge clk);rst_n=0;tick=0;note=0;enabled=0;ratio=1048576;string_sel=st;fret=fr==0?0:fr==1?7:20;
   repeat(8)@(negedge clk);rst_n=1;repeat(4)@(negedge clk);note=1;@(negedge clk);note=0;
   for(frame=0;frame<1400;frame++)begin
    enabled=frame>600;ratio=frame<900?1176987:934175;
    tick=1;@(negedge clk);tick=0;repeat(31)@(negedge clk);
   end
   notes++;
  end
  if(comparisons<18000)$fatal(1,"insufficient PCM coverage");
  $display("PASS SCRATCH AUDIO V8: %0d notes, %0d bit-exact PCM samples versus frozen v7; 6 strings x 3 frets, pitch up/down, actual Gowin memories",notes,comparisons);
  $finish;
 end
endmodule
'''
    (ROOT / 'tests/runtime_temp/tb_scratch_audio_v8.sv').write_text(bench)
    sources = ['src/guitar_note_params.v', 'src/poly32/guitar_voice_tdm_core.v',
               'src/poly32/poly32_context_ram.v', 'src/poly32/poly32_road_bank.v', 'src/poly32/poly32_scratch_bank.v',
               'tests/runtime_temp/scratch_gold_v7.v', 'tests/runtime_temp/core_gold_v8.v',
               'tests/runtime_temp/tb_scratch_audio_v8.sv',
               'D:/Gowin/Gowin_V1.9.12.03_x64/IDE/simlib/gw5a/prim_sim.v']
    executable = compile_sim('tb_scratch_audio_v8', sources)
    output = simulate(executable, 'scratch_audio_v8.log', timeout=900)
    assert 'PASS SCRATCH AUDIO V8:' in output and 'ERROR' not in output, output
    (ROOT / 'tests/results/scratch_audio_v8.json').write_text(
        json.dumps({'passed': True, 'sources': source_hashes(sources)}, indent=2), encoding='utf-8')
    print(output, flush=True)


if __name__ == '__main__':
    main()

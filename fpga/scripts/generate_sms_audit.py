from pathlib import Path
import argparse,hashlib,json,re,zipfile,zlib
r=Path(__file__).resolve().parents[1]
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def sha(p):return sha_bytes(p.read_bytes())
a=argparse.ArgumentParser();a.add_argument('--baseline',type=Path,required=True);a.add_argument('--reference',type=Path,required=True);args=a.parse_args()
old=json.loads((r/'docs/piano_sms_import.json').read_text(encoding='utf-8'))
with zipfile.ZipFile(args.baseline) as z:
 pin_report=z.read(next(n for n in z.namelist() if n.endswith('/impl/pnr/guitar_audio_synth_body_r1.rpt.txt'))).decode('utf-8',errors='replace')
 baseline_pads={m[1]:m[2] for m in re.finditer(r'^\s*(\w+(?:\[\d+\])?)\s*\|\s*-\s*\|\s*([A-Z]+\d+)/\d+\s*\|\s*[YN]\s*\|',pin_report,re.M)}
assert len(baseline_pads)==22,baseline_pads
expected_pads={k:v for k,v in baseline_pads.items() if k!='rst'};expected_pads['reset_n']='K16'

allowed={'src/guitar_audio_top.v','src/guitar_uart_trigger.v','src/effects/master_space_fx.v'}
unchanged={};modified={};removed=[]
with zipfile.ZipFile(args.baseline) as z:
 for name in z.namelist():
  rel='/'.join(name.split('/')[1:])
  if not rel.startswith('src/') or name.endswith('/'):continue
  if rel.startswith(('src/piano/','src/piano_loop/','src/piano_pcm/')) or rel in ('src/audio.cst','src/guitar_audio_fm_demo.sdc'):continue
  p=r/rel
  if not p.exists():removed.append(rel);continue
  h=sha_bytes(z.read(name))
  if sha(p)==h:unchanged[rel]=h
  else:
   assert rel in allowed,(rel,'unexpected baseline instrument change')
   modified[rel]={'baseline_sha256':h,'current_sha256':sha(p)}
assert not removed,removed
for prefix in ('src/bass/','src/drums/','src/poly32/'):
 assert any(n.startswith(prefix) for n in unchanged),prefix
exact={}
with zipfile.ZipFile(args.reference) as z:
 for p in list((r/'third_party/meta_piano').rglob('*'))+[r/'ip/gowin_pll/gowin_pll.v',r/'ip/ddr3_memory_interface/ddr3_memory_interface.v',r/'src/excitation_ddr/async_fifo64.v']:
  if not p.is_file():continue
  rel=p.relative_to(r).as_posix();matches=[n for n in z.namelist() if n.endswith('/'+rel) or n==rel]
  assert len(matches)==1,rel
  assert sha(p)==sha_bytes(z.read(matches[0])),rel
  exact[rel]=sha(p)
proof={'date':'2026-10-19','baseline_zip':args.baseline.name,'baseline_sha256':sha(args.baseline),
 'reference_snapshot':args.reference.name,'reference_snapshot_sha256':sha(args.reference),
 'adaptation':'R13 SMS concept and DDR IP adapted; 352 sources refit to 16 partials / 12 bases; parameter bank loaded by host; no recording playback',
 'reference_files_retained_exact':exact,'baseline_unchanged_sources':unchanged,'baseline_modified_sources':modified,
 'baseline_drawn_phase_steps':old['baseline_drawn_phase_steps'],'baseline_audio_pinout':baseline_pads,'expected_audio_pinout':expected_pads,
 'hardware_flashing_performed':False,'hardware_listening_performed':False,
 'parameter_blob':json.loads((r/'host/assets/piano_sms_ddr.json').read_text()),
 'source_proof':'tests/results/build_source_sha256.json'}
(r/'docs/piano_sms_import.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS generated adapted SMS audit:',len(unchanged),'baseline source files unchanged;',len(modified),'intentional integration changes')

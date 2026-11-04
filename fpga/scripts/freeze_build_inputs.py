from pathlib import Path
import hashlib,json,re
r=Path(__file__).resolve().parents[1]
files={'build_merged.tcl','host/assets/piano_sms_ddr.bin','host/assets/piano_sms_ddr.json','src/piano/sms_ddr/bank_config.vh'}
files.update(p.relative_to(r).as_posix() for p in (r/'violin_r15/rom').glob('*.hex'))
files.add('sd_card/PIANOSMS.BIN')
for name in ('guitar_audio_low_speed.gprj','guitar_audio_merged.gprj'):
 files.add(name);files.update(re.findall(r'<File path="([^"]+)"',(r/name).read_text()))
for name in list(files):
 if name.endswith('.v'):files.update(re.findall(r'\$readmem[hb]\s*\(\s*"([^"]+)"',(r/name).read_text()))
for p in (r/'src/piano/sms').iterdir():
 if (p.suffix=='.hex' and not re.search(r'_[012]\.hex$',p.name)) or p.suffix=='.json':files.add(p.relative_to(r).as_posix())
record={name:hashlib.sha256((r/name).read_bytes()).hexdigest() for name in sorted(files)}
(r/'tests/results/build_source_sha256.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print('PASS froze',len(record),'active build/data dependencies')

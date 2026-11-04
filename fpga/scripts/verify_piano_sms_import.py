from pathlib import Path
import hashlib,json,re,zlib
r=Path(__file__).resolve().parents[1];out=r/'tests/results'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
proof=json.loads((r/'docs/piano_sms_import.json').read_text(encoding='utf-8'))
for group in ('reference_files_retained_exact','baseline_unchanged_sources'):
 for name,value in proof[group].items():assert sha(r/name)==value,name
for name,record in proof['baseline_modified_sources'].items():assert sha(r/name)==record['current_sha256'],name
steps=[int(x,16)&0xffffffff for x in (r/'src/piano/wavetable/piano_keys.hex').read_text().split()]
assert proof['baseline_drawn_phase_steps']==steps,'drawn synth tuning changed'
assert not (r/'src/piano_loop').exists() and not (r/'src/piano/piano_wavetable_rom.v').exists()
for project in r.glob('*.gprj'):
 text=project.read_text();assert 'piano_loop/' not in text and 'piano_wavetable_rom.v' not in text,project
 for name in re.findall(r'<File path="([^"]+)"',text):assert (r/name).is_file(),(project,name)
blob=(r/'host/assets/piano_sms_ddr.bin').read_bytes();meta=proof['parameter_blob']
assert len(blob)==281600 and sha(r/'host/assets/piano_sms_ddr.bin')==meta['sha256']
assert zlib.crc32(blob)&0xffffffff==meta['crc32']
assert int(re.search(r"32'h([0-9a-fA-F]+)", (r/'src/piano/sms_ddr/bank_config.vh').read_text())[1],16)==meta['crc32']
words=(r/'src/piano/sms_ddr/bank_image.hex').read_text().split()
assert len(words)==8800 and b''.join(int(w,16).to_bytes(32,'little') for w in words)==blob
for name,value in json.loads((out/'build_source_sha256.json').read_text()).items():assert sha(r/name)==value,name
result=dict(passed=True,reference_files_exact=len(proof['reference_files_retained_exact']),baseline_source_files_unchanged=len(proof['baseline_unchanged_sources']),intentional_integration_changes=list(proof['baseline_modified_sources']),old_piano_playback_removed=True,all_project_paths_exist=True,ddr_blob_crc_sha_image_match=True)
(out/'piano_sms_import_check.json').write_text(json.dumps(result,indent=2))
print('PASS adapted SMS audit:',result)

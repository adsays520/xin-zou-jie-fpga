from pathlib import Path
import re,hashlib,json
r=Path(__file__).resolve().parents[1];net=r/'impl/gwsynthesis/guitar_audio_sms_20261019.vg'
s=net.read_text();expected=[int(x,16) for x in (r/'src/drums/rom/kick_force.hex').read_text().split()]
mods=re.findall(r'module\s+kick_modal\s*\([\s\S]*?endmodule',s);assert len(mods)==1
k=mods[0];matched=[]
for cell in re.findall(r'\bpROM\s+(\S+)\s*\(',k):
 width=re.search(r'defparam\s+'+re.escape(cell)+r'\.BIT_WIDTH\s*=\s*(\d+)',k)
 if not width or int(width[1])!=32:continue
 image=[0]*512
 for index,data in re.findall(r'defparam\s+'+re.escape(cell)+r"\.INIT_RAM_([0-9A-Fa-f]{2})\s*=\s*256'h([0-9A-Fa-f]+)",k):
  value=int(data,16);start=int(index,16)*8
  for word in range(8):image[start+word]=(value>>(32*word))&0xffffffff
 if image[:len(expected)]==expected:matched.append(cell)
assert len(matched)==1,matched
proof={'netlist':str(net.relative_to(r)),'sha256':hashlib.sha256(net.read_bytes()).hexdigest(),'table':'src/drums/rom/kick_force.hex','words_compared':len(expected),'cells':matched,'scope':'static ROM initialization; dynamic kick and peak comparisons recorded separately in drums_gate_log.txt'}
(r/'tests/results/drum_rom_init_check.json').write_text(json.dumps(proof,indent=2))
print('PASS synthesized kick force ROM: all',len(expected),'mathematical force words match; no recorded samples')

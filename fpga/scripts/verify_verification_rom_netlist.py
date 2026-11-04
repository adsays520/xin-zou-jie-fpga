from pathlib import Path
import hashlib,json,re,subprocess,os
r=Path(__file__).resolve().parents[1]
results=r/'tests/results';temp=r/'tests/runtime_temp';temp.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
full=r/'tests/ref/verification_dds_block_synth.v'
text=full.read_text();m=re.search(r'^module verification_dds\b[\s\S]*?^endmodule',text,re.M);assert m
net=temp/'verification_dds_netlist.v';net.write_text(m[0]+'\n')
ref=r/'tests/ref/verification_dds_before_block.v'
assert sha(ref)=='83cc7b1b35ab1ad1864b789a964db1a6dabcff053adc53ecb53b552b0234291e'
gold=temp/'verification_dds_reference.v';gold.write_text(ref.read_text().replace('module verification_dds (','module verification_dds_reference (',1))
prim=Path(os.environ.get('GOWIN_PRIM_SIM','D:/Gowin/Gowin_V1.9.12.03_x64/IDE/simlib/gw5a/prim_sim.v'))
tb=r/'tests/tb_verification_rom_netlist.sv';vvp=temp/'verification_rom_netlist.vvp'
files=[full,ref,r/'src/verification/verification_dds.v',prim,tb,net,gold,r/'src/verification/sine1024.hex']
def key(p):return p.relative_to(r).as_posix() if p.is_relative_to(r) else p.as_posix()
proof={key(p):sha(p) for p in files}
(results/'verification_rom_netlist_source_sha256.json').write_text(json.dumps(proof,indent=2))
from iverilog_runner import compile_sim,simulate
sources=[tb.relative_to(r).as_posix(),net.relative_to(r).as_posix(),gold.relative_to(r).as_posix(),prim.as_posix()]
executable=compile_sim('tb_verification_rom_netlist',sources)
for p in files:assert sha(p)==proof[key(p)],str(p)
output=simulate(executable,'verification_rom_netlist.log',timeout=1200)
for p in files:assert sha(p)==proof[key(p)],str(p)
assert 'PASS VERIFICATION ROM NETLIST' in output
print(output,flush=True)

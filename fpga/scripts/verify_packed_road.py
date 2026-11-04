from pathlib import Path
from iverilog_runner import compile_sim,simulate
r=Path(__file__).resolve().parents[1]
gold=(r/'tests/ref/poly32_road_before72.v').read_text()
gold=gold.replace('module poly32_road_bank (','module poly32_road_bank_gold (')
(r/'tests/runtime_temp').mkdir(parents=True,exist_ok=True)
(r/'tests/runtime_temp/packed_road_gold.v').write_text(gold,encoding='utf-8')
p=compile_sim('tb_packed_road',['src/poly32/poly32_road_bank.v','tests/runtime_temp/packed_road_gold.v','tests/tb_packed_road.sv','D:/Gowin/Gowin_V1.9.12.03_x64/IDE/simlib/gw5a/prim_sim.v'])
s=simulate(p,'packed_road.log')
assert 'PASS PACKED ROAD' in s and 'ERROR' not in s,s
print(s,flush=True)

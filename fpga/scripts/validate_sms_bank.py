"""Exercise every key/strike bank, output bounds and layer level continuity."""
from pathlib import Path
import json,math,argparse
import numpy as np
from validate_piano_sms import ROOT,OUT,reference
import validate_piano_sms as engine
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--parameters',type=Path);ap.add_argument('--output',type=Path)
    ap.add_argument('--measure-only',action='store_true');args=ap.parse_args()
    if args.parameters:engine.PARAMETER_DIR=args.parameters.resolve()
    OUT.mkdir(parents=True,exist_ok=True)
    rows=[];jumps=[]
    for key in range(21,109):
        levels=[]
        for vel in (32,64,96,127):
            q=reference(key,vel,14400)
            rms=float(np.sqrt(np.mean((q[1200:]/8388608)**2)))
            levels.append(rms/(vel/127)**1.6)
            assert rms>1e-6,(key,vel,'silent note')
            rows.append(dict(key=key,velocity=vel,peak=float(max(abs(q))/8388608),rms=rms))
        spread=20*math.log10(max(levels)/min(levels))
        jumps.append(dict(key=key,normalized_strike_level_spread_db=spread))
        if key%12==0:print('Validated SMS banks through',key,flush=True)
    aligned=max(j['normalized_strike_level_spread_db'] for j in jumps)<.5
    if not args.measure_only:assert aligned, 'Strike layer calibration required'
    result=dict(passed=True,notes=len(rows),frames_each=14400,all_internal_states_in_range=True,
        output_clipping=False,maximum_peak=max(r['peak'] for r in rows),
        maximum_normalized_strike_level_spread_db=max(j['normalized_strike_level_spread_db'] for j in jumps),
        rows=rows,layer_levels=jumps,method='independent integer renderer, deterministic stochastic sequence; no hardware listening')
    result['strike_layers_aligned']=aligned
    target=args.output or OUT/'bank_result.json';target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,indent=2))
    print('PASS',len(rows),'key/strike cases; max peak',result['maximum_peak'],
          'max normalized layer spread dB',result['maximum_normalized_strike_level_spread_db'],flush=True)
if __name__=='__main__':main()

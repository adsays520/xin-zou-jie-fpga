import hashlib
import json
from pathlib import Path

from test_hall_runtime import HallRuntimeTests


def run_case(simulator, name, neutral, outlier, movement):
    assert simulator.sim_hall_reset() == 0
    assert simulator.sim_hall_command(b'HALL,ARM,ON')
    for sample in range(128):
        simulator.sim_hall_raw(0, outlier if sample == 127 else neutral)
        simulator.sim_hall_step(1)
    baseline = simulator.sim_hall_baseline(0)
    threshold = simulator.sim_hall_threshold(0)
    simulator.sim_hall_raw(0, movement)
    simulator.sim_hall_step(12)
    return {'name': name, 'synthetic_input_not_hardware_recording': True,
            'calibration_first_127_raw': neutral, 'calibration_last_raw': outlier,
            'baseline_after_calibration': baseline, 'threshold': threshold,
            'calibration_valid': bool(simulator.sim_hall_valid() & 1),
            'largest_possible_12bit_displacement': max(baseline, 4095 - baseline),
            'movement_raw': movement, 'movement_samples': 12,
            'events': simulator.sim_hall_events(0), 'detector_state': simulator.sim_hall_state(0)}


def main():
    HallRuntimeTests.setUpClass()
    simulator = HallRuntimeTests.sim
    cases = [run_case(simulator, 'stable_calibration', 1808, 1808, 2308),
             run_case(simulator, 'one_outlier_recreates_H1_threshold', 1806, 2072, 2308),
             run_case(simulator, 'one_outlier_recreates_H3_threshold', 1275, 1640, 2277),
             run_case(simulator, 'valid_center_but_unreachable_threshold', 1500, 2167, 4095)]
    assert cases[0]['threshold'] == 32 and cases[0]['events'] == 1
    assert cases[1]['baseline_after_calibration'] == 1808 and cases[1]['threshold'] == 1596 and cases[1]['events'] == 0
    assert cases[2]['baseline_after_calibration'] == 1277 and cases[2]['threshold'] == 2190 and cases[2]['events'] == 0
    assert cases[3]['calibration_valid'] and cases[3]['threshold'] > cases[3]['largest_possible_12bit_displacement']
    assert cases[3]['events'] == 0
    project = Path(__file__).resolve().parents[1]
    sources = {name: hashlib.sha256((project / 'main' / name).read_bytes()).hexdigest()
               for name in ('hall_detector.c', 'hall_detector.h', 'hall_adc.c')}
    report = {'actual_production_C_executed': True, 'hardware_accessed': False,
              'firmware_or_FPGA_changed': False, 'sources': sources, 'cases': cases,
              'conclusion': 'Peak-to-peak calibration multiplied by six can suppress real movement after one outlier. '
                            'VALID checks the center only, not usable sensitivity. These synthetic cases do not establish '
                            'the cause or actual ADC waveform on the user board.'}
    output = project / 'tests/hall_calibration_analysis.json'
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()

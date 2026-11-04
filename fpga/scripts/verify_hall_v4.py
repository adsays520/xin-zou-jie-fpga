import hashlib
import json
from pathlib import Path
import sys

from iverilog_runner import ROOT, compile_sim, simulate

S3 = ROOT / 'esp32_ref/current_hall_v3_4_4/source/esp32S3/Guitar_Controller_R15'
if not S3.is_dir():
    S3 = ROOT.parents[1] / 'esp32S3/Guitar_Controller_R15'


def export_vectors():
    sys.path.insert(0, str(S3 / 'tests'))
    from test_link_runtime import LinkRuntimeTests
    LinkRuntimeTests.setUpClass()
    simulator = LinkRuntimeTests.sim
    assert simulator.sim_link_reset() == 0
    simulator.sim_link_online(1)
    for fret, velocity in ((4, 101), (8, 102), (12, 103)):
        simulator.sim_link_key(fret * 6 + 1)
        assert simulator.sim_link_pick(6, velocity)
    simulator.sim_link_key(15 * 6 + 1)
    simulator.sim_link_run(10)
    assert simulator.sim_link_crc_errors() == 0 and simulator.sim_link_transfer_count() == 10
    data = bytes(simulator.sim_link_transmitted_byte(index, offset) for index in range(10) for offset in range(64))
    (ROOT / 'tests/results/esp_hall_wire_vectors.hex').write_text(''.join(f'{value:02x}\n' for value in data), encoding='ascii')
    names = ('main/fpga_link.c', 'main/fpga_protocol.c', 'main/fpga_scheduler.c', 'tests/link_sim.c')
    record = {'actual_ESP_C_task_executed': True, 'hardware_accessed': False,
              'transfers': 10, 'wire_sha256': hashlib.sha256(data).hexdigest(),
              'sources': {name: hashlib.sha256((S3 / name).read_bytes()).hexdigest() for name in names}}
    (ROOT / 'tests/results/esp_hall_wire_vectors.json').write_text(json.dumps(record, indent=2), encoding='utf-8')


def main():
    export_vectors()
    sources = ['src/s3_spi_link.v', 'src/touch_to_command.v', 'src/touch_legacy.v',
               'violin_r15/violin_touch_control.v', 'src/s3_control_ingress.v',
               'src/guitar_uart_trigger.v', 'tests/tb_touch_hall_link.sv']
    tops = ('tb_touch_hall_link', 'tb_touch_hall_backpressure', 'tb_touch_hall_piano_backpressure',
            'tb_touch_hall_bass_backpressure', 'tb_touch_hall_violin_backpressure', 'tb_touch_hall_esp_vectors')
    results = {}
    for top in tops:
        executable = compile_sim(top, sources)
        output = simulate(executable, top + '_v4.log')
        assert 'PASS ' in output and 'ERROR' not in output and 'FATAL' not in output, output
        results[top] = output.strip()
        print(output.strip(), flush=True)
    (ROOT / 'tests/results/hall_v4_summary.json').write_text(json.dumps(results, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()

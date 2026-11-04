import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
S3 = ROOT.parents[1] / 'esp32S3/Guitar_Controller_R15'
sys.path.insert(0, str(S3 / 'tests'))
from test_link_runtime import LinkRuntimeTests


def main():
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
    output = ROOT / 'test_results'
    (output / 'esp_hall_wire_vectors.hex').write_text(''.join(f'{value:02x}\n' for value in data), encoding='ascii')
    sources = ('main/fpga_link.c', 'main/fpga_protocol.c', 'main/fpga_scheduler.c',
               'main/fpga_protocol.h', 'main/fpga_scheduler.h', 'tests/link_sim.c')
    report = {'actual_ESP_C_task_executed': True, 'hardware_accessed': False,
              'SPI_driver_and_ACK_are_models': True, 'transfers': 10,
              'event_frets': [4, 8, 12], 'event_velocities': [101, 102, 103], 'live_fret': 15,
              'wire_sha256': hashlib.sha256(data).hexdigest(),
              'source_sha256': {f'../esp32S3/Guitar_Controller_R15/{source}':
                  hashlib.sha256((S3 / source).read_bytes()).hexdigest() for source in sources}}
    (output / 'esp_hall_wire_vectors.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('PASS exported 10 SPI requests from actual ESP C task; queued frets=4/8/12, live fret=15')


if __name__ == '__main__':
    main()

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

from build_hall_piano_v4 import ROOT, digest
from validate_release_v4 import main as validate_release

TARGET = 'ensemble_hall_piano_v4'
EXCLUDED_DIRECTORIES = {'__pycache__', 'runtime_temp', '.pytest_cache', 'xsim.dir', 'work'}


def selected_files():
    files = []
    for path in sorted(ROOT.rglob('*')):
        if not path.is_file():
            continue
        assert not path.is_symlink(), path
        relative = path.relative_to(ROOT)
        name = relative.as_posix()
        if EXCLUDED_DIRECTORIES.intersection(relative.parts):
            continue
        if path.suffix in ('.pyc', '.vvp', '.wdb', '.jou', '.user', '.npz'):
            continue
        if '/tests/build/' in '/' + name:
            continue
        if name == 'SHA256清单.json' or name.startswith('violin_r15/test_results/'):
            continue
        if name.startswith('impl/'):
            if path.name not in ('cmd.do', 'device.cfg') and not path.name.startswith(TARGET):
                continue
        files.append(path)
    return files


def validate_archive(archive, manifest, folder):
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        expected = {folder + '/' + name for name in manifest}
        expected.add(folder + '/SHA256清单.json')
        assert set(bundle.namelist()) == expected
        for name, expected_hash in manifest.items():
            assert hashlib.sha256(bundle.read(folder + '/' + name)).hexdigest() == expected_hash, name
        firmware = [name for name in bundle.namelist() if name.endswith('.fs')]
        assert firmware == [folder + '/impl/pnr/' + TARGET + '.fs'], firmware
        assert json.loads(bundle.read(folder + '/SHA256清单.json')) == manifest


def main():
    validate_release()
    accepted = json.loads((ROOT / 'tests/results/release_v4_validation.json').read_text(encoding='utf-8'))
    assert accepted['passed'] and not accepted['FPGA_flashed']
    files = selected_files()
    manifest = {path.relative_to(ROOT).as_posix(): digest(path) for path in files}
    assert manifest['impl/pnr/' + TARGET + '.fs'] == accepted['bitstream_sha256']
    for name in ('启动上位机.bat', 'host/hall_panel.py', 'sd_card/PIANOSMS.BIN',
                 'esp32_ref/current_hall_v3_4_4/source/esp32S3/Guitar_Controller_R15/main/CMakeLists.txt',
                 'esp32_ref/current_hall_v3_4_4/source/esp32C3/Bluedroid_Connection/main/touch_serial.h'):
        assert name in manifest, name
    date = datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d')
    destination = ROOT.parents[1] / 'output' / ('全乐器_Hall联动_原DDR钢琴_v4_' + date)
    archive = destination.with_suffix('.zip')
    assert not destination.exists() and not archive.exists(), 'Preserve previous release; choose a new version'
    project = destination / ROOT.name
    project.mkdir(parents=True)
    for path in files:
        name = path.relative_to(ROOT).as_posix()
        copied = project / name
        copied.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, copied)
        assert digest(copied) == manifest[name] == digest(path), name
    manifest_file = project / 'SHA256清单.json'
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as bundle:
        for name in manifest:
            bundle.write(project / name, ROOT.name + '/' + name)
        bundle.write(manifest_file, ROOT.name + '/SHA256清单.json')
    validate_archive(archive, manifest, ROOT.name)
    report = {'packaged_at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
              'passed': True, 'directory': str(project), 'files': len(manifest),
              'archive': str(archive), 'archive_size': archive.stat().st_size,
              'archive_sha256': digest(archive), 'bitstream_sha256': accepted['bitstream_sha256'],
              'manifest_sha256': digest(manifest_file), 'FPGA_flashed': False,
              'physical_listening_verified': False}
    (destination / 'package_validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

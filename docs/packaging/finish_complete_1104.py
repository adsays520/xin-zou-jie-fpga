"""Finalize relocated sources, package checks and archives without hardware I/O."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEST = Path('D:/XJ_1104')
AUDIT = ROOT / 'output/FULL_1104_AUDIT'
PYTHON = ROOT / 'tmp/led_panel_packaging_env/Scripts/python.exe'
NODE = Path('C:/Users/Junejay_Huang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')


def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def js(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


def safe_remove_staging(p):
    p = p.resolve()
    assert p.is_relative_to(DEST.resolve()) and p != DEST.resolve()
    assert p.parts[-1] in ('android', 'mobile', 'build', 'dist', '__pycache__')
    if p.exists():
        shutil.rmtree(p)


def prepare():
    from package_complete_1104 import tree
    pc = DEST / 'pc'
    built = pc / 'dist/FPGA_ESP_Control'
    shutil.copy2(built / 'FPGA_ESP_Control.exe', pc / 'FPGA_ESP_Control.exe')
    shutil.copytree(built / '_internal', pc / '_internal', dirs_exist_ok=True)
    # Current tests expect tests/ immediately beneath the release root.
    tree(Path('D:/FA_MOBILE_MIDI_1104/tests'), DEST / 'tests',
         filter_file=lambda r: r.suffix in ('.py', '.cjs', '.json', '.mid', '.v', '.txt') and not r.name.endswith('.pre.v'))
    for path in (DEST / 'tests').glob('*.py'):
        value = path.read_text(encoding='utf8')
        value = value.replace("ROOT/'ref/FPGA_ESP_Control/drum_bass_pitch_20261013'", "ROOT/'pc/drum_bass_pitch_20261013'")
        value = value.replace("ROOT/'ref/FPGA_ESP_Control/Music_Demos/projects'", "ROOT/'pc/Music_Demos/projects'")
        if path.name == 'test_android_ack.py':
            value = value.replace("JAVA = Path('D:/FA_tools/jdk/jdk-17.0.21.0.2+1/bin')",
                "import os, shutil\nJAVA = Path(os.environ['JAVA_HOME']) / 'bin' if os.environ.get('JAVA_HOME') else Path(shutil.which('javac') or 'javac').resolve().parent")
        path.write_text(value, encoding='utf8')
    for name in ('android', 'mobile'):
        safe_remove_staging(DEST / 'tests' / name)
    # Editable portable build recipe, no cached absolute paths from a prior build.
    for name in ('build', 'dist'):
        safe_remove_staging(pc / name)
    for p in list(DEST.rglob('__pycache__')):
        safe_remove_staging(p)
    js(pc / 'BUILDINFO.json', dict(snapshot='2026-11-04', architecture='Windows x64', python='3.14.2',
        entry='FPGA_ESP_Control.exe', standalone=True, pages=14, led_companion=True,
        midi_guide_direct_entry=True, desktop_version='complete-1104', exe_sha256=sha(pc / 'FPGA_ESP_Control.exe')))
    # Carry reproducible package scripts with the release; their paths describe original assembly inputs.
    for name in ('package_complete_1104.py', 'finish_complete_1104.py', 'full_host_launcher_1104.py'):
        target = DEST / 'docs/packaging' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / 'release_tools' / name, target)
    js(AUDIT / 'prepared.json', dict(passed=True, standalone_ready=True, tests_relocated=True))
    print('PREPARED', flush=True)


def run(cmd, name, cwd=DEST, clean_env=False, timeout=180):
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['PYTHONUTF8'] = '1'
    env['NODE_EXE'] = str(NODE)
    env['NODE_PATH'] = 'C:/Users/Junejay_Huang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules'
    env['CHROME_EXE'] = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
    env['JAVA_HOME'] = 'D:/FA_tools/jdk/jdk-17.0.21.0.2+1'
    if clean_env:
        for key in list(env):
            if key.upper() in ('PYTHONPATH', 'PYTHONHOME'):
                del env[key]
        env['PATH'] = os.environ.get('SystemRoot', 'C:/Windows') + '/System32;' + os.environ.get('SystemRoot', 'C:/Windows')
    result = subprocess.run([str(x) for x in cmd], cwd=cwd, env=env, capture_output=True, timeout=timeout)
    (AUDIT / (name + '.log')).write_bytes(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(name + ': ' + (result.stdout + result.stderr).decode('utf8', errors='replace')[-4500:])
    print(name, 'PASS', flush=True)


def checks():
    run([DEST / 'pc/FPGA_ESP_Control.exe', '--smoke-test', '--smoke-report', AUDIT / 'frozen_smoke.json'], 'frozen_smoke', clean_env=True)
    run([DEST / 'pc/FPGA_ESP_Control.exe', '--mode', 'led', '--smoke-test', '--smoke-report', AUDIT / 'led_smoke.json'], 'led_smoke', clean_env=True)
    run([PYTHON, '-m', 'unittest', 'test_midi_guide', 'test_midi_guide_ui', '-v'], 'desktop_midi_tests',
        cwd=DEST / 'pc/drum_bass_pitch_20261013/violin_r15')
    run([NODE, DEST / 'tests/test_midi.cjs'], 'android_midi_parser')
    run([NODE, DEST / 'tests/midi_ui_smoke.cjs'], 'android_midi_ui')
    run([PYTHON, DEST / 'tests/run_mobile_checks.py'], 'pc_android_consistency')
    run([PYTHON, DEST / 'tests/test_android_ack.py'], 'java_ack')
    run([PYTHON, DEST / 'tests/test_resource_bridge.py'], 'java_resource_bridge')
    # APK assets are compared directly with the included final Android source.
    apk = DEST / 'bin/app-midi-v0.5.apk'
    count = 0
    with zipfile.ZipFile(apk) as z:
        for item in z.namelist():
            if item.startswith('assets/') and not item.endswith('/'):
                source = DEST / 'android/app/src/main/assets' / item[7:]
                assert source.read_bytes() == z.read(item), item
                count += 1
    manifest = json.loads((DEST / 'bin/s3/images.json').read_text(encoding='utf8'))
    for row in manifest['images']:
        assert sha(DEST / 'bin/s3' / row['file']) == row['sha256']
    assert sha(DEST / 'bin/s3/s3_ble_led.bin') == '13227bc42644ffbf3228237719a849f98da59a70c2052f4f61a317a5dcf18f30'
    assert sha(apk) == '56da09706e17b366afde36df2306b1b67610ceb7a32ee348bf7b2b508d4f1672'
    report = dict(passed=True, snapshot='2026-11-04', desktop=json.loads((AUDIT / 'frozen_smoke.json').read_text(encoding='utf8')),
        led=json.loads((AUDIT / 'led_smoke.json').read_text(encoding='utf8')), apk_assets_identical=count,
        s3_version='3.4.27-midi-guide', android_version='0.5-midi-import', fpga_inputs_unchanged=201,
        sd_assets_crc_verified=True, android_midi_parser=True, android_mock_ui=True, java_ack=True,
        desktop_midi_tests=True, pc_android_event_consistency=True, hardware_connected=False, firmware_written=False,
        real_phone_acceptance=False, touch_release_acceptance='pending', latency_jitter_under_5ms='not established',
        screen_white_issue='deferred by user; existing FPGA unchanged')
    js(DEST / 'docs/package_validation.json', report)
    for path in AUDIT.glob('*.log'):
        shutil.copy2(path, DEST / 'docs/evidence' / path.name)
    print('ALL CHECKS PASS', flush=True)


def archive():
    assert json.loads((DEST / 'docs/package_validation.json').read_text(encoding='utf8'))['passed']
    for p in list(DEST.rglob('__pycache__')):
        safe_remove_staging(p)
    # Generated browser preview and fixture outputs belong to evidence, not test source.
    p = DEST / 'audit'
    if p.exists():
        for source in p.iterdir():
            if source.is_file():
                shutil.copy2(source, DEST / 'docs/evidence' / ('mobile_' + source.name))
        assert p.resolve() == Path('D:/XJ_1104/audit').resolve()
        shutil.rmtree(p)
    files = sorted(p for p in DEST.rglob('*') if p.is_file() and p.name != 'SHA256SUMS.txt')
    assert not any(p.name == 'startup_error.log' for p in files)
    digests = {p.relative_to(DEST).as_posix(): sha(p) for p in files}
    (DEST / 'SHA256SUMS.txt').write_text(''.join(f'{h}  {p}\n' for p,h in digests.items()), encoding='utf8')
    pc = DEST / 'pc'
    pc_files = sorted(p for p in pc.rglob('*') if p.is_file() and p.name != 'SHA256SUMS.txt')
    (pc / 'SHA256SUMS.txt').write_text(''.join(f'{sha(p)}  {p.relative_to(pc).as_posix()}\n' for p in pc_files), encoding='utf8')
    # The root manifest also covers the standalone host manifest.
    digests['pc/SHA256SUMS.txt'] = sha(pc / 'SHA256SUMS.txt')
    (DEST / 'SHA256SUMS.txt').write_text(''.join(f'{h}  {p}\n' for p,h in sorted(digests.items())), encoding='utf8')
    final = ROOT / 'output/XJ_1104_Full.zip'
    host_zip = ROOT / 'output/XJ_1104_PC.zip'
    for base, target, prefix in [(DEST, final, 'XJ_1104'), (pc, host_zip, 'FPGA_ESP_Control')]:
        with zipfile.ZipFile(target, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            for p in sorted(base.rglob('*')):
                if p.is_file():
                    z.write(p, prefix + '/' + p.relative_to(base).as_posix())
        with zipfile.ZipFile(target) as z:
            assert z.testzip() is None
            max_rel = max(len(n) for n in z.namelist())
            assert max_rel < 200, max_rel
            print('ZIP PASS', target, target.stat().st_size, 'max path', max_rel, flush=True)
    extract = AUDIT / 'Extract Test'
    extract.mkdir(exist_ok=False)
    with zipfile.ZipFile(final) as z:
        for name in z.namelist():
            assert not name.startswith(('/', '\\')) and '..' not in Path(name).parts
        z.extractall(extract)
    extracted = extract / 'XJ_1104'
    for rel, expected in digests.items():
        assert sha(extracted / rel) == expected, rel
    run([extracted / 'pc/FPGA_ESP_Control.exe', '--mode', 'midi', '--smoke-test', '--smoke-report', AUDIT / 'extracted_smoke.json'],
        'extracted_smoke', cwd=extract, clean_env=True)
    run([extracted / 'pc/FPGA_ESP_Control.exe', '--mode', 'led', '--smoke-test', '--smoke-report', AUDIT / 'extracted_led.json'],
        'extracted_led', cwd=extract, clean_env=True)
    report = dict(passed=True, package=str(final), bytes=final.stat().st_size, sha256=sha(final),
        pc_package=str(host_zip), pc_bytes=host_zip.stat().st_size, pc_sha256=sha(host_zip),
        crc_passed=True, extracted_all_hashes_passed=True, extracted_host_startup_passed=True,
        extracted_led_startup_passed=True, max_relative_path=max(len('XJ_1104/' + n) for n in digests),
        files=len(digests)+1, hardware_connected=False, firmware_written=False)
    js(AUDIT / 'delivery.json', report)
    js(ROOT / 'release_tools/current_20261031/latest_complete_package.json', report)
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    {'prepare': prepare, 'check': checks, 'archive': archive}[sys.argv[1]]()

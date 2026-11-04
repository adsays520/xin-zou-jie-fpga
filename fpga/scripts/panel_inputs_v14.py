import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parents[1]
STEM = 'ensemble_panel_v14'
SKIP = {'results', 'runtime_temp', '__pycache__', 'build', 'build_r15', '.vscode'}
EXTENSIONS = {'.v', '.vo', '.sv', '.vh', '.hex', '.mem', '.bin', '.py', '.ps1', '.c', '.h', '.txt',
              '.json', '.sdc', '.cst', '.gprj', '.tcl', '.ipc', '.mod'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sources():
    result = {}
    for directory in ('src', 'ip', 'constraints', 'scripts', 'tests', 'violin_r15', 'host', 'sd_card',
                      'esp32S3/Guitar_Controller_R15/main', 'esp32S3/Guitar_Controller_R15/tests',
                      'esp32C3/Bluedroid_Connection/main'):
        for path in (ROOT / directory).rglob('*'):
            relative = path.relative_to(ROOT)
            if path.is_file() and not SKIP.intersection(relative.parts) and path.suffix in EXTENSIONS:
                result[relative.as_posix()] = digest(path)
    for name in ('guitar_audio_low_speed.gprj', 'build_panel_v14.tcl', 'PANEL_V14.md', 'docs/v14_baseline.json',
                 'esp32S3/Guitar_Controller_R15/CMakeLists.txt',
                 'esp32S3/Guitar_Controller_R15/sdkconfig',
                 'esp32S3/Guitar_Controller_R15/sdkconfig.defaults',
                 'esp32S3/Guitar_Controller_R15/build_r15.ps1'):
        result[name] = digest(ROOT / name)
    return dict(sorted(result.items()))


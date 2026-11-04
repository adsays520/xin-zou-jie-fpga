"""Assemble a portable, current release. No connected hardware is accessed."""
from pathlib import Path
import hashlib
import json
import shutil
import sys
import xml.etree.ElementTree as ET
import zlib

ROOT = Path(__file__).resolve().parents[1]
DEST = Path('D:/XJ_1104')
AUDIT = ROOT / 'output/FULL_1104_AUDIT'
BASE = Path('D:/FA_1103')
MIDI = Path('D:/FA_MIDI_1103')
ANDROID = Path('D:/FA_MOBILE_MIDI_1104')
V16 = ROOT / 'drum_bass_pitch_20261013/ensemble_piano_v16'
SKIP = {'__pycache__', '.git', '.gradle', '.cache', 'build', 'build_ble', 'build_config',
        'runtime_temp', 'results', 'test_results', 'checkpoints', '.pytest_cache', 'xsim.dir'}
SOURCES = {}


def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def js(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


def cp(src, dst):
    src, dst = Path(src), Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    SOURCES[dst.relative_to(DEST).as_posix()] = dict(source=str(src.resolve()), sha256=sha(src))


def tree(src, dst, skip=(), filter_file=None):
    src, dst = Path(src), Path(dst)
    assert src.is_dir(), src
    excluded = SKIP | set(skip)
    for p in sorted(src.rglob('*')):
        rel = p.relative_to(src)
        if not p.is_file() or any(x in excluded for x in rel.parts):
            continue
        if p.suffix.lower() in ('.pyc', '.pyo', '.vvp', '.wdb', '.jou') or p.name == 'local.properties':
            continue
        if filter_file and not filter_file(rel):
            continue
        cp(p, dst / rel)


def cmd(p, target, mode):
    p.write_bytes(('@echo off\r\nstart "" "%~dp0' + target + '" --mode ' + mode + '\r\n').encode('ascii'))


def main():
    if DEST.exists():
        assert sha(DEST / 'fpga/guitar_audio_low_speed.gprj') == sha(BASE / 'fpga/guitar_audio_low_speed.gprj'), 'Unexpected staging tree'
        assert (DEST / 'pc/launcher.py').is_file(), 'Unexpected staging tree'
    DEST.mkdir(exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    pc = DEST / 'pc'
    pc.mkdir(exist_ok=True)
    old_pc = ROOT / 'output/MIDI_GUIDE_20261103/FPGA_ESP_Control'
    tree(old_pc / 'licenses', pc / 'licenses')
    cp(old_pc / 'requirements.txt', pc / 'requirements.txt')
    project = pc / 'drum_bass_pitch_20261013'
    tree(ROOT / 'drum_bass_pitch_20261013/host', project / 'host')
    tree(ROOT / 'drum_bass_pitch_20261013/violin_r15', project / 'violin_r15',
         filter_file=lambda r: r.suffix.lower() in ('.py', '.md', '.json', '.hex', '.txt', '.cmd', '.ps1'))
    tree(ROOT / 'Music_Demos', pc / 'Music_Demos', filter_file=lambda r: r.suffix != '.zip')
    if (ROOT / 'rhythm_data').exists():
        tree(ROOT / 'rhythm_data', pc / 'rhythm_data')
    cp(ROOT / 'release_tools/full_host_launcher_1104.py', pc / 'launcher.py')
    cp(ROOT / 'esp32S3/Guitar_Controller_R15/tools/led_debug_panel.py', pc / 'tools/led_debug_panel.py')
    led = pc / 'tools/led_debug_panel.py'
    led.write_text(led.read_text(encoding='utf8').replace("'GPIO3 · 14颗': 3, 'GPIO7 · 13颗': 7", "'GPIO3 · 13颗': 3, 'GPIO7 · 14颗': 7"), encoding='utf8')
    # The matching FPGA build is immutable; S3 is a separate v27 overlay.
    tree(BASE / 'fpga', DEST / 'fpga', skip=('esp32S3', 'esp32C3'))
    tree(MIDI / 'fpga/esp32S3', DEST / 'fpga/esp32S3')
    tree(MIDI / 'fpga/esp32C3', DEST / 'fpga/esp32C3')
    tree(ROOT / 'esp32S3/Guitar_Controller_R15/tools', DEST / 'fpga/esp32S3/Guitar_Controller_R15/tools')
    tree(V16 / 'tests', DEST / 'fpga/tests')
    tree(V16 / 'sd_card', DEST / 'fpga/sd_card')
    tree(V16 / 'host/assets', DEST / 'fpga/host/assets')
    tree(V16 / 'third_party', DEST / 'fpga/third_party')
    tree(V16 / 'preview', DEST / 'docs/piano_audio')
    tree(BASE / 'protocol', DEST / 'docs/protocol')
    cp(ROOT / 'docs/BOARD_INTERCONNECT_PINOUT.md', DEST / 'docs/BOARD_INTERCONNECT_PINOUT.md')
    tree(ANDROID / 'android', DEST / 'android')
    tree(ANDROID / 'tests', DEST / 'tests/android')
    # Android test helpers resolve root/android; provide a documented test-root argument via a runner later.
    tree(BASE / 'tests', DEST / 'tests/mobile', filter_file=lambda r: r.suffix in ('.py', '.v', '.cjs', '.json') and not r.name.endswith('.pre.v'))
    cp(MIDI / 'build_s3.ps1', DEST / 'build_s3.ps1')
    cp(ANDROID / 'build_android.ps1', DEST / 'build_android.ps1')
    cp(ANDROID / 'README_MIDI.md', DEST / 'docs/Android_MIDI.md')
    for f in ('README_BLE_FIX.md', 'README_ORIGINAL.md'):
        cp(BASE / f, DEST / 'docs/history' / f)
    bin_dir = DEST / 'bin'
    for name in ('mobile_spi2.fs', 'mobile_spi2.bin', 'mobile_spi2.binx'):
        cp(BASE / 'bin' / name, bin_dir / name)
    app = ROOT / 'output/MIDI_GUIDE_20261103/hardware_200540/s3_v3427.bin'
    cp(app, bin_dir / 's3/s3_ble_led.bin')
    build = MIDI / 'fpga/esp32S3/Guitar_Controller_R15/build_ble'
    cp(build / 'bootloader/bootloader.bin', bin_dir / 's3/bootloader.bin')
    cp(build / 'partition_table/partition-table.bin', bin_dir / 's3/partition-table.bin')
    assert sha(build / 'Guitar_Controller_S3_R15.bin') == sha(app)
    cp(ANDROID / 'bin/app-midi-v0.5.apk', bin_dir / 'app-midi-v0.5.apk')
    cp(BASE / 'flash_s3.ps1', DEST / 'flash_s3.ps1')
    js(bin_dir / 's3/images.json', dict(version='3.4.27-midi-guide', flash_size='16MB', flash_mode='dio', flash_freq='80m', images=[
        dict(offset=offset, file=name, sha256=sha(bin_dir / 's3' / name))
        for offset, name in [('0x0', 'bootloader.bin'), ('0x8000', 'partition-table.bin'), ('0x10000', 's3_ble_led.bin')]]))
    touch = ROOT / 'output/TOUCH_ALL_HYS4_20261103_225646'
    tree(ROOT / 'esp32S3/CY8_Performance_Config', DEST / 'touch', skip=('device_backups', 'profiles'),
         filter_file=lambda r: r.suffix not in ('.log',))
    cp(touch / 'profiles.json', DEST / 'touch/profiles/profiles.json')
    for name in ('all_after.json', 'final_summary.json', 'proof.json'):
        cp(touch / name, DEST / 'touch/evidence' / name)
    profiles = json.loads((touch / 'profiles.json').read_text(encoding='utf8'))
    for row in profiles['images']:
        raw = bytes.fromhex(row['data'])
        assert len(raw) == 128 and raw[0x1d] == 0x84 and hashlib.sha256(raw).hexdigest() == row['sha256']
        (DEST / 'touch/profiles' / f"chip{row['chip']}_{row['address']:02X}.hex").write_text(
            '\n'.join(raw[i:i+16].hex(' ').upper() for i in range(0, 128, 16)) + '\n', encoding='ascii')
    # Exact SD data must match the current synthesized parameter banks.
    piano_hex = DEST / 'fpga/src/piano/sms_ddr/bank_image.hex'
    piano_raw = b''.join(int(x, 16).to_bytes(32, 'little') for x in piano_hex.read_text().split())
    # Old V16 SD data predates the current mobile bitstream; derive current data.
    import re
    piano_crc = zlib.crc32(piano_raw) & 0xffffffff
    expected_crc = int(re.search(r"32'h([0-9a-fA-F]+)", (DEST / 'fpga/src/piano/sms_ddr/bank_config.vh').read_text())[1], 16)
    assert len(piano_raw) == 281600 and piano_crc == expected_crc
    for rel in ('fpga/sd_card/PIANOSMS.BIN', 'fpga/host/assets/piano_sms_ddr.bin'):
        (DEST / rel).write_bytes(piano_raw)
        SOURCES.pop(rel, None)
    js(DEST / 'fpga/host/assets/piano_sms_ddr.json', dict(format='harmonic_sms_ddr_v1', bytes=len(piano_raw),
        chunks=1100, chunk_bytes=256, records=8800, record_bytes=32, crc32=piano_crc,
        sha256=hashlib.sha256(piano_raw).hexdigest(), recordings_played=False))
    SOURCES.pop('fpga/host/assets/piano_sms_ddr.json', None)
    drum_raw = b''.join(int(x, 16).to_bytes(4, 'little') for x in (DEST / 'fpga/src/drums/rom/drum_bank.hex').read_text().split()[:768])
    expected_drum_crc = int(re.search(r"32'h([0-9a-fA-F]+)", (DEST / 'fpga/src/drums/rom/drum_bank_config.vh').read_text())[1], 16)
    assert len(drum_raw) == 3072 and zlib.crc32(drum_raw) & 0xffffffff == expected_drum_crc
    (DEST / 'fpga/sd_card/DRUMS.BIN').write_bytes(drum_raw)
    SOURCES.pop('fpga/sd_card/DRUMS.BIN', None)
    js(DEST / 'fpga/sd_card/DRUMS_manifest.json', dict(bytes=len(drum_raw), sha256=hashlib.sha256(drum_raw).hexdigest(),
        source='src/drums/rom/drum_bank.hex', byte_order='little-endian 32-bit words'))
    SOURCES.pop('fpga/sd_card/DRUMS_manifest.json', None)
    inputs = json.loads((BASE / 'tests/mobile_spi2_inputs.json').read_text(encoding='utf8'))
    for rel, expected in inputs.items():
        assert sha(DEST / 'fpga' / rel) == expected, rel
    js(DEST / 'docs/fpga_build_inputs.json', inputs)
    for item in ET.parse(DEST / 'fpga/guitar_audio_low_speed.gprj').findall('.//File'):
        assert (DEST / 'fpga' / item.attrib['path']).is_file(), item.attrib['path']
    for src, target in [(ANDROID / 'audit/delivery_proof.json', 'android_delivery.json'),
                        (ROOT / 'output/MIDI_GUIDE_20261103/hardware_200540/proof.json', 's3_hardware.json')]:
        cp(src, DEST / 'docs/evidence' / target)
    for name in ('native_tests', 'host_tests'):
        source = MIDI / ('tests.log' if name == 'native_tests' else 'build.log')
        cp(source, DEST / 'docs/evidence' / (name + '_historical.log'))
    for fname in ('midi_parser_tests.log', 'midi_ui_tests.log', 'java_ack_tests.log', 'native_resource_tests.log', 'existing_ui_tests.log'):
        cp(ANDROID / 'audit' / fname, DEST / 'docs/evidence' / fname)
    for name, mode in [('打开完整上位机.cmd', 'main'), ('打开编曲工作台.cmd', 'arrangement'), ('打开音游.cmd', 'rhythm'),
                       ('打开音乐曲库.cmd', 'demo'), ('打开MIDI跟灯.cmd', 'midi'), ('打开LED控制.cmd', 'led')]:
        cmd(DEST / name, 'pc\\FPGA_ESP_Control.exe', mode)
        cmd(pc / name, 'FPGA_ESP_Control.exe', mode)
    (pc / 'build_pc.ps1').write_text('''param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
& $Python -m PyInstaller --noconfirm --onedir --windowed --name FPGA_ESP_Control --hidden-import argparse --hidden-import binascii --hidden-import bisect --hidden-import copy --hidden-import csv --hidden-import dataclasses --hidden-import functools --hidden-import hashlib --hidden-import math --hidden-import random --hidden-import re --hidden-import struct --hidden-import threading --hidden-import time --hidden-import types --hidden-import uuid --hidden-import queue --hidden-import wave --hidden-import ast --hidden-import zlib --hidden-import base64 --hidden-import webbrowser --distpath "$PSScriptRoot/dist" --workpath "$PSScriptRoot/build" --specpath "$PSScriptRoot/build" "$PSScriptRoot/launcher.py"
if ($LASTEXITCODE) { throw 'Desktop build failed' }
Write-Host 'Copy EXE and _internal from dist/FPGA_ESP_Control beside launcher.py, keeping application source and resources.'
''', encoding='utf8')
    (DEST / 'README.md').write_text(README, encoding='utf8')
    (pc / '使用说明.txt').write_text(PC_README, encoding='utf8')
    (DEST / 'touch/当前配置说明.md').write_text(TOUCH_README, encoding='utf8')
    js(AUDIT / 'copied_sources.json', SOURCES)
    js(AUDIT / 'assembly.json', dict(passed=True, destination=str(DEST), fpga_unchanged_inputs=len(inputs),
        piano_crc32=f'{zlib.crc32(piano_raw):08X}', sd_assets_verified=True,
        hardware_connected=False, firmware_written=False, s3_application_sha256=sha(app)))
    print('ASSEMBLY PASS', DEST, 'sources', len(SOURCES), 'FPGA inputs', len(inputs), flush=True)


README = '''# 芯奏界完整工程包 · 2026-11-04

建议解压到 D:\\，形成 D:\\XJ_1104。保留整个文件夹。

## 直接使用

双击根目录“打开完整上位机.cmd”。Windows x64 便携程序已带 Python、Tk、numpy 和串口运行库，无需另装 Python。编曲、音游、曲库、MIDI 跟灯、LED 控制也各有快捷入口。

电脑主上位机包含：木吉他/贝斯、钢琴、架子鼓、小提琴、音高、效果器、混音、验证测试、霍尔ADC、超级马里奥播放、时间轴编曲、音游、MIDI 跟灯和16首曲库（各含完整/短试听，共32份）。附6首原创MIDI和小星星单旋律/合奏，均带可编辑编曲。

根目录入口的 LED 窗口是配套工具；它和主上位机霍尔/MIDI页共用S3串口，同一时间只连接一个窗口。主串口控制FPGA，霍尔/MIDI页的串口控制ESP32-S3，按设备实际COM号选择。

手机安装 bin/app-midi-v0.5.apk；Android源码入口 android/。支持浏览器下载.mid后在“MIDI 导入 / 跟灯”选择文件、曲目声部、速度与移调，转入编曲、FPGA演奏或灯光引导。网站入口和示例已内置。沿用旧调试签名，可覆盖安装原App。

## 工程和制品

| 路径 | 内容 |
|---|---|
| pc/ | 完整电脑上位机EXE、运行库、可编辑Python源码、测试、曲库与MIDI |
| android/ | Android 0.5-midi-import完整工程与调试签名 |
| fpga/guitar_audio_low_speed.gprj | 当前Gowin FPGA工程，GW5AST-LV138FPG676AES |
| fpga/esp32S3/Guitar_Controller_R15/ | S3 v3.4.27 MIDI/BLE/触摸/霍尔/LED主工程 |
| fpga/esp32C3/ | S3构建依赖的公共触摸布局源码，必须一起保留 |
| bin/mobile_spi2.fs | 配套FPGA已构建位流；.bin/.binx也是FPGA输出 |
| bin/s3/ | S3引导程序、分区表和v27应用；images.json记录地址和SHA256 |
| fpga/sd_card/ | 与当前FPGA参数库逐字节一致的PIANOSMS.BIN和DRUMS.BIN |
| touch/ | 八片CY8配置源码、主机写入工具、最新128字节HEX和保存回读证据 |
| docs/ | 接线、协议、音色参考、构建/实板历史证据和本次打包验证 |
| SHA256SUMS.txt | 当前包每个交付文件的摘要 |

## 保留的当前行为

S3版本R15-HALL-v3.4.27-BLE，八片0x37～0x3E启用，I2C200kHz，扫描轮后等待2ms（不是整机延迟）。GPIO3→13颗链，GPIO7→14颗链；上电赛博炫彩DEMO，支持跟手、RGB/闪烁和MIDI跟灯。已包含BLE ACK拒收不断连、SPI总线锁修复、桌面霍尔版本后缀兼容修复。霍尔H1～H6启用，H7关闭，默认未布防。

CY8滞回全部手动4计数（0x1D=0x84），保留中值/IIR、3次传感器去抖、LBR10，auto-reset关闭。chip1阈值140，其他详见touch/当前配置说明.md。芯片配置单独保存在CY8内，刷S3应用不会自动写入这8份配置。

## SD卡和烧录

在已有FAT32卡根目录复制 fpga/sd_card/PIANOSMS.BIN 和 DRUMS.BIN，保留8.3文件名。本包不执行格式化。

FPGA用Gowin Programmer选 bin/mobile_spi2.fs。S3在装有esptool的Python环境：

```powershell
.\\flash_s3.ps1 -Port COM30 -Python python
```

脚本先校验三份S3制品摘要，再写0x0/0x8000/0x10000；不全片擦除。COM号以实际设备为准，先关闭占用它的程序。触摸配置恢复需要touch专用配置桥，正常S3应用不能直接执行配置桥协议；流程见touch说明。

## 从源码构建

- FPGA：Gowin EDA，以fpga/build_mobile.tcl为当前全量构建入口，顶层guitar_audio_ddr_top。其他tcl为保留的历史入口，以此处指定为准。
- S3：ESP-IDF6.1完整环境，运行build_s3.ps1；支持-IdfPath/-ToolsPath/-PythonEnvironment。
- Android：JDK17、Gradle8.9、Android SDK API35，运行build_android.ps1 -Sdk <SDK路径> -Jdk <JDK路径> -Gradle <gradle.bat路径>。构建不会覆盖bin内已交付APK。
- PC源码：Python3.10+，Tk、numpy、pyserial，运行pc/launcher.py。便携EXE使用Python3.14；重新打包可执行pc/build_pc.ps1，需另装PyInstaller。
- 第三方大型SDK、缓存和历史布局数据库不装入交付；必需IP、ROM/音色参数、SD文件、运行库均已保留。

## 验证范围

本次整理不连接串口、不烧录、不重写触摸配置。FPGA沿用mobile_spi2已构建产物，201项构建输入保持一致，原物理报告随包保留；并非本次重新布局布线。S3/Android制品沿用已编译且核对过的v27/v0.5。本次重新打包电脑EXE并验证所有页面、曲库编译、MIDI导入和解压后启动，详见docs/package_validation.json。

手机实际系统文件选择/BLE播放、MIDI灯光实物效果、触摸释放手感仍以实板验收为准；无线端到端延迟/抖动<5ms尚无完整实测结论。屏幕白屏问题此前暂缓，本包沿用原FPGA屏幕逻辑。历史文档版本以本README、bin清单和本次验证记录为准。
'''

PC_README = '''芯奏界完整电脑上位机 · 2026-11-04

打开“打开完整上位机.cmd”或 FPGA_ESP_Control.exe。完整解压并保留_internal、drum_bass_pitch_20261013、Music_Demos、tools等目录。

主控制台集成乐器演奏、效果/混音、绘制波形和包络、霍尔ADC与拨弦、验证测试、超级马里奥曲谱、编曲工作台、音游、MIDI跟灯和16首Demo曲库。编曲可导入MIDI；MIDI跟灯页面用于静音灯光练习，发声演奏请用编曲工作台。小星星及原创MIDI在Music_Demos/MIDI_*目录。

“打开LED控制.cmd”进入颜色、闪烁、演示、跟手与逐颗测试工具。GPIO3是13颗链，GPIO7是14颗链。同一S3串口同时只能被一个窗口占用；使用LED窗口时先断开霍尔/MIDI页串口。

FPGA演奏串口和S3霍尔串口是不同设备，按实际COM号选择。S3应为v3.4.27-BLE；握手修复和MIDI能力检测已带入。默认不会自动连接或烧录。

运行launcher.py可从源码启动；requirements.txt包含依赖。使用build_pc.ps1可重新打包。整个pc目录可以单独搬到另一台Windows x64电脑。
'''

TOUCH_README = '''# 八片当前CY8配置

profiles/profiles.json来自2026-11-03最后一轮SAVE/reset/readback确认。每片完整128字节、CRC和SHA256已保留；独立HEX为方便查看的字节表，并非Intel HEX。

地址0x37～0x3E均启用；手动滞回4（0x1D=0x84）；中值/IIR开启、传感器去抖3、LBR10、auto-reset关闭。

手动阈值寄存器按chip0..7为120/140/192/120/120/120/120/154。chip7保留ATH自动阈值，154只是其手动寄存器值，不能当作实际生效阈值。

本目录配置不会随着正常S3应用自动写入CY8；不要将旧generate_profiles默认参数重新生成为当前配置。

恢复时需先备份当前S3并编译/烧入本目录配置桥固件（build_config.ps1）；保持完全松手，然后用host/write_config.py --port <COM号> --profiles profiles/profiles.json只读检查。确需恢复时同一命令加--write，程序逐片备份、RAM校验、SAVE、reset并回读；发生不确定写入应停止处理。最后用工程包根flash_s3.ps1恢复v27正常应用。run_config.ps1和旧WRITE_RESULT文档属于历史流程，当前配置以profiles/profiles.json为准。

本次打包未访问硬件、未写配置。证据在evidence/；实物触摸释放表现仍需用户验收。
'''


if __name__ == '__main__':
    main()

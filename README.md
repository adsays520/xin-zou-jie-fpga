# 芯奏界 · FPGA 多乐器演奏与音游系统

**FPGA实时合成 · 多模态交互 · 光影音游**

基于高云 Tang Mega GW5AST-138B 与 ESP32-S3，实现木吉他、钢琴、贝斯、小提琴及架子鼓实时合成，配合触摸、霍尔拨弦、炫彩灯效、桌面编曲、节奏游戏和 Android BLE 控制。

## 下载可直接运行的工程包

请到 [Releases](https://github.com/adsays520/xin-zou-jie-fpga/releases/tag/v2026.11.04) 下载：

| 文件 | 用途 |
|---|---|
| `XJ_1104_Full_Public.zip` | 完整工程、Windows免安装上位机、Android APK、FPGA/ESP固件、SD音色文件、触摸配置、曲库与说明 |
| `XJ_1104_PC.zip` | 单独完整Windows x64上位机，已附运行库，无需安装Python |
| `app-midi-v0.5.apk` | 支持MIDI导入、编曲、BLE播放、MIDI跟灯和LED控制的Android安装包 |
| `SHA256SUMS.txt` | 上述制品的SHA256摘要 |

建议完整工程包解压到 `D:\`，形成 `D:\XJ_1104`，双击“打开完整上位机.cmd”。单独上位机包完整解压后运行 `FPGA_ESP_Control.exe`。不要只提取EXE，需保留其旁的运行库和资源。

GitHub的“Code → Download ZIP”下载的是源码；便携EXE、运行库和已构建固件请从Releases下载。

## 主要功能

- **多乐器音源**：木吉他物理建模、钢琴时变频谱合成、贝斯双波表合成、小提琴谐波/弓噪合成、算法鼓组。
- **完整电脑控制台**：14个页面，含乐器演奏、音高、效果/混音、测试、霍尔ADC、乐曲播放、编曲工作台、音游、MIDI跟灯和曲库；另有LED控制工具。
- **编曲与MIDI**：导入MIDI、编辑时间轴、选择声部/速度/移调，向FPGA播放或通过弦品灯辅助实体练习。
- **曲库**：16首Demo各含完整/短试听，共32份编曲；另附6首原创MIDI及小星星单旋律/合奏。
- **交互与灯效**：八片CY8触摸、六路启用的霍尔输入、GPIO3/7两路灯链，炫彩展示、实时跟手、RGB/闪烁和谱面引导。
- **手机App**：Android BLE控制、音色与效果、编曲、MIDI下载资源入口与系统文件导入。

## 源码目录

| 目录 | 内容 |
|---|---|
| `fpga/` | Gowin RTL、IP、约束、ROM参数、SD文件与构建脚本 |
| `fpga/esp32S3/Guitar_Controller_R15/` | ESP32-S3 v3.4.27触摸/霍尔/BLE/LED主工程 |
| `fpga/esp32C3/` | S3所需公共触摸布局源码 |
| `pc/` | 完整Python上位机源码、曲库、MIDI示例与打包脚本 |
| `android/` | Android v0.5-midi-import工程 |
| `touch/` | 八片CY8最新配置、写入工具与保存回读记录 |
| `tests/` | Android/PC数据一致性、MIDI、Java处理和SPI仿真测试 |
| `docs/` | 接线、协议、验证记录、音色参考、视频字幕和完整说明 |

## 构建与验证

- FPGA：器件 `GW5AST-LV138FPG676AES`，Gowin工程 `fpga/guitar_audio_low_speed.gprj`，当前构建入口 `fpga/build_mobile.tcl`。
- S3：ESP-IDF6.1，执行根目录 `build_s3.ps1`。
- Android：JDK17、Gradle8.9、Android SDK API35，执行 `build_android.ps1` 并指定SDK/JDK/Gradle路径。
- PC：Python3.10+、Tk、numpy和pyserial，执行 `python pc/launcher.py`；重新生成便携程序使用 `pc/build_pc.ps1` 和PyInstaller。
- 离线测试流程见 [docs/TESTING.md](docs/TESTING.md)，工程包完整使用说明见 [docs/工程包说明.md](docs/工程包说明.md)。

当前配套版本：FPGA `mobile_spi2`、S3 `R15-HALL-v3.4.27-BLE`、Android `0.5-midi-import`。GPIO3为13颗灯链，GPIO7为14颗灯链；八片CY8手动滞回4计数。触摸芯片配置单独保存，刷S3应用不会自动改写CY8。

已验证便携程序14页面、32份编曲编译、8个MIDI示例、MIDI/Java处理、PC与Android曲谱事件一致性及工程包解压校验。FPGA沿用已构建产物，201项构建输入保持；本次公开发布不烧录硬件。手机实板BLE、MIDI灯光实物表现及触摸释放效果仍需验收，端到端抖动小于5ms尚无完整实测结论。屏幕白屏问题保留原状态。

## 签名与第三方资料

公开版不包含Android原开发机的调试签名密钥。Releases中的APK保留原签名；自行构建时使用本机调试签名，详情见 [android/keystore/README.md](android/keystore/README.md)。

第三方资料、组件和曲目请遵循其各自许可与归属说明，见 `pc/licenses/`、`fpga/third_party/` 和资源附带说明。公开可见不代表所有内容采用同一种开源许可证。

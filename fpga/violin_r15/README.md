# R15 小提琴整体集成候选

2026-10-20 最新源码为 **Hall时序修复v3**：独立位流`impl/pnr/guitar_audio_hall_timing_v3.fs`于北京时间18:13通过正式验收，Setup/Hold均0违例，最差Setup **+0.354 ns**，主时钟Fmax **50.901 MHz**，BSRAM仍为314/340。使用**布局2（时序优先）/布线1（按时序）**，原50 MHz及DDR约束不变。八组定向对拍、普通/四音色阻塞/ESP实际帧跨端和完整七组整板回归通过；新位流及配套S3 v3.4.3均未烧录，实物Hall和听感尚未复测。通过版封存于工作区`output/hall_timing_v3_passed_20261020_181354`，v2和中止实验也保留。详情见 [HALL_TIMING_V3.md](HALL_TIMING_V3.md)。下文v2及更早段落均为历史记录。

2026-10-20 当前源码：**Hall联动修复v2 / S3 v3.4.3候选**。已修复排队事件错用品位，并加入ESP入队快照、公平调度和接收槽信用；73项固件、22项主机、正常/四音色阻塞/ESP实际帧跨端/7组整板定向回归通过，S3真实SDK编译通过。FPGA独立候选`guitar_audio_hall_link_v2`已于17:13完成构建并生成位流，但Setup验收失败：397个违例端点、最差−2.331 ns，sys_clk Fmax 44.780 MHz不足50 MHz；Hold无违例，DDR用户时钟满足要求。此候选不可作为合格烧录版；本轮未烧录、不改Hall阈值和CY8配置，下一轮尚未启动。详情见 [HALL_LINK_V2.md](HALL_LINK_V2.md)。以下是修复前历史记录，不作为当前源码或通过状态的声明。

2026-10-20 触摸/Hall联合审查：普通联测14个拨弦事件通过，但新增阻塞联测**失败**，复现排队事件使用后续品位（4/8/12变成4/12/12）。S3两队列共享单在途事务且固定控制优先，也存在队头阻塞/饿死风险。本轮仅增加测试和审查记录，未修改生产逻辑或烧录，不能宣称并发问题已修复。复现入口、原因与边界见 [TOUCH_HALL_LINK_AUDIT_20261020.md](TOUCH_HALL_LINK_AUDIT_20261020.md)。

2026-10-20 Hall诊断显示补充（仅上位机，不需烧录）：增加“复制诊断”，保留此前只更新表格、不进入日志框的七路 `RAW/BASE/THRESHOLD/VALID/EVENTS/REJECTED/ERRORS`，并附各项接收时间距今多久、缺失/过期提示及最近日志。表格新增 `|RAW-BASE|`，不是把原始ADC数值直接与阈值比较；每秒读取的快照不能证明有没有瞬态越阈值，`VALID=1`也不等于检测器已回中。`ARMED=0/1`改为明确中文提示；“木吉他试音”更名为“选择木吉他”，它只选音色，真正发声按钮是“直接试音”。PICK模式的触摸日志 `role=FRET_SELECT` 只确认选品，不是拨弦。复制诊断不改变模式、启用状态或触摸配置；仍需手动启用实物拨杆。诊断值超过3秒不再认定为当前状态，断开后清空当前快照；原日志保留但明确标为可能包含旧连接。

2026-10-20 USB联调修复：配套S3升级v3.4.2，修复副控制台路径/RX驱动；主机增加握手重试并区分“能力未知”和“在线CAP=0”。请关闭旧主机进程后重新启动本目录 `launch_gui.cmd`，在“霍尔 / 拨杆测试”页连接S3原生USB（当前COM30）；与主界面的FPGA串口独立。详见工作区 `esp32S3/Guitar_Controller_R15/HALL_USB_V3_4_2.md`。本次不修改FPGA，下面失败位流仍不能作为时序通过版本。

2026-10-20 新增软件触发模式 `0x09`、SPI能力回报及主机“霍尔 / 拨杆测试”页面。配套S3 v3.4已开启ADC采样，上电不自动发实物触发；完整操作见 `esp32S3/Guitar_Controller_R15/HALL_V3_4.md`。新位流独立输出 `guitar_audio_hall_v1`，由 `python violin_r15/build_event_fix.py --hall` 重做正式时序检查，不沿用下面历史结论。

Hall v1实际构建结果：综合/布局布线完成，但Setup 208个违规，最差−2.848ns，sys_clk Fmax 43.768MHz；Hold 0违规、BSRAM 314/340，独立原DDR脉宽检查通过。**`guitar_audio_hall_v1.fs` 已被拒绝，不得烧录**。本轮53项S3测试、7项主机测试及7组FPGA控制/霍尔定向整板仿真通过，不等于正式时序通过；完整报告在 `tests/results/hall_v1_build/summary.json`。原R15位流保持不变，本轮未烧录。

2026-10-19当前工作源码已加入演奏事件队列及背压修复；这是新候选，不能沿用旧R15的时序结论。新构建使用 `python violin_r15/build_event_fix.py` 和独立输出 `guitar_audio_events_v1`，原位流不覆盖；修改、验证状态和实机限制见 [EVENT_FIX_V1.md](EVENT_FIX_V1.md)。本次尚未烧录FPGA或配套S3 v3.3。下文原位流结果是历史通过版本。

R13、V2b 和 V3c 保持不变。R15 是独立工程，不是对 R13 位流的替换承诺。真实板端听感尚未验证。

当前完整集成版已生成位流 `impl/pnr/guitar_audio_violin_r15.fs`，正式 Setup/Hold 均为 0 违规；最差 Setup +0.018 ns，裕量偏小。完整实测报告见 `RESULTS.md`，通过版本由 `seal.py` 校验并保存到 `checkpoints/timing_passed_*`，不与失败实验混用。

## 工程入口

- FPGA：工程根目录 `guitar_ddr_violin_r15.gprj`，顶层 `guitar_ddr_violin_r15_top`。
- 综合：工程根目录运行 `gw_sh build_ddr_violin_r15.tcl`。
- 布局布线：工程根目录运行 `gw_sh pnr_ddr_violin_r15.tcl`；沿用正式时序检查和 DDR 脉宽检查，不放宽约束。
- 推荐通过 `python violin_r15/build.py syn`、`python violin_r15/build.py pnr` 重建；额外检查综合前后源码哈希以及网表与当前源码的一致性，防止旧结果被误用。
- 主机：双击本目录 `launch_gui.cmd`，选择串口并连接，进入“独奏小提琴 · R15”。原三种音色、鼓机和效果页保留。旧的 `host/launch_gui.ps1` 仍启动 R13 界面，不含小提琴。
- 也可在工程根目录运行 `python violin_r15/host_controller.py`；`launch_gui.ps1 -CheckOnly` 只检查启动环境，不打开窗口或连接串口。启动器自动寻找本机 Python，需要 tkinter、numpy、pyserial；依赖清单沿用 `host/requirements.txt`。
- S3：工作区 `esp32S3/Guitar_Controller_R15`，独立工程，原 `Guitar_Controller` 不改动。

## 完整链路

UART / S3 SPI / 触摸 / Hall → 校验与控制 → 单声部弓弦波导（96 kHz）→ 六段声体 → DC 抑制 → 95 tap 抗混叠降采样（48 kHz）→ 独立音量 → 原鼓机混音 → 原全局空间效果 → 原 PT8211 输出。

这是首版独奏小提琴，不是四声部实现。音域 MIDI 55..100，即 G3..E7。包含力度映射、起弓、分弓重触发、连弓、滑音、延迟揉弦和释放。触摸按键释放后回退至仍按住的最高扫描位置；主机按键使用最后按下优先。Hall 触发保留独立力度并定时收弓。本地拨弦兼容入口采用 120 ms 定时收弓。

两段弦延迟为 512×24 与 128×24，FIR 历史为 128×24；这些是逻辑容量，不等同于芯片实际 BSRAM 块数。真实资源以布局布线报告为准。

## 控制协议

所有帧均为六字节，最后一字节是前五字节 XOR。

| 功能 | 帧 |
| --- | --- |
| 选择小提琴 | `A5 04 03 00 00 A2` |
| 音符 | `A5 08 MIDI VELOCITY ACTION XOR` |
| 独立音量 | `A5 70 03 LEVEL 00 XOR` |

`MIDI=55..100`，`VELOCITY=1..127`，`ACTION=0` 松开、`1` 分弓起音、`3` 连弓起音。非当前音高的旧松键不会截断当前音符。音色或模式切换强制收弓。上传数据中的 `A5` 不会被另一个扫描器误识别成小提琴命令。

S3 文本入口：`FPGA,TIMBRE,3`、`FPGA,VIOLIN,69,100,1`、`FPGA,VIOLIN,72,100,3`、`FPGA,VIOLIN,72,1,0`、`FPGA,LEVEL,3,100`。

## 验证

- `python violin_r15/test_host.py`：主机帧、音域、分弓/连弓、最后按键优先及回退。
- `python violin_r15/test_ui.py`：隐藏窗口与模拟串口的真实界面导航、音色、按键、音量与离页收弓测试，不连接真实设备。
- `python violin_r15/run_tests.py --core 31000`：与封存 V3c 整数模型对拍 31,000 个 PCM / 62,000 个内部采样，包含揉弦与释放。拆分声体系数查表后的最坏工作量 852 clocks，最短帧预算 1041 clocks。此结果是运算周期预算，不代表布局布线 Setup/Hold 已通过。
- `python violin_r15/run_tests.py --repair-units --board`：额外对拍空间效果 5,500 个立体声采样帧，并测试缓存读写/填充并发、错误响应及完整板级路径。
- `python violin_r15/run_tests.py --board`：旧 UART/SPI/触摸回归、新控制测试和真实板级顶层模拟。DDR PHY 使用模型；PT8211 接收器检查实际串行输出及建立/保持时间。
- `python violin_r15/audit.py`：检查 R13、V2b、V3c 与 R13 完整工程包未变更，输出当前验证记录。

时序未通过的试验位流不得当作正式推荐版本；综合通过也不能替代布局布线和板端试听。

S3 配套工程已使用本机 ESP-IDF 6.1 编译，应用镜像为 `esp32S3/Guitar_Controller_R15/build_r15/Guitar_Controller_S3_R15.bin`。这不代表已刷入 S3 或完成硬件联调。

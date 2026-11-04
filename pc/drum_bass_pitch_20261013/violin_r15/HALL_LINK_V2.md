# Hall联动修复候选 v2 / S3 v3.4.3

本页已作为v2历史记录保留。后续时序修改和当前构建状态见 [HALL_TIMING_V3.md](HALL_TIMING_V3.md)，v2原源码、证明和失败位流均已封存；下述v2功能通过不代表修改后的源码已经验证。

## 当前状态

2026-10-20：S3 v3.4.3已编译通过，73项固件回归通过；主机22项回归通过。普通联合、四音色阻塞、实际ESP C发送帧到FPGA解析器的跨端仿真，以及Hall定向和完整板级两套各7组回归均通过。

FPGA独立候选`guitar_audio_hall_link_v2`于北京时间2026-10-20 17:13:48完成正式构建，源码摘要与构建前一致；已生成位流，但**Setup时序验收失败，不可作为合格烧录版本**。本轮构建已结束，尚未启动下一轮时序修改或构建。构建证据见`tests/results/hall_link_v2_build/proof.json`，详细时序见同目录`timing.json`。

| 本轮正式结果 | 数值 |
| --- | --- |
| Setup违例端点 / 最差裕量 | 397 / −2.331 ns |
| Hold违例端点 / 最差裕量 | 0 / +0.135 ns |
| sys_clk Fmax / 要求 | 44.780 / 50 MHz，未满足 |
| DDR用户时钟Fmax / 要求 | 108.180 / 100 MHz，满足 |
| DDR参考时钟Fmax / 要求 | 176.577 / 100 MHz，满足 |
| mem400 Fmax / 要求 | 2240.145 / 400 MHz，满足 |
| 最小脉宽裕量 | +0.153 ns，通过 |
| BSRAM | 314 / 340 |

最差路径为`u_audio/u_drums/n530_s`到`current_step_1_s0`，属于鼓机swing量输出、阈值加减与步进比较控制链；报告还列出吉他参数查找、效果器、复音FIFO和触摸门控的负裕量路径，不能只修鼓机就宣称全部通过。下一轮应先拆分最差组合链并做功能对拍，再重新正式布局布线；暂缓BRAM压缩，不降低时钟或放宽时序约束。以上Fmax和裕量只描述本候选，不代表板端试听或实物Hall检测已经通过。

本次未通过的位流保留在`impl/pnr/guitar_audio_hall_link_v2.fs`，SHA256为`197b92a031f91de2b5a858fe1d81d1067864f7e2bf6a08fe6f05337f028ac70e`；不能与原`guitar_audio_violin_r15.fs`时序通过版混用。

本轮未烧录S3或FPGA，未访问COM30，未更改Hall阈值、ADC采样/校准算法、触摸过滤、CY8配置或原始HEX。最后已确认烧入的S3仍为v3.4.2。旧源与旧固件保存在工作区`output/pre_touch_hall_link_fix_20261020`，之前的USB修复封存也保留。

## 修复内容

### ESP：在入队时绑定事件快照

- Hall事件入队时调用原有触摸快照接口，保存经过既有过滤、在线掩码筛选后的126个逻辑键，而不是发送时才取品位。
- Hall队列仍为32项，每项由2字节扩为18字节：弦、力度、16字节键快照；队列存储比旧版增加512字节S3 RAM。
- 当前触摸快照仍随每帧更新，事件历史快照另存于帧的保留区，两者不会互相覆盖。绑定的是“产生事件时已确认的触摸状态”，不是未经扫描确认的瞬时物理触点。

### ESP：公平调度与接收槽信用

- 当固定控制与Hall都可发送时交替选取，单一路径有数据时不强迫空等；各自队列保持FIFO顺序。
- 使用有效ACK中的固定命令槽状态；新FPGA还报告Hall槽可用性。忙槽对应的队列暂留，另一队列或触摸心跳仍有机会发送。
- **仍保留一个在途事务。**等待不确定ACK期间逐字节重发同一帧，不替换载荷、不跳序号，保留CRC/会话/序号去重。信用来自已确认的状态，并不是“从此任何情况下都不会阻塞”的保证。
- 若UART长期占用、某事务已在途而未获ACK、链路离线或接收方停止处理，仍可能等待；有限队列满时明确拒绝，不无声覆盖旧事件。

### FPGA：从SPI接收开始冻结事件品位

- Hall帧接收时单独锁存所属键快照，分21个时钟扫描六弦最高品位；扫描与实时触摸状态更新相互独立，不引入21层组合优先链。
- 扫描中与等待消费期间均占用Hall槽；槽忙时不接受另一个Hall帧，也不提前ACK。
- 吉他、Bass、钢琴和小提琴处理器在接收事件时锁存六弦品位。出队时不再读会被后续触摸更新的实时品位。
- 保留原声音末端16项拨弦FIFO；本次没有新增BRAM数组，实际资源与时序须以本候选的综合/布局布线报告为准。

修复前阻塞联测是4/8/12品变成4/12/12品；修复后四种音色均保持4/8/12品与各自力度101/102/103。测试输入为合法SPI事件，不是对板端ADC信号的测量。

## 兼容的帧扩展

仍使用原64字节帧、版本1、Hall类型2和长度7，CRC覆盖范围不变：

| 字节 | 请求中的含义 |
| --- | --- |
| 8～23 | 当前实时触摸快照，旧字段不变 |
| 31 | Hall弦掩码，bit0为6弦 |
| 32～37 | 六弦力度，旧字段不变 |
| 38 | `0xC1`表示40～55含事件快照 |
| 40～55 | Hall产生时保存的触摸键快照，最高两位为0 |

新FPGA回复字节46为`0xC1`；回复47的bit0/bit1分别表示固定控制槽/Hall槽可用。原回复39的`0xA0 | trigger_override`保持不变，软件切换能力与快照绑定能力分开判断。

- **旧S3＋新FPGA：**仍接受旧Hall帧，锁存其8～23字段作为事件快照，修复FPGA内部排队错配，但无法回补ESP入队时尚未保存的历史状态。
- **新S3＋旧FPGA：**旧Hall协议仍可使用，但旧FPGA忽略扩展快照，不能宣称完成并发修复。
- **新S3＋新FPGA：**`SNAPSHOT_CAP=1`后才有完整的入队至FPGA事件绑定能力；能力回复不证明音频、ADC或正式时序通过。

新`FPGA,STATUS`追加`SNAPSHOT_CAP/CTRL_READY/HALL_READY/CTRL_QUEUE/PICK_QUEUE/TOUCH_ENABLED`。旧字段位置与主机解析保持兼容。新界面区分能力未知、明确不支持和支持，不会因缺少字段或未握手就要求换位流。

旧FPGA未报告Hall槽信用时，S3按旧协议假定可以尝试发送，`HALL_READY=1`不代表已收到空槽报告；应结合`SNAPSHOT_CAP`解读。队列深度不含已经取出、正在等待ACK的那一项。

## 验证入口及证据

- S3工程运行`python -B tests/validate_link_fix.py`：73项回归、真实SDK编译镜像、源码时间/摘要，以及Hall检测和触摸相关文件与修改前逐字节相同的检查。报告`tests/hall_v3_4_3_validation.json`；旧`validate_hall.py`保留作v3.4.2历史验证，不用于本候选。
- FPGA工程运行`python -B -m unittest discover -s violin_r15 -p 'test_*.py' -v`：22项主机/协议测试，日志`violin_r15/test_results/hall_link_v2_host_tests.log`。
- `python -B violin_r15/run_tests.py --touch-hall`：17个普通/扩展快照拨弦事件，实时品位继续变化时历史事件仍保持正确；`touch_hall_link_proof.json`记录源码摘要。
- `python -B violin_r15/run_tests.py --touch-hall-backpressure`：吉他、钢琴、Bass、小提琴四组阻塞测试；`touch_hall_backpressure_proof.json`包含四组源码摘要。
- `python -B violin_r15/run_tests.py --esp-wire`：执行实际`fpga_link.c`任务和协议代码，用模拟队列/SPI ACK生成原始MOSI字节，再由实际FPGA SPI/选品/仲裁/解析器消费。事件快照为4/8/12品，实时触摸为15品；包括重复请求和下游阻塞。`esp_hall_wire_proof.json`同时记录ESP/FPGA源码与原始帧摘要。
- `python -B violin_r15/run_tests.py --hall-board`：7组原控制、SPI、模式切换与Hall定向整板测试。Hall E2激活吉他音源，模型DAC接收267字，建立/保持保护322/304ns；DDR PHY是模型，不代表板端DDR或听感验收。
- `python -B violin_r15/run_tests.py --board`：完整7组回归通过。原Bass、钢琴、底鼓/混音和空间效果与参考精确对拍474帧；小提琴690帧均有非零输出，模型DAC共2709字、建立/保持保护316/302ns。结果见`integration_proof.json`与`tb_violin_board_run.log`，仍不是板端试听。
- `python -B violin_r15/validate_link_fix.py`：核对上述ESP/FPGA当前源码、镜像与测试证明，确认只有预期五个FPGA模块改变，原时钟/引脚/DDR约束及其余音频源码不变，旧时序通过位流摘要不变；综合结果在`hall_link_v2_validation.json`。`functional_validation_passed=true`与`FPGA_build_accepted`是独立字段，不把功能通过当作时序通过。
- `python -B violin_r15/build_event_fix.py --hall-link`：独立输出候选，沿用原50MHz及DDR时钟、Setup/Hold、Gray指针最大延迟和DDR脉宽检查，不放宽约束，也不覆盖旧R15位流。
- 正式构建结束后，`python -B violin_r15/timing.py --hall-link`整理本候选的约束时序、四时钟Fmax、资源和最差路径到`tests/results/hall_link_v2_build/timing.json`，不覆盖历史R15时序结果。

原4/12/12失败日志保存在`output/pre_touch_hall_link_fix_20261020/fpga/tb_touch_hall_backpressure_run.log`，没有把失败证据改写成通过。

## S3候选镜像

- `esp32S3/Guitar_Controller_R15/build_r15/Guitar_Controller_S3_R15.bin`
- 303104字节；SHA256：`32a4f5a962bc9c32acc29a466ebd92466c748e72e0e1408489ad7de4493988a7`。
- 编译标识`R15-HALL-v3.4.3`；**未烧录**，上电仍只采样、实物触发停用。

## 尚不能据此确认的事情

这次修复的是事件状态绑定和发送公平性，没有改变校准阈值、35ms回中条件或ADC接线。若实物拨动后S3的`EVENTS`仍为0，应继续检查检测端，不能把本轮联动修复等同于“实物无声已修好”。实际烧录和试听也尚未执行。

# Hall联动时序修复候选 v3

## 当前状态

2026-10-20：在保留v2联动修复的前提下，针对v2正式报告中的负裕量路径修改六个RTL文件，并增加一个分银行参数查表模块。独立构建`guitar_audio_hall_timing_v3`按用户要求使用**时序优先布局2、按时序布线1，并开启timing_driven**，于北京时间**18:13:54完成并通过正式时序验收**。源码摘要与构建前一致，四个时钟、Setup/Hold、Gray指针最大延迟和DDR脉宽检查均通过；该结论不等于板端听感或实物Hall检测已经通过。

| 正式结果 | v2 | v3（本版） |
| --- | --- | --- |
| Setup违例端点 | 397 | **0** |
| 最差Setup裕量 | −2.331 ns | **+0.354 ns** |
| Hold违例端点 | 0 | **0** |
| 最差Hold裕量 | +0.135 ns | +0.126 ns |
| sys_clk Fmax / 要求 | 44.780 / 50 MHz | **50.901 / 50 MHz** |
| DDR用户时钟Fmax / 要求 | 108.180 / 100 MHz | **131.177 / 100 MHz** |
| DDR参考时钟Fmax / 要求 | 176.577 / 100 MHz | 273.378 / 100 MHz |
| mem400 Fmax / 要求 | 2240.145 / 400 MHz | 2240.145 / 400 MHz |
| 最小脉宽裕量 | +0.153 ns | +0.143 ns |
| BSRAM | 314 / 340 | **314 / 340** |
| DSP | 145.5 / 298 | 145.5 / 298 |
| 寄存器 | 41172 | 42840 |
| Logic | 64443 | 64947 |

本版主时钟裕量仍不宽裕，后续修改必须重新验收；不能把这次通过泛化到其他布局或重新编译的版本。此前RTL修改和布局/布线策略同时变化，不能单独归因于某一项。

位流：`impl/pnr/guitar_audio_hall_timing_v3.fs`，42340874字节，SHA256 `967faad6f191e14cb72d2cc6be3b54a3482cb1a3a561b2986bee49fe0bbf4efc`。证据：`tests/results/hall_timing_v3_build/proof.json`、`timing.json`及`violin_r15/test_results/hall_timing_v3_validation.json`。独立封存目录：工作区`output/hall_timing_v3_passed_20261020_181354`。

原0/0策略实验在布局阶段已主动中止，未生成位流、未运行正式时序验收，不能记为Setup失败；其源码、综合产物和中止记录封存在`output/hall_timing_v3_place0_aborted_20261020`。选项含义已从本机Gowin 1.9.12.03的`IDE/data/config/rtlplaceoptions.xml`与`rtlrouteoptions.xml`核对：布局0以编译速度优先、布局2为timing priority，布线1按时序选择路径。保持时钟/约束/RTL不变，只切换本候选的物理实现策略。

八组定向对拍已通过：采样节拍与音频引脚100万周期完全一致；256个查表地址的150位参数一致；鼓机两种采样率覆盖swing 0～50、BPM 30/300、错误CRC与非法配置；三种钢琴门控长度覆盖反压、重触发、停用与切模式；空间效果5500帧立体声一致，包括正负极值、帧边界控制变化和1000个有效反馈帧。

截至北京时间17:56，普通联动、四音色阻塞、实际ESP发送帧跨端以及完整七组整板回归均通过，并经`validate_timing_v3.py`核对当前源码摘要。整板原音色474帧PCM/串行输出与参考一致，Hall E2恰好产生一次力度99事件；小提琴690帧均有非零输出，DAC模型接收2709字、建立/保持保护316/302 ns。新增查表元信息对齐与FIFO分配周期断言均通过。功能证明和18:13完成的正式时序证明独立保存，不把模型结果当作板端试听。

未修改S3固件、Hall检测/阈值、触摸过滤、CY8配置、音色参数数据或DDR控制器，也未打开串口或烧录设备。S3候选仍为v3.4.3；板上最后确认版本仍为v3.4.2。实物Hall拨动无声的问题尚未经过板端复测。

## 修改范围

- **鼓机阈值：**利用接收帧中参数字节与校验字节之间的一拍，提前计算swing量；仅校验成功且参数合法时提交长/短阈值。相位计数使用覆盖48 kHz合法BPM/swing范围的位宽，切掉DSP输出后的长阈值加减链；实际步进和音符事件按周期与原版对拍。
- **采样节拍：**根据序列化器下一拍的位时钟、输出状态和位计数提前计算寄存后的`sample_tick`，不是把原脉冲简单延后一拍。BCK、WS、DIN、请求和采样tick的周期均保持不变，重复复位也一致。
- **吉他参数：**原生成的126组音色数据文件保持不变；按弦并行查表、寄存后再选择。增加一拍20 ns的控制流水，弦、力度、包络模式与触发同步传递；整板仿真加入数据/元信息对齐断言。
- **钢琴门控：**握手只产生局部计数器重载信号，宽计数器下一拍装载扣除一拍后的长度。有效门控到期和发出的命令保持原周期，闲置计数器的内部数值不要求与旧版相同。
- **复音FIFO：**提前寄存“末槽第30周期”的译码，保留原出队周期、队列容量、满队列同拍出入队和分配策略；整板加入与原组合条件逐拍一致的断言。
- **空间效果：**拆分合唱插值的减法、乘法与加法，增加两拍处理时间；提前寄存反馈限幅参数与反馈基数。稳态/帧边界控制下的PCM逐帧对拍保持一致；不宣称任意处理中途改变控制参数也具有相同的逐周期采样点。

## 构建和验证

工程仍为`guitar_ddr_violin_r15.gprj`，只增加`violin_r15/note_params_banked.v`一项。时钟、引脚、DDR约束与正式验收脚本均保持原样：50 MHz主时钟、DDR时钟、Setup/Hold、跨时钟Gray指针最大延迟和DDR脉宽均继续检查，不通过就拒绝候选。

当前脚本明确设置`set_option -timing_driven 1`、`set_option -place_option 2`、`set_option -route_option 1`。本轮不再使用0号布局/布线策略，也不通过减少时序分析项目换取通过。

时序优先重跑于北京时间17:49:08启动；已从Gowin实际生成的工程过程配置确认`Place_Option=2`、`Route_Option=1`、`Run_Timing_Driven=true`及正确输出名。快照保存于`tests/results/hall_timing_v3_build/implementation_options.json`，与本轮启动时间绑定，不只依赖脚本里写了什么。

- 定向对拍：`python -B violin_r15/run_timing_tests.py`，证据`violin_r15/test_results/hall_timing_v3/proof.json`。鼓机定向对拍使用静音音源桩，只验证控制；音源和DAC由整板回归验证。
- 联动/阻塞/真实ESP发送帧：原`run_tests.py --touch-hall`、`--touch-hall-backpressure`、`--esp-wire`。
- 整板：`python -B violin_r15/run_tests.py --board`，包含原音色精确比较、Hall E2、四音色路由和DAC模型检查；DDR PHY仍为模型，不等于板端试听。
- 正式构建：`python -B violin_r15/build_event_fix.py --hall-timing`。日志和证明独立存于`tests/results/hall_timing_v3_build`。
- 构建完成后整理：`python -B violin_r15/timing.py --hall-timing --strict`，本次严格检查已通过。
- 汇总：`python -B violin_r15/validate_timing_v3.py`核对当前源码与功能证明、S3未变、原约束/验收未变及旧位流摘要；功能通过和正式时序通过分开报告。

## 已保留版本

v2源码、约束、综合/布局布线产物、失败位流及验证证据已完整按清单复制到工作区`output/hall_link_v2_setup_failed_20261020_171348`，206个文件记录在`sha256.json`。其Setup为397个违例、最差−2.331 ns，不能当作合格烧录版。原时序通过的`impl/pnr/guitar_audio_violin_r15.fs`也保留不动。v3在上述独立目录封存源码、验证、综合/布局布线产物与通过位流；BRAM并未下降，本轮优先解决时序，未以削减功能换取资源节省。

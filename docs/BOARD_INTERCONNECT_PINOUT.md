# ESP32-S3 与 Tang Mega 138K Pro 接线汇总

更新日期：2026-10-10。

2026-10-20 补充：R15 v3.4候选按第6节GPIO主方案启用Hall ADC采样，并增加软件触发模式和测试界面，未改用第7节全ADC1方案。默认H1～H6采样、H7可手动开启测量，上电不自动发实物触发；烧录及FPGA时序是否通过须看独立记录。操作与当前限制见 [霍尔v3.4说明](../esp32S3/Guitar_Controller_R15/HALL_V3_4.md)。本文原有“规划/尚需实现”描述是历史硬件说明，不代替新候选的验证记录。

本文是新板/转接板的接线规划，不表示这些功能已经写入、烧录或实测。现有 C3 固件、FPGA 工程和触摸芯片 NVM 本次均未修改。

2026-10-16 补充：S3 SPI、126 键和 SW1 直接/拨杆触发的软件已另行接入，
当前实现、命令与验证边界见 [S3 联调说明](../drum_bass_pitch_20261013/docs/S3_SPI_联调.md)。
下文仍保留 10 月 10 日的硬件规划；旋钮和其他开关不能据此视为已经实现。

## 1. 使用范围与投板前条件

- ESP：按之前原理图中的 **ESP32-S3-WROOM-1-N16R8** 规划，不适用于 ESP32-C3。
- FPGA：Tang Mega 138K **Pro**，使用底板 **J23 / SDRAM CONN. / 2×20** 排针，不是 P1。
- J23 上不安装 SDRAM 扩展模块；保留当前屏幕工程的 LCD 六路连接。
- SPI：S3 固定为主机，FPGA 固定为从机，MOSI/MISO 全双工；不在同一组线上同时设置两个主机。
- RKJXT1F42001：七路输入；公共端另接地。
- 六个钮子开关：暂按 **两档、六路独立开关量** 设计。三档完整识别不属于此六路方案。
- 七个霍尔：用户给出的 **Hallwee HAL49ESO / 立创 C7420984 / SOT-23-3L**，按用户确定的 **5V 供电**，输出分压后由 S3 ADC 采集。

必须注意：

1. **J23 第 11 针是 +5V，第 12 针是 GND，J23 没有直接提供 3.3V 电源针。**
2. FPGA 数字接口用 3.3V 电平。核对相关 Bank 的实际供电，再设置 `LVCMOS33` 和 `BANK_VCCIO=3.3`；软件约束不能改变板上供电电压。
3. HAL49ESO 的物料号已经确认，但其立创规格书 V3.2 第 1 页与第 4 页对 2、3 脚的功能标注冲突。**本文按 VDD/GND/OUT 功能给出连接，暂不冻结 2、3 脚对应的焊盘号。未解决此项，不应直接投板。**
4. 下述七路直接采集方案用了 ADC2，面向先不启动 Wi-Fi 的调试。需要 Wi-Fi 或连续 DMA 采集时，优先考虑第 7 节的全 ADC1 改线方案或外置 ADC。

## 2. J23 完整占用表

“原网络名”只是原 SDRAM 接口的用途，不限制该引脚在新 FPGA 工程中的功能。

| J23 针号 | FPGA 引脚/电源 | Bank | 原网络名 | 本次规划用途 | 相对 FPGA 的方向 |
| --- | --- | --- | --- | --- | --- |
| 1 | U16 | 2 | SDRAM_D0 | LCD SCK / `lcd_sck`，保留 | 输出 |
| 2 | V16 | 2 | SDRAM_D1 | LCD SDA / `lcd_sda`，保留 | 输出 |
| 3 | U15 | 2 | SDRAM_D2 | LCD CS_N / `lcd_cs_n`，保留 | 输出 |
| 4 | V17 | 2 | SDRAM_D3 | LCD DC / `lcd_dc`，保留 | 输出 |
| 5 | W21 | 2 | SDRAM_D4 | LCD RST_N / `lcd_rst_n`，保留 | 输出 |
| 6 | Y21 | 2 | SDRAM_D5 | LCD 背光控制 / `lcd_led`，保留 | 输出 |
| 7 | P21 | 3 | SDRAM_D6 | S3 SPI SCLK / `spi_sclk` | 输入 |
| 8 | U17 | 2 | SDRAM_D7 | S3 SPI MOSI / `spi_mosi` | 输入 |
| 9 | P23 | 3 | SDRAM_D15 | 本方案不占用 | — |
| 10 | P24 | 3 | SDRAM_D14 | 本方案不占用 | — |
| 11 | +5V | — | +5V | 电源，仅按供电方案使用 | 电源 |
| 12 | GND | — | GND | 公共地 | 地 |
| 13 | T23 | 3 | SDRAM_D13 | 本方案不占用 | — |
| 14 | R23 | 3 | SDRAM_D12 | 本方案不占用 | — |
| 15 | R25 | 3 | SDRAM_D11 | 本方案不占用 | — |
| 16 | T25 | 3 | SDRAM_D10 | 本方案不占用 | — |
| 17 | W23 | 2 | SDRAM_D9 | 本方案不占用 | — |
| 18 | P25 | 3 | SDRAM_D8 | 本方案不占用 | — |
| 19 | U24 | 2 | SDRAM_A12 | S3 SPI MISO / `spi_miso` | 输出 |
| 20 | V23 | 2 | SDRAM_CLK | S3 SPI CS_N / `spi_cs_n` | 输入 |
| 21 | AC26 | 2 | SDRAM_A9 | IRQ / DATA_READY / `fpga_irq` | 输出 |
| 22 | U25 | 2 | SDRAM_A11 | FPGA_READY / `fpga_ready`，可选预留 | 输出 |
| 23 | AB25 | 2 | SDRAM_A7 | 旋钮 Encoder A / `enc_a` | 输入 |
| 24 | AB26 | 2 | SDRAM_A8 | 旋钮 Encoder B / `enc_b` | 输入 |
| 25 | AA25 | 2 | SDRAM_A5 | 旋钮方向 A / `joy_a_n` | 输入 |
| 26 | AA24 | 2 | SDRAM_A6 | 旋钮方向 B / `joy_b_n` | 输入 |
| 27 | Y26 | 2 | SDRAM_WE | 旋钮方向 C / `joy_c_n` | 输入 |
| 28 | Y25 | 2 | SDRAM_A4 | 旋钮方向 D / `joy_d_n` | 输入 |
| 29 | L22 | 3 | SDRAM_DM0 | 本方案不占用，与 PMOD0_IO1 共网 | — |
| 30 | M24 | 3 | SDRAM_DM1 | 本方案不占用 | — |
| 31 | W26 | 2 | SDRAM_CAS | 旋钮 Push / `joy_push_n` | 输入 |
| 32 | W25 | 2 | SDRAM_RAS | 开关 1 / `toggle_1_n` | 输入 |
| 33 | U26 | 2 | SDRAM_CS | 开关 2 / `toggle_2_n` | 输入 |
| 34 | V26 | 2 | SDRAM_BA0 | 开关 3 / `toggle_3_n` | 输入 |
| 35 | W20 | 2 | SDRAM_BA1 | 开关 4 / `toggle_4_n` | 输入 |
| 36 | Y20 | 2 | SDRAM_A10 | 开关 5 / `toggle_5_n` | 输入 |
| 37 | V19 | 2 | SDRAM_A0 | 开关 6 / `toggle_6_n` | 输入 |
| 38 | W19 | 2 | SDRAM_A1 | 本方案不占用 | — |
| 39 | U22 | 2 | SDRAM_A2 | 本方案不占用 | — |
| 40 | V22 | 2 | SDRAM_A3 | 暂保留，复用前核对板载时钟相关连接 | — |

“本方案不占用”不等于整块板上无其他连接，也不保证配置复用条件已经满足。后续使用这些引脚时仍需核对底板、核心板和所用工程。

上述分配保留 LCD，安排六路 SPI/握手、七路旋钮、六路开关，没有重复使用同一个 J23 信号针。

J23 针号依据 [Sipeed 官方底板原理图，第 16 页](https://dl.sipeed.com/fileList/TANG/Mega_138K_Pro/02_Schematic/TANG_MEGA-138K_Pro-Dock-4071f_Schematics.pdf)。LCD 保留项依据当前 [屏幕工程引脚配置](C:/Users/Junejay_Huang/Desktop/gowin-2/distorionpro_screen_mixer/src/audio.cst)。

## 3. ESP32-S3 与 FPGA 的 SPI 接线

| 信号 | ESP32-S3 GPIO | J23 针号 | FPGA 引脚 | 方向 |
| --- | --- | --- | --- | --- |
| SCLK | GPIO12 | 7 | P21 | S3 → FPGA |
| MOSI | GPIO11 | 8 | U17 | S3 → FPGA |
| MISO | GPIO13 | 19 | U24 | FPGA → S3 |
| CS_N | GPIO10 | 20 | V23 | S3 → FPGA |
| IRQ / DATA_READY | GPIO8 | 21 | AC26 | FPGA → S3 |
| FPGA_READY，可选 | GPIO9 | 22 | U25 | FPGA → S3 |
| GND | GND | 12 | GND | 共地 |

- S3 产生 SCLK 和 CS_N。一笔传输中，MOSI 发送触摸/霍尔事件或指令，MISO 同时接收 FPGA 已准备好的 RGB/状态数据。
- 建议 IRQ 使用高电平有效：FPGA 有待读数据时保持高，S3 读取并确认后再由 FPGA 清除。不要只发一个容易漏掉的短脉冲。
- FPGA_READY 表示 FPGA 已配置完成并且 SPI 逻辑已就绪，不能仅表示“上电了”。
- 没有待发送指令时，S3 仍可发送空帧，提供时钟以接收 FPGA 数据。FPGA 从机不能自行启动 SPI 时钟。
- 对当前 MOSI 指令计算出的回复通常在后续帧返回，不应默认同一帧里立刻可用。
- 建议从 **Mode 0、MSB first、1MHz** 调试，确认 FPGA 时序和连线后再提高频率。这是调试起点，不是保证的最高速度。
- SCLK/MOSI/CS_N 在 S3 发送端预留 22～47Ω 串联电阻；MISO 在 FPGA 发送端预留同类电阻。
- CS_N 加 10kΩ 上拉到 3.3V；IRQ、FPGA_READY 在 S3 接收侧各加 10kΩ 下拉，定义 FPGA 配置期间的默认状态。
- FPGA 在 CS_N 无效时让 MISO 高阻，便于后续增加共用 SPI 的外设。

四线 SPI 的全双工含义和主机行为参见 [乐鑫 SPI Master 文档](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/spi_master.html)。

## 4. RKJXT1F42001 接法

| 器件端子 | J23 针号 | FPGA 引脚 | 信号名 |
| --- | --- | --- | --- |
| Encoder A | 23 | AB25 | `enc_a` |
| Encoder B | 24 | AB26 | `enc_b` |
| 方向 A | 25 | AA25 | `joy_a_n` |
| 方向 B | 26 | AA24 | `joy_b_n` |
| 方向 C | 27 | Y26 | `joy_c_n` |
| 方向 D | 28 | Y25 | `joy_d_n` |
| Push | 31 | W26 | `joy_push_n` |
| Stick Com | 12 | GND | 地 |
| Encoder Com | 12 | GND | 地 |
| 官方标注的 Ground terminal | 12 | GND | 地 |

- 七路输入各用 10kΩ 上拉到 3.3V；旋钮小板与 FPGA 共地。
- 原理图用方向 A/B/C/D 表示端子，实际上下左右由安装方向和程序映射决定。
- **Push 不是完全独立的第五个按钮输入。** 方向操作也会涉及公共按压触点；中心确认需要结合四个方向输入判定。先做稳定状态判定，避免触点动作先后导致短暂误判。
- FPGA 对外部输入做同步。方向键/中心按压可从约 10ms 稳定消抖开始；编码器使用 A/B 正交相序解码，不把旋转简单处理成两个独立按键，也不直接给两相套用长时间按钮消抖。
- 接口至少八根线：七路信号加 GND。若上拉电阻放在旋钮小板上，再引入 3.3V。
- 官方安装孔图注明是安装面视图，封装、插接方向和丝印需核对。

触点关系依据 [Alps 官方规格书](https://tech.alpsalpine.com/cms.media/product_catalog_mu_02_rkjxt1f_en_9fa93dd1ce.pdf)。

## 5. 六个钮子开关

### 5.1 两档分配

| 开关 | J23 针号 | FPGA 引脚 | 信号名 | 闭合状态 |
| --- | --- | --- | --- | --- |
| SW1 | 32 | W25 | `toggle_1_n` | 低电平 |
| SW2 | 33 | U26 | `toggle_2_n` | 低电平 |
| SW3 | 34 | V26 | `toggle_3_n` | 低电平 |
| SW4 | 35 | W20 | `toggle_4_n` | 低电平 |
| SW5 | 36 | Y20 | `toggle_5_n` | 低电平 |
| SW6 | 37 | V19 | `toggle_6_n` | 低电平 |

六路都是 Bank 2 的输入，按 3.3V 逻辑接线。

### 5.2 每路电路

```text
3.3V ---- 10kΩ ----+---- FPGA 输入
                  |
                1kΩ（串联保护预留）
                  |
               开关触点
                  |
                 GND
```

- 断开为高，闭合为低。1kΩ 装入后闭合电压约 0.3V，需结合实际 FPGA 输入低电平规格确认。
- SPST 两脚开关：接信号和 GND。
- SPDT 两档三脚开关：COM 接 GND，其中一个触点接信号，另一个触点不连接，得到两种状态。COM 位置以开关规格或通断测量为准，不假定一定在中间。
- SPDT ON-OFF-ON 三档：用上述接法不能区分全部三档。完整识别通常需要每个开关两路输入，或另设计编码电路；六个三档不能按本表六根输入直接实现。
- DPDT：需要时只使用其中一组触点；带灯开关的灯电源另接，不能经过 FPGA 输入脚供电。
- 选择适合小信号检测的开关，避免把市电/高压或其他供电线路接入这些输入。
- FPGA 使用两级同步和约 10～20ms 的稳定消抖。长线/外露接口考虑 ESD 保护；可预留小电容，但电容不是程序消抖的替代品。

## 6. 七路 HAL49ESO：保留现有数字接线的直接 ADC 方案

### 6.1 器件与封装确认

用户链接物料 C7420984 对应 Hallwee HAL49ESO，SO 为 SOT-23-3L。它输出随磁场变化的模拟电压，不能按数字霍尔开关接到任意 GPIO 后用高低电平读取。

供电按用户确定的 **5V**，在规格书的 3～6.5V 工作范围内；ESP32-S3 仍使用 3.3V 供电，霍尔 OUT 必须经过下面的分压网络，不能直接接 ADC。无磁场时 OUT 预期约为半供电，即约 2.5V，但每颗的偏置、安装磁场和实际量程都需要单独校准。不能把输出始终约 2.5V 当成保证，磁场变化时仍需按全量程设计输入保护。

**焊盘号待确认：** 立创 C7420984 挂出的厂商规格书 V3.2 中：

| 资料位置 | 脚 1 | 脚 2 | 脚 3 |
| --- | --- | --- | --- |
| 第 1 页“脚位定义” | VDD | GND | OUT |
| 第 4 页“封装尺寸”的脚位注释 | 电源 | 输出 | 地 |

这两处互相矛盾，SO 封装的图示编号还需要与 PCB 库编号核对。**不要自行选其中一处当作确认结果，也不要仅凭“通用 SOT-23”或直插 49E 的脚序绘制。** 请让供应商确认本物料的顶视图脚序，并核对实际采用的原理图库和封装库；必要时先在转接测试板上验证。

以下电路中的 VDD/GND/OUT 是功能标签，不等于尚未确认的焊盘号。

资料：[立创 C7420984 对应的 Hallwee V3.2 规格书](https://datasheet.lcsc.com/datasheet/pdf/4c30f55e3c49f4ca4a892a3b844ea483.pdf)。

### 6.2 七路采集分配

| 霍尔编号 | ESP32-S3 GPIO | ADC 单元 | ADC 通道 | 接入信号 |
| --- | --- | --- | --- | --- |
| H1 | GPIO1 | ADC1 | CH0 | `hall_1_adc` |
| H2 | GPIO2 | ADC1 | CH1 | `hall_2_adc` |
| H3 | GPIO14 | ADC2 | CH3 | `hall_3_adc` |
| H4 | GPIO15 | ADC2 | CH4 | `hall_4_adc` |
| H5 | GPIO16 | ADC2 | CH5 | `hall_5_adc` |
| H6 | GPIO17 | ADC2 | CH6 | `hall_6_adc` |
| H7 | GPIO18 | ADC2 | CH7 | `hall_7_adc` |

保持 GPIO4～13 的触摸、RGB、SPI/握手分配不变，不占用 GPIO19/20 的原生 USB。

通道映射已对照本机 ESP-IDF v6.1 的 `components/soc/esp32s3/include/soc/adc_channel.h`，也可查 [乐鑫 S3 ADC 通道文档](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/adc/index.html)。

### 6.3 每颗霍尔的供电和每路输出电路

```text
HAL49ESO VDD ---- 干净的 5V
         GND ---- 公共 GND

每颗 VDD 与 GND 之间：100nF 去耦，尽量靠近器件；可另预留 1µF。

HAL49ESO OUT ---- R1 12kΩ -----+---- 对应 ESP ADC GPIO
                             |
                             +---- R2 10kΩ ---- GND
                             |
                             +---- C 100nF ---- GND
```

- 七颗共用 5V 和 GND，**七个 OUT 各自接独立分压/滤波支路，不能并联**；霍尔与 ESP、FPGA 共地。
- R1、R2 建议 1% 电阻；分压比例约为 `10 / (12 + 10) = 0.4545`。名义 OUT=5V 时 ADC 节点约 2.27V；按 5V 电源 +5% 即 5.25V 核算，名义分压后约 2.39V，留有测量余量。
- 无磁场时若 OUT≈2.5V，分压后 ADC 节点预期约 1.14V，不是仍为 2.5V。恢复霍尔 OUT 电压时，使用校准后的 ADC 节点电压乘以约 2.2，再按实测电阻及零点校准。
- C 放在 ADC 输入侧，靠近 ESP；100nF 与分压网络构成约 292Hz 的低通起点（理想低输出阻抗下），适合慢速位置/控制量。需要更快响应时可减为 10nF，但必须相应调整采样率和抗混叠设计。实际响应还受传感器输出阻抗影响。
- 建议预留每路 OUT 和 ADC 节点测试点。模拟走线远离 SCLK、RGB 大电流回路、开关电源和天线区域。
- 供电容量按七颗传感器及余量核算。规格书 5V 测试条件下单颗最大电流为 4.5mA，七颗为 31.5mA；传感器支路可先按至少 40mA 预算，整板还需计入 ESP 和 RGB 负载。
- 霍尔侧可定义独立三针连接器 `1=5V、2=GND、3=OUT`。这是自定义连接器序号，**不是 HAL49ESO 的芯片焊盘号**。
- 本方案已从原来的 3.3V 供电、4.7kΩ/27kΩ 分压改为 5V 供电、12kΩ/10kΩ 分压。原比例会把 5V 降至约 4.26V，不能沿用。
- 5V 与 ESP 的上电/掉电时序需要一起设计，避免 ESP 未供电时霍尔仍通过 OUT 向 ADC 引脚灌电；分压电阻不能独自解决掉电反灌问题。

S3 ADC 的名义上端测量范围约 3.1V，部分芯片在边界附近表现更差，分压可避免靠近边界。参见 [乐鑫 ADC FAQ](https://docs.espressif.com/projects/esp-faq/en/latest/software-framework/peripherals/adc.html)。

### 6.4 固件与采样限制

- 使用 ESP-IDF `adc_oneshot`，配置 ADC1 和 ADC2 两个单元，12 位、`ADC_ATTEN_DB_12`；ADC 输入不启用数字上拉/下拉。
- 使用 ADC 校准接口换算电压，再按每路的实测偏置、端点和阈值处理。不要假设 `raw / 4095 × 3.3V` 就是准确电压。
- 初步位置采集可从 **每路 1kS/s** 的目标开始，测量实际扫描周期与抖动。七路轮询是顺序采样，**不是七路同步采样**。
- ADC2 与 Wi-Fi 共用资源，驱动提供访问保护。读失败/超时时本次结果无效，不能把它当成正常的零值。需要 Wi-Fi 并保持稳定采样时优先采用第 7 节方案。
- S3 ADC2 的连续 DMA 采集受硬件限制，不把本表七路直接配置成 ADC1+ADC2 连续 DMA；不要靠强制开启 ADC2 DMA 绕过这一限制。
- 位置、磁铁接近检测、拨弦触发可以先用采样值加阈值/滞回验证。**若要采集七根弦的实际振动波形或作为音频拾音，必须重新确认带宽、抗混叠、采样率和通道间时间差；上述 1kS/s 调试起点不适用于完整音频采集。**
- FPGA 与 S3 的 SPI 数据帧可携带霍尔编号、采样值/触发事件、序号；协议尚需后续实现。

限制依据 [乐鑫 ADC Oneshot 文档](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/adc/adc_oneshot.html)及 [ADC Continuous 文档](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/adc/adc_continuous.html)。

## 7. 可选改板方案：七路全部使用 ADC1

**本节不是主表的接线，不与第 6 节混用。仅在愿意重新布置 S3 数字引脚时启用；现有已接线的数字网络不能同时连接霍尔输出。**

若新板尚未投产，希望预留 Wi-Fi 或 ADC1 连续采集，可将五路数字信号移到非 ADC 引脚，保持 FPGA J23 侧针号和 SPI GPIO10～13 不变：

| 数字信号 | 主方案 GPIO | 全 ADC1 改线方案 GPIO |
| --- | --- | --- |
| 触摸 I2C SCL | GPIO4 | GPIO38 |
| 触摸 I2C SDA | GPIO5 | GPIO39 |
| 共用 XRES | GPIO6 | GPIO40 |
| RGB 控制输出 | GPIO7 | GPIO41 |
| FPGA IRQ | GPIO8 | GPIO42 |

改线后霍尔采用：

| 霍尔编号 | GPIO | ADC 单元/通道 |
| --- | --- | --- |
| H1 | GPIO1 | ADC1 CH0 |
| H2 | GPIO2 | ADC1 CH1 |
| H3 | GPIO4 | ADC1 CH3 |
| H4 | GPIO5 | ADC1 CH4 |
| H5 | GPIO6 | ADC1 CH5 |
| H6 | GPIO7 | ADC1 CH6 |
| H7 | GPIO8 | ADC1 CH7 |

该方案仍为顺序扫描，不自动实现七路同步。GPIO39～42 会与外部 GPIO JTAG 功能复用，若使用这些引脚做数字外设，则不要同时连接/启用那组 JTAG。霍尔的分压、滤波、脚序核对要求不变。

若不希望改现有数字线而又需要稳定的七路高速采集，可另选八通道外置 ADC；器件、接口、采样指标和新增引脚需另行确定，不属于本次已分配主方案。

## 8. ESP32-S3 主方案总表

以下均是 GPIO 编号，不是模块焊盘号。

| ESP32-S3 GPIO | 主方案用途 | 方向/备注 |
| --- | --- | --- |
| GPIO1 | 霍尔 H1 | ADC1 CH0 输入 |
| GPIO2 | 霍尔 H2 | ADC1 CH1 输入 |
| GPIO4 | CY8 I2C SCL | 按之前 S3 原理图，开漏总线 |
| GPIO5 | CY8 I2C SDA | 按之前 S3 原理图，开漏总线 |
| GPIO6 | 三颗 CY8 共用 XRES | 复位输出，低有效 |
| GPIO7 | RGB 控制 | 输出，具体灯驱动接口另核对 |
| GPIO8 | FPGA IRQ | 数字输入 |
| GPIO9 | FPGA_READY | 可选数字输入，预留 |
| GPIO10 | FPGA SPI CS_N | 输出 |
| GPIO11 | FPGA SPI MOSI | 输出 |
| GPIO12 | FPGA SPI SCLK | 输出 |
| GPIO13 | FPGA SPI MISO | 输入 |
| GPIO14 | 霍尔 H3 | ADC2 CH3 输入 |
| GPIO15 | 霍尔 H4 | ADC2 CH4 输入 |
| GPIO16 | 霍尔 H5 | ADC2 CH5 输入 |
| GPIO17 | 霍尔 H6 | ADC2 CH6 输入 |
| GPIO18 | 霍尔 H7 | ADC2 CH7 输入 |
| GPIO19 | 保留 USB D- | 不接霍尔 |
| GPIO20 | 保留 USB D+ | 不接霍尔 |
| GPIO43 | 预留 UART0 TX | S3 默认 UART0，不沿用 C3 TX GPIO21 |
| GPIO44 | 预留 UART0 RX | S3 默认 UART0，不沿用 C3 RX GPIO20 |

- **S3 原图的 SCL=GPIO4、SDA=GPIO5，与旧 C3 固件中的 SCL=GPIO5、SDA=GPIO4 相反。** 最终以新板实际网络为准，并修改相应固件常量。
- 三颗 CY8CMBR3116 继续共用一条 I2C 总线，现有地址分别为 0x37、0x38、0x39，保持唯一地址。
- I2C 总线需要上拉；各芯片分支的串联电阻和总线上拉不是同一种作用，不要把串联电阻误当上拉。SPI 和霍尔 OUT 不照搬 I2C 上拉接法。
- N16R8 变体的 GPIO35～37 被 Octal PSRAM 使用，不能因为模块符号上画出来就拿来接外设。
- GPIO0/3/45/46 为启动绑带相关引脚，本方案不分配给开关或霍尔。

模块限制参见 [ESP32-S3-WROOM-1/1U 官方规格书](https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf)。

## 9. 转接板与调试检查清单

- [ ] 核对实体 J23 的 1 脚、奇偶针、间距、插接后镜像；不要仅根据符号左右方向做封装。
- [ ] 未安装 SDRAM 扩展模块；J23 使用的信号没有连接其他会驱动它们的外设。
- [ ] FPGA Bank 2/3 实际电压符合 3.3V 逻辑；没有 5V 接入 S3/FPGA 数字输入。
- [ ] 两板共地，转接板保持完整地平面；长线预留额外地回路，不把 RGB 灯的大电流回流挤进模拟信号回路。
- [ ] J23 没有 3.3V 电源针，数字输入上拉从明确的 3.3V 稳压供电点引入；霍尔使用 5V，不能把 5V 接到数字上拉。若由 J23 第 11 针供电，核对电源容量和掉电时序；两块独立电源的输出不直接并联。
- [ ] LCD 电源电压符合实际模块规格；背光需要大电流时加驱动，不让 FPGA GPIO 直接给整组背光供电。
- [ ] 旋钮两个公共端与 Ground terminal 接地，七路上拉齐全，安装方向已映射。
- [ ] 六个开关确认为两档；若实际为三档，调整 IO 需求与接法。
- [ ] HAL49ESO 原理图库、封装库、顶视图脚序已获得可靠确认，解决规格书 2/3 脚冲突。
- [ ] 每路霍尔 OUT 独立，ADC 端有分压和滤波；磁铁移动全行程时测量输出/ADC 节点，确认不削顶、不超压。
- [ ] 明确霍尔是控制量还是实际波形采集，再确定采样率及滤波。
- [ ] 只选一种霍尔 GPIO 方案；若采用全 ADC1 方案，五路数字线和固件均完成迁移。
- [ ] 新 FPGA 顶层增加 SPI、握手、旋钮和开关端口，配套增加 CST 约束；表里的新用途不会因接线而自动生效。
- [ ] 新 S3 工程设置目标为 esp32s3，更新 I2C/复位/RGB/SPI/ADC 引脚；不直接烧录旧 C3 二进制。
- [ ] 上电先检查电压，再分别测试 LCD、六个开关、旋钮、七路 ADC，最后测试 SPI 双向数据和 IRQ。

## 10. 核对资料

- [Sipeed Tang Mega 138K Pro 官方说明](https://wiki.sipeed.com/hardware/en/tang/tang-mega-138k/mega-138k-pro.html)。
- [Pro Dock 官方原理图](https://dl.sipeed.com/fileList/TANG/Mega_138K_Pro/02_Schematic/TANG_MEGA-138K_Pro-Dock-4071f_Schematics.pdf)，主要核对第 2 页供电选择、第 16 页 J23。
- [当前 LCD 工程 CST](C:/Users/Junejay_Huang/Desktop/gowin-2/distorionpro_screen_mixer/src/audio.cst)。
- [Alps RKJXT1F42001 产品资料](https://tech.alpsalpine.com/e/products/detail/RKJXT1F42001/)。
- [用户给出的立创物料链接](https://so.szlcsc.com/global.html?c=&k=C7420984)。
- [C7420984 对应 Hallwee HAL49E V3.2 PDF](https://datasheet.lcsc.com/datasheet/pdf/4c30f55e3c49f4ca4a892a3b844ea483.pdf)，注意第 1/4 页脚位标注冲突。
- [ESP32-S3 ADC 文档](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/adc/index.html)。

核对方法：按 PDF 核对流程目视检查了 J23 页、旋钮触点图及霍尔的脚位/封装页，再与现有 LCD CST、本机 Gowin 管脚数据库和 ESP-IDF ADC 通道定义交叉核对。未把冲突的霍尔脚位标注作为定论。

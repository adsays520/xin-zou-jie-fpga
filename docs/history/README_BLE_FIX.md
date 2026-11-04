# 蓝牙首条指令后断开：v26 / Android 0.4 修复

`ACK,3,1` 表示应用层第3个包执行失败。它说明S3已收到包并返回了拒收结果；单靠这一行无法区分是文本指令被拒绝、缺少FPGA长包功能、SPI确认超时还是FPGA包校验失败。

旧Android在收到任何非零应用ACK后直接调用 `closeLink()`，所以表现为“有ACK随后断开”。本版改为停止回放和音高控制、清空后续队列、发送一次尽力停止请求，保留BLE连接，允许继续查看状态和重新发送。不会自动重发失败的音符或续传半个上传；真正的GATT链路错误和传输超时仍会终止连接。

实板已找到并修复拒收根因：S3长包路径调用 `spi_device_acquire_bus(...,30ms)`，而实际ESP-IDF驱动只接受 `portMAX_DELAY`，返回 `ESP_ERR_INVALID_ARG`，没有发送SPI数据。已与同一SPI任务里的普通心跳统一使用受支持的调用；重新烧录、独立回读后两次长包查询均成功。FPGA未修改。

旧桌面霍尔页另有版本兼容问题：不接受 `R15-HALL-v3.4.26-BLE` 的后缀，导致不握手、不查询ADC。已修复工作区和本包 `ref/FPGA_ESP_Control/.../violin_r15/hall_panel.py`；重开桌面上位机生效，隐藏真实GUI已与COM30握手验证。实板H1～H6采样更新、校准有效；H7因当前掩码0x3F而未启用。没有改霍尔阈值、布防或引脚。

## 文件与使用

- 安装 `bin/app-debug.apk`：版本0.4-ble-ack-fix，签名与原包一致，可覆盖安装。
- S3完整固件 `bin/s3/s3_ble_led.bin`：版本3.4.26-ble-fix。烧录方法沿用根目录 `flash_s3.ps1` 和 `images.json`。
- 原Android 0.3和S3 v25保留在 `bin/original/`；原封包 `FA_BLE_LED_1103.zip` 没有覆盖。
- FPGA源码、IP、约束和 `mobile_spi2.fs` 未修改。炫彩LED、GPIO3/7交换、八片触摸及I2C200kHz保持。

## 定位板端拒收

手机“设备”页增加“读取蓝牙状态”“检查FPGA转发”。USB也支持以下文本指令：

```text
PING
BLE,STATUS
FPGA,STATUS
BLE,PROBE
```

`BLE,PROBE`使用钢琴音色库状态查询 `A5 B3 00 00 00 16` 经过与手机原始包相同的SPI长包通路，不触发音符、不改音色参数、不上传配置。成功回执为 `OK,BLE,PROBE,RESULT,OK,...`。它验证USB→S3→FPGA转发，不能代替手机BLE实测。

拒收时，新的S3会在ACK前报告 `ERROR,FPGA,BULK,原因,FLAGS,...,LENGTH,...,OPCODE,...`。主要原因：

| 原因 | 含义 |
|---|---|
| NO_CAPABILITY | 当前FPGA回复没有SPI长包能力标志 |
| FRAGMENT_ACK_TIMEOUT | SPI帧未得到匹配CRC/会话/序号的确认 |
| FPGA_PACKET_ERROR | FPGA长包校验报告失败 |
| REPLAY_TIMEOUT | FPGA长包重放等待超过期限 |
| OFFLINE / LOCK_TIMEOUT / PENDING | FPGA离线或S3转发通路暂不可用 |

## 已验证和待验证

真实ESP-IDF和Gradle编译、156项C模块模拟测试、实际Java拒收处理方法回归、3组RTL回归、32份编曲与PC事件一致性、波表0LSB差异、13页面及拒收停止回放/音高流检查通过。APK资源与源码逐字节核对、原签名保持。

板端已更新，SPI探测结果见 `audit/completion.json` 的 `hardware` 字段。手机实际BLE持续连接与听音仍需验证，不能将软件回归或USB转发探测视为无线链路验收。

# 2026-10-19 实机配置写入结果

## 已完成

通过现有 ESP32-S3 原生 USB（COM30，GPIO5 SDA / GPIO4 SCL）实际写入七片 CY8CMBR3116。每片均完成写前备份、RAM连续双份回读、一次 SAVE、状态检查、软件复位及复位后回读。最后另行只读检查，七片的完整128字节均与目标配置完全相同，CRC有效，未回退到出厂默认配置。

用户已确认以 `D:\EZ_CLIK2` 的HEX覆盖板上原配置，再应用演奏设置；不是保留原板阈值、通道屏蔽或引脚功能。D盘32个源文件重新核验SHA256，均未改动。

| 芯片 | 地址 | D盘来源 | 保存后CRC | 结果 |
| --- | --- | --- | --- | --- |
| chip0 | 0x37 | 01 | 0x5BB5 | 保存、复位及回读通过 |
| chip1 | 0x38 | 02 | 0x96C0 | 保存、复位及回读通过 |
| chip2 | 0x39 | 03 | — | 已拆除，配置工具不访问 |
| chip3 | 0x3A | 03a | 0x2EA7 | 保存、复位及回读通过 |
| chip4 | 0x3B | 03B | 0xFA84 | 保存、复位及回读通过 |
| chip5 | 0x3C | 03C | 0xF62F | 保存、复位及回读通过 |
| chip6 | 0x3D | 03D | 0x220C | 保存、复位及回读通过 |
| chip7 | 0x3E | 03E | 0x11A4 | 保存、复位及回读通过 |

七片按钮/滑条长按自动复位均已关闭，Look-for-Touch/Look-for-Proximity间隔统一20ms；不是保证Active扫描周期20ms。保留模板各片地址、阈值、敏感度、滤波、诊断和自动阈值选择。最终SENSOR_EN均为0xFFFF。0x37/0x38等模板的阈值100会覆盖原板的160；0x3E保留模板阈值128和自动阈值选择。

## S3 已恢复演奏固件

写入前已备份S3的0x00000..0x0FFFF区域和完整1MiB应用槽。临时配置桥接只烧写应用区域，没有修改引导、分区或NVS。

写完触摸芯片后，已将原应用槽逐字节恢复至0x10000，并通过独立 `verify-flash` 摘要校验。当前不再运行临时写入桥接，而是原 `R15-I2C-ROBUST-v2` 演奏固件。FPGA、C3及原R15工程没有修改。

- 原应用槽备份：`device_backups/session_20261019_115237/s3_app_slot_before.bin`
- 长度：1048576字节；SHA256：`6bb216420b04ba70bdf81369a5e13458480bb23096911a4a134e751ba0c84fd7`
- 已确认该槽前缀与原R15工作应用一致；原应用SHA256：`a080b372a0ec378d052f25c355194b4f1f73c3ec39a4c8d3a0e704197037dcca`
- 恢复和复核证据：同目录 `s3_restore_flash.log`、`s3_restore_verify.log`、`s3_restore_result.json`。

## 仍需注意的通信问题

写入前的只读诊断发现：部分I2C读取虽然返回成功，数据中途仍会变成错误值及连续0xFF，导致CRC无效。这不只是单纯的地址NACK；尚未用波形测量区分总线电气、芯片状态或控制器时序原因，不能认定改寄存器已经修复根因。

配置工具新增有上限的整幅只读重验：最多六份快照，始终要求连续两份完全一致；RAM阶段还必须与目标逐字节相同才允许SAVE。不会因只读重验重发SAVE或RESET。新增测试后共22项主机测试通过；临时桥接工程已实际编译并使用。

恢复原R15后又只接收20秒日志：记录18条FAIL，其中10条来自已拆除chip2，另8条来自其余芯片；记录3条RETRY_OK，无新的OFFLINE或I2C transaction timeout日志。这是短时观察，不能证明长期稳定，也不能与之前不同测试条件直接比较错误率。

原R15仍保留对chip2的离线探测，所以可能继续打印 `chip=2 addr=0x39 DEVICE_ID` 错误。本次配置桥接和主机工具确实完全排除了0x39，但没有顺便修改原演奏固件的轮询掩码。

## 备份和验证材料

以下路径均位于本工程的 `device_backups/session_20261019_115237`：

- `chips/*.json`：七片完整写前、第一次复位后、目标和最终配置，逐阶段时间及SHA256。七份均为 `saved_reset_verified`。
- `final_touch_verification.json`：独立最终只读检查，七片完整配置与目标一致且CRC有效。
- `completion_audit.json`：七份保存结果、32份D盘原文件未改动及S3恢复验证的汇总。
- `chip0_readback_trials.json`：实际捕获的间歇性无应答错误以外的数据损坏样本。
- `write_chip0_retry.log`、`write_chip1.log`等：每片写入日志，含只读重验记录。
- `restored_r15_observation.log`：恢复原演奏固件后的20秒原始日志。

原板七份写前和第一次复位后快照CRC均有效，已完整归档；`profiles/original_profiles.json`仅代表D盘模板，不应误当成本次写前原板配置。

## 用户下一步

将主控与全部触摸板一起断电再上电，不带电插拔。先逐片测试单键，再测试持续按住超过五秒，最后测试多键演奏。如仍误触或掉线，请保留新的完整日志；配置已实际生效，但通信问题仍需单独排查。无需重新烧录FPGA。

寄存器定义及保存流程依据：[Infineon寄存器TRM](https://www.infineon.com/assets/row/public/documents/30/57/infineon-cy8cmbr3xxx-capsense-express-controllers-registers-trm-additionaltechnicalinformation-en.pdf)、[AN90071设计指南](https://www.infineon.com/dgdl/Infineon-AN90071_CY8CMBR3xxx_CapSense%28R%29_Design_Guide-ApplicationNotes-v09_00-EN.pdf?fileId=8ac78c8c7cdc391c017d07236b6e4698)。

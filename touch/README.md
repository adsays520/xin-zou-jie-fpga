# 当前配置：抗干扰保持，LBR=10单项试验

默认profiles及generate_profiles.py现使用BUTTON_LBR（0x1F）=0x8A，即OVERRIDE=1、10个合格样本。SENSOR_DEBOUNCE=3，IIR与中值滤波开启；S3当前配套v3.4.11变化复读/两轮确认版（I2C=100kHz，扫描配置保持）。Auto reset、20ms Look-for-Touch、阈值、灵敏度、其他基线参数、地址和引脚功能均保持。

八片已保存、复位和完整CRC读回验证；S3原演奏应用恢复且独立读回一致、八片在线。完成证据：C:\Users\Junejay_Huang\Desktop\gowin-2\output\TOUCH_LBR10_20261031_205458\completion_verification.json。本轮只改0x1F与CRC，听感未验收。LBR10是显式试验参数；回退原默认LBR应恢复0x1F=0x00，并重算CRC、保存和复位。完整旧配置见本轮cy8_before.json及before/profiles。

# 抗干扰恢复历史记录：LBR覆盖前

按用户要求恢复关闭抗干扰前的配置：SENSOR_DEBOUNCE（0x1C）=3，DEVICE_CFG0（0x4D）=0x03。八片目标128字节配置与关闭抗干扰前的实际备份逐字节相同。阈值、灵敏度、基线策略、地址和引脚功能保持；按钮长按自动复位关闭、Look-for-Touch间隔20ms、SENSOR_EN=0xFFFF。

八片均已SAVE、复位及完整128字节读回CRC验证；S3恢复v3.4.9抗干扰版并独立读回校验，八片全部在线。配置证据：C:\Users\Junejay_Huang\Desktop\gowin-2\output\TOUCH_RESTORE_GUARD_20261031_200731。此前v3.4.10及关闭滤波实验因误触增加、连击未改善而撤回；本轮恢复不代表连击已修复。

# CY8CMBR3116 八片演奏配置工具

当前入口支持 chip0～chip7（0x37～0x3E），包含已恢复的 chip2/0x39。S3 桥接、主机工具、profiles.json 和 PowerShell -Chip 参数均已同步，不再跳过2号。

配置源为 D:/EZ_CLIK2 八组 HEX/header/IIC，保留各片地址、阈值、灵敏度等；应用之前确认的演奏设置：关闭按钮/滑条长按自动复位、Look-for-Touch间隔20ms，并重算CRC。八片SENSOR_EN均为0xFFFF。

本次八片已完成实机写入、SAVE、复位及完整回读校验。备份和证据见：
C:\Users\Junejay_Huang\Desktop\gowin-2\output\CY8_HEX_FLASH_20261031_162411_retry1

该工具是临时配置桥接，不是演奏固件。默认只读，只有显式 --write/-Write 才写CY8。配置前需备份S3应用；配置后恢复当前 esp32S3/Guitar_Controller_R15/build_r15 的 v3.4.11 演奏程序。演奏固件上电不会自动重写CY8 Flash。

编译：build_config.ps1。仅在临时桥接固件运行时使用以下命令：

```powershell
.\run_config.ps1 -Port COM30
.\run_config.ps1 -Port COM30 -Write -Chip 2
.\run_config.ps1 -Port COM30 -Write
```

每片先确认DEVICE_ID、两份连续一致的128字节配置并备份落盘；RAM写入后必须完整回读相同才允许SAVE。SAVE只发送一次，状态确认、复位并回读后才判成功。异常立即停止，不能因应答不确定而反复擦写；遇到启动诊断禁用传感器，会明确报告，不能把保存成功当成传感器已修复。

旧七片配置及历史写入记录保留于 device_backups、WRITE_RESULT_20261019.md 和本轮主入口同步备份，不作为当前默认策略。

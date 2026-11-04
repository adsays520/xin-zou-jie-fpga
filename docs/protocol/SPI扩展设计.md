# Android BLE / SPI 扩展当前状态（2026-11-03）

已实现并编译：Android BLE GATT → S3分片重组 → SPI kind3 → FPGA整包校验与原子字节重放。kind0触摸、kind1固定控制、kind2霍尔保持兼容。UUID及手机分片格式保持原包协议。

SPI帧64字节：byte6 FIRST/LAST，byte7长度1–48，byte8–55数据，byte56–59 session，byte62–63 CRC16。整包支持6至36字节固定控制束、38字节波表/包络块、266字节bank包。FPGA校验整包的XOR/CRC后再重放；重发通过session/sequence去重，错误不会被当成接收成功。

原3组RTL回归已在当前路径重跑通过：长包长度/CRC/超时/回退，SPI线级CRC/重复/背压，UART半包排斥SPI/SD门控/完整重放。FPGA201项输入摘要与原成功mobile_spi2轮一致，未改RTL、约束及IP。

S3新固件3.4.25-ble-led和Android0.3-ble-led已编译，包含八片触摸、H1扫弦/H2～H7逐弦、BLE、USB控制及赛博LED展示。LED输出已交换为GPIO3的13颗链、GPIO7的14颗链。新增手机灯效页。

边界：原子性覆盖一个完整原始包，不覆盖整段多包上传。PC直连UART与BLE尚无跨端整段事务所有权锁，操作时只使用一个控制端。ACK不等于音源已实际发声；手机实板、上传听音及无线延迟/抖动尚待验收。完整入口与测试记录见根目录README和audit/completion.json。

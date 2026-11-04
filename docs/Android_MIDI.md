# 手机MIDI导入版 v0.5 / 2026-11-04

安装 app-midi-v0.5.apk，可覆盖原 cn.fpga.controller v0.4；签名和应用ID一致，版本号升为5。
S3和FPGA本次均未改写。当前已安装S3 v3.4.27支持实时跟灯；旧固件会显示能力未确认。

操作：
1. 打开App，滑动顶部标签到“MIDI 导入 / 跟灯”。
2. 点“小星星”可离线试导入；也可点资源网站，用手机浏览器下载.mid或.midi。
3. 回App，点“选择文件”，在系统文件选择器的“下载/Downloads”中选择MIDI。
4. 默认只选第一条旋律轨。勾选伴奏，检查映射到吉他/钢琴/Bass/小提琴/鼓；可调速度25%–150%、移调±36。
5. “发送到FPGA演奏”需要连接BLE；也可先“转入编曲编辑”，继续编辑和导出Tang工程。
6. “开始/继续跟灯”只提示实体弦与品位，由人手演奏；暂停、跳转、离开页面或进入后台停止提示。

文件支持：标准MIDI 0/1、PPQ时间制、速度变化、NoteOn/Off、延音踏板、GM乐器分类；最多4MB/20000音符。
MIDI时间变化保留为实际音符时刻。转入现有编曲后使用起始BPM作为时间刻度。
GM乐器映射到板上已有五种音源；不加载SoundFont/PCM，其他控制器、弯音与效果不自动复现。
小提琴最多单声部，钢琴16、吉他32、Bass8；不适配的密集轨道会提示，可减少勾选轨或改映射。
重复钢琴同音的延音重叠会在下一次同音处截开，以适配按音高松音的板端协议；未映射的鼓号显示跳过数量。
跟灯为标准吉他/当前钢琴触摸布局的弦品映射，音域E2–C6；超范围音符跳过，可移调。多音灯显示集合，不能唯一表示所有交叉点。
蓝牙实际时延和手机SAF文件选择仍需真机验证，未宣称端到端抖动小于5ms。

资源网站：
- Mutopia https://www.mutopiaproject.org/ ：曲目有公有领域或CC授权，可下载MIDI。授权 https://www.mutopiaproject.org/legal.html
- Wikimedia Commons https://commons.wikimedia.org/wiki/Category:MIDI_files ：每份文件有授权说明，进入文件页下载原文件。
- BitMidi https://bitmidi.com/ ：作为曲目搜索入口，单曲使用条件需自行核对；不将“可下载”视为全部曲目都有开放授权。
- 已实际下载测试的公有领域示例《致爱丽丝》 https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=931 ：页面点击 MIDI file。

验证：真实Gradle构建、APK签名与资源逐字节核对；9份MIDI/4123音符与桌面解析逐项对照；变速/跨轨踏板/running status/坏文件/重叠同音测试；
412×915 Chromium手机视口中实际文件输入、缓存恢复、选轨、编曲、模拟发送和跟灯清除测试；原ACK拒收和播放队列回归通过。
没有连接到安卓真机，系统文件选择器、浏览器下载和无线实板听音待验证。

源码：Android_MIDI_v0.5_source.zip。保留原v0.4 APK；新源码在 D:/FA_MOBILE_MIDI_1104/android。
构建需要JDK17、Android SDK35/BuildTools34、Gradle8.9，使用build_android.ps1传入工具路径。
JS测试需要Node20+；浏览器测试需要playwright及Chrome，通过NODE_PATH/CHROME_EXE指定安装。

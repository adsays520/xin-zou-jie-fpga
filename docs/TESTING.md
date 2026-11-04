# 离线复核

在完整工程根目录运行。PC便携EXE自带依赖，源码测试需要Python、Tk、numpy、pyserial。

```powershell
.\pc\FPGA_ESP_Control.exe --smoke-test --smoke-report smoke.json
.\pc\FPGA_ESP_Control.exe --mode led --smoke-test --smoke-report led_smoke.json
python tests/run_mobile_checks.py
node tests/test_midi.cjs
node tests/test_playback.cjs
python tests/test_android_ack.py
python tests/test_resource_bridge.py
```

UI测试需要Node的playwright和可用Chromium，可通过CHROME_EXE指定Chrome路径，执行node tests/midi_ui_smoke.cjs。Java测试需要JDK17，设置JAVA_HOME或将javac加入PATH。

桌面MIDI及编曲UI回归：进入pc/drum_bass_pitch_20261013/violin_r15，运行python -m unittest test_midi_guide test_midi_guide_ui -v。

S3 C模块模拟回归：python tests/run_native.py --tcc <TinyCC的tcc.exe>。SPI长包和仲裁RTL回归需Icarus，设置IVERILOG_ROOT后执行python tests/run_all_rtl.py和python tests/run_ingress.py。

本次结果见package_validation.json和evidence。FPGA的原物理报告在fpga/impl；构建输入摘要在fpga_build_inputs.json。此次验证未连接实板，不自动烧录。MIDI跟灯起始帧已修正能力确认后的计时采样顺序；23项相关测试通过。

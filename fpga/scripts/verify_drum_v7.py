import hashlib
import json

from iverilog_runner import ROOT, OUT, compile_sim, simulate

payload = (ROOT / "sd_card/DRUMS.BIN").read_bytes()
(ROOT / "tests/runtime_temp/drums_bytes.hex").write_text("".join(f"{value:02x}\n" for value in payload), encoding="utf-8")
bank = compile_sim("tb_drum_bank_v7", ["src/drums/drum_parameter_bank.v", "tests/tb_drum_bank_v7.sv"])
bank_log = simulate(bank, "drum_bank_v7.log")
assert "PASS DRUM BANK V7:" in bank_log
print(bank_log, flush=True)
reference = ROOT.parent / "ensemble_hall_v6"
original = (reference / "src/drums/drum_synth.v").read_text(encoding="utf-8")
baseline = original.replace("module drum_synth(", "module drum_synth_v6_reference(", 1).replace("kick_modal u_kick", "kick_modal_v6_reference u_kick")
baseline += (reference / "src/drums/kick_modal.v").read_text(encoding="utf-8").replace("module kick_modal(", "module kick_modal_v6_reference(", 1)
snapshot = ROOT / "tests/runtime_temp/drum_v6_reference.v"
snapshot.write_text(baseline, encoding="utf-8")
audio = compile_sim("tb_drum_audio_v7", ["src/drums/drum_synth.v", "src/drums/kick_modal.v",
                    "src/performance_mixer.v", str(snapshot), "tests/tb_drum_audio_v7.sv"])
audio_log = simulate(audio, "drum_audio_v7.log", timeout=1800)
assert "PASS DRUM AUDIO V7:" in audio_log
proof = {"passed": True, "reference_source_sha256": hashlib.sha256(original.encode()).hexdigest(),
         "bank_log": bank_log, "audio_log": audio_log, "physical_timing_accepted": False}
(OUT / "drum_v7_result.json").write_text(json.dumps(proof, indent=2), encoding="utf-8")
print(audio_log, flush=True)

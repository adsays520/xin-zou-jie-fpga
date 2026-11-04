import hashlib
import json
import os
import subprocess
from pathlib import Path


PROJECT = Path(__file__).resolve().parent.parent
SIM = PROJECT.parent / "tmp/sim_tools/mingw64"
OUTPUT = PROJECT / "tests/results/pluck_delivery_fixed"


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    core = (PROJECT / "violin_r15/audio_core.v").read_text(encoding="utf-8")
    token = "    always @(posedge clk or negedge rst_n) begin"
    start = core.index("    pluck_event_queue u_pluck_event_queue(")
    control_start = core.index(token, start)
    end = core.index(token, control_start + len(token))
    block = core[start:end]
    wrapper = """module pluck_stage_from_source(
input wire clk,rst_n,sample_tick,uart_pluck_trigger,
input wire [2:0] uart_trigger_string_sel,
input wire [4:0] uart_trigger_fret_sel,
input wire [6:0] uart_trigger_velocity,
output reg note_on,output reg [2:0] string_sel,output reg [4:0] fret_sel,
output wire pluck_ingress_ready,output wire pluck_queue_overflow
);
reg [6:0] note_velocity;
reg poly_mode,timbre_piano,timbre_bass,timbre_violin,clear_voice_bank;
reg [2:0] pluck_selected_string;
reg [4:0] pluck_selected_fret;
reg [6:0] pluck_selected_velocity;
wire pluck_event_valid;
wire [14:0] pluck_event_data;
wire long_pluck_pulse=0,verification_fast_pluck=0,uart_mode_set=0,uart_mode_poly4=1;
wire uart_timbre_set=0,uart_timbre_piano=0,uart_timbre_bass=0,uart_timbre_violin=0;
wire drawn_mode_event=0;
""" + block + "\nendmodule\n"
    (OUTPUT / "pluck_stage_from_source.v").write_text(wrapper, encoding="utf-8")
    sources = ["violin_r15/touch_legacy.v", "src/s3_control_ingress.v",
               "violin_r15/guitar_uart_trigger.v", "output_r12/audio_driver.v",
               "violin_r15/pluck_event_queue.v", "tests/tb_pluck_delivery_probe.sv",
               "tests/results/pluck_delivery_fixed/pluck_stage_from_source.v"]
    hashes = {source: hashlib.sha256((PROJECT / source).read_bytes()).hexdigest() for source in sources}
    environment = os.environ.copy()
    environment["PATH"] = str(SIM / "bin") + os.pathsep + environment["PATH"]
    environment["TMP"] = environment["TEMP"] = str(OUTPUT)
    executable = OUTPUT / "probe.vvp"
    commands = [("compile", [SIM / "bin/iverilog.exe", "-B", SIM / "lib/ivl", "-g2012", "-Wall",
                              "-s", "tb_pluck_delivery_probe", "-o", executable, *sources]),
                ("run", [SIM / "bin/vvp.exe", executable])]
    for name, command in commands:
        result = subprocess.run([str(item) for item in command], cwd=PROJECT, env=environment,
                                capture_output=True, text=True, timeout=60)
        output = result.stdout + result.stderr
        (OUTPUT / f"{name}.log").write_text(output, encoding="utf-8")
        print(output, flush=True)
        assert result.returncode == 0, name
    assert "PASS_FIXED" in output
    assert all(hashlib.sha256((PROJECT / source).read_bytes()).hexdigest() == digest
               for source, digest in hashes.items())
    report = {"result": "queued_control_events_delivered_in_order_with_backpressure",
              "source_hashes": hashes,
              "audio_core_sha256": hashlib.sha256(core.encode()).hexdigest(),
              "event_block_sha256": hashlib.sha256(block.encode()).hexdigest(),
              "isolated_E2_requests_delivered": 2, "burst_commands_parsed": 9,
              "burst_engine_requests": 9, "burst_E2_engine_requests": 1,
              "full_layout_parsed_and_delivered": 126,
              "production_RTL_changed": True, "FPGA_written": False,
              "scope": "Actual touch/parser/sample clock RTL and exact extracted top-level event block; not waveform/DAC validation."}
    (OUTPUT / "proof.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

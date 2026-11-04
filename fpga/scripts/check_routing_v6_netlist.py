from collections import Counter
import json
import re

from build_hall_piano_v4 import ROOT, digest


def inspect(path):
    source = path.read_text(encoding="utf-8")
    matches = re.findall(r"(?ms)^module drum_synth\s*\(.*?^endmodule", source)
    assert len(matches) == 1, "Expected one drum synthesis module"
    module = matches[0]
    cells = re.findall(r"(?m)^\s+(\w+)\s+([^\n]+?)\s*\(", module)
    counts = Counter(primitive for primitive, instance in cells)
    phase_registers = [instance for primitive, instance in cells
                       if primitive.startswith("DFF") and instance.startswith("\\phase[")]
    phase_rams = [{"primitive": primitive, "instance": instance}
                  for primitive, instance in cells
                  if primitive in ("SDPB", "SDPX9B", "DPB", "DPX9B", "SP", "SPX9", "SDP36KE")
                  and "phase" in instance]
    return {"sha256": digest(path), "cells": sum(counts.values()),
            "flops": sum(count for primitive, count in counts.items() if primitive.startswith("DFF")),
            "phase_array_flops": len(phase_registers), "phase_block_rams": phase_rams,
            "primitive_counts": dict(counts)}


def main():
    baseline = ROOT.parent / "ensemble_hall_v4/impl/gwsynthesis/ensemble_hall_piano_v4.vg"
    candidate = ROOT / "impl/gwsynthesis/ensemble_hall_piano_v6.vg"
    before, after = inspect(baseline), inspect(candidate)
    assert before["phase_array_flops"] == 2304, before
    assert after["phase_array_flops"] == 0 and after["phase_block_rams"], after
    assert before["flops"] - after["flops"] >= 2200, (before["flops"], after["flops"])
    assert before["cells"] > after["cells"], (before["cells"], after["cells"])
    proof = {"passed": True, "baseline": before, "candidate": after,
             "removed_drum_flops": before["flops"] - after["flops"],
             "removed_drum_cells": before["cells"] - after["cells"],
             "scope": "Visible synthesis structure; not physical wire length or final timing",
             "physical_timing_accepted": False}
    (ROOT / "tests/results/routing_v6_netlist.json").write_text(json.dumps(proof, indent=2), encoding="utf-8")
    print("PASS V6 routing structure:", json.dumps({name: value for name, value in proof.items()
                                                   if name not in ("baseline", "candidate")}), flush=True)


if __name__ == "__main__":
    main()

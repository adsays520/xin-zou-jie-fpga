from collections import Counter
import json
import re

from build_hall_piano_v4 import ROOT, digest


def inspect(path):
    code = path.read_text(encoding="utf-8")
    modules = {}
    for match in re.finditer(r"(?ms)^module\s+(\S+)\s*\(.*?^endmodule", code):
        if match[1] == "drum_synth" or match[1].startswith(("drum_parameter_bank", "kick_modal")):
            cells = re.findall(r"(?m)^\s+(\w+)\s+([^\n]+?)\s*\(", match[0])
            counts = Counter(primitive for primitive, instance in cells)
            modules[match[1]] = {"cells": sum(counts.values()), "primitives": dict(counts),
                                "phase_registers": sum(primitive.startswith("DFF") and instance.startswith("\\phase[")
                                                       for primitive, instance in cells)}
    return {"sha256": digest(path), "modules": modules}


def main():
    baseline = inspect(ROOT.parent / "ensemble_hall_v6/impl/gwsynthesis/ensemble_hall_piano_v6.vg")
    candidate = inspect(ROOT / "impl/gwsynthesis/ensemble_hall_piano_v7.vg")
    bank = [module for name, module in candidate["modules"].items() if name.startswith("drum_parameter_bank")]
    assert len(bank) == 1 and bank[0]["primitives"].get("SDPB", 0) >= 1, bank
    assert candidate["modules"]["drum_synth"]["phase_registers"] == 0
    assert candidate["modules"]["drum_synth"]["primitives"].get("LUT3", 0) < baseline["modules"]["drum_synth"]["primitives"].get("LUT3", 0)
    previous_cells = sum(module["cells"] for module in baseline["modules"].values())
    current_cells = sum(module["cells"] for module in candidate["modules"].values())
    assert current_cells < previous_cells, (previous_cells, current_cells)
    proof = {"passed": True, "baseline": baseline, "candidate": candidate,
             "removed_visible_drum_cells": previous_cells - current_cells,
             "scope": "Visible synthesis structure only; final routing and timing pending"}
    (ROOT / "tests/results/routing_v7_structure.json").write_text(json.dumps(proof, indent=2), encoding="utf-8")
    print("PASS V7 routing structure: actual parameter block RAM; no phase flop bank; fewer visible drum cells", flush=True)


if __name__ == "__main__":
    main()

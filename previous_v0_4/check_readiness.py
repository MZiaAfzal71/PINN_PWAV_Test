#!/usr/bin/env python3
"""Report the inherited direct-enthalpy gate; exit 2 while it is unmet."""
from pathlib import Path
import csv
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parent


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest_path = ROOT / "MANIFEST.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for relative, metadata in manifest["files"].items():
            if sha256(ROOT / relative) != metadata["sha256"]:
                raise SystemExit("Release integrity failure: " + relative)
    with (ROOT / "frozen" / "enthalpy_primary_labels.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    approved = [
        row for row in rows
        if row["split"] == "train"
        and row["decision"] == "approve_primary_calorimetry"
        and row["training_allowed"] == "True"
        and row["independent_of_pressure_verified"] == "True"
    ]
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    molecules = {row["molecule_id"] for row in approved}
    required = config["minimum_independent_training_enthalpy_molecules"]
    ready = len(approved) == len(rows) and len(molecules) >= required
    result = {
        "status": "READY" if ready else "HOLD_ENTHALPY_PROVENANCE",
        "approved_direct_enthalpy_labels": len(approved),
        "approved_direct_enthalpy_training_molecules": len(molecules),
        "required_training_molecules": required,
        "additional_training_molecules_needed": max(0, required - len(molecules)),
        "nist_gamma_constraints": 14,
        "gamma_constraints_count_toward_direct_H_gate": False,
        "reason": "The inherited project gate requires 100 training molecules with strict direct-H labels; raw gamma constraints and sensitivity-only published L values do not count.",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if ready else 2


if __name__ == "__main__":
    sys.exit(main())

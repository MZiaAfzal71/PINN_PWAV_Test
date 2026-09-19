#!/usr/bin/env python3
"""Verify release integrity, arithmetic, tier separation, and frozen splits."""
from collections import Counter
from decimal import Decimal as D, ROUND_HALF_UP, getcontext
from pathlib import Path
import argparse
import csv
import hashlib
import json

getcontext().prec = 50
ROOT = Path(__file__).resolve().parent
PARENT = ROOT / "previous_v0_3"
BASE = PARENT / "baseline_v0_1"
checks = []


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(condition, description):
    if not condition:
        raise AssertionError(description)
    checks.append(description)


def near(a, b, tolerance=D("1e-11")):
    return abs(D(a) - D(b)) <= tolerance


def verify():
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    parent_manifest_path = PARENT / "MANIFEST.json"
    check(sha256(parent_manifest_path) == config["parent_manifest_sha256"], "Parent v0.3 manifest hash retained")
    parent_manifest = json.loads(parent_manifest_path.read_text(encoding="utf-8"))
    for relative, metadata in parent_manifest["files"].items():
        check(sha256(PARENT / relative) == metadata["sha256"], "Unchanged parent file: " + relative)

    current_labels_path = ROOT / "frozen" / "enthalpy_primary_labels.csv"
    parent_labels_path = PARENT / "frozen" / "enthalpy_primary_labels.csv"
    check(sha256(current_labels_path) == sha256(parent_labels_path), "Strict label export is byte-identical to v0.3")
    check(
        sha256(ROOT / "frozen" / "training_enthalpy_molecules.csv")
        == sha256(PARENT / "frozen" / "training_enthalpy_molecules.csv"),
        "Strict molecule export is byte-identical to v0.3",
    )
    labels = read_csv(current_labels_path)
    check(len(labels) == 42, "Exactly 42 strict labels retained")
    check(len({row["molecule_id"] for row in labels}) == 41, "Exactly 41 strict training molecules retained")
    for row in labels:
        check(row["split"] == "train", "Strict label remains in train: " + row["record_id"])
        check(row["training_allowed"] == "True", "Strict label remains training-approved: " + row["record_id"])
        check(row["independent_of_pressure_verified"] == "True", "Strict label retains pressure-independence flag: " + row["record_id"])

    parent_candidates = {row["record_id"]: row for row in read_csv(PARENT / "frozen" / "enthalpy_candidates_reviewed.csv")}
    candidates = {row["record_id"]: row for row in read_csv(ROOT / "frozen" / "enthalpy_candidates_reviewed.csv")}
    check(len(candidates) == len(parent_candidates) == 751, "All 751 candidate IDs preserved exactly once")
    check(set(candidates) == set(parent_candidates), "No candidate ID added or removed")

    inputs = {row["record_id"]: row for row in read_csv(ROOT / "review" / "nist_ancillary_inputs.csv")}
    parent_hold = {row["record_id"]: row for row in read_csv(PARENT / "frozen" / "enthalpy_nist_ancillary_hold.csv")}
    check(set(inputs) == set(parent_hold) and len(inputs) == 14, "Fourteen NIST input rows map exactly to the held parent rows")
    for record_id, old in parent_candidates.items():
        new = candidates[record_id]
        check(
            all(new[key] == old[key] for key in ("record_id", "molecule_id", "inchi", "name", "split", "component_id")),
            "Candidate identity and partition unchanged: " + record_id,
        )
        if record_id not in inputs:
            check(
                all(new[key] == old[key] for key in ("H_kJ_mol", "T_K", "decision", "training_allowed")),
                "Non-NIST scientific decision inherited: " + record_id,
            )
        else:
            check(new["training_allowed"] == "False", "NIST published L excluded from strict training: " + record_id)
            check(new["independent_of_pressure_verified"] == "False", "NIST published L is not pressure-independent: " + record_id)
            check(new["v0_4_gamma_constraint_ready"] == "True", "NIST gamma constraint tier recorded: " + record_id)

    reconstruction = {row["record_id"]: row for row in read_csv(ROOT / "evidence" / "nist_ancillary_reconstruction.csv")}
    sensitivity = {row["record_id"]: row for row in read_csv(ROOT / "frozen" / "enthalpy_nist_sensitivity_labels.csv")}
    constraints = {row["record_id"]: row for row in read_csv(ROOT / "frozen" / "enthalpy_nist_gamma_constraints.csv")}
    gamma_checks = {row["record_id"]: row for row in read_csv(ROOT / "evidence" / "nist_gamma_constraint_checks.csv")}
    check(set(reconstruction) == set(sensitivity) == set(constraints) == set(gamma_checks) == set(inputs), "All four NIST exports have the same 14 IDs")

    T = D(config["nist_historical_absolute_temperature_K"])
    t_C = D("25")
    ln10 = D(10).ln()
    conversion = D(config["nist_joule_conversion_factor"])
    energy_factor = D(config["pressure_conversion_Pa_per_mmHg"]) * D("1e-6")
    nearest_matches = 0
    direct_lineages = 0
    for record_id, item in inputs.items():
        source = parent_hold[record_id]
        rec = reconstruction[record_id]
        mass = D(source["molar_mass_g_mol"])
        if item["molar_volume_25C_mL_mol"]:
            volume = D(item["molar_volume_25C_mL_mol"])
        else:
            dt = t_C - D(item["density_t0_C"])
            density = (
                D(item["density_d0_g_mL"])
                + D("1e-3") * D(item["density_alpha"]) * dt
                + D("1e-6") * D(item["density_beta"]) * dt**2
                + D("1e-9") * D(item["density_gamma"]) * dt**3
            )
            check(near(rec["density_25C_g_mL"], density), "ICT n-decane density equation reproduced")
            volume = mass / density
        A, B, C = D(item["antoine_A"]), D(item["antoine_B"]), D(item["antoine_C_C"])
        p = ((A - B / (C + t_C)) * ln10).exp()
        dp_dT = ln10 * p * B / (C + t_C) ** 2
        beta = T * (volume / mass) * dp_dT * energy_factor
        published = D(source["beta_intJ_g"])
        nearest = beta.quantize(D("0.01"), rounding=ROUND_HALF_UP)
        match = nearest == published
        nearest_matches += match
        direct = item["vapor_pressure_source_directly_in_cited_beta_pair"] == "True"
        direct_lineages += direct
        check(near(rec["molar_volume_25C_mL_mol"], volume), "Archival volume arithmetic: " + record_id)
        check(near(rec["p_sat_25C_mmHg"], p), "Antoine pressure arithmetic: " + record_id)
        check(near(rec["dp_sat_dT_25C_mmHg_K"], dp_dT), "Antoine derivative arithmetic: " + record_id)
        check(near(rec["reconstructed_beta_int_J_g"], beta), "Beta reconstruction arithmetic: " + record_id)
        check(rec["nearest_0.01_matches_published"] == str(match), "Printed-precision decision: " + record_id)
        check(rec["archival_lineage_complete"] == str(direct), "Exact cited/surrogate slope classification: " + record_id)

        gamma = D(source["mean_gamma_intJ_g"])
        L = D(source["primary_H"])
        check(gamma - published == L, "Printed gamma minus beta equals L: " + record_id)
        scale = conversion * mass / D("1000")
        check(near(constraints[record_id]["gamma_abs_kJ_mol"], gamma * scale), "Gamma unit conversion: " + record_id)
        check(near(sensitivity[record_id]["published_L_abs_kJ_mol"], L * scale), "Sensitivity L unit conversion: " + record_id)
        check(sensitivity[record_id]["use_for_primary_training"] == "False", "Sensitivity L cannot enter primary training: " + record_id)
        check(sensitivity[record_id]["use_for_validation"] == "False" and sensitivity[record_id]["use_for_test"] == "False", "Sensitivity L cannot enter evaluation: " + record_id)
        check(constraints[record_id]["constraint_ready"] == "True", "Gamma constraint is complete: " + record_id)
        check(constraints[record_id]["direct_enthalpy_label"] == "False", "Gamma is not relabeled as direct H: " + record_id)
        check(constraints[record_id]["held_out_pressure_targets_permitted"] == "False", "Gamma constraint forbids held-out pressure targets: " + record_id)
        check(gamma_checks[record_id]["converted_gamma_minus_beta_equals_converted_L"] == "True", "Converted gamma-beta identity: " + record_id)

    check(nearest_matches == 7, "Exactly 7 of 14 beta values reproduce by nearest-cent rounding")
    check(direct_lineages == 12, "Exactly 12 pressure-slope inputs come directly from the cited API table family")
    check(sum(row["nearest_0.01_matches_published"] == "False" for row in reconstruction.values()) == 7, "Exactly 7 printed-precision mismatches are retained")
    check(sum(row["archival_lineage_complete"] == "False" for row in reconstruction.values()) == 2, "Two surrogate slope lineages are disclosed")

    overlap = {row["record_id"]: row for row in read_csv(ROOT / "evidence" / "nist_pressure_lineage_overlap.csv")}
    pressure = read_csv(BASE / "frozen" / "pressure_observations.csv")
    for record_id, row in overlap.items():
        source_rows = [x for x in pressure if x["molecule_id"] == row["molecule_id"]]
        check(int(row["frozen_pressure_rows"]) == len(source_rows), "Molecule-specific pressure-row count: " + record_id)
        check(row["split"] == "train" and all(x["split"] == "train" for x in source_rows), "No partition bridge for NIST molecule: " + record_id)
        check(row["overlaps_nist_measurement_doi"] == "False", "No NIST measurement DOI overlap: " + record_id)
        check(row["overlaps_any_archival_document_doi"] == "False", "No archival DOI overlap with frozen pressure: " + record_id)
    check(len(overlap) == 14, "Pressure-lineage receipt covers all 14 NIST molecules")

    assignments = read_csv(BASE / "frozen" / "split_assignments.csv")
    check(Counter(row["split"] for row in assignments) == {"train": 492, "validation": 106, "test": 105}, "Frozen molecular split counts retained")
    episodes = read_csv(BASE / "frozen" / "episodes.csv")
    check(sum(row["split"] == "test" and row["pressure_ceiling_Pa"] == "20000" for row in episodes) == 78, "Primary 20 kPa test episodes retained")
    check(len(read_csv(BASE / "frozen" / "test_anchors.csv")) == 234, "Primary test anchors retained")
    check(len(read_csv(BASE / "frozen" / "test_cold_targets.csv")) == 512, "Primary cold targets retained")

    queue = read_csv(ROOT / "review" / "remaining_verification_queue.csv")
    check(all(row["reference_code"] != "1947OSB/GIN" for row in queue), "Completed NIST audit removed from remaining queue")
    check(queue[0]["reference_code"] == "1977MAN/SEL", "Mansson 1977 is the highest remaining source opportunity")
    check("full_text_not_obtained" in queue[0]["row_level_review_status"], "Mansson access limitation remains explicit")
    resolved = read_csv(ROOT / "review" / "resolved_source_decisions.csv")
    check(len(resolved) == 1 and resolved[0]["gamma_constraints_frozen"] == "14", "Resolved NIST decision receipt reconciles")

    summary = json.loads((ROOT / "frozen" / "summary.json").read_text(encoding="utf-8"))
    check(summary["strict_primary_labels"] == 42 and summary["strict_primary_training_molecules"] == 41, "Summary strict coverage reconciles")
    check(summary["additional_training_molecules_needed"] == 59, "Original 100-molecule gate remains 59 short")
    check(summary["nist_beta_nearest_cent_matches"] == 7 and summary["nist_beta_nearest_cent_mismatches"] == 7, "Summary beta audit reconciles")
    check(summary["nist_gamma_physics_constraints"] == summary["nist_published_L_sensitivity_labels"] == 14, "Summary NIST tiers reconcile")
    check(summary["status"] == "HOLD_ENTHALPY_PROVENANCE", "Scientific readiness remains on hold")
    check(config["model_fits_performed"] is False and summary["model_fits_performed"] is False, "No model fit represented")
    check(config["test_targets_used_for_label_decisions"] is False and summary["test_targets_used_for_label_decisions"] is False, "No test target informed label decisions")
    check(not list(ROOT.rglob("*.pdf")), "No third-party PDF redistributed in the release")

    result = {
        "status": "PASS",
        "checks_passed": len(checks),
        "strict_primary_labels": 42,
        "strict_primary_training_molecules": 41,
        "additional_training_molecules_needed": 59,
        "nist_beta_matches": 7,
        "nist_beta_mismatches": 7,
        "nist_gamma_constraints": 14,
        "scientific_readiness": "HOLD_ENTHALPY_PROVENANCE",
        "scope": "Integrity, exact mappings, archival-input arithmetic, tier separation, and split/leakage checks; not independent experimental replication.",
    }
    manifest_path = ROOT / "MANIFEST.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for relative, metadata in manifest["files"].items():
            check(sha256(ROOT / relative) == metadata["sha256"], "Release file hash: " + relative)
        result["checks_passed"] = len(checks)
        result["manifest_files_verified"] = len(manifest["files"])
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-validation", action="store_true")
    args = parser.parse_args()
    result = verify()
    if args.write_validation:
        (ROOT / "evidence" / "validation.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    print(json.dumps(result, indent=2, sort_keys=True))

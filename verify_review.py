#!/usr/bin/env python3
"""Verify v0.5 identity, access, temperature-window, and freeze invariants."""
from collections import Counter
from decimal import Decimal as D
from pathlib import Path
import argparse
import csv
import hashlib
import json

ROOT = Path(__file__).resolve().parent
PARENT = ROOT / "previous_v0_4"
BASE = PARENT / "previous_v0_3" / "baseline_v0_1"
TARGET = "1996VIT/CHA"


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    checks = []

    def check(condition, label):
        if not condition:
            raise AssertionError(label)
        checks.append(label)

    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    parent_manifest_path = PARENT / "MANIFEST.json"
    check(sha256(parent_manifest_path) == config["parent_manifest_sha256"], "Parent manifest hash")
    parent_manifest = json.loads(parent_manifest_path.read_text(encoding="utf-8"))
    check(parent_manifest["release_id"] == config["parent_release_id"], "Parent release identity")
    for relative, metadata in parent_manifest["files"].items():
        check(sha256(PARENT / relative) == metadata["sha256"], "Parent file hash: " + relative)

    inherited_files = (
        "enthalpy_primary_labels.csv",
        "training_enthalpy_molecules.csv",
        "enthalpy_nist_ancillary_hold.csv",
        "enthalpy_nist_gamma_constraints.csv",
        "enthalpy_nist_sensitivity_labels.csv",
    )
    for name in inherited_files:
        check(sha256(ROOT / "frozen" / name) == sha256(PARENT / "frozen" / name), "Inherited frozen file unchanged: " + name)

    parent_candidates = {row["record_id"]: row for row in read_csv(PARENT / "frozen" / "enthalpy_candidates_reviewed.csv")}
    current = {row["record_id"]: row for row in read_csv(ROOT / "frozen" / "enthalpy_candidates_reviewed.csv")}
    check(set(current) == set(parent_candidates) and len(current) == 751, "All 751 candidate identities retained")
    target_ids = {record_id for record_id, row in parent_candidates.items() if TARGET in json.loads(row["reference_codes_json"])}
    check(len(target_ids) == 19, "Exactly 19 1996VIT/CHA candidates")
    check(len({parent_candidates[x]["molecule_id"] for x in target_ids}) == 5, "Exactly five 1996VIT/CHA molecules")

    identity_keys = ("record_id", "molecule_id", "inchi", "name", "split", "component_id", "H_kJ_mol", "T_K")
    for record_id, old in parent_candidates.items():
        new = current[record_id]
        check(all(new[key] == old[key] for key in identity_keys), "Candidate identity and value unchanged: " + record_id)
        if record_id in target_ids:
            check(new["training_allowed"] == "False" and new["v0_5_training_allowed"] == "False", "Target remains excluded: " + record_id)
            check(new["decision"] == "hold_primary_table_and_method_unverified", "Explicit target hold: " + record_id)
            check(new["primary_numeric_table_verified"] == "False" and new["full_primary_methods_verified"] == "False", "No primary-table overclaim: " + record_id)
            check(new["source_review_status"] == "bibliographic_identity_resolved_primary_full_text_unavailable", "Access status retained: " + record_id)
        else:
            check(new["decision"] == old["decision"] and new["training_allowed"] == old["training_allowed"], "Non-target decision inherited: " + record_id)

    decisions = read_csv(ROOT / "review" / "viton_chavret_candidate_decisions.csv")
    check({row["record_id"] for row in decisions} == target_ids, "Decision table covers all and only target rows")
    statuses = Counter(row["temperature_window_status"] for row in decisions)
    check(statuses == {
        "within_reported_measurement_window": 14,
        "outside_reported_measurement_window_below": 4,
        "outside_reported_measurement_window_above": 1,
    }, "Temperature-window counts are 14 in, 4 below, 1 above")
    for row in decisions:
        t = D(row["T_K"])
        expected = "within_reported_measurement_window" if D("313") <= t <= D("344") else (
            "outside_reported_measurement_window_below" if t < D("313") else "outside_reported_measurement_window_above"
        )
        check(row["temperature_window_status"] == expected, "Row-level temperature classification: " + row["record_id"])
        check(row["training_allowed"] == "False", "No triaged candidate promoted: " + row["record_id"])
        check(row["exact_primary_numeric_table_verified"] == "False", "Exact numeric table remains unverified: " + row["record_id"])
    check(sha256(ROOT / "evidence" / "source_temperature_window_audit.csv") == sha256(ROOT / "review" / "viton_chavret_candidate_decisions.csv"), "Evidence and decision window tables agree")

    identities = {row["assertion_id"]: row for row in read_csv(ROOT / "evidence" / "source_identity_resolution.csv")}
    check(set(identities) == {"code_mapping", "official_later_chapter", "experimental_window", "document_equivalence"}, "Four identity assertions recorded")
    check(identities["code_mapping"]["status"] == "verified_secondary_bibliography", "Reference-code mapping status")
    check(identities["experimental_window"]["status"] == "verified_official_abstract", "Official abstract status")
    check(identities["document_equivalence"]["status"] == "unverified", "ELDATA/Springer equivalence not assumed")

    access = read_csv(ROOT / "evidence" / "source_access_audit.csv")
    check(len(access) == 4, "Four access records retained")
    check(all(row["full_primary_text_obtained"] == "False" for row in access), "No unavailable full text is represented as obtained")
    check(all(row["primary_numeric_table_obtained"] == "False" for row in access), "No unavailable primary table is represented as obtained")
    check({row["reference_code"] for row in access} == {"1977MAN/SEL", "1926MAT", "1996VIT/CHA", "1996VIT/CHA_RELATED_1998"}, "Access audit source set")

    queue = read_csv(ROOT / "review" / "remaining_verification_queue.csv")
    check(queue[0]["reference_code"] == "1977MAN/SEL", "Månsson remains highest-yield open source")
    q = {row["reference_code"]: row for row in queue}
    check("full_primary_text_not_obtained" in q["1977MAN/SEL"]["row_level_review_status"], "Månsson full-text blocker explicit")
    check("full_primary_text_not_obtained" in q["1926MAT"]["row_level_review_status"], "Mathews full-text blocker explicit")
    check("temperature_window_triaged" in q[TARGET]["row_level_review_status"], "Viton/Chavret triage completion explicit")

    resolved = read_csv(ROOT / "review" / "resolved_source_decisions.csv")
    target_resolution = [row for row in resolved if row["reference_code"] == TARGET]
    check(len(target_resolution) == 1, "One Viton/Chavret resolution receipt")
    check(target_resolution[0]["strict_primary_labels_added"] == "0", "Viton/Chavret added zero strict labels")

    strict = read_csv(ROOT / "frozen" / "enthalpy_primary_labels.csv")
    check(len(strict) == 42, "Strict label count remains 42")
    check(len({row["molecule_id"] for row in strict if row["split"] == "train"}) == 41, "Strict training-molecule count remains 41")
    check(all(row["split"] == "train" for row in strict), "No validation/test enthalpy labels")
    assignments = read_csv(BASE / "frozen" / "split_assignments.csv")
    check(Counter(row["split"] for row in assignments) == {"train": 492, "validation": 106, "test": 105}, "Molecular split counts retained")
    episodes = read_csv(BASE / "frozen" / "episodes.csv")
    check(sum(row["split"] == "test" and row["pressure_ceiling_Pa"] == "20000" for row in episodes) == 78, "Primary test episodes retained")
    check(len(read_csv(BASE / "frozen" / "test_anchors.csv")) == 234, "Primary test anchors retained")
    check(len(read_csv(BASE / "frozen" / "test_cold_targets.csv")) == 512, "Primary cold targets retained")

    summary = json.loads((ROOT / "frozen" / "summary.json").read_text(encoding="utf-8"))
    check(summary["version"] == "0.5.0", "Summary version")
    check(summary["strict_primary_labels"] == 42 and summary["strict_primary_training_molecules"] == 41, "Summary strict coverage")
    check(summary["additional_training_molecules_needed"] == 59, "Gate remains 59 molecules short")
    check(summary["viton_chavret_candidate_rows_audited"] == 19, "Summary Viton/Chavret rows")
    check(summary["viton_chavret_rows_inside_reported_measurement_window"] == 14, "Summary in-window rows")
    check(summary["viton_chavret_rows_below_reported_measurement_window"] == 4, "Summary below-window rows")
    check(summary["viton_chavret_rows_above_reported_measurement_window"] == 1, "Summary above-window rows")
    check(summary["viton_chavret_strict_labels_added"] == 0, "Summary zero promotions")
    check(summary["status"] == "HOLD_ENTHALPY_PROVENANCE", "Scientific readiness remains on hold")
    check(config["model_fits_performed"] is False and summary["model_fits_performed"] is False, "No model fit represented")
    check(config["test_targets_used_for_label_decisions"] is False and summary["test_targets_used_for_label_decisions"] is False, "No test target informed label decisions")
    check(not list(ROOT.rglob("*.pdf")), "No third-party PDF redistributed")

    result = {
        "status": "PASS",
        "checks_passed": len(checks),
        "strict_primary_labels": 42,
        "strict_primary_training_molecules": 41,
        "additional_training_molecules_needed": 59,
        "viton_chavret_candidate_rows": 19,
        "viton_chavret_rows_in_window": 14,
        "viton_chavret_rows_outside_window": 5,
        "viton_chavret_labels_promoted": 0,
        "scientific_readiness": "HOLD_ENTHALPY_PROVENANCE",
        "scope": "Integrity, exact mappings, source-access claims, row-level temperature-window classification, freeze invariants, and split checks; not independent experimental replication.",
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

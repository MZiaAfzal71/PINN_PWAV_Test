#!/usr/bin/env python3
"""Rebuild the v0.5 source-identity and temperature-window audit.

The script derives all row-level decisions from the immutable v0.4 parent and
the versioned source-access inputs. It does not fetch documents, fit a model,
or turn metadata/secondary compilations into experimental labels.
"""
from collections import Counter
from decimal import Decimal as D
from pathlib import Path
import csv
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parent
PARENT = ROOT / "previous_v0_4"
BASE = PARENT / "previous_v0_3" / "baseline_v0_1"
TARGET_CODE = "1996VIT/CHA"


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def save_csv(path, rows, fields=None):
    rows = list(rows)
    if fields is None:
        fields = list(dict.fromkeys(key for row in rows for key in row))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_parent(config):
    manifest_path = PARENT / "MANIFEST.json"
    assert sha256(manifest_path) == config["parent_manifest_sha256"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["release_id"] == config["parent_release_id"]
    for relative, metadata in manifest["files"].items():
        assert sha256(PARENT / relative) == metadata["sha256"], relative
    return manifest


def copy_parent_outputs():
    for name in (
        "enthalpy_primary_labels.csv",
        "training_enthalpy_molecules.csv",
        "enthalpy_nist_ancillary_hold.csv",
        "enthalpy_nist_gamma_constraints.csv",
        "enthalpy_nist_sensitivity_labels.csv",
    ):
        shutil.copyfile(PARENT / "frozen" / name, ROOT / "frozen" / name)
    for name in (
        "nist_ancillary_reconstruction.csv",
        "nist_gamma_constraint_checks.csv",
        "nist_pressure_lineage_overlap.csv",
        "archival_source_overlap.csv",
    ):
        shutil.copyfile(PARENT / "evidence" / name, ROOT / "evidence" / name)
    for name in (
        "archival_document_register.json",
        "modeling_contract.json",
        "sensitivity_policy.json",
    ):
        shutil.copyfile(PARENT / "evidence" / name, ROOT / "evidence" / name)
    shutil.copyfile(PARENT / "review" / "nist_ancillary_inputs.csv", ROOT / "review" / "nist_ancillary_inputs.csv")


def temperature_status(value, lower, upper):
    value = D(value)
    if value < lower:
        return "outside_reported_measurement_window_below"
    if value > upper:
        return "outside_reported_measurement_window_above"
    return "within_reported_measurement_window"


def main():
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    parent_manifest = verify_parent(config)
    copy_parent_outputs()

    lower = D(config["viton_chavret_reported_measurement_T_min_K"])
    upper = D(config["viton_chavret_reported_measurement_T_max_K"])
    parent_candidates = read_csv(PARENT / "frozen" / "enthalpy_candidates_reviewed.csv")
    target = [row for row in parent_candidates if TARGET_CODE in json.loads(row["reference_codes_json"])]
    assert len(target) == config["viton_chavret_candidate_rows"]
    assert len({row["molecule_id"] for row in target}) == 5

    revised = []
    decisions = []
    for old in parent_candidates:
        row = old.copy()
        is_target = TARGET_CODE in json.loads(old["reference_codes_json"])
        if is_target:
            status = temperature_status(old["T_K"], lower, upper)
            in_window = status == "within_reported_measurement_window"
            role = (
                "plausibly_experimental_by_official_abstract_and_compendium_method_code_but_primary_table_unverified"
                if in_window else
                "outside_officially_reported_experimental_window_role_unresolved"
            )
            blocker = (
                "Exact primary numeric table, row identity, uncertainty/precision, and correction lineage not verified."
                if in_window else
                "Candidate temperature lies outside the official abstract's 313-344 K measurement interval; full source is required to distinguish measurement, literature value, interpolation, correlation, or extrapolation."
            )
            row.update(
                review_wave="source_identity_temperature_window_v0_5",
                review_date=config["review_date"],
                decision="hold_primary_table_and_method_unverified",
                decision_reasons=blocker,
                independent_of_pressure_verified="False",
                training_allowed="False",
                full_primary_methods_verified="False",
                primary_numeric_table_verified="False",
                primary_identity_verified="True",
                review_reference_code=TARGET_CODE,
                source_review_status="bibliographic_identity_resolved_primary_full_text_unavailable",
                reference_code=TARGET_CODE,
                reviewed_by=config["human_review_status"],
                v0_5_source_identity_status="bibliographic_code_mapping_resolved",
                v0_5_temperature_window_status=status,
                v0_5_primary_table_verified="False",
                v0_5_training_allowed="False",
                v0_5_review_note=role,
            )
            decisions.append({
                "record_id": old["record_id"],
                "molecule_id": old["molecule_id"],
                "inchi": old["inchi"],
                "name": old["name"],
                "split": old["split"],
                "component_id": old["component_id"],
                "reference_code": TARGET_CODE,
                "H_kJ_mol": old["H_kJ_mol"],
                "T_K": old["T_K"],
                "method_code_from_compendium": old["method"],
                "reported_measurement_T_min_K": str(lower),
                "reported_measurement_T_max_K": str(upper),
                "temperature_window_status": status,
                "inside_reported_measurement_window": str(in_window),
                "source_role_assessment": role,
                "bibliographic_identity_resolved": "True",
                "primary_full_text_obtained": "False",
                "exact_primary_numeric_table_verified": "False",
                "full_primary_methods_verified": "False",
                "pressure_correction_lineage_verified": "False",
                "uncertainty_or_precision_verified": "False",
                "training_allowed": "False",
                "decision": "hold_primary_table_and_method_unverified",
                "approval_blocker": blocker,
            })
        else:
            row.update(
                v0_5_source_identity_status="not_applicable",
                v0_5_temperature_window_status="not_applicable",
                v0_5_primary_table_verified="False",
                v0_5_training_allowed=row.get("training_allowed", "False"),
                v0_5_review_note="Inherited without a scientific-decision change from v0.4.",
            )
        revised.append(row)

    save_csv(ROOT / "frozen" / "enthalpy_candidates_reviewed.csv", revised)
    save_csv(ROOT / "review" / "viton_chavret_candidate_decisions.csv", decisions)
    save_csv(ROOT / "evidence" / "source_temperature_window_audit.csv", decisions)

    source_inputs = read_csv(ROOT / "review" / "source_access_inputs.csv")
    save_csv(ROOT / "evidence" / "source_access_audit.csv", source_inputs)

    identities = [
        {
            "assertion_id": "code_mapping",
            "reference_code": TARGET_CODE,
            "assertion": config["viton_chavret_source_mapping_citation"],
            "status": "verified_secondary_bibliography",
            "source_url": config["viton_chavret_source_mapping_url"],
            "source_locator": "Acree and Chickos 2016, reference list page 540, lines/entry 1996VIT/CHA",
            "strict_label_implication": "Resolves the shorthand citation only; does not verify any numeric row.",
        },
        {
            "assertion_id": "official_later_chapter",
            "reference_code": TARGET_CODE,
            "assertion": "Viton, Chavret, and Jose (1998), Enthalpy of Vaporization of N-Alkanes (from Nonane to Pentadecane). Experimental Results - Correlation, pp. 21-32.",
            "status": "verified_publisher_metadata",
            "source_url": "https://doi.org/" + config["viton_chavret_springer_chapter_doi"],
            "source_locator": "Springer chapter landing page",
            "strict_label_implication": "Confirms a later related publication, title, authors, pages, and DOI; not proof that it is textually identical to the 1996 ELDATA item.",
        },
        {
            "assertion_id": "experimental_window",
            "reference_code": TARGET_CODE,
            "assertion": "The official chapter abstract reports calorimetric measurements for n-alkanes C9-C15 over 313-344 K and comparison with literature and predicted values.",
            "status": "verified_official_abstract",
            "source_url": "https://doi.org/" + config["viton_chavret_springer_chapter_doi"],
            "source_locator": "Springer abstract",
            "strict_label_implication": "Supports temperature-window triage but cannot identify which compiled rows are measurements or supply missing uncertainty/correction details.",
        },
        {
            "assertion_id": "document_equivalence",
            "reference_code": TARGET_CODE,
            "assertion": "The 1996 ELDATA item and 1998 Springer chapter are the same version and contain identical numeric tables.",
            "status": "unverified",
            "source_url": "",
            "source_locator": "",
            "strict_label_implication": "No equivalence assumption is used for label approval.",
        },
    ]
    save_csv(ROOT / "evidence" / "source_identity_resolution.csv", identities)

    queue = read_csv(PARENT / "review" / "remaining_verification_queue.csv")
    for item in queue:
        if item["reference_code"] == "1977MAN/SEL":
            item["row_level_review_status"] = "publisher_metadata_verified_full_primary_text_not_obtained_v0_5"
            item["caveat"] = "Highest-yield open item: 13 rows and up to 12 additional molecules. No approval from abstract/search snippets; full methods, tables, footnotes, and correction lineage are required."
        elif item["reference_code"] == "1926MAT":
            item["row_level_review_status"] = "publisher_identity_verified_full_primary_text_not_obtained_v0_5"
            item["caveat"] = "ACS article identity and DOI are resolved, but the full primary methods and numeric table were not obtained; all 12 rows remain held."
        elif item["reference_code"] == TARGET_CODE:
            item["row_level_review_status"] = "identity_resolved_temperature_window_triaged_primary_full_text_not_obtained_v0_5"
            item["primary_url"] = config["viton_chavret_source_mapping_url"]
            item["caveat"] = "All 19 rows remain held. Four 299 K rows and one 359 K row lie outside the official 313-344 K measurement interval; 14 in-window rows still require the exact primary table, method details, uncertainty, and correction lineage."
    save_csv(ROOT / "review" / "remaining_verification_queue.csv", queue)

    resolved = read_csv(PARENT / "review" / "resolved_source_decisions.csv")
    resolved.append({
        "reference_code": TARGET_CODE,
        "candidate_rows": "19",
        "candidate_molecules": "5",
        "strict_primary_labels_added": "0",
        "sensitivity_labels_frozen": "0",
        "gamma_constraints_frozen": "0",
        "final_status": "bibliographic_identity_and_temperature_window_triage_complete_all_rows_held",
        "decision_basis": "Primary 1996 ELDATA full text unavailable; 1998 official abstract reports a 313-344 K experimental window; exact equivalence and row roles remain unverified.",
    })
    save_csv(ROOT / "review" / "resolved_source_decisions.csv", resolved)

    strict = read_csv(ROOT / "frozen" / "enthalpy_primary_labels.csv")
    molecules = {row["molecule_id"] for row in strict if row["split"] == "train"}
    counts = Counter(row["temperature_window_status"] for row in decisions)
    parent_summary = json.loads((PARENT / "frozen" / "summary.json").read_text(encoding="utf-8"))
    summary = parent_summary | {
        "version": config["version"],
        "review_date": config["review_date"],
        "status": "HOLD_ENTHALPY_PROVENANCE",
        "strict_pool_changed_from_v0_4": False,
        "strict_primary_labels": len(strict),
        "strict_primary_training_molecules": len(molecules),
        "additional_training_molecules_needed": max(0, config["minimum_independent_training_enthalpy_molecules"] - len(molecules)),
        "viton_chavret_candidate_rows_audited": len(decisions),
        "viton_chavret_candidate_molecules": len({row["molecule_id"] for row in decisions}),
        "viton_chavret_rows_inside_reported_measurement_window": counts["within_reported_measurement_window"],
        "viton_chavret_rows_below_reported_measurement_window": counts["outside_reported_measurement_window_below"],
        "viton_chavret_rows_above_reported_measurement_window": counts["outside_reported_measurement_window_above"],
        "viton_chavret_strict_labels_added": 0,
        "viton_chavret_primary_full_text_obtained": False,
        "viton_chavret_eldata_springer_equivalence_verified": False,
        "note": "The strict direct-H pool remains 42 labels on 41 molecules. The 1996VIT/CHA shorthand is resolved and 19 rows are temperature-window-triaged, but no primary numeric table was obtained and no row is promoted.",
    }
    save_json(ROOT / "frozen" / "summary.json", summary)

    save_json(ROOT / "evidence" / "access_followup.json", {
        "review_date": config["review_date"],
        "sources": source_inputs,
        "conclusion": "No full primary document was obtained for the three closed-source targets. Metadata and abstracts were used only for access, identity, and temperature-window triage; zero labels were promoted.",
    })
    save_json(ROOT / "evidence" / "parent_release_receipt.json", {
        "status": "PASS",
        "release_id": parent_manifest["release_id"],
        "manifest_sha256": config["parent_manifest_sha256"],
        "manifest_files_verified": len(parent_manifest["files"]),
        "zip_sha256": config["parent_zip_sha256"],
        "strict_label_csv_sha256": sha256(PARENT / "frozen" / "enthalpy_primary_labels.csv"),
        "strict_molecule_csv_sha256": sha256(PARENT / "frozen" / "training_enthalpy_molecules.csv"),
    })


if __name__ == "__main__":
    main()

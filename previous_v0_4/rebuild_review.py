#!/usr/bin/env python3
"""Rebuild the v0.4 NIST ancillary audit from frozen v0.3 data.

The manually transcribed archival inputs live in
review/nist_ancillary_inputs.csv.  This script performs arithmetic, assigns
the predeclared tiers, and copies the unchanged strict label pool.  It does
not fit a model or automate scientific document review.
"""
from collections import Counter
from decimal import Decimal as D, ROUND_DOWN, ROUND_HALF_UP, getcontext
from pathlib import Path
import csv
import hashlib
import json
import shutil

getcontext().prec = 50
ROOT = Path(__file__).resolve().parent
PARENT = ROOT / "previous_v0_3"
BASE = PARENT / "baseline_v0_1"


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


def fixed(value, places=15):
    text = format(value, f".{places}f").rstrip("0").rstrip(".")
    return text if text not in ("", "-0") else "0"


def verify_parent(config):
    manifest_path = PARENT / "MANIFEST.json"
    assert sha256(manifest_path) == config["parent_manifest_sha256"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for relative, metadata in manifest["files"].items():
        assert sha256(PARENT / relative) == metadata["sha256"], relative
    return manifest


def archival_documents():
    return [
        {
            "source_key": "NIST_1947_OSBORNE_GINNINGS",
            "title": "Measurements of heat of vaporization and heat capacity of a number of hydrocarbons",
            "year": 1947,
            "doi": "10.6028/jres.039.031",
            "landing_url": "https://doi.org/10.6028/jres.039.031",
            "download_url": "https://nistdigitalarchives.contentdm.oclc.org/digital/api/collection/p16009coll6/id/118316/download",
            "sha256": "0dcceb5865b44de7cb6fb02e5d0f23d1257e63106d1f135400095c1340abd288",
            "role": "Primary calorimetry and printed gamma, beta, and L values",
            "locators": "Table 1, printed pp.465-469; method and beta definition, printed pp.460 and 469-470",
            "included_in_release": False,
        },
        {
            "source_key": "NBS_CIRCULAR_461",
            "title": "Selected Values of Properties of Hydrocarbons, NBS Circular 461",
            "year": 1947,
            "doi": "10.6028/NBS.CIRC.461",
            "landing_url": "https://www.nist.gov/publications/circular-bureau-standards-no-461selected-values-properties-hydrocarbons",
            "download_url": "https://nvlpubs.nist.gov/nistpubs/Legacy/circ/nbscircular461.pdf",
            "sha256": "720ea51fea0d1aa26fb887090221eec030185b88308ac1d3633d08c9e6d75cf1",
            "role": "Bound API Research Project 44 molecular-volume and Antoine tables",
            "locators": "Printed pp.86-93 and 122-130; absolute-temperature convention on printed p.3",
            "included_in_release": False,
        },
        {
            "source_key": "WILLINGHAM_1945",
            "title": "Vapor pressures and boiling points of some paraffin, alkylcyclopentane, alkylcyclohexane, and alkylbenzene hydrocarbons",
            "year": 1945,
            "doi": "",
            "landing_url": "https://nvlpubs.nist.gov/nistpubs/jres/35/jresv35n3p219_A1b.pdf",
            "download_url": "https://nvlpubs.nist.gov/nistpubs/jres/35/jresv35n3p219_A1b.pdf",
            "sha256": "d9687895ce24d7bd4439896a950259c771d432582e54dd2486a37a9152e848ef",
            "role": "Accessible primary Antoine correlations for n-nonane and n-decane; surrogate for unavailable exact cited slope entries",
            "locators": "Table 3, printed p.239, PDF p.21",
            "included_in_release": False,
        },
        {
            "source_key": "ICT_VOL3",
            "title": "International Critical Tables, volume III",
            "year": 1928,
            "doi": "",
            "landing_url": "https://archive.org/details/int-cr-tab-v-3",
            "download_url": "https://archive.org/download/int-cr-tab-v-3/Int_cr_tab_v3.pdf",
            "sha256": "7e591bbbf5ef10306ba01f00e8a4dd2628daf829993fb3f7382115fd9a94473a",
            "role": "Cited density source; n-decane density equation used to obtain the 25 C specific volume",
            "locators": "Density equation and n-decane row, printed pp.27 and 30; PDF pp.40 and 43",
            "included_in_release": False,
        },
    ]


def main():
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    parent_manifest = verify_parent(config)

    strict_source = PARENT / "frozen" / "enthalpy_primary_labels.csv"
    molecules_source = PARENT / "frozen" / "training_enthalpy_molecules.csv"
    shutil.copyfile(strict_source, ROOT / "frozen" / "enthalpy_primary_labels.csv")
    shutil.copyfile(molecules_source, ROOT / "frozen" / "training_enthalpy_molecules.csv")

    strict_labels = read_csv(strict_source)
    parent_candidates = read_csv(PARENT / "frozen" / "enthalpy_candidates_reviewed.csv")
    parent_hold = {row["record_id"]: row for row in read_csv(PARENT / "frozen" / "enthalpy_nist_ancillary_hold.csv")}
    inputs = read_csv(ROOT / "review" / "nist_ancillary_inputs.csv")
    assert len(inputs) == len(parent_hold) == 14
    assert {row["record_id"] for row in inputs} == set(parent_hold)

    T = D(config["nist_historical_absolute_temperature_K"])
    nominal_T = config["nist_nominal_modern_temperature_K"]
    t_C = D("25")
    conversion = D(config["nist_joule_conversion_factor"])
    pa_per_mmhg = D(config["pressure_conversion_Pa_per_mmHg"])
    mmhg_cm3_to_joule = pa_per_mmhg * D("1e-6")
    ln10 = D(10).ln()

    reconstructions = []
    sensitivity = []
    constraints = []
    gamma_checks = []
    recon_by_id = {}
    for item in inputs:
        record = parent_hold[item["record_id"]]
        mass = D(record["molar_mass_g_mol"])
        density = None
        if item["molar_volume_25C_mL_mol"]:
            volume = D(item["molar_volume_25C_mL_mol"])
            volume_derivation = "printed_molar_volume"
        else:
            dt = t_C - D(item["density_t0_C"])
            density = (
                D(item["density_d0_g_mL"])
                + D("1e-3") * D(item["density_alpha"]) * dt
                + D("1e-6") * D(item["density_beta"]) * dt**2
                + D("1e-9") * D(item["density_gamma"]) * dt**3
            )
            volume = mass / density
            volume_derivation = "molar_mass_divided_by_archival_density_equation"

        A, B, C = D(item["antoine_A"]), D(item["antoine_B"]), D(item["antoine_C_C"])
        log10_p = A - B / (C + t_C)
        p_mmhg = (log10_p * ln10).exp()
        dp_dT_mmhg_K = ln10 * p_mmhg * B / (C + t_C) ** 2
        specific_volume_cm3_g = volume / mass
        beta = T * specific_volume_cm3_g * dp_dT_mmhg_K * mmhg_cm3_to_joule
        published_beta = D(record["beta_intJ_g"])
        published_gamma = D(record["mean_gamma_intJ_g"])
        published_L = D(record["primary_H"])
        nearest = beta.quantize(D("0.01"), rounding=ROUND_HALF_UP)
        truncated = beta.quantize(D("0.01"), rounding=ROUND_DOWN)
        difference = beta - published_beta
        nearest_match = nearest == published_beta
        within_half_cent = abs(difference) <= D("0.005")
        direct_slope_lineage = item["vapor_pressure_source_directly_in_cited_beta_pair"] == "True"
        lineage_complete = direct_slope_lineage and item["volume_source_key"] in {"NBS_CIRCULAR_461", "ICT_VOL3"}
        if lineage_complete and nearest_match:
            status = "reproduced_at_printed_precision"
        elif lineage_complete:
            status = "not_reproduced_at_printed_precision"
        elif nearest_match:
            status = "numerically_reproduced_with_surrogate_slope_source"
        else:
            status = "not_reproduced_and_direct_slope_lineage_incomplete"

        reconstruction = {
            "record_id": record["record_id"],
            "molecule_id": record["molecule_id"],
            "primary_name": item["primary_name"],
            "split": record["split"],
            "T_C": "25",
            "T_K_historical_absolute": fixed(T, 3),
            "T_K_nominal_modern_metadata": nominal_T,
            "molar_mass_g_mol": record["molar_mass_g_mol"],
            "molar_volume_25C_mL_mol": fixed(volume, 12),
            "density_25C_g_mL": fixed(density, 12) if density is not None else "",
            "specific_volume_25C_cm3_g": fixed(specific_volume_cm3_g, 15),
            "volume_derivation": volume_derivation,
            "volume_source_key": item["volume_source_key"],
            "volume_source_locator": item["volume_source_locator"],
            "vapor_pressure_source_key": item["vapor_pressure_source_key"],
            "vapor_pressure_source_locator": item["vapor_pressure_source_locator"],
            "vapor_pressure_source_directly_in_cited_beta_pair": str(direct_slope_lineage),
            "archival_lineage_complete": str(lineage_complete),
            "antoine_equation": "log10(p_mmHg)=A-B/(C+t_C)",
            "antoine_A": item["antoine_A"],
            "antoine_B": item["antoine_B"],
            "antoine_C_C": item["antoine_C_C"],
            "p_sat_25C_mmHg": fixed(p_mmhg, 12),
            "dp_sat_dT_25C_mmHg_K": fixed(dp_dT_mmhg_K, 12),
            "beta_equation": "beta=T*v_liquid*dp_sat/dT",
            "reconstructed_beta_int_J_g": fixed(beta, 15),
            "published_beta_int_J_g": fixed(published_beta, 2),
            "signed_difference_reconstructed_minus_published_int_J_g": fixed(difference, 15),
            "absolute_difference_int_J_g": fixed(abs(difference), 15),
            "nearest_0.01_half_up_int_J_g": fixed(nearest, 2),
            "nearest_0.01_matches_published": str(nearest_match),
            "within_unrounded_half_cent": str(within_half_cent),
            "truncated_0.01_int_J_g": fixed(truncated, 2),
            "truncation_matches_published": str(truncated == published_beta),
            "reconstruction_status": status,
            "lineage_note": item["lineage_note"],
        }
        reconstructions.append(reconstruction)
        recon_by_id[record["record_id"]] = reconstruction

        molar_scale = conversion * mass / D("1000")
        gamma_kJ_mol = published_gamma * molar_scale
        beta_kJ_mol = published_beta * molar_scale
        L_kJ_mol = published_L * molar_scale
        assert published_gamma - published_beta == published_L
        assert L_kJ_mol == D(record["H_kJ_mol"])

        sensitivity.append({
            "record_id": record["record_id"],
            "molecule_id": record["molecule_id"],
            "inchi": record["inchi"],
            "name": record["name"],
            "primary_name": item["primary_name"],
            "split": record["split"],
            "component_id": record["component_id"],
            "T_K": nominal_T,
            "T_K_historical_absolute": fixed(T, 3),
            "published_gamma_int_J_g": fixed(published_gamma, 2),
            "published_beta_int_J_g": fixed(published_beta, 2),
            "published_L_int_J_g": fixed(published_L, 2),
            "published_L_abs_kJ_mol": fixed(L_kJ_mol, 15),
            "source_doi": record["source_doi"],
            "source_locator": record["source_locator"],
            "beta_reconstruction_status": status,
            "archival_lineage_complete": str(lineage_complete),
            "label_tier": "sensitivity_only_published_L",
            "use_for_primary_training": "False",
            "use_for_validation": "False",
            "use_for_test": "False",
            "use_for_sensitivity_analysis": "True",
            "do_not_mix_with_primary_labels": "True",
            "exclusion_basis": "Published L subtracts a pressure-derived beta; the 14-row audit has incomplete exact lineage for two slopes and seven printed-precision mismatches.",
        })

        equation = "gamma_kJ_mol = H_vap_model_kJ_mol + T_K*V_m3_mol*dp_sat_dT_Pa_K/1000"
        constraints.append({
            "record_id": record["record_id"],
            "molecule_id": record["molecule_id"],
            "inchi": record["inchi"],
            "name": record["name"],
            "primary_name": item["primary_name"],
            "split": record["split"],
            "component_id": record["component_id"],
            "T_K_model_coordinate": nominal_T,
            "T_K_historical_absolute_for_source_arithmetic": fixed(T, 3),
            "gamma_int_J_g": fixed(published_gamma, 2),
            "gamma_abs_kJ_mol": fixed(gamma_kJ_mol, 15),
            "molar_mass_g_mol": record["molar_mass_g_mol"],
            "energy_conversion_abs_J_per_int_J": fixed(conversion, 6),
            "molar_volume_25C_mL_mol": fixed(volume, 12),
            "molar_volume_25C_m3_mol": fixed(volume * D("1e-6"), 18),
            "volume_source_key": item["volume_source_key"],
            "volume_source_locator": item["volume_source_locator"],
            "constraint_equation": equation,
            "pressure_derivative_definition": "dp_sat/dT = p_sat*d(ln p_sat)/dT",
            "constraint_ready": "True",
            "direct_enthalpy_label": "False",
            "primary_training_label": "False",
            "evaluation_label": "False",
            "held_out_pressure_targets_permitted": "False",
            "training_visible_pressure_or_model_derivative_only": "True",
            "uncertainty_status": "No per-row gamma uncertainty reported; do not invent sigma or inverse-variance weights.",
            "source_doi": record["source_doi"],
            "source_locator": record["source_locator"],
            "tier_note": "Direct electrical-energy-per-withdrawn-mass observable; use only as a coupled physics residual after the strict project gate is satisfied or explicitly revised.",
        })
        gamma_checks.append({
            "record_id": record["record_id"],
            "gamma_minus_published_beta_equals_published_L": "True",
            "gamma_abs_kJ_mol": fixed(gamma_kJ_mol, 15),
            "published_beta_abs_kJ_mol": fixed(beta_kJ_mol, 15),
            "published_L_abs_kJ_mol": fixed(L_kJ_mol, 15),
            "converted_gamma_minus_beta_equals_converted_L": str(gamma_kJ_mol - beta_kJ_mol == L_kJ_mol),
            "volume_input_traced": "True",
            "constraint_ready": "True",
            "direct_H_training_allowed": "False",
        })

    save_csv(ROOT / "evidence" / "nist_ancillary_reconstruction.csv", reconstructions)
    save_csv(ROOT / "frozen" / "enthalpy_nist_sensitivity_labels.csv", sensitivity)
    save_csv(ROOT / "frozen" / "enthalpy_nist_gamma_constraints.csv", constraints)
    save_csv(ROOT / "evidence" / "nist_gamma_constraint_checks.csv", gamma_checks)

    revised = []
    nist_ids = set(recon_by_id)
    for old in parent_candidates:
        row = old.copy()
        if old["record_id"] in nist_ids:
            rec = recon_by_id[old["record_id"]]
            row.update(
                review_wave="archival_ancillary_verification_v0_4",
                review_date=config["review_date"],
                source_review_status="primary_table_verified_ancillary_audit_complete_sensitivity_only",
                decision="hold_published_enthalpy_sensitivity_only_beta_not_reproduced",
                decision_reasons="Direct gamma retained as a coupled physics constraint; published L excluded from the strict label pool because it subtracts pressure-derived beta and the archival audit yields seven printed-precision mismatches plus two surrogate slope lineages.",
                independent_of_pressure_verified=False,
                training_allowed=False,
                benchmark_pressure_used_for_label="False; archival correction sources have no DOI overlap with the frozen pressure records",
                v0_4_tier="sensitivity_L_plus_gamma_physics_constraint",
                v0_4_gamma_constraint_ready=True,
                v0_4_beta_reconstruction_status=rec["reconstruction_status"],
                v0_4_review_note="Published L is sensitivity-only; measured gamma is not a direct H label.",
            )
        else:
            row.update(
                v0_4_tier="strict_primary_label" if old.get("training_allowed") == "True" else "inherited_hold_or_quarantine",
                v0_4_gamma_constraint_ready=False,
                v0_4_beta_reconstruction_status="not_applicable",
                v0_4_review_note="Inherited unchanged from v0.3 scientific decision.",
            )
        revised.append(row)
    save_csv(ROOT / "frozen" / "enthalpy_candidates_reviewed.csv", revised)
    save_csv(ROOT / "frozen" / "enthalpy_nist_ancillary_hold.csv", [row for row in revised if row["record_id"] in nist_ids])

    pressure = read_csv(BASE / "frozen" / "pressure_observations.csv")
    pressure_dois = {row["source_doi"].lower() for row in pressure if row["source_doi"]}
    documents = archival_documents()
    archival_dois = {doc["doi"].lower() for doc in documents if doc["doi"]}
    overlap_rows = []
    for constraint in constraints:
        rows = [row for row in pressure if row["molecule_id"] == constraint["molecule_id"]]
        dois = sorted({row["source_doi"] for row in rows if row["source_doi"]})
        temperatures = [D(row["T_K"]) for row in rows]
        overlap_rows.append({
            "record_id": constraint["record_id"],
            "molecule_id": constraint["molecule_id"],
            "name": constraint["name"],
            "split": constraint["split"],
            "frozen_pressure_rows": len(rows),
            "frozen_pressure_unique_dois": len(dois),
            "frozen_pressure_T_min_K": fixed(min(temperatures), 6) if temperatures else "",
            "frozen_pressure_T_max_K": fixed(max(temperatures), 6) if temperatures else "",
            "frozen_pressure_dois_json": json.dumps(dois, separators=(",", ":")),
            "overlaps_nist_measurement_doi": str("10.6028/jres.039.031" in {d.lower() for d in dois}),
            "overlaps_any_archival_document_doi": str(bool({d.lower() for d in dois} & archival_dois)),
            "partition_bridge_detected": "False",
            "conclusion": "No frozen pressure DOI overlap and the molecule remains in train; this does not make published L pressure-independent.",
        })
    save_csv(ROOT / "evidence" / "nist_pressure_lineage_overlap.csv", overlap_rows)
    save_json(ROOT / "evidence" / "archival_document_register.json", documents)
    save_csv(
        ROOT / "evidence" / "archival_source_overlap.csv",
        [
            {
                "source_key": doc["source_key"],
                "doi": doc["doi"],
                "overlaps_any_frozen_pressure_doi": str(bool(doc["doi"] and doc["doi"].lower() in pressure_dois)),
                "role": doc["role"],
                "review_limit": "DOI non-overlap is a leakage check, not proof of statistical or metrological independence.",
            }
            for doc in documents
        ],
    )

    parent_queue = read_csv(PARENT / "review" / "remaining_verification_queue.csv")
    remaining_queue = [row for row in parent_queue if row["reference_code"] != "1947OSB/GIN"]
    for row in remaining_queue:
        if row["reference_code"] == "1977MAN/SEL":
            row["row_level_review_status"] = "closed_full_text_not_obtained_after_metadata_and_access_followup"
            row["caveat"] = "Highest remaining source opportunity. Full methods, tables, footnotes and correction lineage are still required before any approval."
    save_csv(ROOT / "review" / "remaining_verification_queue.csv", remaining_queue)
    save_csv(
        ROOT / "review" / "resolved_source_decisions.csv",
        [{
            "reference_code": "1947OSB/GIN",
            "candidate_rows": 14,
            "candidate_molecules": 14,
            "strict_primary_labels_added": 0,
            "sensitivity_labels_frozen": 14,
            "gamma_constraints_frozen": 14,
            "final_status": "archival_audit_complete_sensitivity_L_and_gamma_constraint_tier",
            "decision_basis": "Pressure-derived beta; two surrogate pressure-slope lineages; seven of fourteen beta values fail printed-precision reconstruction.",
        }],
    )

    save_json(ROOT / "evidence" / "sensitivity_policy.json", {
        "primary_analysis": "Use only frozen/enthalpy_primary_labels.csv after the project gate is met.",
        "nist_published_L": "Exclude from primary training, validation and test; use all 14 together only in a separately reported sensitivity analysis.",
        "nist_gamma": "Use only as the specified coupled physics residual; never concatenate with direct H labels.",
        "selection_timing": "The tier decision was frozen before model fitting and without target-performance information.",
        "models_fitted": False,
    })
    save_json(ROOT / "evidence" / "modeling_contract.json", {
        "constraint_name": "raw_calorimetric_gamma_balance",
        "equation": "gamma_kJ_mol = H_vap_model_kJ_mol + T_K*V_m3_mol*dp_sat_dT_Pa_K/1000",
        "log_pressure_form": "dp_sat/dT = p_sat*d(ln(p_sat/1Pa))/dT",
        "rows": 14,
        "partition": "train only",
        "direct_H_label": False,
        "permitted_pressure_information": "Training-visible pressure observations and model/autodiff derivatives at the constraint state.",
        "prohibited_pressure_information": "Frozen validation/test targets, test losses, and target-informed hyperparameter selection.",
        "loss_weighting": "No per-row gamma sigma is reported. Predeclare a common robust weight or tune only within training/validation without test targets.",
        "primary_gate": "The inherited 100-independent-training-molecule direct-H gate remains unchanged and is not satisfied by gamma constraints.",
    })
    save_json(ROOT / "evidence" / "access_followup.json", {
        "doi": "10.1016/0021-9614(77)90202-6",
        "title": "Enthalpies of vaporization of some 1-substituted n-alkanes",
        "checked_on": config["review_date"],
        "status": "closed_full_text_not_obtained",
        "publisher_landing_page": "https://www.sciencedirect.com/science/article/pii/0021961477902026",
        "metadata_sources_checked": ["ScienceDirect", "Crossref", "OpenAlex", "Semantic Scholar", "NIST WebBook", "general web search"],
        "open_full_text_found": False,
        "decision": "No candidate row approved from metadata or secondary compilations. Full methods, tables, footnotes and corrections remain required.",
    })
    save_json(ROOT / "evidence" / "parent_release_receipt.json", {
        "release_id": config["parent_release_id"],
        "manifest_sha256": config["parent_manifest_sha256"],
        "zip_sha256": config["parent_zip_sha256"],
        "manifest_files_verified": len(parent_manifest["files"]),
        "strict_label_csv_sha256": sha256(strict_source),
        "strict_molecule_csv_sha256": sha256(molecules_source),
        "status": "PASS",
    })

    assignments = read_csv(BASE / "frozen" / "split_assignments.csv")
    strict_molecules = {row["molecule_id"] for row in strict_labels}
    matches = sum(row["nearest_0.01_matches_published"] == "True" for row in reconstructions)
    direct = sum(row["archival_lineage_complete"] == "True" for row in reconstructions)
    summary = {
        "version": "0.4.0",
        "review_date": config["review_date"],
        "status": "HOLD_ENTHALPY_PROVENANCE",
        "model_fits_performed": False,
        "test_targets_used_for_label_decisions": False,
        "strict_primary_labels": len(strict_labels),
        "strict_primary_training_molecules": len(strict_molecules),
        "required_primary_training_molecules": config["minimum_independent_training_enthalpy_molecules"],
        "additional_training_molecules_needed": max(0, config["minimum_independent_training_enthalpy_molecules"] - len(strict_molecules)),
        "strict_pool_changed_from_v0_3": False,
        "nist_rows_audited": len(reconstructions),
        "nist_beta_nearest_cent_matches": matches,
        "nist_beta_nearest_cent_mismatches": len(reconstructions) - matches,
        "nist_complete_cited_ancillary_lineages": direct,
        "nist_surrogate_slope_lineages": len(reconstructions) - direct,
        "nist_published_L_sensitivity_labels": len(sensitivity),
        "nist_gamma_physics_constraints": len(constraints),
        "nist_gamma_constraints_count_toward_direct_H_gate": False,
        "nist_molecules_all_in_train_split": all(row["split"] == "train" for row in constraints),
        "nist_archival_document_doi_overlap_with_frozen_pressure": any(row["overlaps_any_archival_document_doi"] == "True" for row in overlap_rows),
        "candidate_rows_preserved": len(revised),
        "remaining_quarantined_or_held_candidates": len(revised) - len(strict_labels),
        "split_counts": dict(sorted(Counter(row["split"] for row in assignments).items())),
        "primary_test_episodes": sum(
            row["split"] == "test" and row["pressure_ceiling_Pa"] == "20000"
            for row in read_csv(BASE / "frozen" / "episodes.csv")
        ),
        "primary_test_anchor_rows": len(read_csv(BASE / "frozen" / "test_anchors.csv")),
        "primary_test_target_rows": len(read_csv(BASE / "frozen" / "test_cold_targets.csv")),
        "next_high_value_source": "1977MAN/SEL",
        "next_high_value_source_status": "closed_full_text_not_obtained",
        "note": "The direct-H gate remains at 42 labels on 41 molecules. Published NIST L values are sensitivity-only; raw gamma values are a distinct coupled-physics tier and are not enthalpy labels.",
    }
    save_json(ROOT / "frozen" / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

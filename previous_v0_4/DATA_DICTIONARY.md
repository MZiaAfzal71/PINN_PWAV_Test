# Data dictionary

CSV files use UTF-8, comma delimiters, one header row, `.` as the decimal mark, and explicit `True`/`False` strings for Boolean fields. Energies labeled `int_J_g` are US international joules per gram as printed in the 1947 paper. Fields labeled `abs_kJ_mol` apply the recorded 1.000165 conversion and the explicit molar mass.

## `frozen/enthalpy_primary_labels.csv`

The strict direct-enthalpy export. It is byte-identical to v0.3 and contains 42 observations on 41 training molecules. These are the only current labels allowed in the primary direct-H loss. Its inherited columns are documented in `previous_v0_3/DATA_DICTIONARY.md`.

## `frozen/enthalpy_candidates_reviewed.csv`

All 751 frozen candidate rows and their current decision. Identity, molecule, component, and split fields are unchanged from v0.3.

| New field | Meaning |
|---|---|
| `v0_4_tier` | `strict_primary_label`, `sensitivity_L_plus_gamma_physics_constraint`, or inherited hold/quarantine. |
| `v0_4_gamma_constraint_ready` | Whether a separate raw-gamma constraint is complete. This never means the row is a direct H label. |
| `v0_4_beta_reconstruction_status` | Compound-level outcome of the archival beta audit. |
| `v0_4_review_note` | Short statement of the v0.4 action. |

For the 14 NIST rows, `training_allowed=False` and `independent_of_pressure_verified=False` remain mandatory.

## `frozen/enthalpy_nist_sensitivity_labels.csv`

The 14 published `L = gamma - beta` values, isolated from the primary pool.

| Field | Meaning |
|---|---|
| `published_gamma_int_J_g` | Mean measured energy per withdrawn mass. |
| `published_beta_int_J_g` | Source-applied pressure-slope correction. |
| `published_L_int_J_g` | Printed latent heat after subtraction. |
| `published_L_abs_kJ_mol` | Recorded molar conversion of printed L. |
| `beta_reconstruction_status` | Whether accessible inputs reproduce beta at 0.01 J/g and whether the exact source lineage is complete. |
| `archival_lineage_complete` | True only when the chosen slope and volume sources belong to the exact source pair cited for the correction. |
| `label_tier` | Always `sensitivity_only_published_L`. |
| `use_for_primary_training` | Always false. |
| `use_for_validation`, `use_for_test` | Always false. |
| `use_for_sensitivity_analysis` | Always true; use all 14 as one prespecified tier. |
| `do_not_mix_with_primary_labels` | Always true. |

## `frozen/enthalpy_nist_gamma_constraints.csv`

Fourteen raw calorimetric constraints for a future coupled pressure-enthalpy PINN.

| Field | Unit or meaning |
|---|---|
| `gamma_int_J_g` | Printed US international J/g. |
| `gamma_abs_kJ_mol` | Converted absolute kJ/mol. |
| `T_K_model_coordinate` | 298.15 K, retained for compatibility with the frozen model coordinates. |
| `T_K_historical_absolute_for_source_arithmetic` | 298.160 K, the archived absolute-temperature convention. |
| `molar_volume_25C_mL_mol` | Traced liquid molar volume used by the constraint. |
| `molar_volume_25C_m3_mol` | Same volume in SI. |
| `constraint_equation` | Molar raw-observable balance. |
| `pressure_derivative_definition` | Stable form for a log-pressure model. |
| `constraint_ready` | Required fields and volume provenance are present. |
| `direct_enthalpy_label`, `primary_training_label`, `evaluation_label` | Always false. |
| `held_out_pressure_targets_permitted` | Always false. |
| `training_visible_pressure_or_model_derivative_only` | Always true. |
| `uncertainty_status` | Prevents invented rowwise sigma or inverse-variance weighting. |

## `review/nist_ancillary_inputs.csv`

Versioned manual transcriptions used by `rebuild_review.py`.

| Field | Meaning |
|---|---|
| `molar_volume_25C_mL_mol` | Printed API molar volume; blank for n-decane because its volume is derived from density. |
| `volume_source_key`, `volume_source_locator` | Document key and exact table/page location. |
| `vapor_pressure_source_key`, `vapor_pressure_source_locator` | Document key and exact Antoine-table location. |
| `antoine_A`, `antoine_B`, `antoine_C_C` | Constants in `log10(p_mmHg)=A-B/(C+t_C)`. |
| `vapor_pressure_source_directly_in_cited_beta_pair` | False for the two accessible surrogate correlations. |
| `density_d0_g_mL`, `density_alpha`, `density_beta`, `density_gamma`, `density_t0_C` | ICT density-equation inputs for n-decane. |

## `evidence/nist_ancillary_reconstruction.csv`

The complete compound-level arithmetic receipt.

| Field | Meaning |
|---|---|
| `p_sat_25C_mmHg` | Pressure calculated from the archived Antoine equation. |
| `dp_sat_dT_25C_mmHg_K` | Analytic derivative at 25 °C. |
| `specific_volume_25C_cm3_g` | Liquid specific volume used in beta. |
| `reconstructed_beta_int_J_g` | `T v dp/dT`, in international-J/g-compatible source units. |
| `signed_difference_reconstructed_minus_published_int_J_g` | Unrounded signed discrepancy. |
| `nearest_0.01_half_up_int_J_g` | Primary printed-precision comparison. |
| `nearest_0.01_matches_published` | Frozen match decision. |
| `within_unrounded_half_cent` | Independent tolerance receipt. |
| `truncated_0.01_int_J_g`, `truncation_matches_published` | Diagnostic only; not the primary rule. |
| `reconstruction_status` | Combines numerical agreement and exact/surrogate lineage. |

## `evidence/nist_pressure_lineage_overlap.csv`

One row per NIST molecule. Counts and temperature ranges are computed from the deduplicated frozen pressure table. DOI overlap fields compare the archival documents with the frozen pressure sources. A false overlap flag is a leakage receipt, not proof of thermodynamic independence.

## JSON evidence

- `archival_document_register.json`: title, year, role, URLs, SHA256, and locators for each checked document. PDFs are not bundled.
- `modeling_contract.json`: machine-readable constraint equation and leakage rules.
- `sensitivity_policy.json`: primary, sensitivity, and gamma-tier use restrictions.
- `parent_release_receipt.json`: v0.3 hashes and verification result.
- `access_followup.json`: current full-text status for Månsson et al. (1977).
- `validation.json`: software verification result.
- `reproducibility.json`: byte-identical rebuild receipt.

## Historical files

`previous_v0_3/` is an immutable copy of the complete parent release. The pressure observations, split assignments, episodes, anchors, and cold targets used here are under `previous_v0_3/baseline_v0_1/frozen/`.

# Data dictionary

CSV files use UTF-8, comma delimiters, one header row, `.` as the decimal mark, and explicit `True`/`False` strings for Boolean fields. Candidate enthalpies are in kJ/mol and temperatures are in K unless stated otherwise.

## `frozen/enthalpy_primary_labels.csv`

The strict direct-enthalpy export. It is byte-identical to v0.4 and contains 42 observations on 41 training molecules. These are the only current labels permitted in the primary direct-H loss.

## `frozen/enthalpy_candidates_reviewed.csv`

All 751 candidate rows and their current decision. Identity, value, molecule, component, and split fields are unchanged from v0.4.

| v0.5 field | Meaning |
|---|---|
| `v0_5_source_identity_status` | Whether the v0.5 source-identity audit applies and its result. |
| `v0_5_temperature_window_status` | `within_reported_measurement_window`, `outside_reported_measurement_window_below`, `outside_reported_measurement_window_above`, or `not_applicable`. |
| `v0_5_primary_table_verified` | Whether the exact primary numeric table was checked; false for all 19 `1996VIT/CHA` rows. |
| `v0_5_training_allowed` | Current row-level training permission after this review. |
| `v0_5_review_note` | Concise source-role assessment or inheritance note. |

For the 19 `1996VIT/CHA` records, `training_allowed=False`, `independent_of_pressure_verified=False`, `primary_numeric_table_verified=False`, and `full_primary_methods_verified=False` are mandatory.

## `review/viton_chavret_candidate_decisions.csv`

One row per `1996VIT/CHA` candidate.

| Field | Meaning |
|---|---|
| `H_kJ_mol`, `T_K` | Unchanged compiled candidate value and temperature. |
| `method_code_from_compendium` | Method code copied from the source compendium; not independently reinterpreted as primary proof. |
| `reported_measurement_T_min_K`, `reported_measurement_T_max_K` | Inclusive 313–344 K range from the official related-chapter abstract. |
| `temperature_window_status` | Mechanical comparison of candidate `T_K` with that interval. |
| `inside_reported_measurement_window` | True only for 313 ≤ T ≤ 344 K. |
| `source_role_assessment` | Separates plausible in-window observations from out-of-window records of unresolved role. |
| `bibliographic_identity_resolved` | The shorthand code has a verified secondary-bibliography mapping. |
| `primary_full_text_obtained` | False for all rows. |
| `exact_primary_numeric_table_verified` | False for all rows. |
| `pressure_correction_lineage_verified` | False for all rows; absence of proof is not treated as pressure independence. |
| `training_allowed` | False for all rows. |
| `approval_blocker` | Exact evidence still needed before reconsideration. |

`evidence/source_temperature_window_audit.csv` is byte-identical to this table.

## `evidence/source_identity_resolution.csv`

Four independently scoped assertions:

- the 1996 shorthand-to-bibliography mapping;
- the official 1998 related chapter metadata;
- the official abstract's experimental interval; and
- the explicitly unverified equivalence of the 1996 and 1998 documents.

`status` describes the evidence level. `strict_label_implication` prevents bibliographic or abstract evidence from being mistaken for numeric-table verification.

## `review/source_access_inputs.csv` and `evidence/source_access_audit.csv`

Versioned access receipts for Månsson 1977, Mathews 1926, the 1996 ELDATA item, and the related 1998 Springer chapter. They record the exact access level and whether full text, methods, or numeric tables were obtained. The evidence export is regenerated from the review input.

## `review/remaining_verification_queue.csv`

The inherited source queue with updated access and triage statuses. `candidate_rows` and `additional_unapproved_training_molecules` are opportunities, not guaranteed additions and must not be summed across overlapping reference codes.

## Inherited v0.4 files

The NIST sensitivity labels, gamma constraints, ancillary reconstruction, pressure-lineage checks, modeling contract, and sensitivity policy are byte-identical to v0.4. Their definitions are in `previous_v0_4/DATA_DICTIONARY.md`.

## JSON evidence

- `access_followup.json`: structured copy of the four access receipts and the no-promotion conclusion.
- `parent_release_receipt.json`: v0.4 manifest, archive, strict-label, and molecule-list hashes.
- `validation.json`: software-verification result.
- `reproducibility.json`: repeated-rebuild hash comparison.
- `frozen/summary.json`: machine-readable current counts and readiness status.

## Historical files

`previous_v0_4/` is an immutable complete copy of the parent release. It already contains the earlier releases and the original pressure observations, splits, episodes, anchors, and cold targets.

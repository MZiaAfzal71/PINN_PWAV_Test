# Additional fields in the v0.2 enthalpy review

Original identities and candidate metadata follow `baseline_v0_1/DATA_DICTIONARY.md`. CSV booleans serialize as `True`/`False`; empty cells mean unknown/not applicable, never zero. Record IDs are stable source identifiers. Use a CSV parser, not comma splitting, because names, InChIs and JSON cells may contain commas.

| Field | Meaning |
|---|---|
| `original_H_kJ_mol`, `original_T_K`, `original_reported_deviation`, `original_decision` | Unmodified v0.1 values retained for audit. |
| `primary_H`, `primary_deviation`, `primary_unit` | Original printed measurement and deviation, before conversion. |
| `unit_multiplier_to_kJ` | 4.1840 for defined kcal/mol; 1 for kJ/mol. |
| `H_kJ_mol`, `H_J_mol`, `T_K` | Current curated numeric label and actual measurement temperature on approved rows. On unresolved rows these remain the original candidate values. |
| `primary_page`, `primary_table`, `primary_compound_name` | Location and chemical name/formula in the original table. |
| `structure_smiles_from_primary_name` | Explicitly reviewed chemical-name/formula interpretation; converted to full InChI and checked against the frozen identity. |
| `primary_identity_verified` | Name/formula interpretation gives an exact full-InChI match. Does not assert identity of physical samples across different experiments. |
| `primary_numeric_table_verified`, `table_image_visually_checked` | Numeric entries checked against the original table image. |
| `full_primary_methods_verified` | Measurement paper and applicable original apparatus description were reviewed. |
| `primary_document_sha256`, `primary_source_url` | Exact reviewed document receipt and public source link. |
| `thermodynamic_state` | Approved rows: liquid-to-real-vapor saturation enthalpy; no ideal-gas conversion. |
| `uncertainty_kind` | Either estimated total including systematics with unknown coverage, or twice the standard error of the mean for random error only. |
| `reported_deviation` | Quoted deviation converted to kJ/mol on reviewed direct rows; not automatically one sigma. |
| `random_standard_error_kJ_mol` | Quoted deviation / 2 only where the original source explicitly states twice-standard-error. |
| `standard_error_multiplier` | 2 for those random-error entries; separate from a confidence coverage factor. |
| `systematic_error_bound_kJ_mol` | 0.08 for the 1968 source; no assumed probability distribution. Missing in another paper does not mean zero systematic error. |
| `uncertainty_confidence_percent`, `uncertainty_coverage_factor` | Blank for all approved rows: not supplied by these sources as modern expanded uncertainty metadata. |
| `ancillary_apparatus_pressure_used` | Pressure affects operation or small apparatus/mass corrections; this differs from deriving H from a vapor-pressure curve. |
| `pressure_curve_used_to_derive_label`, `benchmark_pressure_used_for_label` | False for approved labels after original-method and correction-lineage review. |
| `independent_of_pressure_verified` | Operational measurement independence defined in `config.json`; not statistical independence of laboratory errors. |
| `measurement_lineage_id` | Source and experiment lineage; distinct measurements can share the same molecule. |
| `minimum_replicates_in_reported_mean` | Source states at least five determinations; not five independent molecular labels. |
| `training_allowed` | Label-level eligibility for future training. The project-level readiness gate is separate and still HOLD. |
| `quality_flags` | Retained impurity, water, phase-stability or source-conflict limitations. |
| `inside_pressure_temperature_envelope` | Coverage check against retained same-molecule pressure temperatures; no pressure slope fitted. |
| `review_wave`, `source_review_status` | Distinguish this 14-code review from candidates not examined in this wave. |

`approve_primary_calorimetry` is the only approved decision. All `hold_*` and `quarantine_*` rows remain excluded from fitting. A verified direct table row can still be held, as for the source-conflicted ethylenediamine value.

`source_register.csv` DOI arrays for unresolved references are bibliography leads, not approved data lineage. In particular, the two 1985 paper candidates must not both be attached to every row.

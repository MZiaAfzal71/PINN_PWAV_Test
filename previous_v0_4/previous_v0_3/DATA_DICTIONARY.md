# Fields in the v0.3 enthalpy review

Original identities and candidate metadata follow `baseline_v0_1/DATA_DICTIONARY.md`. CSV booleans serialize as `True`/`False`; empty cells mean unknown/not applicable, never zero. Record IDs are stable source identifiers. Use a CSV parser, not comma splitting, because names, InChIs and JSON cells may contain commas.

| Field | Meaning |
|---|---|
| `original_H_kJ_mol`, `original_T_K`, `original_reported_deviation`, `original_decision` | Unmodified v0.1 values retained for audit. |
| `primary_H`, `primary_deviation`, `primary_unit` | Original printed measurement and deviation, before conversion. |
| `unit_multiplier_to_kJ` | 4.1840 for defined kcal/mol; 1 for kJ/mol; for NIST specific energies, 1.000165 × molar_mass_g_mol / 1000. The transcription input marks this as computed; the reviewed export stores the numeric multiplier. |
| `H_kJ_mol`, `H_J_mol`, `T_K` | Current curated numeric label and actual measurement temperature on approved rows. NIST held rows also contain normalized primary values; other unresolved rows retain original candidate values. Eligibility is a separate field. |
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
| `minimum_replicates_in_reported_mean` | Source-reported minimum; five was retained from v0.2. New Lund rows also have exact replicate counts; NIST rows have 2–4, as transcribed. |
| `training_allowed` | Label-level eligibility for future training. The project-level readiness gate is separate and still HOLD. |
| `quality_flags` | Retained impurity, water, phase-stability or source-conflict limitations. |
| `inside_pressure_temperature_envelope` | Coverage check against retained same-molecule pressure temperatures; no pressure slope fitted. |
| `review_wave`, `source_review_status` | Distinguish original wave1 rows, new wave2 transcriptions, access review and unreviewed candidates. |

`approve_primary_calorimetry` is the only approved decision. All `hold_*` and `quarantine_*` rows remain excluded from fitting. A verified direct table row can still be held, as for the source-conflicted ethylenediamine value.

`source_register.csv` DOI arrays for unresolved references are bibliography leads, not approved data lineage. In particular, the two 1985 paper candidates must not both be attached to every row.


## Additional distinctions introduced in v0.3

| Field / file | Meaning |
|---|---|
| `previous_v0_2_decision` | Historical decision before this follow-up. |
| `overall_uncertainty_relation`, `overall_uncertainty_value_kJ_mol` | Printed overall-error statement: 1971 `<= 0.1`; 1970 `>= 0.2`. No reversal, Gaussian model or upper bound inferred for the latter. |
| `reported_replicates_exact` | Actual number of determinations in a new source table, not molecular sample size. |
| `moisture_treatment` | Whether water uptake was corrected, negligible as reported, known but uncorrected, or a source-wide caution. |
| `ancillary_reference_notes` | Unresolved pagination, reference-constant or upstream source limitations. |
| `source_temperature_adjustment` | Source's within-experiment temperature treatment, distinct from any adjustment performed in this release. |
| `temperature_correction_applied` | No additional enthalpy correction was applied by this curation. It does not mean the original authors made no run-temperature corrections. |
| `temperature_scale_note` | Retains historical scale caveats, especially NIST's International Temperature Scale. |
| `mean_gamma_intJ_g`, `beta_intJ_g`, `primary_H` on NIST rows | Printed energy per withdrawn mass, correction, and specific latent heat; L=gamma−beta. |
| `energy_conversion_factor_to_abs_J` | 1.000165 for US international J, from NBS Circular 475 p.22. It is not the defined-calorie conversion. |
| `molar_mass_g_mol` | Conventional natural-isotopic-average RDKit MolWt, rounded to 0.001 g/mol and made explicit for NIST normalization. |
| `estimated_relative_error_fraction` | NIST authors' 0.001 relative-error estimate, with no confidence convention. |
| `author_estimated_total_error_kJ_mol` | NIST estimate × normalized H; separate from a reported statistical deviation. |
| `pressure_slope_ancillary_correction` | True for NIST beta; false for eligible labels. |
| `pressure_curve_used_to_derive_label` | True for NIST because a curve derivative contributes to the correction; this does not mean the whole measurement is a pressure-derived pseudo-label. |
| `benchmark_pressure_used_for_label` | False for eligible labels; `unknown_upstream_ancillary_lineage` for NIST. No benchmark pressures were used by this curation. |
| `source_role` | Distinguishes reported primary calorimetry, possible historical reuse, and NIST calorimetry with a derivative correction. |
| `unresolved_lineage_leads.csv` | Comparison values only, all ineligible. Numerical resemblance does not establish a source-code mapping. |

Blank cells are missing/not applicable, never a measured zero. The NIST `primary_deviation` and `reported_deviation` stay blank because the source gives an overall relative accuracy estimate rather than a printed row-level deviation. Extra digits in exact arithmetic are not claims of experimental precision. All 14 NIST rows remain excluded under `hold_ancillary_pressure_slope_lineage`.

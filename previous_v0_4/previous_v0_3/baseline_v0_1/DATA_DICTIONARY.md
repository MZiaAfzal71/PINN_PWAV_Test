# Data dictionary and release contents

All CSV files are UTF-8 with headers. Boolean columns use `True`/`False`; blank cells mean unavailable or not applicable, **not zero**. JSON-valued columns are literal JSON arrays or objects. Record identifiers are stable source locators. Numerical uncertainty values must be interpreted with their accompanying convention; they are not automatically standard deviations.

## Frozen tables

| File in `frozen/` | Meaning and safe use |
|---|---|
| `molecular_review.csv` | All 860 earlier pressure candidate identities, RDKit checks and exclusion reasons. Includes excluded molecules. |
| `split_assignments.csv` | One row per included molecule: full InChI, canonical isomeric SMILES, connectivity key, component, split and coverage/candidate flags. This is the authoritative molecular partition. |
| `pressure_observations.csv` | Audit ledger of all 13,731 retained-scope pressure rows before copy removal, including held-out targets and duplicate copies. Not a training table. |
| `train_pressure.csv` | All 9,776 allowed global-training pressure observations. |
| `validation_anchors.csv`, `test_anchors.csv` | Three allowed adaptation anchors per primary-cap held-out episode. |
| `validation_cold_targets.csv`, `test_cold_targets.csv` | Primary-cap held-out scoring responses; never global-training or adaptation inputs. |
| `source_series_review.csv` | Coverage and descriptive monotonicity flags for all 1,317 included source series. A flag is not a rejection. |
| `episodes.csv` | One row per eligible molecule/cap, with source series, coverage and fixed JSON lists of anchor/cold-target record IDs. Training episodes are simulations, not an additional held-out split. |
| `episode_records.csv` | One row per episode/observation, with `anchor` or `cold_target` role and its cap-specific temperature-level identifier. Join to pressure observations by `record_id`; use these levels for metric aggregation. |
| `enthalpy_decisions.csv` | All compendium rows plus ThermoML rows sharing an identity with the earlier pressure candidate set. Includes out-of-scope and quarantined labels. |
| `enthalpy_candidates.csv` | In-scope calorimetry candidates only. **Every row is quarantined; none is a training label.** |
| `enthalpy_primary_labels.csv` | Approved enthalpy supervision. Header-only in this release. |
| `enthalpy_lineage_links.csv` | Seven possible shared-measurement links between compendium and archive; original numerical values retained, no averaging or automatic merger. |
| `source_review_queue.csv` | 194 reference/DOI entries requiring review, ordered by training-molecule coverage, then total coverage and reference ID. A source may appear through both a code and DOI. |
| `group_edges.csv` | The identity, structural and source relationships that define indivisible components. |
| `source_aliases_for_grouping.csv` | Conservative possible matches between reference codes and archive DOIs. Used for split embargo only; not certified reference resolution. |
| `summary.json` | Counts, versions, readiness result and partition summaries. |
| `pressure_ceiling_sensitivity.json` | Fixed episode counts and shared-source/split policy at 20, 10 and 5 kPa. |

## Identifier and pressure fields

| Field | Definition |
|---|---|
| `record_id` | ThermoML: `DOI#d<data block>#p<property>#r<1-based numeric row>`; compendium: `rdr250199#csvline<1-based line>`, counting the header as line 1. |
| `series_id` | ThermoML DOI, block and property, without the numeric-row suffix. |
| `molecule_id` | `mol_` plus first 16 hex characters of SHA256 of the exact full InChI. The full InChI remains available for verification. |
| `component_id` | `grp_` plus first 16 hex characters of SHA256 of sorted full InChIs joined with newline. |
| `T_K` | Temperature in kelvin from the original numeric variable or constraint; enthalpy rows use their own reported temperature. |
| `p_Pa` | Vapor pressure in pascals, computed from the archive's kPa value by multiplying by 1,000. |
| `log10_p_over_1Pa` | `log10(p_Pa / 1 Pa)`, the prediction/scoring target. |
| `ln_p_over_1Pa` | Natural log of the same dimensionless pressure, for CC derivatives. |
| `temperature_level_id` | Sorted 0.1 K full-series level grouping; for scoring use the episode-specific level in `episode_records.csv`. |
| `episode_temperature_level_id` | Cap-specific level computed after episode filtering; repeated rows at this level receive equal collective weight in the primary metric. |
| `base_role` | `train_pressure`, `adaptation_anchor`, `cold_target`, `withheld_other`, or `duplicate_copy_never_used`; anchor/target roles here refer only to 20 kPa. |
| `is_duplicate_copy` | Exact repeated source/full-InChI/T/p observation; excluded from all fitting and scoring. |
| `duplicate_representative_id` | Stable retained observation for that exact tuple. |
| `original_property_value_metadata_json` | Unchanged archive value metadata. Pressure uncertainties in this JSON retain original **kPa** units, even though `p_Pa` is in Pa. Do not weight a Pa residual with an unconverted kPa uncertainty. |
| `state_metadata_json`, `state_origin` | Original temperature information and whether it came from a variable or constraint. |

Exact copies are identified across blocks within a DOI. Similar but unequal values are not rounded into equality. Common measurements copied across different papers remain a provenance-review issue.

## Enthalpy fields and decisions

| Field | Definition |
|---|---|
| `H_kJ_mol`, `H_J_mol` | Reported molar vaporization/sublimation enthalpy and its exact factor-1,000 SI conversion. Only liquid/gas calorimetry passes the candidate screen. |
| `method` | Original compendium method code or archive method string; only exact C enters the compendium candidate pool. |
| `reference_codes_json`, `source_doi`, `source_locator` | Original references and row-level source locator. A blank DOI does not mean no reference exists. |
| `reported_deviation` | Source deviation/uncertainty in kJ/mol for enthalpy; its interpretation is given separately. |
| `uncertainty_kind` | `combined_expanded`, `unspecified_compendium_deviation`, or `not_reported`. |
| `uncertainty_confidence_percent`, `uncertainty_coverage_factor` | Reported convention only. Blank coverage factor is not silently filled with 2. |
| `experimental_temperature_range` | Original compendium range if present. It is not substituted with auxiliary `T_low`, `T_high` or `T_mid` fields. |
| `inside_pressure_temperature_envelope` | Whether reported H temperature lies inside any screened pressure-temperature span for the identity; a descriptive flag, not proof of state validity and not an inclusion requirement. |
| `raw_row_verified`, `archive_XML_verified` | Original CSV or XML transcription checks. They do not certify independence. |
| `calorimetry_candidate` | Passes numeric, identity, method and available-metadata screening. It does **not** authorize training. |
| `full_primary_methods_verified`, `independent_of_pressure_verified`, `training_allowed` | All false in this release. These distinctions must remain explicit in future releases. |
| `corrected_298_field_excluded` | True: derived compendium `Hvap_298` is not used as an independent observed target. |
| `duplicate_family`, `linked_record_ids_json` | Possible shared-measurement family and connected original records; original temperatures/values remain separate pending review. |
| `decision` | `excluded_from_primary_scope`, `quarantine_compendium_provenance`, `quarantine_archive_calorimetry`, or `quarantine_same_source_conflict`. No `approved` rows exist. |
| `decision_reasons` | Semicolon-delimited screening/provenance issues. |

`split=outside_frozen_scope` in the enthalpy ledger means the molecule is not one of the 703 assigned pressure molecules. It is not a fourth training split. Compendium values can refer to corrected reference temperatures even when they carry C; read the original method before interpreting them as direct values at `T_K`.

## Inputs, evidence and code

`inputs/` preserves the earlier extracted pressure and enthalpy tables, the original digitized compendium, source citations, block-level ThermoML provenance, NIST/RDR metadata, original dataset README, previous source-review examples and the new full XML-check report. `input_hashes.json` protects these exact bytes. The large archive is referenced by checksum and must be supplied separately to repeat XML parsing.

`evidence/integrity_verification.json` lists independent checks, cross-split similarities and episode counts. `evidence/reproducibility.json` records the second-build byte comparison. `evidence/readiness.json` records the separate scientific gate and its expected exit code. `MANIFEST.json` fingerprints all packaged files except itself and supplies a content-based release ID.

`build_freeze.py` recreates the frozen tables from included inputs with pinned RDKit grouping. `verify_source_archive.py` checks the original XML independently using only Python's standard library. `verify_freeze.py` checks leakage, IDs, units, episode access and quarantines. `check_readiness.py` checks package hashes and the independent-label release gate. `requirements.txt` pins the data/structure libraries; no model code or training outputs are included.

`review/label_review_template.csv` is an unfilled working template for the 751 candidate rows. Work on a copy and cite primary page/table/method evidence; filling it alone does not overwrite the frozen decisions. Do not use the template to replace source-specific temperatures or uncertainty conventions without recording a derivation.

`review/source_lookup.csv` links source queue entries to available DOI leads. Code-to-DOI leads remain provisional. `review/prioritized_training_sources.csv` greedily selects the reference with the most as-yet-uncovered candidate training molecules, with lexical reference-code ties, until all 168 have potential coverage. The first 14 entries cover 100 candidates; the complete 69-entry plan is a review aid, not evidence that those labels are valid.

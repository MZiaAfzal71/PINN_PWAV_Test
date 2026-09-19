# Enthalpy curation and evaluation split freeze — v0.1.0

Frozen 16 September 2026. **The split and transcription checks pass; the enthalpy training release remains on hold.** No predictive models have been trained.

This package addresses the proposed study: can independently measured vaporization enthalpies improve cold-end vapor-pressure prediction, and does a Clausius–Clapeyron constraint improve on an otherwise matched multitask model given the same enthalpy labels?

The package freezes the data decisions, molecular assignments, observation IDs, three-anchor evaluation episodes, metrics, seeds and provenance. It deliberately distinguishes a *calorimetry candidate* from a *certified pressure-independent training label*. The latter requires primary methods and correction-lineage evidence that is not established by the supplied archive or the compendium method code.

| Result | Frozen count |
|---|---:|
| Compendium rows checked against the original CSV | 16,727 |
| Pressure / enthalpy rows checked against original ThermoML XML | 16,214 / 1,008 |
| Transcription mismatches | 0 |
| Eligible pressure molecules after conservative structure screens | 703 |
| Pressure observations after exact-copy removal | 13,500 |
| Quarantined calorimetry candidate rows / molecules | 751 / 194 |
| Certified independent enthalpy training labels | **0** |

| Split | Molecules | Pressure rows after deduplication | Cold-end episodes at 20 kPa | Exposed warm anchors | Cold target rows |
|---|---:|---:|---:|---:|---:|
| Training | 492 | 9,776 | 292 for training simulations | Not an evaluation restriction | Not held out |
| Validation | 106 | 1,706 | 66 | 198 | 376 |
| Test | 105 | 2,018 | 78 | 234 | 512 |

Read `VALIDATION_REPORT.md` for findings and limitations, then `EVALUATION_PROTOCOL.md` for the fixed experiment. `DATA_DICTIONARY.md` describes the files. `frozen/summary.json` contains machine-readable counts.

## Files to use

- `frozen/train_pressure.csv`: the only pressure observations permitted for global model fitting.
- `frozen/validation_anchors.csv` and `frozen/test_anchors.csv`: exactly three warm anchors per evaluation molecule at the primary 20 kPa cap. Fit an isolated adaptation instance for each molecule.
- `frozen/validation_cold_targets.csv` and `frozen/test_cold_targets.csv`: scoring targets. Test targets must stay out of model selection and adaptation.
- `frozen/enthalpy_primary_labels.csv`: **intentionally header-only**. Nothing in the candidate pool is currently approved for enthalpy supervision.
- `frozen/enthalpy_candidates.csv`: 736 compendium C rows and 15 ThermoML calorimetry rows, all quarantined. They are not 751 independent experiments.
- `frozen/source_review_queue.csv` and `review/label_review_template.csv`: the remaining source review. `review/source_lookup.csv` provides available DOI leads, and `review/prioritized_training_sources.csv` prioritizes new training-molecule coverage.

Do not fit a model directly on `pressure_observations.csv` or `enthalpy_decisions.csv`: these audit ledgers also contain held-out observations, duplicate copies, rejected rows and unverified labels. All held-out molecules' enthalpies remain hidden from training and adaptation, including values at warm temperatures.

## Reproduce and verify

Use Python 3.12; the executed environment was Python 3.12.14. From this extracted package directory:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python verify_freeze.py
python check_readiness.py
```

`verify_freeze.py` exits 0 for the internal checks. `check_readiness.py` deliberately exits **2**, reporting `HOLD_ENTHALPY_PROVENANCE`. This is the scientific conclusion of the audit, not an installation failure.

Rebuild into a separate directory to preserve this release:

```bash
python build_freeze.py --out ../freeze_rebuild
python verify_freeze.py --frozen ../freeze_rebuild --out ../rebuild_verification.json
```

The frozen tables were rebuilt independently into a second output directory and compared byte-for-byte. Input hashes, output hashes and the release identifier are in `input_hashes.json`, `evidence/reproducibility.json` and `MANIFEST.json`.

The 189.4 MB uploaded archive is not duplicated in this package. Its exact checksum is in `config.json`. To repeat the independent XML check, supply your original archive and write the new report outside this release:

```bash
python verify_source_archive.py --archive /path/to/ThermoML.v2020-09-30.tgz --out ../archive_recheck.json
```

The XML/JSON comparison checks extraction, units, identity, phase, temperature and stored numerical metadata. NIST generates XML and JSON from the same data; their agreement is not independent experimental replication.

## What is needed before the enthalpy models

Review the primary measurement papers and corrections for the candidate labels. The previous audit proposed a feasibility threshold of at least 100 independently verified molecules; this release makes it operational by requiring at least 100 in the **training partition**. This is a project-specific feasibility criterion, not a statistical power calculation or a universal publication requirement. Currently, 168 training molecules have candidates, but none has completed that review.

The coverage-prioritized plan reaches 100 candidate training molecules in its first **14 reference entries**. This is a practical starting set for primary-paper review, not a promise that all 100 will pass certification. The complete plan covers all 168 candidate training molecules.

Create a reviewed successor release when the evidence is available. Preserve this release and its assignments; do not silently promote C rows, replace measured-temperature values with `Hvap_298`, or move molecules between splits. Newly discovered common-source lineage that crosses a split requires a documented embargo or an explicitly versioned split revision before modeling.

Data attribution, dataset versions and original compendium citations are retained in `THIRD_PARTY_NOTICES.md` and `inputs/`. This package does not claim ownership of the source measurements.

# Enthalpy source verification v0.3.0

**42 primary labels on 41 training molecules are eligible. The original 100-training-molecule gate remains on hold; 59 more are needed.** This update adds five eligible Lund labels and documents fourteen NIST labels whose pressure-slope correction lineage remains unresolved. No models were fitted.

Read `SOURCE_REVIEW_REPORT.md` for source links, corrections, uncertainty interpretation, limitations and the next verification priorities.

| Use | File |
|---|---|
| Current primary labels | `frozen/enthalpy_primary_labels.csv` |
| All 751 candidates and current decisions | `frozen/enthalpy_candidates_reviewed.csv` |
| NIST values normalized but ineligible | `frozen/enthalpy_nist_ancillary_hold.csv` |
| Unique eligible training molecules | `frozen/training_enthalpy_molecules.csv` |
| Original numeric transcriptions and source-driven decisions | `review/primary_table_transcriptions.csv` |
| Source identities and review/access status | `review/source_register.csv` |
| NIST correction/unit arithmetic | `evidence/nist_conversion_checks.csv` |
| Six published water-correction runs | `review/1971_methoxyethanol_correction_runs.csv` |
| Full-InChI mapping and source overlap receipts | `evidence/identity_verification.csv`, `evidence/source_overlap_check.csv` |
| Remaining verification opportunities | `review/remaining_verification_queue.csv` |
| Software verification and rebuild results | `evidence/validation.json`, `evidence/reproducibility.json` |

The complete original freeze is in `baseline_v0_1/`, unchanged. Use its pressure tables, split assignments and evaluation protocol. The previous review's files are archived in `previous_v0_2/`; its baseline dependency is shared at this release's root and checked by the current verifier. Those archived scripts are historical records, not the commands for this release. Do not concatenate historical label exports with current labels.

## Reproduce

Python standard-library integrity and arithmetic checks:

```bash
python verify_review.py
python check_readiness.py
```

The readiness command intentionally exits **2**, reporting `HOLD_ENTHALPY_PROVENANCE`. A successful integrity check does not open the scientific gate.

With the environment pinned in `baseline_v0_1/requirements.txt`, including RDKit 2025.09.6:

```bash
python rebuild_review.py
python verify_review.py
```

The builder validates the original releases, interprets each reviewed primary name/formula through its recorded SMILES, checks the full InChI, and performs documented conversions. It reproduces scientific review inputs; it does not automatically verify a publication or certify an experiment.

Optional retrieval of the ten original measurement/method/comparison PDFs for reinspection:

```bash
python fetch_primary_sources.py --out ../primary_papers
```

The downloader checks recorded SHA256 hashes. Availability and response time depend on the host. The NBS metrology reference has a separate official-PDF text receipt; direct local download was unavailable. Full source PDFs/OCR are not redistributed in this bundle.

All eligible labels are at one temperature, from one laboratory and one training component. Printed random deviations, overall-error estimates and inequality directions remain separate. In particular, the 1970 paper prints overall uncertainty **>=0.2 kJ/mol**, with no finite upper bound; its small random errors must not be treated as total uncertainties. The report specifies source-driven moisture sensitivities before any model fitting. This is an AI-assisted source/table review without independent human sign-off.

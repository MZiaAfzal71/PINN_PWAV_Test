# Enthalpy source review — v0.2.0

**37 calorimetric labels on 36 training molecules are approved for a future model. The main modeling gate remains on hold: 100 approved training molecules are required.** No models were fitted.

This release follows the first 14 references in the v0.1 priority queue. Those references cover 174 candidate rows and 100 molecular identities. Four original measurement papers and two referenced apparatus papers were obtained and reviewed. The other ten reference codes have explicit access or attribution blockers; their measurements have not been certified.

Read **SOURCE_REVIEW_REPORT.md** for findings and links to the remaining papers. All approved labels are measured at 298.15 K, from one laboratory and one existing training component. These counts do not imply 36 independent sources or adequate temperature coverage.

## Files to use

| Purpose | File |
|---|---|
| Current approved enthalpy labels | `frozen/enthalpy_primary_labels.csv` |
| All 751 candidates, with current decisions and original values | `frozen/enthalpy_candidates_reviewed.csv` |
| One row per approved training molecule | `frozen/training_enthalpy_molecules.csv` |
| Original-table numbers, units, pages and review decisions | `review/primary_table_transcriptions.csv` |
| All 174 rows in this priority wave | `review/priority_14_row_decisions.csv` |
| Reference identities, access status, DOI links and evidence notes | `review/source_register.csv` |
| Coverage and unresolved counts for the 14 references | `review/priority_source_results.csv` |
| Original versus restored values, temperatures and deviations | `review/numeric_changes.csv` |
| Experiment lineage, including the older acetonitrile comparison | `review/measurement_lineages.csv` |
| Original-document URLs and SHA256 hashes | `evidence/primary_document_register.json` |
| Exact primary-name structure to frozen InChI checks | `evidence/identity_verification.csv` |
| Source DOI overlap and partition checks | `evidence/source_overlap_check.csv` |

**The entire v0.1 release is preserved, byte for byte, in `baseline_v0_1/`.** Use its `frozen/train_pressure.csv`, split assignments, episodes, anchors, targets and evaluation protocol. Its historical enthalpy exports and readiness status describe v0.1 only; the current enthalpy exports and readiness check are at this release's root. Do not concatenate old and new label tables.

## Reproduce and verify

Basic integrity, numeric conversion and partition checks use Python's standard library:

```bash
python verify_review.py
python check_readiness.py
```

The second command intentionally exits with status **2** and reports `HOLD_ENTHALPY_PROVENANCE`, because 64 more approved training molecules are needed. A passing integrity check does not open the scientific gate.

To reconstruct the exports, use the environment pinned in `baseline_v0_1/requirements.txt` (including RDKit 2025.09.6), then run:

```bash
python rebuild_review.py
python verify_review.py
```

The builder verifies the parent release, maps each transcribed compound name through its explicitly reviewed SMILES to the existing full InChI, applies exact unit conversions, and reproduces the decision tables. It does **not** independently infer scientific truth from a method code or automatically review the papers. The reviewed transcriptions and judgments are versioned inputs.

To obtain the six original papers locally for reinspection:

```bash
python fetch_primary_sources.py --out ../primary_papers
```

The script checks the recorded PDF hashes. Access depends on the publisher archive remaining available. Paper PDFs and OCR text are not redistributed here. The source links, hash receipts, table coordinates and numeric facts are included.

This is an AI-assisted literature and table review, with no independent human sign-off. Confirm source-specific judgments before manuscript submission. The source-explicit ethylenediamine conflict and unverified older acetonitrile correction remain quarantined.

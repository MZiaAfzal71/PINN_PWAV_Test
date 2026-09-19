# Enthalpy source verification v0.5.0

**The strict direct-enthalpy pool remains frozen at 42 labels on 41 training molecules. The 100-molecule gate is still 59 molecules short, so main model fitting remains on hold.** No label, molecular split, evaluation episode, or pressure record changed, and no model was fitted.

This release completes the next source-access and identity-verification step:

| Source | Candidate rows | Potential additional molecules | Verification reached | Decision |
|---|---:|---:|---|---|
| `1977MAN/SEL` | 13 | 12 | DOI, publisher metadata, and abstract; full article not obtained | Hold all rows |
| `1926MAT` | 12 | 5 | Article identity and DOI; full article not obtained | Hold all rows |
| `1996VIT/CHA` | 19 | 5 | Bibliographic code resolved; official related chapter abstract checked; primary numeric table not obtained | Hold all rows |

The `1996VIT/CHA` reference code maps to C. Viton, M. Chavret, and J. Jose, *ELDATA: International Electronic Journal of Physico-Chemical Data* **2**, 103 (1996). A later official Springer chapter by the same authors is titled *Enthalpy of Vaporization of N-Alkanes (from Nonane to Pentadecane). Experimental Results - Correlation*, DOI `10.1007/978-3-642-72207-3_3`.

The official chapter abstract reports calorimetric measurements over **313–344 K**. Of the 19 compiled candidates:

- 14 lie inside that reported interval;
- four lie below it at 299 K; and
- one lies above it at 359 K.

The 14 in-window rows are plausible experimental observations, but the exact primary table, method details, uncertainty or precision statement, and correction lineage were not available. The five out-of-window rows cannot be classified as direct measurements rather than literature, normalized, interpolated, correlated, or extrapolated values. Therefore **zero rows are promoted**.

| Use | File |
|---|---|
| Unchanged strict direct-H labels | `frozen/enthalpy_primary_labels.csv` |
| Current decisions for all 751 candidates | `frozen/enthalpy_candidates_reviewed.csv` |
| Row-level Viton–Chavret decisions | `review/viton_chavret_candidate_decisions.csv` |
| Source identity assertions and limits | `evidence/source_identity_resolution.csv` |
| Access audit for the three closed-source targets | `evidence/source_access_audit.csv` |
| Full scientific findings | `SOURCE_REVIEW_REPORT.md` |
| Exact documents/pages needed next | `PRIMARY_SOURCE_REQUEST.md` |
| Remaining verification queue | `review/remaining_verification_queue.csv` |

The complete v0.4 release is preserved under `previous_v0_4/`, including the NIST gamma physics-constraint tier and the original frozen pressure evaluation design. Historical and current label exports must not be concatenated.

## Verify

Only the Python 3.12 standard library is required:

```bash
python rebuild_review.py
python verify_review.py
python check_readiness.py
```

`verify_review.py` must report `PASS`. `check_readiness.py` intentionally exits with status 2 and reports `HOLD_ENTHALPY_PROVENANCE` while the strict coverage gate remains unmet.

Source PDFs are not redistributed. URLs and access limits are recorded, and every metadata-only inference remains explicitly separated from primary-table verification. This is an AI-assisted review without independent human sign-off.

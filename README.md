# Enthalpy source verification v0.4.0

**The strict direct-enthalpy pool remains 42 labels on 41 training molecules. The inherited 100-molecule gate is still 59 molecules short, so main model fitting remains on hold.** No split changed and no model was fitted.

This release completes the archival follow-up for 14 values from Osborne and Ginnings (1947). The published latent heat is `L = gamma - beta`, where `gamma` is the measured electrical energy per withdrawn mass and `beta = T v dp_sat/dT` is calculated from vapor-pressure and liquid-volume data.

The result is a two-tier freeze:

- All 14 published `L` values are **sensitivity-only**. They cannot enter primary training, validation, or test.
- All 14 measured `gamma` values are frozen as **coupled PINN physics constraints**, not as direct enthalpy labels.

The accessible archival inputs reproduce 7 of the 14 printed beta values by nearest 0.01 international J/g rounding. Seven do not reproduce at that precision. Twelve pressure-slope inputs are present in the cited API table family; the n-nonane and n-decane slopes use an accessible 1945 primary correlation as a surrogate because the exact cited per-compound entries were not recovered. All 14 liquid-volume inputs are traced.

| Use | File |
|---|---|
| Unchanged strict direct-H labels | `frozen/enthalpy_primary_labels.csv` |
| Unchanged unique strict training molecules | `frozen/training_enthalpy_molecules.csv` |
| Current decisions for all 751 candidates | `frozen/enthalpy_candidates_reviewed.csv` |
| Published NIST L values, sensitivity only | `frozen/enthalpy_nist_sensitivity_labels.csv` |
| Raw NIST gamma physics constraints | `frozen/enthalpy_nist_gamma_constraints.csv` |
| Compound-level beta reconstruction | `evidence/nist_ancillary_reconstruction.csv` |
| Molecule-level pressure-source overlap check | `evidence/nist_pressure_lineage_overlap.csv` |
| Constraint equation and leakage rules | `PINN_CONSTRAINT_PROTOCOL.md`, `evidence/modeling_contract.json` |
| Full findings and limitations | `SOURCE_REVIEW_REPORT.md` |
| Remaining source-verification queue | `review/remaining_verification_queue.csv` |

The complete v0.3 release is preserved under `previous_v0_3/`, including the original v0.1 pressure data, molecular splits, and evaluation tables. Do not concatenate historical and current label exports.

## Verify

Only the Python standard library is required for the v0.4 calculations:

```bash
python rebuild_review.py
python verify_review.py
python check_readiness.py
```

`verify_review.py` must report `PASS`. `check_readiness.py` intentionally exits with status 2 and reports `HOLD_ENTHALPY_PROVENANCE` because the strict direct-H gate is not yet met.

The source PDFs are not redistributed. Their official URLs, SHA256 hashes, page locators, and roles are recorded in `evidence/archival_document_register.json`. This is an AI-assisted document and table review without independent human sign-off.

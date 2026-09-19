# NIST ancillary verification and final tier decision

18 September 2026. Parent release: v0.3.0. Original evaluation freeze: v0.1.0.

## Decision

The 14 Osborne-Ginnings rows do not enter the strict direct-enthalpy pool. Their published latent heats are frozen as a single sensitivity-only tier. Their directly measured `gamma` values are frozen separately as raw calorimetric constraints for a future coupled PINN.

The strict pool therefore remains **42 labels on 41 training molecules**, and the original 100-molecule project gate remains **59 molecules short**. No model was fitted, no molecular assignment changed, and no validation or test pressure target informed this decision.

## What the 1947 experiment measured

Osborne and Ginnings supplied electrical energy while withdrawing vapor at constant evaporation temperature. Their Table 1 reports the energy per withdrawn mass as `gamma`. The paper obtains latent heat through

`L = gamma - beta`, where `beta = T v_liquid dp_sat/dT`.

The `beta` term is therefore calculated from a saturation-pressure slope and liquid specific volume. It is small relative to `L`, but it is part of every published `L` value. The source says the volume and slope data came from API Research Project 44 tables and International Critical Tables, volume III.

The paper reports US international J/g. The retained conversion is 1.000165 absolute J per international J. Molar normalization is

`quantity [kJ/mol] = quantity [international J/g] * 1.000165 * molar_mass [g/mol] / 1000`.

All 14 printed `gamma - beta = L` subtractions and all molar conversions pass exactly.

## Archival inputs recovered

The following primary or archival documents were checked. Exact URLs, file hashes, and locators are in `evidence/archival_document_register.json`.

1. Osborne and Ginnings (1947), the official NIST scan: calorimetry, equations, and printed Table 1 values.
2. NBS Circular 461 (1947): the bound API Research Project 44 compilation. It supplies all 12 directly recovered Antoine pressure correlations and 13 of the 14 liquid molar volumes.
3. Willingham et al. (1945): primary Antoine correlations used here for n-nonane and n-decane. These are accessible surrogate slope inputs; the exact per-compound entries cited by the 1947 beta paragraph were not recovered.
4. International Critical Tables, volume III (1928): the printed density equation and n-decane coefficients. At 25 °C,

   `rho = 0.7455 - 0.7293e-3(25) - 0.371e-6(25)^2 = 0.727035625 g/mL`.

   This yields the n-decane specific volume used in the reconstruction.

The API volume tables state that the values apply to air-saturated liquid at one atmosphere. Circular 461 defines its historical absolute-temperature relation as K = °C + 273.160, so the source calculation uses 298.160 K. The frozen model coordinate remains 298.15 K for compatibility and is labeled separately.

## Numerical reconstruction

For an Antoine equation

`log10(p_mmHg) = A - B/(C+t_C)`,

the reconstruction uses

`dp/dT = ln(10) p B/(C+t_C)^2`

and

`beta [J/g] = 298.160 * v [cm3/g] * dp/dT [mmHg/K] * 0.000133322368421...`.

The primary decision rule is nearest 0.01 international J/g using round-half-up, matching the source's printed precision. The unrounded absolute difference and truncation result are also retained, but they do not replace the declared decision rule.

| Compound | Reconstructed beta | Published beta | Nearest 0.01 match | Slope lineage |
|---|---:|---:|:---:|---|
| n-Nonane | 0.015254 | 0.02 | Yes | Accessible surrogate |
| n-Decane | 0.005096 | 0.01 | Yes | Accessible surrogate |
| Benzene | 0.199900 | 0.20 | Yes | Cited API family |
| Cyclohexane | 0.226079 | 0.24 | No | Cited API family |
| n-Hexane | 0.398281 | 0.39 | No | Cited API family |
| Toluene | 0.067922 | 0.15 | No | Cited API family |
| o-Xylene | 0.017911 | 0.03 | No | Cited API family |
| m-Xylene | 0.022384 | 0.02 | Yes | Cited API family |
| p-Xylene | 0.023553 | 0.03 | No | Cited API family |
| Ethylbenzene, pure series | 0.025303 | 0.05 | No | Cited API family |
| Ethylcyclohexane | 0.035827 | 0.05 | No | Cited API family |
| n-Octane | 0.045117 | 0.05 | Yes | Cited API family |
| 2,2,4-Trimethylpentane | 0.136737 | 0.14 | Yes | Cited API family |
| 1,2,4-Trimethylbenzene | 0.006571 | 0.01 | Yes | Cited API family |

Thus **7/14 reproduce** by the declared nearest-cent rule and **7/14 do not**. The n-hexane value would agree under simple truncation, but its unrounded difference is 0.008281 J/g and it fails the frozen nearest-cent rule. Complete row-level arithmetic is in `evidence/nist_ancillary_reconstruction.csv`.

This result does not establish that the 1947 paper is erroneous. Exact working copies, revisions, interpolation choices, and unprinted intermediate digits are not all available, and the authors explicitly said high accuracy was not required for the small beta term. It does establish that the published correction cannot be reproduced uniformly from the accessible archival inputs at the printed precision. That is sufficient to withhold the resulting `L` values from the strict pressure-independent label pool.

## Why gamma remains useful

Unlike the published `L`, `gamma` is the reported energy-per-mass observation before subtracting the pressure-derived term. It supports a stronger PINN formulation that compares the raw instrumental observable with the coupled prediction:

`gamma = H_vap_model + T V_m dp_sat/dT`.

This avoids treating a historically corrected quantity as if it were a pressure-free enthalpy label. It also makes the pressure dependence explicit in the loss. The 14 records in `frozen/enthalpy_nist_gamma_constraints.csv` contain converted molar gamma, traced molar volume, both temperature conventions, the equation, and leakage flags.

These constraints do not count toward the direct-H coverage gate. No per-row gamma uncertainty was reported, so no artificial sigma or inverse-variance weights are supplied. The complete data-flow and ablation rules are frozen in `PINN_CONSTRAINT_PROTOCOL.md`.

## Pressure lineage and evaluation freeze

All 14 molecules belong to the original training split and the same frozen connected component as the strict labels. The frozen pressure data for these molecules contain 3 to 111 deduplicated rows per molecule. No NIST measurement DOI or archival-document DOI appears among their frozen pressure-source DOIs.

That non-overlap is a leakage check, not proof of statistical independence and not a reason to reclassify published `L` as pressure-free. The correction still uses a pressure slope by definition.

The original evaluation design remains unchanged:

- 492 train, 106 validation, and 105 test molecules.
- 78 primary 20 kPa test episodes.
- 234 warm adaptation anchors.
- 512 cold pressure targets.
- 42 strict enthalpy labels in train; none in validation or test.

The future gamma residual may use training-visible pressure data and model derivatives only. Held-out validation and test pressure targets are prohibited.

## Remaining verification

The completed NIST item has been removed from the open queue. The highest-value remaining source is Månsson et al. (1977), DOI `10.1016/0021-9614(77)90202-6`, with 13 candidate rows and up to 12 additional currently unapproved training molecules. Publisher and scholarly metadata are available, but the full methods, tables, footnotes, and correction lineage were not obtained. No row is approved from metadata or secondary compilations.

The release remains `HOLD_ENTHALPY_PROVENANCE`. The next research action is to obtain and verify that full paper or another comparably valuable primary calorimetry source before main model training.

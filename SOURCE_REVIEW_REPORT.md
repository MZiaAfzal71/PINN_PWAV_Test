# Enthalpy verification follow-up: v0.3.0

18 September 2026. Parent review: v0.2.0. Original evaluation freeze: v0.1.0.

**Five additional labels pass the existing primary-calorimetry eligibility rule. The primary pool now has 42 labels on 41 training molecules.** Fourteen additional NIST rows have verified original tables, identities and unit conversions, but remain excluded pending their ancillary pressure-slope lineage review. The 100-approved-training-molecule project gate is unchanged: 59 more molecules are needed. No models were fitted.

| Result | v0.2 | v0.3 |
|---|---:|---:|
| Primary labels eligible for future training | 37 | 42 |
| Unique training molecules represented | 36 | 41 |
| Original-table candidate rows checked | 38 | 57 |
| Candidates still excluded across the 751-row freeze | 714 | 709 |
| NIST rows normalized but held separately | 0 | 14 |
| Approved enthalpy temperatures | 298.15 K | 298.15 K |
| Laboratories represented in the primary pool | 1 | 1 |
| Frozen components represented in the primary pool | 1 | 1 |

These are molecular identities and observations, not independent laboratories. Eligibility means adequate evidence for the reported calorimetric quantity under the documented policy, not that every systematic error has a modern uncertainty budget. The original 100-molecule threshold is a project feasibility criterion, not a universal statistical power or publication rule.

## Five additional primary labels

All five belong to the existing training split and component. The original compendium values remain alongside the restored primary values. All temperatures are the reported 25°C, represented as 298.15 K; no new enthalpy extrapolation was applied.

| Compound | H at 298.15 K (kJ/mol) | Printed random deviation (kJ/mol) | Determinations | Primary source |
|---|---:|---:|---:|---|
| 2-Methoxyethanol | 45.17 | ±0.04 | 6 | Kusano–Wadsö 1971, Table 2, p.222 |
| 2-Ethoxyethanol | 48.21 | ±0.05 | 8 | Kusano–Wadsö 1971, Table 2, p.222 |
| 2-Propoxyethanol | 52.12 | ±0.10 | 7 | Kusano–Wadsö 1971, Table 2, p.222 |
| 2-Methoxyethyl acetate | 50.27 | ±0.06 | 5 | Kusano–Wadsö 1970, Table 1, p.2038 |
| 2-Butoxyethyl acetate | 59.54 | ±0.04 | 5 | Kusano–Wadsö 1970, Table 1, p.2038 |

The printed deviations are **twice the standard error of the mean for random error**. They are not total one-sigma uncertainties. The acetates' primary formulas were independently mapped to the frozen full InChIs. In particular, the ambiguous original name “ethylene glycol methyl ethyl acetate” is retained in the source-name field, with the verified interpretation 2-methoxyethyl acetate recorded separately.

### Water uptake and uncertainty

The [1971 alkoxyethanol paper](https://actachemscand.ki.ku.dk/pdf/acta_vol_25_p0219-0224.pdf) measures water uptake and corrects methoxyethanol and ethoxyethanol using electrical energy, evaporated mass and water uptake. Its Table 1 supplies six methoxyethanol runs. Every printed apparent enthalpy plus condensation and dissolution corrections reproduces its printed corrected value. The source obtains 45.17 kJ/mol from a joint fit. The simple mean of rounded corrected runs is 45.164833 kJ/mol; this is not claimed to reproduce that fit exactly. Propoxyethanol uptake was reported as very small. The authors print overall uncertainty ≤0.1 kJ/mol. This statement is separate from the random deviations.

The [1970 acetate paper](https://actachemscand.ki.ku.dk/pdf/acta_vol_24_p2037-2042.pdf) prints an overall uncertainty of **≥0.2 kJ/mol**. The inequality was checked on the page image and retained verbatim as a numerical relation; it has not been silently reversed. It supplies no finite overall upper bound. Methoxy compounds gained about 0.02% water during measurement, without correction. Both acetate labels carry the source-wide systematic-error caution, and the methoxy acetate carries the specific moisture flag. They remain eligible under the existing policy, which already retains disclosed purity/moisture limitations in the absence of a source-reported contradictory measurement. They must not receive high confidence merely because their random SE is small.

For a later robustness analysis, exclude the two 1970 acetate labels together and report the change; a stricter moisture-lineage check may additionally exclude the two water-corrected 1971 labels. These source-driven exclusions are specified before model fitting. They are not selected by agreement with pressure data. Do not use inverse random-SE weighting as if it represented total measurement precision.

### Ancillary reference limitations retained

Both new Lund papers cite the verified [1966 apparatus description](https://actachemscand.ki.ku.dk/pdf/acta_vol_20_p0536-0543.pdf). Their additional citation to Acta 22 (1968), p.2434 does not match the archive: p.2434 belongs to an unrelated article spanning pp.2429–2437. The Wadsö paper with calorimeter modifications starts on [p.2438](https://actachemscand.ki.ku.dk/pdf/acta_vol_22_p2438-2444.pdf), making it a plausible intended reference, not a confirmed correction to the bibliography.

The 1971 water correction explicitly uses **2.433 kJ/g**. This is recorded as the source's numerical input; it has not been replaced by a modern water value. The exact cited-reference derivation of that constant was not established. Primary energy/mass measurement, the published correction mechanism and the run arithmetic are established; complete metrological traceability of every auxiliary constant is not claimed. This limitation motivates the predefined moisture sensitivity. The published label itself is preserved rather than recalculated from incomplete raw experimental records.

## Osborne–Ginnings 1947: recovered and checked, still held

The full 25-page paper was obtained from the [official NIST Digital Archives](https://nistdigitalarchives.contentdm.oclc.org/digital/collection/p16009coll6/id/118316/). Table 1 covers calorimetry at 25°C. Fourteen frozen candidate rows were visually transcribed, with exact primary-name-to-InChI checks. The pure ethylbenzene series was selected explicitly; its impure-sample series was not averaged into it. No new molecular identities were added from the other compounds in the paper.

The table's energies are **US international J/g**, not modern molar kJ. [NBS Circular 475, p.22](https://nvlpubs.nist.gov/nistpubs/Legacy/circ/nbscircular475.pdf) supplies the factor 1.000165 absolute J per US international J. Normalization uses

`H [kJ/mol] = L [international J/g] × 1.000165 × M [g/mol] / 1000`.

Each molar mass is explicit, using RDKit 2025.09.6 conventional natural-isotopic-average masses. This is a documented modern mass normalization of a primary specific-energy measurement. Extra output digits preserve arithmetic, not experimental accuracy. The reported 25°C used the historical International Temperature Scale; 298.15 K is its nominal representation, with no claim of conversion to ITS-90.

The measured electrical energy per withdrawn mass is gamma. The published latent heat is

`L = gamma − beta`, with `beta = T × v_liquid × dp_sat/dT`.

All fourteen printed subtractions pass exactly. Across these candidate rows, beta is approximately **0.00251–0.10654%** of L. The paper derives the pressure slopes and liquid volumes from API Research Project 44 tables and International Critical Tables, volume 3 (1928), identified as references 14 and 15. The original per-compound ancillary entries have not been traced.

These are principally calorimetric measurements with a small pressure-derived correction. They should not be described as pressure-curve-free, and the correction does not imply that the entire measurement is a pressure-derived pseudo-label. The measurement DOI does not overlap any frozen pressure DOI. That fact alone cannot establish upstream independence. The fourteen rows remain in `frozen/enthalpy_nist_ancillary_hold.csv`, with `training_allowed=False`, and do not count toward the primary gate.

The authors estimate that the error is unlikely to exceed 0.1% for these hydrocarbons. That statement is stored separately as an author estimate, with no invented confidence probability or Gaussian sigma. Small source-applied run-temperature corrections and sample-purity limitations are disclosed. No ideal-gas-state transformation was applied.

## Source attribution and repeated measurements

The [1962 Sellers–Sunner paper](https://actachemscand.ki.ku.dk/pdf/acta_vol_16_p0046-0052.pdf), Table 7, reports calorimetric vaporization values for cyclopentanone, cyclopentanol, cyclohexanone and cyclohexanol. Their numerical resemblance to the four unresolved `1968PLA/WIL` candidates is a useful lead. It does not prove the compendium's source attribution, so no code or DOI was substituted and no new label was added.

The neighboring uncertainties in that table belong to **combustion**, not vaporization, and must not be transferred. Cyclopentanol's 13.74 kcal/mol and sample source also appear in Wadsö 1966, which includes earlier measurements. The existing approved row is annotated as a possible repeated report of the same experiment. It is counted once. The 1962 report does not create a second independent observation.

The alcohol/pyridine ambiguity in `1985MAJ/SVO2` is unresolved. The 2016 compendium reference-list PDF was not retrieved: the UMSL repository returned 403 and the UNT advertised download returned a request-validation challenge. No bypass was attempted. Earlier ambiguous-reference and inaccessible-full-text holds continue. The source-conflicted ethylenediamine value and the older temperature-corrected acetonitrile entry remain excluded.

## Evaluation freeze and verification

The entire v0.1 release remains byte-identical. The v0.2 review is also preserved with its own checksums. Current review exports retain all **751 original candidate IDs**, full InChIs, molecule IDs, source/structure components and split assignments. The five new eligible molecules all belong to the existing training component.

- Molecular partitions: **492 train / 106 validation / 105 test**.
- Primary 20 kPa test protocol: **78 episodes, 234 warm anchors, 512 cold targets**.
- Eligible enthalpy labels: **42 train / 0 validation / 0 test**.
- Primary labels within their molecule's retained pressure-temperature envelope: **23**; outside: **19**.

Outside-envelope labels remain auxiliary observations at their reported temperature. No pressure extrapolation or artificial pointwise pressure–enthalpy join was created. No pressure fit, Clausius–Clapeyron residual, test loss or held-out target value was used to decide label eligibility. DOI and temperature metadata were used only for provenance and coverage checks.

`verify_review.py` checks original release hashes, all candidate identities/splits, unchanged prior eligible values, the five new approvals, exact unit arithmetic, NIST quarantine, uncertainty inequality direction, correction arithmetic and preserved test records. `rebuild_review.py` reproduces the exports from the versioned scientific review inputs. Passing software checks supports data integrity; it does not replicate experiments or provide independent human scientific sign-off.

## Next verification with the highest value

1. Trace the 1947 ancillary pressure/volume entries in API Project 44 and International Critical Tables, then make an explicit primary-versus-sensitivity eligibility decision. Potential reach: 14 currently unapproved training molecules.
2. Obtain the full [Månsson et al. 1977 paper](https://doi.org/10.1016/0021-9614(77)90202-6), including methods, tables, footnotes and correction references. It potentially reaches 12 additional molecules beyond the current primary pool, with overlap against other sources possible.
3. Obtain the compendium reference list and original papers to resolve `1968PLA/WIL` and `1985MAJ/SVO2`. Consult `review/remaining_verification_queue.csv` for all remaining source opportunities; these counts are not guaranteed approvals.

Main modeling remains on hold. The eventual comparison still requires a matched multitask control receiving identical enthalpy labels, and the low-pressure Clausius–Clapeyron relation must remain explicitly approximate.

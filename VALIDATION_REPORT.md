# Validation findings — 16 September 2026

## Decision

**Accept v0.1.0 as a reproducible curation and evaluation-split snapshot. Hold release of enthalpy supervision.** Transcription and known-leakage checks passed. Primary experimental methods, state conventions and correction lineage remain unresolved, so the number of certified independent enthalpy labels is zero. Calling all calorimetry-tagged rows independently measured labels would overstate the evidence.

## Source verification completed

The input archive is `ThermoML.v2020-09-30.tgz`, 189,433,115 bytes, SHA256 `231161b5e443dc1ae0e5da8429d86a88474cb722016e5b790817bb31c58d7ec2`. The source is the [NIST ThermoML/Data Archive](https://data.nist.gov/od/id/mds2-2422). The supplementary enthalpy source is file 250199, `ChickosAcreeCompendiumVaporization.csv`, of [KU Leuven RDR dataset 10.48804/CBHEAB](https://doi.org/10.48804/CBHEAB); the retained metadata identify dataset version 2. Original citations, metadata and the source README are included.

An independent XML parser checked all 16,214 pressure rows from the earlier primary metadata screen and all 1,008 extracted ThermoML enthalpy rows, across 780 source XML studies. It checked the full InChI, property, liquid/crystal phase metadata, measurement-method string, numerical value, temperature variable or constraint, kPa-to-Pa conversion and stored property-value metadata, including available uncertainty entries. **All 17,222 rows matched; none was missing.** The broader enthalpy check includes rows later excluded as sublimation, derived values or outside the frozen join.

All 16,727 extracted compendium rows were matched back to their original CSV lines for identity, method, reference and numerical enthalpy/temperature fields. There were zero mismatches. CSV floating-point values were parsed with round-trip precision, avoiding parser-rounding differences being mistaken for source discrepancies.

This validates transcription from the supplied sources. It does not prove the experiments are correct or independent: the archive's XML and JSON are representations of the same underlying data.

## Identity and pressure decisions

Of 860 molecules passing the earlier pure-compound pressure metadata screen, 703 enter this release. RDKit 2025.09.6 parsed their full InChIs; the review also checked InChI round trips, InChIKeys, disconnected fragments, net charge, radical electrons and possible stereochemistry. The identity join remains **exact full InChI equality**. Neither a molecular name, a fingerprint, nor the first InChIKey block is used to join labels.

The conservative exclusions are 122 identifiers with RDKit flags for unspecified potential stereochemistry and 35 carboxylic acids requiring vapor-association review. These flags are not experimental determinations: the potential-stereo screen includes representation-sensitive cases, such as isocyanates and tautomeric forms, and may exclude molecules that a subsequent chemical review can resolve. Exclusion here is preferable to silently choosing a stereoisomer or tautomer. Neutral charge-separated resonance representations are not excluded solely because individual atoms carry formal charges. Sample identity and purity are not independently certified by graph agreement.

The retained numerical domain is 250–500 K and 1–20,000 Pa, with liquid/gas metadata and the previous measurement-method screen. There are 13,731 pressure rows; removing 231 exact copies leaves 13,500. An exact copy is a repeated `(DOI, full InChI, T, p)` tuple. Different values or different sources are preserved; no averaging was used to manufacture agreement.

Small nonmonotonic steps are flagged in 160 of 1,317 source series. They are not automatically removed: measurement scatter, closely spaced temperatures and rounding can cause such steps. The flags are descriptive and did not determine source selection, molecular assignments or exclusions. No row was rejected for disagreement with a pressure-derived Clausius–Clapeyron estimate.

## Enthalpy decisions and unresolved examples

The complete decision ledger contains 16,964 rows: all 16,727 compendium rows and the 237 ThermoML enthalpy rows sharing an InChI with the earlier 860-molecule pressure candidate set. The full 1,008-row ThermoML extract remains available in `inputs/`.

The in-scope candidate pool contains **736 exact-C compendium rows and 15 liquid/gas ThermoML calorimetry rows**, covering 194 molecules. The [NIST enthalpy-method definitions](https://webbook.nist.gov/chemistry/enthalpy.html) distinguish calorimetric and vapor-pressure-derived methods. A C code is a useful screen, but does not establish the full measurement or correction history of an individual digitized row. Mixed/non-C methods, nonpositive values, unresolved source notes, unresolved identities and out-of-domain temperatures do not enter the primary candidate pool.

For every candidate, the reported enthalpy is paired with its own reported temperature. `Tm (K)` in this compendium is treated as the row's reported enthalpy temperature, **not as a melting point**. Whether it is the actual measurement temperature or a corrected reference temperature remains a source-review question. The derived `Hvap_298` column is retained only in the original inputs, never promoted as a second independent measurement. Auxiliary enthalpy need not coincide exactly with a pressure observation's temperature; 479 candidate rows are outside their molecule's screened pressure-temperature envelope, so their applicable liquid state and correction history particularly require review.

| Example | Evidence retained | Frozen decision |
|---|---|---|
| Ethyl decanoate, [10.1021/je900093h](https://doi.org/10.1021/je900093h) | Compendium: 69.9 kJ/mol at 305 K; ThermoML: 69.9 at 304.79 K. The archived abstract describes calorimetry and separate pressure measurements. | Link as a possible copied measurement with rounded temperature; retain original values and require methods/correction review. |
| Cyclohexyl butanoate, [10.1021/je025634v](https://doi.org/10.1021/je025634v) | Compendium: 60.1 kJ/mol at 298 K; archive: 58.72 at 315.57 K. The archived abstract describes multiple methods and refinement using their comparison. | Do not equate temperatures or average these values. Flag possible dependence through corrections/refinement. |
| (−)-Verbenone, [10.1016/j.jct.2013.01.009](https://doi.org/10.1016/j.jct.2013.01.009) | 58.9 kJ/mol at 298 K in the compendium and 298.15 K in ThermoML. | Link their source lineage; do not count a copied value twice. |
| Decane, [10.1016/j.jct.2019.02.001](https://doi.org/10.1016/j.jct.2019.02.001) | Two calorimetry-tagged blocks give 49.89 and 52.24 kJ/mol at 298.15 K for the same source/sample identifier, with expanded uncertainties of 2.20 and 1.42 kJ/mol. | Quarantine both pending primary-table and calibration/correction lineage. Overlapping uncertainty intervals mean the difference is not itself proof of an erroneous value. |
| 2-Methyl-3-buten-2-ol, [10.1016/j.jct.2015.07.028](https://doi.org/10.1016/j.jct.2015.07.028) | The archived abstract discusses gas-phase association. | Flag the approximation/state issue for source review; do not certify it from a low pressure cutoff alone. |

Seven cross-dataset links are recorded; these establish possible shared measurement lineages, not seven additional experiments or automatic numeric mergers. The full primary methods sections were not obtained and verified in this step. Source examples above rely on the archived abstracts and numerical metadata; they are not full-paper certifications.

ThermoML expanded uncertainties are preserved with their reported 95% confidence metadata. An explicit coverage factor was not supplied for these candidate entries, so none was invented and the expanded values were not relabeled as one-standard-deviation errors. Compendium deviations have unspecified conventions until the underlying table is reviewed. No inverse-uncertainty weighting is authorized by this release.

## Evaluation split verification

Source and structural relationships define indivisible connected components. These include shared full-molecule connectivity, Morgan radius-2 2048-bit similarity of at least 0.7, every retained pressure DOI, each candidate enthalpy reference code, and conservative year/author-code-to-DOI aliases. Ambiguous aliases are used only to keep potentially related sources together; they do not validate bibliographic identity or an enthalpy label.

The 703 molecules form 122 components. The largest has 423 molecules and is entirely in training. A single deterministic size-first allocation with seed 20260916 yields 492/106/105 molecules in training/validation/test. There was no seed search, model fitting or optimization against prediction error. Approximate 70/15/15 allocation concerns molecule counts, not necessarily pressure-row counts.

The independent verification found no overlap in the known molecular/source groups. Maximum cross-split Morgan similarities are 0.642857 for train–validation, 0.642857 for train–test, and 0.666667 for validation–test, all below 0.7. Unknown historical copying or correction lineage is not completely resolved; the result must not be described as a guarantee that every possible experimental dependency has been eliminated.

At the primary 20 kPa cutoff, the test set has 78 eligible episodes, 234 warm anchors and 512 cold-target observations, distributed over **28 atomic components**. Validation has 66 episodes across 24 components. Error bars must resample components, not treat 512 rows as independent experiments. The large training component prevents a convincing claim of balanced five-fold source-independent cross-validation; this release uses one fixed holdout design.

| Pressure cap | Training episodes | Validation episodes | Test episodes |
|---|---:|---:|---:|
| 20 kPa — primary | 292 | 66 | 78 |
| 10 kPa — sensitivity | 259 | 61 | 74 |
| 5 kPa — sensitivity | 234 | 57 | 70 |

These sensitivities retain molecular assignments and the same preselected source series. They reconstruct the warm/cold intervals under each cap, so their populations differ. Any pressure-cap comparison should also report the common set of eligible molecules.

## Scope of the sign-off

The archive was already explored in the join audit, including descriptive pressure/enthalpy comparisons. This is therefore a **retrospective pre-model holdout**, not a prospectively blinded data collection or an external validation cohort. Test labels were not used to tune a predictive model; they must now remain out of model selection. A low pressure cap also does not establish ideal-gas behavior, absence of association, distance from the critical point or correct standard/saturation-state conversion for every molecule.

The remaining gate is primary-source certification of at least 100 independently labeled training molecules. There are 168 training molecules with candidates, 16 in validation and 10 in test; a usable candidate is not a certified label. The 194-entry source queue includes 184 compendium reference codes and 10 archive DOIs; entries can refer to overlapping underlying papers. The review template records page/table evidence, actual/reference temperature, phase/state, all corrections, any pressure data used, duplicate lineage, uncertainty convention and reviewer/date. Prioritize training-source coverage, while using held-out sources only to check provenance or future evaluation labels.

The greedy source-review plan prioritizes previously uncovered training molecules, with lexical reference-code tie breaking. Its first 14 reference entries potentially cover 100 training molecules; 69 entries cover all 168. These are coverage counts, not successful certification counts. Available DOI leads are included separately and remain tentative unless the source reference is verified.

Future certification must not be based on agreement with the pressure curve. A new provenance discovery may require embargoing a source or revising the split with a new version. Preserve v0.1.0 and its hashes; do not silently change the benchmark after model results are available.

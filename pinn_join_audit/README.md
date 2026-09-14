# Pressure–enthalpy feasibility audit

Audit date: 14 September 2026. This package supports the proposed PWAV–ChemBERTa PINN study. It contains an extraction and feasibility audit, not trained models or a finalized benchmark.

**Decision:** the pressure coverage and identifier overlap justify continuing with the proposed research question. Experimental independence, full molecular validation, and enthalpy state/temperature provenance are still to be established before model training. `C_candidate=True` is a screening flag, not certification.

## Reproduce

Keep the original uploaded `ThermoML.v2020-09-30.tgz` unchanged. It is not repeated in this package. The enthalpy CSV is included in `inputs/` with its original source README and metadata.

```bash
python audit_thermoml.py --archive /path/to/ThermoML.v2020-09-30.tgz --enthalpy inputs/ChickosAcreeCompendiumVaporization.csv --out results
python verify_and_diagnose.py --archive /path/to/ThermoML.v2020-09-30.tgz --results results
```

The extraction script requires Python 3.10+ and only the standard library. The second script needs NumPy (audit environment: Python 3.12, NumPy 2.3.5). Both operate locally, without scraping or network requests. The archive is streamed rather than unpacked. Exact input SHA-256 checks prevent accidentally processing a different release. The extraction handles temperature as either a variable or a constraint, using the ThermoML numeric property/variable identifiers.

`build_audit_report.py` optionally regenerates the PDF and figure with NumPy 2.3.5, Matplotlib 3.10.8, and ReportLab 4.4.9. It reads the already-computed results and creates no model results.

## Observed coverage

| Screen | Pressure rows | Full InChI identifiers |
|---|---:|---:|
| All pure-component vapor/sublimation pressure entries | 66,226 | 1,943 |
| Property phase Liquid; block phases Liquid and Gas | 44,515 | 1,455 |
| Also 250–500 K and 1–20,000 Pa | 20,145 | 1,111 |
| Also basic chemical-identity and pressure-method screens | 16,214 | 860 |

The 860 identifiers include 742 with any enthalpy method and 214 with candidate C-method enthalpies. There are 793 candidate C rows across 190 reference-string groups. These are not 793 independent experiments. The same pressure pool contains 15,953 unique (DOI, InChI, T, p) tuples: repeated tuples are flagged, not silently erased.

There are 584 identifiers with at least six temperature levels spanning at least 30 K. Of these, 535 also have at least three warm-end levels and two cold-end levels, where each end covers 30% of that molecule's eligible temperature span. 116 of those 535 have a C-method candidate. Requiring the whole warm/cold protocol to fit within one source series gives 518 identifiers, 102 with C candidates. Temperature levels group sorted unique temperatures into consecutive groups whose maximum minus minimum is at most 0.1 K, represented by their median. This prevents nearly repeated temperatures from supplying artificial anchors. Original observations and temperatures remain unchanged in the data tables.

An explicitly limited acid-name review flag identifies 36 of the 860 identifiers, leaving 824 without that flag, 209 with C candidates, and 101 with both C candidates and a qualifying single-source curve. This flag is not a complete chemical substructure or vapor-association screen. It does not replace examination of molecular graphs, actual phase stability, or critical-region/nonideal-gas effects.

## Exact meanings of the screens

- Join by complete, unchanged Standard InChI equality. Names, CAS guesses, truncated InChIKeys, and stereochemistry-stripped identifiers are not join keys. This is a conservative intersection, not a toolkit-canonicalized identity universe. InChI can itself normalize tautomers, and missing stereochemical information must still be reviewed. No RDKit or equivalent graph validation was run.
- The basic chemical screen requires a single formula component containing carbon, restricted to C/H/B/N/O/F/Si/P/S/Cl/Br/I, with no explicit charge, protonation, or isotope layer. It does not prove closed-shell character or correct source assignments.
- Require `PropPhaseID=Liquid` and exactly Liquid/Gas block phases. Crystal, metastable-liquid, mixed-phase, and mixture endpoints are outside the primary pool. Nineteen records lack temperature metadata, all in crystal phases, and are retained with issues in `extraction_errors.csv`; none entered the primary liquid pool.
- Convert pressure kPa to Pa by multiplying by 1,000. Temperatures stay in K. Enthalpies stay in kJ/mol in these tables; multiply by 1,000 inside a physics residual using R in J/(mol K).
- The method screen retains recognizable static/manometric, ebulliometric, transpiration/gas-saturation, Knudsen/torsion-effusion, isoteniscope and related equilibrium-pressure methods. The explicit regex is in the extraction script. “Calculated from Knudsen effusion weight loss” is retained as a measurement method. Chromatographic correlations, generic “Calculation”, evaporation-rate/thermal-analysis methods, and unrecognized labels are outside this conservative pool. This metadata screen is not a methods-section validation.
- `C_candidate` requires compendium Method exactly `C`, finite positive reported enthalpy, 250–500 K reported temperature, and blank Notes. NIST defines C as calorimetry. Missing or non-C methods are preserved but do not count toward this gate.
- The compendium's `Enthalpy` is the value reported in the compendium, not necessarily an uncorrected instrumental observation. `Tm (K)` is its reported temperature, not a melting point. Some reference-temperature values already incorporate corrections from the original paper. `Hvap_298` is a further derived field and must not be counted as an additional independent label. `T_low`, `T_high`, and `T_mid` are not experimental pressure-curve coverage.
- Of the 793 C candidates, 772 have no usable listed experimental temperature range, 17 have reported T inside that range, and four outside it. These flags neither prove nor disprove direct measurement; recover actual measurement T, correction procedures, saturation/standard-state conventions, and uncertainty from primary papers.

## Files and how to use the join

| File | Meaning |
|---|---|
| `results/pressure_records.csv` | One original pressure-property observation per row, including excluded phases, original numeric metadata, converted Pa, DOI, method and screening flags. Filter `primary_candidate=True` to reproduce the 16,214-row candidate pool. |
| `results/enthalpy_records.csv` | All 16,727 compendium rows, full identifiers, reported/corrected values, method, notes, source references, original row JSON, and flags. |
| `results/thermoml_enthalpy_records.csv` | ThermoML enthalpy observations with liquid/crystal phases and original methods. Do not add these blindly to the compendium: the sources overlap. |
| `results/molecule_audit.csv` | One row per identifier in the pressure candidate pool, with coverage and lists of linked enthalpy record IDs. This is the molecule-level join table. |
| `results/series_audit.csv` | Temperature coverage for individual source/property series. |
| `results/enthalpy_source_audit.csv` | The 190 C-reference groups requiring methods and lineage review. Year/author code matching provides lookup suggestions only; 14 groups have suggestions and some are ambiguous. |
| `source_review_examples.json` | Three concrete source/temperature/duplicate examples, with evidence level and remaining issues. |
| `results/thermoml_provenance.jsonl` | Compound, citation, property, phase, variable, constraint, sample and uncertainty-definition metadata by series. |
| `results/boiling_records_supplement.csv` | Pure-component boiling-at-P entries, converted to (T,p); kept separate from the primary audit. Normal boiling-point values and pure endpoints embedded in mixture tables are not added. |
| `results/xml_verification.json` | Independent comparison of 300 observations in five XML studies with the JSON-derived CSVs; zero mismatches. |
| `results/local_clapeyron_diagnostics.csv` | Descriptive local-slope comparisons, not predictions or independence verification. |
| `results/statistics.json` | Main audit counts and input SHA-256 hashes. |

Do not create a Cartesian pressure×enthalpy table and then treat its rows as independent observations. Keep the two observation tables, linked through the molecular identifier and their own record IDs. Pressure labels supervise p(M,Tp); enthalpy labels supervise H(M,TH), at their respective validated temperatures. Identical temperatures are not needed for multitask supervision. Direct numerical comparisons require an appropriate common temperature/state or a justified correction.

## What was verified; what remains open

The uploaded archive's size and SHA-256 match the NIST release. All 11,923 JSON studies were scanned exactly once, avoiding the duplicate XML representation. An independent XML parser reproduced identity, property, phase, numerical values, and temperature/pressure conversions for 300 records in five selected studies.

For a descriptive physics check, log(p) was fitted against 1/T within one pressure series, using at least six distinct temperatures spanning at least 10 K, all within ±20 K of the reported enthalpy temperature and bracketing it. If multiple series qualified, the most locally sampled one was selected, then the narrowest span and stable series ID. Mean log(p) combines replicate values at identical T for this diagnostic only. H≈−R·slope gives 180 comparisons for 84 identifiers: median absolute relative difference 1.53%, 90th percentile 5.59%. This unweighted, locally constant-enthalpy approximation is descriptive, not an uncertainty-calibrated test, experimental independence proof, or predictive model score. No observations were excluded using this agreement.

The candidate pool is adequate for the next curation stage. It does not establish the proposed gate of at least 100 source-verified independent calorimetric molecules. Full graph/stereo/phase checks, source-lineage and temperature/state audits, independence grouping, and clustered train/validation/test splits remain required. Same DOI can contain distinct measurement methods; different DOI can republish the same measurement. All source-related copies must stay in one fold. Select the final benchmark before comparing model scores.

The largest local-slope discrepancies identify concrete review cases: 1-octanol (pressure DOI 10.1021/je030168a, H reference 1977MAN/SEL) differs by about 40.4%, and butanoic acid (pressure DOI 10.1021/je800888n, H reference 1970KON/WAD) by about 38.0%. The octanol local fit has a 0.0785-log10-unit residual RMSE, so the pressure series and its uncertainty need inspection. The acid is already within the acid-name review group; vapor association and enthalpy state conventions require checking. Neither discrepancy alone establishes a wrong measurement or justifies deleting it.

## Research problem to retain

Can independently measured vaporization enthalpies improve cold-end vapor-pressure extrapolation for organic liquids, and does a Clausius–Clapeyron constraint add predictive value beyond the same auxiliary labels in ordinary multitask learning?

Use log10[p_sat/(1 Pa)] as the primary target and validated ΔHvap(T) as the auxiliary target. Compare matched encoders and information: pressure-only model; multitask model with H but no physics; PINN with the same H; and an Antoine-parameter model also allowed the same H supervision. Include conventional-descriptor-only, PWAV-core, full PWAV, ChemBERTa, and fusion ablations. The independent contribution of PWAV is a separate question from the value of physics.

For the main extrapolation task, hold out molecular clusters with all their property labels, then permit only three warm-end pressure anchors per held-out molecule for adaptation. Tune adaptation using validation molecules. Evaluate cold-end pressure values, with single-source-series analysis to separate temperature extrapolation from source differences. Auxiliary H labels for held-out molecules stay hidden in this main task; a separate explicitly labeled extra-H experiment can assess their value. Grouped cross-validation and molecule-level paired uncertainty estimates are preferable to claiming precision from thousands of correlated rows.

Use u=ln[p/(1 Pa)] and r=(R T² du/dT−H)/Hscale, with H in J/mol. This approximates exact Clapeyron dp/dT=H/[T(vg−vl)] under ideal dilute vapor and negligible liquid volume. The chosen pressure ceiling is a screen, not a proof. Retain 5 and 10 kPa sensitivity analyses. Do not label this the first molecular vapor-pressure PINN: related work, including Clapeyron Neural Networks (2026), already exists.

## Sources and terms

- NIST ThermoML Archive: https://data.nist.gov/od/id/mds2-2422 . Release `ThermoML.v2020-09-30.tgz`, 189,433,115 bytes. Dataset metadata: https://data.nist.gov/rmm/records/mds2-2422 . NIST open license: https://www.nist.gov/open/license . Original archive is supplied separately by the user.
- Leenhouts, Jankelevitch, Raike, Müller, and Vermeire, *Replication Data for: Thermodynamics-informed Graph Neural Networks for Phase Transition Enthalpies*, KU Leuven RDR, DOI https://doi.org/10.48804/CBHEAB, dataset V2. Original vaporization file ID 250199: https://rdr.kuleuven.be/api/access/datafile/250199 . Metadata lists MIT terms. Preserve the original attribution and included source README. Paper: https://doi.org/10.69997/sct.140638 . The underlying data compilation is attributed to Acree and Chickos; see the paper's original compendium references.
- NIST method codes: https://webbook.nist.gov/chemistry/enthalpy.html . C=calorimetry; A is derived from vapor-pressure data. H-type codes can indicate temperature corrections.
- Zaitsau et al. (2003), cyclohexyl esters: https://doi.org/10.1021/je025634v . Zaitsau et al. (2009), ethyl decanoate: https://doi.org/10.1021/je900093h . Stejfa et al. (2013), monoterpenes: https://doi.org/10.1016/j.jct.2013.01.009 . Evidence inspected here includes the original-study abstracts and numeric metadata embedded in the supplied ThermoML archive; the full methods sections were not obtained.
- Pavšek et al. (2026), *Clapeyron Neural Networks for Single-Species Vapor-Liquid Equilibria*: https://arxiv.org/abs/2602.18313 . GRAPPA: https://arxiv.org/abs/2501.08729 . See the earlier research brief for the wider literature review.

Audit scripts may be reused and modified. Source data retain their original attribution and terms. No original journal article PDF is redistributed in this package.

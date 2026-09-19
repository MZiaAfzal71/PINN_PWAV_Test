# Frozen evaluation protocol — v0.1.0

This protocol was fixed before fitting predictive models. It is a retrospective holdout of an already explored experimental archive. Its file hashes and configuration belong to the release; any later change needs a new version and an explicit explanation.

## Question and estimand

The primary question is whether adding a Clausius–Clapeyron residual improves prediction of cold-temperature vapor pressure for previously unseen molecular/source groups, compared with matched multitask learning given exactly the same independently verified enthalpy measurements. A pressure-only comparison separately tests the benefit of extra enthalpy supervision. Neither comparison is currently authorized to use the quarantined candidate labels.

The response is `log10[p_sat/(1 Pa)]`. Temperature is in kelvin. The auxiliary quantity is molar vaporization enthalpy at its verified reported temperature, stored in kJ/mol for readability and converted to J/mol for physics calculations. Standard-state, saturation-state and temperature corrections must be documented before label release.

For a future network using `u(T) = ln[p_sat/(1 Pa)]`, the proposed residual is:

\[
r(T)=\frac{R T^2\,\partial u/\partial T-\Delta H_{\mathrm{vap}}(T)}{H_{\mathrm{scale}}},
\qquad R=8.314462618\ \mathrm{J\,mol^{-1}\,K^{-1}}.
\]

`H_scale` and all learned normalization constants must be determined using training data only. If the network predicts log10 pressure directly, multiply its temperature derivative by `ln(10)` before using this residual. Automatic differentiation must include the chain rule for any normalized temperature input.

This is the ideal/dilute-vapor Clausius–Clapeyron approximation, with negligible liquid molar volume, rather than exact Clapeyron thermodynamics. The 5/10/20 kPa sensitivities assess one aspect of that approximation; they do not establish ideal behavior or exclude association in every substance.

## Molecular and source partition

The frozen universe is the 703 molecules listed in `split_assignments.csv`. Full InChI is the identity key. Same-connectivity InChIKeys, structural fingerprints and source aliases are grouping tools only.

Create connected components using the relations exported in `group_edges.csv`: common connectivity, Morgan radius-2 2048-bit Tanimoto similarity at least 0.7 without chirality, shared eligible pressure DOI, shared candidate calorimetry reference, and conservative possible source aliases. All pressure sources of an included molecule participate, including sources not selected for a scoring episode. Components are never divided across splits.

Components are processed by decreasing size, with SHA256-based seed 20260916 tie ordering. Each is assigned to minimize the sum of squared deviations from molecule fractions 0.70/0.15/0.15. Split ties are resolved in the explicit order training, validation, test. There is one allocation and no seed search. The resulting counts are 492, 106 and 105 molecules.

Training uses all retained deduplicated training pressure rows. The largest component contains 423 training molecules; this release does not prescribe balanced k-fold cross-validation. All test and validation molecular labels, including alternative pressure series and enthalpies, are excluded from global training. Only the designated warm anchors may be used for per-molecule adaptation.

## One source series and three anchors per episode

1. Within a molecule, retain the earlier pure-liquid pressure metadata screen, 250–500 K and 1–20,000 Pa. Identify exact duplicate `(source DOI, full InChI, T, p)` copies using a stable record-ID representative; exclude copies from all fitting/scoring exports. Preserve conflicting numerical observations for audit. Source coverage for the initial selection uses the original series, with the post-removal eligibility check specified in step 4.
2. Group temperatures by sorted greedy bins whose maximum-minus-minimum is at most 0.1 K; use the median of distinct temperatures as each level's representative. Coverage is defined by those representatives, not the number of repeated observations.
3. An eligible source series has at least six levels and at least 30 K total span. Its upper 30% of the temperature span must contain at least three levels, and its lower 30% at least two. These fractions refer to temperature span, not row quantiles.
4. Before fitting, select one source series per molecule: prefer eligible series, then larger temperature span, then more levels, then lexical series ID. This uses coverage and identifiers, not a fitted prediction error, a CC agreement score or a monotonicity criterion. Exact-copy removal is then applied to the chosen series; if its remaining coverage fails, do not switch to another series to rescue the episode.
5. Use the lowest, lower-middle and highest level in the warm region as the three anchors. With an odd number of warm levels, the middle is exact; with an even number, use the lower middle. Within an anchor level choose the row closest to the median temperature, then lexical record ID. Do not average targets to create an anchor.
6. Every retained observation at a level in the cold region is a scoring target. Temperatures between the warm and cold regions, unused warm observations, and alternative source series remain hidden for held-out molecules. They are not extra adaptation data.

`episodes.csv` fixes all anchor/target record IDs. `episode_records.csv` explicitly maps every included record to its episode, role and **cap-specific temperature level**. Use this map for evaluation aggregation; `pressure_observations.csv` also has a general full-series temperature-level ID, which is not a substitute when a cap changes the level grouping. The primary 20 kPa anchor and target exports are provided separately.

At 10 and 5 kPa, retain the same molecular assignments and preselected source series. Apply the new pressure cap, recalculate levels and coverage, and reconstruct anchors/targets with the identical rules. Do not change source series or tune a new split. The episodes present at each cap are frozen, even when a molecule loses eligibility. Report the cap-specific population and a paired common-molecule sensitivity so composition changes are visible.

## Permitted information and adaptation

Global preprocessing, descriptor selection, scaling, representation tuning, enthalpy loss scaling and model parameters are fitted on training molecules only. Deterministic physical descriptors and externally pretrained representations must disclose their provenance. Check benchmark overlap for any externally supervised pretraining before use; this data release does not audit such pretraining.

Use validation molecules to select architecture, physics/data-loss weights, optimizer settings, adaptation parameters and stopping rules. For each validation or test episode, start a fresh copy of the trained model; permit only its three warm pressure anchors and known molecular structure. Do not carry an adapted state from one held-out molecule to another or update a shared model across the test set. All held-out experimental enthalpies remain inaccessible to adaptation, even if they exist at warm temperatures.

Physics collocation may use temperatures and the model's own enthalpy predictions; it must not introduce held-out enthalpy observations or estimates obtained by differentiating the hidden pressure curve. Collocation-domain and phase rules must be chosen using training/validation information and documented before test scoring. Test stopping cannot depend on a cold-target loss or a hidden-label residual. Prediction temperatures themselves are legitimate query inputs.

Any adaptation advantage needs fair controls: report the number of free parameters, anchor updates and optimization budget for every method. If a PINN uses additional test-time physics optimization, report that explicitly and include matched ablations. Choose these implementation details on validation data before opening final test scores; this release fixes data access, not a yet-unbuilt architecture.

## Metrics, statistical unit and failures

The primary population is **all 78 eligible test cold episodes at 20 kPa**, not just molecules with an enthalpy candidate. The primary contrast is PINN minus matched multitask learning with the same certified training labels; a negative error difference favors PINN.

For model prediction error `e_ijr = predicted_log10p - observed_log10p`, let `j` index a cold temperature level, `r` its replicate rows, and `i` a molecule. First average `|e_ijr|` over observations in each level. Then average equally over levels within a molecule. Finally average equally over test molecules. This **macro, temperature-level-balanced MAE in log10 pressure** is the primary metric. It prevents a densely measured series or repeated temperature from dominating the comparison.

Secondary metrics are the analogous per-molecule RMSE (average squared errors within levels and across levels, take the molecule's square root, then macro-average), pooled row MAE, worst-molecule errors, prediction coverage and physical-residual summaries. Residual agreement is not a substitute for experimental prediction accuracy. Report a leave-largest-evaluation-component-out sensitivity without redefining the primary population.

Use the same model seeds `[17, 23, 41, 59, 83]` for every stochastic comparison. Report all seeds and average paired error differences across the five; never select the best seed. Average model error differences within each molecule across seeds before component resampling. Seed variability and data-sampling uncertainty are different quantities and should be shown separately.

Use 10,000 paired bootstrap resamples with seed 20260916. Sample the **28 atomic test components** with replacement and include all their eligible molecules with the sampled component multiplicity. Recompute the molecule-macro difference in every resample and report the 2.5th/97.5th percentiles. Use the same resample for both compared methods. This accounts for the known source/structural grouping but cannot correct unknown historical data dependencies. It is not an IID bootstrap of 512 pressure rows. Report the full paired molecule/component results so the interval can be reproduced.

Prespecify the PINN-vs-multitask contrast as primary. Treat representation ablations, other baselines, caps and additional endpoints as secondary; do not select the most favorable comparison and call it the main result. Do not claim a statistically powered universal advantage from the molecule count alone.

A method must produce a finite prediction for every frozen target. Record convergence failures and coverage. Never silently omit failed molecules and present a primary complete-case score as if it used the frozen population. Repair implementation failures using training/validation evidence, or report the comparison as incomplete. Any test-informed repair must be disclosed and cannot be represented as untouched holdout evaluation.

## Controls required when modeling begins

- Pressure-only learning with the same representation and training pressure data.
- Matched multitask pressure/enthalpy learning with identical certified enthalpy labels and zero CC penalty.
- The corresponding PINN with the CC penalty; all data, representation and other capacity choices matched where possible.
- A transparent pressure-curve baseline using the same three warm anchors; any use of enthalpy must be restricted to the same allowed training information. Report instability of a three-parameter Antoine fit to only three anchors rather than hiding failures.
- PWAV, ChemBERTa and fused-representation ablations if these remain in the eventual manuscript, with identical split IDs and budgets.

The independent-enthalpy comparison remains on hold until the source-review gate is met. Its minimum of 100 certified training molecules is a practical project gate inherited from the feasibility audit, not a guarantee of statistical power. No corrected or pressure-derived enthalpy may be substituted merely to reach it.

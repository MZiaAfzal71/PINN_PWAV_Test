# Closed-source follow-up and Viton–Chavret temperature-window audit

18 September 2026. Parent release: v0.4.0. Original evaluation freeze: v0.1.0.

## Decision

No candidate is added to the strict direct-enthalpy pool. The pool remains **42 labels on 41 training molecules**, leaving the inherited 100-molecule gate **59 molecules short**. Main model fitting remains on hold.

The new scientific result is narrower but important: the shorthand source `1996VIT/CHA` is bibliographically resolved, and its 19 candidate records are classified against the only temperature interval verified from an official source. This prevents clearly out-of-window values from being silently treated as direct calorimetry and prevents plausible in-window values from being promoted without their primary table.

## Source-access follow-up

### Månsson et al. (1977)

The article *Enthalpies of vaporization of some 1-substituted n-alkanes* is identified by DOI `10.1016/0021-9614(77)90202-6`. Publisher metadata and an abstract are discoverable, but the full article was not obtained in this review. Its 13 candidate rows, covering up to 12 currently unapproved training molecules, remain the highest-yield open source item.

No decision about numeric values is made from the abstract or search-result snippets. The methods, full tables, footnotes, uncertainty treatment, temperature adjustments, and any pressure-based correction must be checked first.

### Mathews (1926)

The article *The Accurate Measurement of Heats of Vaporization of Liquids* is identified by DOI `10.1021/ja01414a002`. The article identity is resolved, but the complete primary article was not obtained. All 12 associated candidates remain held.

### Viton, Chavret, and Jose (1996/1998)

The Acree–Chickos reference list maps `1996VIT/CHA` to:

> C. Viton, M. Chavret, and J. Jose, ELDATA: Int. Electron. J. Phys.-Chem. Data 2, 103 (1996).

A publisher page also verifies a 1998 chapter by the same authors, *Enthalpy of Vaporization of N-Alkanes (from Nonane to Pentadecane). Experimental Results - Correlation*, pages 21–32, DOI `10.1007/978-3-642-72207-3_3`.

The official abstract says that calorimetric measurements for C9–C15 n-alkanes were made from 313 to 344 K and compared with literature and equation-of-state predictions. The accessible page is subscription content. The 1996 ELDATA full text was not obtained, and textual/numeric equivalence between the 1996 item and 1998 chapter is **not established**.

Consequently, the later chapter is used only to establish a reported experimental window and related-source identity. It is not substituted for the missing primary numeric table.

## Row-level temperature-window result

The candidate values themselves are unchanged. Classification is inclusive of the stated 313–344 K interval.

| Molecule | Below interval | Inside interval | Above interval |
|---|---|---|---|
| Nonane | 46.7 kJ/mol at 299 K | 46.0 kJ/mol at 314 K | — |
| Decane | 51.5 kJ/mol at 299 K | 50.5 at 314 K; 50.1 at 324 K; 49.2 at 334 K | — |
| Undecane | 56.2 kJ/mol at 299 K | 55.4 at 314 K; 54.5 at 324 K; 54.0 at 334 K; 53.1 at 344 K | — |
| Dodecane | 61.4 kJ/mol at 299 K | 58.1 at 334 K; 57.4 at 344 K | — |
| Tetradecane | — | 69.0 at 324 K; 68.6 at 329 K; 67.9 at 334 K; 66.8 at 344 K | 65.7 kJ/mol at 359 K |

Totals: **14 inside, 4 below, and 1 above**.

### Why the 14 in-window rows are still held

An abstract-level match to the experimental interval is necessary but insufficient. At least five unresolved questions remain:

1. Does each compiled number appear in the primary authors' experimental table, rather than in a literature-comparison or predicted-value column?
2. Are temperatures exact measurement temperatures, rounded means, or reference-temperature reductions?
3. What uncertainty, precision, repeatability, and sample-purity information accompanies each row?
4. Was any saturation-pressure derivative, vapor-pressure correlation, ideal-gas correction, or other ancillary property used to derive the reported enthalpy?
5. Are the 1996 ELDATA and 1998 Springer tables identical, revised, or partially overlapping?

Until those questions are answered from the full document, the 14 rows remain `hold_primary_table_and_method_unverified`.

### Why the five out-of-window rows receive a stronger warning

The four 299 K records and the 359 K record lie outside the official abstract's 313–344 K measurement range. They may be valid values, but the accessible evidence cannot tell whether they are measured, imported from literature, normalized to a reference temperature, interpolated, correlated, or extrapolated. They therefore cannot be described as direct observations from this experiment.

This is a source-role warning, not a claim that the numbers are wrong.

## Leakage and evaluation freeze

No validation or test pressure target informed any source decision. The original evaluation design remains unchanged:

- 492 train, 106 validation, and 105 test molecules;
- 78 primary 20 kPa test episodes;
- 234 warm-adaptation anchors;
- 512 cold pressure targets; and
- 42 strict enthalpy labels, all in train.

The 14 Osborne–Ginnings gamma constraints from v0.4 remain a separate coupled-physics tier and do not count toward the direct-H coverage gate.

## Next acquisition priority

The most valuable next document is the complete Månsson et al. (1977) article because it could resolve up to 12 additional training molecules. The complete 1996 ELDATA paper or 1998 Springer chapter is the best targeted document for resolving the 14 plausible in-window alkane rows and the five out-of-window source roles. The exact acquisition checklist is in `PRIMARY_SOURCE_REQUEST.md`.

The release remains `HOLD_ENTHALPY_PROVENANCE` and no model has been trained.

# Frozen PINN constraint protocol

## Quantity and equation

For each of the 14 Osborne-Ginnings observations at 25 °C, the directly observed calorimetric quantity is `gamma`, the electrical energy added per mass of vapor withdrawn. The source relation is

`gamma = DeltaH_vap + T v_liquid dp_sat/dT`.

The molar constraint frozen for a coupled model is

`gamma_kJ_mol = H_vap_model_kJ_mol + T_K * V_m3_mol * dp_sat_dT_Pa_K / 1000`.

If the pressure head predicts `ln(p_sat / 1 Pa)`, calculate the derivative as

`dp_sat/dT = p_sat * d ln(p_sat / 1 Pa)/dT`.

The residual for row `i` is

`r_gamma,i = H_vap_model(x_i,T_i) + T_i V_i p_i dlnp_i/dT - gamma_i`,

with the pressure term converted from J/mol to kJ/mol. Minimize a predeclared robust aggregate of `r_gamma` only after the direct-H project gate is satisfied or explicitly revised.

## Allowed data flow

- All 14 constraint molecules belong to the frozen training split.
- The pressure value and derivative may come only from training-visible pressure observations or from the model evaluated at the constraint state.
- Frozen validation and test pressure targets, test losses, and target-informed hyperparameter choices are prohibited.
- `gamma` rows must not be concatenated with direct enthalpy labels. They use a separate residual and a separate loss coefficient.
- The 14 published `L = gamma - beta` values may be used together only as a separately reported sensitivity analysis.

## Weighting and uncertainty

The source does not provide a per-row statistical uncertainty for `gamma`. Do not invent Gaussian standard deviations and do not apply inverse-variance weighting. Predeclare a common robust scale or select it using training and validation information without access to test targets. Report the result with and without the entire gamma-constraint tier.

## Temperature metadata

The source measurement is 25 °C on the historical International Temperature Scale. The source arithmetic uses 298.160 K, following the archived API convention. The model coordinate remains the frozen nominal 298.15 K for compatibility. Both values are present in the constraint table; this does not claim an ITS-90 conversion.

## Required comparisons when modeling begins

1. Pressure-only model.
2. Matched multitask model using the unchanged strict direct-H labels but no thermodynamic residual.
3. Coupled PINN using the same labels plus the gamma residual.
4. Prespecified sensitivity run adding all 14 published NIST `L` values as sensitivity-only labels.

Use identical molecular splits and report the frozen 20 kPa cold-target metric. The gamma tier does not increase the count of strict direct-H molecules.

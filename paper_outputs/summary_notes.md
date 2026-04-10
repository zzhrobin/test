# Summary Notes

## Default Case

- `base_blm = 0.0003`
- `theta_min = 0.2`
- `theta_max = 1.0`
- `sci_alpha = 0.5`
- `sci_beta = 0.5`
- `sci_group_weights = {"fixed_barriers": 1.0, "linear_transit": 0.8, "soft_competition": 0.5}`

## Stability Checks

- Theta stability check: `theta_0.3_0.9`
- Group-weight primary stability check: `compressed_weights`
- Group-weight alternate stability check: `transit_heavier`

## Source Files

- Calibration sweep:
  - `BLM_Calibration_real_macos_sweep/blm_calibration_method_comparison.csv`
- Latest sensitivity authority:
  - `BLM_Sensitivity_real_macos_3e4_groupweights/adaptive_blm_sensitivity_report.csv`
  - `BLM_Sensitivity_real_macos_3e4_groupweights/theta_sensitivity_comparison.csv`
  - `BLM_Sensitivity_real_macos_3e4_groupweights/alpha_beta_sensitivity_comparison.csv`
  - `BLM_Sensitivity_real_macos_3e4_groupweights/group_weight_sensitivity_comparison.csv`

## Figure-Ready Exports

- `figure_blm_sweep.csv`
- `figure_theta_sensitivity.csv`
- `figure_group_weight_sensitivity.csv`

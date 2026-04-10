# Methods Support

## Default Parameter Settings

- `base_blm = 3e-4`
- `theta_min = 0.2`
- `theta_max = 1.0`
- `sci_alpha = 0.5`
- `sci_beta = 0.5`
- `sci_group_weights = {fixed_barriers: 1.0, linear_transit: 0.8, soft_competition: 0.5}`

## Robustness / Stability-Check Settings

- Theta:
  - main robustness check: `theta_0.3_0.9`
  - stronger but less moderate case: `theta_0.1_1.0`
- Alpha/beta:
  - tested `(0.3,0.7)`, `(0.5,0.5)`, `(0.7,0.3)`
  - treated as stability evidence because tested settings were solution-invariant
- Group weights:
  - main robustness check: `compressed_weights`
  - optional alternate: `transit_heavier`

## Sensitivity Families Run

- BLM sweep over nonzero `base_blm`
- `theta_min / theta_max` sensitivity at `base_blm = 3e-4`
- `sci_alpha / sci_beta` sensitivity at `base_blm = 3e-4`
- `sci_group_weights` sensitivity at `base_blm = 3e-4`

## Paper-Facing Outputs

- Summary tables under `paper_outputs/`
- Figure-ready CSVs under `paper_outputs/`
- Rendered figure files under `paper_outputs/figures/`
- Writing-support files under `paper_outputs/writing_support/`

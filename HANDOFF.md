# HANDOFF.md

## Project summary
This repository implements a marine spatial planning (MSP) decision-support workflow for Balikpapan Bay. The current paper direction focuses on a **SCI-driven adaptive BLM** to address the problem that a single global BLM is not suitable for both narrow inner-bay waters and open offshore waters.

## Scientific framing
The contribution is **not** a new ecological cumulative-impact model.
The core contribution is an **adaptive boundary penalty mechanism**:
- use `SCI_local` to represent local aggregation resistance,
- convert it into local BLM multipliers,
- apply that multiplier to true shared boundary length,
- compare with fixed BLM in calibration experiments.

## Current method definition

### SCI
`SCI_local = norm(alpha * G_i + beta * H_i)`

Where:
- `G_i` = geometric confinement / restrictedness,
- `H_i` = human-use competition pressure,
- ecological protection/value/biodiversity layers are excluded.

### Adaptive BLM
- `theta_i = theta_min + (1 - SCI_local_i) * (theta_max - theta_min)`
- `theta_ij = (theta_i + theta_j) / 2`
- `B_ij_star = B_ij * theta_ij`
- effective penalty = `base_blm * B_ij_star`

Interpretation:
- high `SCI_local` = crowded / constrained,
- lower local compactness pressure,
- more flexibility in narrow inner-bay areas,
- stronger compactness in open waters.

## Current paper-ready state

- Real macOS + Gurobi calibration succeeds on `msp_state.pkl`.
- A nonzero BLM sweep confirmed `fixed_blm` and `sci_adaptive_blm` no longer collapse to identical outcomes.
- The manuscript-facing default setting set is:
  - `base_blm = 3e-4`
  - `theta_min = 0.2`
  - `theta_max = 1.0`
  - `sci_alpha = 0.5`
  - `sci_beta = 0.5`
  - `sci_group_weights = {fixed_barriers: 1.0, linear_transit: 0.8, soft_competition: 0.5}`

## Stability checks completed

- `theta_min / theta_max` sensitivity at `base_blm = 3e-4`
  - tested: `(0.2,1.0)`, `(0.4,1.0)`, `(0.1,1.0)`, `(0.2,0.8)`, `(0.3,0.9)`
  - adaptive effect stayed present across all tested settings
  - preferred moderate stability check: `(0.3,0.9)`

- `sci_alpha / sci_beta` sensitivity at `base_blm = 3e-4`
  - tested: `(0.3,0.7)`, `(0.5,0.5)`, `(0.7,0.3)`
  - tested range was solution-stable

- `sci_group_weights` sensitivity at `base_blm = 3e-4`
  - tested:
    - baseline `(1.0, 0.8, 0.5)`
    - transit_heavier `(1.0, 1.0, 0.5)`
    - soft_heavier `(1.0, 0.8, 0.8)`
    - fixed_lighter `(0.8, 0.8, 0.5)`
    - compressed_weights `(1.0, 0.9, 0.7)`
  - adaptive-vs-fixed separation stayed stable across all tested weight settings
  - preferred stability checks: `compressed_weights`, optionally `transit_heavier`

## Consolidated outputs

Paper-ready summary tables, figure-ready CSVs, and manuscript-ready figure files are now under `paper_outputs/`:

- `calibration_summary_table.csv`
- `theta_sensitivity_summary_table.csv`
- `alpha_beta_sensitivity_summary_table.csv`
- `group_weight_sensitivity_summary_table.csv`
- `figure_blm_sweep.csv`
- `figure_alpha_beta_sensitivity.csv`
- `figure_theta_sensitivity.csv`
- `figure_group_weight_sensitivity.csv`
- `summary_notes.md`
- `figures/blm_sweep.png`
- `figures/blm_sweep.pdf`
- `figures/theta_sensitivity.png`
- `figures/theta_sensitivity.pdf`
- `figures/group_weight_sensitivity.png`
- `figures/group_weight_sensitivity.pdf`

Writing-support markdown outputs are now under `paper_outputs/writing_support/`:

- `results_summary.md`
- `figure_captions.md`
- `methods_support.md`
- manuscript-friendly markdown tables for calibration and sensitivity summaries

## Immediate next priority

- turn `paper_outputs/`, `paper_outputs/figures/`, and `paper_outputs/writing_support/` into final manuscript section text, table placement, and figure placement,
- keep the current default setting set as the main reported result,
- use `theta_0.3_0.9` and `compressed_weights` as the main robustness checks,
- keep alpha/beta table-only unless a reviewer-facing invariance figure is specifically needed,
- only if paper framing requires it later, consider a very small extreme-case weight check.

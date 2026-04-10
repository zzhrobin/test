1. Files changed

- [paper_outputs/writing_support/results_summary.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/writing_support/results_summary.md)
- [paper_outputs/writing_support/figure_captions.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/writing_support/figure_captions.md)
- [paper_outputs/writing_support/methods_support.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/writing_support/methods_support.md)
- [paper_outputs/writing_support/table_calibration_summary.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/writing_support/table_calibration_summary.md)
- [paper_outputs/writing_support/table_theta_sensitivity.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/writing_support/table_theta_sensitivity.md)
- [paper_outputs/writing_support/table_alpha_beta_sensitivity.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/writing_support/table_alpha_beta_sensitivity.md)
- [paper_outputs/writing_support/table_group_weight_sensitivity.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/writing_support/table_group_weight_sensitivity.md)
- [HANDOFF.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/HANDOFF.md)

2. Exact files generated

Generated under [paper_outputs/writing_support](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/writing_support):

- [results_summary.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/writing_support/results_summary.md)
- [figure_captions.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/writing_support/figure_captions.md)
- [methods_support.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/writing_support/methods_support.md)
- [table_calibration_summary.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/writing_support/table_calibration_summary.md)
- [table_theta_sensitivity.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/writing_support/table_theta_sensitivity.md)
- [table_alpha_beta_sensitivity.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/writing_support/table_alpha_beta_sensitivity.md)
- [table_group_weight_sensitivity.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/writing_support/table_group_weight_sensitivity.md)

3. Writing-support outputs completed

Completed:
- concise results interpretation for:
  - BLM sweep
  - theta sensitivity
  - alpha/beta stability
  - group-weight stability
- draft figure captions for:
  - `blm_sweep`
  - `theta_sensitivity`
  - `group_weight_sensitivity`
- methods-support summary covering:
  - default parameter settings
  - robustness/stability-check settings
  - sensitivity families run
  - paper-facing outputs
- compact manuscript-friendly markdown tables for calibration and all three sensitivity families

4. Whether markdown tables were added

Yes. All four optional markdown tables were added.

To keep them manuscript-friendly, I used compact labels and short tuple notation for group weights instead of dumping long JSON inline.

5. Any assumptions used in interpreting results

- English manuscript-facing prose was assumed.
- The current paper default was treated as:
  - `base_blm = 3e-4`
  - `theta_min = 0.2`
  - `theta_max = 1.0`
  - `sci_alpha = 0.5`
  - `sci_beta = 0.5`
  - baseline `sci_group_weights`
- Robustness framing used:
  - BLM sweep:
    - divergence begins by `1e-5`
    - clearer at `1e-4`
    - paper-useful at `3e-4`
  - theta:
    - main robustness check `theta_0.3_0.9`
    - stronger but less moderate case `theta_0.1_1.0`
  - alpha/beta:
    - treated as stability evidence because the tested settings are solution-invariant
  - group weights:
    - `compressed_weights` as main robustness check
    - `transit_heavier` as optional alternate

6. Remaining issues / risks

- These are support materials, not final manuscript prose; they still need section-specific integration into the paper.
- The markdown tables are concise, but a journal may still require later reformatting into LaTeX/Word table style.
- Figure captions are draft-level and may need venue-specific shortening or expansion.
- `HANDOFF.md` was only lightly updated, as requested.

7. Review summary for external method check

This step was presentation-only and did not:
- rerun optimization
- change scientific logic
- touch GUI

The new `paper_outputs/writing_support/` package now gives you:
- short results text
- draft captions
- methods-facing support text
- compact markdown tables

So the project now has a full chain from solved experiments to manuscript-facing tables, figure files, and writing support without altering the validated method.

8 个文件已更改
+110
-1



HANDOFF.md
- `figures/group_weight_sensitivity.png`
- `figures/group_weight_sensitivity.pdf`

Writing-support markdown outputs are now under `paper_outputs/writing_support/`:

- `results_summary.md`
- `figure_captions.md`
- `methods_support.md`
- manuscript-friendly markdown tables for calibration and sensitivity summaries

## Immediate next priority

- turn the `paper_outputs/` CSVs and `paper_outputs/figures/` outputs into final manuscript placement-ready assets,
- turn `paper_outputs/`, `paper_outputs/figures/`, and `paper_outputs/writing_support/` into final manuscript section text, table placement, and figure placement,
- keep the current default setting set as the main reported result,
- use `theta_0.3_0.9` and `compressed_weights` as the main robustness checks,
- keep alpha/beta table-only unless a reviewer-facing invariance figure is specifically needed,
paper_outputs/writing_support/figure_captions.md
# Figure Caption Drafts

## blm_sweep

Effect of increasing `base_blm` on the difference between SCI-adaptive BLM and fixed BLM. The x-axis is shown on a log scale. Divergence between the two methods begins at low nonzero BLM values, becomes clearer at `1e-4`, and is readily interpretable at the recommended default `3e-4`, which is highlighted as the manuscript default. Panels summarize adaptive-minus-fixed objective difference, changed cells, and patch difference.

## theta_sensitivity

Sensitivity of SCI-adaptive BLM to the local multiplier range defined by `theta_min` and `theta_max`, evaluated against a reused fixed-BLM baseline at `base_blm = 3e-4`. The default setting `theta_0.2_1.0` and the preferred robustness check `theta_0.3_0.9` yield closely aligned conclusions, while `theta_0.1_1.0` shows a stronger but less moderate adaptive response.

## group_weight_sensitivity

Sensitivity of SCI-adaptive BLM to reasonable reweighting of human-use pressure groups, evaluated against a reused fixed-BLM baseline at `base_blm = 3e-4`. The baseline and `compressed_weights` settings are highlighted to emphasize robustness rather than contrast. Across tested settings, the adaptive-vs-fixed separation remains stable, indicating that the reported effect is not fragile to moderate reweighting of fixed-barrier, transit, and soft-competition pressures.
paper_outputs/writing_support/methods_support.md
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
paper_outputs/writing_support/results_summary.md
# Results Summary

## BLM Sweep

The nonzero-BLM sweep shows that SCI-adaptive BLM no longer collapses to the same solution as fixed BLM. Divergence begins at `1e-5`, becomes clearer at `1e-4`, and is paper-useful at `3e-4`. At the recommended default `base_blm = 3e-4`, the adaptive method improves the objective relative to fixed BLM while increasing shared compactness pressure in a controlled way, with a modest but real shift in solved allocation.

## Theta Sensitivity

The adaptive effect remains present across all tested `theta_min / theta_max` settings at `base_blm = 3e-4`. The default case `(0.2, 1.0)` and the moderate robustness check `(0.3, 0.9)` give closely aligned conclusions, supporting parameter stability. The setting `(0.1, 1.0)` produces a stronger adaptive response, but it is better interpreted as an upper-strength sensitivity case than as the preferred manuscript default.

## Alpha/Beta Stability

The tested `alpha / beta` settings `(0.3, 0.7)`, `(0.5, 0.5)`, and `(0.7, 0.3)` produced the same solved outcome in the current experiment range. This supports the interpretation that the adaptive-vs-fixed separation at `base_blm = 3e-4` is stable to reasonable shifts between geometry and human-use weighting, rather than being driven by a narrow balance point.

## Group-Weight Stability

The tested `sci_group_weights` settings all preserved the same adaptive-vs-fixed separation pattern. Objective differences varied only slightly, while boundary difference, patch difference, overlap, and changed-cell counts remained unchanged across the tested range. This supports using the baseline group weights as the default manuscript setting, with `compressed_weights` as the main robustness check and `transit_heavier` as an optional alternate check.
paper_outputs/writing_support/table_alpha_beta_sensitivity.md
# Table: Alpha/Beta Sensitivity

| setting | alpha | beta | obj diff | boundary diff | patch diff | different cells | note |
|---|---:|---:|---:|---:|---:|---:|---|
| alpha_0.3_beta_0.7 | 0.3 | 0.7 | -0.57 | 1750 | 2 | 4 | stable |
| alpha_0.5_beta_0.5 | 0.5 | 0.5 | -0.57 | 1750 | 2 | 4 | default |
| alpha_0.7_beta_0.3 | 0.7 | 0.3 | -0.57 | 1750 | 2 | 4 | stable |

All tested settings were solution-invariant in this experiment range.
paper_outputs/writing_support/table_calibration_summary.md
# Table: Calibration Summary

| base_blm | obj diff (adaptive-fixed) | boundary diff | patch diff | different cells | note |
|---|---:|---:|---:|---:|---|
| 1e-6 | 0.00 | 0 | 0 | 0 | effectively identical |
| 1e-5 | -0.02 | 500 | 1 | 2 | divergence begins |
| 1e-4 | -0.19 | 500 | 1 | 3 | clearer separation |
| 3e-4 | -0.57 | 1750 | 2 | 4 | manuscript default |
| 1e-3 | -1.78 | 1500 | 3 | 9 | strongest tested separation |
paper_outputs/writing_support/table_group_weight_sensitivity.md
# Table: Group-Weight Sensitivity

| setting | weights | obj diff | boundary diff | patch diff | different cells | note |
|---|---|---:|---:|---:|---:|---|
| baseline | `(1.0, 0.8, 0.5)` | -0.57 | 1750 | 2 | 4 | default |
| transit_heavier | `(1.0, 1.0, 0.5)` | -0.56 | 1750 | 2 | 4 | alternate robustness check |
| soft_heavier | `(1.0, 0.8, 0.8)` | -0.58 | 1750 | 2 | 4 | stable |
| fixed_lighter | `(0.8, 0.8, 0.5)` | -0.57 | 1750 | 2 | 4 | stable |
| compressed_weights | `(1.0, 0.9, 0.7)` | -0.57 | 1750 | 2 | 4 | preferred robustness check |
paper_outputs/writing_support/table_theta_sensitivity.md
# Table: Theta Sensitivity

| setting | theta_min | theta_max | obj diff | boundary diff | patch diff | different cells | note |
|---|---:|---:|---:|---:|---:|---:|---|
| theta_0.2_1.0 | 0.2 | 1.0 | -0.57 | 1750 | 2 | 4 | default |
| theta_0.4_1.0 | 0.4 | 1.0 | -0.42 | 750 | 1 | 4 | weaker spread |
| theta_0.1_1.0 | 0.1 | 1.0 | -0.64 | 2000 | 3 | 6 | stronger, less moderate |
| theta_0.2_0.8 | 0.2 | 0.8 | -0.60 | 1750 | 2 | 4 | compressed upper range |
| theta_0.3_0.9 | 0.3 | 0.9 | -0.51 | 1750 | 2 | 4 | preferred robustness check |

# Figure Caption Drafts

## blm_sweep

Effect of increasing `base_blm` on the difference between SCI-adaptive BLM and fixed BLM. The x-axis is shown on a log scale. Divergence between the two methods begins at low nonzero BLM values, becomes clearer at `1e-4`, and is readily interpretable at the recommended default `3e-4`, which is highlighted as the manuscript default. Panels summarize adaptive-minus-fixed objective difference, changed cells, and patch difference.

## theta_sensitivity

Sensitivity of SCI-adaptive BLM to the local multiplier range defined by `theta_min` and `theta_max`, evaluated against a reused fixed-BLM baseline at `base_blm = 3e-4`. The default setting `theta_0.2_1.0` and the preferred robustness check `theta_0.3_0.9` yield closely aligned conclusions, while `theta_0.1_1.0` shows a stronger but less moderate adaptive response.

## group_weight_sensitivity

Sensitivity of SCI-adaptive BLM to reasonable reweighting of human-use pressure groups, evaluated against a reused fixed-BLM baseline at `base_blm = 3e-4`. The baseline and `compressed_weights` settings are highlighted to emphasize robustness rather than contrast. Across tested settings, the adaptive-vs-fixed separation remains stable, indicating that the reported effect is not fragile to moderate reweighting of fixed-barrier, transit, and soft-competition pressures.

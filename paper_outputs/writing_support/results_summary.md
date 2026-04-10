# Results Summary

## BLM Sweep

The nonzero-BLM sweep shows that SCI-adaptive BLM no longer collapses to the same solution as fixed BLM. Divergence begins at `1e-5`, becomes clearer at `1e-4`, and is paper-useful at `3e-4`. At the recommended default `base_blm = 3e-4`, the adaptive method improves the objective relative to fixed BLM while increasing shared compactness pressure in a controlled way, with a modest but real shift in solved allocation.

## Theta Sensitivity

The adaptive effect remains present across all tested `theta_min / theta_max` settings at `base_blm = 3e-4`. The default case `(0.2, 1.0)` and the moderate robustness check `(0.3, 0.9)` give closely aligned conclusions, supporting parameter stability. The setting `(0.1, 1.0)` produces a stronger adaptive response, but it is better interpreted as an upper-strength sensitivity case than as the preferred manuscript default.

## Alpha/Beta Stability

The tested `alpha / beta` settings `(0.3, 0.7)`, `(0.5, 0.5)`, and `(0.7, 0.3)` produced the same solved outcome in the current experiment range. This supports the interpretation that the adaptive-vs-fixed separation at `base_blm = 3e-4` is stable to reasonable shifts between geometry and human-use weighting, rather than being driven by a narrow balance point.

## Group-Weight Stability

The tested `sci_group_weights` settings all preserved the same adaptive-vs-fixed separation pattern. Objective differences varied only slightly, while boundary difference, patch difference, overlap, and changed-cell counts remained unchanged across the tested range. This supports using the baseline group weights as the default manuscript setting, with `compressed_weights` as the main robustness check and `transit_heavier` as an optional alternate check.

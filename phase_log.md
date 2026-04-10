1. Commands run

`python run_blm_calibration_methods.py --pkl msp_state.pkl --output-dir BLM_Calibration_real_macos_sweep --blm-values 1e-6,1e-5,1e-4,3e-4,1e-3 --scenario-name BLM_Calibration_macOS_sweep`

`python - <<'PY' ... read BLM_Calibration_real_macos_sweep/blm_calibration_method_comparison.csv, load each fixed/adaptive GPKG pair, compute objective/boundary/patch diffs and changed-cell counts ... PY`

2. base_blm values tested

`1e-6, 1e-5, 1e-4, 3e-4, 1e-3`

3. Solve status summary

All 10 runs solved successfully on macOS with real Gurobi.

Per pair:
- `1e-6`: fixed `solved`, adaptive `solved`
- `1e-5`: fixed `solved`, adaptive `solved`
- `1e-4`: fixed `solved`, adaptive `solved`
- `3e-4`: fixed `solved`, adaptive `solved`
- `1e-3`: fixed `solved`, adaptive `solved`

4. Compact comparison table

`objective_diff` = `adaptive - fixed`  
`boundary_diff` = `adaptive - fixed`  
`patch_diff` = `adaptive - fixed`  
`baseline_overlap_share` below is the adaptive row’s overlap against the sweep baseline used by the workflow.

| base_blm | fixed_status | adaptive_status | objective_diff | boundary_diff | patch_diff | baseline_overlap_share | different_cells |
|---|---|---:|---:|---:|---:|---:|---:|
| `1e-6` | solved | solved | `0.00` | `0.0` | `0` | `1.000000` | `0` |
| `1e-5` | solved | solved | `-0.02` | `500.0` | `1` | `1.000000` | `2` |
| `1e-4` | solved | solved | `-0.19` | `500.0` | `1` | `0.999915` | `3` |
| `3e-4` | solved | solved | `-0.57` | `1750.0` | `2` | `0.999787` | `4` |
| `1e-3` | solved | solved | `-1.78` | `1500.0` | `3` | `0.999488` | `9` |

5. Which base_blm values show the clearest divergence

`1e-3` shows the clearest divergence in this sweep. It has the largest objective gap, the largest patch-count gap, and the most changed cells.

`3e-4` also looks paper-useful. It already gives a visible separation while staying closer to the current `1e-4` neighborhood.

`1e-4` is enough to confirm divergence, but the gap is still small.

6. Any anomalies or failures

No solve failures occurred.

At `1e-6`, the two methods are effectively identical in solved outcome.

The `baseline_overlap_share` metric is workflow-relative, not direct fixed-vs-adaptive overlap. It is measured against the sweep’s baseline solution convention from the calibration script, so the direct `different_cells` count is the cleaner method-comparison signal.

Runtime was reasonable, so I did not trim the requested BLM set and made no further code changes.

7. Review summary for external method check

This step used the same real [msp_state.pkl](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/msp_state.pkl) and the same calibration workflow, with no broad refactor.

The sweep supports a method-consistent external summary:
- very small nonzero BLM (`1e-6`) is too weak to separate fixed and SCI-adaptive BLM,
- divergence appears at `1e-5`,
- becomes clearer at `1e-4`,
- and is strongest in this tested range at `3e-4` to `1e-3`.

If you want a paper-facing recommendation from this sweep alone, `3e-4` and `1e-3` are the clearest comparison candidates, with `1e-4` retained as a lower-strength reference point near the original calibration level.

1. Files inspected

- [AGENTS.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/AGENTS.md)
- [HANDOFF.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/HANDOFF.md)
- [run_blm_calibration_methods.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/run_blm_calibration_methods.py)
- [run_sensitivity_paper.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/run_sensitivity_paper.py)
- [core/method_params.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/core/method_params.py)
- [core/adaptive_boundary.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/core/adaptive_boundary.py)
- [core/kde_engine.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/core/kde_engine.py)
- [core/scenario_engine.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/core/scenario_engine.py)
- [tests/test_adaptive_boundary.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/tests/test_adaptive_boundary.py)
- [tests/test_scenario_engine_adaptive_boundary.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/tests/test_scenario_engine_adaptive_boundary.py)
- [tests/test_kde_engine.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/tests/test_kde_engine.py)
- [run_blm_pareto.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/run_blm_pareto.py)
- [run_batch_experiments.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/run_batch_experiments.py)

2. Current calibration logic found

- The current paper-relevant workflow is already centered in [run_blm_calibration_methods.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/run_blm_calibration_methods.py).
- It currently sweeps `base_blm`, runs both `fixed_blm` and `sci_adaptive_blm`, and exports:
  - `objective_value`
  - `total_boundary_length`
  - `patch_count_8_neighbor`
  - `largest_patch_share_8_neighbor`
  - `target_achievement`
  - `baseline_overlap_share`
  - solution files for direct comparison
- The calibration script now already handles missing SCI columns by recomputing `SCI_geometry`, `SCI_human_use`, `SCI_local`, and `SCI` from `confirmed_mapping` and centralized params before solving.
- `fixed_blm` vs `sci_adaptive_blm` is switched only through method flags plus shared `base_blm`; this is exactly the right comparison frame for the next phase.
- `theta_min` and `theta_max` are consumed in [core/scenario_engine.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/core/scenario_engine.py) only in the adaptive boundary weighting path.
- `sci_alpha` and `sci_beta` are consumed in [core/kde_engine.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/core/kde_engine.py) when constructing `SCI_local`, and then feed the same adaptive chain.
- [run_sensitivity_paper.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/run_sensitivity_paper.py) is older and UI/plot oriented; it is not the right base for these paper-method stability experiments.

3. Planned theta sensitivity design

- Keep `base_blm = 3e-4` fixed for all runs.
- Keep `fixed_blm` as the unchanged baseline comparator in every run.
- For each theta setting, run:
  - one `fixed_blm` solve at `base_blm = 3e-4`
  - one `sci_adaptive_blm` solve at `base_blm = 3e-4` with that theta pair
- Narrow theta grid:
  - baseline: `(theta_min=0.2, theta_max=1.0)`
  - weaker spread: `(0.4, 1.0)`
  - stronger spread: `(0.1, 1.0)`
  - compressed upper/lower range: `(0.2, 0.8)`
  - moderate interior range: `(0.3, 0.9)`
- This keeps the method intact while testing whether adaptive effects persist when the multiplier range is tightened or widened.
- Interpretation target:
  - if adaptive-vs-fixed differences remain directionally similar across these settings, the effect is stable;
  - if only extreme theta ranges create divergence, stability is weaker.

4. Planned alpha/beta sensitivity design

- Keep `base_blm = 3e-4` fixed.
- Keep theta at the validated default baseline:
  - `theta_min=0.2`
  - `theta_max=1.0`
- Keep `fixed_blm` as the unchanged comparator for every tested alpha/beta combination.
- Narrow alpha/beta grid around the default `0.5 / 0.5`:
  - `(0.3, 0.7)` human-use heavier
  - `(0.5, 0.5)` baseline
  - `(0.7, 0.3)` geometry heavier
- Optional extension only if runtime is still comfortable:
  - `(0.2, 0.8)`
  - `(0.8, 0.2)`
- This directly tests whether the adaptive effect depends too strongly on geometry-vs-human weighting while preserving the SCI formula and exclusions.

5. Metrics to compare

Use the current workflow’s existing minimal metrics and one direct solution-difference metric:

- `objective_value`
- `total_boundary_length`
- `patch_count_8_neighbor`
- `largest_patch_share_8_neighbor`
- `target_achievement`
- `baseline_overlap_share`
- direct fixed-vs-adaptive `different_cells` count from exported solutions, if feasible in the runner/report step

For reporting, I’d summarize each parameter setting as:
- fixed status / adaptive status
- adaptive minus fixed:
  - objective difference
  - boundary length difference
  - patch count difference
  - largest patch share difference
- `baseline_overlap_share`
- `different_cells`

6. What will remain unchanged

- Real workspace: [msp_state.pkl](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/msp_state.pkl)
- Comparison frame: `fixed_blm` vs `sci_adaptive_blm`
- `base_blm = 3e-4`
- SCI scientific definition
- ecological exclusions from `SCI_local`
- adaptive BLM chain
- true shared-boundary `B_ij`
- centralized defaults in [core/method_params.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/core/method_params.py)
- no GUI changes
- no zoned BLM expansion

7. Risks / assumptions

- The current calibration script does not yet expose a parameter-grid CLI for theta or alpha/beta, so Phase 2 will likely need a small, narrow experiment wrapper or a modest extension to the calibration runner.
- To keep comparisons fair, the fixed baseline should ideally be solved once per experiment family and reused, since changing adaptive-only parameters does not alter `fixed_blm`.
- `baseline_overlap_share` in the current CSV is workflow-relative rather than pure fixed-vs-adaptive overlap, so for paper clarity the direct `different_cells` count is the better comparison signal.
- I’m assuming the default geometry window and human-use smoothing stay fixed during these stability tests; otherwise the experiment space expands too quickly.
- Runtime should be manageable for these narrow grids on macOS/Gurobi, but a larger alpha/beta grid would multiply solve count quickly.

1. Files changed

- [run_adaptive_blm_sensitivity.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/run_adaptive_blm_sensitivity.py)
- [HANDOFF.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/HANDOFF.md)

2. Exact functions/scripts added or modified

Added new script [run_adaptive_blm_sensitivity.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/run_adaptive_blm_sensitivity.py) with:

- `compare_zoning_solutions(...)`
- `save_solution(...)`
- `load_prepared_state(...)`
- `run_fixed_baseline(...)`
- `run_adaptive_family(...)`
- `build_comparison_table(...)`
- `run_sensitivity_workflow(...)`
- `parse_args()`
- `main()`

Updated [HANDOFF.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/HANDOFF.md) concisely with:
- what sensitivity experiments were run
- which settings look most paper-useful
- the next recommended step

3. Theta sensitivity runs completed

At `base_blm = 3e-4`, with one reused fixed baseline for the `theta_sensitivity` family:

- `fixed_blm` baseline: solved once
- `theta_0.2_1.0`: solved
- `theta_0.4_1.0`: solved
- `theta_0.1_1.0`: solved
- `theta_0.2_0.8`: solved
- `theta_0.3_0.9`: solved

4. Alpha/beta sensitivity runs completed

At `base_blm = 3e-4`, with one reused fixed baseline for the `alpha_beta_sensitivity` family:

- `fixed_blm` baseline: solved once
- `alpha_0.3_beta_0.7`: solved
- `alpha_0.5_beta_0.5`: solved
- `alpha_0.7_beta_0.3`: solved

5. Compact comparison tables

Theta sensitivity, adaptive relative to the reused fixed baseline:

| setting | status | objective diff | boundary diff | patch diff | largest patch share diff | overlap share | different cells |
|---|---|---:|---:|---:|---:|---:|---:|
| `theta_0.2_1.0` | solved | `-0.57` | `+1750.0` | `+2` | `0.0` | `0.999829` | `4` |
| `theta_0.4_1.0` | solved | `-0.42` | `+750.0` | `+1` | `0.0` | `0.999829` | `4` |
| `theta_0.1_1.0` | solved | `-0.64` | `+2000.0` | `+3` | `0.0` | `0.999744` | `6` |
| `theta_0.2_0.8` | solved | `-0.60` | `+1750.0` | `+2` | `0.0` | `0.999829` | `4` |
| `theta_0.3_0.9` | solved | `-0.51` | `+1750.0` | `+2` | `0.0` | `0.999829` | `4` |

Alpha/beta sensitivity, adaptive relative to the reused fixed baseline:

| setting | status | objective diff | boundary diff | patch diff | largest patch share diff | overlap share | different cells |
|---|---|---:|---:|---:|---:|---:|---:|
| `alpha_0.3_beta_0.7` | solved | `-0.57` | `+1750.0` | `+2` | `0.0` | `0.999829` | `4` |
| `alpha_0.5_beta_0.5` | solved | `-0.57` | `+1750.0` | `+2` | `0.0` | `0.999829` | `4` |
| `alpha_0.7_beta_0.3` | solved | `-0.57` | `+1750.0` | `+2` | `0.0` | `0.999829` | `4` |

Outputs are saved under [BLM_Sensitivity_real_macos_3e4](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/BLM_Sensitivity_real_macos_3e4).

6. Which settings show the most stable adaptive effect

Most stable theta settings in this run:
- `theta_0.2_1.0`
- `theta_0.2_0.8`
- `theta_0.3_0.9`

They all preserve the same qualitative adaptive effect and nearly the same quantitative separation from `fixed_blm`.

Strongest theta separation:
- `theta_0.1_1.0`

It gives the largest objective gap, boundary gap, patch gap, and changed-cell count, but it is also the most aggressive setting.

Most stable alpha/beta result:
- all three tested settings were effectively identical in solved outcome at `base_blm = 3e-4`

That makes `alpha=0.5, beta=0.5` a clean default to keep, with nearby settings acting as stability evidence.

7. Any anomalies or failures

No solve failures occurred.

The main notable result is that the tested alpha/beta range produced the same solved outcome across all three settings. That is not a failure; it is a useful stability finding.

`largest_patch_share_8_neighbor` did not move across the tested settings even when patch count and changed-cell count did move.

I also validated the new runner with:
- `python -m py_compile`
- targeted `unittest` runs

8. Review summary for external method check

This was kept narrow and method-consistent.

What changed:
- a dedicated sensitivity runner was added that reuses the existing calibration workflow
- each experiment family solves `fixed_blm` once and reuses it as the comparator
- `HANDOFF.md` was updated with concise experiment status and next-step guidance

What did not change:
- SCI scientific definition
- ecological exclusions from `SCI_local`
- adaptive BLM chain
- true shared-boundary `B_ij`
- GUI
- zoned BLM scope

Method takeaway:
- at `base_blm = 3e-4`, the adaptive effect is stable across reasonable theta settings, with moderate variation in strength
- at the same BLM level, the adaptive effect is robust to the tested alpha/beta changes
- for paper use, `base_blm = 3e-4`, `(theta_min, theta_max) = (0.2, 1.0)`, and `(alpha, beta) = (0.5, 0.5)` look like the clean default, with `(0.3, 0.9)` as a good theta stability check

2 个文件已更改
+422
-12



HANDOFF.md
### 4. Export note
GeoPackage export failed in one workflow and was downgraded to GeoJSON fallback. This is acceptable for debugging but should be revisited if paper deliverables require GPKG.

## Latest macOS calibration status

- Real macOS + Gurobi calibration now succeeds on `msp_state.pkl`.
- A nonzero BLM sweep confirmed `fixed_blm` and `sci_adaptive_blm` no longer collapse to identical outcomes.
- Around the currently useful comparison range:
  - `1e-4` shows small but real divergence,
  - `3e-4` shows clearer divergence with moderate solve separation,
  - `1e-3` shows the strongest divergence in the tested range.

## Latest sensitivity experiments

At `base_blm = 3e-4`, two adaptive-BLM stability families were run against a reused `fixed_blm` baseline per family:

1. `theta_min / theta_max` sensitivity
   - tested: `(0.2,1.0)`, `(0.4,1.0)`, `(0.1,1.0)`, `(0.2,0.8)`, `(0.3,0.9)`
   - all runs solved
   - adaptive effect remained present across all tested theta settings
   - strongest separation in this family: `theta_min=0.1, theta_max=1.0`
   - stable, paper-useful moderate settings: `(0.2,1.0)`, `(0.2,0.8)`, `(0.3,0.9)`

2. `sci_alpha / sci_beta` sensitivity
   - tested: `(0.3,0.7)`, `(0.5,0.5)`, `(0.7,0.3)`
   - all runs solved
   - all three tested settings produced the same solved outcome at this BLM level
   - this suggests the adaptive result is stable to reasonable geometry-vs-human weighting changes in the tested range

## Immediate next priority
On macOS (with working Gurobi), prioritize:
Paper-oriented next step:

1. verify optimizer adjacency fallback when `libpysal` is unavailable,
2. rerun a small real-data trial and confirm that fixed vs SCI-adaptive BLM can actually diverge,
3. once divergence is confirmed, run broader `base_blm` calibration,
4. then proceed to sensitivity analysis for:
   - `theta_min/theta_max`
   - `sci_alpha/sci_beta`
   - group weights
1. use `base_blm = 3e-4` as the primary comparison level,
2. keep `(theta_min, theta_max) = (0.2,1.0)` as the default adaptive setting and optionally report `(0.3,0.9)` as a stability check,
3. keep `(sci_alpha, sci_beta) = (0.5,0.5)` as the default since nearby tested values were solution-invariant,
4. next sensitivity extension: test `sci_group_weights` (still without expanding to zoned BLM).

## Suggested next Codex task
A good next task is:
- inspect optimizer-edge construction in `scenario_engine.py`,
- ensure fallback Queen adjacency is built without `libpysal`,
- rerun the small calibration trial,
- report whether fixed vs SCI-adaptive BLM now produce different metrics.
- run a narrow `sci_group_weights` sensitivity at `base_blm = 3e-4`,
- confirm whether the adaptive-vs-fixed separation remains stable under reasonable human-use group reweighting,
- then consolidate the paper-ready calibration/sensitivity tables.

## Important files to inspect first
- `core/method_params.py`
run_adaptive_blm_sensitivity.py
"""Parameter-stability experiments for SCI-adaptive BLM.

This script reuses the real calibration workflow on ``msp_state.pkl`` while
avoiding repeated fixed-baseline solves inside each experiment family.
"""

from __future__ import annotations

import argparse
import json
import os
import pickle
from datetime import datetime
from typing import Any

import pandas as pd

from core.cost_engine import DEFAULT_CONFLICT_MATRIX_10
from core.kde_engine import calculate_dual_sci
from run_blm_calibration_methods import (
    DEFAULT_ZONE_TARGETS,
    compute_solution_metrics,
    ensure_calibration_sci_columns,
    run_method_once,
)

BASE_BLM = 3e-4
DEFAULT_THETA_SETTINGS = [
    {"label": "theta_0.2_1.0", "theta_min": 0.2, "theta_max": 1.0},
    {"label": "theta_0.4_1.0", "theta_min": 0.4, "theta_max": 1.0},
    {"label": "theta_0.1_1.0", "theta_min": 0.1, "theta_max": 1.0},
    {"label": "theta_0.2_0.8", "theta_min": 0.2, "theta_max": 0.8},
    {"label": "theta_0.3_0.9", "theta_min": 0.3, "theta_max": 0.9},
]
DEFAULT_ALPHA_BETA_SETTINGS = [
    {"label": "alpha_0.3_beta_0.7", "sci_alpha": 0.3, "sci_beta": 0.7},
    {"label": "alpha_0.5_beta_0.5", "sci_alpha": 0.5, "sci_beta": 0.5},
    {"label": "alpha_0.7_beta_0.3", "sci_alpha": 0.7, "sci_beta": 0.3},
]


def compare_zoning_solutions(fixed_gdf, adaptive_gdf, zoning_col: str = "Scenario_Zoning") -> dict[str, float]:
    fixed = fixed_gdf[zoning_col].astype(str).reset_index(drop=True)
    adaptive = adaptive_gdf[zoning_col].astype(str).reset_index(drop=True)
    same = fixed == adaptive
    return {
        "different_cells": int((~same).sum()),
        "fixed_adaptive_overlap_share": float(same.mean()),
    }


def save_solution(result_gdf, out_path: str) -> tuple[str, str | None, str | None]:
    try:
        if os.path.exists(out_path):
            os.remove(out_path)
        result_gdf.to_file(out_path, driver="GPKG")
        return out_path, None, None
    except Exception as export_exc:
        fallback_path = os.path.splitext(out_path)[0] + ".geojson"
        try:
            if os.path.exists(fallback_path):
                os.remove(fallback_path)
            result_gdf.to_file(fallback_path, driver="GeoJSON")
            return (
                fallback_path,
                f"GPKG export failed; wrote GeoJSON fallback: {export_exc}",
                None,
            )
        except Exception as fallback_exc:
            return (
                "",
                None,
                f"GPKG export failed: {export_exc}; GeoJSON fallback failed: {fallback_exc}",
            )


def load_prepared_state(pkl_path: str):
    with open(pkl_path, "rb") as file:
        state = pickle.load(file)

    grid_gdf = state["final_grid"]
    confirmed_mapping = state.get("confirmed_mapping", {})
    global_params = state.get("global_params") or {}
    custom_matrix = state.get("custom_matrix") or DEFAULT_CONFLICT_MATRIX_10
    zone_targets = DEFAULT_ZONE_TARGETS
    prepared_grid = ensure_calibration_sci_columns(
        grid_gdf,
        confirmed_mapping=confirmed_mapping,
        global_params=global_params,
    )
    return prepared_grid, confirmed_mapping, global_params, custom_matrix, zone_targets


def run_fixed_baseline(
    *,
    grid_gdf,
    scenario_name: str,
    confirmed_mapping: dict,
    zone_targets: dict,
    global_params: dict,
    custom_matrix: dict,
    base_blm: float,
    output_dir: str,
    family: str,
):
    result_gdf, report, params = run_method_once(
        grid_gdf=grid_gdf,
        scenario_name=scenario_name,
        confirmed_mapping=confirmed_mapping,
        zone_targets=zone_targets,
        global_params=global_params,
        custom_matrix=custom_matrix,
        method_name="fixed_blm",
        base_blm=base_blm,
    )
    if "Error_Infeasible" in result_gdf["Scenario_Zoning"].values:
        raise RuntimeError(f"Fixed baseline infeasible for family {family}.")

    metrics = compute_solution_metrics(
        result_gdf,
        "Scenario_Zoning",
        zone_targets=zone_targets,
        confirmed_mapping=confirmed_mapping,
        report=report,
        baseline_zoning=result_gdf["Scenario_Zoning"].copy(),
    )
    solution_path, export_warning, export_error = save_solution(
        result_gdf,
        os.path.join(output_dir, f"{family}_fixed_blm_blm_{base_blm:g}.gpkg"),
    )
    row = {
        "family": family,
        "setting_label": "fixed_baseline",
        "method": "fixed_blm",
        "base_blm": base_blm,
        "status": "solved",
        "theta_min": params.get("theta_min"),
        "theta_max": params.get("theta_max"),
        "sci_alpha": params.get("sci_alpha"),
        "sci_beta": params.get("sci_beta"),
        "solution_path": solution_path,
    }
    row.update(metrics)
    row["different_cells"] = 0
    row["fixed_adaptive_overlap_share"] = 1.0
    if export_warning:
        row["solution_export_warning"] = export_warning
    if export_error:
        row["solution_export_error"] = export_error
    return result_gdf, row


def run_adaptive_family(
    *,
    family: str,
    scenario_name: str,
    output_dir: str,
    base_grid,
    confirmed_mapping: dict,
    global_params: dict,
    custom_matrix: dict,
    zone_targets: dict,
    settings: list[dict[str, Any]],
    sci_recompute_keys: set[str],
):
    fixed_gdf, fixed_row = run_fixed_baseline(
        grid_gdf=base_grid,
        scenario_name=scenario_name,
        confirmed_mapping=confirmed_mapping,
        zone_targets=zone_targets,
        global_params=global_params,
        custom_matrix=custom_matrix,
        base_blm=BASE_BLM,
        output_dir=output_dir,
        family=family,
    )

    rows = [fixed_row]
    fixed_zoning = fixed_gdf["Scenario_Zoning"].copy()

    for setting in settings:
        adaptive_params = dict(global_params)
        adaptive_params.update(setting)
        if sci_recompute_keys & set(setting):
            adaptive_grid = calculate_dual_sci(
                base_grid.copy(),
                confirmed_mapping,
                method_params=adaptive_params,
            )
        else:
            adaptive_grid = base_grid

        row = {
            "family": family,
            "setting_label": setting["label"],
            "method": "sci_adaptive_blm",
            "base_blm": BASE_BLM,
            "status": "not_run",
        }
        try:
            result_gdf, report, params = run_method_once(
                grid_gdf=adaptive_grid,
                scenario_name=scenario_name,
                confirmed_mapping=confirmed_mapping,
                zone_targets=zone_targets,
                global_params=adaptive_params,
                custom_matrix=custom_matrix,
                method_name="sci_adaptive_blm",
                base_blm=BASE_BLM,
            )
            row.update(
                {
                    "theta_min": params.get("theta_min"),
                    "theta_max": params.get("theta_max"),
                    "sci_alpha": params.get("sci_alpha"),
                    "sci_beta": params.get("sci_beta"),
                }
            )
            if "Error_Infeasible" in result_gdf["Scenario_Zoning"].values:
                row["status"] = "infeasible"
            else:
                row["status"] = "solved"
                metrics = compute_solution_metrics(
                    result_gdf,
                    "Scenario_Zoning",
                    zone_targets=zone_targets,
                    confirmed_mapping=confirmed_mapping,
                    report=report,
                    baseline_zoning=fixed_zoning,
                )
                row.update(metrics)
                row.update(compare_zoning_solutions(fixed_gdf, result_gdf))
                solution_path, export_warning, export_error = save_solution(
                    result_gdf,
                    os.path.join(
                        output_dir,
                        f"{family}_{setting['label']}_adaptive_blm_blm_{BASE_BLM:g}.gpkg",
                    ),
                )
                row["solution_path"] = solution_path
                if export_warning:
                    row["solution_export_warning"] = export_warning
                if export_error:
                    row["solution_export_error"] = export_error
        except Exception as exc:
            row["status"] = "error"
            row["error"] = str(exc)
        rows.append(row)

    return pd.DataFrame(rows)


def build_comparison_table(report_df: pd.DataFrame, family: str) -> pd.DataFrame:
    family_df = report_df[report_df["family"] == family].copy()
    fixed_row = family_df[family_df["method"] == "fixed_blm"].iloc[0]
    adaptive_df = family_df[family_df["method"] == "sci_adaptive_blm"].copy()
    adaptive_df["objective_diff_adaptive_minus_fixed"] = (
        adaptive_df["objective_value"] - fixed_row["objective_value"]
    )
    adaptive_df["boundary_diff_adaptive_minus_fixed"] = (
        adaptive_df["total_boundary_length"] - fixed_row["total_boundary_length"]
    )
    adaptive_df["patch_diff_adaptive_minus_fixed"] = (
        adaptive_df["patch_count_8_neighbor"] - fixed_row["patch_count_8_neighbor"]
    )
    adaptive_df["largest_patch_share_diff_adaptive_minus_fixed"] = (
        adaptive_df["largest_patch_share_8_neighbor"] - fixed_row["largest_patch_share_8_neighbor"]
    )
    return adaptive_df[
        [
            "setting_label",
            "status",
            "theta_min",
            "theta_max",
            "sci_alpha",
            "sci_beta",
            "objective_diff_adaptive_minus_fixed",
            "boundary_diff_adaptive_minus_fixed",
            "patch_diff_adaptive_minus_fixed",
            "largest_patch_share_diff_adaptive_minus_fixed",
            "baseline_overlap_share",
            "fixed_adaptive_overlap_share",
            "different_cells",
        ]
    ].copy()


def run_sensitivity_workflow(
    *,
    pkl_path: str,
    output_dir: str | None = None,
    scenario_name: str = "BLM_Sensitivity",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    grid_gdf, confirmed_mapping, global_params, custom_matrix, zone_targets = load_prepared_state(
        pkl_path
    )

    output_dir = output_dir or os.path.join(
        os.path.dirname(pkl_path),
        f"BLM_Sensitivity_{datetime.now().strftime('%Y%m%d_%H%M')}",
    )
    os.makedirs(output_dir, exist_ok=True)

    theta_df = run_adaptive_family(
        family="theta_sensitivity",
        scenario_name=scenario_name,
        output_dir=output_dir,
        base_grid=grid_gdf,
        confirmed_mapping=confirmed_mapping,
        global_params=global_params,
        custom_matrix=custom_matrix,
        zone_targets=zone_targets,
        settings=DEFAULT_THETA_SETTINGS,
        sci_recompute_keys=set(),
    )
    alpha_beta_df = run_adaptive_family(
        family="alpha_beta_sensitivity",
        scenario_name=scenario_name,
        output_dir=output_dir,
        base_grid=grid_gdf,
        confirmed_mapping=confirmed_mapping,
        global_params=global_params,
        custom_matrix=custom_matrix,
        zone_targets=zone_targets,
        settings=DEFAULT_ALPHA_BETA_SETTINGS,
        sci_recompute_keys={"sci_alpha", "sci_beta"},
    )

    report_df = pd.concat([theta_df, alpha_beta_df], ignore_index=True)
    report_df.to_csv(
        os.path.join(output_dir, "adaptive_blm_sensitivity_report.csv"),
        index=False,
        encoding="utf-8-sig",
    )

    theta_compare = build_comparison_table(report_df, "theta_sensitivity")
    alpha_beta_compare = build_comparison_table(report_df, "alpha_beta_sensitivity")
    theta_compare.to_csv(
        os.path.join(output_dir, "theta_sensitivity_comparison.csv"),
        index=False,
        encoding="utf-8-sig",
    )
    alpha_beta_compare.to_csv(
        os.path.join(output_dir, "alpha_beta_sensitivity_comparison.csv"),
        index=False,
        encoding="utf-8-sig",
    )

    with open(os.path.join(output_dir, "experiment_config.json"), "w", encoding="utf-8") as file:
        json.dump(
            {
                "scenario_name": scenario_name,
                "base_blm": BASE_BLM,
                "families": {
                    "theta_sensitivity": DEFAULT_THETA_SETTINGS,
                    "alpha_beta_sensitivity": DEFAULT_ALPHA_BETA_SETTINGS,
                },
                "fixed_blm_baseline_reuse": True,
                "methods": ["fixed_blm", "sci_adaptive_blm"],
            },
            file,
            ensure_ascii=False,
            indent=4,
        )

    print(f"Saved sensitivity report: {os.path.join(output_dir, 'adaptive_blm_sensitivity_report.csv')}")
    return report_df, theta_compare, alpha_beta_compare


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pkl", default="msp_state.pkl", help="Path to saved MSP workspace pickle.")
    parser.add_argument("--output-dir", default=None, help="Output directory for CSV and solutions.")
    parser.add_argument("--scenario-name", default="BLM_Sensitivity")
    return parser.parse_args()


def main():
    args = parse_args()
    run_sensitivity_workflow(
        pkl_path=args.pkl,
        output_dir=args.output_dir,
        scenario_name=args.scenario_name,
    )


if __name__ == "__main__":
    main()


1. Files inspected

- [run_adaptive_blm_sensitivity.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/run_adaptive_blm_sensitivity.py)
- [run_blm_calibration_methods.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/run_blm_calibration_methods.py)
- [core/kde_engine.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/core/kde_engine.py)
- [core/method_params.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/core/method_params.py)
- [HANDOFF.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/HANDOFF.md)
- relevant tests via `rg`, especially [tests/test_kde_engine.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/tests/test_kde_engine.py) and [tests/test_method_params.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/tests/test_method_params.py)

2. Current sensitivity logic found

- The current sensitivity runner in [run_adaptive_blm_sensitivity.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/run_adaptive_blm_sensitivity.py) already has the right structure for this task:
  - one reused `fixed_blm` baseline per family via `run_fixed_baseline(...)`
  - adaptive settings iterated via `run_adaptive_family(...)`
  - direct fixed-vs-adaptive comparison via:
    - `different_cells`
    - `fixed_adaptive_overlap_share`
  - compact family-specific CSV export via `build_comparison_table(...)`
- Right now it supports two families:
  - `theta_sensitivity`
  - `alpha_beta_sensitivity`
- In [core/kde_engine.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/core/kde_engine.py), `SCI_local` already supports group-weight overrides through `sci_group_weights`, and these weights only affect the human-use component `H_i`.
- The group mapping is still explicit and method-consistent:
  - `fixed_barriers`
  - `linear_transit`
  - `soft_competition`
  - `excluded_from_sci`
- In [core/method_params.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/core/method_params.py), default SCI group weights are centralized and merge cleanly with overrides.

3. Planned group-weight sensitivity design

- Add one new family to the existing sensitivity workflow, for example `group_weight_sensitivity`.
- Keep one reused `fixed_blm` baseline for the whole family:
  - real [msp_state.pkl](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/msp_state.pkl)
  - `base_blm = 3e-4`
  - fixed baseline solved once and exported once
- For all adaptive runs in this family, keep fixed:
  - `theta_min = 0.2`
  - `theta_max = 1.0`
  - `sci_alpha = 0.5`
  - `sci_beta = 0.5`
- Recompute SCI for each adaptive setting because `sci_group_weights` changes `SCI_human_use` and therefore `SCI_local`.
- Use these five candidate settings exactly as the experiment grid:
  - `baseline`
    - `fixed_barriers = 1.0`
    - `linear_transit = 0.8`
    - `soft_competition = 0.5`
  - `transit_heavier`
    - `fixed_barriers = 1.0`
    - `linear_transit = 1.0`
    - `soft_competition = 0.5`
  - `soft_heavier`
    - `fixed_barriers = 1.0`
    - `linear_transit = 0.8`
    - `soft_competition = 0.8`
  - `fixed_lighter`
    - `fixed_barriers = 0.8`
    - `linear_transit = 0.8`
    - `soft_competition = 0.5`
  - `compressed_weights`
    - `fixed_barriers = 1.0`
    - `linear_transit = 0.9`
    - `soft_competition = 0.7`
- Export:
  - one family-level full report row set
  - one compact comparison CSV for this family, parallel to the existing theta/alpha-beta outputs

4. Metrics to compare

Keep aligned with the current workflow and your requested set:

- `objective_value`
- `total_boundary_length`
- `patch_count_8_neighbor`
- `largest_patch_share_8_neighbor`
- `target_achievement`
- `different_cells`
- `fixed_adaptive_overlap_share`

For the compact comparison table, I’d report adaptive relative to the reused fixed baseline:
- setting label
- solve status
- objective diff
- boundary diff
- patch diff
- largest patch share diff
- `fixed_adaptive_overlap_share`
- `different_cells`

5. What will remain unchanged

- real [msp_state.pkl](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/msp_state.pkl)
- `base_blm = 3e-4`
- `theta_min = 0.2`
- `theta_max = 1.0`
- `sci_alpha = 0.5`
- `sci_beta = 0.5`
- comparison frame: `fixed_blm` reused baseline vs `sci_adaptive_blm`
- SCI scientific definition
- ecological exclusions from `SCI_local`
- adaptive BLM chain
- true shared-boundary `B_ij`
- no GUI changes
- no zoned BLM expansion
- `HANDOFF.md` unchanged until successful completion

6. Risks / assumptions

- The expected code change is narrow, but SCI must be recomputed for each group-weight setting; otherwise the weights would not actually propagate into `SCI_local`.
- Because [run_adaptive_blm_sensitivity.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/run_adaptive_blm_sensitivity.py) currently records `theta` and `alpha/beta` columns explicitly, I’ll likely need a small extension so the report also stores the tested `sci_group_weights` labels or values cleanly.
- It’s possible some of these reasonable reweightings produce identical solutions, as happened with the tested alpha/beta range. That would still be a useful stability result, not a failure.
- I’m assuming the current solve time at `base_blm = 3e-4` remains acceptable for one fixed baseline plus five adaptive runs in this family.

1. Files changed

- [run_adaptive_blm_sensitivity.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/run_adaptive_blm_sensitivity.py)
- [HANDOFF.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/HANDOFF.md)

2. Exact functions/scripts added or modified

Modified [run_adaptive_blm_sensitivity.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/run_adaptive_blm_sensitivity.py):

- Added `DEFAULT_GROUP_WEIGHT_SETTINGS`
- Updated `run_fixed_baseline(...)` to store `sci_group_weights` in report rows
- Updated `run_adaptive_family(...)` to store `sci_group_weights` in report rows
- Updated `build_comparison_table(...)` to include `sci_group_weights`
- Updated `run_sensitivity_workflow(...)` to:
  - run a new `group_weight_sensitivity` family
  - recompute SCI for each adaptive group-weight setting via `sci_recompute_keys={"sci_group_weights"}`
  - export `group_weight_sensitivity_comparison.csv`
  - include the new family in `experiment_config.json`

Updated [HANDOFF.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/HANDOFF.md) concisely with:
- that `sci_group_weights` sensitivity was run
- that the adaptive effect stayed stable
- which settings look most paper-useful
- the next recommended step

3. Group-weight sensitivity runs completed

At `base_blm = 3e-4`, with reused `fixed_blm` family baseline and fixed:
- `theta_min = 0.2`
- `theta_max = 1.0`
- `sci_alpha = 0.5`
- `sci_beta = 0.5`

Completed runs:
- `fixed_blm` baseline: solved once
- `baseline`: solved
- `transit_heavier`: solved
- `soft_heavier`: solved
- `fixed_lighter`: solved
- `compressed_weights`: solved

SCI was recomputed for every adaptive setting, so the group-weight changes did feed `SCI_human_use` and `SCI_local`.

4. Compact comparison table

From [group_weight_sensitivity_comparison.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/BLM_Sensitivity_real_macos_3e4_groupweights/group_weight_sensitivity_comparison.csv), adaptive relative to reused fixed baseline:

| setting | objective diff | boundary diff | patch diff | largest patch share diff | overlap share | different cells |
|---|---:|---:|---:|---:|---:|---:|
| `baseline` | `-0.57` | `+1750.0` | `+2` | `0.0` | `0.999829` | `4` |
| `transit_heavier` | `-0.56` | `+1750.0` | `+2` | `0.0` | `0.999829` | `4` |
| `soft_heavier` | `-0.58` | `+1750.0` | `+2` | `0.0` | `0.999829` | `4` |
| `fixed_lighter` | `-0.57` | `+1750.0` | `+2` | `0.0` | `0.999829` | `4` |
| `compressed_weights` | `-0.57` | `+1750.0` | `+2` | `0.0` | `0.999829` | `4` |

The tested weight values are also stored clearly in the full report rows under `sci_group_weights` in [adaptive_blm_sensitivity_report.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/BLM_Sensitivity_real_macos_3e4_groupweights/adaptive_blm_sensitivity_report.csv).

5. Which settings show the most stable adaptive effect

All five tested group-weight settings showed essentially the same adaptive-vs-fixed separation.

Most stable conclusion:
- the adaptive effect stayed stable under all tested reasonable group reweightings

Paper-useful settings:
- `baseline` remains the clean default
- `compressed_weights` and `transit_heavier` are good stability-check alternatives if you want to show robustness without changing the story

6. Any anomalies or failures

No solve failures occurred.

No GUI or zoned-BLM changes were made.

The main result is that this sensitivity family was highly stable:
- boundary length difference, patch difference, overlap, and changed-cell counts were identical across all five settings
- only tiny objective shifts appeared across the group-weight variants

That is a useful stability finding rather than a problem.

7. Review summary for external method check

This was a narrow, method-consistent extension of the existing sensitivity workflow.

Unchanged:
- SCI scientific definition
- ecological exclusions from `SCI_local`
- adaptive BLM chain
- true shared-boundary `B_ij`
- fixed-vs-adaptive comparison frame
- no GUI changes
- no zoned BLM expansion

What the new result says:
- at `base_blm = 3e-4`, with `theta_min = 0.2`, `theta_max = 1.0`, `alpha = beta = 0.5`, the adaptive-vs-fixed separation is robust to the tested `sci_group_weights` reweightings
- this strengthens the case that the observed adaptive effect is not fragile to reasonable human-use group weighting choices

2 个文件已更改
+87
-7



HANDOFF.md
   - all three tested settings produced the same solved outcome at this BLM level
   - this suggests the adaptive result is stable to reasonable geometry-vs-human weighting changes in the tested range

3. `sci_group_weights` sensitivity
   - tested:
     - baseline `(1.0, 0.8, 0.5)`
     - transit_heavier `(1.0, 1.0, 0.5)`
     - soft_heavier `(1.0, 0.8, 0.8)`
     - fixed_lighter `(0.8, 0.8, 0.5)`
     - compressed_weights `(1.0, 0.9, 0.7)`
   - all runs solved
   - adaptive-vs-fixed separation stayed stable across all tested weight settings
   - objective differences moved only slightly; boundary, patch count, overlap, and changed-cell results were unchanged across the tested range
   - paper-useful settings: baseline remains the clean default, with `compressed_weights` and `transit_heavier` acceptable as stability checks

## Immediate next priority
Paper-oriented next step:

1. use `base_blm = 3e-4` as the primary comparison level,
2. keep `(theta_min, theta_max) = (0.2,1.0)` as the default adaptive setting and optionally report `(0.3,0.9)` as a stability check,
3. keep `(sci_alpha, sci_beta) = (0.5,0.5)` as the default since nearby tested values were solution-invariant,
4. next sensitivity extension: test `sci_group_weights` (still without expanding to zoned BLM).
4. keep baseline `sci_group_weights = {fixed_barriers: 1.0, linear_transit: 0.8, soft_competition: 0.5}` as the default since tested reweightings were stable,
5. next recommended step: consolidate the paper-ready calibration and sensitivity tables, then decide whether any broader weight extremes are worth testing.

## Suggested next Codex task
A good next task is:
- run a narrow `sci_group_weights` sensitivity at `base_blm = 3e-4`,
- confirm whether the adaptive-vs-fixed separation remains stable under reasonable human-use group reweighting,
- then consolidate the paper-ready calibration/sensitivity tables.
- consolidate the current BLM sweep plus theta / alpha-beta / group-weight sensitivity outputs into paper-ready tables,
- identify one default setting set and one or two stability-check settings for the manuscript,
- then only if needed test a small extreme-case weight grid.

## Important files to inspect first
- `core/method_params.py`
run_adaptive_blm_sensitivity.py
    {"label": "alpha_0.5_beta_0.5", "sci_alpha": 0.5, "sci_beta": 0.5},
    {"label": "alpha_0.7_beta_0.3", "sci_alpha": 0.7, "sci_beta": 0.3},
]
DEFAULT_GROUP_WEIGHT_SETTINGS = [
    {
        "label": "baseline",
        "sci_group_weights": {
            "fixed_barriers": 1.0,
            "linear_transit": 0.8,
            "soft_competition": 0.5,
        },
    },
    {
        "label": "transit_heavier",
        "sci_group_weights": {
            "fixed_barriers": 1.0,
            "linear_transit": 1.0,
            "soft_competition": 0.5,
        },
    },
    {
        "label": "soft_heavier",
        "sci_group_weights": {
            "fixed_barriers": 1.0,
            "linear_transit": 0.8,
            "soft_competition": 0.8,
        },
    },
    {
        "label": "fixed_lighter",
        "sci_group_weights": {
            "fixed_barriers": 0.8,
            "linear_transit": 0.8,
            "soft_competition": 0.5,
        },
    },
    {
        "label": "compressed_weights",
        "sci_group_weights": {
            "fixed_barriers": 1.0,
            "linear_transit": 0.9,
            "soft_competition": 0.7,
        },
    },
]


def compare_zoning_solutions(fixed_gdf, adaptive_gdf, zoning_col: str = "Scenario_Zoning") -> dict[str, float]:
        "theta_max": params.get("theta_max"),
        "sci_alpha": params.get("sci_alpha"),
        "sci_beta": params.get("sci_beta"),
        "sci_group_weights": json.dumps(params.get("sci_group_weights", {}), sort_keys=True),
        "solution_path": solution_path,
    }
    row.update(metrics)
                    "theta_max": params.get("theta_max"),
                    "sci_alpha": params.get("sci_alpha"),
                    "sci_beta": params.get("sci_beta"),
                    "sci_group_weights": json.dumps(
                        params.get("sci_group_weights", {}),
                        sort_keys=True,
                    ),
                }
            )
            if "Error_Infeasible" in result_gdf["Scenario_Zoning"].values:
            "theta_max",
            "sci_alpha",
            "sci_beta",
            "sci_group_weights",
            "objective_diff_adaptive_minus_fixed",
            "boundary_diff_adaptive_minus_fixed",
            "patch_diff_adaptive_minus_fixed",
    pkl_path: str,
    output_dir: str | None = None,
    scenario_name: str = "BLM_Sensitivity",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    grid_gdf, confirmed_mapping, global_params, custom_matrix, zone_targets = load_prepared_state(
        pkl_path
    )
        settings=DEFAULT_ALPHA_BETA_SETTINGS,
        sci_recompute_keys={"sci_alpha", "sci_beta"},
    )
    group_weight_df = run_adaptive_family(
        family="group_weight_sensitivity",
        scenario_name=scenario_name,
        output_dir=output_dir,
        base_grid=grid_gdf,
        confirmed_mapping=confirmed_mapping,
        global_params=global_params,
        custom_matrix=custom_matrix,
        zone_targets=zone_targets,
        settings=DEFAULT_GROUP_WEIGHT_SETTINGS,
        sci_recompute_keys={"sci_group_weights"},
    )

    report_df = pd.concat([theta_df, alpha_beta_df], ignore_index=True)
    report_df = pd.concat([theta_df, alpha_beta_df, group_weight_df], ignore_index=True)
    report_df.to_csv(
        os.path.join(output_dir, "adaptive_blm_sensitivity_report.csv"),
        index=False,

    theta_compare = build_comparison_table(report_df, "theta_sensitivity")
    alpha_beta_compare = build_comparison_table(report_df, "alpha_beta_sensitivity")
    group_weight_compare = build_comparison_table(report_df, "group_weight_sensitivity")
    theta_compare.to_csv(
        os.path.join(output_dir, "theta_sensitivity_comparison.csv"),
        index=False,
        index=False,
        encoding="utf-8-sig",
    )
    group_weight_compare.to_csv(
        os.path.join(output_dir, "group_weight_sensitivity_comparison.csv"),
        index=False,
        encoding="utf-8-sig",
    )

    with open(os.path.join(output_dir, "experiment_config.json"), "w", encoding="utf-8") as file:
        json.dump(
                "families": {
                    "theta_sensitivity": DEFAULT_THETA_SETTINGS,
                    "alpha_beta_sensitivity": DEFAULT_ALPHA_BETA_SETTINGS,
                    "group_weight_sensitivity": DEFAULT_GROUP_WEIGHT_SETTINGS,
                },
                "fixed_blm_baseline_reuse": True,
                "methods": ["fixed_blm", "sci_adaptive_blm"],
        )

    print(f"Saved sensitivity report: {os.path.join(output_dir, 'adaptive_blm_sensitivity_report.csv')}")
    return report_df, theta_compare, alpha_beta_compare
    return report_df, theta_compare, alpha_beta_compare, group_weight_compare


def parse_args():

1. Files inspected

- [HANDOFF.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/HANDOFF.md)
- [run_blm_calibration_methods.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/run_blm_calibration_methods.py)
- [run_adaptive_blm_sensitivity.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/run_adaptive_blm_sensitivity.py)
- [BLM_Calibration_real_macos_sweep/blm_calibration_method_comparison.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/BLM_Calibration_real_macos_sweep/blm_calibration_method_comparison.csv)
- [BLM_Sensitivity_real_macos_3e4/adaptive_blm_sensitivity_report.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/BLM_Sensitivity_real_macos_3e4/adaptive_blm_sensitivity_report.csv)
- [BLM_Sensitivity_real_macos_3e4/theta_sensitivity_comparison.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/BLM_Sensitivity_real_macos_3e4/theta_sensitivity_comparison.csv)
- [BLM_Sensitivity_real_macos_3e4/alpha_beta_sensitivity_comparison.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/BLM_Sensitivity_real_macos_3e4/alpha_beta_sensitivity_comparison.csv)
- [BLM_Sensitivity_real_macos_3e4_groupweights/adaptive_blm_sensitivity_report.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/BLM_Sensitivity_real_macos_3e4_groupweights/adaptive_blm_sensitivity_report.csv)
- [BLM_Sensitivity_real_macos_3e4_groupweights/group_weight_sensitivity_comparison.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/BLM_Sensitivity_real_macos_3e4_groupweights/group_weight_sensitivity_comparison.csv)
- result directories:
  - [BLM_Calibration_real_macos_sweep](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/BLM_Calibration_real_macos_sweep)
  - [BLM_Sensitivity_real_macos_3e4](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/BLM_Sensitivity_real_macos_3e4)
  - [BLM_Sensitivity_real_macos_3e4_groupweights](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/BLM_Sensitivity_real_macos_3e4_groupweights)

2. Current outputs available

- Calibration sweep outputs already exist and appear complete:
  - one main CSV with all `fixed_blm` and `sci_adaptive_blm` rows across `1e-6, 1e-5, 1e-4, 3e-4, 1e-3`
  - paired solution GPKGs for each tested `base_blm`
- Sensitivity outputs already exist for:
  - theta family:
    - full report rows in `adaptive_blm_sensitivity_report.csv`
    - compact table in `theta_sensitivity_comparison.csv`
  - alpha/beta family:
    - full report rows in `adaptive_blm_sensitivity_report.csv`
    - compact table in `alpha_beta_sensitivity_comparison.csv`
  - group-weight family:
    - full report rows in `adaptive_blm_sensitivity_report.csv`
    - compact table in `group_weight_sensitivity_comparison.csv`
- There are two sensitivity result directories:
  - [BLM_Sensitivity_real_macos_3e4](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/BLM_Sensitivity_real_macos_3e4) for theta and alpha/beta
  - [BLM_Sensitivity_real_macos_3e4_groupweights](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/BLM_Sensitivity_real_macos_3e4_groupweights) for theta, alpha/beta, and group weights
- `HANDOFF.md` is now accurate but a bit cumulative; it can be tightened to reflect only the current recommended defaults, stability checks, and next step.

3. Planned consolidation outputs

I’d keep this narrow and build one small manuscript-facing output folder, reusing existing CSVs.

Planned table outputs:
- `paper_outputs/calibration_summary_table.csv`
  - one row per `base_blm`
  - fixed vs adaptive comparison focused on paper metrics
  - include explicit default row highlight for `3e-4`
- `paper_outputs/theta_sensitivity_summary_table.csv`
  - one row per theta setting
  - adaptive-minus-fixed deltas at `base_blm=3e-4`
- `paper_outputs/alpha_beta_sensitivity_summary_table.csv`
  - one row per alpha/beta setting
  - adaptive-minus-fixed deltas at `base_blm=3e-4`
- `paper_outputs/group_weight_sensitivity_summary_table.csv`
  - one row per group-weight setting
  - adaptive-minus-fixed deltas at `base_blm=3e-4`

Planned figure-ready CSV exports:
- `paper_outputs/figure_blm_sweep.csv`
  - compact plotting table for the BLM sweep
  - likely columns:
    - `base_blm`
    - `objective_diff_adaptive_minus_fixed`
    - `boundary_diff_adaptive_minus_fixed`
    - `patch_diff_adaptive_minus_fixed`
    - `different_cells`
- `paper_outputs/figure_theta_sensitivity.csv`
  - compact plotting table for theta sensitivity
  - likely columns:
    - `setting_label`
    - `theta_min`
    - `theta_max`
    - `objective_diff_adaptive_minus_fixed`
    - `boundary_diff_adaptive_minus_fixed`
    - `patch_diff_adaptive_minus_fixed`
    - `different_cells`
- `paper_outputs/figure_group_weight_sensitivity.csv`
  - compact plotting table for group-weight sensitivity
  - likely columns:
    - `setting_label`
    - weight columns expanded or preserved as readable labels
    - `objective_diff_adaptive_minus_fixed`
    - `boundary_diff_adaptive_minus_fixed`
    - `patch_diff_adaptive_minus_fixed`
    - `different_cells`

I’d also add one short markdown note:
- `paper_outputs/summary_notes.md`
  - default setting set
  - stability-check settings
  - which CSVs feed tables vs figures

4. Which results will be treated as default vs stability-check cases

Default case:
- `base_blm = 3e-4`
- `theta_min = 0.2`
- `theta_max = 1.0`
- `sci_alpha = 0.5`
- `sci_beta = 0.5`
- `sci_group_weights = {fixed_barriers: 1.0, linear_transit: 0.8, soft_competition: 0.5}`

Stability-check cases to preserve:
- theta:
  - `theta = (0.3, 0.9)` as the moderate robustness check
- group weights:
  - `compressed_weights` as the preferred robustness check
  - `transit_heavier` as the alternate robustness check if a second is useful

Interpretation framing:
- alpha/beta can be presented as “stable in tested range,” with the default `0.5/0.5` retained
- group-weight sensitivity can be presented as “stable in tested range,” with baseline as default and `compressed_weights` as the most presentation-friendly robustness check

5. Proposed files to add or modify

Likely additions:
- `paper_outputs/calibration_summary_table.csv`
- `paper_outputs/theta_sensitivity_summary_table.csv`
- `paper_outputs/alpha_beta_sensitivity_summary_table.csv`
- `paper_outputs/group_weight_sensitivity_summary_table.csv`
- `paper_outputs/figure_blm_sweep.csv`
- `paper_outputs/figure_theta_sensitivity.csv`
- `paper_outputs/figure_group_weight_sensitivity.csv`
- `paper_outputs/summary_notes.md`

Likely code addition or narrow modification:
- either add a small consolidation script such as `prepare_paper_outputs.py`
- or add a very small utility section to [run_adaptive_blm_sensitivity.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/run_adaptive_blm_sensitivity.py) only if reuse is cleaner

Likely modification:
- [HANDOFF.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/HANDOFF.md)
  - short cleanup only after successful consolidation
  - reduce older historical framing and keep current latest state + next step

6. Risks / assumptions

- The cleanest source for final sensitivity tables is probably [BLM_Sensitivity_real_macos_3e4_groupweights/adaptive_blm_sensitivity_report.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/BLM_Sensitivity_real_macos_3e4_groupweights/adaptive_blm_sensitivity_report.csv), since it includes all three families in one place.
- The calibration sweep CSV alone does not contain the direct fixed-vs-adaptive `different_cells` field, so the figure-ready BLM sweep export may need a small derived step that reads the existing GPKGs or reuses the already computed pairwise comparison logic. That should still be lightweight and should not require rerunning solves.
- There are now two sensitivity output directories; I’d treat [BLM_Sensitivity_real_macos_3e4_groupweights](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/BLM_Sensitivity_real_macos_3e4_groupweights) as the authoritative latest source to avoid mixing versions.
- I’m assuming manuscript-facing outputs should be plain CSV/Markdown only for now, not formatted DOCX/LaTeX tables yet.

1. Files changed

- [prepare_paper_outputs.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/prepare_paper_outputs.py)
- [HANDOFF.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/HANDOFF.md)

2. Exact functions/scripts added or modified

Added new standalone script [prepare_paper_outputs.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/prepare_paper_outputs.py) with:

- `_load_jsonish(...)`
- `_canonical_group_weights(...)`
- `_derive_solution_overlap(...)`
- `build_calibration_outputs()`
- `build_family_summary(...)`
- `build_figure_family(...)`
- `write_summary_notes()`
- `main()`

Updated [HANDOFF.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/HANDOFF.md) to reflect the current latest state, the current default settings, completed stability checks, the new `paper_outputs/` artifacts, and the next recommended step.

3. Paper-output files generated

Under [paper_outputs](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs):

- [calibration_summary_table.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/calibration_summary_table.csv)
- [theta_sensitivity_summary_table.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/theta_sensitivity_summary_table.csv)
- [alpha_beta_sensitivity_summary_table.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/alpha_beta_sensitivity_summary_table.csv)
- [group_weight_sensitivity_summary_table.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/group_weight_sensitivity_summary_table.csv)
- [figure_blm_sweep.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/figure_blm_sweep.csv)
- [figure_theta_sensitivity.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/figure_theta_sensitivity.csv)
- [figure_group_weight_sensitivity.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/figure_group_weight_sensitivity.csv)
- [summary_notes.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/summary_notes.md)

4. Source files used for each output

`calibration_summary_table.csv`
- [BLM_Calibration_real_macos_sweep/blm_calibration_method_comparison.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/BLM_Calibration_real_macos_sweep/blm_calibration_method_comparison.csv)
- paired fixed/adaptive solution GPKGs in [BLM_Calibration_real_macos_sweep](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/BLM_Calibration_real_macos_sweep) for direct overlap and `different_cells`

`theta_sensitivity_summary_table.csv`
- [BLM_Sensitivity_real_macos_3e4_groupweights/adaptive_blm_sensitivity_report.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/BLM_Sensitivity_real_macos_3e4_groupweights/adaptive_blm_sensitivity_report.csv)

`alpha_beta_sensitivity_summary_table.csv`
- [BLM_Sensitivity_real_macos_3e4_groupweights/adaptive_blm_sensitivity_report.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/BLM_Sensitivity_real_macos_3e4_groupweights/adaptive_blm_sensitivity_report.csv)

`group_weight_sensitivity_summary_table.csv`
- [BLM_Sensitivity_real_macos_3e4_groupweights/adaptive_blm_sensitivity_report.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/BLM_Sensitivity_real_macos_3e4_groupweights/adaptive_blm_sensitivity_report.csv)

`figure_blm_sweep.csv`
- same sources as `calibration_summary_table.csv`

`figure_theta_sensitivity.csv`
- same source as `theta_sensitivity_summary_table.csv`

`figure_group_weight_sensitivity.csv`
- same source as `group_weight_sensitivity_summary_table.csv`

`summary_notes.md`
- interpreted from the default/stability conclusions already established in:
  - [BLM_Calibration_real_macos_sweep/blm_calibration_method_comparison.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/BLM_Calibration_real_macos_sweep/blm_calibration_method_comparison.csv)
  - [BLM_Sensitivity_real_macos_3e4_groupweights/adaptive_blm_sensitivity_report.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/BLM_Sensitivity_real_macos_3e4_groupweights/adaptive_blm_sensitivity_report.csv)

5. Any derived steps performed

- No large solves were rerun.
- The only nontrivial derived step was for the BLM sweep:
  - `different_cells` and `fixed_adaptive_overlap_share` were derived by reading the existing fixed/adaptive GPKG solution pairs from [BLM_Calibration_real_macos_sweep](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/BLM_Calibration_real_macos_sweep), not by rerunning optimization.
- For sensitivity tables, the script reused the authoritative latest report in [BLM_Sensitivity_real_macos_3e4_groupweights](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/BLM_Sensitivity_real_macos_3e4_groupweights) and normalized the stored `sci_group_weights` into a clean canonical JSON string for manuscript-facing tables.

6. Remaining issues / risks

- The outputs are manuscript-facing CSV/Markdown, not final formatted LaTeX/Word tables yet.
- `summary_notes.md` is intentionally compact; if you want journal-ready captions or table notes, that would be a separate presentation step.
- The authoritative sensitivity source is now clearly [BLM_Sensitivity_real_macos_3e4_groupweights](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/BLM_Sensitivity_real_macos_3e4_groupweights); older sensitivity folders should be treated as superseded working artifacts.
- `HANDOFF.md` is now current, but if you later decide to test any extreme-case weight settings, it will need another concise refresh.

7. Review summary for external method check

This step only consolidated existing completed results into paper-ready outputs. It did not alter:
- the SCI scientific definition
- ecological exclusions from `SCI_local`
- the adaptive BLM chain
- true shared-boundary `B_ij`
- GUI
- scope into zoned BLM

The resulting `paper_outputs/` package now reflects the current recommended manuscript framing:
- default case:
  - `base_blm = 3e-4`
  - `theta_min = 0.2`
  - `theta_max = 1.0`
  - `sci_alpha = 0.5`
  - `sci_beta = 0.5`
  - baseline group weights
- stability checks preserved:
  - `theta_0.3_0.9`
  - `compressed_weights`
  - optionally `transit_heavier`

  2 个文件已更改
+289
-55



HANDOFF.md
- objective value,
- baseline overlap.

## Current known blockers / issues
## Current paper-ready state

### 1. Windows local Gurobi limit
A full run using the real workspace failed under the Windows environment because the local restricted Gurobi license rejected the large model.
- Real macOS + Gurobi calibration succeeds on `msp_state.pkl`.
- A nonzero BLM sweep confirmed `fixed_blm` and `sci_adaptive_blm` no longer collapse to identical outcomes.
- The manuscript-facing default setting set is:
  - `base_blm = 3e-4`
  - `theta_min = 0.2`
  - `theta_max = 1.0`
  - `sci_alpha = 0.5`
  - `sci_beta = 0.5`
  - `sci_group_weights = {fixed_barriers: 1.0, linear_transit: 0.8, soft_competition: 0.5}`

### 2. Small-trial run was not scientifically informative yet
A derived 10x10 trial workspace ran successfully, but all methods and all tested `base_blm` values produced identical results.
This strongly suggests that boundary penalties were not effectively entering the optimizer in that environment.
## Stability checks completed

### 3. Suspected cause
The environment lacked `libpysal`, and the optimizer adjacency path may have skipped BLM-edge construction when `libpysal` was unavailable.
This must be verified and, if needed, replaced with a robust fallback based on existing `row_idx` / `col_idx` Queen-neighborhood logic.
- `theta_min / theta_max` sensitivity at `base_blm = 3e-4`
  - tested: `(0.2,1.0)`, `(0.4,1.0)`, `(0.1,1.0)`, `(0.2,0.8)`, `(0.3,0.9)`
  - adaptive effect stayed present across all tested settings
  - preferred moderate stability check: `(0.3,0.9)`

### 4. Export note
GeoPackage export failed in one workflow and was downgraded to GeoJSON fallback. This is acceptable for debugging but should be revisited if paper deliverables require GPKG.
- `sci_alpha / sci_beta` sensitivity at `base_blm = 3e-4`
  - tested: `(0.3,0.7)`, `(0.5,0.5)`, `(0.7,0.3)`
  - tested range was solution-stable

## Latest macOS calibration status
- `sci_group_weights` sensitivity at `base_blm = 3e-4`
  - tested:
    - baseline `(1.0, 0.8, 0.5)`
    - transit_heavier `(1.0, 1.0, 0.5)`
    - soft_heavier `(1.0, 0.8, 0.8)`
    - fixed_lighter `(0.8, 0.8, 0.5)`
    - compressed_weights `(1.0, 0.9, 0.7)`
  - adaptive-vs-fixed separation stayed stable across all tested weight settings
  - preferred stability checks: `compressed_weights`, optionally `transit_heavier`

- Real macOS + Gurobi calibration now succeeds on `msp_state.pkl`.
- A nonzero BLM sweep confirmed `fixed_blm` and `sci_adaptive_blm` no longer collapse to identical outcomes.
- Around the currently useful comparison range:
  - `1e-4` shows small but real divergence,
  - `3e-4` shows clearer divergence with moderate solve separation,
  - `1e-3` shows the strongest divergence in the tested range.
## Consolidated outputs

## Latest sensitivity experiments
Paper-ready summary tables and figure-ready CSVs are now under `paper_outputs/`:

At `base_blm = 3e-4`, two adaptive-BLM stability families were run against a reused `fixed_blm` baseline per family:

1. `theta_min / theta_max` sensitivity
   - tested: `(0.2,1.0)`, `(0.4,1.0)`, `(0.1,1.0)`, `(0.2,0.8)`, `(0.3,0.9)`
   - all runs solved
   - adaptive effect remained present across all tested theta settings
   - strongest separation in this family: `theta_min=0.1, theta_max=1.0`
   - stable, paper-useful moderate settings: `(0.2,1.0)`, `(0.2,0.8)`, `(0.3,0.9)`

2. `sci_alpha / sci_beta` sensitivity
   - tested: `(0.3,0.7)`, `(0.5,0.5)`, `(0.7,0.3)`
   - all runs solved
   - all three tested settings produced the same solved outcome at this BLM level
   - this suggests the adaptive result is stable to reasonable geometry-vs-human weighting changes in the tested range

3. `sci_group_weights` sensitivity
   - tested:
     - baseline `(1.0, 0.8, 0.5)`
     - transit_heavier `(1.0, 1.0, 0.5)`
     - soft_heavier `(1.0, 0.8, 0.8)`
     - fixed_lighter `(0.8, 0.8, 0.5)`
     - compressed_weights `(1.0, 0.9, 0.7)`
   - all runs solved
   - adaptive-vs-fixed separation stayed stable across all tested weight settings
   - objective differences moved only slightly; boundary, patch count, overlap, and changed-cell results were unchanged across the tested range
   - paper-useful settings: baseline remains the clean default, with `compressed_weights` and `transit_heavier` acceptable as stability checks
- `calibration_summary_table.csv`
- `theta_sensitivity_summary_table.csv`
- `alpha_beta_sensitivity_summary_table.csv`
- `group_weight_sensitivity_summary_table.csv`
- `figure_blm_sweep.csv`
- `figure_theta_sensitivity.csv`
- `figure_group_weight_sensitivity.csv`
- `summary_notes.md`

## Immediate next priority
Paper-oriented next step:

1. use `base_blm = 3e-4` as the primary comparison level,
2. keep `(theta_min, theta_max) = (0.2,1.0)` as the default adaptive setting and optionally report `(0.3,0.9)` as a stability check,
3. keep `(sci_alpha, sci_beta) = (0.5,0.5)` as the default since nearby tested values were solution-invariant,
4. keep baseline `sci_group_weights = {fixed_barriers: 1.0, linear_transit: 0.8, soft_competition: 0.5}` as the default since tested reweightings were stable,
5. next recommended step: consolidate the paper-ready calibration and sensitivity tables, then decide whether any broader weight extremes are worth testing.
- turn the `paper_outputs/` CSVs into manuscript tables/figures,
- keep the current default setting set as the main reported result,
- use `theta_0.3_0.9` and `compressed_weights` as the main robustness checks,
- only if reviewers or paper framing require it, consider a very small extreme-case weight check later.

## Suggested next Codex task
A good next task is:
- consolidate the current BLM sweep plus theta / alpha-beta / group-weight sensitivity outputs into paper-ready tables,
- identify one default setting set and one or two stability-check settings for the manuscript,
- then only if needed test a small extreme-case weight grid.

- format the `paper_outputs/` tables into final manuscript-ready presentation form,
- generate plotting code or publication figures directly from the figure-ready CSVs,
- keep method logic frozen unless a presentation-only change is needed.

## Important files to inspect first
- `core/method_params.py`
- `core/kde_engine.py`
prepare_paper_outputs.py
"""Prepare manuscript-facing summary tables and figure-ready exports.

This script consolidates existing calibration and sensitivity results without
rerunning optimization solves.
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd


CALIBRATION_DIR = Path("BLM_Calibration_real_macos_sweep")
SENSITIVITY_DIR = Path("BLM_Sensitivity_real_macos_3e4_groupweights")
OUTPUT_DIR = Path("paper_outputs")

DEFAULT_CASE = {
    "base_blm": 3e-4,
    "theta_min": 0.2,
    "theta_max": 1.0,
    "sci_alpha": 0.5,
    "sci_beta": 0.5,
    "sci_group_weights": {
        "fixed_barriers": 1.0,
        "linear_transit": 0.8,
        "soft_competition": 0.5,
    },
}
STABILITY_CASES = {
    "theta": {"setting_label": "theta_0.3_0.9"},
    "group_weights_primary": {"setting_label": "compressed_weights"},
    "group_weights_alternate": {"setting_label": "transit_heavier"},
}


def _load_jsonish(value):
    if isinstance(value, str) and value:
        return json.loads(value)
    return value


def _canonical_group_weights(value) -> str:
    weights = _load_jsonish(value) or {}
    clean = {
        "fixed_barriers": weights.get("fixed_barriers"),
        "linear_transit": weights.get("linear_transit"),
        "soft_competition": weights.get("soft_competition"),
    }
    return json.dumps(clean, sort_keys=True)


def _derive_solution_overlap(fixed_path: Path, adaptive_path: Path) -> tuple[int, float]:
    fixed = gpd.read_file(fixed_path)
    adaptive = gpd.read_file(adaptive_path)
    same = (
        fixed["Scenario_Zoning"].astype(str).reset_index(drop=True)
        == adaptive["Scenario_Zoning"].astype(str).reset_index(drop=True)
    )
    return int((~same).sum()), float(same.mean())


def build_calibration_outputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(CALIBRATION_DIR / "blm_calibration_method_comparison.csv")
    rows = []
    for base_blm in sorted(df["base_blm"].unique()):
        pair = df[df["base_blm"] == base_blm].set_index("method")
        fixed = pair.loc["fixed_blm"]
        adaptive = pair.loc["sci_adaptive_blm"]
        different_cells, overlap = _derive_solution_overlap(
            Path(fixed["solution_path"]),
            Path(adaptive["solution_path"]),
        )
        rows.append(
            {
                "base_blm": base_blm,
                "fixed_status": fixed["status"],
                "adaptive_status": adaptive["status"],
                "fixed_objective_value": fixed["objective_value"],
                "adaptive_objective_value": adaptive["objective_value"],
                "objective_diff_adaptive_minus_fixed": adaptive["objective_value"] - fixed["objective_value"],
                "fixed_total_boundary_length": fixed["total_boundary_length"],
                "adaptive_total_boundary_length": adaptive["total_boundary_length"],
                "boundary_diff_adaptive_minus_fixed": adaptive["total_boundary_length"] - fixed["total_boundary_length"],
                "fixed_patch_count_8_neighbor": fixed["patch_count_8_neighbor"],
                "adaptive_patch_count_8_neighbor": adaptive["patch_count_8_neighbor"],
                "patch_diff_adaptive_minus_fixed": adaptive["patch_count_8_neighbor"] - fixed["patch_count_8_neighbor"],
                "fixed_largest_patch_share_8_neighbor": fixed["largest_patch_share_8_neighbor"],
                "adaptive_largest_patch_share_8_neighbor": adaptive["largest_patch_share_8_neighbor"],
                "largest_patch_share_diff_adaptive_minus_fixed": adaptive["largest_patch_share_8_neighbor"] - fixed["largest_patch_share_8_neighbor"],
                "fixed_target_min_achievement_ratio": fixed["target_min_achievement_ratio"],
                "adaptive_target_min_achievement_ratio": adaptive["target_min_achievement_ratio"],
                "fixed_adaptive_overlap_share": overlap,
                "different_cells": different_cells,
                "is_recommended_default_base_blm": bool(abs(base_blm - DEFAULT_CASE["base_blm"]) < 1e-12),
            }
        )

    summary = pd.DataFrame(rows)
    figure = summary[
        [
            "base_blm",
            "objective_diff_adaptive_minus_fixed",
            "boundary_diff_adaptive_minus_fixed",
            "patch_diff_adaptive_minus_fixed",
            "different_cells",
            "fixed_adaptive_overlap_share",
        ]
    ].copy()
    return summary, figure


def build_family_summary(family: str) -> pd.DataFrame:
    report = pd.read_csv(SENSITIVITY_DIR / "adaptive_blm_sensitivity_report.csv")
    family_df = report[report["family"] == family].copy()
    fixed = family_df[family_df["method"] == "fixed_blm"].iloc[0]
    adaptive = family_df[family_df["method"] == "sci_adaptive_blm"].copy()
    adaptive["sci_group_weights"] = adaptive["sci_group_weights"].apply(_canonical_group_weights)
    adaptive["fixed_objective_value"] = fixed["objective_value"]
    adaptive["adaptive_objective_value"] = adaptive["objective_value"]
    adaptive["objective_diff_adaptive_minus_fixed"] = adaptive["objective_value"] - fixed["objective_value"]
    adaptive["fixed_total_boundary_length"] = fixed["total_boundary_length"]
    adaptive["adaptive_total_boundary_length"] = adaptive["total_boundary_length"]
    adaptive["boundary_diff_adaptive_minus_fixed"] = adaptive["total_boundary_length"] - fixed["total_boundary_length"]
    adaptive["fixed_patch_count_8_neighbor"] = fixed["patch_count_8_neighbor"]
    adaptive["adaptive_patch_count_8_neighbor"] = adaptive["patch_count_8_neighbor"]
    adaptive["patch_diff_adaptive_minus_fixed"] = adaptive["patch_count_8_neighbor"] - fixed["patch_count_8_neighbor"]
    adaptive["fixed_largest_patch_share_8_neighbor"] = fixed["largest_patch_share_8_neighbor"]
    adaptive["adaptive_largest_patch_share_8_neighbor"] = adaptive["largest_patch_share_8_neighbor"]
    adaptive["largest_patch_share_diff_adaptive_minus_fixed"] = (
        adaptive["largest_patch_share_8_neighbor"] - fixed["largest_patch_share_8_neighbor"]
    )
    adaptive["fixed_target_min_achievement_ratio"] = fixed["target_min_achievement_ratio"]
    adaptive["adaptive_target_min_achievement_ratio"] = adaptive["target_min_achievement_ratio"]
    return adaptive[
        [
            "setting_label",
            "status",
            "theta_min",
            "theta_max",
            "sci_alpha",
            "sci_beta",
            "sci_group_weights",
            "fixed_objective_value",
            "adaptive_objective_value",
            "objective_diff_adaptive_minus_fixed",
            "fixed_total_boundary_length",
            "adaptive_total_boundary_length",
            "boundary_diff_adaptive_minus_fixed",
            "fixed_patch_count_8_neighbor",
            "adaptive_patch_count_8_neighbor",
            "patch_diff_adaptive_minus_fixed",
            "fixed_largest_patch_share_8_neighbor",
            "adaptive_largest_patch_share_8_neighbor",
            "largest_patch_share_diff_adaptive_minus_fixed",
            "fixed_target_min_achievement_ratio",
            "adaptive_target_min_achievement_ratio",
            "fixed_adaptive_overlap_share",
            "different_cells",
        ]
    ].copy()


def build_figure_family(family: str) -> pd.DataFrame:
    summary = build_family_summary(family)
    return summary[
        [
            "setting_label",
            "theta_min",
            "theta_max",
            "sci_group_weights",
            "objective_diff_adaptive_minus_fixed",
            "boundary_diff_adaptive_minus_fixed",
            "patch_diff_adaptive_minus_fixed",
            "different_cells",
            "fixed_adaptive_overlap_share",
        ]
    ].copy()


def write_summary_notes() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    notes = f"""# Summary Notes

## Default Case

- `base_blm = {DEFAULT_CASE['base_blm']}`
- `theta_min = {DEFAULT_CASE['theta_min']}`
- `theta_max = {DEFAULT_CASE['theta_max']}`
- `sci_alpha = {DEFAULT_CASE['sci_alpha']}`
- `sci_beta = {DEFAULT_CASE['sci_beta']}`
- `sci_group_weights = {json.dumps(DEFAULT_CASE['sci_group_weights'], sort_keys=True)}`

## Stability Checks

- Theta stability check: `{STABILITY_CASES['theta']['setting_label']}`
- Group-weight primary stability check: `{STABILITY_CASES['group_weights_primary']['setting_label']}`
- Group-weight alternate stability check: `{STABILITY_CASES['group_weights_alternate']['setting_label']}`

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
"""
    (OUTPUT_DIR / "summary_notes.md").write_text(notes, encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    calibration_summary, figure_blm = build_calibration_outputs()
    theta_summary = build_family_summary("theta_sensitivity")
    alpha_beta_summary = build_family_summary("alpha_beta_sensitivity")
    group_weight_summary = build_family_summary("group_weight_sensitivity")
    figure_theta = build_figure_family("theta_sensitivity")
    figure_group_weight = build_figure_family("group_weight_sensitivity")

    calibration_summary.to_csv(OUTPUT_DIR / "calibration_summary_table.csv", index=False, encoding="utf-8-sig")
    theta_summary.to_csv(OUTPUT_DIR / "theta_sensitivity_summary_table.csv", index=False, encoding="utf-8-sig")
    alpha_beta_summary.to_csv(OUTPUT_DIR / "alpha_beta_sensitivity_summary_table.csv", index=False, encoding="utf-8-sig")
    group_weight_summary.to_csv(OUTPUT_DIR / "group_weight_sensitivity_summary_table.csv", index=False, encoding="utf-8-sig")
    figure_blm.to_csv(OUTPUT_DIR / "figure_blm_sweep.csv", index=False, encoding="utf-8-sig")
    figure_theta.to_csv(OUTPUT_DIR / "figure_theta_sensitivity.csv", index=False, encoding="utf-8-sig")
    figure_group_weight.to_csv(OUTPUT_DIR / "figure_group_weight_sensitivity.csv", index=False, encoding="utf-8-sig")
    write_summary_notes()

    print(f"Wrote paper outputs to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

1. Files inspected

- [paper_outputs/figure_blm_sweep.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/figure_blm_sweep.csv)
- [paper_outputs/figure_theta_sensitivity.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/figure_theta_sensitivity.csv)
- [paper_outputs/figure_group_weight_sensitivity.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/figure_group_weight_sensitivity.csv)
- [paper_outputs/alpha_beta_sensitivity_summary_table.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/alpha_beta_sensitivity_summary_table.csv)
- [paper_outputs/summary_notes.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/summary_notes.md)
- [HANDOFF.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/HANDOFF.md)

2. Current plotting-ready outputs available

Already plotting-ready:
- [paper_outputs/figure_blm_sweep.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/figure_blm_sweep.csv)
  - has `base_blm`
  - `objective_diff_adaptive_minus_fixed`
  - `patch_diff_adaptive_minus_fixed`
  - `different_cells`
  - `fixed_adaptive_overlap_share`
- [paper_outputs/figure_theta_sensitivity.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/figure_theta_sensitivity.csv)
  - has setting labels and theta values
  - adaptive-minus-fixed deltas
  - overlap and changed-cell counts
- [paper_outputs/figure_group_weight_sensitivity.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/figure_group_weight_sensitivity.csv)
  - has weight-setting labels
  - adaptive-minus-fixed deltas
  - overlap and changed-cell counts

Available but not yet figure-ready:
- [paper_outputs/alpha_beta_sensitivity_summary_table.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/alpha_beta_sensitivity_summary_table.csv)
  - enough to derive a compact figure CSV without rerunning anything

3. Planned figures

1. BLM sweep figure
- Input: [paper_outputs/figure_blm_sweep.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/figure_blm_sweep.csv)
- Recommended design:
  - one multi-panel figure with shared x-axis on log-scale `base_blm`
  - panel A: `objective_diff_adaptive_minus_fixed`
  - panel B: `different_cells`
  - panel C: optional `patch_diff_adaptive_minus_fixed`
- Emphasis:
  - mark `3e-4` as the recommended default with a vertical reference line and label

2. Theta sensitivity figure
- Input: [paper_outputs/figure_theta_sensitivity.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/figure_theta_sensitivity.csv)
- Recommended design:
  - categorical x-axis by `setting_label`
  - two aligned panels or one dot/lollipop figure
  - primary y-metric: `objective_diff_adaptive_minus_fixed`
  - secondary y-metric: `different_cells` or `patch_diff_adaptive_minus_fixed`
- Emphasis:
  - visually highlight default `theta_0.2_1.0`
  - visually highlight preferred stability check `theta_0.3_0.9`

3. Group-weight sensitivity figure
- Input: [paper_outputs/figure_group_weight_sensitivity.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/figure_group_weight_sensitivity.csv)
- Recommended design:
  - categorical x-axis by weight-setting label
  - one compact panel is likely enough because the results are nearly invariant
  - primary y-metric: `objective_diff_adaptive_minus_fixed`
  - optional secondary overlay or annotation for `different_cells`
- Emphasis:
  - baseline vs `compressed_weights`
  - optionally also `transit_heavier`

4. One small cleanup pass
- Add `paper_outputs/figure_alpha_beta_sensitivity.csv` from the existing summary table if we want a complete plotting set.
- If included, the alpha/beta figure would likely be a very small invariance plot with three points showing the same result.

5. Clean up `HANDOFF.md`
- Keep only:
  - current default setting set
  - completed stability checks
  - existence of `paper_outputs/`
  - next recommended step: generate plotting scripts and final figure files
- Remove or compress older repeated explanatory sections if we want it leaner.

4. Proposed files to add or modify

Likely additions:
- `make_paper_figures.py`
- `paper_outputs/figure_alpha_beta_sensitivity.csv`
- figure files, likely under `paper_outputs/figures/`, for example:
  - `paper_outputs/figures/blm_sweep.png`
  - `paper_outputs/figures/blm_sweep.pdf`
  - `paper_outputs/figures/theta_sensitivity.png`
  - `paper_outputs/figures/theta_sensitivity.pdf`
  - `paper_outputs/figures/group_weight_sensitivity.png`
  - `paper_outputs/figures/group_weight_sensitivity.pdf`

Likely modification:
- [HANDOFF.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/HANDOFF.md)

5. Whether alpha/beta should get a figure or remain table-only

It can reasonably remain table-only because the tested alpha/beta settings are solution-invariant in the current results, so a figure may add little beyond showing three overlapping points.

That said, adding `paper_outputs/figure_alpha_beta_sensitivity.csv` is easy and low-risk, so I’d recommend generating the CSV for completeness even if we choose not to render a standalone plotted figure in the manuscript.

6. Risks / assumptions

- The current figure-ready CSVs are sufficient for plotting without rerunning any optimization.
- For the group-weight figure, visual separation is minimal by design, so the figure should be styled to communicate robustness rather than contrast.
- A standalone plotting script should probably use `matplotlib` only, to keep reproduction simple and repo-local.
- `HANDOFF.md` is already much cleaner than before; the cleanup here should be a light trim, not a rewrite.

1. Files changed

- [make_paper_figures.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/make_paper_figures.py)
- [HANDOFF.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/HANDOFF.md)

2. Exact functions/scripts added or modified

Added standalone plotting script [make_paper_figures.py](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/make_paper_figures.py) with:

- `prepare_alpha_beta_figure_csv()`
- `_save(...)`
- `plot_blm_sweep()`
- `_highlight_colors(...)`
- `plot_theta_sensitivity()`
- `plot_group_weight_sensitivity()`
- `main()`

Updated [HANDOFF.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/HANDOFF.md) with a light cleanup so it now focuses on:
- current default setting set
- completed stability checks
- existence of `paper_outputs/`
- next recommended step

3. Figure files generated

Under [paper_outputs/figures](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/figures):

- [blm_sweep.png](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/figures/blm_sweep.png)
- [blm_sweep.pdf](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/figures/blm_sweep.pdf)
- [theta_sensitivity.png](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/figures/theta_sensitivity.png)
- [theta_sensitivity.pdf](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/figures/theta_sensitivity.pdf)
- [group_weight_sensitivity.png](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/figures/group_weight_sensitivity.png)
- [group_weight_sensitivity.pdf](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/figures/group_weight_sensitivity.pdf)

4. CSV files generated or reused

Generated:
- [paper_outputs/figure_alpha_beta_sensitivity.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/figure_alpha_beta_sensitivity.csv)

Reused as plotting inputs:
- [paper_outputs/figure_blm_sweep.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/figure_blm_sweep.csv)
- [paper_outputs/figure_theta_sensitivity.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/figure_theta_sensitivity.csv)
- [paper_outputs/figure_group_weight_sensitivity.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/figure_group_weight_sensitivity.csv)
- [paper_outputs/alpha_beta_sensitivity_summary_table.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/alpha_beta_sensitivity_summary_table.csv)

5. Any derived steps performed

- No optimization was rerun.
- `figure_alpha_beta_sensitivity.csv` was derived directly from [alpha_beta_sensitivity_summary_table.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/alpha_beta_sensitivity_summary_table.csv).
- Matplotlib used a temporary writable cache directory because `/Users/mac/.matplotlib` was not writable. This did not affect figure generation.

6. Whether alpha/beta remained table-only or also got a figure CSV

It remained figure-CSV-only.

I generated [figure_alpha_beta_sensitivity.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/figure_alpha_beta_sensitivity.csv) for completeness, but I did not generate a rendered alpha/beta figure because the three tested settings are visually redundant:
- same objective diff
- same boundary diff
- same patch diff
- same overlap
- same changed-cell count

So alpha/beta is best kept table-only unless a reviewer explicitly asks for an invariance figure.

7. Remaining issues / risks

- The figures are manuscript-ready outputs, but final styling may still need small venue-specific tweaks later.
- If you want a single combined multi-panel figure for the paper instead of three separate figures, that would be a presentation-only follow-up.
- `HANDOFF.md` is now lighter, but it still retains the project summary and method-definition context; that seems appropriate unless you want it made even more skeletal.

8. Review summary for external method check

This step was presentation-only and fully reused existing paper-output CSVs. It did not:
- rerun optimization
- change the scientific method
- touch GUI
- expand into zoned BLM

The plotting outputs now reproducibly reflect the current recommended manuscript framing:
- BLM sweep with log-scale `base_blm` and default `3e-4` marked
- theta sensitivity with default `theta_0.2_1.0` and preferred stability check `theta_0.3_0.9` highlighted
- group-weight sensitivity emphasizing robustness, with `baseline` and `compressed_weights` highlighted and `transit_heavier` available as an alternate robustness check

2 个文件已更改
+188
-90



HANDOFF.md
- more flexibility in narrow inner-bay areas,
- stronger compactness in open waters.

## What has already been implemented

### 1. Adaptive boundary module
A dedicated adaptive boundary module was added and tested.
It computes:
- `theta_i`
- `theta_ij`
- `B_ij_star`

### 2. Scenario engine integration
`scenario_engine.py` was updated so that:
- adaptive BLM can be enabled/disabled,
- effective penalty is `base_blm * B_ij_star`,
- the pipeline no longer multiplies SCI directly into the objective.

### 3. True boundary length
Boundary logic was improved so `B_ij` is now based on true shared boundary length between adjacent polygons, not just adjacency constants.
Corner-only contacts are removed from the effective boundary table.

### 4. SCI refactor
SCI generation was refactored into:
- geometry component,
- human-use pressure component,
- final `SCI_local` combination.

Outputs now include:
- `SCI_geometry`
- `SCI_human_use`
- `SCI_local`
- `SCI` (kept for compatibility / plotting)

### 5. Ecological exclusions
Biodiversity/ecological value/protection categories were explicitly excluded from `SCI_local`.

### 6. Parameter centralization
A single authoritative default parameter source was introduced in:
- `core/method_params.py`

This centralizes defaults for:
- `sci_alpha`
- `sci_beta`
- `sci_geometry_window`
- `sci_sigma_short`
- `sci_sigma_long`
- `theta_min`
- `theta_max`
- `base_blm`
- `sci_group_weights`

### 7. Calibration workflow scaffold
A dedicated calibration/experiment script was added:
- `run_blm_calibration_methods.py`

It currently supports comparison of:
- `fixed_blm`
- `sci_adaptive_blm`

with exports including:
- boundary length,
- patch count,
- largest patch share,
- conflict/cost,
- target achievement,
- objective value,
- baseline overlap.

## Current paper-ready state

- Real macOS + Gurobi calibration succeeds on `msp_state.pkl`.

## Consolidated outputs

Paper-ready summary tables and figure-ready CSVs are now under `paper_outputs/`:
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

## Immediate next priority

- turn the `paper_outputs/` CSVs into manuscript tables/figures,
- turn the `paper_outputs/` CSVs and `paper_outputs/figures/` outputs into final manuscript placement-ready assets,
- keep the current default setting set as the main reported result,
- use `theta_0.3_0.9` and `compressed_weights` as the main robustness checks,
- only if reviewers or paper framing require it, consider a very small extreme-case weight check later.

## Suggested next Codex task

- format the `paper_outputs/` tables into final manuscript-ready presentation form,
- generate plotting code or publication figures directly from the figure-ready CSVs,
- keep method logic frozen unless a presentation-only change is needed.

## Important files to inspect first
- `core/method_params.py`
- `core/kde_engine.py`
- `core/adaptive_boundary.py`
- `core/scenario_engine.py`
- `run_blm_calibration_methods.py`
- relevant tests under `tests/`

## Important constraints
Do not:
- reintroduce biodiversity/ecological layers into `SCI_local`,
- collapse adaptive BLM back into direct SCI weighting in the objective,
- replace true boundary length with adjacency constants,
- make broad GUI changes unless explicitly requested.
- keep alpha/beta table-only unless a reviewer-facing invariance figure is specifically needed,
- only if paper framing requires it later, consider a very small extreme-case weight check.
make_paper_figures.py
"""Create manuscript-ready figures from paper_outputs CSV files."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PAPER_DIR = Path("paper_outputs")
FIG_DIR = PAPER_DIR / "figures"
DEFAULT_BLM = 3e-4
DEFAULT_THETA = "theta_0.2_1.0"
STABILITY_THETA = "theta_0.3_0.9"
DEFAULT_GROUP = "baseline"
STABILITY_GROUP = "compressed_weights"
ALT_GROUP = "transit_heavier"


def prepare_alpha_beta_figure_csv() -> Path:
    src = PAPER_DIR / "alpha_beta_sensitivity_summary_table.csv"
    dst = PAPER_DIR / "figure_alpha_beta_sensitivity.csv"
    df = pd.read_csv(src)
    out = df[
        [
            "setting_label",
            "theta_min",
            "theta_max",
            "sci_alpha",
            "sci_beta",
            "objective_diff_adaptive_minus_fixed",
            "boundary_diff_adaptive_minus_fixed",
            "patch_diff_adaptive_minus_fixed",
            "different_cells",
            "fixed_adaptive_overlap_share",
        ]
    ].copy()
    out.to_csv(dst, index=False, encoding="utf-8-sig")
    return dst


def _save(fig: plt.Figure, stem: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_DIR / f"{stem}.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG_DIR / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_blm_sweep() -> None:
    df = pd.read_csv(PAPER_DIR / "figure_blm_sweep.csv").sort_values("base_blm")
    fig, axes = plt.subplots(3, 1, figsize=(8.2, 9.2), sharex=True)

    series = [
        ("objective_diff_adaptive_minus_fixed", "Objective Diff"),
        ("different_cells", "Different Cells"),
        ("patch_diff_adaptive_minus_fixed", "Patch Diff"),
    ]
    color = "#1f4e79"
    accent = "#c0392b"

    for ax, (col, ylabel) in zip(axes, series):
        ax.plot(df["base_blm"], df[col], marker="o", color=color, linewidth=2)
        ax.axvline(DEFAULT_BLM, color=accent, linestyle="--", linewidth=1.5)
        default_row = df.loc[df["base_blm"] == DEFAULT_BLM].iloc[0]
        ax.scatter([DEFAULT_BLM], [default_row[col]], color=accent, s=55, zorder=3)
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.25)

    axes[-1].set_xscale("log")
    axes[-1].set_xlabel("base_blm (log scale)")
    axes[0].set_title("BLM Sweep: Adaptive minus Fixed")
    axes[0].text(
        DEFAULT_BLM,
        axes[0].get_ylim()[1] * 0.95,
        "default 3e-4",
        color=accent,
        ha="left",
        va="top",
    )
    fig.tight_layout()
    _save(fig, "blm_sweep")


def _highlight_colors(labels: list[str], default_label: str, stability_label: str, alt_label: str | None = None):
    colors = []
    for label in labels:
        if label == default_label:
            colors.append("#c0392b")
        elif label == stability_label:
            colors.append("#1f4e79")
        elif alt_label is not None and label == alt_label:
            colors.append("#6c7a89")
        else:
            colors.append("#b7c4cf")
    return colors


def plot_theta_sensitivity() -> None:
    df = pd.read_csv(PAPER_DIR / "figure_theta_sensitivity.csv")
    labels = df["setting_label"].tolist()
    x = range(len(labels))
    colors = _highlight_colors(labels, DEFAULT_THETA, STABILITY_THETA)

    fig, axes = plt.subplots(2, 1, figsize=(8.5, 7.8), sharex=True)
    axes[0].bar(x, df["objective_diff_adaptive_minus_fixed"], color=colors)
    axes[0].set_ylabel("Objective Diff")
    axes[0].set_title("Theta Sensitivity")
    axes[0].grid(True, axis="y", alpha=0.25)

    axes[1].bar(x, df["different_cells"], color=colors)
    axes[1].set_ylabel("Different Cells")
    axes[1].grid(True, axis="y", alpha=0.25)
    axes[1].set_xticks(list(x))
    axes[1].set_xticklabels(labels, rotation=20, ha="right")

    for ax in axes:
        for idx, label in enumerate(labels):
            if label in {DEFAULT_THETA, STABILITY_THETA}:
                ax.annotate(
                    "default" if label == DEFAULT_THETA else "stability",
                    (idx, ax.patches[idx].get_height()),
                    xytext=(0, 6),
                    textcoords="offset points",
                    ha="center",
                    fontsize=8,
                )

    fig.tight_layout()
    _save(fig, "theta_sensitivity")


def plot_group_weight_sensitivity() -> None:
    df = pd.read_csv(PAPER_DIR / "figure_group_weight_sensitivity.csv")
    labels = df["setting_label"].tolist()
    x = range(len(labels))
    colors = _highlight_colors(labels, DEFAULT_GROUP, STABILITY_GROUP, ALT_GROUP)

    fig, axes = plt.subplots(2, 1, figsize=(8.8, 7.6), sharex=True)
    axes[0].bar(x, df["objective_diff_adaptive_minus_fixed"], color=colors)
    axes[0].set_ylabel("Objective Diff")
    axes[0].set_title("Group-Weight Sensitivity")
    axes[0].grid(True, axis="y", alpha=0.25)

    axes[1].plot(x, df["fixed_adaptive_overlap_share"], marker="o", color="#1f4e79", linewidth=2)
    axes[1].set_ylabel("Overlap Share")
    axes[1].set_ylim(0.9997, 1.0000)
    axes[1].grid(True, axis="y", alpha=0.25)
    axes[1].set_xticks(list(x))
    axes[1].set_xticklabels(labels, rotation=20, ha="right")

    for idx, label in enumerate(labels):
        if label in {DEFAULT_GROUP, STABILITY_GROUP, ALT_GROUP}:
            axes[0].annotate(
                label,
                (idx, axes[0].patches[idx].get_height()),
                xytext=(0, 6),
                textcoords="offset points",
                ha="center",
                fontsize=8,
            )

    fig.tight_layout()
    _save(fig, "group_weight_sensitivity")


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    prepare_alpha_beta_figure_csv()
    plot_blm_sweep()
    plot_theta_sensitivity()
    plot_group_weight_sensitivity()
    print(f"Wrote figures to {FIG_DIR}")


if __name__ == "__main__":
    main()

1. Files inspected

- [paper_outputs/calibration_summary_table.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/calibration_summary_table.csv)
- [paper_outputs/theta_sensitivity_summary_table.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/theta_sensitivity_summary_table.csv)
- [paper_outputs/alpha_beta_sensitivity_summary_table.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/alpha_beta_sensitivity_summary_table.csv)
- [paper_outputs/group_weight_sensitivity_summary_table.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/group_weight_sensitivity_summary_table.csv)
- [paper_outputs/figure_blm_sweep.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/figure_blm_sweep.csv)
- [paper_outputs/figure_theta_sensitivity.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/figure_theta_sensitivity.csv)
- [paper_outputs/figure_group_weight_sensitivity.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/figure_group_weight_sensitivity.csv)
- [paper_outputs/figure_alpha_beta_sensitivity.csv](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/figure_alpha_beta_sensitivity.csv)
- [paper_outputs/summary_notes.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/summary_notes.md)
- [paper_outputs/figures/blm_sweep.png](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/figures/blm_sweep.png)
- [paper_outputs/figures/theta_sensitivity.png](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/figures/theta_sensitivity.png)
- [paper_outputs/figures/group_weight_sensitivity.png](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/figures/group_weight_sensitivity.png)
- [HANDOFF.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/HANDOFF.md)

2. Current paper-facing outputs available

- Clean manuscript tables already exist for:
  - calibration sweep
  - theta sensitivity
  - alpha/beta sensitivity
  - group-weight sensitivity
- Figure-ready CSVs already exist for:
  - BLM sweep
  - theta sensitivity
  - group-weight sensitivity
  - alpha/beta sensitivity
- Rendered figure files already exist for:
  - `blm_sweep`
  - `theta_sensitivity`
  - `group_weight_sensitivity`
- A compact manuscript-orientation note already exists in [summary_notes.md](/Users/mac/Library/CloudStorage/OneDrive-个人/0XMUstart/PHD_thesis/6balikpapanbay/py/paper_outputs/summary_notes.md).

3. Planned writing-support outputs

Under a new folder `paper_outputs/writing_support/`, I’d add:

- `results_summary.md`
  - short prose for:
    - BLM sweep interpretation
    - theta sensitivity interpretation
    - alpha/beta stability interpretation
    - group-weight stability interpretation
- `figure_captions.md`
  - draft caption text for:
    - `blm_sweep`
    - `theta_sensitivity`
    - `group_weight_sensitivity`
- `methods_support.md`
  - concise methods-facing support text for:
    - default parameter settings
    - robustness/stability-check settings
    - which sensitivity families were run
    - which files are paper-facing outputs
- optional markdown tables:
  - `table_calibration_summary.md`
  - `table_theta_sensitivity.md`
  - `table_alpha_beta_sensitivity.md`
  - `table_group_weight_sensitivity.md`

4. Which results will be treated as default vs robustness evidence

Default result:
- `base_blm = 3e-4`
- `theta_min = 0.2`
- `theta_max = 1.0`
- `sci_alpha = 0.5`
- `sci_beta = 0.5`
- `sci_group_weights = {fixed_barriers: 1.0, linear_transit: 0.8, soft_competition: 0.5}`

Robustness evidence:
- BLM sweep:
  - adaptive-vs-fixed divergence emerges by `1e-5`, is clearer at `1e-4`, and is paper-useful at `3e-4`
- Theta:
  - main robustness check: `theta_0.3_0.9`
  - stronger but less moderate case: `theta_0.1_1.0`
- Alpha/beta:
  - treated as stability evidence because tested settings are solution-invariant
- Group weights:
  - main robustness check: `compressed_weights`
  - optional alternate: `transit_heavier`

5. Proposed files to add

- `paper_outputs/writing_support/results_summary.md`
- `paper_outputs/writing_support/figure_captions.md`
- `paper_outputs/writing_support/methods_support.md`
- optionally:
  - `paper_outputs/writing_support/table_calibration_summary.md`
  - `paper_outputs/writing_support/table_theta_sensitivity.md`
  - `paper_outputs/writing_support/table_alpha_beta_sensitivity.md`
  - `paper_outputs/writing_support/table_group_weight_sensitivity.md`

6. Risks / assumptions

- The outputs should stay concise and writing-oriented, not drift into rewriting the paper itself.
- Alpha/beta is likely best written as table-supported invariance text, not emphasized visually.
- Markdown tables may get wide because some rows include full `sci_group_weights`; if needed, those tables should use short setting labels with a legend instead of full inline JSON.
- I’m assuming you want manuscript-support prose and captions in English unless you specify otherwise.

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

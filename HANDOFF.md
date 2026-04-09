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

## Current known blockers / issues

### 1. Windows local Gurobi limit
A full run using the real workspace failed under the Windows environment because the local restricted Gurobi license rejected the large model.

### 2. Small-trial run was not scientifically informative yet
A derived 10x10 trial workspace ran successfully, but all methods and all tested `base_blm` values produced identical results.
This strongly suggests that boundary penalties were not effectively entering the optimizer in that environment.

### 3. Suspected cause
The environment lacked `libpysal`, and the optimizer adjacency path may have skipped BLM-edge construction when `libpysal` was unavailable.
This must be verified and, if needed, replaced with a robust fallback based on existing `row_idx` / `col_idx` Queen-neighborhood logic.

### 4. Export note
GeoPackage export failed in one workflow and was downgraded to GeoJSON fallback. This is acceptable for debugging but should be revisited if paper deliverables require GPKG.

## Immediate next priority
On macOS (with working Gurobi), prioritize:

1. verify optimizer adjacency fallback when `libpysal` is unavailable,
2. rerun a small real-data trial and confirm that fixed vs SCI-adaptive BLM can actually diverge,
3. once divergence is confirmed, run broader `base_blm` calibration,
4. then proceed to sensitivity analysis for:
   - `theta_min/theta_max`
   - `sci_alpha/sci_beta`
   - group weights

## Suggested next Codex task
A good next task is:
- inspect optimizer-edge construction in `scenario_engine.py`,
- ensure fallback Queen adjacency is built without `libpysal`,
- rerun the small calibration trial,
- report whether fixed vs SCI-adaptive BLM now produce different metrics.

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

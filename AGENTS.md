# AGENTS.md

This repository contains a marine spatial planning (MSP) decision-support workflow for Balikpapan Bay.

## Project intent
The core paper contribution is **SCI-driven adaptive BLM** for heterogeneous marine environments with narrow inner bays and open offshore waters.

This repository should prioritize:
1. reproducible method implementation,
2. paper-ready calibration/experiment workflows,
3. minimal, well-scoped code changes.

## Method rules that must stay consistent

### 1) SCI definition
`SCI_local` is **not** a general ecological conflict index.

It is a **spatial crowding coefficient** used operationally as a **proxy for local aggregation resistance** in adaptive BLM.

Current intended formulation:

`SCI_i = norm(alpha * G_i + beta * H_i)`

Where:
- `G_i` = geometric confinement / restrictedness,
- `H_i` = human-use competition pressure,
- biodiversity/ecological protection/value layers must **not** be included in `SCI_local`.

### 2) Geometry component
Prefer a simple, robust openness/confinement implementation:
- use neighborhood marine proportion if available,
- define local openness `O_i`, then `G_i = 1 - O_i`.

Do **not** switch to effective fetch unless explicitly requested.

### 3) Human-use component
Use explicit grouped mapping only. Do **not** use fuzzy category-name matching as the main logic.

Allowed groups:
- `fixed_barriers`
- `linear_transit`
- `soft_competition`
- `excluded_from_sci`

By default, any unknown category should fall into `excluded_from_sci`.

### 4) Ecological exclusions
The following must not enter `SCI_local` unless explicitly redefined by the user:
- ecological protection zones,
- ecological value layers,
- biodiversity features,
- habitat/value targets,
- `Z1_MPZ`,
- `Z5_TZE`,
- similar ecological/value/protection labels.

### 5) Adaptive BLM chain
The adaptive BLM logic must remain:

`SCI_local -> theta_i -> theta_ij -> B_ij_star -> base_blm * B_ij_star`

Definitions:
- `theta_i = theta_min + (1 - SCI_local_i) * (theta_max - theta_min)`
- `theta_ij = (theta_i + theta_j) / 2`
- `B_ij_star = B_ij * theta_ij`

Interpretation:
- higher `SCI_local` = more crowded / constrained,
- therefore smaller `theta_i`,
- therefore weaker local compactness pressure.

### 6) Boundary geometry
`B_ij` must represent **true shared boundary length** between adjacent planning-unit polygons.

If shared boundary length is zero, that pair should not remain in the effective boundary table.

Do not silently fall back to a fake `B_ij = 1.0` when geometry or CRS is invalid. Raise a clear error instead.

### 7) Fixed BLM baseline
The fixed BLM baseline should still use true boundary length:

`base_blm * B_ij`

This matters because earlier code used adjacency constants, but the current method requires geometric boundary meaning.

### 8) Parameters
Use a **single authoritative default source** for method parameters.
Current default source should remain centralized in `core/method_params.py`.

Important configurable parameters include:
- `sci_alpha`
- `sci_beta`
- `sci_geometry_window`
- `sci_sigma_short` (legacy fallback only)
- `sci_sigma_long`
- `theta_min`
- `theta_max`
- `base_blm`
- `sci_group_weights`

If both `sci_geometry_window` and `sci_sigma_short` are present, `sci_geometry_window` must take precedence.

## Development priorities

### Prefer these first
- core method consistency,
- experiment/calibration scripts,
- test coverage,
- reproducibility.

### Avoid broad changes unless requested
- large GUI refactors,
- renaming many files at once,
- adding new ecological logic into SCI,
- changing optimization constraints without explicit approval.

## Experiment rules
Current paper-oriented comparisons should prioritize:
1. fixed BLM,
2. SCI-adaptive BLM.

`zoned BLM` is a useful comparison but may remain a planned extension unless explicitly requested.

Important experiment outputs should include at minimum:
- total boundary length,
- patch count,
- largest patch share,
- total conflict/cost,
- target achievement,
- objective value.

Boundary metrics should use shared-edge geometry.
Patch metrics may use the existing connected-component rule, but the adjacency rule must always be documented explicitly.

## Working style for Codex
For non-trivial tasks, use a two-phase workflow.

### Phase 1
Inspect first, do not edit yet.
Reply with:
1. Files inspected
2. Current logic found
3. Planned changes
4. What will remain unchanged
5. Risks / assumptions

Then stop and wait for approval.

### Phase 2
After approval, edit narrowly and reply with:
1. Files changed
2. Exact functions added/modified
3. Behavior change summary
4. Commands run
5. Test results
6. Remaining issues / risks
7. Review summary for external method check

If relevant, also include short code excerpts for the most critical modified sections.

## Safety against drift
If the current repository state appears inconsistent with the method rules above, prefer:
1. pointing out the inconsistency,
2. proposing a narrow correction plan,
3. waiting for approval before broad edits.

"""Calibration workflow for fixed vs SCI-adaptive BLM experiments.

This script is intentionally separate from the UI. It keeps the optimization
engine unchanged and exports paper-oriented comparison metrics.

Adjacency rules:
- Boundary metrics use shared-edge geometry. Corner-only Queen contacts have
  zero shared-boundary length and are excluded by ``build_raw_boundary_table``.
- Patch metrics use 8-neighbor connected components, matching the earlier
  paper sensitivity helper.
"""

from __future__ import annotations

import argparse
import json
import os
import pickle
import re
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
from scipy.ndimage import label

from core.cost_engine import DEFAULT_CONFLICT_MATRIX_10
from core.method_params import resolve_method_params
from core.scenario_engine import (
    HAS_PY_SAL,
    ZONES_10,
    build_raw_boundary_table,
    resolve_scenario_allocation,
)

DEFAULT_BLM_SWEEP = [0.0, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1]
DEFAULT_ZONE_TARGETS = {"Z2_UIZ": 15, "Z3_PSZ": 15, "Z4_TZ": 15, "Z6_FZT": 15}


def parse_objective_value(report: str) -> float | None:
    """Extract the Gurobi objective from the scenario-engine report string."""
    if not report:
        return None
    for line in reversed(report.splitlines()):
        line_lower = line.lower()
        if "objective" in line_lower or "\u76ee\u6807" in line:
            match = re.search(r":\s*([0-9.+\-eE]+)", line)
            if match:
                return float(match.group(1))
    candidates = re.findall(r":\s*([0-9.+\-eE]+)", report)
    return float(candidates[-1]) if candidates else None


def build_queen_edges(grid_gdf) -> list[tuple[int, int]]:
    """Return Queen candidate edges for metric calculation.

    libpysal is used when available. For regular gridded planning units, the
    row_idx/col_idx fallback preserves Queen candidate generation for tests and
    lightweight experiment environments. Boundary metrics are still computed
    from shared-edge geometry after candidate generation.
    """
    if HAS_PY_SAL:
        import libpysal

        weights = libpysal.weights.contiguity.Queen.from_dataframe(grid_gdf, use_index=False)
        edges = []
        for i, neighbors in weights.neighbors.items():
            for j in neighbors:
                if i < j:
                    edges.append((i, j))
        return edges

    if {"row_idx", "col_idx"}.issubset(grid_gdf.columns):
        by_cell = {
            (int(row.row_idx), int(row.col_idx)): idx
            for idx, row in grid_gdf.reset_index(drop=True).iterrows()
        }
        edges = set()
        for (row_idx, col_idx), idx in by_cell.items():
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    neighbor = by_cell.get((row_idx + dr, col_idx + dc))
                    if neighbor is not None:
                        edges.add(tuple(sorted((idx, neighbor))))
        return sorted(edges)

    raise RuntimeError("libpysal or row_idx/col_idx columns are required to build Queen adjacency metrics.")


def compute_boundary_metrics(grid_gdf, zoning_col: str) -> dict[str, float]:
    """Compute shared-edge boundary metrics for the solved zoning."""
    edges = build_queen_edges(grid_gdf)
    boundary_table = build_raw_boundary_table(grid_gdf, edges)
    boundary_table = boundary_table[boundary_table["B_ij"] > 0.0].copy()

    split_boundary = 0.0
    same_boundary = 0.0
    for row in boundary_table.itertuples(index=False):
        left_zone = grid_gdf.iloc[row.i][zoning_col]
        right_zone = grid_gdf.iloc[row.j][zoning_col]
        if left_zone == right_zone:
            same_boundary += row.B_ij
        else:
            split_boundary += row.B_ij

    total_candidate_boundary = split_boundary + same_boundary
    compactness = (
        same_boundary / total_candidate_boundary if total_candidate_boundary > 0 else None
    )
    return {
        "total_boundary_length": split_boundary,
        "same_zone_boundary_length": same_boundary,
        "candidate_boundary_length": total_candidate_boundary,
        "aggregation_compactness": compactness,
    }


def _zoning_matrix(grid_gdf, zoning_col: str):
    max_r = int(grid_gdf["row_idx"].max())
    max_c = int(grid_gdf["col_idx"].max())
    zones = sorted(str(z) for z in grid_gdf[zoning_col].dropna().unique())
    zone_to_int = {zone: idx + 1 for idx, zone in enumerate(zones)}
    matrix = np.zeros((max_r + 1, max_c + 1), dtype=int)
    matrix[grid_gdf["row_idx"], grid_gdf["col_idx"]] = (
        grid_gdf[zoning_col].astype(str).map(zone_to_int).fillna(0).astype(int)
    )
    return matrix, zone_to_int


def compute_patch_metrics(grid_gdf, zoning_col: str) -> dict[str, float]:
    """Compute patch count and largest-patch share using 8-neighbor components."""
    matrix, zone_to_int = _zoning_matrix(grid_gdf, zoning_col)
    structure = np.ones((3, 3), dtype=int)
    patch_count = 0
    largest_patch = 0
    assigned_cells = int(np.count_nonzero(matrix))

    for zone_value in zone_to_int.values():
        binary = (matrix == zone_value).astype(int)
        labeled, num_features = label(binary, structure=structure)
        patch_count += int(num_features)
        if num_features > 0:
            sizes = np.bincount(labeled.ravel())
            sizes[0] = 0
            largest_patch = max(largest_patch, int(sizes.max()))

    largest_patch_share = largest_patch / assigned_cells if assigned_cells else None
    return {
        "patch_count_8_neighbor": patch_count,
        "largest_patch_share_8_neighbor": largest_patch_share,
    }


def compute_total_conflict_cost(grid_gdf, zoning_col: str) -> float | None:
    """Sum cost_conflict over active non-RZ cells when available."""
    if "cost_conflict" not in grid_gdf.columns:
        return None
    active_mask = ~grid_gdf[zoning_col].astype(str).str.contains("RZ", na=False)
    return float(grid_gdf.loc[active_mask, "cost_conflict"].sum())


def _zone_features_from_mapping(confirmed_mapping: dict[str, list[str]]) -> dict[str, list[str]]:
    zone_features = {zone: [] for zone in ZONES_10}
    for role, cols in confirmed_mapping.items():
        if role in ZONES_10:
            zone_features[role].extend(cols)
        elif role == "L4_???(????)":
            zone_features["Z3_PSZ"].extend(cols)
        elif role == "L1_???????":
            zone_features["Z2_UIZ"].extend(cols)
        elif "??" in role:
            zone_features["Z1_MPZ"].extend(cols)
        elif "??" in role:
            zone_features["Z6_FZT"].extend(cols)
    return zone_features


def compute_target_achievement(grid_gdf, zoning_col: str, zone_targets: dict, confirmed_mapping: dict) -> dict[str, Any]:
    """Report achieved cells against scenario target quotas where derivable."""
    zone_features = _zone_features_from_mapping(confirmed_mapping or {})
    per_zone = {}
    min_ratio = None

    for zone, pct in (zone_targets or {}).items():
        achieved = int((grid_gdf[zoning_col] == zone).sum())
        target_cells = None
        ratio = None
        feats = [col for col in zone_features.get(zone, []) if col in grid_gdf.columns]
        if feats:
            footprint = int((grid_gdf[feats].max(axis=1).fillna(0) > 0).sum())
            target_cells = int(footprint * (float(pct) / 100.0))
            ratio = achieved / target_cells if target_cells > 0 else None
            if ratio is not None:
                min_ratio = ratio if min_ratio is None else min(min_ratio, ratio)
        per_zone[zone] = {
            "target_percent": pct,
            "target_cells": target_cells,
            "achieved_cells": achieved,
            "achievement_ratio": ratio,
        }

    return {"target_min_achievement_ratio": min_ratio, "target_achievement": per_zone}


def compute_solution_metrics(
    grid_gdf,
    zoning_col: str,
    *,
    zone_targets: dict,
    confirmed_mapping: dict,
    report: str,
    baseline_zoning: pd.Series | None = None,
) -> dict[str, Any]:
    """Collect the minimal paper-oriented metrics for one solved zoning."""
    metrics = {}
    metrics.update(compute_boundary_metrics(grid_gdf, zoning_col))
    metrics.update(compute_patch_metrics(grid_gdf, zoning_col))
    metrics["total_conflict_cost"] = compute_total_conflict_cost(grid_gdf, zoning_col)
    metrics["objective_value"] = parse_objective_value(report)
    metrics.update(
        compute_target_achievement(grid_gdf, zoning_col, zone_targets, confirmed_mapping)
    )
    if baseline_zoning is not None:
        metrics["baseline_overlap_share"] = float(
            (grid_gdf[zoning_col].astype(str).reset_index(drop=True) == baseline_zoning.astype(str).reset_index(drop=True)).mean()
        )
    else:
        metrics["baseline_overlap_share"] = None
    return metrics


def run_method_once(
    *,
    grid_gdf,
    scenario_name: str,
    confirmed_mapping: dict,
    zone_targets: dict,
    global_params: dict,
    custom_matrix: dict,
    method_name: str,
    base_blm: float,
):
    """Run one fixed or SCI-adaptive BLM solve."""
    params = resolve_method_params(global_params)
    params.update(global_params)
    params["base_blm"] = base_blm
    if method_name == "fixed_blm":
        params["enable_adaptive_blm"] = False
        params["enable_sci"] = False
    elif method_name == "sci_adaptive_blm":
        params["enable_adaptive_blm"] = True
        params["enable_sci"] = True
    else:
        raise ValueError(f"Unsupported method: {method_name}")

    result_gdf, report = resolve_scenario_allocation(
        grid_gdf=grid_gdf.copy(),
        scenario_name=scenario_name,
        confirmed_mapping=confirmed_mapping,
        locked_features=[],
        zone_targets=zone_targets,
        special_targets={},
        global_params=params,
        custom_matrix=custom_matrix,
    )
    return result_gdf, report, params


def run_calibration_workflow(
    *,
    pkl_path: str,
    output_dir: str | None = None,
    blm_values: list[float] | None = None,
    scenario_name: str = "BLM_Calibration",
    zone_targets: dict | None = None,
) -> pd.DataFrame:
    """Run fixed-BLM recalibration and SCI-adaptive comparison."""
    with open(pkl_path, "rb") as file:
        state = pickle.load(file)

    grid_gdf = state["final_grid"]
    confirmed_mapping = state.get("confirmed_mapping", {})
    global_params = state.get("global_params") or {}
    custom_matrix = state.get("custom_matrix") or DEFAULT_CONFLICT_MATRIX_10
    zone_targets = zone_targets or DEFAULT_ZONE_TARGETS
    blm_values = blm_values or DEFAULT_BLM_SWEEP

    output_dir = output_dir or os.path.join(
        os.path.dirname(pkl_path), f"BLM_Calibration_{datetime.now().strftime('%Y%m%d_%H%M')}"
    )
    os.makedirs(output_dir, exist_ok=True)

    rows = []
    baseline_zoning = None

    for base_blm in blm_values:
        for method_name in ["fixed_blm", "sci_adaptive_blm"]:
            row = {
                "method": method_name,
                "base_blm": base_blm,
                "status": "not_run",
            }
            try:
                result_gdf, report, params = run_method_once(
                    grid_gdf=grid_gdf,
                    scenario_name=scenario_name,
                    confirmed_mapping=confirmed_mapping,
                    zone_targets=zone_targets,
                    global_params=global_params,
                    custom_matrix=custom_matrix,
                    method_name=method_name,
                    base_blm=base_blm,
                )
                row.update(
                    {
                        "theta_min": params.get("theta_min"),
                        "theta_max": params.get("theta_max"),
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
                        baseline_zoning=baseline_zoning,
                    )
                    row.update(metrics)
                    if baseline_zoning is None and method_name == "fixed_blm":
                        baseline_zoning = result_gdf["Scenario_Zoning"].copy()
                    out_path = os.path.join(output_dir, f"{method_name}_blm_{base_blm:g}.gpkg")
                    try:
                        if os.path.exists(out_path):
                            os.remove(out_path)
                        result_gdf.to_file(out_path, driver="GPKG")
                        row["solution_path"] = out_path
                    except Exception as export_exc:
                        fallback_path = os.path.join(output_dir, f"{method_name}_blm_{base_blm:g}.geojson")
                        try:
                            if os.path.exists(fallback_path):
                                os.remove(fallback_path)
                            result_gdf.to_file(fallback_path, driver="GeoJSON")
                            row["solution_path"] = fallback_path
                            row["solution_export_warning"] = f"GPKG export failed; wrote GeoJSON fallback: {export_exc}"
                        except Exception as fallback_exc:
                            row["solution_export_error"] = f"GPKG export failed: {export_exc}; GeoJSON fallback failed: {fallback_exc}"
            except Exception as exc:
                row["status"] = "error"
                row["error"] = str(exc)
            rows.append(row)

    report_df = pd.DataFrame(rows)
    csv_path = os.path.join(output_dir, "blm_calibration_method_comparison.csv")
    report_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    with open(os.path.join(output_dir, "experiment_config.json"), "w", encoding="utf-8") as file:
        json.dump(
            {
                "scenario_name": scenario_name,
                "zone_targets": zone_targets,
                "blm_values": blm_values,
                "methods": ["fixed_blm", "sci_adaptive_blm"],
                "zoned_blm_status": "planned_extension_not_implemented_in_this_step",
                "adjacency_rules": {
                    "boundary_metrics": "shared-edge geometry; B_ij <= 0 excluded",
                    "patch_metrics": "8-neighbor connected components",
                },
            },
            file,
            ensure_ascii=False,
            indent=4,
        )
    print(f"Saved calibration report: {csv_path}")
    return report_df


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pkl", default="msp_state.pkl", help="Path to saved MSP workspace pickle.")
    parser.add_argument("--output-dir", default=None, help="Output directory for CSV and solutions.")
    parser.add_argument(
        "--blm-values",
        default=",".join(str(v) for v in DEFAULT_BLM_SWEEP),
        help="Comma-separated base_blm values to test.",
    )
    parser.add_argument("--scenario-name", default="BLM_Calibration")
    return parser.parse_args()


def main():
    args = parse_args()
    blm_values = [float(value.strip()) for value in args.blm_values.split(",") if value.strip()]
    run_calibration_workflow(
        pkl_path=args.pkl,
        output_dir=args.output_dir,
        blm_values=blm_values,
        scenario_name=args.scenario_name,
    )


if __name__ == "__main__":
    main()

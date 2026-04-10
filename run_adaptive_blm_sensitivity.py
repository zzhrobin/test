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
        "sci_group_weights": json.dumps(params.get("sci_group_weights", {}), sort_keys=True),
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
                    "sci_group_weights": json.dumps(
                        params.get("sci_group_weights", {}),
                        sort_keys=True,
                    ),
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
            "sci_group_weights",
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
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
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

    report_df = pd.concat([theta_df, alpha_beta_df, group_weight_df], ignore_index=True)
    report_df.to_csv(
        os.path.join(output_dir, "adaptive_blm_sensitivity_report.csv"),
        index=False,
        encoding="utf-8-sig",
    )

    theta_compare = build_comparison_table(report_df, "theta_sensitivity")
    alpha_beta_compare = build_comparison_table(report_df, "alpha_beta_sensitivity")
    group_weight_compare = build_comparison_table(report_df, "group_weight_sensitivity")
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
    group_weight_compare.to_csv(
        os.path.join(output_dir, "group_weight_sensitivity_comparison.csv"),
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
                    "group_weight_sensitivity": DEFAULT_GROUP_WEIGHT_SETTINGS,
                },
                "fixed_blm_baseline_reuse": True,
                "methods": ["fixed_blm", "sci_adaptive_blm"],
            },
            file,
            ensure_ascii=False,
            indent=4,
        )

    print(f"Saved sensitivity report: {os.path.join(output_dir, 'adaptive_blm_sensitivity_report.csv')}")
    return report_df, theta_compare, alpha_beta_compare, group_weight_compare


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

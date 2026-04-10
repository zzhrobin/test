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

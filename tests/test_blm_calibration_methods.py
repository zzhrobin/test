import unittest

import geopandas as gpd
import pandas as pd
from shapely.geometry import box

from run_blm_calibration_methods import (
    compute_boundary_metrics,
    compute_patch_metrics,
    compute_solution_metrics,
    compute_target_achievement,
    parse_objective_value,
)


def _metric_grid():
    return gpd.GeoDataFrame(
        {
            "row_idx": [0, 0, 1, 1],
            "col_idx": [0, 1, 0, 1],
            "Scenario_Zoning": ["Z1_MPZ", "Z2_UIZ", "Z1_MPZ", "Z2_UIZ"],
            "feat_uiz": [0, 1, 0, 1],
            "cost_conflict": [1.0, 2.0, 3.0, 4.0],
        },
        geometry=[
            box(0, 0, 1, 1),
            box(1, 0, 2, 1),
            box(0, 1, 1, 2),
            box(1, 1, 2, 2),
        ],
        crs="EPSG:3857",
    )


class BlmCalibrationMethodsTest(unittest.TestCase):
    def test_parse_objective_value(self):
        report = "some log\nFinal objective: 12.34 (Gap: 0.00%)"

        self.assertEqual(parse_objective_value(report), 12.34)

    def test_boundary_metrics_use_shared_edge_geometry(self):
        metrics = compute_boundary_metrics(_metric_grid(), "Scenario_Zoning")

        self.assertEqual(metrics["total_boundary_length"], 2.0)
        self.assertEqual(metrics["same_zone_boundary_length"], 2.0)
        self.assertEqual(metrics["candidate_boundary_length"], 4.0)
        self.assertEqual(metrics["aggregation_compactness"], 0.5)

    def test_patch_metrics_use_8_neighbor_components(self):
        metrics = compute_patch_metrics(_metric_grid(), "Scenario_Zoning")

        self.assertEqual(metrics["patch_count_8_neighbor"], 2)
        self.assertEqual(metrics["largest_patch_share_8_neighbor"], 0.5)

    def test_target_achievement_reports_zone_quota_ratios(self):
        metrics = compute_target_achievement(
            _metric_grid(),
            "Scenario_Zoning",
            {"Z2_UIZ": 50},
            {"Z2_UIZ": ["feat_uiz"]},
        )

        self.assertEqual(metrics["target_achievement"]["Z2_UIZ"]["target_cells"], 1)
        self.assertEqual(metrics["target_achievement"]["Z2_UIZ"]["achieved_cells"], 2)
        self.assertEqual(metrics["target_min_achievement_ratio"], 2.0)

    def test_solution_metrics_include_baseline_overlap(self):
        grid = _metric_grid()
        baseline = pd.Series(["Z1_MPZ", "Z2_UIZ", "Z2_UIZ", "Z2_UIZ"])

        metrics = compute_solution_metrics(
            grid,
            "Scenario_Zoning",
            zone_targets={"Z2_UIZ": 50},
            confirmed_mapping={"Z2_UIZ": ["feat_uiz"]},
            report="Final objective: 9.5",
            baseline_zoning=baseline,
        )

        self.assertEqual(metrics["objective_value"], 9.5)
        self.assertEqual(metrics["total_conflict_cost"], 10.0)
        self.assertEqual(metrics["baseline_overlap_share"], 0.75)


if __name__ == "__main__":
    unittest.main()

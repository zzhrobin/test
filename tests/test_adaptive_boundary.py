import unittest

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from core.adaptive_boundary import (
    apply_adaptive_boundary_multiplier,
    compute_local_theta,
)


def _grid():
    return gpd.GeoDataFrame(
        {
            "cell_id": ["a", "b", "c"],
            "SCI_local": [0.0, 0.5, 1.0],
            "Cost_L_Z1_MPZ": [10.0, 20.0, 30.0],
            "target_hint": [1, 1, 0],
        },
        geometry=[Point(0, 0), Point(1, 0), Point(2, 0)],
        crs="EPSG:4326",
    )


class AdaptiveBoundaryTest(unittest.TestCase):
    def assert_list_almost_equal(self, actual, expected):
        self.assertEqual(len(actual), len(expected))
        for actual_value, expected_value in zip(actual, expected):
            self.assertAlmostEqual(actual_value, expected_value)

    def test_compute_local_theta_uses_inverse_sci_direction(self):
        theta = compute_local_theta(_grid(), theta_min=0.2, theta_max=1.0)

        self.assert_list_almost_equal(theta.tolist(), [1.0, 0.6, 0.2])
        self.assertEqual(theta.name, "theta_i")

    def test_apply_adaptive_boundary_multiplier_returns_scaled_copy(self):
        grid = _grid()
        boundary = pd.DataFrame(
            {
                "i": [0, 1],
                "j": [1, 2],
                "B_ij": [10.0, 20.0],
            }
        )

        result = apply_adaptive_boundary_multiplier(
            grid,
            boundary,
            theta_min=0.2,
            theta_max=1.0,
        )

        self.assert_list_almost_equal(result["theta_ij"].tolist(), [0.8, 0.4])
        self.assert_list_almost_equal(result["B_ij_star"].tolist(), [8.0, 8.0])
        self.assertNotIn("B_ij_star", boundary.columns)
        self.assertNotIn("theta_ij", boundary.columns)
        self.assertNotIn("B_ij_star", grid.columns)
        self.assertEqual(grid["Cost_L_Z1_MPZ"].tolist(), [10.0, 20.0, 30.0])
        self.assertEqual(grid["target_hint"].tolist(), [1, 1, 0])

    def test_apply_adaptive_boundary_multiplier_can_use_explicit_id_column(self):
        boundary = pd.DataFrame(
            {
                "left": ["a", "b"],
                "right": ["c", "c"],
                "B_ij": [5.0, 5.0],
            }
        )

        result = apply_adaptive_boundary_multiplier(
            _grid(),
            boundary,
            theta_min=0.2,
            theta_max=1.0,
            id_col="cell_id",
            left_col="left",
            right_col="right",
        )

        self.assert_list_almost_equal(result["theta_ij"].tolist(), [0.6, 0.4])
        self.assert_list_almost_equal(result["B_ij_star"].tolist(), [3.0, 2.0])

    def test_compute_local_theta_rejects_sci_below_normalized_range(self):
        grid = _grid()
        grid.loc[0, "SCI_local"] = -0.1

        with self.assertRaisesRegex(ValueError, r"\[0, 1\]"):
            compute_local_theta(grid)

    def test_compute_local_theta_rejects_sci_above_normalized_range(self):
        grid = _grid()
        grid.loc[0, "SCI_local"] = 1.1

        with self.assertRaisesRegex(ValueError, r"\[0, 1\]"):
            compute_local_theta(grid)

    def test_apply_adaptive_boundary_multiplier_rejects_unknown_pair_ids(self):
        boundary = pd.DataFrame({"i": [0], "j": [99], "B_ij": [1.0]})

        with self.assertRaisesRegex(ValueError, "99"):
            apply_adaptive_boundary_multiplier(_grid(), boundary)


if __name__ == "__main__":
    unittest.main()

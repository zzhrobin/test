import unittest

import geopandas as gpd
from shapely.geometry import Point

from core.kde_engine import (
    SCI_CATEGORY_GROUPS,
    build_sci_group_assignments,
    calculate_geometry_confinement,
    calculate_human_use_pressure,
    calculate_sci_local,
)


def _grid_2x2():
    return gpd.GeoDataFrame(
        {
            "row_idx": [0, 0, 1, 1],
            "col_idx": [0, 1, 0, 1],
            "fixed": [1.0, 0.0, 0.0, 0.0],
            "linear": [0.0, 1.0, 0.0, 0.0],
            "soft": [0.0, 0.0, 1.0, 0.0],
            "eco": [0.0, 0.0, 0.0, 1.0],
        },
        geometry=[Point(0, 0), Point(1, 0), Point(0, 1), Point(1, 1)],
        crs="EPSG:3857",
    )


def _grid_3x3_with_marine_prop():
    rows, cols, marine = [], [], []
    for r in range(3):
        for c in range(3):
            rows.append(r)
            cols.append(c)
            marine.append(0.0 if (r == 1 and c == 1) else 1.0)
    return gpd.GeoDataFrame(
        {"row_idx": rows, "col_idx": cols, "marine_proportion": marine},
        geometry=[Point(c, r) for r, c in zip(rows, cols)],
        crs="EPSG:3857",
    )


class KdeEngineSciLocalTest(unittest.TestCase):
    def assert_list_almost_equal(self, actual, expected):
        self.assertEqual(len(actual), len(expected))
        for actual_value, expected_value in zip(actual, expected):
            self.assertAlmostEqual(actual_value, expected_value)

    def test_group_assignments_are_explicit_and_exclude_ecology(self):
        mapping = {
            "Z2_UIZ": ["fixed"],
            "Z3_PSZ": ["linear"],
            "Z6_FZT": ["soft"],
            "Z1_MPZ": ["eco"],
            "Z5_TZE": ["tze"],
            "unknown category": ["unknown"],
        }

        assignments = build_sci_group_assignments(mapping)

        self.assertEqual(assignments["fixed"], "fixed_barriers")
        self.assertEqual(assignments["linear"], "linear_transit")
        self.assertEqual(assignments["soft"], "soft_competition")
        self.assertEqual(assignments["eco"], "excluded_from_sci")
        self.assertEqual(assignments["tze"], "excluded_from_sci")
        self.assertEqual(assignments["unknown"], "excluded_from_sci")
        self.assertEqual(SCI_CATEGORY_GROUPS["Z5_TZE"], "excluded_from_sci")

    def test_human_use_pressure_uses_group_weights_and_excludes_ecology(self):
        grid = _grid_2x2()
        mapping = {
            "Z2_UIZ": ["fixed"],
            "Z3_PSZ": ["linear"],
            "Z6_FZT": ["soft"],
            "Z1_MPZ": ["eco"],
        }

        pressure = calculate_human_use_pressure(
            grid,
            mapping,
            sigma=0.0,
            robust_norm=False,
        )

        self.assert_list_almost_equal(pressure.tolist(), [1.0, 0.8, 0.5, 0.0])

    def test_geometry_confinement_prefers_marine_proportion_field(self):
        grid = _grid_3x3_with_marine_prop()

        confinement = calculate_geometry_confinement(grid, window_size=3)

        center_idx = grid[(grid["row_idx"] == 1) & (grid["col_idx"] == 1)].index[0]
        self.assertAlmostEqual(confinement[center_idx], 1.0 / 9.0)

    def test_calculate_sci_local_writes_expected_columns_in_normalized_range(self):
        grid = _grid_2x2()
        mapping = {
            "Z2_UIZ": ["fixed"],
            "Z1_MPZ": ["eco"],
        }

        result = calculate_sci_local(
            grid,
            mapping,
            alpha=0.0,
            beta=1.0,
            geometry_window=1,
            human_sigma=0.0,
            robust_norm=False,
        )

        self.assertIs(result, grid)
        for col in ["SCI_geometry", "SCI_human_use", "SCI_local", "SCI"]:
            self.assertIn(col, result.columns)
        self.assertTrue(((result["SCI_local"] >= 0.0) & (result["SCI_local"] <= 1.0)).all())
        self.assert_list_almost_equal(result["SCI_local"].tolist(), [1.0, 0.0, 0.0, 0.0])
        self.assert_list_almost_equal(result["SCI"].tolist(), [100.0, 0.0, 0.0, 0.0])

    def test_calculate_sci_local_requires_grid_indices(self):
        grid = gpd.GeoDataFrame({"fixed": [1.0]}, geometry=[Point(0, 0)], crs="EPSG:3857")

        with self.assertRaisesRegex(ValueError, "row_idx"):
            calculate_sci_local(grid, {"Z2_UIZ": ["fixed"]})


if __name__ == "__main__":
    unittest.main()

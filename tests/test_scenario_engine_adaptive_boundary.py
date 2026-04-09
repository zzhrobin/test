import unittest

import geopandas as gpd
from shapely.geometry import Point, box

from core.scenario_engine import (
    build_boundary_edges_and_weights,
    build_boundary_weights,
    build_raw_boundary_table,
    resolve_adaptive_blm_enabled,
)


def _polygon_grid():
    return gpd.GeoDataFrame(
        {"SCI_local": [0.0, 0.5, 1.0, 0.5]},
        geometry=[
            box(0, 0, 1, 2),
            box(1, 0, 2, 2),
            box(2, 0, 3, 1),
            box(2, 2, 3, 3),
        ],
        crs="EPSG:3857",
    )


class ScenarioEngineAdaptiveBoundaryTest(unittest.TestCase):
    def assert_list_almost_equal(self, actual, expected):
        self.assertEqual(len(actual), len(expected))
        for actual_value, expected_value in zip(actual, expected):
            self.assertAlmostEqual(actual_value, expected_value)

    def test_raw_boundary_uses_true_shared_boundary_length(self):
        raw_boundary = build_raw_boundary_table(_polygon_grid(), [(0, 1), (1, 2)])

        self.assertGreater(raw_boundary.loc[0, "B_ij"], 0.0)
        self.assertGreater(raw_boundary.loc[0, "B_ij"], raw_boundary.loc[1, "B_ij"])
        self.assert_list_almost_equal(raw_boundary["B_ij"].tolist(), [2.0, 1.0])

    def test_corner_only_queen_neighbor_is_zero_and_filtered_out(self):
        grid = _polygon_grid()
        raw_boundary = build_raw_boundary_table(grid, [(1, 3)])
        edges, weights = build_boundary_edges_and_weights(
            grid,
            [(1, 3)],
            base_blm=3.0,
            enable_adaptive_blm=True,
            theta_min=0.2,
            theta_max=1.0,
        )

        self.assertEqual(raw_boundary.loc[0, "B_ij"], 0.0)
        self.assertEqual(edges, [])
        self.assertEqual(weights, [])

    def test_longer_shared_borders_produce_larger_adaptive_weights(self):
        weights = build_boundary_weights(
            _polygon_grid(),
            [(0, 1), (1, 2)],
            base_blm=3.0,
            enable_adaptive_blm=True,
            theta_min=0.2,
            theta_max=1.0,
        )

        self.assert_list_almost_equal(weights, [4.8, 1.2])
        self.assertGreater(weights[0], weights[1])

    def test_disabled_adaptive_boundary_uses_raw_boundary_lengths(self):
        weights = build_boundary_weights(
            _polygon_grid(),
            [(0, 1), (1, 2)],
            base_blm=3.0,
            enable_adaptive_blm=False,
            theta_min=0.2,
            theta_max=1.0,
        )

        self.assert_list_almost_equal(weights, [6.0, 3.0])

    def test_boundary_length_pipeline_does_not_mutate_grid(self):
        grid = _polygon_grid()
        original_columns = grid.columns.tolist()
        original_sci = grid["SCI_local"].tolist()
        original_geometry = grid.geometry.copy()

        build_boundary_edges_and_weights(
            grid,
            [(0, 1), (1, 2)],
            base_blm=3.0,
            enable_adaptive_blm=True,
            theta_min=0.2,
            theta_max=1.0,
        )

        self.assertEqual(grid.columns.tolist(), original_columns)
        self.assertEqual(grid["SCI_local"].tolist(), original_sci)
        self.assertTrue(grid.geometry.equals(original_geometry))

    def test_boundary_length_rejects_geographic_crs(self):
        grid = _polygon_grid().to_crs("EPSG:4326")

        with self.assertRaisesRegex(ValueError, "geographic CRS"):
            build_raw_boundary_table(grid, [(0, 1)])

    def test_boundary_length_rejects_non_polygon_geometry(self):
        grid = gpd.GeoDataFrame(
            {"SCI_local": [0.0, 0.5]},
            geometry=[Point(0, 0), Point(1, 0)],
            crs="EPSG:3857",
        )

        with self.assertRaisesRegex(ValueError, "non-polygon"):
            build_raw_boundary_table(grid, [(0, 1)])

    def test_enable_adaptive_blm_alias_takes_priority_over_enable_sci(self):
        self.assertFalse(
            resolve_adaptive_blm_enabled(
                {"enable_adaptive_blm": False, "enable_sci": True}
            )
        )
        self.assertTrue(resolve_adaptive_blm_enabled({"enable_sci": True}))
        self.assertFalse(resolve_adaptive_blm_enabled({"enable_sci": False}))


if __name__ == "__main__":
    unittest.main()

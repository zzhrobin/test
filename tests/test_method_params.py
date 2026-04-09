import unittest

from core.method_params import DEFAULT_METHOD_PARAMS, resolve_method_params


class MethodParamsTest(unittest.TestCase):
    def test_geometry_window_takes_precedence_over_legacy_sigma_short(self):
        params = resolve_method_params({"sci_geometry_window": 7, "sci_sigma_short": 2.0})

        self.assertEqual(params["sci_geometry_window"], 7)

    def test_sigma_short_is_backward_compatible_fallback(self):
        params = resolve_method_params({"sci_sigma_short": 4.4})

        self.assertEqual(params["sci_geometry_window"], 4)

    def test_group_weight_overrides_are_merged(self):
        params = resolve_method_params({"sci_group_weights": {"fixed_barriers": 2.0}})

        self.assertEqual(params["sci_group_weights"]["fixed_barriers"], 2.0)
        self.assertEqual(
            params["sci_group_weights"]["linear_transit"],
            DEFAULT_METHOD_PARAMS["sci_group_weights"]["linear_transit"],
        )


if __name__ == "__main__":
    unittest.main()

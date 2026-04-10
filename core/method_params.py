"""Default method parameters for SCI generation and adaptive BLM.

This module is the single authoritative source for scientific default values.
Runtime config and experiment scripts may override these keys without changing
core method logic.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

DEFAULT_METHOD_PARAMS = {
    "sci_alpha": 0.5,
    "sci_beta": 0.5,
    "sci_geometry_window": 3,
    "sci_sigma_short": 3.0,
    "sci_sigma_long": 10.0,
    "theta_min": 0.2,
    "theta_max": 1.0,
    "base_blm": 1.0,
    "sci_group_weights": {
        "fixed_barriers": 1.0,
        "linear_transit": 0.8,
        "soft_competition": 0.5,
        "excluded_from_sci": 0.0,
    },
}

DEFAULT_SCI_GROUP_WEIGHTS = DEFAULT_METHOD_PARAMS["sci_group_weights"]


def resolve_method_params(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Merge method defaults with runtime overrides.

    If the caller provides ``sci_geometry_window``, it takes precedence. The
    legacy ``sci_sigma_short`` is used as the geometry-window fallback only when
    ``sci_geometry_window`` is absent from the caller's overrides.
    """
    overrides = overrides or {}
    params = deepcopy(DEFAULT_METHOD_PARAMS)

    for key, value in overrides.items():
        if key == "sci_group_weights" and isinstance(value, dict):
            params["sci_group_weights"].update(value)
        elif value is not None:
            params[key] = value

    if "sci_geometry_window" in overrides and overrides["sci_geometry_window"] is not None:
        params["sci_geometry_window"] = max(1, int(round(float(overrides["sci_geometry_window"]))))
    elif "sci_sigma_short" in overrides and overrides["sci_sigma_short"] is not None:
        params["sci_geometry_window"] = max(1, int(round(float(overrides["sci_sigma_short"]))))
    else:
        params["sci_geometry_window"] = int(params["sci_geometry_window"])

    return params

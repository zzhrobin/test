import numpy as np
import geopandas as gpd
from scipy.ndimage import gaussian_filter, uniform_filter
from core.method_params import DEFAULT_SCI_GROUP_WEIGHTS, resolve_method_params

SCI_GROUP_WEIGHTS = DEFAULT_SCI_GROUP_WEIGHTS

SCI_CATEGORY_GROUPS = {
    # Fixed barriers and hard constraints.
    "\u57ce\u9547\u548c\u5de5\u4e1a\u7528\u6d77\u533a": "fixed_barriers",
    "Z2_UIZ": "fixed_barriers",
    "\u6c34\u4ea7\u517b\u6b96\u533a": "fixed_barriers",
    "Z8_FZA": "fixed_barriers",
    "\u7279\u6b8a\u5229\u7528\u533a": "fixed_barriers",
    "Z9_SPZ": "fixed_barriers",
    "\U0001f534 \u5f3a\u538b\u529b\u6e90": "fixed_barriers",
    "\u5f3a\u538b\u529b\u6e90": "fixed_barriers",
    "\U0001f512 \u7279\u6b8a\u9501\u5b9a": "fixed_barriers",
    "\u7279\u6b8a\u9501\u5b9a": "fixed_barriers",
    "L1_\u5de5\u4e1a\u77ff\u4e1a\u80fd\u6e90\u533a": "fixed_barriers",
    "L7_\u56fd\u9632\u4e0e\u5b89\u5168\u533a": "fixed_barriers",

    # Linear transit and disturbance corridors.
    "\u6e2f\u53e3\u822a\u9053\u533a": "linear_transit",
    "Z3_PSZ": "linear_transit",
    "\u26a0\ufe0f \u5f71\u54cd\u8981\u7d20": "linear_transit",
    "\u5f71\u54cd\u8981\u7d20": "linear_transit",
    "L4_\u4ea4\u901a\u533a(\u6e2f\u53e3\u7801\u5934)": "linear_transit",
    "L6_\u6d77\u5e95\u7ba1\u9053\u4e0e\u7535\u7f06": "linear_transit",

    # Soft competitive human uses.
    "\u65c5\u6e38\u533a": "soft_competition",
    "Z4_TZ": "soft_competition",
    "\u4f20\u7edf\u6e14\u4e1a\u533a": "soft_competition",
    "Z6_FZT": "soft_competition",
    "\u5546\u4e1a\u6e14\u4e1a\u533a": "soft_competition",
    "Z7_FZC": "soft_competition",
    "\U0001f7e1 \u5f31\u538b\u529b\u6e90": "soft_competition",
    "\u5f31\u538b\u529b\u6e90": "soft_competition",
    "L2_\u5c45\u4f4f\u8d38\u6613\u670d\u52a1\u533a": "soft_competition",
    "L5_\u65c5\u6e38\u533a(\u5c0f\u5c9b\u516c\u56ed)": "soft_competition",

    # Biodiversity/ecological value layers are excluded from adaptive-BLM SCI.
    "\u751f\u6001\u4fdd\u62a4\u548c\u63a7\u5236\u533a": "excluded_from_sci",
    "Z1_MPZ": "excluded_from_sci",
    "\u751f\u6001\u65c5\u6e38\u533a": "excluded_from_sci",
    "Z5_TZE": "excluded_from_sci",
    "\U0001f331 \u9ad8\u4ef7\u503c\u751f\u6001\u76ee\u6807": "excluded_from_sci",
    "\u9ad8\u4ef7\u503c\u751f\u6001\u76ee\u6807": "excluded_from_sci",
    "ECO_\u9ad8\u4ef7\u503c\u751f\u6001\u533a(\u65e0\u8f90\u5c04)": "excluded_from_sci",
    "\u4fdd\u7559\u533a": "excluded_from_sci",
    "Z10_RZ": "excluded_from_sci",
}
MARINE_PROPORTION_COLUMNS = (
    "marine_proportion",
    "marine_prop",
    "marine_ratio",
    "water_proportion",
    "water_prop",
    "water_ratio",
    "sea_proportion",
    "sea_prop",
    "sea_ratio",
    "is_marine",
    "is_water",
)


def calculate_dual_sci(
    grid_gdf: gpd.GeoDataFrame,
    tree_mapping: dict,
    sigma_short: float | None = None,
    sigma_long: float | None = None,
    robust_norm: bool = True,
    *,
    method_params: dict | None = None,
    alpha: float | None = None,
    beta: float | None = None,
    geometry_window: int | None = None,
    human_sigma: float | None = None,
    group_weights: dict | None = None,
) -> gpd.GeoDataFrame:
    """Compatibility wrapper for adaptive-BLM SCI generation.

    The new SCI_local is a local aggregation-resistance proxy built only from
    geometry confinement and human-use competition. Biodiversity and ecological
    value/protection layers are explicitly excluded from SCI_local.
    """
    overrides = dict(method_params or {})
    if sigma_short is not None and "sci_geometry_window" not in overrides:
        overrides["sci_sigma_short"] = sigma_short
    if sigma_long is not None:
        overrides["sci_sigma_long"] = sigma_long
    if alpha is not None:
        overrides["sci_alpha"] = alpha
    if beta is not None:
        overrides["sci_beta"] = beta
    if geometry_window is not None:
        overrides["sci_geometry_window"] = geometry_window
    if human_sigma is not None:
        overrides["sci_sigma_long"] = human_sigma
    if group_weights is not None:
        overrides["sci_group_weights"] = group_weights

    params = resolve_method_params(overrides)
    return calculate_sci_local(
        grid_gdf,
        tree_mapping,
        alpha=params["sci_alpha"],
        beta=params["sci_beta"],
        geometry_window=params["sci_geometry_window"],
        human_sigma=params["sci_sigma_long"],
        group_weights=params["sci_group_weights"],
        robust_norm=robust_norm,
    )


def calculate_sci_local(
    grid_gdf: gpd.GeoDataFrame,
    tree_mapping: dict,
    *,
    alpha: float | None = None,
    beta: float | None = None,
    geometry_window: int | None = None,
    human_sigma: float | None = None,
    group_weights: dict | None = None,
    robust_norm: bool = True,
) -> gpd.GeoDataFrame:
    """Calculate SCI_local = norm(alpha * G_i + beta * H_i)."""
    params = resolve_method_params(
        {
            "sci_alpha": alpha,
            "sci_beta": beta,
            "sci_geometry_window": geometry_window,
            "sci_sigma_long": human_sigma,
            "sci_group_weights": group_weights or {},
        }
    )
    result = grid_gdf
    geometry_confinement = calculate_geometry_confinement(
        result,
        window_size=params["sci_geometry_window"],
    )
    human_pressure = calculate_human_use_pressure(
        result,
        tree_mapping,
        sigma=params["sci_sigma_long"],
        group_weights=params["sci_group_weights"],
        robust_norm=robust_norm,
    )

    combined = params["sci_alpha"] * geometry_confinement + params["sci_beta"] * human_pressure
    sci_local = _normalize_array(combined, robust_norm=robust_norm)

    result["SCI_geometry"] = geometry_confinement
    result["SCI_human_use"] = human_pressure
    result["SCI_local"] = sci_local
    result["SCI"] = sci_local * 100.0
    return result


def calculate_geometry_confinement(
    grid_gdf: gpd.GeoDataFrame,
    *,
    window_size: int = 3,
) -> np.ndarray:
    """Return G_i from neighborhood water openness: G_i = 1 - O_i."""
    _validate_grid_indices(grid_gdf)
    window_size = max(1, int(window_size))
    marine_col = _find_marine_proportion_column(grid_gdf)

    if marine_col is not None:
        openness_source = np.clip(
            grid_gdf[marine_col].fillna(0.0).astype(float).to_numpy(),
            0.0,
            1.0,
        )
    else:
        openness_source = np.ones(len(grid_gdf), dtype=float)

    openness_matrix = _values_to_grid(grid_gdf, openness_source, fill_value=0.0)
    occupancy_matrix = _values_to_grid(grid_gdf, np.ones(len(grid_gdf)), fill_value=0.0)

    neighborhood_sum = uniform_filter(
        openness_matrix,
        size=window_size,
        mode="constant",
        cval=0.0,
    )
    occupancy_sum = uniform_filter(
        occupancy_matrix,
        size=window_size,
        mode="constant",
        cval=0.0,
    )
    openness = np.divide(
        neighborhood_sum,
        occupancy_sum,
        out=np.zeros_like(neighborhood_sum, dtype=float),
        where=occupancy_sum > 0,
    )
    openness_vals = openness[grid_gdf["row_idx"], grid_gdf["col_idx"]]
    return np.clip(1.0 - openness_vals, 0.0, 1.0)


def calculate_human_use_pressure(
    grid_gdf: gpd.GeoDataFrame,
    tree_mapping: dict,
    *,
    sigma: float | None = None,
    group_weights: dict | None = None,
    robust_norm: bool = True,
) -> np.ndarray:
    """Return normalized H_i from explicitly grouped human-use layers."""
    params = resolve_method_params(
        {"sci_sigma_long": sigma, "sci_group_weights": group_weights or {}}
    )
    resolved_group_weights = params["sci_group_weights"]
    _validate_grid_indices(grid_gdf)
    grouped_intensity = np.zeros(len(grid_gdf), dtype=float)
    assignments = build_sci_group_assignments(tree_mapping)

    for col, group_name in assignments.items():
        if group_name == "excluded_from_sci" or col not in grid_gdf.columns:
            continue
        weight = resolved_group_weights[group_name]
        grouped_intensity += grid_gdf[col].fillna(0.0).astype(float).to_numpy() * weight

    intensity_matrix = _values_to_grid(grid_gdf, grouped_intensity, fill_value=0.0)
    smoothed_matrix = gaussian_filter(intensity_matrix, sigma=params["sci_sigma_long"])
    smoothed_vals = smoothed_matrix[grid_gdf["row_idx"], grid_gdf["col_idx"]]
    return _normalize_array(smoothed_vals, robust_norm=robust_norm)


def build_sci_group_assignments(tree_mapping: dict) -> dict:
    """Assign each mapped layer to exactly one SCI group."""
    assignments = {}
    for category_name, cols in tree_mapping.items():
        group_name = SCI_CATEGORY_GROUPS.get(category_name, "excluded_from_sci")
        for col in cols:
            assignments[col] = group_name
    return assignments


def _find_marine_proportion_column(grid_gdf: gpd.GeoDataFrame) -> str | None:
    for col in MARINE_PROPORTION_COLUMNS:
        if col in grid_gdf.columns:
            return col
    return None


def _validate_grid_indices(grid_gdf: gpd.GeoDataFrame) -> None:
    missing_cols = [col for col in ("row_idx", "col_idx") if col not in grid_gdf.columns]
    if missing_cols:
        raise ValueError(
            "SCI_local calculation requires grid index columns: "
            + ", ".join(missing_cols)
        )


def _values_to_grid(
    grid_gdf: gpd.GeoDataFrame,
    values: np.ndarray,
    *,
    fill_value: float,
) -> np.ndarray:
    max_row = int(grid_gdf["row_idx"].max())
    max_col = int(grid_gdf["col_idx"].max())
    matrix = np.full((max_row + 1, max_col + 1), fill_value, dtype=float)
    matrix[grid_gdf["row_idx"], grid_gdf["col_idx"]] = values
    return matrix


def _normalize_array(values: np.ndarray, *, robust_norm: bool) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    v_min = float(np.nanmin(values)) if len(values) else 0.0
    if not len(values):
        v_max = 0.0
    elif robust_norm:
        v_max = float(np.nanpercentile(values, 98))
    else:
        v_max = float(np.nanmax(values))
    if v_max > v_min:
        return np.clip((values - v_min) / (v_max - v_min), 0.0, 1.0)
    return np.zeros_like(values, dtype=float)

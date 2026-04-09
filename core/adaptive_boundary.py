"""Adaptive boundary multipliers for SCI-aware BLM weighting.

This module only transforms an adjacency/boundary table. It expects SCI to have
already been computed outside this module and does not inspect biodiversity
features, target settings, or cost layers.
"""

from __future__ import annotations

from typing import Hashable

import geopandas as gpd
import pandas as pd


DEFAULT_SCI_COL = "SCI_local"
DEFAULT_BOUNDARY_COL = "B_ij"
DEFAULT_OUTPUT_COL = "B_ij_star"


def compute_local_theta(
    grid_gdf: gpd.GeoDataFrame,
    *,
    sci_col: str = DEFAULT_SCI_COL,
    theta_min: float = 0.2,
    theta_max: float = 1.0,
) -> pd.Series:
    """Return local adaptive BLM multipliers indexed like ``grid_gdf``.

    ``SCI_local`` is treated as local aggregation resistance in ``[0, 1]``:
    higher crowding/constrained space receives a smaller multiplier.

    Formula:
        theta_i = theta_min + (1 - SCI_local_i) * (theta_max - theta_min)

    Parameters
    ----------
    grid_gdf:
        Planning-unit GeoDataFrame containing a normalized SCI column.
    sci_col:
        Column with normalized SCI values in ``[0, 1]``.
    theta_min, theta_max:
        Inclusive lower and upper bounds for local BLM multipliers.

    Returns
    -------
    pandas.Series
        Local theta values named ``"theta_i"`` and indexed like ``grid_gdf``.
    """
    _validate_theta_bounds(theta_min, theta_max)
    if sci_col not in grid_gdf.columns:
        raise ValueError(f"Missing required SCI column: {sci_col!r}")

    sci = pd.to_numeric(grid_gdf[sci_col], errors="raise")
    if sci.isna().any():
        raise ValueError(f"{sci_col!r} contains missing values.")
    if ((sci < 0.0) | (sci > 1.0)).any():
        raise ValueError(f"{sci_col!r} must be normalized to the [0, 1] range.")

    theta = theta_min + (1.0 - sci) * (theta_max - theta_min)
    theta.name = "theta_i"
    return theta


def apply_adaptive_boundary_multiplier(
    grid_gdf: gpd.GeoDataFrame,
    boundary_table: pd.DataFrame,
    *,
    theta_min: float = 0.2,
    theta_max: float = 1.0,
    sci_col: str = DEFAULT_SCI_COL,
    id_col: str | None = None,
    left_col: str = "i",
    right_col: str = "j",
    boundary_col: str = DEFAULT_BOUNDARY_COL,
    theta_ij_col: str = "theta_ij",
    output_col: str = DEFAULT_OUTPUT_COL,
) -> pd.DataFrame:
    """Return a boundary table with SCI-adaptive boundary weights.

    For each adjacent pair ``(i, j)``, this function computes:

    ``theta_ij = (theta_i + theta_j) / 2``
    ``B_ij_star = B_ij * theta_ij``

    The input GeoDataFrame and boundary table are not modified. The lookup uses
    ``grid_gdf.index`` by default; pass ``id_col`` when the adjacency table uses
    an explicit planning-unit identifier column instead.

    Parameters
    ----------
    grid_gdf:
        Planning-unit GeoDataFrame with normalized ``SCI_local`` values.
    boundary_table:
        Adjacency/boundary DataFrame with pair columns and a base boundary
        weight column.
    theta_min, theta_max:
        Inclusive lower and upper bounds for local BLM multipliers.
    sci_col:
        Name of the normalized SCI column in ``grid_gdf``.
    id_col:
        Optional planning-unit id column used by ``left_col`` and ``right_col``.
    left_col, right_col:
        Columns in ``boundary_table`` identifying adjacent planning units.
    boundary_col:
        Base boundary weight column, usually ``B_ij``.
    theta_ij_col:
        Name for the pairwise multiplier column added to the result.
    output_col:
        Name for the adaptive boundary weight column added to the result.

    Returns
    -------
    pandas.DataFrame
        A copy of ``boundary_table`` with ``theta_ij`` and ``B_ij_star``.
    """
    _validate_boundary_table(boundary_table, left_col, right_col, boundary_col)

    theta = compute_local_theta(
        grid_gdf,
        sci_col=sci_col,
        theta_min=theta_min,
        theta_max=theta_max,
    )
    theta_lookup = _build_theta_lookup(grid_gdf, theta, id_col)

    result = boundary_table.copy()
    result[boundary_col] = pd.to_numeric(result[boundary_col], errors="raise")
    left_theta = result[left_col].map(theta_lookup)
    right_theta = result[right_col].map(theta_lookup)

    missing_ids = _missing_pair_ids(result, left_col, right_col, left_theta, right_theta)
    if missing_ids:
        raise ValueError(
            "Boundary table references ids not present in the grid: "
            + ", ".join(repr(v) for v in missing_ids)
        )

    result[theta_ij_col] = (left_theta + right_theta) / 2.0
    result[output_col] = result[boundary_col] * result[theta_ij_col]
    return result


def _validate_theta_bounds(theta_min: float, theta_max: float) -> None:
    if theta_min < 0.0:
        raise ValueError("theta_min must be non-negative.")
    if theta_max < theta_min:
        raise ValueError("theta_max must be greater than or equal to theta_min.")


def _validate_boundary_table(
    boundary_table: pd.DataFrame,
    left_col: str,
    right_col: str,
    boundary_col: str,
) -> None:
    missing_cols = [
        col
        for col in (left_col, right_col, boundary_col)
        if col not in boundary_table.columns
    ]
    if missing_cols:
        raise ValueError(
            "Boundary table is missing required columns: "
            + ", ".join(repr(col) for col in missing_cols)
        )


def _build_theta_lookup(
    grid_gdf: gpd.GeoDataFrame,
    theta: pd.Series,
    id_col: str | None,
) -> pd.Series:
    if id_col is None:
        if not grid_gdf.index.is_unique:
            raise ValueError("grid_gdf.index must be unique when id_col is not set.")
        return theta

    if id_col not in grid_gdf.columns:
        raise ValueError(f"Missing required id column: {id_col!r}")
    if grid_gdf[id_col].duplicated().any():
        raise ValueError(f"{id_col!r} must uniquely identify planning units.")

    lookup = pd.Series(theta.to_numpy(), index=grid_gdf[id_col], name=theta.name)
    return lookup


def _missing_pair_ids(
    result: pd.DataFrame,
    left_col: str,
    right_col: str,
    left_theta: pd.Series,
    right_theta: pd.Series,
) -> list[Hashable]:
    left_missing = result.loc[left_theta.isna(), left_col].tolist()
    right_missing = result.loc[right_theta.isna(), right_col].tolist()
    return sorted(set(left_missing + right_missing), key=repr)

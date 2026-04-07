import numpy as np
import geopandas as gpd
from scipy.ndimage import gaussian_filter
from core.gurobi_engine import run_gurobi_optimization

try:
    import libpysal

    HAS_PY_SAL = True
except ImportError:
    HAS_PY_SAL = False

ZONES_10 = [
    "Z1_MPZ",
    "Z2_UIZ",
    "Z3_PSZ",
    "Z4_TZ",
    "Z5_TZE",
    "Z6_FZT",
    "Z7_FZC",
    "Z8_FZA",
    "Z9_SPZ",
    "Z10_RZ",
]


def redistribute_fishery_costs(grid_gdf, locked_indices, unlocked_indices):
    """渔业成本被挤压后的外溢均摊逻辑"""
    for z in ["Z6_FZT", "Z7_FZC", "Z8_FZA"]:
        col_name = f"Cost_L_{z}"
        if col_name not in grid_gdf.columns:
            continue
        displaced_cost = grid_gdf.loc[locked_indices, col_name].sum()
        if displaced_cost > 0:
            valid_mask = (grid_gdf.index.isin(unlocked_indices)) & (
                grid_gdf[col_name] > 0
            )
            valid_idx = grid_gdf[valid_mask].index
            if len(valid_idx) > 0:
                base_sum = grid_gdf.loc[valid_idx, col_name].sum()
                if base_sum > 0:
                    weights = grid_gdf.loc[valid_idx, col_name] / base_sum
                    grid_gdf.loc[valid_idx, col_name] += displaced_cost * weights
                else:
                    grid_gdf.loc[valid_idx, col_name] += displaced_cost / len(valid_idx)
            grid_gdf.loc[locked_indices, col_name] = 0.0
    return grid_gdf


def resolve_scenario_allocation(
    grid_gdf: gpd.GeoDataFrame,
    scenario_name: str,
    confirmed_mapping: dict,
    locked_features: list,
    zone_targets: dict,
    special_targets: dict,
    global_params: dict,
    custom_matrix: dict,
) -> tuple:
    logs = [f"--- 启动 {scenario_name} Gurobi 优化推演 ---"]
    total_cells = len(grid_gdf)
    num_zones = len(ZONES_10)

    # ==========================================
    # 1. 提取精准的空间锁定约束 (【修复】字典去重，防止交叉重叠死锁)
    # ==========================================
    col_to_role = {c: role for role, cols in confirmed_mapping.items() for c in cols}
    locked_dict = {}

    for feat in locked_features:
        if feat in grid_gdf.columns:
            role = col_to_role.get(feat)
            if role and role in ZONES_10:
                target_j = ZONES_10.index(role)
                feat_cells = np.where(grid_gdf[feat].fillna(0).values > 0)[0]
                for cell_idx in feat_cells:
                    # 如果同一个格子被多个不同图层要求锁定，遵循“先到先得”，避免 Gurobi 逻辑崩溃
                    if cell_idx not in locked_dict:
                        locked_dict[cell_idx] = target_j

    locked_data = [(k, v) for k, v in locked_dict.items()]
    locked_indices_set = set(locked_dict.keys())
    unlocked_indices = list(set(range(total_cells)) - locked_indices_set)
    logs.append(f"🔒 成功硬锁定 {len(locked_data)} 个网格 (已自动消解空间重叠冲突)。")

    # ==========================================
    # 2. 渔业平摊与归一化
    # ==========================================
    if locked_indices_set:
        grid_gdf = redistribute_fishery_costs(
            grid_gdf, list(locked_indices_set), unlocked_indices
        )

    raw_cols = [f"Cost_L_{z}" for z in ZONES_10]
    if unlocked_indices:
        all_unlocked_data = grid_gdf.loc[unlocked_indices, raw_cols].values
        global_min, global_max = np.min(all_unlocked_data), np.max(all_unlocked_data)
    else:
        all_raw_data = grid_gdf[raw_cols].values
        global_min, global_max = np.min(all_raw_data), np.max(all_raw_data)

    cost_matrix = np.zeros((total_cells, num_zones))
    scen_prefix = "S_" + scenario_name.split(" ")[0]

    for idx, z in enumerate(ZONES_10):
        col_name = f"Cost_L_{z}"
        if global_max > global_min:
            norm_array = (
                (grid_gdf[col_name].values - global_min) / (global_max - global_min)
            ) * 100.0 + 1.0
        else:
            norm_array = np.ones(total_cells)

        grid_gdf[f"{scen_prefix}_Cost_{z}"] = norm_array
        grid_2d = np.full(
            (grid_gdf["row_idx"].max() + 1, grid_gdf["col_idx"].max() + 1), 101.0
        )
        grid_2d[grid_gdf["row_idx"], grid_gdf["col_idx"]] = norm_array
        sigma_val = 2.0 if "保护" in scenario_name or "现状" in scenario_name else 1.2
        smoothed_2d = gaussian_filter(grid_2d, sigma=sigma_val)
        cost_matrix[:, idx] = (
            0.5 * norm_array
            + 0.5 * smoothed_2d[grid_gdf["row_idx"], grid_gdf["col_idx"]]
        )

    # ==========================================
    # 3. 提取空间配额 (【修复】防爆仓自适应压缩)
    # ==========================================
    zone_features = {z: [] for z in ZONES_10}
    for role, cols in confirmed_mapping.items():
        if role in ZONES_10:
            zone_features[role].extend(cols)
        elif role == "L4_交通区(港口码头)":
            zone_features["Z3_PSZ"].extend(cols)
        elif role == "L1_工业矿业能源区":
            zone_features["Z2_UIZ"].extend(cols)
        elif "生态" in role:
            zone_features["Z1_MPZ"].extend(cols)
        elif "渔业" in role:
            zone_features["Z6_FZT"].extend(cols)

    zone_quotas = []
    total_quota_cells = 0

    for z in ZONES_10:
        if z in ["Z10_RZ", "Z9_SPZ"]:
            zone_quotas.append(0)
            continue

        pct = zone_targets.get(z, 0)
        feats = [f for f in zone_features[z] if f in grid_gdf.columns]
        if feats:
            footprint_mask = grid_gdf[feats].max(axis=1).values > 0
            footprint_area = np.sum(footprint_mask)
            quota = int(footprint_area * (pct / 100.0))
        else:
            quota = 0

        zone_quotas.append(quota)
        total_quota_cells += quota
        if quota > 0:
            logs.append(
                f"🎯 [{z.split('_')[1]}] 现有足迹 {footprint_area}，提取配额: {quota} 单元"
            )

    # 核心容量检查：如果总配额超过了可用海域，按比例压缩，强行保住模型不崩！
    if total_quota_cells > (total_cells - len(locked_data)):
        logs.append(
            f"⚠️ 警告: 总配额({total_quota_cells}) 超过剩余可用空间！启用自适应压缩..."
        )
        safe_ratio = (total_cells - len(locked_data)) * 0.95 / total_quota_cells
        zone_quotas = [int(q * safe_ratio) for q in zone_quotas]

    # ==========================================
    # 4. 构建空间相邻拓扑 (【修复】FutureWarning)
    # ==========================================
    edges, weights = [], []
    blm_base = global_params.get("base_blm", 1.0)
    enable_sci = global_params.get("enable_sci", True)

    if HAS_PY_SAL and blm_base > 0:
        logs.append("🌐 正在提取空间邻接矩阵 (Queen Contiguity)...")
        # 加上 use_index=False，彻底屏蔽底层警告
        w = libpysal.weights.contiguity.Queen.from_dataframe(grid_gdf, use_index=False)
        sci_col = "Conflict_Index" if "Conflict_Index" in grid_gdf.columns else None

        for i, neighbors in w.neighbors.items():
            for k in neighbors:
                if i < k:
                    edges.append((i, k))
                    if enable_sci and sci_col:
                        sci_w = (
                            (grid_gdf.at[i, sci_col] + grid_gdf.at[k, sci_col])
                            / 2.0
                            / 100.0
                        )
                        weights.append(blm_base * sci_w)
                    else:
                        weights.append(blm_base)
        logs.append(f"🔗 连片拓扑提取完成，共 {len(edges)} 条相交边界参与惩罚计算。")

    # ==========================================
    # 5. 正式调起 Gurobi
    # ==========================================
    conflict_matrix_2d = np.zeros((num_zones, num_zones))
    for i, z1 in enumerate(ZONES_10):
        for j, z2 in enumerate(ZONES_10):
            conflict_matrix_2d[i, j] = custom_matrix.get(z1, {}).get(z2, 0.0)

    is_mandatory = global_params.get("is_mandatory", True)
    time_limit = global_params.get("gurobi_time", 300)
    mip_gap = global_params.get("gurobi_gap", 0.05)

    logs.append(f"⚙️ 启动 MIP Gurobi (TimeLimit={time_limit}s, Gap={mip_gap}) ...")
    g_solution, g_msg = run_gurobi_optimization(
        total_cells,
        num_zones,
        cost_matrix,
        zone_quotas,
        locked_data,
        edges,
        weights,
        conflict_matrix_2d,
        time_limit,
        mip_gap,
        is_mandatory,
    )
    logs.append(g_msg)

    if g_solution is not None:
        final_zones = []
        for i in g_solution:
            if i == -1:
                final_zones.append("Z10_RZ")
            else:
                final_zones.append(ZONES_10[i])
        grid_gdf["Scenario_Zoning"] = final_zones
    else:
        grid_gdf["Scenario_Zoning"] = "Error_Infeasible"

    return grid_gdf, "\n".join(logs)

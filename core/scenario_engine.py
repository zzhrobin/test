import numpy as np
import geopandas as gpd
from core.gurobi_engine import run_gurobi_optimization
from scipy.ndimage import gaussian_filter  # <--- 必须补上这句！

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
    # 1. 跨列全局归一化 (防爆破：剔除锁定格子)
    # ==========================================
    locked_indices_set = set()
    for feat in locked_features:
        if feat in grid_gdf.columns:
            locked_indices_set.update(np.where(grid_gdf[feat].fillna(0).values > 0)[0])

    unlocked_indices = list(set(range(total_cells)) - locked_indices_set)
    raw_cols = [f"Cost_L_{z}" for z in ZONES_10]

    # 仅使用未锁定的自由网格来寻找全域极大极小值
    if unlocked_indices:
        all_unlocked_data = grid_gdf.loc[unlocked_indices, raw_cols].values
        global_min, global_max = np.min(all_unlocked_data), np.max(all_unlocked_data)
    else:
        all_raw_data = grid_gdf[raw_cols].values
        global_min, global_max = np.min(all_raw_data), np.max(all_raw_data)

    logs.append(
        f"🔍 剔除锁定极值后，提取全域本底落差: Min={global_min:.2f}, Max={global_max:.2f}"
    )

    cost_matrix = np.zeros((total_cells, num_zones))
    norm_costs = {}
    for idx, z in enumerate(ZONES_10):
        col_name = f"Cost_L_{z}"
        if global_max > global_min:
            norm_array = (
                (grid_gdf[col_name].values - global_min) / (global_max - global_min)
            ) * 100.0 + 1.0
        else:
            norm_array = np.ones(total_cells)
        norm_costs[z] = norm_array
        grid_gdf[f"Norm_Cost_{z}"] = norm_array

    # 边界集聚平滑 (模拟 BLM)
    max_r = grid_gdf["row_idx"].max()
    max_c = grid_gdf["col_idx"].max()
    for idx, z in enumerate(ZONES_10):
        grid_2d = np.full((max_r + 1, max_c + 1), 101.0)
        grid_2d[grid_gdf["row_idx"], grid_gdf["col_idx"]] = norm_costs[z]
        sigma_val = 2.0 if "保护" in scenario_name or "现状" in scenario_name else 1.2
        smoothed_2d = gaussian_filter(grid_2d, sigma=sigma_val)
        blended = (
            0.5 * norm_costs[z]
            + 0.5 * smoothed_2d[grid_gdf["row_idx"], grid_gdf["col_idx"]]
        )
        cost_matrix[:, idx] = blended

    # ==========================================
    # 2. 基于“本底面积足迹”的相对配额提取
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
    for z in ZONES_10:
        if z == "Z10_RZ":
            zone_quotas.append(0)  # 核心逻辑：保留区没有主动配额，全靠留白！
            continue

        pct = zone_targets.get(z, 0)
        feats = [f for f in zone_features[z] if f in grid_gdf.columns]
        if feats:
            # 算出该类型要素原本总共占据了多少个网格 (Footprint)
            footprint_mask = grid_gdf[feats].max(axis=1).values > 0
            footprint_area = np.sum(footprint_mask)
            # 从原本的 100% 占地中，按比例提取目标网格数
            quota = int(footprint_area * (pct / 100.0))
        else:
            quota = 0

        zone_quotas.append(quota)
        if quota > 0:
            logs.append(
                f"🎯 [{z.split('_')[1]}] 现有足迹 {footprint_area} 个网格，提取目标配额: {quota} 个"
            )

    # 3. 提取空间相邻边 (Edges) 与动态 SCI 权重
    edges, weights = [], []

    # ==========================================
    # 补充丢失的 Gurobi 调起逻辑
    # ==========================================
    is_mandatory = global_params.get("is_mandatory", True)
    time_limit = global_params.get("gurobi_time", 300)
    mip_gap = global_params.get("gurobi_gap", 0.05)

    # 转换冲突矩阵为二维数组
    conflict_matrix_2d = np.zeros((num_zones, num_zones))
    for i, z1 in enumerate(ZONES_10):
        for j, z2 in enumerate(ZONES_10):
            conflict_matrix_2d[i, j] = custom_matrix.get(z1, {}).get(z2, 0.0)

    # 生成锁定网格数据
    locked_data = []
    for feat in locked_features:
        if feat in grid_gdf.columns:
            target_zone = next((z for z in ZONES_10 if z.split("_")[1] in feat), None)
            if target_zone:
                target_j = ZONES_10.index(target_zone)
                feat_cells = np.where(grid_gdf[feat].fillna(0).values > 0)[0]
                for cell_idx in feat_cells:
                    locked_data.append((cell_idx, target_j))

    logs.append(f"⚙️ 启动 Gurobi (TimeLimit={time_limit}s, Gap={mip_gap}) ...")
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
    # ==========================================

    if g_solution is not None:
        final_zones = []
        for i in g_solution:
            if i == -1:
                final_zones.append(
                    "Z10_RZ"
                )  # 核心：Gurobi没分配的留白网格，自动归入保留区！
            else:
                final_zones.append(ZONES_10[i])
        grid_gdf["Scenario_Zoning"] = final_zones
    else:
        grid_gdf["Scenario_Zoning"] = "Error_Infeasible"

    return grid_gdf, "\n".join(logs)

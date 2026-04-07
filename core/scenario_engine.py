import numpy as np
import geopandas as gpd
from scipy.ndimage import gaussian_filter
from core.gurobi_engine import run_gurobi_optimization

# 确保安装了 libpysal： pip install libpysal
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

        # 提取被锁定/挤压区域的渔业总成本
        displaced_cost = grid_gdf.loc[locked_indices, col_name].sum()
        if displaced_cost > 0:
            # 找到可以接受均摊的自由网格 (原本就有该渔业潜力的)
            valid_mask = (grid_gdf.index.isin(unlocked_indices)) & (
                grid_gdf[col_name] > 0
            )
            valid_idx = grid_gdf[valid_mask].index

            if len(valid_idx) > 0:
                base_sum = grid_gdf.loc[valid_idx, col_name].sum()
                if base_sum > 0:
                    # 按原本的适宜性权重分配
                    weights = grid_gdf.loc[valid_idx, col_name] / base_sum
                    grid_gdf.loc[valid_idx, col_name] += displaced_cost * weights
                else:
                    grid_gdf.loc[valid_idx, col_name] += displaced_cost / len(valid_idx)

            # 将被锁定区的该项渔业成本清零
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
    # 1. 提取精准的空间锁定约束
    # ==========================================
    col_to_role = {c: role for role, cols in confirmed_mapping.items() for c in cols}
    locked_data = []
    locked_indices_set = set()

    for feat in locked_features:
        if feat in grid_gdf.columns:
            # 直接使用预检时的映射字典进行匹配
            role = col_to_role.get(feat)
            if role and role in ZONES_10:
                target_j = ZONES_10.index(role)
                feat_cells = np.where(grid_gdf[feat].fillna(0).values > 0)[0]
                for cell_idx in feat_cells:
                    locked_data.append((cell_idx, target_j))
                    locked_indices_set.add(cell_idx)

    unlocked_indices = list(set(range(total_cells)) - locked_indices_set)
    logs.append(f"🔒 成功硬锁定 {len(locked_data)} 个既定事实网格。")

    # ==========================================
    # 2. 渔业成本平摊与全域极值归一化
    # ==========================================
    # 执行渔业挤压成本均摊
    if locked_indices_set:
        grid_gdf = redistribute_fishery_costs(
            grid_gdf, list(locked_indices_set), unlocked_indices
        )
        logs.append("🌊 渔业成本挤压与外溢平摊完成。")

    raw_cols = [f"Cost_L_{z}" for z in ZONES_10]

    if unlocked_indices:
        all_unlocked_data = grid_gdf.loc[unlocked_indices, raw_cols].values
        global_min, global_max = np.min(all_unlocked_data), np.max(all_unlocked_data)
    else:
        all_raw_data = grid_gdf[raw_cols].values
        global_min, global_max = np.min(all_raw_data), np.max(all_raw_data)

    cost_matrix = np.zeros((total_cells, num_zones))

    # 在这个情景下，生成专属的归一化属性列
    scen_prefix = "S_" + scenario_name.split(" ")[0]  # e.g., S_开发优先
    for idx, z in enumerate(ZONES_10):
        col_name = f"Cost_L_{z}"
        if global_max > global_min:
            norm_array = (
                (grid_gdf[col_name].values - global_min) / (global_max - global_min)
            ) * 100.0 + 1.0
        else:
            norm_array = np.ones(total_cells)

        # 保存专属属性，供用户在属性表中单独查看该情景的博弈成本
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
    # 3. 提取空间配额 (RZ和SPZ绝对不参与比例)
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
        if z in ["Z10_RZ", "Z9_SPZ"]:
            zone_quotas.append(0)
            continue

        pct = zone_targets.get(z, 0)
        feats = [f for f in zone_features[z] if f in grid_gdf.columns]
        if feats:
            footprint_mask = grid_gdf[feats].max(axis=1).values > 0
            quota = int(np.sum(footprint_mask) * (pct / 100.0))
        else:
            quota = 0
        zone_quotas.append(quota)

    # ==========================================
    # 4. 构建空间相邻拓扑 (激活 BLM 的关键)
    # ==========================================
    edges, weights = [], []
    blm_base = global_params.get("base_blm", 1.0)
    if HAS_PY_SAL and blm_base > 0:
        logs.append("🌐 正在提取空间邻接矩阵 (Queen Contiguity)...")
        w = libpysal.weights.contiguity.Queen.from_dataframe(grid_gdf)
        sci_col = "Conflict_Index" if "Conflict_Index" in grid_gdf.columns else None

        for i, neighbors in w.neighbors.items():
            for k in neighbors:
                if i < k:
                    edges.append((i, k))
                    if sci_col:
                        sci_w = (
                            (grid_gdf.at[i, sci_col] + grid_gdf.at[k, sci_col])
                            / 2.0
                            / 100.0
                        )
                        weights.append(blm_base * sci_w)
                    else:
                        weights.append(blm_base)
        logs.append(f"🔗 连片拓扑提取完成，共 {len(edges)} 条相交边界参与惩罚计算。")
    else:
        logs.append("⚠️ libpysal 未安装或 BLM 设为 0，将不执行连片惩罚！")

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

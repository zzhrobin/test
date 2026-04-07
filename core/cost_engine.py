import numpy as np
import geopandas as gpd
import itertools
from scipy.ndimage import distance_transform_edt

ZONES_10 = ['Z1_MPZ', 'Z2_UIZ', 'Z3_PSZ', 'Z4_TZ', 'Z5_TZE', 'Z6_FZT', 'Z7_FZC', 'Z8_FZA', 'Z9_SPZ', 'Z10_RZ']

ZONE_NAME_MAP = {
    'Z1_MPZ': "生态保护和控制区", 'Z2_UIZ': "城镇和工业用海区", 'Z3_PSZ': "港口航道区",
    'Z4_TZ':  "旅游区", 'Z5_TZE': "生态旅游区", 'Z6_FZT': "传统渔业区",
    'Z7_FZC': "商业渔业区", 'Z8_FZA': "水产养殖区", 'Z9_SPZ': "特殊利用区", 'Z10_RZ': "保留区"
}

DEFAULT_CONFLICT_MATRIX_10 = {
    'Z1_MPZ': {'Z1_MPZ':0.0, 'Z2_UIZ':1.0, 'Z3_PSZ':1.0, 'Z4_TZ':0.3, 'Z5_TZE':0.1, 'Z6_FZT':0.2, 'Z7_FZC':0.8, 'Z8_FZA':0.8, 'Z9_SPZ':0.9, 'Z10_RZ':0.1},
    'Z2_UIZ': {'Z1_MPZ':1.0, 'Z2_UIZ':0.0, 'Z3_PSZ':0.1, 'Z4_TZ':0.8, 'Z5_TZE':0.9, 'Z6_FZT':0.9, 'Z7_FZC':0.6, 'Z8_FZA':0.9, 'Z9_SPZ':0.2, 'Z10_RZ':0.4},
    'Z3_PSZ': {'Z1_MPZ':1.0, 'Z2_UIZ':0.1, 'Z3_PSZ':0.0, 'Z4_TZ':0.7, 'Z5_TZE':1.0, 'Z6_FZT':1.0, 'Z7_FZC':0.7, 'Z8_FZA':1.0, 'Z9_SPZ':0.3, 'Z10_RZ':0.5},
    'Z4_TZ':  {'Z1_MPZ':0.3, 'Z2_UIZ':0.8, 'Z3_PSZ':0.7, 'Z4_TZ':0.0, 'Z5_TZE':0.2, 'Z6_FZT':0.3, 'Z7_FZC':0.6, 'Z8_FZA':0.5, 'Z9_SPZ':0.8, 'Z10_RZ':0.3},
    'Z5_TZE': {'Z1_MPZ':0.1, 'Z2_UIZ':0.9, 'Z3_PSZ':1.0, 'Z4_TZ':0.2, 'Z5_TZE':0.0, 'Z6_FZT':0.2, 'Z7_FZC':0.8, 'Z8_FZA':0.4, 'Z9_SPZ':0.8, 'Z10_RZ':0.2},
    'Z6_FZT': {'Z1_MPZ':0.2, 'Z2_UIZ':0.9, 'Z3_PSZ':1.0, 'Z4_TZ':0.3, 'Z5_TZE':0.2, 'Z6_FZT':0.0, 'Z7_FZC':0.6, 'Z8_FZA':0.3, 'Z9_SPZ':0.7, 'Z10_RZ':0.2},
    'Z7_FZC': {'Z1_MPZ':0.8, 'Z2_UIZ':0.6, 'Z3_PSZ':0.7, 'Z4_TZ':0.6, 'Z5_TZE':0.8, 'Z6_FZT':0.6, 'Z7_FZC':0.0, 'Z8_FZA':0.7, 'Z9_SPZ':0.7, 'Z10_RZ':0.3},
    'Z8_FZA': {'Z1_MPZ':0.8, 'Z2_UIZ':0.9, 'Z3_PSZ':1.0, 'Z4_TZ':0.5, 'Z5_TZE':0.4, 'Z6_FZT':0.3, 'Z7_FZC':0.7, 'Z8_FZA':0.0, 'Z9_SPZ':0.9, 'Z10_RZ':0.3},
    'Z9_SPZ': {'Z1_MPZ':0.9, 'Z2_UIZ':0.2, 'Z3_PSZ':0.3, 'Z4_TZ':0.8, 'Z5_TZE':0.8, 'Z6_FZT':0.7, 'Z7_FZC':0.7, 'Z8_FZA':0.9, 'Z9_SPZ':0.0, 'Z10_RZ':0.1},
    'Z10_RZ': {'Z1_MPZ':0.1, 'Z2_UIZ':0.4, 'Z3_PSZ':0.5, 'Z4_TZ':0.3, 'Z5_TZE':0.2, 'Z6_FZT':0.2, 'Z7_FZC':0.3, 'Z8_FZA':0.3, 'Z9_SPZ':0.1, 'Z10_RZ':0.0}
}

LAND_SEA_PENALTY = {
    'L1_工业矿业能源区': {'MPZ':1.0, 'TZE':1.0, 'FZT':0.9, 'FZA':0.9, 'TZ':0.8, 'FZC':0.6, 'UIZ':0.0, 'PSZ':0.1, 'SPZ':0.2, 'RZ':0.4},
    'L2_居住贸易服务区': {'MPZ':0.8, 'TZE':0.7, 'FZT':0.5, 'FZA':0.6, 'TZ':0.4, 'FZC':0.5, 'UIZ':0.3, 'PSZ':0.3, 'SPZ':0.4, 'RZ':0.3},
    'L3_农业与生产林':  {'MPZ':0.8, 'TZE':0.6, 'FZT':0.5, 'FZA':0.8, 'TZ':0.6, 'FZC':0.5, 'UIZ':0.3, 'PSZ':0.3, 'SPZ':0.4, 'RZ':0.3},
    'L4_交通区(港口码头)': {'MPZ':0.9, 'TZE':0.8, 'FZT':0.8, 'FZA':1.0, 'TZ':0.7, 'FZC':0.6, 'UIZ':0.1, 'PSZ':0.0, 'SPZ':0.3, 'RZ':0.4},
    'L5_旅游区(小岛公园)': {'MPZ':0.4, 'TZE':0.1, 'FZT':0.3, 'FZA':0.5, 'TZ':0.0, 'FZC':0.4, 'UIZ':0.8, 'PSZ':0.7, 'SPZ':0.8, 'RZ':0.2},
    'L6_海底管道与电缆': {'MPZ':0.9, 'TZE':0.8, 'FZT':0.8, 'FZA':1.0, 'TZ':0.7, 'FZC':0.6, 'UIZ':0.1, 'PSZ':0.0, 'SPZ':0.3, 'RZ':0.4}, 
    'L7_国防与安全区':  {'MPZ':0.5, 'TZE':1.0, 'FZT':1.0, 'FZA':1.0, 'TZ':1.0, 'FZC':1.0, 'UIZ':0.7, 'PSZ':0.7, 'SPZ':0.5, 'RZ':0.5}
}

RADIATION_DISTANCES = {
    'L1_工业矿业能源区': 1000.0, 'L2_居住贸易服务区': 1500.0, 'L3_农业与生产林': 2000.0,
    'L4_交通区(港口码头)': 1000.0, 'L5_旅游区(小岛公园)': 100.0, 'L6_海底管道与电缆': 750.0, 'L7_国防与安全区': 1000.0
}

def calculate_fishery_cost(grid_gdf, villages_gdf, tree_mapping, range_km=15.0, trad_col=None, comm_col=None, aqua_col=None):
    grid_gdf['cost_fishery_T'] = 0.0; grid_gdf['cost_fishery_C'] = 0.0; grid_gdf['cost_fishery_A'] = 0.0
    logs = []; fzt_cols, fzc_cols, fza_cols = [], [], []
    
    if trad_col and trad_col != "[使用树形分类]": fzt_cols = [trad_col]
    else:
        for k, v in tree_mapping.items():
            if "传统渔业" in k: fzt_cols.extend(v)
            
    if comm_col and comm_col != "[使用树形分类]": fzc_cols = [comm_col]
    else:
        for k, v in tree_mapping.items():
            if "商业渔业" in k: fzc_cols.extend(v)

    if aqua_col and aqua_col != "[使用树形分类]": fza_cols = [aqua_col]
    else:
        for k, v in tree_mapping.items():
            if "水产养殖" in k: fza_cols.extend(v)
        
    valid_fzt = [c for c in fzt_cols if c in grid_gdf.columns]
    base_fzt_intensity = grid_gdf[valid_fzt].max(axis=1).values if valid_fzt else np.zeros(len(grid_gdf))
    
    valid_fzc = [c for c in fzc_cols if c in grid_gdf.columns]
    base_fzc_intensity = grid_gdf[valid_fzc].max(axis=1).values if valid_fzc else np.zeros(len(grid_gdf))

    valid_fza = [c for c in fza_cols if c in grid_gdf.columns]
    base_fza_intensity = grid_gdf[valid_fza].max(axis=1).values if valid_fza else np.zeros(len(grid_gdf))
    
    decay_coefficient = np.zeros(len(grid_gdf))
    if villages_gdf is not None and not villages_gdf.empty:
        grid_m = grid_gdf.to_crs(epsg=3857); vil_m = villages_gdf.to_crs(epsg=3857)
        dists = grid_m.geometry.distance(vil_m.geometry.unary_union)
        range_m = range_km * 1000.0
        decay_coefficient = np.clip((range_m - dists) / range_m, 0.0, 1.0)

    # 核心修正：绝对保留原始计算强度，不作任何归一化！
    grid_gdf['cost_fishery_T'] = base_fzt_intensity * decay_coefficient
    grid_gdf['cost_fishery_C'] = base_fzc_intensity
    grid_gdf['cost_fishery_A'] = base_fza_intensity
        
    grid_gdf['cost_fishery_merged'] = grid_gdf['cost_fishery_T'] + grid_gdf['cost_fishery_C'] + grid_gdf['cost_fishery_A']
    
    logs.append(f"🗺️ 三大渔业基础强度保留了绝对原始量级（未归一化），直接进入矩阵计算！")
    return grid_gdf, "\n".join(logs)

def _get_distance_penalty(grid_gdf, target_cols, influence_dist, grid_size):
    if not target_cols: return np.zeros(len(grid_gdf))
    valid_cols = [c for c in target_cols if c in grid_gdf.columns]
    if not valid_cols: return np.zeros(len(grid_gdf))
    presence = grid_gdf[valid_cols].max(axis=1).values
    max_r, max_c = grid_gdf['row_idx'].max(), grid_gdf['col_idx'].max()
    mask = np.ones((max_r + 1, max_c + 1))
    mask[grid_gdf['row_idx'], grid_gdf['col_idx']] = np.where(presence > 0, 0, 1)
    dist_matrix = distance_transform_edt(mask) * grid_size
    flat_dist = dist_matrix[grid_gdf['row_idx'], grid_gdf['col_idx']]
    
    # 核心修正：不再限制在 [0, 1] 之间。原始距离衰减乘数直接输出！
    penalty_array = np.clip(1.0 - (flat_dist / influence_dist), 0.0, 1.0)
    return penalty_array

def calculate_current_conflict(grid_gdf: gpd.GeoDataFrame, confirmed_mapping: dict, custom_matrix: dict = None) -> tuple:
    """【解耦新增】：纯粹展示现状要素重叠的矛盾热力图，不涉及未来成本"""
    matrix_to_use = custom_matrix if custom_matrix else DEFAULT_CONFLICT_MATRIX_10
    logs = ["--- 现状空间矛盾 (Current Conflict Index) 演算 ---"]
    col_to_role = {c: role for role, cols in confirmed_mapping.items() for c in cols if c in grid_gdf.columns}

    total_conflict = np.zeros(len(grid_gdf))
    # 简化逻辑：计算每个网格内，所有现有要素两两之间的冲突叠加
    active_cols = list(col_to_role.keys())
    for i in range(len(active_cols)):
        for j in range(i + 1, len(active_cols)):
            col1, col2 = active_cols[i], active_cols[j]
            role1, role2 = col_to_role[col1], col_to_role[col2]
            
            # 如果是明确的海域分区角色，查询冲突矩阵
            if role1 in ZONES_10 and role2 in ZONES_10:
                c_val = matrix_to_use.get(role1, {}).get(role2, 0.0)
                if c_val > 0:
                    overlap = grid_gdf[col1].fillna(0).values * grid_gdf[col2].fillna(0).values
                    total_conflict += overlap * c_val

    c_min, c_max = np.min(total_conflict), np.max(total_conflict)
    if c_max > c_min: grid_gdf['Conflict_Index'] = ((total_conflict - c_min) / (c_max - c_min)) * 100.0 + 1.0
    else: grid_gdf['Conflict_Index'] = 1.0

    logs.append("✅ 全域现状矛盾空间重叠度提取完成，已生成 [Conflict_Index] 热力图。")
    return grid_gdf, "\n".join(logs)

def calculate_base_transition_cost(grid_gdf: gpd.GeoDataFrame, confirmed_mapping: dict, custom_matrix: dict = None) -> tuple:
    """【解耦新增】：专注于计算转化为未来分区的绝对成本列"""
    matrix_to_use = custom_matrix if custom_matrix else DEFAULT_CONFLICT_MATRIX_10
    logs = ["--- 基础转换成本 (Base Transition Cost) 结算 ---"]
    col_to_role = {c: role for role, cols in confirmed_mapping.items() for c in cols if c in grid_gdf.columns}

    for z_target in ZONES_10:
        cost_array = np.zeros(len(grid_gdf))
        for col, role in col_to_role.items():
            val_array = grid_gdf[col].fillna(0).values
            coeff = 0.0
            if role in ZONES_10: coeff = matrix_to_use.get(role, {}).get(z_target, 0.0)
            elif role in LAND_SEA_PENALTY: coeff = LAND_SEA_PENALTY[role].get(z_target.split('_')[1], 0.0)
            if coeff > 0: cost_array += val_array * coeff
            
        grid_gdf[f'Cost_to_{z_target}'] = cost_array

    logs.append("✅ 基础转换成本计算完毕，[Cost_to_Zxxx] 序列已就绪。")
    return grid_gdf, "\n".join(logs)

def calculate_total_cost(grid_gdf: gpd.GeoDataFrame, confirmed_mapping: dict, grid_size: float) -> tuple:
    logs = ["--- 叠加陆源与周边阻力 (Total Extractive Cost) 结算 ---"]
    if 'Cost_to_Z1_MPZ' not in grid_gdf.columns:
        raise ValueError("缺少基础转换成本！请先执行【生成各分区基础转换成本】。")

    total_raw_cost = np.zeros(len(grid_gdf))
    for z in ZONES_10:
        z_abbr = z.split('_')[1] 
        zone_raw = np.copy(grid_gdf[f'Cost_to_{z}'].values)
        
        for land_role in LAND_SEA_PENALTY.keys():
            w_impact = LAND_SEA_PENALTY[land_role].get(z_abbr, 0.0)
            if w_impact > 0:
                source_cols = confirmed_mapping.get(land_role, [])
                if source_cols:
                    influence_dist = RADIATION_DISTANCES.get(land_role, 1000.0)
                    source_intensity = grid_gdf[source_cols].max(axis=1).values
                    dist_penalty = _get_distance_penalty(grid_gdf, source_cols, influence_dist, grid_size)
                    zone_raw += dist_penalty * source_intensity * w_impact

        grid_gdf[f'Cost_L_{z}'] = zone_raw
        total_raw_cost += zone_raw

    grid_gdf['cost_conflict'] = total_raw_cost
    logs.append("📉 综合陆海辐射阻力完成，终极成本 [Cost_L_Zxxx] 序列已封存入库！")
    return grid_gdf, "\n".join(logs)
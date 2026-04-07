import numpy as np
import geopandas as gpd
from scipy.ndimage import gaussian_filter

def calculate_dual_sci(grid_gdf: gpd.GeoDataFrame, tree_mapping: dict, sigma_short: float, sigma_long: float, robust_norm: bool = True) -> gpd.GeoDataFrame:
    """透明化的强度加权核密度估计 (基于你的树形分类赋予拥挤度权重)"""
    
    # 不同的要素投入不同的基础拥挤权重
    category_weights = {
        "城镇和工业用海区": 1.0, "强压力源": 1.0,
        "港口航道区": 0.8, "特殊利用区": 0.8, "影响要素": 0.7,
        "弱压力源": 0.6, "商业渔业区": 0.5, "旅游区": 0.4,
        "传统渔业区": 0.3, "生态旅游区": 0.2,
        "高价值生态目标": 0.1, "生态保护和控制区": 0.1,
    }

    max_row = grid_gdf['row_idx'].max()
    max_col = grid_gdf['col_idx'].max()
    grid_matrix = np.zeros((max_row + 1, max_col + 1))
    
    weighted_intensity = np.zeros(len(grid_gdf))
    
    for cat_name, cols in tree_mapping.items():
        weight = 0.5 # 默认兜底
        for k, v in category_weights.items():
            if k in cat_name:
                weight = v; break
                
        for col in cols:
            if col in grid_gdf.columns:
                weighted_intensity += grid_gdf[col].fillna(0).values * weight
    
    grid_matrix[grid_gdf['row_idx'], grid_gdf['col_idx']] = weighted_intensity
    
    # 双核高斯扩散 (局部碰撞风险 + 宏观生态压迫)
    smooth_short = gaussian_filter(grid_matrix, sigma=sigma_short)
    smooth_long = gaussian_filter(grid_matrix, sigma=sigma_long)
    smoothed_combined = np.maximum(smooth_short, smooth_long)
    smoothed_vals = smoothed_combined[grid_gdf['row_idx'], grid_gdf['col_idx']]
    
    v_min = smoothed_vals.min()
    v_max = np.percentile(smoothed_vals, 98) if robust_norm else smoothed_vals.max()

    if v_max > v_min: sci_vals = np.clip((smoothed_vals - v_min) / (v_max - v_min), 0.0, 1.0) * 100.0
    else: sci_vals = np.zeros_like(smoothed_vals)
        
    grid_gdf['SCI'] = sci_vals
    return grid_gdf
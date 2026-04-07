import geopandas as gpd
import pandas as pd
import numpy as np

def intersect_features_to_grid(grid_gdf: gpd.GeoDataFrame, feature_gdf: gpd.GeoDataFrame, 
                               class_column: str, user_name: str, 
                               is_numeric: bool = False, is_ecological: bool = False) -> tuple:
    """智能空间相交引擎：废除剔除门槛，只要相交(Intersects)即刻保留"""
    if feature_gdf.crs != grid_gdf.crs:
        feature_gdf = feature_gdf.to_crs(grid_gdf.crs)

    added_cols = []
    unique_vals = []
    val_map = {}

    # 1. 纯净列名初始化
    if class_column == "[仅提取几何,不读取属性]":
        unique_vals = ["Presence"]
        col_name = user_name
        added_cols.append(col_name)
        if col_name not in grid_gdf.columns: grid_gdf[col_name] = 0.0
    elif is_numeric:
        feature_gdf = feature_gdf.dropna(subset=[class_column])
        unique_vals = sorted(feature_gdf[class_column].unique().tolist()) 
        n = len(unique_vals)
        if n == 1:
            val_map[unique_vals[0]] = 100.0
        else:
            for idx, v in enumerate(unique_vals):
                val_map[v] = 20.0 + idx * (80.0 / (n - 1))
        
        col_name = user_name
        added_cols.append(col_name)
        if col_name not in grid_gdf.columns: grid_gdf[col_name] = 0.0
    else:
        feature_gdf = feature_gdf.dropna(subset=[class_column])
        unique_vals = feature_gdf[class_column].unique().tolist()
        for cls_name in unique_vals:
            col_name = str(cls_name).strip()
            added_cols.append(col_name)
            if col_name not in grid_gdf.columns: grid_gdf[col_name] = 0.0

    # 2. 空间相交基础筛选 (直接使用 sjoin 的相交结果，不再执行严苛的面积过滤)
    valid_candidates = gpd.sjoin(grid_gdf, feature_gdf, how='inner', predicate='intersects')
    valid_candidates = valid_candidates.reset_index() 

    # 3. 矩阵赋值
    if class_column == "[仅提取几何,不读取属性]":
        grid_gdf.loc[valid_candidates['index'].unique(), user_name] = 100.0
    elif is_numeric:
        for i, idx in enumerate(valid_candidates['index']):
            feat_val = valid_candidates.iloc[i][class_column]
            assigned_score = val_map[feat_val]
            grid_gdf.at[idx, user_name] = max(grid_gdf.at[idx, user_name], assigned_score)
    else:
        for cls_val in unique_vals:
            col_n = str(cls_val).strip()
            subset = valid_candidates[valid_candidates[class_column] == cls_val]
            grid_gdf.loc[subset['index'].unique(), col_n] = 100.0

    return grid_gdf, added_cols, unique_vals
import numpy as np
import geopandas as gpd
from shapely.geometry import box
from scipy.ndimage import label

def suggest_grid_size(study_area_gdf: gpd.GeoDataFrame, target_count: int = 20000) -> float:
    """自动推算最接近 20000 个单元的整 50/100 边长"""
    if study_area_gdf.crs is None or study_area_gdf.crs.is_geographic:
        return 250.0 # 默认值，防崩溃
        
    total_area = study_area_gdf.geometry.area.sum()
    ideal_edge = np.sqrt(total_area / target_count)
    
    # 规整化：舍入到最近的 50 米
    rounded_length = round(ideal_edge / 50.0) * 50.0
    return max(50.0, rounded_length)

def generate_and_clean_grid(study_area_gdf: gpd.GeoDataFrame, grid_size: float = 250.0, remove_isolated: bool = True) -> gpd.GeoDataFrame:
    """切割网格：沾边保留法则 + 孤立网格切除"""
    if study_area_gdf.crs is None or study_area_gdf.crs.is_geographic:
        raise ValueError("请先确认坐标系为米制投影！")

    minx, miny, maxx, maxy = study_area_gdf.total_bounds
    cols = np.arange(minx, maxx + grid_size, grid_size)
    rows = np.arange(miny, maxy + grid_size, grid_size)
    
    polygons, col_indices, row_indices = [], [], []
    for c_idx, x in enumerate(cols[:-1]):
        for r_idx, y in enumerate(rows[:-1]):
            polygons.append(box(x, y, x + grid_size, y + grid_size))
            col_indices.append(c_idx)
            row_indices.append(r_idx)
            
    raw_grid = gpd.GeoDataFrame({
        'geometry': polygons,
        'col_idx': col_indices, 
        'row_idx': row_indices
    }, crs=study_area_gdf.crs)

    # 1. 沾边即保留 (Intersects)
    study_poly_gdf = gpd.GeoDataFrame(geometry=[study_area_gdf.unary_union], crs=study_area_gdf.crs)
    grid_filtered = gpd.sjoin(raw_grid, study_poly_gdf, how='inner', predicate='intersects')
    grid_filtered = grid_filtered.drop(columns=['index_right']).drop_duplicates(subset=['col_idx', 'row_idx'])
    grid_filtered = grid_filtered.reset_index(drop=True)

    # 2. 剔除孤立飞地网格 (连通性图论扫描)
    if remove_isolated and not grid_filtered.empty:
        max_r = grid_filtered['row_idx'].max()
        max_c = grid_filtered['col_idx'].max()
        matrix = np.zeros((max_r + 1, max_c + 1), dtype=int)
        matrix[grid_filtered['row_idx'], grid_filtered['col_idx']] = 1
        
        # 8-邻域结构
        structure = np.ones((3, 3), dtype=int)
        labeled_array, num_features = label(matrix, structure=structure)
        
        # 计算每个连通斑块的格子数，剔除大小 <= 2 的孤立格子
        sizes = np.bincount(labeled_array.ravel())
        sizes[0] = 0 # 忽略背景
        isolated_labels = np.where((sizes > 0) & (sizes <= 2))[0]
        
        valid_mask = ~np.isin(labeled_array[grid_filtered['row_idx'], grid_filtered['col_idx']], isolated_labels)
        grid_filtered = grid_filtered[valid_mask].reset_index(drop=True)

    return grid_filtered
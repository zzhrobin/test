import geopandas as gpd

def calculate_best_utm_epsg(lon: float, lat: float) -> int:
    """
    通用化工具：通过经纬度纯数学推导全球最佳的 UTM 投影带 EPSG 代码。
    北半球: 32601-32660 | 南半球: 32701-32760
    """
    zone_number = int((lon + 180) / 6) + 1
    base_epsg = 32600 if lat >= 0 else 32700
    return base_epsg + zone_number

def assess_and_recommend_crs(gdf: gpd.GeoDataFrame) -> dict:
    """评估坐标系，如果是经纬度则推算最合适的投影坐标系"""
    if gdf.crs is None:
        return {"status": "missing", "epsg": None, "msg": "缺失坐标系定义"}
        
    if gdf.crs.is_projected:
        return {"status": "ready", "epsg": gdf.crs.to_epsg(), "msg": "已是投影坐标系"}
        
    # 如果是经纬度，转化为4326后获取中心点，推导UTM带
    centroid = gdf.to_crs(epsg=4326).geometry.unary_union.centroid
    recommended_epsg = calculate_best_utm_epsg(centroid.x, centroid.y)
    
    return {
        "status": "geographic", 
        "epsg": recommended_epsg, 
        "msg": f"检测到经纬度坐标。建议转为米制投影 EPSG:{recommended_epsg}"
    }

def align_layer_crs(target_gdf: gpd.GeoDataFrame, master_epsg: int) -> gpd.GeoDataFrame:
    """强制对齐上传要素坐标系"""
    if target_gdf.crs is None or target_gdf.crs.to_epsg() != master_epsg:
        return target_gdf.to_crs(epsg=master_epsg)
    return target_gdf
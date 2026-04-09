import geopandas as gpd
import os
import logging

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def export_grid_to_shp(grid_gdf, output_path):
    """
    将带有分析结果的网格 GeoDataFrame 导出为 Shapefile。

    Args:
        grid_gdf (GeoDataFrame): 包含所有分析结果的网格。
        output_path (str): 保存 Shapefile 的完整路径 (e.g., "C:/results/final_grid.shp")。

    Returns:
        tuple: (bool, str) 表示成功与否和相关消息。
    """
    if grid_gdf is None or grid_gdf.empty:
        return False, "错误: 网格数据为空，无法导出。"
    
    try:
        # 确保导出目录存在
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logging.info(f"创建目录: {output_dir}")

        # Shapefile 字段名长度限制为10个字符，且不支持非 ASCII 字符
        # 创建一个副本进行清理
        export_gdf = grid_gdf.copy()
        
        # 创建一个映射来缩短和清理列名
        column_mapping = {col: str(col)[:10] for col in export_gdf.columns if col != 'geometry'}
        export_gdf.rename(columns=column_mapping, inplace=True)
        
        # 将坐标系转换回 WGS84 (EPSG:4326)，这是最通用的地理坐标系
        logging.info(f"正在将坐标系从 {export_gdf.crs} 转换为 EPSG:4326...")
        export_gdf = export_gdf.to_crs(epsg=4326)

        # 导出文件，使用 'utf-8' 编码以防万一
        export_gdf.to_file(output_path, driver='ESRI Shapefile', encoding='utf-8')
        
        logging.info(f"成功导出到: {output_path}")
        return True, f"成功导出到: {output_path}"

    except Exception as e:
        logging.error(f"导出 Shapefile 失败: {e}")
        return False, f"导出失败: {str(e)}"

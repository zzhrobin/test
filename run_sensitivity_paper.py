import os
import pickle
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches 
import tkinter as tk
from tkinter import filedialog
from scipy.ndimage import label
from core.scenario_engine import resolve_scenario_allocation

# 尝试载入中文字体，确保标题和图例不乱码
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

def calculate_metrics(grid_gdf, zoning_col):
    """计算用于论文指标的：碎片化指数 与 冲突成本"""
    max_r = grid_gdf['row_idx'].max()
    max_c = grid_gdf['col_idx'].max()
    
    unique_zones = grid_gdf[zoning_col].unique()
    zone_to_int = {z: i+1 for i, z in enumerate(unique_zones)}
    
    matrix = np.zeros((max_r + 1, max_c + 1), dtype=int)
    matrix[grid_gdf['row_idx'], grid_gdf['col_idx']] = grid_gdf[zoning_col].map(zone_to_int)
    
    total_isolated_patches = 0
    for z_val in zone_to_int.values():
        binary_matrix = (matrix == z_val).astype(int)
        structure = np.ones((3, 3), dtype=int) # 8-邻域
        labeled_array, num_features = label(binary_matrix, structure=structure)
        total_isolated_patches += num_features
        
    total_conflict = 0.0
    if 'cost_conflict' in grid_gdf.columns:
        # 排除无需管理的留白区，统计真正下达规划指令区域的潜在冲突
        active_mask = ~grid_gdf[zoning_col].str.contains('RZ', na=False)
        total_conflict = grid_gdf.loc[active_mask, 'cost_conflict'].sum()
        
    return total_isolated_patches, total_conflict

def run_paper_experiment():
    # 唤起系统原生的文件选择框
    root = tk.Tk()
    root.withdraw() # 隐藏 Tkinter 主窗口
    
    print("⏳ 等待选择工作区记忆文件 (.pkl)...")
    pkl_path = filedialog.askopenfilename(
        title="选择 MSP 进度文件", 
        filetypes=[("Pickle Files", "*.pkl")]
    )
    
    if not pkl_path:
        print("❌ 已取消选择，程序退出。")
        return

    print(f"📦 正在载入工作区状态: {os.path.basename(pkl_path)}")
    with open(pkl_path, 'rb') as f:
        state = pickle.load(f)
        
    # 提取核心数据
    grid_gdf = state['final_grid']
    study_area = state['study_area']
    bounds = study_area.total_bounds
    
    # 设定基准情景 (均衡发展情景进行控制变量测试最能体现SCI自适应的作用)
    test_scenario = "均衡发展 (Bay of Plenty)"
    modes = ['adaptive', 'fixed_low', 'fixed_high']
    results_report = []

    # --- 修复：已找回特殊利用区 (Z6_SPZ)，并保持统一的标签格式 ---
    zone_config = {
        'Z1_MPZ':  {'c': '#4CAF50', 'l': 'Z1 MPZ (海洋保护区)'}, 
        'Z2_FZ':   {'c': '#2196F3', 'l': 'Z2 FZ (渔业发展区)'}, 
        'Z3_PSZ':  {'c': '#00BCD4', 'l': 'Z3 PSZ (港口航运区)'}, 
        'Z4_UIZ':  {'c': '#F44336', 'l': 'Z4 UIZ (工业开发区)'}, 
        'Z5_TZ':   {'c': '#FFEB3B', 'l': 'Z5 TZ (旅游娱乐区)'}, 
        'Z6_SPZ':  {'c': '#9C27B0', 'l': 'Z6 SPZ (特殊利用区)'}, 
        'Z7_RZ_保留留白区': {'c': '#9E9E9E', 'l': 'Z7 RZ (保留留白区)'}
    }

    print(f"🚀 开始执行控制变量实验: {test_scenario}")
    
    # 获取 pkl 文件所在的目录，确保图片输出在同一个文件夹下
    output_dir = os.path.dirname(pkl_path)
    
    for mode in modes:
        out_col = f'Zoning_{mode}'
        print(f"  -> 正在演算模式: [{mode}] ...")
        
        # 调用核心算法引擎
        grid_gdf, _ = resolve_scenario_allocation(grid_gdf, scenario=test_scenario, out_col=out_col, mode=mode)
        
        # 计算科研指标
        patches, conflict = calculate_metrics(grid_gdf, out_col)
        results_report.append({
            'Control_Mode': mode,
            'Fragmentation_Index': patches,
            'Total_Conflict_Cost': round(conflict, 2)
        })
        
        # --- 创建画布与绘图 ---
        fig, ax = plt.subplots(figsize=(13, 10)) 
        
        # 根据映射字典获取每个网格的颜色
        colors = [zone_config.get(val, zone_config['Z7_RZ_保留留白区'])['c'] for val in grid_gdf[out_col]]
        grid_gdf.plot(ax=ax, color=colors, edgecolor='none')
        
        # 论文排版级别的标题 (英文)
        title = f"Scenario: {test_scenario}\nMode: {mode.upper()} | Patches: {patches} | Conflict: {conflict:.2f}"
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        
        # 坐标轴设置
        ax.set_xlim(bounds[0], bounds[2])
        ax.set_ylim(bounds[1], bounds[3])
        ax.set_xticks([]); ax.set_yticks([]) # 隐藏坐标刻度
        ax.set_aspect('equal')
        
        # --- 创建包含 Z1 到 Z7 的完整图例 ---
        legend_patches = []
        possible_zones = ['Z1_MPZ', 'Z2_FZ', 'Z3_PSZ', 'Z4_UIZ', 'Z5_TZ', 'Z6_SPZ', 'Z7_RZ_保留留白区']
        
        for z_id in possible_zones:
            info = zone_config[z_id]
            patch = mpatches.Patch(color=info['c'], label=info['l'])
            legend_patches.append(patch)
        
        # 将图例放置在右侧中央
        ax.legend(
            handles=legend_patches, 
            title="功能分区图例 (Legend)", 
            loc='center left', 
            bbox_to_anchor=(1, 0.5), 
            fontsize=11, 
            title_fontsize=13,
            frameon=True 
        )
        
        # --- 保存图片 ---
        display_mode_name = 'SCI_Adaptive' if mode == 'adaptive' else mode.capitalize()
        file_name = f"Result_Scenario_{display_mode_name}.png"
        output_path = os.path.join(output_dir, file_name)
        
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        print(f"    ✅ 已导出图像: {output_path}")

    # --- 打印最终数据报告 ---
    print("\n===========================================")
    print("📊 敏感性对比实验最终数据报告 (可直接用于论文)")
    print("===========================================")
    report_df = pd.DataFrame(results_report)
    report_df['Control_Mode'] = report_df['Control_Mode'].map({'adaptive':'SCI-Adaptive (Proposed)', 'fixed_low':'Uniform-Low (Fragmentation)', 'fixed_high':'Uniform-High (Over-smoothing)'})
    print(report_df.to_string(index=False))
    print("===========================================")

if __name__ == "__main__":
    run_paper_experiment()
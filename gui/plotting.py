import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.colors import ListedColormap
import geopandas as gpd
import pandas as pd
import numpy as np

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar

# 【Mac/Win 双端兼容字体组】
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC', 'Heiti SC', 'Microsoft YaHei', 'SimHei', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

class PlottingManager:
    def __init__(self, main_window):
        self.win = main_window
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.toolbar = NavigationToolbar(self.canvas, self.win)
        self.win.visual_layout.addWidget(self.toolbar)
        self.win.visual_layout.addWidget(self.canvas)

    def update_plot(self):
        self.figure.clf()
        self.ax = self.figure.add_subplot(111)
        gdf = self.win.final_grid
        
        if gdf is None or gdf.empty:
            self.ax.set_title("Status: 等待基础网格数据...")
            self.ax.axis('off'); self.canvas.draw(); return

        col_name = self.win.ui.view_combo.currentText()
        show_legend = self.win.ui.legend_combo.currentText() != "Hide"
        special_views = ["基础网格底盘 (Base Grid)", "已上传要素叠加 (All Features)"]
        
        if not col_name or (col_name not in gdf.columns and col_name not in special_views):
            gdf.plot(ax=self.ax, color='#E0E0E0', edgecolor='#A0A0A0', linewidth=0.2)
            self.ax.set_title("基础网格底盘 (Base Grid)")
            self.ax.axis('off'); self.canvas.draw(); return

        if col_name == "基础网格底盘 (Base Grid)":
            gdf.plot(ax=self.ax, color='#F0F0F0', edgecolor='#B0B0B0', linewidth=0.2)
            self.ax.set_title("基础网格底盘 (Base Grid)")
            
        elif col_name == "已上传要素叠加 (All Features)":
            gdf.plot(ax=self.ax, color='#F0F0F0', edgecolor='#E0E0E0', linewidth=0.1)
            for layer in self.win.feature_layers:
                feat_gdf = layer['data']
                if feat_gdf.crs != gdf.crs: feat_gdf = feat_gdf.to_crs(gdf.crs)
                feat_gdf.plot(ax=self.ax, color='red', alpha=0.5, edgecolor='darkred', linewidth=0.5)
            self.ax.set_title("已上传要素叠加总览")

        elif col_name == 'Scenario_Zoning':
            zone_colors = {
                'Z1_MPZ': '#4CAF50',  'Z2_UIZ': '#9E9E9E',  'Z3_PSZ': '#2196F3',
                'Z4_TZ':  '#00BCD4',  'Z5_TZE': '#8BC34A',  'Z6_FZT': '#FF9800',
                'Z7_FZC': '#F44336',  'Z8_FZA': '#FFEB3B',  'Z9_SPZ': '#9C27B0',
                'Z10_RZ': '#F5F5F5',  'Not Allocated': '#FFFFFF'
            }
            if 'Scenario_Zoning' in gdf.columns:
                present_zones = sorted(gdf[col_name].unique())
                colors = [zone_colors.get(z, '#000000') for z in present_zones]
                cmap = ListedColormap(colors)
                gdf.plot(column=col_name, ax=self.ax, cmap=cmap, legend=show_legend, categorical=True,
                         edgecolor='none', legend_kwds={'loc': 'center left', 'bbox_to_anchor': (1, 0.5), 'fontsize': 8})
                self.ax.set_title("空间分配远景蓝图 (白色区域为留白)")

        elif col_name in ["SCI", "cost_fishery_merged", "Conflict_Index", "cost_conflict"] or str(col_name).startswith("Cost_to_") or str(col_name).startswith("Cost_L_"):
            if col_name in gdf.columns:
                zeros = gdf[gdf[col_name] <= 0.001]
                positives = gdf[gdf[col_name] > 0.001]
                if not zeros.empty: zeros.plot(ax=self.ax, color='#E8E8E8', edgecolor='none')
                if not positives.empty:
                    c_max = positives[col_name].max()
                    vmax_val = 1.0 if c_max <= 1.01 else (100.0 if c_max <= 100.1 else c_max)
                    positives.plot(column=col_name, ax=self.ax, cmap='YlOrRd', legend=show_legend, vmin=0.0, vmax=vmax_val, edgecolor='none')
                self.ax.set_title(f"强度与分布: {col_name}")

        self.ax.axis('off'); self.figure.tight_layout(); self.canvas.draw()
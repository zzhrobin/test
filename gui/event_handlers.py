import os
import pickle
import json
import geopandas as gpd
import pandas as pd
import numpy as np
from PyQt6.QtWidgets import (
    QFileDialog,
    QInputDialog,
    QMessageBox,
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QApplication,
    QTreeWidgetItem,
    QTreeWidgetItemIterator,
    QDialog,
    QPushButton,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QDoubleSpinBox,
    QSpinBox,
    QCheckBox,
)
from PyQt6.QtCore import Qt

from core.grid_topology import generate_and_clean_grid, suggest_grid_size
from core.spatial_intersect import intersect_features_to_grid
from core.kde_engine import calculate_dual_sci
from core.cost_engine import (
    calculate_current_conflict,
    calculate_base_transition_cost,
    calculate_total_cost,
    calculate_fishery_cost,
    ZONES_10,
    DEFAULT_CONFLICT_MATRIX_10,
)
from core.crs_manager import assess_and_recommend_crs, align_layer_crs
from scenarios.event_router import ScenarioEventRouter  # 引入第二阶段路由

from core.cost_engine import DEFAULT_CONFLICT_MATRIX_10


class EventHandlers:
    def __init__(self, main_window):
        self.win = main_window
        # 激活第二阶段专属路由
        self.scenario_router = ScenarioEventRouter(self)
        self.scenario_router.bind_events()

    def _auto_suggest_zone(self, feature_name):
        name_l = str(feature_name).lower()
        dict_map = {
            "MPZ": [
                "mangrove",
                "coral",
                "turtle",
                "dolphin",
                "seagrass",
                "红树",
                "珊瑚",
                "生态",
                "海草",
            ],
            "UIZ": ["industry", "oil", "port", "factory", "工业", "油", "码头", "填海"],
            "PSZ": ["shipping", "channel", "航道", "锚地"],
            "TZ": ["tourism", "beach", "旅游", "沙滩", "ltour"],
            "FZT": ["traditional", "artisanal", "传统", "捕捞", "tfishing"],
            "FZA": ["aquaculture", "farm", "养殖"],
            "SPZ": ["military", "国防", "defence"],
            "影响要素": ["cable", "pipe", "电缆", "管线"],
            "强压力源": ["plant", "mine", "污染", "矿", "pforest"],
            "弱压力源": ["agriculture", "road", "农", "路", "ipark"],
            "高价值生态目标": ["lpa", "monkey", "gspace", "sand", "长鼻猴", "绿地"],
            "特殊锁定": ["bridge", "桥"],
        }
        for zone, keywords in dict_map.items():
            if any(k in name_l for k in keywords):
                return zone
        return "待分类"

    def _get_col_to_folder_mapping(self):
        col_to_folder = {}
        iterator = QTreeWidgetItemIterator(self.win.ui.layer_tree)
        while iterator.value():
            item = iterator.value()
            col_name = item.data(0, Qt.ItemDataRole.UserRole)
            if col_name:
                parent = item.parent()
                if parent:
                    col_to_folder[col_name] = parent.text(0)
            iterator += 1
        return col_to_folder

    def _parse_tree_classifications(self):
        mapping = {}
        target_cats = [
            "生态保护和控制区",
            "城镇和工业用海区",
            "港口航道区",
            "旅游区",
            "生态旅游区",
            "传统渔业区",
            "商业渔业区",
            "水产养殖区",
            "特殊利用区",
            "保留区",
            "⚠️ 影响要素",
            "🌱 高价值生态目标",
            "🔴 强压力源",
            "🟡 弱压力源",
            "🔒 特殊锁定",
        ]
        col_to_folder = self._get_col_to_folder_mapping()
        for col_name, folder_name in col_to_folder.items():
            for t_cat in target_cats:
                if t_cat in folder_name:
                    if t_cat not in mapping:
                        mapping[t_cat] = []
                    mapping[t_cat].append(col_name)
                    break
        return mapping

    def _refresh_view_combo(self):
        win = self.win
        current_view = win.ui.view_combo.currentText()
        win.ui.view_combo.blockSignals(True)
        win.ui.view_combo.clear()

        items = ["基础网格底盘 (Base Grid)"]
        if win.feature_layers:
            items.append("已上传要素叠加 (All Features)")

        # 极简核心视图白名单
        core_outputs = [
            "SCI",
            "cost_fishery_merged",
            "Conflict_Index",
            "cost_conflict",
            "Scenario_Zoning",
        ]

        if win.final_grid is not None:
            for out in core_outputs:
                if out in win.final_grid.columns:
                    items.append(out)

        win.ui.view_combo.addItems(items)
        if current_view in items:
            win.ui.view_combo.setCurrentText(current_view)
        else:
            win.ui.view_combo.setCurrentText(items[-1] if len(items) > 1 else items[0])

        win.ui.view_combo.blockSignals(False)
        win.plotter.update_plot()

    def reset_workspace(self):
        win = self.win
        reply = QMessageBox.question(
            win,
            "彻底重置",
            "确定清空当前工作区吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.No:
            return
        win.study_area = None
        win.final_grid = None
        win.feature_layers = []

        def clear_leaves(node):
            for i in reversed(range(node.childCount())):
                child = node.child(i)
                if child.data(0, Qt.ItemDataRole.UserRole):
                    node.removeChild(child)
                else:
                    clear_leaves(child)

        for i in range(win.ui.layer_tree.topLevelItemCount()):
            clear_leaves(win.ui.layer_tree.topLevelItem(i))
        for i in range(1, 6):
            win.ui.tabs.setTabEnabled(i, False)
        self._refresh_view_combo()

    def delete_selected_feature(self):
        win = self.win
        selected_items = win.ui.layer_tree.selectedItems()
        if not selected_items:
            return
        item = selected_items[0]
        col_name = item.data(0, Qt.ItemDataRole.UserRole)
        if not col_name:
            return
        item.parent().removeChild(item)
        if win.final_grid is not None and col_name in win.final_grid.columns:
            win.final_grid.drop(columns=[col_name], inplace=True, errors="ignore")
        for layer in win.feature_layers:
            if "added_cols" in layer and col_name in layer["added_cols"]:
                layer["added_cols"].remove(col_name)
        win.feature_layers = [
            layer
            for layer in win.feature_layers
            if len(layer.get("added_cols", [])) > 0
        ]
        self._refresh_view_combo()

    def load_feature(self, is_ecological=False):
        win = self.win
        if win.study_area is None:
            return
        file_paths, _ = QFileDialog.getOpenFileNames(
            win, "选择要素文件", "", "Vector (*.shp *.geojson)"
        )
        if not file_paths:
            return
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        total_extracted = 0
        for file_path in file_paths:
            try:
                gdf = align_layer_crs(
                    gpd.read_file(file_path), int(win.ui.epsg_input.text().strip())
                )
                layer_filename = os.path.basename(file_path).split(".")[0]
                col_choice = next(
                    (col for col in gdf.columns if col.lower() == "feature"), None
                )
                if not col_choice:
                    QApplication.restoreOverrideCursor()
                    columns = ["[仅提取几何,不读取属性]"] + list(gdf.columns)
                    col_choice, ok = QInputDialog.getItem(
                        win,
                        f"属性选择 - {layer_filename}",
                        "请指定要投影的属性：",
                        columns,
                        0,
                        False,
                    )
                    QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                    if not ok:
                        continue
                is_num = False
                base_name = layer_filename
                if col_choice != "[仅提取几何,不读取属性]":
                    converted = pd.to_numeric(gdf[col_choice], errors="coerce")
                    if converted.notna().sum() > 0:
                        gdf[col_choice] = converted
                        is_num = True
                win.final_grid, added_cols, unique_vals = intersect_features_to_grid(
                    win.final_grid, gdf, col_choice, base_name, is_num, is_ecological
                )
                win.feature_layers.append(
                    {
                        "name": layer_filename,
                        "source_col": col_choice,
                        "data": gdf,
                        "added_cols": added_cols,
                    }
                )
                feature_flags = (
                    Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsSelectable
                    | Qt.ItemFlag.ItemIsDragEnabled
                )
                for col_n in added_cols:
                    display_name = (
                        f"{col_n} [年份阶梯 | 源: {layer_filename}]"
                        if is_num
                        else f"{col_n} [源: {layer_filename} | 推: {self._auto_suggest_zone(col_n)}]"
                    )
                    child = QTreeWidgetItem(win.ui.cat_inbox, [display_name])
                    child.setData(0, Qt.ItemDataRole.UserRole, col_n)
                    child.setFlags(feature_flags)
                    total_extracted += 1
            except Exception as e:
                print(f"错误: {e}")
        win.ui.cat_inbox.setExpanded(True)
        self._refresh_view_combo()
        if total_extracted > 0:
            win.ui.view_combo.setCurrentText("已上传要素叠加 (All Features)")
        QApplication.restoreOverrideCursor()
        QMessageBox.information(
            win, "提取完毕", f"成功解析出 {total_extracted} 个特征！"
        )

    def run_kde_calculation(self):
        win = self.win
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        s_short = win.global_params.get("sci_sigma_short", 3.0)
        s_long = win.global_params.get("sci_sigma_long", 10.0)
        win.final_grid = calculate_dual_sci(
            win.final_grid, self._parse_tree_classifications(), s_short, s_long, True
        )
        self._refresh_view_combo()
        win.ui.view_combo.setCurrentText("SCI")
        QApplication.restoreOverrideCursor()

    def save_workspace(self):
        win = self.win
        if win.final_grid is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            win, "Save Workspace", "msp_state.pkl", "Pickle (*.pkl)"
        )
        if path:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            with open(path, "wb") as file:
                pickle.dump(
                    {
                        "study_area": win.study_area,
                        "final_grid": win.final_grid,
                        "epsg": win.ui.epsg_input.text(),
                        "layers": win.feature_layers,
                        "col_to_folder": self._get_col_to_folder_mapping(),
                        "custom_matrix": win.custom_conflict_matrix,
                        "global_params": win.global_params,
                        "confirmed_mapping": getattr(win, "confirmed_mapping", {}),
                    },
                    file,
                )
            QApplication.restoreOverrideCursor()
            QMessageBox.information(win, "保存", "进度封存！")

    def load_workspace(self):
        win = self.win
        path, _ = QFileDialog.getOpenFileName(
            win, "Load Workspace", "", "Pickle (*.pkl)"
        )
        if not path:
            return
        try:
            with open(path, "rb") as file:
                state = pickle.load(file)
            win.study_area = state.get("study_area")
            win.final_grid = state.get("final_grid")
            if "epsg" in state:
                win.ui.epsg_input.setText(state["epsg"])
            if "custom_matrix" in state:
                win.custom_conflict_matrix = state["custom_matrix"]
            if "global_params" in state:
                win.global_params.update(state["global_params"])
            if "confirmed_mapping" in state:
                win.confirmed_mapping = state["confirmed_mapping"]
            if "layers" in state:
                win.feature_layers = state["layers"]

                def clear_leaves(node):
                    for i in reversed(range(node.childCount())):
                        child = node.child(i)
                        if child.data(0, Qt.ItemDataRole.UserRole):
                            node.removeChild(child)
                        else:
                            clear_leaves(child)

                for i in range(win.ui.layer_tree.topLevelItemCount()):
                    clear_leaves(win.ui.layer_tree.topLevelItem(i))
                col_to_folder = state.get("col_to_folder", {})

                def find_folder(name):
                    it = QTreeWidgetItemIterator(win.ui.layer_tree)
                    while it.value():
                        if name in it.value().text(0):
                            return it.value()
                        it += 1
                    return win.ui.cat_inbox

                for index, layer in enumerate(win.feature_layers):
                    layer_name = layer.get("name", f"layer_{index + 1}")
                    added_cols = layer.get("added_cols", [])
                    if not added_cols:
                        added_cols = [
                            col
                            for col in win.final_grid.columns
                            if col.startswith(layer_name) or col == layer_name
                        ]
                        layer["added_cols"] = added_cols
                    for col_n in added_cols:
                        folder_node = find_folder(
                            col_to_folder.get(col_n, "📥 待分类 (Inbox)")
                        )
                        child = QTreeWidgetItem(folder_node, [f"{col_n} [载入恢复]"])
                        child.setData(0, Qt.ItemDataRole.UserRole, col_n)
                        child.setFlags(
                            Qt.ItemFlag.ItemIsEnabled
                            | Qt.ItemFlag.ItemIsSelectable
                            | Qt.ItemFlag.ItemIsDragEnabled
                        )
                win.ui.layer_tree.expandAll()
            for i in range(1, 6):
                win.ui.tabs.setTabEnabled(i, True)
            self._refresh_view_combo()
            QMessageBox.information(win, "载入成功", "进度已恢复！")
        except Exception as e:
            QMessageBox.critical(win, "载入失败", f"发生错误:\n{str(e)}")

    def open_global_params_editor(self):
        from PyQt6.QtWidgets import (
            QDialog,
            QFormLayout,
            QDoubleSpinBox,
            QPushButton,
            QHBoxLayout,
            QSpinBox,
            QCheckBox,
        )

        dialog = QDialog(self.win)
        dialog.setWindowTitle("⚙️ 全局核心参数控制台 (对标 PrioritizR)")
        dialog.resize(550, 500)
        layout = QFormLayout(dialog)

        spin_tmax = QDoubleSpinBox()
        spin_tmax.setRange(0, 100)
        spin_tmax.setValue(self.win.global_params.get("time_decay_max", 100.0))
        spin_tmin = QDoubleSpinBox()
        spin_tmin.setRange(0, 100)
        spin_tmin.setValue(self.win.global_params.get("time_decay_min", 20.0))
        spin_fish_dist = QDoubleSpinBox()
        spin_fish_dist.setRange(0, 200)
        spin_fish_dist.setValue(self.win.global_params.get("fishery_range_km", 15.0))
        spin_base_cost = QDoubleSpinBox()
        spin_base_cost.setRange(0, 5.0)
        spin_base_cost.setSingleStep(0.1)
        spin_base_cost.setValue(self.win.global_params.get("holness_base_cost", 0.3))
        spin_strong = QDoubleSpinBox()
        spin_strong.setRange(0, 10000)
        spin_strong.setSingleStep(100)
        spin_strong.setValue(self.win.global_params.get("influence_strong_m", 1500.0))
        spin_weak = QDoubleSpinBox()
        spin_weak.setRange(0, 10000)
        spin_weak.setSingleStep(100)
        spin_weak.setValue(self.win.global_params.get("influence_weak_m", 500.0))
        spin_sci_short = QDoubleSpinBox()
        spin_sci_short.setRange(0.1, 50.0)
        spin_sci_short.setSingleStep(0.5)
        spin_sci_short.setValue(self.win.global_params.get("sci_sigma_short", 3.0))
        spin_sci_long = QDoubleSpinBox()
        spin_sci_long.setRange(0.1, 100.0)
        spin_sci_long.setSingleStep(1.0)
        spin_sci_long.setValue(self.win.global_params.get("sci_sigma_long", 10.0))

        spin_blm = QDoubleSpinBox()
        spin_blm.setRange(0.0, 100.0)
        spin_blm.setSingleStep(0.5)
        spin_blm.setValue(self.win.global_params.get("base_blm", 1.0))
        spin_gurobi = QSpinBox()
        spin_gurobi.setRange(10, 3600)
        spin_gurobi.setSingleStep(60)
        spin_gurobi.setValue(self.win.global_params.get("gurobi_time", 300))
        spin_gap = QDoubleSpinBox()
        spin_gap.setRange(0.01, 1.0)
        spin_gap.setSingleStep(0.01)
        spin_gap.setValue(self.win.global_params.get("gurobi_gap", 0.05))

        cb_mandatory = QCheckBox("启用强制全域分配 (Mandatory Allocation)")
        cb_mandatory.setChecked(self.win.global_params.get("is_mandatory", True))

        layout.addRow("时间序列：最新年份得分 (Max 100):", spin_tmax)
        layout.addRow("时间序列：最老年份保底 (Min 20):", spin_tmin)
        layout.addRow("渔业空间：生计极限距离 (km):", spin_fish_dist)
        layout.addRow("向海辐射：强压力源惩罚半径 (m):", spin_strong)
        layout.addRow("拥挤指数：SCI 短高斯半径:", spin_sci_short)
        layout.addRow("【原著】Gurobi 基础边界惩罚 (Base BLM):", spin_blm)
        layout.addRow("【原著】Gurobi 求解容差 (MIP Gap 0.05):", spin_gap)
        layout.addRow("【原著】Gurobi 最大求解时间 (秒):", spin_gurobi)
        layout.addRow("【原著】空间策略:", cb_mandatory)

        h_btns = QHBoxLayout()
        btn_apply = QPushButton("✔️ 应用")
        btn_save_admin = QPushButton("💾 保存默认")
        h_btns.addWidget(btn_apply)
        h_btns.addWidget(btn_save_admin)

        def update_mem():
            self.win.global_params.update(
                {
                    "time_decay_max": spin_tmax.value(),
                    "time_decay_min": spin_tmin.value(),
                    "fishery_range_km": spin_fish_dist.value(),
                    "holness_base_cost": spin_base_cost.value(),
                    "influence_strong_m": spin_strong.value(),
                    "influence_weak_m": spin_weak.value(),
                    "sci_sigma_short": spin_sci_short.value(),
                    "sci_sigma_long": spin_sci_long.value(),
                    "base_blm": spin_blm.value(),
                    "gurobi_time": spin_gurobi.value(),
                    "gurobi_gap": spin_gap.value(),
                    "is_mandatory": cb_mandatory.isChecked(),
                }
            )

        def apply_only():
            update_mem()
            dialog.accept()

        def save_admin():
            update_mem()
            import json

            with open(self.win.config_file, "w", encoding="utf-8") as file:
                json.dump(self.win.global_params, file, indent=4, ensure_ascii=False)
            dialog.accept()

        btn_apply.clicked.connect(apply_only)
        btn_save_admin.clicked.connect(save_admin)
        layout.addRow("", h_btns)
        dialog.exec()

    def run_fishery_cost_calculation(self):
        win = self.win
        if win.final_grid is None:
            return
        dialog = QDialog(win)
        dialog.setWindowTitle("🐟 配置渔业与水产养殖")
        dialog.resize(500, 250)
        layout = QFormLayout(dialog)
        cb_village = QComboBox()
        layer_names = [
            str(layer.get("name", "Unknown")) for layer in win.feature_layers
        ]
        if not layer_names:
            cb_village.addItems(["[无可用图层，请先在 Tab 2 上传]"])
        else:
            cb_village.addItems(layer_names)
        cb_trad = QComboBox()
        cb_comm = QComboBox()
        cb_aqua = QComboBox()
        skip_cols = ["geometry", "col_idx", "row_idx", "intersect_area"]
        grid_cols = [
            c
            for c in win.final_grid.columns
            if c not in skip_cols and pd.api.types.is_numeric_dtype(win.final_grid[c])
        ]
        cb_trad.addItems(["[使用树形分类]"] + grid_cols)
        cb_comm.addItems(["[使用树形分类]"] + grid_cols)
        cb_aqua.addItems(["[使用树形分类]"] + grid_cols)
        layout.addRow("📍 选择【渔村基站】源文件:", cb_village)
        layout.addRow("🛶 选择【传统渔业】分布列:", cb_trad)
        layout.addRow("🚢 选择【商业渔业】分布列:", cb_comm)
        layout.addRow("🐟 选择【水产养殖】分布列:", cb_aqua)
        btn_run = QPushButton("▶ 开始测算")
        layout.addRow("", btn_run)

        def execute():
            if cb_village.currentText() == "[无可用图层，请先在 Tab 2 上传]":
                return
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                result = calculate_fishery_cost(
                    win.final_grid,
                    win.feature_layers[cb_village.currentIndex()]["data"],
                    self._parse_tree_classifications(),
                    range_km=win.global_params.get("fishery_range_km", 15.0),
                    trad_col=cb_trad.currentText(),
                    comm_col=cb_comm.currentText(),
                    aqua_col=cb_aqua.currentText(),
                )
                win.final_grid = result[0]
                self._refresh_view_combo()
                win.ui.view_combo.setCurrentText("cost_fishery_merged")
                QApplication.restoreOverrideCursor()
                dialog.accept()
            except Exception as e:
                QApplication.restoreOverrideCursor()
                QMessageBox.critical(dialog, "计算失败", str(e))

        btn_run.clicked.connect(execute)
        dialog.exec()

    def open_role_confirmation_dialog(self):
        win = self.win
        if win.final_grid is None:
            return
        from PyQt6.QtWidgets import (
            QDialog,
            QVBoxLayout,
            QTableWidget,
            QTableWidgetItem,
            QComboBox,
            QPushButton,
            QHBoxLayout,
            QFileDialog,
        )
        import json

        dialog = QDialog(win)
        dialog.setWindowTitle("📋 全局要素分类与角色指派预检 (支持本地模板记忆)")
        dialog.resize(750, 600)
        layout = QVBoxLayout(dialog)

        skip_cols = [
            "geometry",
            "col_idx",
            "row_idx",
            "intersect_area",
            "cost_conflict",
            "Conflict_Index",
            "cost_fishery_merged",
            "cost_fishery_T",
            "cost_fishery_C",
            "cost_fishery_A",
        ]
        for z in ZONES_10:
            skip_cols.extend(
                [z, f"Cost_to_{z}", f"Cost_L_{z}", f"Cost_{z}", f"Norm_Cost_{z}"]
            )
        grid_cols = [
            c
            for c in win.final_grid.columns
            if c not in skip_cols and pd.api.types.is_numeric_dtype(win.final_grid[c])
        ]

        # 内置智能关键词映射表 (根据你的 R 代码和常识预设)
        keyword_dict = {
            "MPZ": [
                "mangrove",
                "coral",
                "turtle",
                "dolphin",
                "seagrass",
                "egrass",
                "lpa",
                "monkey",
                "gspace",
                "sand",
                "mudflat",
            ],
            "UIZ": [
                "industry",
                "oil",
                "port",
                "factory",
                "mine",
                "offshrl",
                "dump",
                "waste",
                "blstwtr",
            ],
            "PSZ": ["shipping", "channel", "shipint", "shippin"],
            "TZ": ["tourism", "beach", "dive", "surf", "kite", "sup", "ltour"],
            "FZT": ["traditional", "smallpe", "ssf", "linefis"],
            "FZC": ["commercial", "trawl", "squid", "sharkfi"],
            "FZA": ["aquaculture", "maricul", "aqua"],
            "SPZ": ["military", "defence", "anchor", "cable", "pipe"],
        }

        role_options = [
            "不参与运算 (Ignore)",
            "Z1_MPZ (生态保护和控制区)",
            "Z2_UIZ (城镇和工业用海区)",
            "Z3_PSZ (港口航道区)",
            "Z4_TZ (旅游区)",
            "Z5_TZE (生态旅游区)",
            "Z6_FZT (传统渔业区)",
            "Z7_FZC (商业渔业区)",
            "Z8_FZA (水产养殖区)",
            "Z9_SPZ (特殊利用区)",
            "Z10_RZ (保留区)",
            "L1_工业矿业能源区",
            "L2_居住贸易服务区",
            "L3_农业与生产林",
            "L4_交通区(港口码头)",
            "L5_旅游区(小岛公园)",
            "L6_海底管道与电缆",
            "L7_国防与安全区",
            "ECO_高价值生态区(无辐射)",
        ]

        table = QTableWidget(len(grid_cols), 2)
        table.setHorizontalHeaderLabels(
            ["要素名称 (Feature)", "角色指派 (Role Assignment)"]
        )
        table.setColumnWidth(0, 300)
        table.setColumnWidth(1, 400)
        combo_refs = {}

        for i, col in enumerate(grid_cols):
            table.setItem(i, 0, QTableWidgetItem(col))
            cb = QComboBox()
            cb.addItems(role_options)
            matched_idx = 0
            col_lower = col.lower()

            # 智能关键字匹配
            if col == "cost_fishery_T":
                matched_idx = role_options.index("Z6_FZT (传统渔业区)")
            elif col == "cost_fishery_C":
                matched_idx = role_options.index("Z7_FZC (商业渔业区)")
            elif col == "cost_fishery_A":
                matched_idx = role_options.index("Z8_FZA (水产养殖区)")
            else:
                for r_key, keywords in keyword_dict.items():
                    if any(k in col_lower for k in keywords):
                        # 找到匹配的下拉项
                        for r_idx, r_opt in enumerate(role_options):
                            if r_key in r_opt:
                                matched_idx = r_idx
                                break
                        break
            cb.setCurrentIndex(matched_idx)
            table.setCellWidget(i, 1, cb)
            combo_refs[col] = cb

        layout.addWidget(table)

        # === 新增：本地记忆模板功能 ===
        h_mem = QHBoxLayout()
        btn_load_json = QPushButton("📁 从本地 JSON 加载映射模板")
        btn_save_json = QPushButton("💾 保存当前映射为 JSON 模板")
        btn_save_json.setStyleSheet("background-color: #607D8B; color: white;")
        h_mem.addWidget(btn_load_json)
        h_mem.addWidget(btn_save_json)
        layout.addLayout(h_mem)

        def load_mapping():
            path, _ = QFileDialog.getOpenFileName(
                dialog, "加载模板", "", "JSON (*.json)"
            )
            if not path:
                return
            try:
                with open(path, "r", encoding="utf-8") as f:
                    saved_map = json.load(f)
                for col, role_text in saved_map.items():
                    if col in combo_refs:
                        combo_refs[col].setCurrentText(role_text)
                QMessageBox.information(dialog, "成功", "模板加载成功！")
            except Exception as e:
                QMessageBox.critical(dialog, "错误", str(e))

        def save_mapping():
            path, _ = QFileDialog.getSaveFileName(
                dialog, "保存模板", "role_mapping_template.json", "JSON (*.json)"
            )
            if not path:
                return
            current_map = {col: cb.currentText() for col, cb in combo_refs.items()}
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(current_map, f, indent=4, ensure_ascii=False)
                QMessageBox.information(
                    dialog, "成功", "模板保存成功！以后可以一键导入。"
                )
            except Exception as e:
                QMessageBox.critical(dialog, "错误", str(e))

        btn_load_json.clicked.connect(load_mapping)
        btn_save_json.clicked.connect(save_mapping)

        btn_confirm = QPushButton("✔️ 确认无误并锁入系统内存")
        btn_confirm.setStyleSheet(
            "background-color: #FF9800; color: white; font-weight: bold; height: 40px;"
        )
        layout.addWidget(btn_confirm)

        def execute():
            win.confirmed_mapping = {}
            for col, cb in combo_refs.items():
                role_text = cb.currentText()
                if "Ignore" in role_text:
                    continue
                role_key = role_text.split(" ")[0]
                if role_key not in win.confirmed_mapping:
                    win.confirmed_mapping[role_key] = []
                win.confirmed_mapping[role_key].append(col)
            QMessageBox.information(dialog, "预检成功", "角色指派已锁定！")
            dialog.accept()

        btn_confirm.clicked.connect(execute)
        dialog.exec()

    def run_conflict_calculation(self):
        win = self.win
        if win.final_grid is None:
            return
        if not hasattr(win, "confirmed_mapping") or not win.confirmed_mapping:
            QMessageBox.warning(
                win, "请先预检", "请先点击上方的【全局要素分类全域确认 (预检)】按钮！"
            )
            return

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            win.final_grid, report = calculate_conflict_index(
                win.final_grid, win.confirmed_mapping, win.custom_conflict_matrix
            )
            self._refresh_view_combo()
            win.ui.view_combo.setCurrentText("Conflict_Index")
            QApplication.restoreOverrideCursor()
            QMessageBox.information(win, "基础成本测算完成", report)
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(win, "计算错误", str(e))

    def run_total_cost_calculation(self):
        win = self.win
        if win.final_grid is None:
            return
        if not hasattr(win, "confirmed_mapping") or not win.confirmed_mapping:
            QMessageBox.warning(
                win, "请先预检", "请先点击上方的【全局要素分类全域确认 (预检)】按钮！"
            )
            return

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            s_m = win.global_params.get("influence_strong_m", 1500.0)
            w_m = win.global_params.get("influence_weak_m", 500.0)
            base_c = win.global_params.get("holness_base_cost", 0.3)
            win.final_grid, report = calculate_total_cost(
                win.final_grid,
                win.confirmed_mapping,
                float(win.ui.grid_size_input.text()),
            )
            self._refresh_view_combo()
            win.ui.view_combo.setCurrentText("cost_conflict")
            QApplication.restoreOverrideCursor()
            QMessageBox.information(win, "综合成本结算完成", report)
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(win, "错误", str(e))

    def open_matrix_editor(self):
        from PyQt6.QtWidgets import (
            QDialog,
            QTableWidget,
            QTableWidgetItem,
            QVBoxLayout,
            QPushButton,
        )

        dialog = QDialog(self.win)
        dialog.setWindowTitle("10大分区冲突矩阵")
        dialog.resize(800, 600)
        layout = QVBoxLayout(dialog)
        table = QTableWidget(10, 10)
        headers = [z.split("_")[1] for z in ZONES_10]
        table.setHorizontalHeaderLabels(headers)
        table.setVerticalHeaderLabels(headers)
        current_matrix = (
            self.win.custom_conflict_matrix
            if self.win.custom_conflict_matrix
            else DEFAULT_CONFLICT_MATRIX_10
        )
        table.blockSignals(True)
        for i, z1 in enumerate(ZONES_10):
            for j, z2 in enumerate(ZONES_10):
                val = current_matrix.get(z1, {}).get(z2, 0.0)
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if i == j:
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                    item.setBackground(Qt.GlobalColor.lightGray)
                table.setItem(i, j, item)
        table.blockSignals(False)

        def sync_mirror(row, col):
            if row != col:
                table.blockSignals(True)
                table.item(col, row).setText(table.item(row, col).text())
                table.blockSignals(False)

        table.cellChanged.connect(sync_mirror)
        layout.addWidget(table)
        btn_save = QPushButton("💾 保存")
        btn_save.setStyleSheet("background-color: #4CAF50; color: white; height: 35px;")

        def save_matrix():
            new_matrix = {z1: {z2: 0.0 for z2 in ZONES_10} for z1 in ZONES_10}
            try:
                for i, z1 in enumerate(ZONES_10):
                    for j, z2 in enumerate(ZONES_10):
                        new_matrix[z1][z2] = float(table.item(i, j).text())
                self.win.custom_conflict_matrix = new_matrix
                dialog.accept()
            except ValueError:
                QMessageBox.critical(dialog, "错误", "必须填数字！")

        btn_save.clicked.connect(save_matrix)
        layout.addWidget(btn_save)
        dialog.exec()

    def show_attribute_table(self):
        win = self.win
        if win.final_grid is None:
            return
        df = win.final_grid.drop(columns=["geometry"], errors="ignore")
        new_tb = QWidget()
        new_tb.setWindowTitle("底层矩阵追踪")
        layout = QVBoxLayout(new_tb)
        table = QTableWidget(len(df), len(df.columns))
        table.setHorizontalHeaderLabels(df.columns.tolist())
        for i, (_, row) in enumerate(df.iterrows()):
            for j, col in enumerate(df.columns):
                table.setItem(
                    i,
                    j,
                    QTableWidgetItem(
                        str(round(row[col], 2))
                        if isinstance(row[col], float)
                        else str(row[col])
                    ),
                )
        layout.addWidget(table)
        new_tb.resize(1000, 600)
        win.spawned_windows.append(new_tb)
        new_tb.show()

    def load_study_area(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self.win, "Select File", "", "Shapefiles (*.shp);;GeoJSON (*.geojson)"
        )
        if not file_path:
            return
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        gdf = gpd.read_file(file_path)
        crs_assessment = assess_and_recommend_crs(gdf)
        if crs_assessment["status"] == "geographic":
            QApplication.restoreOverrideCursor()
            epsg_input, ok = QInputDialog.getInt(
                self.win,
                "CRS",
                f"EPSG: {crs_assessment['epsg']}\nConfirm:",
                value=crs_assessment["epsg"],
                min=1024,
                max=32767,
            )
            if not ok:
                return
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            gdf = gdf.to_crs(epsg=epsg_input)
            self.win.ui.epsg_input.setText(str(epsg_input))
        else:
            self.win.ui.epsg_input.setText(str(crs_assessment["epsg"]))
        self.win.study_area = gdf
        self.win.ui.grid_size_input.setText(str(int(suggest_grid_size(gdf))))
        self._refresh_view_combo()
        QApplication.restoreOverrideCursor()

    def run_grid_generation(self):
        win = self.win
        if win.study_area is None:
            return
        if win.final_grid is not None:
            reply = QMessageBox.question(
                win,
                "确认覆盖",
                "确定继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                return
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        win.final_grid = generate_and_clean_grid(
            win.study_area,
            float(win.ui.grid_size_input.text()),
            win.ui.cb_remove_isolated.isChecked(),
        )
        for i in range(1, 5):
            win.ui.tabs.setTabEnabled(i, True)
        self._refresh_view_combo()
        QApplication.restoreOverrideCursor()

    def export_results(self):
        win = self.win
        if win.final_grid is None:
            return
        save_dir = QFileDialog.getExistingDirectory(win, "选择保存结果文件夹")
        if not save_dir:
            return
        try:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            shp_path = os.path.join(save_dir, "Balikpapan_MSP_Result.shp")
            export_gdf = win.final_grid.copy()
            for col in export_gdf.columns:
                if export_gdf[col].dtype == bool:
                    export_gdf[col] = export_gdf[col].astype(int)
            export_gdf.to_file(shp_path, driver="ESRI Shapefile")
            QApplication.restoreOverrideCursor()
            QMessageBox.information(win, "成功", "Shapefile 导出成功！")
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(win, "导出失败", str(e))

    def force_reproject(self):
        pass


def calculate_conflict_index(grid_gdf, confirmed_mapping, custom_matrix=None):
    """
    Calculate the conflict index for the given grid GeoDataFrame.

    Parameters:
    - grid_gdf: GeoDataFrame containing the grid data.
    - confirmed_mapping: Dictionary mapping roles to columns.
    - custom_matrix: Optional custom conflict matrix.

    Returns:
    - Updated grid_gdf with a new 'Conflict_Index' column.
    - A string report summarizing the calculation.
    """
    import numpy as np
    import pandas as pd

    # Initialize conflict index column
    grid_gdf["Conflict_Index"] = 0.0

    # Default conflict matrix if none provided
    if custom_matrix is None:
        custom_matrix = {
            "Role1": {"Role2": 1.0, "Role3": 0.5},
            "Role2": {"Role1": 1.0, "Role3": 0.2},
            "Role3": {"Role1": 0.5, "Role2": 0.2},
        }

    # Calculate conflict index
    for role, columns in confirmed_mapping.items():
        for col in columns:
            if col not in grid_gdf.columns:
                continue
            for other_role, weights in custom_matrix.get(role, {}).items():
                for other_col in confirmed_mapping.get(other_role, []):
                    if other_col not in grid_gdf.columns:
                        continue
                    grid_gdf["Conflict_Index"] += (
                        grid_gdf[col] * grid_gdf[other_col] * weights
                    )

    # Generate a summary report
    total_conflict = grid_gdf["Conflict_Index"].sum()
    report = f"Conflict Index calculated. Total conflict value: {total_conflict:.2f}"

    return grid_gdf, report


def redistribute_locked_costs(self, locked_costs, total_budget):
    """
    Redistribute locked costs proportionally based on the total budget.

    Parameters:
    locked_costs (dict): A dictionary where keys are categories and values are the locked costs.
    total_budget (float): The total budget available for redistribution.

    Returns:
    dict: A dictionary with redistributed costs.
    """
    if not locked_costs or total_budget <= 0:
        return {}

    total_locked = sum(locked_costs.values())
    if total_locked == 0:
        return {key: 0 for key in locked_costs}

    redistribution_ratio = total_budget / total_locked
    redistributed_costs = {
        category: cost * redistribution_ratio for category, cost in locked_costs.items()
    }

    return redistributed_costs


def on_run_development_scenario_clicked(self):
    """
    开发优先情景求解：严格按照排他锁定 -> 成本转移 -> 均一化 -> 目标提取的顺序
    """
    from PyQt5.QtWidgets import QMessageBox, QApplication
    from PyQt5.QtCore import Qt

    QApplication.setOverrideCursor(Qt.WaitCursor)

    try:
        # 基础数据准备
        if not hasattr(self.main_window, "gdf") or self.main_window.gdf is None:
            raise ValueError("未检测到基础网格底盘数据。")
        scenario_gdf = self.main_window.gdf.copy()
        cost_columns = [
            col for col in scenario_gdf.columns if col.startswith("Cost_to_Z")
        ]

        # =======================================================
        # 第一步：空间锁定与排除 (Exclusion & Pre-determination)
        # =======================================================
        # 1. 排除 RZ 保留区
        if "Cost_to_Z10_RZ" in scenario_gdf.columns:
            scenario_gdf.drop(columns=["Cost_to_Z10_RZ"], inplace=True)
            cost_columns.remove("Cost_to_Z10_RZ")

        # 2. 获取被提前锁定的网格索引
        locked_indices = self.get_locked_spatial_indices()

        # 3. 冲突排解：如果有格子被锁定但包含多种功能意向，应用特定规则 (UIZ > PSZ)
        if locked_indices:
            scenario_gdf = self.resolve_locked_zone_priorities(
                scenario_gdf, locked_indices
            )

        # =======================================================
        # 第二步：渔业成本均摊与情景内 Min-Max 均一化
        # =======================================================
        # 1. 渔业成本平摊（被排除/锁定为非渔业的成本，转移到同类空间）
        if locked_indices:
            scenario_gdf = self.redistribute_locked_costs(scenario_gdf, locked_indices)

        # 2. 情景内 Min-Max 均一化（严格在均摊计算完成之后进行）
        for col in cost_columns:
            c_min = scenario_gdf[col].min()
            c_max = scenario_gdf[col].max()
            if c_max - c_min != 0:
                scenario_gdf[col] = (scenario_gdf[col] - c_min) / (c_max - c_min)
            else:
                scenario_gdf[col] = 0.0

        # =======================================================
        # 第三步：设置求解目标 (大类/小类比例 & 生态要素单独设置)
        # =======================================================
        # 1. 大类与小类的目标比例设置
        scenario_targets = {
            "MPZ": self.main_window.ui.spin_target_mpz.value() / 100.0,
            "TZE": self.main_window.ui.spin_target_tze.value() / 100.0,
            "FZT": self.main_window.ui.spin_target_fzt.value() / 100.0,
            "FZC": self.main_window.ui.spin_target_fzc.value() / 100.0,
            "FZA": self.main_window.ui.spin_target_fza.value() / 100.0,
            "UIZ": self.main_window.ui.spin_target_uiz.value() / 100.0,
            "PSZ": self.main_window.ui.spin_target_psz.value() / 100.0,
            "TZ": self.main_window.ui.spin_target_tz.value() / 100.0,
            "SPZ": self.main_window.ui.spin_target_spz.value() / 100.0,
        }

        # 2. 其他生态要素的单独设置（例如 Holness 特保目标）
        ecological_targets = self.get_holness_special_rules()

        # --- 至此，所有题干准备完毕，提交 Gurobi 求解 ---
        print("[引擎] 题干生成完毕，启动求解器...")
        # self.solve_with_prioritizr(scenario_gdf, scenario_targets, ecological_targets)

        # ==========================================
        # 5. 调用 Gurobi 引擎求解
        # ==========================================
        print("[引擎] 数据准备完毕，进入求解环节...")

        # 获取你在参数控制台输入的字典 (包含 time_limit, mip_gap 等)
        global_params = self.get_global_params()

        # 获取真实冲突矩阵
        conflict_matrix = self.main_window.conflict_matrix

        # 引入第一批次构建的引擎类
        from optimization_engine import PrioritizREngine

        engine = PrioritizREngine(
            scenario_gdf, scenario_targets, global_params, conflict_matrix
        )
        engine.build_model()

        # 这里的 engine.solve() 我们会在后续批次完成
        QApplication.restoreOverrideCursor()
        QMessageBox.information(
            self.main_window, "准备就绪", "三步处理完成，数据已送入求解引擎！"
        )

    except Exception as e:
        QApplication.restoreOverrideCursor()
        QMessageBox.critical(self.main_window, "中断", f"发生错误：\n{str(e)}")


def resolve_locked_zone_priorities(self, gdf, locked_indices):
    """
    第一步中的冲突排解逻辑：处理同一网格具备多种锁定意向的情况。
    强制规则示例：如果同时预选了 UIZ 和 PSZ，UIZ 优先级更高。
    """
    # 初始化一个新列，用于记录该网格最终被“锁死”的唯一功能
    if "Final_Locked_Zone" not in gdf.columns:
        gdf["Final_Locked_Zone"] = None

    for idx in locked_indices:
        # 假设你通过某种方式获取了该网格用户勾选的候选锁定功能列表
        # TODO: 替换为获取真实勾选列表的方法，例如 ['UIZ', 'PSZ', 'FZT']
        candidate_zones = self.get_candidate_locks_for_grid(idx)

        if not candidate_zones:
            continue

        # 应用优先级裁决逻辑
        if "UIZ" in candidate_zones and "PSZ" in candidate_zones:
            final_zone = "UIZ"  # UIZ 大于 PSZ
        elif "MPZ" in candidate_zones:
            final_zone = "MPZ"  # 假设核心保护区拥有绝对最高优先级
        else:
            # 如果没有冲突，或者按列表第一个默认意向
            final_zone = candidate_zones[0]

        # 将最终裁决结果写入底盘
        gdf.at[idx, "Final_Locked_Zone"] = final_zone

        # 【关键】将该网格转换为其他功能的成本设为极大值（或无穷大），确保求解器不会去改它
        # 或者将其目标功能的成本设为 0
        target_cost_col = f"Cost_to_{final_zone}"  # 例如 Cost_to_UIZ
        for col in [c for c in gdf.columns if c.startswith("Cost_to_Z")]:
            if target_cost_col in col:
                gdf.at[idx, col] = 0.0  # 转化为目标功能的难度为 0
            else:
                gdf.at[idx, col] = 99999.0  # 转化为其他功能的难度极高

    return gdf


def get_candidate_locks_for_grid(self, index):
    """
    根据网格索引，返回用户为该网格勾选的拟锁定功能列表。
    这需要连接你的 UI 锁定界面逻辑。
    """
    # 示例：假设这个网格刚好被用户同时框进了 UIZ 和 PSZ 的锁定区
    # 返回 ['UIZ', 'PSZ']
    return []

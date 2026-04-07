from PyQt6.QtWidgets import QMessageBox, QApplication, QListWidgetItem, QSpinBox, QDialog, QVBoxLayout, QListWidget, QPushButton, QFormLayout, QLabel
from PyQt6.QtCore import Qt
from core.scenario_engine import resolve_scenario_allocation
import numpy as np

class ScenarioEventRouter:
    def __init__(self, main_handlers):
        self.handlers = main_handlers
        self.win = main_handlers.win

    def bind_events(self):
        self.win.ui.btn_to_phase2.clicked.connect(self.switch_to_phase2)
        self.win.ui.btn_back_to_phase1.clicked.connect(lambda: self.win.ui.stacked_widget.setCurrentIndex(0))
        
        for sc_name, controls in self.win.ui.scenario_controls.items():
            controls['btn_run'].clicked.connect(lambda checked, name=sc_name: self.run_scenario_zoning(name))
            controls['btn_lock'].clicked.connect(lambda checked, name=sc_name: self.open_lock_dialog(name))

    def switch_to_phase2(self):
        win = self.win
        if win.final_grid is None or 'Cost_L_Z1_MPZ' not in win.final_grid.columns:
            QMessageBox.warning(win, "禁止通行", "请先算完【综合排斥总成本】！")
            return
            
        mapping = getattr(win, 'confirmed_mapping', {})
        lockable_features = []
        for role, cols in mapping.items():
            if str(role).startswith("L"): continue 
            lockable_features.extend(cols)
                
        self.win.lockable_cache = list(set(lockable_features))
        win.ui.stacked_widget.setCurrentIndex(1)

    def open_lock_dialog(self, scenario_name):
        controls = self.win.ui.scenario_controls[scenario_name]
        dialog = QDialog(self.win); dialog.setWindowTitle(f"配置锁定要素 - {scenario_name}"); dialog.resize(400, 500)
        layout = QVBoxLayout(dialog)
        
        list_widget = QListWidget()
        for f in getattr(self.win, 'lockable_cache', []):
            item = QListWidgetItem(f)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if f in controls['locked_features'] else Qt.CheckState.Unchecked)
            list_widget.addItem(item)
            
        layout.addWidget(list_widget)
        btn_ok = QPushButton("确认锁定"); layout.addWidget(btn_ok)
        
        def save_locks():
            selected = []
            for i in range(list_widget.count()):
                if list_widget.item(i).checkState() == Qt.CheckState.Checked: selected.append(list_widget.item(i).text())
            controls['locked_features'] = selected
            controls['lbl_lock_status'].setText(f"已锁定: {len(selected)} 项")
            controls['lbl_lock_status'].setStyleSheet("color: green; font-weight: bold;")
            dialog.accept()
            
        btn_ok.clicked.connect(save_locks); dialog.exec()

    # 原生复刻：Holness et al. 2022 阶梯目标算法
    def _calculate_holness_targets(self, eco_features):
        grid = self.win.final_grid
        target_percentages = {}
        for feat in eco_features:
            if feat in grid.columns:
                area_sum = np.sum(grid[feat].fillna(0).values > 0)
                if area_sum <= 0: continue
                # 根据论文公式进行阶梯折算
                if area_sum <= 1000: target_pu = area_sum * 0.6
                elif area_sum <= 5000: target_pu = 1000 * 0.6 + (area_sum - 1000) * 0.5
                elif area_sum <= 10000: target_pu = 1000 * 0.6 + 4000 * 0.5 + (area_sum - 5000) * 0.4
                elif area_sum <= 50000: target_pu = 1000 * 0.6 + 4000 * 0.5 + 5000 * 0.4 + (area_sum - 10000) * 0.3
                else: target_pu = 1000 * 0.6 + 4000 * 0.5 + 5000 * 0.4 + 10000 * 0.3 + (area_sum - 20000) * 0.2
                
                pct = (target_pu / area_sum) * 100.0
                target_percentages[feat] = min(pct, 100.0)
        return target_percentages

    def run_scenario_zoning(self, scenario_name):
        win = self.win
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            controls = win.ui.scenario_controls[scenario_name]
            locked_features = controls['locked_features']
            zone_targets = {z: spin.value() for z, spin in controls['target_spins'].items()}
            
            mapping = getattr(win, 'confirmed_mapping', {})
            eco_features = []
            for role, cols in mapping.items():
                if "生态" in role or "MPZ" in role: eco_features.extend(cols)
                    
            special_targets = self._calculate_holness_targets(list(set(eco_features)))
            
            # 【重要更新】传入全局参数 (获取 BLM) 与 自定义矛盾矩阵
            current_matrix = win.custom_conflict_matrix if win.custom_conflict_matrix else self.handlers.DEFAULT_CONFLICT_MATRIX_10
            
            win.final_grid, report = resolve_scenario_allocation(
                win.final_grid, scenario_name, mapping, locked_features, 
                zone_targets, special_targets, win.global_params, current_matrix
            )
            
            self.handlers._refresh_view_combo()
            win.ui.view_combo.setCurrentText("Scenario_Zoning")
            
            QApplication.restoreOverrideCursor()
            QMessageBox.information(win, f"{scenario_name} Gurobi 优化完毕", report)
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(win, "推演错误", str(e))
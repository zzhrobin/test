from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QTabWidget,
    QGroupBox,
    QGridLayout,
    QHBoxLayout,
    QSpinBox,
    QScrollArea,
    QCheckBox,
    QFileDialog,
    QMessageBox,
)
import json


class ScenarioUIBuilder:
    def __init__(self, ui_setup_instance):
        self.ui = ui_setup_instance

    def build_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        self.ui.btn_back_to_phase1 = QPushButton("⬅️ 返回基础数据处理阶段")
        self.ui.btn_back_to_phase1.setStyleSheet(
            "background-color: #607D8B; color: white; font-weight: bold; height: 35px;"
        )
        layout.addWidget(self.ui.btn_back_to_phase1)
        layout.addWidget(QLabel("<b>⚙️ 情景沙盘实验室 (Gurobi Engine)</b>"))

        self.ui.scenario_tabs = QTabWidget()
        scenarios = ["保持现状", "均衡发展", "保护优先", "开发优先", "利益相关者偏好"]
        for sc in scenarios:
            tab = QWidget()
            self._build_standard_scenario_ui(tab, sc)
            self.ui.scenario_tabs.addTab(tab, sc)

        layout.addWidget(self.ui.scenario_tabs)
        return panel

    def _build_standard_scenario_ui(self, tab_widget, scenario_name):
        main_layout = QVBoxLayout(tab_widget)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        l = QVBoxLayout(content_widget)

        controls = {"target_spins": {}, "locked_features": [], "special_targets": {}}

        # --- 新增：配置存档与载入 ---
        gb_io = QGroupBox("💾 情景参数存档")
        h_io = QHBoxLayout()
        btn_save = QPushButton("保存本情景配置")
        controls["btn_save"] = btn_save
        btn_load = QPushButton("载入配置")
        controls["btn_load"] = btn_load
        h_io.addWidget(btn_save)
        h_io.addWidget(btn_load)
        gb_io.setLayout(h_io)
        l.addWidget(gb_io)

        # 1. 绝对锁定要素
        gb_lock = QGroupBox("🔒 空间锁定 (既定事实绝对约束)")
        hl1 = QHBoxLayout()
        btn_lock = QPushButton("配置强制锁定海域...")
        controls["btn_lock"] = btn_lock
        lbl_lock_status = QLabel("未锁定")
        lbl_lock_status.setStyleSheet("color: gray;")
        controls["lbl_lock_status"] = lbl_lock_status
        hl1.addWidget(btn_lock)
        hl1.addWidget(lbl_lock_status)
        gb_lock.setLayout(hl1)
        l.addWidget(gb_lock)

        # --- 新增：SCI 对比开关 ---
        gb_sci = QGroupBox("🔬 空间拥挤度 (SCI) 实验对照")
        h_sci = QHBoxLayout()
        cb_sci = QCheckBox("启用 SCI 动态加权以惩罚高冲突区边界")
        cb_sci.setChecked(True)
        controls["cb_sci"] = cb_sci
        h_sci.addWidget(cb_sci)
        gb_sci.setLayout(h_sci)
        l.addWidget(gb_sci)

        # 2. 分类海域目标配额
        gb_target = QGroupBox("🎯 全局分区约束占比 (%)")
        gl = QGridLayout()
        categories = {
            "🟢 保育类": ["Z1_MPZ", "Z5_TZE"],
            "🔵 社区与渔业": ["Z6_FZT", "Z7_FZC", "Z8_FZA"],
            "🟠 开发与矿运": ["Z2_UIZ", "Z3_PSZ", "Z4_TZ"],
        }

        row = 0
        for cat_name, zones in categories.items():
            gl.addWidget(QLabel(f"<b>{cat_name}</b>"), row, 0, 1, 4)
            row += 1
            col = 0
            for z in zones:
                z_abbr = z.split("_")[1]
                gl.addWidget(QLabel(z_abbr), row, col)
                spin = QSpinBox()
                spin.setRange(0, 100)

                # 同款 2025 论文基准参数预设
                if "保护优先" in scenario_name:
                    defaults = {
                        "MPZ": 45,
                        "TZE": 30,
                        "FZT": 30,
                        "FZC": 15,
                        "FZA": 20,
                        "UIZ": 10,
                        "PSZ": 15,
                        "TZ": 20,
                    }
                elif "开发优先" in scenario_name:
                    defaults = {
                        "MPZ": 15,
                        "TZE": 15,
                        "FZT": 15,
                        "FZC": 35,
                        "FZA": 40,
                        "UIZ": 45,
                        "PSZ": 30,
                        "TZ": 35,
                    }
                elif "利益相关者" in scenario_name:
                    defaults = {
                        "MPZ": 25,
                        "TZE": 20,
                        "FZT": 45,
                        "FZC": 40,
                        "FZA": 35,
                        "UIZ": 25,
                        "PSZ": 20,
                        "TZ": 45,
                    }
                else:
                    defaults = {
                        "MPZ": 25,
                        "TZE": 20,
                        "FZT": 25,
                        "FZC": 25,
                        "FZA": 25,
                        "UIZ": 20,
                        "PSZ": 20,
                        "TZ": 20,
                    }

                spin.setValue(defaults.get(z_abbr, 10))
                gl.addWidget(spin, row, col + 1)
                controls["target_spins"][z] = spin
                col += 2
                if col >= 4:
                    col = 0
                    row += 1
            if col != 0:
                row += 1
        gb_target.setLayout(gl)
        l.addWidget(gb_target)

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        btn_run = QPushButton(f"▶ 启动 {scenario_name.split('_')[0]} 求解")
        btn_run.setStyleSheet(
            "background-color: #E91E63; color: white; font-weight: bold; height: 45px;"
        )
        controls["btn_run"] = btn_run
        main_layout.addWidget(btn_run)

        self.ui.scenario_controls[scenario_name] = controls

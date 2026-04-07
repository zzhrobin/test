from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QTabWidget,
    QGroupBox,
    QFormLayout,
    QSpinBox,
    QScrollArea,
    QGridLayout,
    QHBoxLayout,
)


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

        # 【论文同款情景】
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

        # 1. 弹出式：绝对锁定要素
        gb_lock = QGroupBox("🔒 空间锁定 (Gurobi 绝对约束)")
        hl1 = QHBoxLayout()
        btn_lock = QPushButton("配置强制锁定海域...")
        controls["btn_lock"] = btn_lock
        lbl_lock_status = QLabel("已锁定: 0 项")
        lbl_lock_status.setStyleSheet("color: gray;")
        controls["lbl_lock_status"] = lbl_lock_status
        hl1.addWidget(btn_lock)
        hl1.addWidget(lbl_lock_status)
        gb_lock.setLayout(hl1)
        l.addWidget(gb_lock)

        # 2. 分类海域目标配额
        gb_target = QGroupBox("🎯 全局分区约束占比 (%)")
        gl = QGridLayout()
        categories = {
            "🟢 保育类 (Conservation)": ["Z1_MPZ", "Z5_TZE"],
            "🔵 社区与渔业 (Community/Fishery)": ["Z6_FZT", "Z7_FZC", "Z8_FZA"],
            "🟠 开发与矿运 (Development/Mining)": ["Z2_UIZ", "Z3_PSZ", "Z4_TZ"],
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

                # 根据不同情景配置默认保留百分比
                if "保持现状" in scenario_name:
                    spin.setValue(15 if "UIZ" in z else 10)
                elif "均衡发展" in scenario_name:
                    spin.setValue(30 if "MPZ" in z else 8)
                elif "保护优先" in scenario_name:
                    spin.setValue(45 if "MPZ" in z else 5)
                elif "开发优先" in scenario_name:
                    spin.setValue(25 if "UIZ" in z else 8)
                else:
                    spin.setValue(10)

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

        # 3. 基于 Holness 2022 的保护目标
        gb_special = QGroupBox("🌟 阶梯式特保目标 (Holness 2022 算法)")
        l.addWidget(gb_special)
        # 该处按钮将调用后台的 Holness 算法自动计算目标百分比，存入 Gurobi

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        btn_run = QPushButton(f"▶ 启动 {scenario_name.split('_')[0]} 求解")
        btn_run.setStyleSheet(
            "background-color: #E91E63; color: white; font-weight: bold; height: 45px;"
        )
        controls["btn_run"] = btn_run
        main_layout.addWidget(btn_run)

        self.ui.scenario_controls[scenario_name] = controls

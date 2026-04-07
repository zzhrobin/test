import json
import os
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout
from .ui_setup import UISetup
from .event_handlers import EventHandlers
from .plotting import PlottingManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Marine Spatial Planning SDSS (v6.0 Academic Edition)")
        self.study_area = None
        self.final_grid = None
        self.feature_layers = []
        self.bay_area = None
        self.villages = None
        self.custom_conflict_matrix = None
        self.spawned_windows = []

        self.config_file = "admin_global_config.json"
        self._init_global_params()
        self.ui = UISetup(self)
        self.init_ui()
        self.plotter = PlottingManager(self)
        self.handlers = EventHandlers(self)
        self.connect_signals()

    def _init_global_params(self):
        default_params = {
            "time_decay_max": 100.0,
            "time_decay_min": 20.0,
            "fishery_range_km": 15.0,
            "holness_base_cost": 0.3,
            "influence_strong_m": 1500.0,
            "influence_weak_m": 500.0,
            "sci_sigma_short": 3.0,
            "sci_sigma_long": 10.0,
        }
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as file:
                    self.global_params = json.load(file)
            except Exception:
                self.global_params = default_params
        else:
            self.global_params = default_params
            with open(self.config_file, "w", encoding="utf-8") as file:
                json.dump(default_params, file, indent=4, ensure_ascii=False)

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        # 获取最新的 StackedWidget
        left_panel = self.ui.create_left_panel()
        layout.addWidget(left_panel)
        self.visual_layout = QVBoxLayout()
        layout.addLayout(self.visual_layout, 3)

    def connect_signals(self):
        # 页面切换绑定

        self.ui.view_combo.currentTextChanged.connect(self.plotter.update_plot)
        self.ui.legend_combo.currentTextChanged.connect(self.plotter.update_plot)
        self.ui.cb_top.stateChanged.connect(self.plotter.update_plot)
        self.ui.cb_bottom.stateChanged.connect(self.plotter.update_plot)
        self.ui.cb_left.stateChanged.connect(self.plotter.update_plot)
        self.ui.cb_right.stateChanged.connect(self.plotter.update_plot)

        self.ui.btn_save.clicked.connect(self.handlers.save_workspace)
        self.ui.btn_load.clicked.connect(self.handlers.load_workspace)
        self.ui.btn_export_shp.clicked.connect(self.handlers.export_results)
        self.ui.btn_reset.clicked.connect(self.handlers.reset_workspace)
        self.ui.btn_load_study.clicked.connect(self.handlers.load_study_area)
        self.ui.btn_force_crs.clicked.connect(self.handlers.force_reproject)
        self.ui.btn_gen_grid.clicked.connect(self.handlers.run_grid_generation)
        self.ui.btn_load_normal.clicked.connect(
            lambda: self.handlers.load_feature(is_ecological=False)
        )
        self.ui.btn_load_eco.clicked.connect(
            lambda: self.handlers.load_feature(is_ecological=True)
        )
        self.ui.btn_delete_feature.clicked.connect(
            self.handlers.delete_selected_feature
        )
        self.ui.btn_show_table.clicked.connect(self.handlers.show_attribute_table)
        self.ui.btn_show_table_cost.clicked.connect(self.handlers.show_attribute_table)
        self.ui.btn_run_kde.clicked.connect(self.handlers.run_kde_calculation)
        self.ui.btn_run_fishery_cost.clicked.connect(
            self.handlers.run_fishery_cost_calculation
        )
        self.ui.btn_edit_matrix.clicked.connect(self.handlers.open_matrix_editor)
        self.ui.btn_run_conflict.clicked.connect(
            self.handlers.run_base_cost_calculation
        )
        self.ui.btn_run_total_cost.clicked.connect(
            self.handlers.run_total_cost_calculation
        )
        self.ui.btn_global_params.clicked.connect(
            self.handlers.open_global_params_editor
        )
        # 把预检按钮和后台弹窗函数连起来
        self.ui.btn_confirm_roles.clicked.connect(
            self.handlers.open_role_confirmation_dialog
        )
        # 正确对接按钮2和按钮3
        if hasattr(self.ui, "btn_run_current_conflict"):
            self.ui.btn_run_current_conflict.clicked.connect(
                self.handlers.run_current_conflict_calculation
            )

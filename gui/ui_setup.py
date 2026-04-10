from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QComboBox, QLineEdit, QGroupBox, QTreeWidget, 
                             QTabWidget, QCheckBox, QAbstractItemView, QStackedWidget, QTreeWidgetItem)
from PyQt6.QtCore import Qt
from scenarios.ui_builder import ScenarioUIBuilder

class UISetup:
    def __init__(self, main_window): 
        self.win = main_window
        self.scenario_controls = {} # 将由 ScenarioUIBuilder 填充

    def create_left_panel(self):
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setFixedWidth(420)
        
        self.phase1_widget = self._create_phase1_panel()
        self.phase2_widget = ScenarioUIBuilder(self).build_panel()
        
        self.stacked_widget.addWidget(self.phase1_widget)
        self.stacked_widget.addWidget(self.phase2_widget)
        
        return self.stacked_widget

    def _create_phase1_panel(self):
        panel = QWidget(); layout = QVBoxLayout(panel)
        
        gb_global = QGroupBox("💾 工作区状态 (Workspace)")
        l_global = QVBoxLayout(); h_btn_sys = QHBoxLayout()
        self.btn_save = QPushButton("保存(pkl)"); self.btn_load = QPushButton("载入(pkl)"); self.btn_export_shp = QPushButton("导出(SHP)")
        h_btn_sys.addWidget(self.btn_save); h_btn_sys.addWidget(self.btn_load); h_btn_sys.addWidget(self.btn_export_shp)
        l_global.addLayout(h_btn_sys)
        self.btn_reset = QPushButton("♻️ 彻底重置工作区"); self.btn_reset.setStyleSheet("background-color: #F44336; color: white; font-weight: bold;")
        l_global.addWidget(self.btn_reset); gb_global.setLayout(l_global); layout.addWidget(gb_global)

        self.tabs = QTabWidget()
        self.tab1 = QWidget(); self.tab2 = QWidget(); self.tab3 = QWidget(); self.tab4 = QWidget(); self.tab5 = QWidget()
        self.tabs.addTab(self.tab1, "1.底盘"); self.tabs.addTab(self.tab2, "2.图层"); self.tabs.addTab(self.tab3, "3.拥挤度")
        self.tabs.addTab(self.tab4, "4.渔业生计"); self.tabs.addTab(self.tab5, "5.成本矩阵")
        
        self._build_tab1(); self._build_tab2(); self._build_tab3(); self._build_tab4(); self._build_tab5()
        for i in range(1, 5): self.tabs.setTabEnabled(i, False)
        layout.addWidget(self.tabs)

        self.btn_to_phase2 = QPushButton("➡️ 下一步：确认成本并进入情景推演")
        self.btn_to_phase2.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; height: 45px;")
        layout.addWidget(self.btn_to_phase2)

        gb_view = QGroupBox("👁️ 视图控制"); l_view = QVBoxLayout()
        self.view_combo = QComboBox(); self.view_combo.addItems(["基础网格底盘 (Base Grid)", "已上传要素叠加 (All Features)"])
        l_view.addWidget(QLabel("主屏视图:")); l_view.addWidget(self.view_combo)
        h_legend = QHBoxLayout(); h_legend.addWidget(QLabel("图例位置:")); self.legend_combo = QComboBox(); self.legend_combo.addItems(["Outside Right", "Hide"]); h_legend.addWidget(self.legend_combo); l_view.addLayout(h_legend)
        h_coord = QHBoxLayout(); h_coord.addWidget(QLabel("坐标框:")); self.cb_top = QCheckBox("上"); self.cb_bottom = QCheckBox("下"); self.cb_bottom.setChecked(True); self.cb_left = QCheckBox("左"); self.cb_left.setChecked(True); self.cb_right = QCheckBox("右"); h_coord.addWidget(self.cb_top); h_coord.addWidget(self.cb_bottom); h_coord.addWidget(self.cb_left); h_coord.addWidget(self.cb_right); l_view.addLayout(h_coord); gb_view.setLayout(l_view); layout.addWidget(gb_view)
        return panel

    def _build_tab1(self): l = QVBoxLayout(self.tab1); self.btn_load_study = QPushButton("📁 1. 上传研究区域"); self.btn_load_study.setStyleSheet("background-color: #4FC3F7; font-weight: bold; height: 35px;"); l.addWidget(self.btn_load_study); l.addWidget(QLabel("等待上传...", objectName="lbl_status")); gb_crs = QGroupBox("🌐 坐标系管理"); cl = QVBoxLayout(); h_epsg = QHBoxLayout(); h_epsg.addWidget(QLabel("全局 EPSG:")); self.epsg_input = QLineEdit(); h_epsg.addWidget(self.epsg_input); cl.addLayout(h_epsg); self.btn_force_crs = QPushButton("⚙️ 强制重置坐标系"); cl.addWidget(self.btn_force_crs); gb_crs.setLayout(cl); l.addWidget(gb_crs); gb_grid = QGroupBox("🔲 规划单元"); gl = QVBoxLayout(); self.lbl_grid_info = QLabel("-"); gl.addWidget(self.lbl_grid_info); h_size = QHBoxLayout(); h_size.addWidget(QLabel("边长(米):")); self.grid_size_input = QLineEdit("250"); h_size.addWidget(self.grid_size_input); gl.addLayout(h_size); self.cb_remove_isolated = QCheckBox("剔除孤立飞地网格"); self.cb_remove_isolated.setChecked(True); gl.addWidget(self.cb_remove_isolated); self.btn_gen_grid = QPushButton("🚀 2. 生成基础规划网格"); self.btn_gen_grid.setStyleSheet("background-color: #FFB74D; font-weight: bold; height: 35px;"); gl.addWidget(self.btn_gen_grid); gb_grid.setLayout(gl); l.addWidget(gb_grid); l.addStretch()
    def _build_tab2(self): l = QVBoxLayout(self.tab2); h = QHBoxLayout(); self.btn_load_normal = QPushButton("📁 上传普通要素"); self.btn_load_eco = QPushButton("🌱 上传生态要素"); self.btn_load_eco.setStyleSheet("background-color: #81C784;"); h.addWidget(self.btn_load_normal); h.addWidget(self.btn_load_eco); l.addLayout(h); l.addWidget(QLabel("要素归类 (拖拽分组):")); self.layer_tree = QTreeWidget(); self.layer_tree.setHeaderHidden(True); self.layer_tree.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove); self.cat_inbox = QTreeWidgetItem(self.layer_tree, ["📥 待分类 (Inbox)"]); self.cat_inbox.setForeground(0, Qt.GlobalColor.blue); cat_marine = QTreeWidgetItem(self.layer_tree, ["🌊 海洋要素 (Marine)"]); cat_zone = QTreeWidgetItem(cat_marine, ["📁 分区要素 (10大分区)"]); QTreeWidgetItem(cat_zone, ["生态保护和控制区 (MPZ)"]); QTreeWidgetItem(cat_zone, ["城镇和工业用海区 (UIZ)"]); QTreeWidgetItem(cat_zone, ["港口航道区 (PSZ)"]); QTreeWidgetItem(cat_zone, ["旅游区 (TZ)"]); QTreeWidgetItem(cat_zone, ["生态旅游区 (TZE)"]); QTreeWidgetItem(cat_zone, ["传统渔业区 (FZT)"]); QTreeWidgetItem(cat_zone, ["商业渔业区 (FZC)"]); QTreeWidgetItem(cat_zone, ["水产养殖区 (FZA)"]); QTreeWidgetItem(cat_zone, ["特殊利用区 (SPZ)"]); QTreeWidgetItem(cat_zone, ["保留区 (RZ)"]); QTreeWidgetItem(cat_marine, ["⚠️ 影响要素 (海洋)"]); cat_land = QTreeWidgetItem(self.layer_tree, ["🌲 陆地要素 (Land)"]); QTreeWidgetItem(cat_land, ["🌱 高价值生态目标"]); QTreeWidgetItem(cat_land, ["🔴 强压力源"]); QTreeWidgetItem(cat_land, ["🟡 弱压力源"]); QTreeWidgetItem(cat_land, ["🔒 特殊锁定"]); self.layer_tree.expandAll(); l.addWidget(self.layer_tree); h_btn = QHBoxLayout(); self.btn_delete_feature = QPushButton("❌ 删除选中"); self.btn_delete_feature.setStyleSheet("color: red;"); self.btn_show_table = QPushButton("📊 属性表"); h_btn.addWidget(self.btn_delete_feature); h_btn.addWidget(self.btn_show_table); l.addLayout(h_btn)
    def _build_tab3(self): l = QVBoxLayout(self.tab3); self.btn_run_kde = QPushButton("▶ 空间拥挤度演算 (SCI)"); self.btn_run_kde.setStyleSheet("background-color: #BA68C8; color: white; font-weight: bold; height: 40px;"); l.addWidget(self.btn_run_kde); l.addStretch()
    def _build_tab4(self): l = QVBoxLayout(self.tab4); self.b_cost = QGroupBox("🌊 第一大产业：水产捕捞与养殖测算"); vl2 = QVBoxLayout(); self.btn_run_fishery_cost = QPushButton("▶ 选择基站，测算海域三大渔业依赖度"); self.btn_run_fishery_cost.setStyleSheet("background-color: #03A9F4; color: white; font-weight: bold; height: 40px;"); vl2.addWidget(self.btn_run_fishery_cost); self.b_cost.setLayout(vl2); l.addWidget(self.b_cost); l.addStretch()
    def _build_tab5(self): 
        l = QVBoxLayout(self.tab5)
        
        # 【找回丢失的全局参数按钮】
        self.btn_global_params = QPushButton("⚙️ 设置全局算法参数 (Gurobi & BLM 等)")
        self.btn_global_params.setStyleSheet("background-color: #FF5722; color: white; font-weight: bold; height: 35px;")
        l.addWidget(self.btn_global_params)

        # 模块 1：预检与现状
        self.gb_current = QGroupBox("👁️ 第一步：要素预检与现状矛盾 (Current Status)")
        gl = QVBoxLayout()
        self.btn_edit_matrix = QPushButton("📝 编辑 10x10 空间冲突矩阵")
        self.btn_confirm_roles = QPushButton("📋 1. 全局要素分类全域确认 (预检锁定)")
        self.btn_confirm_roles.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold; height: 35px;")
        self.btn_run_current_conflict = QPushButton("🔥 2. 生成全域现状矛盾热力图 (Conflict Index)")
        self.btn_run_current_conflict.setStyleSheet("background-color: #00BCD4; color: white; font-weight: bold; height: 35px;")
        gl.addWidget(self.btn_edit_matrix)
        gl.addWidget(self.btn_confirm_roles)
        gl.addWidget(self.btn_run_current_conflict)
        self.gb_current.setLayout(gl)
        l.addWidget(self.gb_current)

        # 模块 2：未来基础转换成本
        self.c_conf = QGroupBox("⚔️ 第二步：未来空间转换基础成本 (Base Transition Cost)")
        cl = QVBoxLayout()
        self.btn_run_conflict = QPushButton("▶ 3. 生成各分区基础转换成本 (Cost_to_Z)")
        self.btn_run_conflict.setStyleSheet("background-color: #E91E63; color: white; font-weight: bold; height: 40px;")
        cl.addWidget(self.btn_run_conflict)
        self.c_conf.setLayout(cl)
        l.addWidget(self.c_conf)

        # 模块 3：综合辐射排斥总成本
        self.c_total = QGroupBox("📉 第三步：叠加综合排斥总成本 (Total Extractive Cost)")
        cl2 = QVBoxLayout()
        self.btn_run_total_cost = QPushButton("▶ 4. 叠加陆源与周边辐射，生成终极成本 (Cost_L_Z)")
        self.btn_run_total_cost.setStyleSheet("background-color: #8E24AA; color: white; font-weight: bold; height: 35px;")
        self.btn_show_table_cost = QPushButton("📊 查看底层属性表")
        self.btn_show_table_cost.setStyleSheet("background-color: #607D8B; color: white; font-weight: bold; height: 35px;")
        cl2.addWidget(self.btn_run_total_cost)
        cl2.addWidget(self.btn_show_table_cost)
        self.c_total.setLayout(cl2)
        l.addWidget(self.c_total)

        l.addStretch()
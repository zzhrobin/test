import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import numpy as np


class PrioritizREngine:
    """
    对标 PrioritizR 核心逻辑的 Gurobi 求解引擎
    处理：多区划分配 (Multi-zone allocation)、成本最小化、边界惩罚 (BLM) 与 SCI 动态加权
    """

    def __init__(self, gdf, targets, global_params, conflict_matrix):
        # 1. 接收从 EventHandlers 传过来的干净、已归一化数据的题干
        self.gdf = gdf
        self.targets = targets
        self.params = global_params
        self.matrix = conflict_matrix

        # 提取所有的规划分区名称 (排除RZ后剩下的，例如 'Z1_MPZ', 'Z2_UIZ' 等)
        self.zones = [
            col.replace("Cost_to_", "")
            for col in self.gdf.columns
            if col.startswith("Cost_to_Z")
        ]
        self.num_grids = len(self.gdf)
        self.num_zones = len(self.zones)

        # 建立 Gurobi 模型环境
        self.model = gp.Model("MSP_Scenario_Optimization")

        # 按照用户界面的参数设置 Gurobi 求解器容差和时间上限
        self.model.setParam("TimeLimit", self.params.get("time_limit", 300))
        self.model.setParam("MIPGap", self.params.get("mip_gap", 0.05))

        # 存放决策变量的字典
        self.x = {}

    def build_model(self):
        """构建完整的数学规划模型"""
        self._add_decision_variables()
        self._add_hard_constraints()
        # self._add_target_constraints() # 第二批次提供
        # self._add_objective_function() # 第三批次提供

        self.model.update()
        print(
            f"[Gurobi] 模型构建完成: {self.num_grids} 个网格，{self.num_zones} 个候选功能区。"
        )

    def _add_decision_variables(self):
        """
        定义二元决策变量 x[i, j]：
        如果网格 i 被分配给功能区 j，则 x[i, j] = 1，否则为 0。
        """
        print("[Gurobi] 正在生成决策变量...")
        # 为了加速构建，使用 tupledict
        indices = [(i, j) for i in self.gdf.index for j in self.zones]
        self.x = self.model.addVars(indices, vtype=GRB.BINARY, name="x")

    def _add_hard_constraints(self):
        """
        添加绝对物理约束与用户锁定约束 (硬约束)
        """
        print("[Gurobi] 正在注入空间锁定与硬约束...")

        # 1. 唯一性约束 (Uniqueness Constraint)
        # 每个海洋网格必须且只能被分配给 1 个功能区
        for i in self.gdf.index:
            self.model.addConstr(
                gp.quicksum(self.x[i, j] for j in self.zones) == 1,
                name=f"Assign_Once_{i}",
            )

        # 2. 空间锁定约束 (Locked-in Constraint)
        # 提取上一阶段通过 UIZ > PSZ 等规则裁决后的最终锁定意向
        if "Final_Locked_Zone" in self.gdf.columns:
            locked_grids = self.gdf[self.gdf["Final_Locked_Zone"].notnull()]

            lock_count = 0
            for i, row in locked_grids.iterrows():
                locked_zone = row["Final_Locked_Zone"]

                # 必须确保锁定的目标区域在当前情景的计算列表中
                # 比如：Z2_UIZ 中包含 'UIZ'
                target_j = next((z for z in self.zones if locked_zone in z), None)

                if target_j:
                    # 强制将该决策变量设为 1，直接消解该变量，极大降低求解器负担
                    self.model.addConstr(
                        self.x[i, target_j] == 1, name=f"Locked_{i}_{target_j}"
                    )
                    lock_count += 1

            print(f"[Gurobi] 成功应用了 {lock_count} 个事前锁定网格。")

    def _add_target_constraints(self):
        """
        添加分区面积比例约束 (Soft/Target Constraints)
        按照 UI 面板设置的百分比，强制要求某类分区的网格数量达标。
        """
        print("[Gurobi] 正在注入大类/小类面积目标约束...")

        # 假设底盘网格面积均匀，总网格数作为基数
        total_grids = len(self.gdf)

        for zone_suffix, target_ratio in self.targets.items():
            if target_ratio <= 0:
                continue

            # 匹配具体的列名，例如从 'MPZ' 匹配到 'Z1_MPZ'
            target_j = next((z for z in self.zones if zone_suffix in z), None)

            if target_j:
                # 约束公式：划入该分区的网格总数 >= 设定的比例 * 总网格数
                min_grids_required = int(total_grids * target_ratio)
                self.model.addConstr(
                    gp.quicksum(self.x[i, target_j] for i in self.gdf.index)
                    >= min_grids_required,
                    name=f"Target_{target_j}",
                )
                print(
                    f"  - 目标约束: {target_j} 需 >= {target_ratio*100}% (至少 {min_grids_required} 个网格)"
                )

    def _add_objective_function(self, adj_pairs):
        """
        核心目标函数: Minimize (归一化成本 + BLM * SCI * 边界断裂惩罚)
        """
        print("[Gurobi] 正在构建复杂的空间目标函数...")

        # 1. 获取参数
        blm = self.params.get("base_blm", 1.0)
        sci_col = "Conflict_Index" if "Conflict_Index" in self.gdf.columns else None

        # 2. 基础成本项 (Base Cost)
        obj_expr = gp.LinExpr()
        for i in self.gdf.index:
            for j in self.zones:
                cost_val = self.gdf.at[i, f"Cost_to_{j}"]
                obj_expr += cost_val * self.x[i, j]

        # 3. 边界惩罚项 (Boundary Penalty) + SCI 加权
        # 原理：引入辅助变量 d[i,k]，如果 i 和 k 分区不同，d=1
        if adj_pairs and blm > 0:
            print(f"[Gurobi] 正在为 {len(adj_pairs)} 组邻居注入边界连片约束...")

            # 创建辅助变量 d[i, k]，表示邻居 i 和 k 是否【分区不一致】
            d = self.model.addVars(adj_pairs, vtype=GRB.BINARY, name="boundary")

            for i, k in adj_pairs:
                # 获取 SCI 加权值（取两个格子 SCI 的平均值，若无则默认为 1）
                sci_val = 1.0
                if sci_col:
                    sci_val = (self.gdf.at[i, sci_col] + self.gdf.at[k, sci_col]) / 2.0

                # 惩罚权重 = BLM * SCI加权
                penalty_weight = blm * sci_val

                # 数学约束：确保当 x[i,j] != x[k,j] 时，d[i,k] 必须为 1
                # 简化逻辑：对每个分区 j，如果 i 选了 j 但 k 没选，则断裂
                for j in self.zones:
                    self.model.addConstr(self.x[i, j] - self.x[k, j] <= d[i, k])
                    self.model.addConstr(self.x[k, j] - self.x[i, j] <= d[i, k])

                obj_expr += penalty_weight * d[i, k]

        self.model.setObjective(obj_expr, GRB.MINIMIZE)

    def solve(self):
        """
        启动 Gurobi 引擎进行正式求解，并提取结果
        """
        print("\n[Gurobi] 模型构建完毕，启动求解引擎...")

        # 在求解前调用上面写好的两步
        self._add_target_constraints()
        self._add_objective_function()

        # 更新并求解
        self.model.update()
        self.model.optimize()

        if self.model.status == GRB.OPTIMAL:
            print("\n[Gurobi] 求解成功！已找到满足所有约束的最优空间布局。")
            return self._extract_results()

        elif self.model.status == GRB.INFEASIBLE:
            print("\n[Gurobi] 警告：模型无解 (Infeasible)！")
            print(
                "原因可能是：\n 1. 比例目标加起来超过了100%\n 2. 预先锁定的格子与目标比例产生了死锁冲突"
            )
            # Gurobi 提供冲突排查工具，自动把冲突的方程写入文件
            self.model.computeIIS()
            self.model.write("model_conflict.ilp")
            return None

        else:
            print(f"\n[Gurobi] 求解被中断或未达到最优，状态码: {self.model.status}")
            # 如果到达时间上限，依然可以提取当前的最优可行解
            if self.model.SolCount > 0:
                print("提取当前找到的次优解...")
                return self._extract_results()
            return None

    def _extract_results(self):
        """将求解出的 0/1 决策变量翻译回 GeoDataFrame"""
        result_gdf = self.gdf.copy()
        result_gdf["Optimized_Zone"] = "Unassigned"

        for i in self.gdf.index:
            for j in self.zones:
                # Gurobi 的结果提取：变量名.x 会返回 1.0 或 0.0
                if self.x[i, j].x > 0.5:
                    result_gdf.at[i, "Optimized_Zone"] = j
                    break  # 找到分配的区划就跳出内循环

        return result_gdf

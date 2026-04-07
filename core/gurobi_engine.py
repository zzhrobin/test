import numpy as np
import gurobipy as gp
from gurobipy import GRB

def run_gurobi_optimization(total_cells, num_zones, cost_matrix, zone_quotas, locked_data, edges, edge_weights, conflict_matrix_2d, time_limit=300, mip_gap=0.05, is_mandatory=True):
    env = gp.Env(empty=True)
    env.setParam('OutputFlag', 1)
    env.setParam('MIPGap', mip_gap)       # 动态精度控制
    env.setParam('TimeLimit', time_limit)
    env.start()
    
    model = gp.Model("MSP_SCI_BLM_Optimization", env=env)
    x = model.addVars(total_cells, num_zones, vtype=GRB.BINARY, name="x")
    obj = gp.QuadExpr()

    for i in range(total_cells):
        for k in range(num_zones):
            if cost_matrix[i, k] < 9000:
                obj.addTerms(cost_matrix[i, k], x[i, k])

    if edges is not None and len(edges) > 0:
        for e_idx in range(len(edges)):
            i, j = edges[e_idx]
            w = edge_weights[e_idx]
            if w > 0:
                for k in range(num_zones):
                    for l in range(num_zones):
                        c_kl = conflict_matrix_2d[k, l]
                        if c_kl > 0: obj.addTerms(w * c_kl, x[i, k], x[j, l])

    model.setObjective(obj, GRB.MINIMIZE)

    # 【核心突破】：对标 R 语言的 add_mandatory_allocation_constraints
    for i in range(total_cells):
        if is_mandatory:
            model.addConstr(gp.quicksum(x[i, k] for k in range(num_zones)) == 1, name=f"Mandatory_{i}")
        else:
            # 允许留白 (Not Allocated)，即该网格可以不属于任何 10 大分区
            model.addConstr(gp.quicksum(x[i, k] for k in range(num_zones)) <= 1, name=f"Optional_{i}")

    for k in range(num_zones):
        if zone_quotas[k] > 0:
            model.addConstr(gp.quicksum(x[i, k] for i in range(total_cells)) >= zone_quotas[k])

    for cell_idx, target_zone_idx in locked_data:
        model.addConstr(x[cell_idx, target_zone_idx] == 1)

    model.optimize()

    if model.Status in [GRB.OPTIMAL, GRB.TIME_LIMIT, GRB.SUBOPTIMAL]:
        solution = np.full(total_cells, -1, dtype=object) # 默认 -1 表示留白
        for i in range(total_cells):
            for k in range(num_zones):
                if x[i, k].X > 0.5:
                    solution[i] = k
                    break
        return solution, f"✅ 求解成功！最终目标值: {model.ObjVal:.2f} (Gap: {model.MIPGap*100:.2f}%)"
    else:
        return None, f"❌ Gurobi 无解 (状态码: {model.Status})。目标配额可能冲突！"
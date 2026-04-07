import os
import pickle
import pandas as pd
import geopandas as gpd
from datetime import datetime
from core.scenario_engine import resolve_scenario_allocation
from run_sensitivity_paper import calculate_metrics


def run_batch():
    # 1. 指定你的进度文件路径 (请确保你已经在主界面保存了 msp_state.pkl)
    pkl_path = "msp_state.pkl"
    if not os.path.exists(pkl_path):
        print("❌ 找不到 msp_state.pkl！请先在软件主界面点击 [保存(pkl)]。")
        return

    print("📦 正在载入基础工作区...")
    with open(pkl_path, "rb") as f:
        state = pickle.load(f)

    grid_gdf = state["final_grid"]
    mapping = state.get("confirmed_mapping", {})
    global_params = state.get("global_params", {})
    custom_matrix = state.get("custom_matrix", {})

    # 调大时间限制，防止复杂模型半路夭折 (单位：秒)
    global_params["gurobi_time"] = 1200

    # 创建结果输出目录
    output_dir = f"Batch_Results_{datetime.now().strftime('%Y%m%d_%H%M')}"
    os.makedirs(output_dir, exist_ok=True)

    # ==========================================
    # 🧪 核心实验设计：在这里配置你要自动测试的所有参数组合！
    # ==========================================
    experiments = [
        # 实验组 1：低开发配额，不强制填满，无边界惩罚 (跑得最快)
        {
            "name": "Exp1_Low_Dev_No_BLM",
            "blm": 0.0,
            "mandatory": False,
            "targets": {"Z2_UIZ": 15, "Z3_PSZ": 15, "Z1_MPZ": 30, "Z6_FZT": 20},
        },
        # 实验组 2：中等配额，不强制填满，引入标准边界惩罚
        {
            "name": "Exp2_Mid_Dev_BLM_1",
            "blm": 1.0,
            "mandatory": False,
            "targets": {"Z2_UIZ": 25, "Z3_PSZ": 20, "Z1_MPZ": 25, "Z6_FZT": 30},
        },
        # 实验组 3：高强度开发，强制全域填满海洋 (跑得最慢，最容易无解)
        {
            "name": "Exp3_High_Dev_Mandatory",
            "blm": 0.5,
            "mandatory": True,
            "targets": {"Z2_UIZ": 40, "Z3_PSZ": 30, "Z1_MPZ": 15, "Z6_FZT": 15},
        },
    ]

    results_log = []

    print(f"\n🚀 开始全自动批处理，共 {len(experiments)} 组实验...")

    for i, exp in enumerate(experiments):
        print(f"\n==============================================")
        print(f"▶ 正在执行 [{i+1}/{len(experiments)}]: {exp['name']}")
        print(f"   参数: BLM={exp['blm']}, 强制分配={exp['mandatory']}")

        # 注入当前实验参数
        global_params["base_blm"] = exp["blm"]
        global_params["is_mandatory"] = exp["mandatory"]

        try:
            # 调起底层引擎
            res_gdf, report = resolve_scenario_allocation(
                grid_gdf=grid_gdf.copy(),
                scenario_name=exp["name"],
                confirmed_mapping=mapping,
                locked_features=[],  # 如果你需要锁定机场等，可以在这里填入列名列表，如 ['airport']
                zone_targets=exp["targets"],
                special_targets={},
                global_params=global_params,
                custom_matrix=custom_matrix,
            )

            # 判断是否解算成功
            if "Error_Infeasible" in res_gdf["Scenario_Zoning"].values:
                print(f"❌ 实验 {exp['name']} 模型无解 (配额冲突或时间耗尽)。")
                results_log.append(
                    {
                        "Experiment": exp["name"],
                        "Status": "Infeasible",
                        "Patches": None,
                        "Conflict_Cost": None,
                    }
                )
            else:
                # 统计论文核心指标
                patches, conflict = calculate_metrics(res_gdf, "Scenario_Zoning")
                print(f"✅ 求解成功！碎片数: {patches}, 冲突总成本: {conflict:.2f}")

                # 保存运行结果和报告
                results_log.append(
                    {
                        "Experiment": exp["name"],
                        "Status": "Optimal/Suboptimal",
                        "BLM": exp["blm"],
                        "Mandatory": exp["mandatory"],
                        "Patches": patches,
                        "Conflict_Cost": round(conflict, 2),
                    }
                )

                # 自动将本组的最优解导出为 Shapefile
                export_cols = ["geometry", "col_idx", "row_idx", "Scenario_Zoning"]
                # 把该情景专用的归一化成本列也带上
                cost_cols = [c for c in res_gdf.columns if c.startswith("S_")]
                out_gdf = res_gdf[export_cols + cost_cols].copy()

                shp_path = os.path.join(output_dir, f"{exp['name']}.shp")
                out_gdf.to_file(shp_path, driver="ESRI Shapefile")
                print(f"💾 SHP 结果已保存至: {shp_path}")

        except Exception as e:
            print(f"⚠️ 代码异常中断: {str(e)}")
            results_log.append(
                {"Experiment": exp["name"], "Status": f"Error: {str(e)[:30]}"}
            )

    # ==========================================
    # 📊 输出综合统计报表
    # ==========================================
    print("\n🎉 所有批处理任务执行完毕！")
    df_report = pd.DataFrame(results_log)
    csv_path = os.path.join(output_dir, "Batch_Experiment_Report.csv")
    df_report.to_csv(csv_path, index=False, encoding="utf-8-sig")

    print("\n================ 最终报告 ================")
    print(df_report.to_string(index=False))
    print(f"==========================================")
    print(f"所有 Shapefile 和汇总报表已存入文件夹: {output_dir}/")


if __name__ == "__main__":
    run_batch()

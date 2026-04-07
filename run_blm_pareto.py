import os
import pickle
import pandas as pd
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog
from core.scenario_engine import resolve_scenario_allocation
from run_sensitivity_paper import calculate_metrics

# 兼容中文字体
plt.rcParams["font.sans-serif"] = [
    "SimHei",
    "Microsoft YaHei",
    "Arial Unicode MS",
    "sans-serif",
]
plt.rcParams["axes.unicode_minus"] = False


def generate_pareto_frontier():
    root = tk.Tk()
    root.withdraw()
    print("⏳ 请选择你保存的 MSP 进度文件 (.pkl)...")
    pkl_path = filedialog.askopenfilename(
        title="选择进度文件", filetypes=[("Pickle", "*.pkl")]
    )
    if not pkl_path:
        return

    with open(pkl_path, "rb") as f:
        state = pickle.load(f)

    grid_gdf = state["final_grid"]
    mapping = state.get("confirmed_mapping", {})
    global_params = state.get("global_params", {})
    custom_matrix = state.get("custom_matrix", {})

    # 经典的 BLM 测试梯度 (从完全不惩罚到极度惩罚)
    blm_test_values = [0.0, 0.01, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
    results = []

    # 为了保证能算出解，这里的测试配额设得比较保守 (15%)
    scenario_name = "开发优先"
    zone_targets = {"Z2_UIZ": 15, "Z3_PSZ": 15, "Z4_TZ": 15, "Z6_FZT": 15}

    print("🚀 开始执行 BLM 帕累托边界扫描...")
    for blm in blm_test_values:
        print(f"\n---> 正在测试 BLM = {blm}")
        global_params["base_blm"] = blm

        try:
            res_gdf, report = resolve_scenario_allocation(
                grid_gdf.copy(),
                scenario_name,
                mapping,
                [],
                zone_targets,
                {},
                global_params,
                custom_matrix,
            )

            if "Error_Infeasible" in res_gdf["Scenario_Zoning"].values:
                print(f"❌ BLM={blm} 时无解，跳过。")
                continue

            patches, conflict = calculate_metrics(res_gdf, "Scenario_Zoning")
            results.append({"BLM": blm, "Patches": patches, "Conflict_Cost": conflict})
            print(f"✅ 完成! 孤立碎片数: {patches}, 冲突总成本: {conflict:.2f}")

        except Exception as e:
            print(f"⚠️ 发生错误: {e}")

    if not results:
        print("\n💥 所有测试均无解！请检查底盘数据或进一步调低测试配额。")
        return

    # === 绘制帕累托曲线 ===
    df = pd.DataFrame(results)
    plt.figure(figsize=(9, 6))

    # 核心权衡图：X轴为碎片数(越小越好)，Y轴为成本(越小越好)
    plt.plot(
        df["Patches"],
        df["Conflict_Cost"],
        marker="o",
        markersize=8,
        linestyle="-",
        color="#E91E63",
        linewidth=2,
    )

    for i, row in df.iterrows():
        plt.annotate(
            f"BLM={row['BLM']}",
            (row["Patches"], row["Conflict_Cost"]),
            textcoords="offset points",
            xytext=(10, 10),
            ha="left",
            fontsize=9,
        )

    plt.title("边界惩罚与冲突成本权衡曲线 (Pareto Frontier)", fontsize=14, pad=15)
    plt.xlabel("空间碎片化程度 (孤立斑块数量)", fontsize=12)
    plt.ylabel("综合冲突总成本 (Total Extractive Cost)", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.6)

    # 寻找拐点逻辑：曲线最靠近左下角 (理想点) 的那个真实点
    plt.plot(
        df["Patches"].min(),
        df["Conflict_Cost"].min(),
        marker="*",
        color="gold",
        markersize=15,
        label="理想乌托邦点 (无法达到)",
    )
    plt.legend()

    out_path = os.path.join(os.path.dirname(pkl_path), "BLM_Pareto_Frontier.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"\n🎉 帕累托曲线已保存至: {out_path}")


if __name__ == "__main__":
    generate_pareto_frontier()

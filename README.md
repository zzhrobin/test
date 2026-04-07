# 海洋空间规划决策支持系统 (MSP-DSS) 项目交接说明

## 1. 项目概述 (Project Overview)
这是一个为印度尼西亚巴厘巴板湾定制开发的海洋空间规划（MSP）桌面决策支持系统（DSS）。

**核心目标**：量化和可视化多种海洋功能（如航道、养殖、保护区）之间的**空间拥挤度/冲突（SCI指数）**，并评估特定情景下的**机会成本**（目前已实现渔业成本模型）。

该系统使用 Python 和 PyQt6 构建，所有空间分析均由 `geopandas` 在后端完成。

## 2. 核心科学工作流 (Core Scientific Workflow)
软件的运行遵循严格的四步分析流程，这与UI上的四个选项卡一一对应：

1.  **网格底盘构建 (Tab 1)**
    *   用户上传研究区域的边界（Shapefile）。
    *   系统将其投影到米制单位（如 EPSG:3857），并以此为基础生成一个均匀的方形网格 `GeoDataFrame`。这个网格是所有后续分析的基础单元。
    *   *相关代码: `core/grid_topology.py`*

2.  **要素空间交集 (Tab 2)**
    *   用户上传多个代表不同海洋功能的矢量图层（Shapefile）。
    *   系统会将这些图层与第一步生成的网格进行空间相交，并将结果作为新的属性列（例如 `M_航道=1`, `M_养殖=1`）附加到网格 `GeoDataFrame` 中。
    *   *相关代码: `core/spatial_intersect.py`*

3.  **拥挤度/冲突计算 (Tab 3)**
    *   用户从已加载的要素中勾选出那些被认为会引发“拥挤”的要素。
    *   系统对这些要素的空间分布进行一次**双尺度核密度估计（Dual-scale KDE）**，生成一个综合的**空间拥挤度指数（SCI）**，并以热力图形式可视化。
    *   *相关代码: `core/kde_engine.py`*

4.  **机会成本构建 (Tab 4)**
    *   目前实现了**渔业机会成本模型**。
    *   用户需上传**渔村位置**和**海湾范围**两个Shapefile。
    *   算法会根据预设规则计算成本：
        *   **湾外区域**：被视为远洋，成本为固定的 `0.4`。
        *   **湾内区域**：成本与到最近渔村的距离相关，在15km范围内呈线性衰减。超出15km则成本为0。
    *   *相关代码: `core/cost_engine.py`*

## 3. 项目代码结构 (Project Code Structure)
项目遵循模块化设计，主要分为 `gui` 和 `core` 两大块：

*   `main.py`: **程序主入口**，负责启动PyQt应用和主窗口。
*   `gui/`: **图形用户界面**
    *   `main_window.py`: 主窗口，作为“总指挥”，协调UI、事件和绘图三大模块。
    *   `ui_setup.py`: “UI布局工程师”，负责创建所有的按钮、标签页、列表等组件。
    *   `event_handlers.py`: “事件响应中心”，包含所有按钮点击后触发的复杂逻辑（如加载文件、启动计算）。
    *   `plotting.py`: “绘图工作室”，管理主画布的刷新和所有热力图的绘制。
*   `core/`: **核心算力引擎**
    *   `grid_topology.py`: 网格生成。
    *   `spatial_intersect.py`: 空间相交。
    *   `kde_engine.py`: SCI计算。
    *   `cost_engine.py`: 成本计算。

## 4. 关键技术栈 (Key Technology Stack)
*   **GUI**: `PyQt6`
*   **空间分析**: `geopandas`, `shapely`
*   **科学计算**: `numpy`, `scipy`
*   **数据可视化**: `matplotlib`
*   **数据持久化**: `pickle` (用于保存/读取工作区状态)

## 5. 当前状态与重要修复历史 (v1.8)
*   **功能状态**：v1.8版本，核心功能已全部实现且稳定。
*   **几何错误修复**：项目曾频繁遭遇 `Component rings have coordinate sequences...` 拓扑错误。最终通过在 `core/cost_engine.py` 中使用 `shapely.wkb` 强制剥离Z轴，并用 `.buffer(0)` 修复拓扑，最后改用 `gpd.sjoin` 替代 `unary_union` 的方式被**彻底解决**。
*   **索引错位修复**：修复了因 Pandas 索引不连续导致的“花屏条纹”Bug。通过在 `cost_engine.py` 开头强制 `reset_index(drop=True)` 并使用 `.loc` 安全赋值解决。
*   **面状数据兼容**：`cost_engine.py` 已支持“渔村”数据为面状（Polygon），通过自动计算其质心（Centroid）作为距离计算的起点。
*   **UI与绘图Bug**：修复了 Matplotlib 图例无限叠加和中文字体乱码的问题。
*   **代码重构**：项目已从单个巨大的 `main_window.py` 文件重构为 `gui/` 下的多个模块，结构清晰，易于维护。

## 6. 未来工作方向 (To the Next AI)
请在此处告诉下一个AI你希望继续做什么，例如：
*   “我希望增加一个新的成本计算模块，比如航运成本...”
*   “我希望能够将最终的成本图层导出为新的Shapefile文件...”
*   “我希望在UI上增加一个参数X，用来调整Y算法...”

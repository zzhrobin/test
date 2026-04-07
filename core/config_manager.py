import json
import os
from datetime import datetime
from core.cost_engine import DEFAULT_CONFLICT_MATRIX_10

class MetadataLogger:
    def __init__(self):
        self.metadata = {
            "experiment_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "project": "Balikpapan Bay MSP SDSS",
            "grid_settings": {},
            "sci_kde_settings": {
                "sigma_short": 3.0,
                "sigma_long": 10.0,
                "robust_normalization": True
            },
            "conflict_matrix_snapshot": DEFAULT_CONFLICT_MATRIX_10,
            "scenario_allocation": {
                "target_ratios": "38% (Low) : 34% (Mid) : 28% (High)",
                "eco_anchor_ikn": "Enabled (Distance decay applied)",
                "land_sea_synergy": "Enabled (50% reduction for near-coast villages)"
            },
            "execution_scenario": ""
        }

    def set_grid_info(self, epsg, size, count):
        self.metadata["grid_settings"] = {"EPSG": epsg, "cell_size_m": size, "total_cells": count}

    def log_run(self, scenario_name, mode):
        self.metadata["execution_scenario"] = f"{scenario_name} (Mode: {mode})"

    def export(self, output_dir="."):
        # 生成带时间戳的 JSON 文件名，绝对不会覆盖之前的数据
        time_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Run_Metadata_{time_str}.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=4)
        return filepath
"""Create manuscript-ready figures from paper_outputs CSV files."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PAPER_DIR = Path("paper_outputs")
FIG_DIR = PAPER_DIR / "figures"
DEFAULT_BLM = 3e-4
DEFAULT_THETA = "theta_0.2_1.0"
STABILITY_THETA = "theta_0.3_0.9"
DEFAULT_GROUP = "baseline"
STABILITY_GROUP = "compressed_weights"
ALT_GROUP = "transit_heavier"


def prepare_alpha_beta_figure_csv() -> Path:
    src = PAPER_DIR / "alpha_beta_sensitivity_summary_table.csv"
    dst = PAPER_DIR / "figure_alpha_beta_sensitivity.csv"
    df = pd.read_csv(src)
    out = df[
        [
            "setting_label",
            "theta_min",
            "theta_max",
            "sci_alpha",
            "sci_beta",
            "objective_diff_adaptive_minus_fixed",
            "boundary_diff_adaptive_minus_fixed",
            "patch_diff_adaptive_minus_fixed",
            "different_cells",
            "fixed_adaptive_overlap_share",
        ]
    ].copy()
    out.to_csv(dst, index=False, encoding="utf-8-sig")
    return dst


def _save(fig: plt.Figure, stem: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_DIR / f"{stem}.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG_DIR / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_blm_sweep() -> None:
    df = pd.read_csv(PAPER_DIR / "figure_blm_sweep.csv").sort_values("base_blm")
    fig, axes = plt.subplots(3, 1, figsize=(8.2, 9.2), sharex=True)

    series = [
        ("objective_diff_adaptive_minus_fixed", "Objective Diff"),
        ("different_cells", "Different Cells"),
        ("patch_diff_adaptive_minus_fixed", "Patch Diff"),
    ]
    color = "#1f4e79"
    accent = "#c0392b"

    for ax, (col, ylabel) in zip(axes, series):
        ax.plot(df["base_blm"], df[col], marker="o", color=color, linewidth=2)
        ax.axvline(DEFAULT_BLM, color=accent, linestyle="--", linewidth=1.5)
        default_row = df.loc[df["base_blm"] == DEFAULT_BLM].iloc[0]
        ax.scatter([DEFAULT_BLM], [default_row[col]], color=accent, s=55, zorder=3)
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.25)

    axes[-1].set_xscale("log")
    axes[-1].set_xlabel("base_blm (log scale)")
    axes[0].set_title("BLM Sweep: Adaptive minus Fixed")
    axes[0].text(
        DEFAULT_BLM,
        axes[0].get_ylim()[1] * 0.95,
        "default 3e-4",
        color=accent,
        ha="left",
        va="top",
    )
    fig.tight_layout()
    _save(fig, "blm_sweep")


def _highlight_colors(labels: list[str], default_label: str, stability_label: str, alt_label: str | None = None):
    colors = []
    for label in labels:
        if label == default_label:
            colors.append("#c0392b")
        elif label == stability_label:
            colors.append("#1f4e79")
        elif alt_label is not None and label == alt_label:
            colors.append("#6c7a89")
        else:
            colors.append("#b7c4cf")
    return colors


def plot_theta_sensitivity() -> None:
    df = pd.read_csv(PAPER_DIR / "figure_theta_sensitivity.csv")
    labels = df["setting_label"].tolist()
    x = range(len(labels))
    colors = _highlight_colors(labels, DEFAULT_THETA, STABILITY_THETA)

    fig, axes = plt.subplots(2, 1, figsize=(8.5, 7.8), sharex=True)
    axes[0].bar(x, df["objective_diff_adaptive_minus_fixed"], color=colors)
    axes[0].set_ylabel("Objective Diff")
    axes[0].set_title("Theta Sensitivity")
    axes[0].grid(True, axis="y", alpha=0.25)

    axes[1].bar(x, df["different_cells"], color=colors)
    axes[1].set_ylabel("Different Cells")
    axes[1].grid(True, axis="y", alpha=0.25)
    axes[1].set_xticks(list(x))
    axes[1].set_xticklabels(labels, rotation=20, ha="right")

    for ax in axes:
        for idx, label in enumerate(labels):
            if label in {DEFAULT_THETA, STABILITY_THETA}:
                ax.annotate(
                    "default" if label == DEFAULT_THETA else "stability",
                    (idx, ax.patches[idx].get_height()),
                    xytext=(0, 6),
                    textcoords="offset points",
                    ha="center",
                    fontsize=8,
                )

    fig.tight_layout()
    _save(fig, "theta_sensitivity")


def plot_group_weight_sensitivity() -> None:
    df = pd.read_csv(PAPER_DIR / "figure_group_weight_sensitivity.csv")
    labels = df["setting_label"].tolist()
    x = range(len(labels))
    colors = _highlight_colors(labels, DEFAULT_GROUP, STABILITY_GROUP, ALT_GROUP)

    fig, axes = plt.subplots(2, 1, figsize=(8.8, 7.6), sharex=True)
    axes[0].bar(x, df["objective_diff_adaptive_minus_fixed"], color=colors)
    axes[0].set_ylabel("Objective Diff")
    axes[0].set_title("Group-Weight Sensitivity")
    axes[0].grid(True, axis="y", alpha=0.25)

    axes[1].plot(x, df["fixed_adaptive_overlap_share"], marker="o", color="#1f4e79", linewidth=2)
    axes[1].set_ylabel("Overlap Share")
    axes[1].set_ylim(0.9997, 1.0000)
    axes[1].grid(True, axis="y", alpha=0.25)
    axes[1].set_xticks(list(x))
    axes[1].set_xticklabels(labels, rotation=20, ha="right")

    for idx, label in enumerate(labels):
        if label in {DEFAULT_GROUP, STABILITY_GROUP, ALT_GROUP}:
            axes[0].annotate(
                label,
                (idx, axes[0].patches[idx].get_height()),
                xytext=(0, 6),
                textcoords="offset points",
                ha="center",
                fontsize=8,
            )

    fig.tight_layout()
    _save(fig, "group_weight_sensitivity")


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    prepare_alpha_beta_figure_csv()
    plot_blm_sweep()
    plot_theta_sensitivity()
    plot_group_weight_sensitivity()
    print(f"Wrote figures to {FIG_DIR}")


if __name__ == "__main__":
    main()

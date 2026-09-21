"""Figures for the README and the report.

House style: the title states the finding rather than naming the variable, the series
that carries the finding is in colour and everything else is grey, the grid is a
recessive hairline, labels are selective, and the footer names the source and the
collection date.

Palette: highlight #2a78d6, de-emphasis #898781, both checked for contrast against the
#fcfcfb surface and for separation under simulated colour vision deficiency. The grey is
deliberate de-emphasis, not a second category.
"""
from __future__ import annotations

import logging
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.config import DATA_PROCESSED, FIGURES

log = logging.getLogger("figures")

HIGHLIGHT = "#2a78d6"
MUTED = "#898781"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e1e0d9"
SURFACE = "#fcfcfb"
SOURCE = "Source: SALIC API (api.salic.cultura.gov.br), collected 2026-09-20. Approval cohorts 2019 to 2022, fundraising window closed, n = 12,722."

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "font.family": "DejaVu Sans", "font.size": 10,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "grid.linestyle": "-", "axes.axisbelow": True,
})


def _frame(ax, xgrid=True):
    for side in ("top", "right", "left" if xgrid else "bottom"):
        ax.spines[side].set_visible(False)
    ax.grid(axis="x" if xgrid else "y")
    ax.grid(axis="y" if xgrid else "x", visible=False)


def _finish(fig, title, subtitle=None):
    """Wrap by figure width rather than by eye, so a longer subtitle cannot silently
    run off the canvas."""
    width_in = fig.get_size_inches()[0]
    fig.text(0.02, 0.97, "\n".join(textwrap.wrap(title, int(width_in * 9.2))),
             ha="left", va="top", fontsize=13.5, fontweight="bold", color=INK)
    if subtitle:
        fig.text(0.02, 0.885, "\n".join(textwrap.wrap(subtitle, int(width_in * 13.5))),
                 ha="left", va="top", fontsize=9.5, color=INK2, linespacing=1.4)
    fig.text(0.02, 0.015, "\n".join(textwrap.wrap(SOURCE, int(width_in * 18))),
             ha="left", va="bottom", fontsize=7, color=MUTED, linespacing=1.4)


def value_band(v: pd.Series) -> pd.Series:
    return pd.cut(v, [0, 1e5, 5e5, 1e6, 5e6, np.inf],
                  labels=["Under 100k", "100k to 500k", "500k to 1M",
                          "1M to 5M", "5M and above"])


def fig_value_band(s: pd.DataFrame) -> None:
    d = s.assign(band=value_band(s["valor_solicitado"]))
    g = d.groupby("band", observed=True)["target_ge50"].agg(["size", "mean"])
    worst = g["mean"].idxmin()
    colors = [HIGHLIGHT if b == worst else MUTED for b in g.index]

    fig, ax = plt.subplots(figsize=(8.2, 4.0))
    fig.subplots_adjust(left=0.20, right=0.97, top=0.82, bottom=0.17)
    y = np.arange(len(g))
    ax.barh(y, g["mean"] * 100, color=colors, height=0.48)
    ax.set_yticks(y, g.index, fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel("Reached at least half the requested amount (%)")
    ax.set_xlim(0, max(g["mean"] * 100) * 1.18)
    _frame(ax)
    # Label only the bars, with the sample size, since there are few of them.
    for i, (n, m) in enumerate(zip(g["size"], g["mean"])):
        ax.text(m * 100 + 0.8, i, f"{m*100:.0f}%  (n={n:,})", va="center",
                fontsize=9, color=INK if g.index[i] == worst else INK2)
    _finish(fig, "Asking for 100k to 500k gives the worst odds of getting funded",
            "Share of approved projects that raised at least half of what they asked for, "
            "by size of the request")
    fig.savefig(FIGURES / "funding_by_value_band.png", dpi=200)
    plt.close(fig)


def fig_cohorts(all_rows: pd.DataFrame) -> None:
    d = all_rows[all_rows["ano_projeto"] >= 2019]
    g = d.groupby("ano_projeto").agg(
        pct_open=("window_state", lambda x: (x == "open").mean()))
    # The rate each cohort appears to have, computed the same way for every cohort.
    # For cohorts that are still open it is biased downwards, which is the point.
    apparent = (d[d["window_state"].eq("closed") & d["has_requested_amount"]]
                .groupby("ano_projeto")["target_ge50"].mean())
    usable = g["pct_open"] < 0.05

    fig, ax = plt.subplots(figsize=(8.6, 4.2))
    fig.subplots_adjust(left=0.10, right=0.99, top=0.78, bottom=0.17)
    x = np.arange(len(g))
    vals = [apparent.get(y, np.nan) * 100 for y in g.index]
    colors = [HIGHLIGHT if usable[y] else MUTED for y in g.index]
    ax.bar(x, vals, color=colors, width=0.5)
    ax.set_xticks(x, [str(int(y)) for y in g.index])
    ax.set_ylabel("Reached at least half\nthe requested amount (%)", labelpad=8)
    ax.set_ylim(0, 58)
    _frame(ax, xgrid=False)
    for i, y in enumerate(g.index):
        if usable[y]:
            ax.text(i, vals[i] + 1.4, f"{vals[i]:.0f}%", ha="center", fontsize=9.5,
                    color=INK, fontweight="bold")
        else:
            ax.text(i, vals[i] + 1.4, f"{vals[i]:.0f}%", ha="center", fontsize=9,
                    color=MUTED)
            ax.text(i, vals[i] + 6.5, f"{g['pct_open'][y]*100:.0f}% of the\ncohort is\nstill raising",
                    ha="center", fontsize=7.5, color=MUTED, linespacing=1.35)
    _finish(fig, "The rate is flat where it can be measured, and unreadable after 2022",
            "Grey cohorts are still raising money. The projects that close first are the ones "
            "that closed empty, so their apparent rate is biased downwards")
    fig.savefig(FIGURES / "funding_by_cohort.png", dpi=200)
    plt.close(fig)


def fig_concentration(s: pd.DataFrame) -> None:
    g = s.groupby("proponente_hash")["valor_captado"].sum().sort_values()
    g = g[g.notna()]
    cum = np.cumsum(g.to_numpy()) / g.sum()
    x = np.arange(1, len(g) + 1) / len(g)
    top10 = 1 - cum[int(len(g) * 0.9) - 1]

    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    fig.subplots_adjust(left=0.11, right=0.97, top=0.80, bottom=0.22)
    ax.plot([0, 1], [0, 1], color=MUTED, linewidth=1.2)
    ax.plot(x, cum, color=HIGHLIGHT, linewidth=2)
    ax.fill_between(x, cum, x, color=HIGHLIGHT, alpha=0.08)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_xlabel("Proponents, poorest to richest in money raised")
    ax.set_ylabel("Cumulative share of all money raised")
    _frame(ax, xgrid=False); ax.grid(axis="x")
    ax.annotate(f"The top 10% of proponents\nraised {top10*100:.0f}% of all the money",
                xy=(0.895, cum[int(len(g) * 0.9) - 1]), xytext=(0.42, 0.30),
                fontsize=9.5, color=INK, ha="left",
                arrowprops=dict(arrowstyle="-", color=MUTED, linewidth=1))
    _finish(fig, f"{top10*100:.0f}% of the money went to 10% of the proponents",
            "Lorenz curve of money raised per proponent. The straight line is perfect equality")
    fig.savefig(FIGURES / "concentration_proponents.png", dpi=200)
    plt.close(fig)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    FIGURES.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(DATA_PROCESSED / "projetos.parquet")
    s = df[df["in_model_sample"]]
    fig_value_band(s)
    fig_cohorts(df)
    fig_concentration(s)
    for p in sorted(FIGURES.glob("*.png")):
        log.info("wrote %s (%.0f KB)", p.name, p.stat().st_size / 1024)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

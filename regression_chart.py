"""Standalone creative regression chart — also used as a sanity-check exporter."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("WC_DATA_DIR", PROJECT_ROOT / "data"))

CSV_PATH = DATA_DIR / "team_statistics.csv"
OUTPUT_HTML = DATA_DIR / "attempts_vs_goals.html"


def build_figure() -> go.Figure:
    df = pd.read_csv(CSV_PATH)
    if "Rank" not in df.columns:
        df = df.rename(columns={df.columns[0]: "Rank"})
    for col in ["Attempts At Goal", "Goals", "xG", "Possession Control (%)"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["Attempts At Goal", "Goals"]).reset_index(drop=True)

    x = df["Attempts At Goal"].to_numpy()
    y = df["Goals"].to_numpy()
    n = len(df)

    slope, intercept = np.polyfit(x, y, 1)
    x_line = np.linspace(x.min() - 1, x.max() + 1, 200)
    y_line = slope * x_line + intercept

    y_pred = slope * x + intercept
    ss_res = float(np.sum((y - y_pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot else float("nan")

    x_mean = x.mean()
    sxx = float(np.sum((x - x_mean) ** 2)) or 1.0
    s_err = float(np.sqrt(ss_res / max(n - 2, 1)))
    t_crit = 2.013
    se_mean = s_err * np.sqrt(1.0 / n + (x_line - x_mean) ** 2 / sxx)
    band = t_crit * se_mean

    df["Residual"] = y - y_pred
    res_abs_max = float(np.max(np.abs(df["Residual"]))) or 1.0

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=np.concatenate([x_line, x_line[::-1]]),
        y=np.concatenate([y_line + band, (y_line - band)[::-1]]),
        fill="toself",
        fillcolor="rgba(120,120,120,0.12)",
        line=dict(color="rgba(0,0,0,0)"),
        hoverinfo="skip",
        name="95% confidence band",
        showlegend=True,
    ))
    fig.add_trace(go.Scatter(
        x=x_line, y=y_line, mode="lines",
        line=dict(color="#111111", width=2, dash="dash"),
        name=f"Trend  y = {slope:.3f}x + {intercept:.2f}   R² = {r2:.2f}",
        hoverinfo="skip",
    ))

    rng = np.random.default_rng(7)
    x_jit = x + rng.uniform(-0.05, 0.05, size=n)

    fig.add_trace(go.Scatter(
        x=x_jit, y=y, mode="markers+text",
        text=df["Team"], textposition="top center",
        textfont=dict(size=10, color="#222"),
        marker=dict(
            size=df["xG"],
            sizemode="area",
            sizeref=2.0 * df["xG"].max() / (55.0 ** 2),
            sizemin=6,
            color=df["Residual"],
            colorscale="RdYlGn",
            cmin=-res_abs_max,
            cmax=res_abs_max,
            line=dict(width=1, color="#333"),
            colorbar=dict(
                title=dict(text="Goals vs trend<br>(over / under)", side="right"),
                thickness=14, len=0.6, x=1.02,
            ),
        ),
        customdata=np.stack(
            [df["Team"], df["Rank"], df["xG"],
             df["Possession Control (%)"], df["Residual"].round(2)], axis=-1
        ),
        hovertemplate=(
            "<b>%{customdata[0]}</b> (rank %{customdata[1]})<br>"
            "Attempts: %{x:.0f}<br>Goals: %{y:.0f}<br>"
            "xG: %{customdata[2]}<br>Possession: %{customdata[3]}%<br>"
            "Over/under trend: %{customdata[4]:+.2f}<extra></extra>"
        ),
        name="Teams", showlegend=False,
    ))

    top_over = df.nlargest(3, "Residual")
    top_under = df.nsmallest(3, "Residual")
    for _, row in pd.concat([top_over, top_under]).iterrows():
        fig.add_annotation(
            x=row["Attempts At Goal"], y=row["Goals"],
            text=f"<b>{row['Team']}</b>",
            showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1,
            arrowcolor="#444",
            ax=0, ay=-30 if row["Residual"] > 0 else 30,
            font=dict(size=11, color="#000"),
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#444", borderwidth=1, borderpad=3,
        )

    fig.update_layout(
        title=dict(
            text=(
                "<b>FIFA World Cup 2026 — Attempts At Goal vs Goals</b><br>"
                "<span style='font-size:13px;color:#555'>"
                "Bubble size = xG · Color = goals vs. trend (over / under). "
                f"R² = {r2:.2f}, n = {n}."
                "</span>"
            ),
            x=0.02, xanchor="left",
        ),
        xaxis=dict(title="Attempts At Goal", gridcolor="#eee", zeroline=False),
        yaxis=dict(title="Goals", gridcolor="#eee", zeroline=False),
        plot_bgcolor="white", paper_bgcolor="white",
        width=1300, height=820,
        margin=dict(l=70, r=120, t=110, b=70),
    )
    return fig


if __name__ == "__main__":
    fig = build_figure()
    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(OUTPUT_HTML, include_plotlyjs="cdn")
    print(f"Wrote {OUTPUT_HTML}")

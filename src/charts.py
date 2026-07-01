"""Plotly figures for the four panels — light Material theme."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .data_loader import get
from .features import DNA_FIELDS, percentile_rank
from .models import OLSResult, fit_ols_regression
from .tournament import ELIMINATED


# ---------------------------------------------------------------------------
# Theme — Google / Material light
# ---------------------------------------------------------------------------

BG = "#ffffff"
PANEL = "#ffffff"
SURFACE = "#f8f9fa"
GRID = "#e8eaed"
TEXT = "#202124"
MUTED = "#5f6368"
PRIMARY = "#1a73e8"
PRIMARY_LIGHT = "#4285f4"
ACCENT = "#1967d2"
GOOD = "#188038"
WARN = "#d93025"
NEON = "#fbbc04"

FONT = "Roboto, system-ui, -apple-system, sans-serif"


def _empty(message: str, height: int = 420) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message, showarrow=False,
        font=dict(color=MUTED, size=14, family=FONT),
        x=0.5, y=0.5, xref="paper", yref="paper",
    )
    fig.update_layout(
        paper_bgcolor=BG, plot_bgcolor=BG,
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        margin=dict(l=20, r=20, t=40, b=20),
        autosize=True,
    )
    return fig


def _base_layout(fig: go.Figure, title: str, height: int = 420) -> None:
    # Title is supplied by the HTML banner above the chart, so we leave the
    # Plotly title empty and reclaim the vertical space.
    fig.update_layout(
        title=None,
        paper_bgcolor=BG, plot_bgcolor=BG,
        font=dict(color=TEXT, family=FONT, size=11),
        xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, color=MUTED, linecolor=GRID),
        yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, color=MUTED, linecolor=GRID),
        margin=dict(l=50, r=20, t=18, b=44),
        autosize=True,
        hoverlabel=dict(bgcolor="white", font=dict(color=TEXT, family=FONT),
                        bordercolor=GRID),
    )


# ---------------------------------------------------------------------------
# Chart 1 — PERSISTENT regression (does not depend on selected team)
# Ported from regression_chart.py: confidence band, team labels, color = residual,
# bubble size = xG, callouts for biggest over/under-performers.
# ---------------------------------------------------------------------------


def goals_vs_attempts_persistent(df: pd.DataFrame, height: int = 460) -> tuple[go.Figure, OLSResult]:
    """One figure for all teams; identical regardless of dropdown selection."""

    x = pd.to_numeric(get(df, "attempts_at_goal"), errors="coerce")
    y = pd.to_numeric(get(df, "goals"), errors="coerce")
    xg = pd.to_numeric(get(df, "xg"), errors="coerce")

    mask = x.notna() & y.notna()
    if mask.sum() < 3:
        return _empty("Missing Attempts At Goal or Goals", height), OLSResult(
            0, 0, float("nan"), 0, pd.Series(dtype=float), pd.Series(dtype=float)
        )

    teams = df.loc[mask, "Team"].reset_index(drop=True)
    x_arr = x.loc[mask].to_numpy(dtype=float)
    y_arr = y.loc[mask].to_numpy(dtype=float)
    xg_arr = xg.loc[mask].fillna(xg[mask].median() if xg[mask].notna().any() else 1.0).to_numpy(dtype=float)
    n = len(x_arr)

    ols = fit_ols_regression(x, y)
    slope = ols.slope
    intercept = ols.intercept
    r2 = ols.r2

    # Smooth line + 95% confidence band
    x_line = np.linspace(x_arr.min() - 1, x_arr.max() + 1, 200)
    y_line = slope * x_line + intercept
    y_pred = slope * x_arr + intercept
    ss_res = float(np.sum((y_arr - y_pred) ** 2))
    dof = max(n - 2, 1)
    s_err = float(np.sqrt(ss_res / dof))
    x_mean = float(x_arr.mean())
    sxx = float(np.sum((x_arr - x_mean) ** 2)) or 1.0
    t_crit = 2.013
    se_mean = s_err * np.sqrt(1.0 / n + (x_line - x_mean) ** 2 / sxx)
    band = t_crit * se_mean

    residuals = y_arr - y_pred
    res_abs_max = float(np.max(np.abs(residuals))) or 1.0

    fig = go.Figure()

    # Confidence band
    fig.add_trace(go.Scatter(
        x=np.concatenate([x_line, x_line[::-1]]),
        y=np.concatenate([y_line + band, (y_line - band)[::-1]]),
        fill="toself",
        fillcolor="rgba(26,115,232,0.10)",
        line=dict(color="rgba(0,0,0,0)"),
        hoverinfo="skip",
        showlegend=False,
    ))

    # Regression line
    fig.add_trace(go.Scatter(
        x=x_line, y=y_line,
        mode="lines",
        line=dict(color=PRIMARY, width=2, dash="dash"),
        hoverinfo="skip",
        showlegend=False,
    ))

    rng = np.random.default_rng(7)
    x_jit = x_arr + rng.uniform(-0.05, 0.05, size=n)

    # Bubbles + team labels
    xg_max = float(np.max(xg_arr)) or 1.0
    sref = 2.0 * xg_max / (55.0 ** 2)

    alive_mask = np.array([t not in ELIMINATED for t in teams])
    alive_idx = np.where(alive_mask)[0]
    elim_idx = np.where(~alive_mask)[0]

    fig.add_trace(go.Scatter(
        x=x_jit[alive_idx], y=y_arr[alive_idx],
        mode="markers+text",
        text=[teams[i] for i in alive_idx],
        textposition="top center",
        textfont=dict(size=9, color=TEXT, family=FONT),
        marker=dict(
            size=xg_arr[alive_idx],
            sizemode="area",
            sizeref=sref,
            sizemin=6,
            color=residuals[alive_idx],
            colorscale="RdYlGn",
            cmin=-res_abs_max,
            cmax=res_abs_max,
            line=dict(width=1, color="white"),
            colorbar=dict(
                title=dict(text="vs trend", side="right",
                           font=dict(color=MUTED, family=FONT, size=10)),
                tickfont=dict(color=MUTED, family=FONT, size=9),
                thickness=8, len=0.55, x=1.0, xanchor="left",
                outlinewidth=0,
            ),
        ),
        customdata=np.stack([xg_arr[alive_idx], residuals[alive_idx]], axis=-1),
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Attempts: %{x:.0f}<br>"
            "Goals: %{y:.0f}<br>"
            "xG: %{customdata[0]:.2f}<br>"
            "Residual: %{customdata[1]:+.2f}<extra></extra>"
        ),
        name="Still alive",
        showlegend=False,
    ))

    if len(elim_idx) > 0:
        fig.add_trace(go.Scatter(
            x=x_jit[elim_idx], y=y_arr[elim_idx],
            mode="markers+text",
            text=[teams[i] for i in elim_idx],
            textposition="top center",
            textfont=dict(size=9, color="#bdc1c6", family=FONT),
            marker=dict(
                size=xg_arr[elim_idx],
                sizemode="area",
                sizeref=sref,
                sizemin=6,
                color="#9aa0a6",
                opacity=0.28,
                line=dict(width=1, color="white"),
            ),
            customdata=np.stack([xg_arr[elim_idx], residuals[elim_idx]], axis=-1),
            hovertemplate=(
                "<b>%{text} — eliminated</b><br>"
                "Attempts: %{x:.0f}<br>"
                "Goals: %{y:.0f}<br>"
                "xG: %{customdata[0]:.2f}<br>"
                "Residual: %{customdata[1]:+.2f}<extra></extra>"
            ),
            name="Eliminated",
            showlegend=False,
        ))

    # Callouts: 3 biggest over- and under-performers among alive teams
    if len(alive_idx) >= 2:
        alive_res = residuals[alive_idx]
        order_local = np.argsort(alive_res)
        picks_local = list(order_local[-3:][::-1]) + list(order_local[:3])
        for j in picks_local:
            i = int(alive_idx[j])
            fig.add_annotation(
                x=x_arr[i], y=y_arr[i],
                text=f"<b>{teams[i]}</b>",
                showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1,
                arrowcolor=MUTED,
                ax=0, ay=-26 if residuals[i] > 0 else 26,
                font=dict(size=10, color=TEXT, family=FONT),
                bgcolor="rgba(255,255,255,0.92)",
                bordercolor=GRID, borderwidth=1, borderpad=3,
            )

    _base_layout(fig, "Goals vs Attempts At Goal — bubble = xG", height=height)
    fig.update_xaxes(title="Attempts At Goal")
    fig.update_yaxes(title="Goals")
    # Equation in-plot so the chart is self-documenting without a legend
    fig.add_annotation(
        x=0.01, y=0.99, xref="paper", yref="paper",
        xanchor="left", yanchor="top",
        text=(f"<b>y = {slope:.3f}x + {intercept:.2f}</b>"
              f"  ·  R² = {r2:.2f}  ·  n = {n}"),
        showarrow=False, align="left",
        font=dict(color=MUTED, size=10, family=FONT),
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor=GRID, borderwidth=1, borderpad=3,
    )
    fig.update_layout(
        showlegend=False,
        margin=dict(l=50, r=65, t=18, b=44),
    )
    return fig, ols


def highlight_team_in_regression(base_fig: go.Figure, df: pd.DataFrame,
                                 team: str) -> go.Figure:
    """Return a *copy* of the persistent regression figure with a red ring + arrow
    pointing at the selected team. The cached base figure is never mutated."""
    fig = go.Figure(base_fig)
    row = df.loc[df["Team"] == team]
    if row.empty:
        return fig

    idx = row.index[0]
    x_val = pd.to_numeric(get(df, "attempts_at_goal").iloc[idx], errors="coerce")
    y_val = pd.to_numeric(get(df, "goals").iloc[idx], errors="coerce")
    if pd.isna(x_val) or pd.isna(y_val):
        return fig
    x_val = float(x_val)
    y_val = float(y_val)

    RED = "#d93025"

    # Hollow red ring around the existing residual-colored bubble
    fig.add_trace(go.Scatter(
        x=[x_val], y=[y_val],
        mode="markers",
        marker=dict(
            size=26,
            color="rgba(0,0,0,0)",
            line=dict(color=RED, width=3),
            symbol="circle",
        ),
        hoverinfo="skip",
        showlegend=False,
        name="_selected_ring",
    ))

    # Smart offset for the arrow label so it doesn't fall off-axis
    x_all = pd.to_numeric(get(df, "attempts_at_goal"), errors="coerce").dropna()
    y_all = pd.to_numeric(get(df, "goals"), errors="coerce").dropna()
    x_mid = float((x_all.max() + x_all.min()) / 2)
    y_mid = float((y_all.max() + y_all.min()) / 2)
    ax_off = -70 if x_val > x_mid else 70
    ay_off = 60 if y_val > y_mid else -60

    fig.add_annotation(
        x=x_val, y=y_val,
        text=f"<b>{team}</b>",
        showarrow=True,
        arrowhead=3,
        arrowsize=1.4,
        arrowwidth=2.5,
        arrowcolor=RED,
        ax=ax_off, ay=ay_off,
        font=dict(size=12, color=RED, family=FONT),
        bgcolor="rgba(255,255,255,0.97)",
        bordercolor=RED,
        borderwidth=1.5,
        borderpad=4,
    )
    return fig


# ---------------------------------------------------------------------------
# Chart 2 — Style Map (Verticality × Pressing)
# ---------------------------------------------------------------------------


def style_map(df: pd.DataFrame, selected_team: str, height: int = 460) -> go.Figure:
    if "factor_verticality" not in df.columns or "factor_pressing" not in df.columns:
        return _empty("Missing Verticality or Pressing components", height)

    x = df["factor_verticality"]
    y = df["factor_pressing"]
    size_raw = get(df, "xg")
    if size_raw.notna().sum() == 0:
        size_raw = get(df, "attempts_at_goal")
    size_raw = size_raw.fillna(size_raw.median() if size_raw.notna().any() else 1.0)

    is_sel = df["Team"] == selected_team

    x_pad = (x.max() - x.min()) * 0.12 or 1
    y_pad = (y.max() - y.min()) * 0.12 or 1
    x_lo, x_hi = x.min() - x_pad, x.max() + x_pad
    y_lo, y_hi = y.min() - y_pad, y.max() + y_pad

    fig = go.Figure()
    quads = [
        (0, x_hi, 0, y_hi, "rgba(26,115,232,0.06)", "Modern transition",
         (x_hi, y_hi), "right", "top"),
        (x_lo, 0, 0, y_hi, "rgba(251,188,4,0.08)", "Pressing w/o penetration",
         (x_lo, y_hi), "left", "top"),
        (0, x_hi, y_lo, 0, "rgba(24,128,56,0.07)", "Direct / counter",
         (x_hi, y_lo), "right", "bottom"),
        (x_lo, 0, y_lo, 0, "rgba(95,99,104,0.06)", "Traditional / passive",
         (x_lo, y_lo), "left", "bottom"),
    ]
    for x0, x1, y0, y1, color, label, (lx, ly), xa, ya in quads:
        fig.add_shape(type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
                      fillcolor=color, line=dict(width=0), layer="below")
        fig.add_annotation(x=lx, y=ly, text=f"<b>{label}</b>", showarrow=False,
                           xanchor=xa, yanchor=ya,
                           font=dict(color=MUTED, size=10, family=FONT),
                           bgcolor="rgba(255,255,255,0.7)", borderpad=3)

    fig.add_shape(type="line", x0=0, x1=0, y0=y_lo, y1=y_hi,
                  line=dict(color=GRID, width=1))
    fig.add_shape(type="line", x0=x_lo, x1=x_hi, y0=0, y1=0,
                  line=dict(color=GRID, width=1))

    smax = float(size_raw.max()) or 1.0
    sref = 2.0 * smax / (40.0 ** 2)

    fig.add_trace(go.Scatter(
        x=x[~is_sel], y=y[~is_sel],
        mode="markers",
        marker=dict(
            size=size_raw[~is_sel],
            sizemode="area", sizeref=sref, sizemin=6,
            color=PRIMARY_LIGHT, opacity=0.55,
            line=dict(color="white", width=1),
        ),
        text=df.loc[~is_sel, "Team"],
        hovertemplate=(
            "<b>%{text}</b><br>Verticality z: %{x:.2f}<br>"
            "Pressing z: %{y:.2f}<extra></extra>"
        ),
        showlegend=False,
    ))

    if is_sel.any():
        fig.add_trace(go.Scatter(
            x=x[is_sel], y=y[is_sel],
            mode="markers+text",
            marker=dict(
                size=size_raw[is_sel],
                sizemode="area", sizeref=sref, sizemin=14,
                color=ACCENT, line=dict(color="white", width=2), symbol="star",
            ),
            text=df.loc[is_sel, "Team"],
            textposition="top center",
            textfont=dict(color=ACCENT, size=12, family=FONT),
            hovertemplate=(
                f"<b>{selected_team}</b><br>"
                "Verticality z: %{x:.2f}<br>Pressing z: %{y:.2f}<extra></extra>"
            ),
            showlegend=False,
        ))

    _base_layout(fig, "Style Map — Verticality × Pressing (bubble = xG)", height=height)
    fig.update_xaxes(title="Verticality (z-score)", range=[x_lo, x_hi])
    fig.update_yaxes(title="Pressing (z-score)", range=[y_lo, y_hi])
    return fig


# ---------------------------------------------------------------------------
# Chart 3 — Magic Factor bar
# ---------------------------------------------------------------------------


def magic_factor_bar(df: pd.DataFrame, selected_team: str, height: int = 460) -> go.Figure:
    if "magic_factor" not in df.columns:
        return _empty("Magic Factor not computed", height)
    d = df[["Team", "magic_factor"]].copy()
    d = d.sort_values("magic_factor", ascending=False).reset_index(drop=True)

    q90 = d["magic_factor"].quantile(0.90)
    q10 = d["magic_factor"].quantile(0.10)

    def label(v: float) -> str:
        if v >= q90:
            return "GOAT tax"
        if v >= 0.75:
            return "Clinical"
        if v <= q10:
            return "Wasteful"
        if v <= -0.75:
            return "Due goals?"
        return ""

    d["tag"] = d["magic_factor"].apply(label)
    colors = [
        ACCENT if t == selected_team else (GOOD if v > 0 else WARN)
        for t, v in zip(d["Team"], d["magic_factor"])
    ]
    line_colors = [
        "#0d47a1" if t == selected_team else "rgba(0,0,0,0)"
        for t in d["Team"]
    ]
    line_widths = [2 if t == selected_team else 0 for t in d["Team"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=d["Team"], y=d["magic_factor"],
        marker=dict(color=colors,
                    line=dict(color=line_colors, width=line_widths)),
        text=d["tag"], textposition="outside",
        textfont=dict(color=MUTED, size=10, family=FONT),
        hovertemplate=(
            "<b>%{x}</b><br>Magic Factor: %{y:+.2f}<br>%{text}<extra></extra>"
        ),
    ))

    fig.add_shape(type="line", x0=-0.5, x1=len(d) - 0.5, y0=0, y1=0,
                  line=dict(color=MUTED, width=1))

    fig.add_annotation(
        x=0.99, y=0.99, xref="paper", yref="paper",
        xanchor="right", yanchor="top",
        text=("<i>Magic Factor is not mystical. It is model residuals<br>"
              "wearing nicer clothes.</i>"),
        showarrow=False, align="right",
        font=dict(color=MUTED, size=10, family=FONT),
        bgcolor="rgba(255,255,255,0.92)",
        bordercolor=GRID, borderwidth=1, borderpad=4,
    )

    _base_layout(fig, "Magic Factor — goals beyond structural model", height=height)
    fig.update_xaxes(title="", tickangle=-55, tickfont=dict(size=8))
    fig.update_yaxes(title="Magic Factor (residual goals)")
    fig.update_layout(margin=dict(l=50, r=20, t=18, b=90))
    return fig


# ---------------------------------------------------------------------------
# Chart 4 — Team DNA percentile bars
# ---------------------------------------------------------------------------


def team_dna(df: pd.DataFrame, selected_team: str, height: int = 460) -> go.Figure:
    rows = []
    for label, col in DNA_FIELDS:
        if col not in df.columns:
            continue
        pct = percentile_rank(df[col])
        sel_row = df.loc[df["Team"] == selected_team]
        if sel_row.empty:
            continue
        idx = sel_row.index[0]
        rows.append({"Metric": label, "Percentile": float(pct.loc[idx])})

    if not rows:
        return _empty("DNA factors unavailable", height)

    d = pd.DataFrame(rows)
    d = d.iloc[::-1]

    def cat_color(p: float) -> str:
        if p >= 75:
            return GOOD
        if p >= 50:
            return PRIMARY
        if p >= 25:
            return NEON
        return WARN

    colors = [cat_color(p) for p in d["Percentile"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=d["Percentile"], y=d["Metric"], orientation="h",
        marker=dict(color=colors, line=dict(color="white", width=1)),
        text=[f"{p:.0f}" for p in d["Percentile"]],
        textposition="outside",
        textfont=dict(color=TEXT, size=11, family=FONT),
        hovertemplate="<b>%{y}</b><br>Percentile: %{x:.0f}<extra></extra>",
    ))

    for ref in (25, 50, 75):
        fig.add_shape(type="line", x0=ref, x1=ref,
                      y0=-0.5, y1=len(d) - 0.5,
                      line=dict(color=GRID, width=1, dash="dot"))

    _base_layout(fig, f"Team DNA — {selected_team} vs field (percentile)", height=height)
    fig.update_xaxes(title="Percentile", range=[0, 110])
    fig.update_yaxes(title="", tickfont=dict(size=10))
    fig.update_layout(margin=dict(l=150, r=30, t=18, b=44))
    return fig

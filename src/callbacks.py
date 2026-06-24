"""Wire dropdown to KPIs, three live charts (Style/Magic/DNA), and the read panel.
Chart 1 (regression) is precomputed once and returned unchanged for any team."""

from __future__ import annotations

import pandas as pd
from dash import Input, Output, html

from .charts import magic_factor_bar, style_map, team_dna
from .data_loader import get
from .features import DNA_FIELDS, percentile_rank
from .store import DataStore


def _style_label(vert_z: float, press_z: float) -> str:
    if vert_z >= 0 and press_z >= 0:
        return "Modern transition football"
    if vert_z < 0 and press_z >= 0:
        return "Pressing without penetration"
    if vert_z >= 0 and press_z < 0:
        return "Direct / counter-attacking"
    return "Traditional / passive"


def _regression_card(team: str, resid: float, conv: float, attempts: float, xg: float):
    if pd.isna(resid):
        verdict = "Insufficient data."
        cls = "muted"
    elif resid >= 1.0:
        verdict = "Positive finishing residual — scoring above shot-volume baseline."
        cls = "good"
    elif resid <= -1.0:
        verdict = "Negative finishing residual — underperforming shot volume."
        cls = "warn"
    elif resid >= 0.3 and not pd.isna(conv) and conv < 12:
        verdict = "Shot volume strong but conversion poor — regression up candidate."
        cls = "watch"
    elif resid > 0 and (pd.isna(xg) or pd.isna(attempts) or xg < attempts * 0.10):
        verdict = "Hot finishing on low xG — beware regression."
        cls = "watch"
    elif resid > 0:
        verdict = "Slightly above the curve."
        cls = "good"
    else:
        verdict = "Slightly below the curve."
        cls = "warn"
    return html.Div([
        html.Span("Regression read: ", className="ic-label"),
        html.Span(f"{team} — ", className="ic-team"),
        html.Span(verdict, className=f"ic-verdict ic-{cls}"),
    ], className="interp-inner")


def _suggested_tag(resid: float, magic: float, finishing_pct: float,
                   chance_pct: float, mfi_pct: float, xg: float) -> str:
    if magic > 1.5 and (pd.isna(xg) or finishing_pct > 75):
        return "CHAOS"
    if finishing_pct >= 80 and chance_pct >= 60:
        return "CLINICAL"
    if magic > 1.0 and chance_pct < 40:
        return "TRAP"
    if chance_pct >= 70 and finishing_pct <= 35:
        return "WASTEFUL"
    if resid >= 1.0 and mfi_pct >= 60:
        return "BUY"
    if resid <= -1.0 and chance_pct <= 35:
        return "FADE"
    return "WATCH"


def register_callbacks(app, store: DataStore) -> None:

    @app.callback(
        Output("kpi-goals", "children"),
        Output("kpi-xg", "children"),
        Output("kpi-attempts", "children"),
        Output("kpi-conv", "children"),
        Output("kpi-mfi-rank", "children"),
        Output("kpi-magic-rank", "children"),
        Output("chart-regression", "figure"),
        Output("chart-style", "figure"),
        Output("chart-magic", "figure"),
        Output("chart-dna", "figure"),
        Output("regression-card", "children"),
        Output("read-team", "children"),
        Output("read-tag", "children"),
        Output("read-tag", "className"),
        Output("read-style", "children"),
        Output("read-strength", "children"),
        Output("read-weakness", "children"),
        Output("read-regression", "children"),
        Output("read-magic", "children"),
        Input("team-dropdown", "value"),
    )
    def update(team):
        snap = store.snapshot
        df = snap.df
        regression_fig = snap.regression_fig
        ols = snap.ols

        row = df.loc[df["Team"] == team]
        if row.empty:
            empty = "—"
            return (empty,) * 6 + (regression_fig, {}, {}, {}, "", team or "",
                                   "", "panel-tag", "", "", "", "", "")
        idx = row.index[0]

        goals = get(df, "goals").iloc[idx]
        xg = get(df, "xg").iloc[idx]
        attempts = get(df, "attempts_at_goal").iloc[idx]
        conv = get(df, "conv_rate").iloc[idx]

        def _fmt(v, suffix=""):
            if pd.isna(v):
                return "—"
            if isinstance(v, float) and not v.is_integer():
                return f"{v:.2f}{suffix}"
            return f"{int(v)}{suffix}"

        kpi_goals = _fmt(goals)
        kpi_xg = _fmt(xg)
        kpi_attempts = _fmt(attempts)
        kpi_conv = _fmt(conv, "%")

        mfi_rank = int(df["factor_modern_index"].rank(ascending=False, method="min").iloc[idx])
        magic_rank = int(df["magic_factor"].rank(ascending=False, method="min").iloc[idx])
        n = len(df)
        kpi_mfi_rank = f"{mfi_rank}/{n}"
        kpi_magic_rank = f"{magic_rank}/{n}"

        # Live charts (depend on selected team)
        fig_style = style_map(df, team)
        fig_magic = magic_factor_bar(df, team)
        fig_dna = team_dna(df, team)

        # Selected team residual from the persistent OLS fit
        resid = ols.residual.iloc[idx] if not ols.residual.empty else float("nan")
        regression_card = _regression_card(team, resid, conv, attempts, xg)

        vert_z = float(df["factor_verticality"].iloc[idx])
        press_z = float(df["factor_pressing"].iloc[idx])
        style = _style_label(vert_z, press_z)

        dna_rows = []
        for label, col in DNA_FIELDS:
            if col in df.columns:
                pct = float(percentile_rank(df[col]).iloc[idx])
                dna_rows.append((label, pct))
        if dna_rows:
            dna_rows.sort(key=lambda r: r[1], reverse=True)
            strength = f"{dna_rows[0][0]} ({dna_rows[0][1]:.0f}p)"
            weakness = f"{dna_rows[-1][0]} ({dna_rows[-1][1]:.0f}p)"
        else:
            strength = weakness = "—"

        if pd.isna(resid):
            reg_text = "—"
        else:
            sign = "+" if resid >= 0 else ""
            reg_text = f"{sign}{resid:.2f} goals vs shot-volume trend"

        magic_val = float(df["magic_factor"].iloc[idx])
        finishing_pct = float(percentile_rank(df["factor_finishing_efficiency"]).iloc[idx]) \
            if "factor_finishing_efficiency" in df.columns else 50.0
        chance_pct = float(percentile_rank(df["factor_chance_creation"]).iloc[idx]) \
            if "factor_chance_creation" in df.columns else 50.0
        mfi_pct = float(percentile_rank(df["factor_modern_index"]).iloc[idx]) \
            if "factor_modern_index" in df.columns else 50.0

        if magic_val >= 1.5:
            magic_text = "Scoring well above structural model — chaos / star quality."
        elif magic_val >= 0.5:
            magic_text = "Modestly above the model."
        elif magic_val <= -1.5:
            magic_text = "Creating structure but not converting — due goals?"
        elif magic_val <= -0.5:
            magic_text = "Slightly under model expectation."
        else:
            magic_text = "On model."
        magic_text = f"{magic_val:+.2f} — {magic_text}"

        tag = _suggested_tag(resid, magic_val, finishing_pct, chance_pct, mfi_pct, xg)
        tag_class = f"panel-tag tag-{tag.lower()}"

        return (
            kpi_goals, kpi_xg, kpi_attempts, kpi_conv,
            kpi_mfi_rank, kpi_magic_rank,
            regression_fig,           # persistent — never changes
            fig_style, fig_magic, fig_dna,
            regression_card,
            team, tag, tag_class,
            style, strength, weakness, reg_text, magic_text,
        )

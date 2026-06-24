"""Dash layout — Material light theme, fixed chart heights."""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html


# Chart container height is owned by CSS (clamp + media queries).
# dcc.Graph fills its parent at 100% so it scales with the viewport
# instead of being pinned at a fixed pixel size.
GRAPH_STYLE = {"height": "100%", "width": "100%"}
GRAPH_CONFIG = {"displayModeBar": False, "responsive": True}


CHART_BANNERS = {
    "chart-regression": dict(
        number="1", accent="accent-blue",
        title="Goals vs Attempts At Goal",
        desc=("Scatter of all 48 teams with an OLS trend line and 95% confidence band. "
              "Bubble size = xG · color = residual (green above trend, red below). "
              "Top three over- and under-performers are labelled. Always shows everyone."),
    ),
    "chart-style": dict(
        number="2", accent="accent-green",
        title="Style Map — Verticality × Pressing",
        desc=("Four quadrants of football identity. X = how vertical/line-breaking a team is, "
              "Y = how hard it presses. Bubble = xG. Selected team appears as a dark star."),
    ),
    "chart-magic": dict(
        number="3", accent="accent-yellow",
        title="Magic Factor",
        desc=("Residual goals from a model fit on xG, attempts, runs in behind, line-breaks, "
              "pressing and verticality."),
    ),
    "chart-dna": dict(
        number="4", accent="accent-red",
        title="Team DNA — Percentile Profile",
        desc=("Selected team's percentile rank across 9 factors. "
              "Green ≥ 75 elite · blue ≥ 50 above · yellow ≥ 25 below · red weak."),
    ),
}


def kpi_card(card_id: str, label: str) -> dbc.Card:
    return dbc.Card(
        dbc.CardBody([
            html.Div(label, className="kpi-label"),
            html.Div(id=card_id, className="kpi-value"),
        ]),
        className="kpi-card",
    )


def chart_card(graph_id: str) -> html.Div:
    meta = CHART_BANNERS[graph_id]
    return html.Div(
        [
            html.Div(
                [
                    html.Div(meta["number"], className=f"chart-num {meta['accent']}"),
                    html.Div(
                        [
                            html.Div(meta["title"], className="chart-title"),
                            html.Div(meta["desc"], className="chart-desc"),
                        ],
                        className="chart-meta",
                    ),
                ],
                className=f"chart-banner {meta['accent']}",
            ),
            html.Div(
                dcc.Graph(
                    id=graph_id,
                    config=GRAPH_CONFIG,
                    style=GRAPH_STYLE,
                    responsive=True,
                ),
                className="chart-graph",
            ),
        ],
        className="chart-card",
    )


def make_layout(team_options: list[dict]) -> dbc.Container:
    return dbc.Container(
        fluid=True,
        className="app-shell",
        children=[
            # Header
            html.Div(
                className="header-bar",
                children=[
                    html.Div(
                        className="brand-block",
                        children=[
                            html.Div("FIFA WORLD CUP 2026", className="brand-eyebrow"),
                            html.H1("Football Edge Dashboard", className="brand-title"),
                            html.Div("Regression · Style · Magic · DNA",
                                     className="brand-subtitle"),
                        ],
                    ),
                    html.Div(
                        className="dropdown-wrap",
                        children=[
                            html.Label("Team", className="dropdown-label"),
                            dcc.Dropdown(
                                id="team-dropdown",
                                options=team_options,
                                value=team_options[0]["value"] if team_options else None,
                                clearable=False,
                                className="team-dropdown",
                            ),
                        ],
                    ),
                ],
            ),

            # KPI strip
            dbc.Row(
                className="kpi-row g-2",
                children=[
                    dbc.Col(kpi_card("kpi-goals", "Goals"), md=2),
                    dbc.Col(kpi_card("kpi-xg", "xG"), md=2),
                    dbc.Col(kpi_card("kpi-attempts", "Attempts"), md=2),
                    dbc.Col(kpi_card("kpi-conv", "Conv. Rate"), md=2),
                    dbc.Col(kpi_card("kpi-mfi-rank", "Modern Rank"), md=2),
                    dbc.Col(kpi_card("kpi-magic-rank", "Magic Rank"), md=2),
                ],
            ),

            # Row 1: full-width regression chart
            dbc.Row(
                className="content-row g-3",
                children=[dbc.Col(chart_card("chart-regression"), md=12)],
            ),

            # Row 2: style map + betting read panel
            dbc.Row(
                className="g-3 mt-1",
                children=[
                    dbc.Col(chart_card("chart-style"), md=6),
                    dbc.Col(_read_panel(), md=6),
                ],
            ),

            # Row 3: magic + DNA
            dbc.Row(
                className="g-3 mt-1",
                children=[
                    dbc.Col(chart_card("chart-magic"), md=6),
                    dbc.Col(chart_card("chart-dna"), md=6),
                ],
            ),

            # Regression interpretation card under the bottom row
            html.Div(id="regression-card", className="interp-card"),
        ],
    )


def _read_panel() -> html.Div:
    return html.Div(
        className="read-panel",
        children=[
            html.Div("BETTING READ", className="panel-eyebrow"),
            html.H3(id="read-team", className="panel-team"),
            html.Div(id="read-tag", className="panel-tag"),
            html.Hr(className="panel-divider"),
            html.Div([
                html.Div("Style", className="panel-key"),
                html.Div(id="read-style", className="panel-val"),
            ], className="panel-row"),
            html.Div([
                html.Div("Strength", className="panel-key"),
                html.Div(id="read-strength", className="panel-val"),
            ], className="panel-row"),
            html.Div([
                html.Div("Weakness", className="panel-key"),
                html.Div(id="read-weakness", className="panel-val"),
            ], className="panel-row"),
            html.Div([
                html.Div("Regression", className="panel-key"),
                html.Div(id="read-regression", className="panel-val"),
            ], className="panel-row"),
            html.Div([
                html.Div("Magic", className="panel-key"),
                html.Div(id="read-magic", className="panel-val"),
            ], className="panel-row"),
            html.Hr(className="panel-divider"),
            html.Div(
                "Analytics framing only — not a betting recommendation.",
                className="panel-disclaimer",
            ),
        ],
    )

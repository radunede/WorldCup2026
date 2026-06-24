"""Three exploratory charts: residual lollipop, flag markers, quadrant chart.

Paths are derived from the script location (or ``WC_DATA_DIR`` env var).
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("WC_DATA_DIR", PROJECT_ROOT / "data"))

CSV_PATH = DATA_DIR / "team_statistics.csv"


df = pd.read_csv(CSV_PATH)
if "Rank" not in df.columns:
    df = df.rename(columns={df.columns[0]: "Rank"})
for col in ["Attempts At Goal", "Goals", "xG", "Possession Control (%)"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")
df = df.dropna(subset=["Attempts At Goal", "Goals"]).reset_index(drop=True)

x = df["Attempts At Goal"].to_numpy(dtype=float)
y = df["Goals"].to_numpy(dtype=float)
n = len(df)

slope, intercept = np.polyfit(x, y, 1)
x_line = np.linspace(x.min() - 1, x.max() + 1, 200)
y_line = slope * x_line + intercept
y_pred = slope * x + intercept
df["Residual"] = y - y_pred
ss_res = float(np.sum((y - y_pred) ** 2))
ss_tot = float(np.sum((y - y.mean()) ** 2))
r2 = 1 - ss_res / ss_tot if ss_tot else float("nan")


ISO = {
    "Germany": "de", "Norway": "no", "Canada": "ca", "Netherlands": "nl",
    "Japan": "jp", "France": "fr", "Sweden": "se", "USA": "us",
    "Portugal": "pt", "Argentina": "ar", "Switzerland": "ch", "Egypt": "eg",
    "Colombia": "co", "England": "gb-eng", "Spain": "es", "Brazil": "br",
    "New Zealand": "nz", "Austria": "at", "Senegal": "sn", "Mexico": "mx",
    "Uruguay": "uy", "Croatia": "hr", "Paraguay": "py", "Korea Republic": "kr",
    "IR Iran": "ir", "Australia": "au", "Morocco": "ma", "Jordan": "jo",
    "Bosnia and Herzegovina": "ba", "Cabo Verde": "cv", "Algeria": "dz",
    "Côte d'Ivoire": "ci", "Czechia": "cz", "Curaçao": "cw", "Congo DR": "cd",
    "Uzbekistan": "uz", "Scotland": "gb-sct", "Tunisia": "tn",
    "South Africa": "za", "Iraq": "iq", "Belgium": "be", "Ghana": "gh",
    "Qatar": "qa", "Saudi Arabia": "sa", "Türkiye": "tr", "Panama": "pa",
    "Ecuador": "ec", "Haiti": "ht",
}


def flag_url(team: str) -> str:
    code = ISO.get(team)
    return f"https://flagcdn.com/w80/{code}.png" if code else ""


# ---- 1) Residual lollipop -------------------------------------------------

lol = df.sort_values("Residual", ascending=False).reset_index(drop=True)
fig1 = go.Figure()
for _, row in lol.iterrows():
    c = "#2ca02c" if row["Residual"] >= 0 else "#d62728"
    fig1.add_shape(type="line", x0=row["Team"], x1=row["Team"],
                   y0=0, y1=row["Residual"], line=dict(color=c, width=2))
fig1.add_trace(go.Scatter(
    x=lol["Team"], y=lol["Residual"], mode="markers",
    marker=dict(size=14,
                color=["#2ca02c" if r >= 0 else "#d62728" for r in lol["Residual"]],
                line=dict(color="#222", width=1)),
    customdata=np.stack([lol["Attempts At Goal"], lol["Goals"], lol["xG"]], axis=-1),
    hovertemplate=("<b>%{x}</b><br>Attempts: %{customdata[0]:.0f}<br>"
                   "Goals: %{customdata[1]:.0f}<br>xG: %{customdata[2]}<br>"
                   "Over/under trend: %{y:+.2f}<extra></extra>"),
    showlegend=False,
))
fig1.add_shape(type="line", x0=-0.5, x1=len(lol) - 0.5, y0=0, y1=0,
               line=dict(color="#222", width=1))
for _, row in pd.concat([lol.head(3), lol.tail(3)]).iterrows():
    fig1.add_annotation(x=row["Team"], y=row["Residual"],
                        text=f"<b>{row['Residual']:+.1f}</b>",
                        showarrow=False,
                        yshift=18 if row["Residual"] >= 0 else -18,
                        font=dict(size=11, color="#000"))
fig1.update_layout(
    title=dict(
        text=("<b>Over- and under-performance vs. the attempts→goals trend</b><br>"
              "<span style='font-size:13px;color:#555'>Green: scored more than expected. "
              "Red: scored less.</span>"),
        x=0.02, xanchor="left",
    ),
    xaxis=dict(title="", tickangle=-45, tickfont=dict(size=11)),
    yaxis=dict(title="Goals vs. trend", gridcolor="#eee", zeroline=False),
    plot_bgcolor="white", paper_bgcolor="white",
    width=1400, height=700,
    margin=dict(l=70, r=40, t=110, b=140),
)
fig1.write_html(DATA_DIR / "residual_lollipop.html", include_plotlyjs="cdn")
print(f"Wrote {DATA_DIR / 'residual_lollipop.html'}")


# ---- 2) Flag markers ------------------------------------------------------

fig2 = go.Figure()
fig2.add_trace(go.Scatter(
    x=x_line, y=y_line, mode="lines",
    line=dict(color="#333", dash="dash", width=2),
    name=f"Trend  y = {slope:.3f}x + {intercept:.2f}   R² = {r2:.2f}",
    hoverinfo="skip",
))
fig2.add_trace(go.Scatter(
    x=df["Attempts At Goal"], y=df["Goals"], mode="markers",
    marker=dict(size=18, color="rgba(0,0,0,0)"),
    customdata=np.stack([df["Team"], df["Rank"], df["xG"],
                         df["Residual"].round(2)], axis=-1),
    hovertemplate=("<b>%{customdata[0]}</b> (rank %{customdata[1]})<br>"
                   "Attempts: %{x}<br>Goals: %{y}<br>"
                   "xG: %{customdata[2]}<br>"
                   "Over/under trend: %{customdata[3]:+.2f}<extra></extra>"),
    showlegend=False,
))
xg_max = float(df["xG"].max())
flag_imgs = []
for _, row in df.iterrows():
    url = flag_url(row["Team"])
    if not url:
        continue
    sx = 2.0 + 1.6 * (float(row["xG"]) / xg_max)
    sy = sx * (9.0 / 60.0) * 1.5
    flag_imgs.append(dict(source=url, xref="x", yref="y",
                          x=row["Attempts At Goal"], y=row["Goals"],
                          sizex=sx, sizey=sy,
                          xanchor="center", yanchor="middle",
                          layer="above", opacity=0.95))
fig2.update_layout(
    images=flag_imgs,
    title=dict(text=("<b>Attempts At Goal vs. Goals — flag markers</b><br>"
                     "<span style='font-size:13px;color:#555'>"
                     f"Flag size scales with xG. R² = {r2:.2f}, n = {n}.</span>"),
               x=0.02, xanchor="left"),
    xaxis=dict(title="Attempts At Goal", gridcolor="#eee", zeroline=False,
               range=[x.min() - 3, x.max() + 3]),
    yaxis=dict(title="Goals", gridcolor="#eee", zeroline=False,
               range=[y.min() - 1, y.max() + 1.5]),
    plot_bgcolor="white", paper_bgcolor="white",
    width=1300, height=820,
    margin=dict(l=70, r=40, t=110, b=70),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0),
)
fig2.write_html(DATA_DIR / "flag_markers.html", include_plotlyjs="cdn")
print(f"Wrote {DATA_DIR / 'flag_markers.html'}")


# ---- 3) Quadrant chart ----------------------------------------------------

x_med = float(np.median(x))
y_med = float(np.median(y))


def quadrant(att, gls):
    if att >= x_med and gls >= y_med:
        return "Volume scorers"
    if att < x_med and gls >= y_med:
        return "Clinical finishers"
    if att >= x_med and gls < y_med:
        return "Wasteful"
    return "Low-output"


df["Quadrant"] = df.apply(lambda r: quadrant(r["Attempts At Goal"], r["Goals"]), axis=1)
QUAD_COLOR = {
    "Volume scorers": "#1f77b4",
    "Clinical finishers": "#2ca02c",
    "Wasteful": "#d62728",
    "Low-output": "#7f7f7f",
}

x_pad = (x.max() - x.min()) * 0.08
y_pad = (y.max() - y.min()) * 0.15
x_lo, x_hi = x.min() - x_pad, x.max() + x_pad
y_lo, y_hi = y.min() - 1, y.max() + y_pad + 1

fig3 = go.Figure()
shade = [
    (x_med, x_hi, y_med, y_hi, "rgba(31,119,180,0.07)",  "Volume scorers",     (x_hi, y_hi)),
    (x_lo,  x_med, y_med, y_hi, "rgba(44,160,44,0.08)",  "Clinical finishers", (x_lo, y_hi)),
    (x_med, x_hi, y_lo,  y_med, "rgba(214,39,40,0.07)",  "Wasteful",           (x_hi, y_lo)),
    (x_lo,  x_med, y_lo,  y_med, "rgba(127,127,127,0.07)","Low-output",         (x_lo, y_lo)),
]
for x0, x1, y0, y1, color, label, (lx, ly) in shade:
    fig3.add_shape(type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
                   fillcolor=color, line=dict(width=0), layer="below")
    xanchor = "right" if lx == x_hi else "left"
    yanchor = "top" if ly == y_hi else "bottom"
    fig3.add_annotation(x=lx, y=ly, text=f"<b>{label}</b>", showarrow=False,
                        xanchor=xanchor, yanchor=yanchor,
                        font=dict(size=14, color=QUAD_COLOR[label]),
                        bgcolor="rgba(255,255,255,0.6)", borderpad=4)
fig3.add_shape(type="line", x0=x_med, x1=x_med, y0=y_lo, y1=y_hi,
               line=dict(color="#888", width=1, dash="dot"))
fig3.add_shape(type="line", x0=x_lo, x1=x_hi, y0=y_med, y1=y_med,
               line=dict(color="#888", width=1, dash="dot"))
fig3.add_annotation(x=x_med, y=y_hi, text=f"median attempts = {x_med:.0f}",
                    showarrow=False, yshift=-12, xshift=4,
                    font=dict(size=10, color="#666"), xanchor="left")
fig3.add_annotation(x=x_hi, y=y_med, text=f"median goals = {y_med:.0f}",
                    showarrow=False, xshift=-4, yshift=8,
                    font=dict(size=10, color="#666"), xanchor="right")
fig3.add_trace(go.Scatter(x=x_line, y=y_line, mode="lines",
                          line=dict(color="rgba(50,50,50,0.5)", dash="dash", width=1.5),
                          name=f"Trend (R² = {r2:.2f})", hoverinfo="skip"))
for quad, color in QUAD_COLOR.items():
    sub = df[df["Quadrant"] == quad]
    if sub.empty:
        continue
    fig3.add_trace(go.Scatter(
        x=sub["Attempts At Goal"], y=sub["Goals"],
        mode="markers+text", text=sub["Team"], textposition="top center",
        textfont=dict(size=10, color="#222"),
        marker=dict(size=10 + sub["xG"] * 1.6, color=color,
                    line=dict(color="#222", width=1), opacity=0.85),
        name=quad,
        customdata=np.stack([sub["Rank"], sub["xG"], sub["Residual"].round(2)], axis=-1),
        hovertemplate=("<b>%{text}</b> (rank %{customdata[0]})<br>"
                       "Attempts: %{x}<br>Goals: %{y}<br>"
                       "xG: %{customdata[1]}<br>"
                       "Over/under trend: %{customdata[2]:+.2f}<extra></extra>"),
    ))
fig3.update_layout(
    title=dict(text=("<b>Attempts vs. Goals — quadrants by team profile</b><br>"
                     "<span style='font-size:13px;color:#555'>"
                     f"Split at median attempts ({x_med:.0f}) and median goals "
                     f"({y_med:.0f}). Bubble size = xG.</span>"),
               x=0.02, xanchor="left"),
    xaxis=dict(title="Attempts At Goal", gridcolor="#eee", zeroline=False,
               range=[x_lo, x_hi]),
    yaxis=dict(title="Goals", gridcolor="#eee", zeroline=False,
               range=[y_lo, y_hi]),
    plot_bgcolor="white", paper_bgcolor="white",
    width=1300, height=820,
    margin=dict(l=70, r=40, t=110, b=70),
    legend=dict(title=dict(text="Profile"), orientation="v",
                yanchor="top", y=0.99, xanchor="left", x=0.01,
                bgcolor="rgba(255,255,255,0.85)",
                bordercolor="#ccc", borderwidth=1),
)
fig3.write_html(DATA_DIR / "quadrant_chart.html", include_plotlyjs="cdn")
print(f"Wrote {DATA_DIR / 'quadrant_chart.html'}")

print("\nQuadrant counts:")
print(df["Quadrant"].value_counts().to_string())

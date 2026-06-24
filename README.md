# World Cup 2026 — Football Edge Dashboard

A focused Dash app that turns the FIFA team-statistics tabs into a one-page
betting-intelligence terminal: one team dropdown, four charts, one read panel.
On startup the app scrapes FIFA and builds the in-memory snapshot; restart
the process to pull fresh data.

## Layout

```
+---------------------------------------------------------------+
| FIFA WORLD CUP 2026                          Team [dropdown]  |
| Football Edge Dashboard                                       |
| ------------------------------------------------------------- |
| KPI strip: Goals · xG · Attempts · Conv% · Modern · Magic     |
| ------------------------------------------------------------- |
| [1 Goals vs Attempts ] [2 Style Map         ] | Betting Read  |
| [3 Magic Factor      ] [4 Team DNA          ] | tag · style · |
|                                               | strength      |
| Regression read for selected team                             |
+---------------------------------------------------------------+
```

## Project layout

```
World Cup/
├── app.py                      # Dash entry, exposes `server` for WSGI runners
├── scrape_team_stats.py        # Playwright scraper for all 7 FIFA tabs
├── regression_chart.py         # standalone exploratory chart
├── charts_extra.py             # lollipop, flags, quadrants
├── requirements.txt
├── assets/custom.css           # Material light theme
├── data/                       # CSVs scraped from FIFA
└── src/
    ├── data_loader.py          # CSV merge + fuzzy column lookup
    ├── features.py             # z-scores, percentiles, factor scores
    ├── models.py               # OLS + Magic Factor multivariate residual
    ├── charts.py               # 4 Plotly figures
    ├── layout.py               # Dash layout
    ├── callbacks.py            # one callback drives the page
    └── store.py                # thread-safe in-memory data snapshot
```

## Run locally

```bash
pip install -r requirements.txt
python -m playwright install chromium       # one-time, for the scraper
python app.py                               # http://127.0.0.1:8050
```

`app.py` scrapes FIFA at startup, then loads everything into memory. If you'd
rather skip the scrape during dev (it adds ~30s) and use whatever CSVs are
already in `data/`:

```bash
SCRAPE_ON_STARTUP=0 python app.py
```

If the startup scrape fails (FIFA outage, no network, Playwright not
installed) the app falls back to the CSVs on disk and still serves.

## Deploy to Render (native Python runtime)

1. Push the repo to GitHub.
2. Create a new **Web Service** in Render and point it at the repo.
3. In **Settings → Build & Deploy**, set the **Build Command** to:

   ```
   pip install -r requirements.txt && python -m playwright install chromium
   ```

   Render's native Python runtime doesn't ship Chromium, so this step
   downloads the headless-shell binary into `/opt/render/.cache/ms-playwright/`.
4. Set the **Start Command** to:

   ```
   gunicorn app:server --workers 1 --threads 4 --bind 0.0.0.0:$PORT --timeout 120
   ```

If the build can't install Chromium for any reason (e.g. you're on a plan
that blocks the cache), set the env var `SCRAPE_ON_STARTUP=0` and scrape
locally before each deploy:

```bash
python scrape_team_stats.py
git add data/team_stats_*.csv && git commit -m "Refresh stats" && git push
```

## Environment variables

| Var | Default | Purpose |
| --- | --- | --- |
| `SCRAPE_ON_STARTUP` | `1` | Set `0` to skip the startup scrape |
| `LOG_LEVEL` | `INFO` | Python logging level |
| `WC_DATA_DIR` | `./data` | Override where CSVs are read/written |
| `PORT` | `8050` | Web server port |
| `HOST` | `127.0.0.1` | Bind address |

## Derived factors (Chart 4 + side panel)

| Factor | Components (z-scored, summed, rescaled) |
| --- | --- |
| Verticality | Offers In Behind, Receptions In Behind, Def Linebreaks Att/Acc, Receptions Between Mid & Def |
| Pressing | Def Pressures Applied, Def Pressures Directly Applied, Forced Turnovers, −Ball Recovery Time |
| Transition Threat | Receptions In Behind, Attempts, xG, Forced Turnovers, −Ball Recovery Time |
| Between-Lines Play | Offers In Between, Receptions Mid-Def, Receptions Under Pressure |
| Chance Creation | xG, Attempts, Attempts On Target, Corners |
| Finishing Efficiency | Goals, Conversion Rate, xG Efficiency |
| Physical Intensity | High Speed Running, Sprints, (Top Speed), Total Distance |
| Modern Football Index | 0.25·Vert + 0.20·Press + 0.20·Trans + 0.15·BetweenLines + 0.10·Chance + 0.10·Physical |
| Magic Factor | Residual from OLS: Goals ~ xG + Attempts + Receptions In Behind + Receptions Mid-Def + Def Linebreaks + Pressing + Verticality |

Missing components are skipped — the FIFA dataset has no Top Speed, for
example, and Total Distance is in metres. Both are handled gracefully.

## Disclaimer

Analytics framing only. Not a betting recommendation, not odds prediction.

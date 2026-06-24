"""World Cup 2026 Football Edge Dashboard — Dash entry point.

Exposes ``server`` for production WSGI runners (``gunicorn app:server``).
On startup, scrapes fresh FIFA data unless ``SCRAPE_ON_STARTUP=0`` (handy
for local dev); if the scrape fails for any reason, falls back to whatever
CSVs are already on disk so the app still serves.
"""

from __future__ import annotations

import logging
import os

import dash
import dash_bootstrap_components as dbc

from src.callbacks import register_callbacks
from src.layout import make_layout
from src.store import STORE

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("app")

GOOGLE_FONT = (
    "https://fonts.googleapis.com/css2?"
    "family=Roboto:wght@300;400;500;700&display=swap"
)


def _scrape_at_startup() -> None:
    """Try to refresh CSVs from FIFA. Never raise — the app must still boot."""
    if os.environ.get("SCRAPE_ON_STARTUP", "1") != "1":
        log.info("Startup scrape disabled (SCRAPE_ON_STARTUP=0)")
        return
    try:
        from scrape_team_stats import scrape
        log.info("Scraping fresh FIFA team stats at startup")
        scrape()
    except Exception:
        log.exception("Startup scrape failed; falling back to existing CSVs")


def build_app() -> dash.Dash:
    _scrape_at_startup()
    STORE.refresh()

    team_options = [{"label": t, "value": t} for t in STORE.teams]

    dash_app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP, GOOGLE_FONT],
        title="WC 2026 Edge",
        suppress_callback_exceptions=True,
    )
    dash_app.layout = make_layout(team_options)
    register_callbacks(dash_app, STORE)
    return dash_app


app = build_app()
server = app.server  # gunicorn app:server


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8050"))
    host = os.environ.get("HOST", "127.0.0.1")
    app.run(debug=False, host=host, port=port)

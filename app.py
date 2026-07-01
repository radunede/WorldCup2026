"""World Cup 2026 Football Edge Dashboard — Dash entry point.

Exposes ``server`` for production WSGI runners (``gunicorn app:server``).
Serves existing CSVs immediately so the web port binds fast (Render's port
scanner times out at ~90s), then refreshes FIFA data in a background thread
unless ``SCRAPE_ON_STARTUP=0``. STORE.refresh() re-runs when the scrape
completes so the fresh data becomes visible without a restart.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import threading
from pathlib import Path

import dash
import dash_bootstrap_components as dbc

from src.callbacks import register_callbacks
from src.layout import make_layout
from src.store import STORE
from src.tournament import ELIMINATED

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("app")

GOOGLE_FONT = (
    "https://fonts.googleapis.com/css2?"
    "family=Roboto:wght@300;400;500;700&display=swap"
)


def _chromium_path() -> Path | None:
    """Return the path Playwright expects the Chromium binary at, or None."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            return Path(p.chromium.executable_path)
    except Exception:
        log.exception("Playwright is not importable")
        return None


def _install_chromium() -> bool:
    """Run `playwright install chromium` inline. Return True on success."""
    log.info("Chromium binary missing — installing via "
             "'python -m playwright install chromium' (one-time, ~30s)…")
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            capture_output=True, text=True, timeout=300, check=False,
        )
    except subprocess.TimeoutExpired:
        log.error("'playwright install chromium' timed out after 5 minutes")
        return False
    except Exception:
        log.exception("Failed to spawn 'playwright install chromium'")
        return False
    if proc.returncode != 0:
        log.error("'playwright install chromium' exited %d:\n%s",
                  proc.returncode, (proc.stderr or proc.stdout).strip())
        return False
    log.info("Chromium installed successfully")
    return True


def _ensure_chromium() -> bool:
    """Make sure Chromium is available, downloading it once if needed."""
    exe = _chromium_path()
    if exe is None:
        return False
    if exe.exists():
        return True
    if not _install_chromium():
        return False
    exe = _chromium_path()
    return bool(exe and exe.exists())


def _scrape_and_refresh() -> None:
    """Body of the background scrape thread. Refresh STORE if new data lands."""
    if not _ensure_chromium():
        log.warning("Chromium unavailable; keeping existing CSVs")
        return
    try:
        from scrape_team_stats import scrape
        log.info("Scraping fresh FIFA team stats in background")
        scrape()
        STORE.refresh()
    except Exception:
        log.exception("Background scrape failed; keeping existing CSVs")


def _kickoff_background_scrape() -> None:
    """Start the scrape in a daemon thread so the web port binds immediately."""
    if os.environ.get("SCRAPE_ON_STARTUP", "1") != "1":
        log.info("Startup scrape disabled (SCRAPE_ON_STARTUP=0)")
        return
    threading.Thread(
        target=_scrape_and_refresh, daemon=True, name="startup-scrape",
    ).start()


def build_app() -> dash.Dash:
    STORE.refresh()
    _kickoff_background_scrape()

    team_options = [
        {
            "label": f"{t} — eliminated" if t in ELIMINATED else t,
            "value": t,
        }
        for t in STORE.teams
    ]

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

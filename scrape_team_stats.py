"""Scrape all 7 tabs of the FIFA WC 2026 team-statistics page into CSVs.

Paths are portable: by default writes to ``./data`` next to this script.
Override with the ``WC_DATA_DIR`` env var or by calling ``scrape(data_dir=...)``.
"""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

URL = (
    "https://www.fifa.com/en/tournaments/mens/worldcup/"
    "canadamexicousa2026/statistics/team-statistics"
)

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"

TABS = [
    "Attacking",
    "Distribution",
    "Defending",
    "Discipline",
    "Goalkeeping",
    "Movement",
    "Physical",
]


# ---------------------------------------------------------------------------
# Page helpers
# ---------------------------------------------------------------------------


def _dismiss_cookies(page) -> None:
    for selector in (
        "#onetrust-accept-btn-handler",
        "button:has-text('Accept All')",
        "button:has-text('Accept all')",
        "button:has-text('I Accept')",
    ):
        try:
            btn = page.locator(selector).first
            if btn.is_visible(timeout=1500):
                btn.click()
                page.wait_for_timeout(500)
                return
        except Exception:
            pass


def _extract_largest_table(page) -> list[list[str]]:
    tables = page.evaluate(
        """
        () => {
          const out = [];
          document.querySelectorAll('table').forEach(t => {
            const rows = [];
            t.querySelectorAll('tr').forEach(tr => {
              const cells = [];
              tr.querySelectorAll('th,td').forEach(c => {
                cells.push(c.innerText.replace(/\\s+/g, ' ').trim());
              });
              if (cells.length) rows.push(cells);
            });
            if (rows.length) out.push(rows);
          });
          return out;
        }
        """
    )
    if not tables:
        return []
    return max(tables, key=lambda t: sum(len(r) for r in t))


def _table_signature(table: list[list[str]]) -> str:
    if not table:
        return ""
    header = "|".join(table[0])
    first_row = "|".join(table[1]) if len(table) > 1 else ""
    return f"{header}::{first_row}::{len(table)}"


def _click_tab(page, tab_name: str) -> bool:
    for sel in (
        f"button:has-text('{tab_name}')",
        f"a:has-text('{tab_name}')",
        f"[role='tab']:has-text('{tab_name}')",
        f"li:has-text('{tab_name}')",
        f"text=\"{tab_name}\"",
    ):
        loc = page.locator(sel).first
        try:
            if loc.count() == 0:
                continue
            loc.scroll_into_view_if_needed(timeout=2000)
            loc.click(timeout=3000)
            return True
        except Exception:
            continue
    return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _scrape_all_tabs() -> dict[str, list[list[str]]]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1440, "height": 900},
        )
        page = context.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        _dismiss_cookies(page)
        page.wait_for_selector("table", timeout=60000)
        page.mouse.wheel(0, 600)
        page.wait_for_timeout(800)

        prev_sig = ""
        results: dict[str, list[list[str]]] = {}

        for tab in TABS:
            print(f"-> {tab}", flush=True)
            if not _click_tab(page, tab):
                print(f"   ! could not find tab '{tab}', skipping", flush=True)
                continue
            try:
                page.wait_for_function(
                    """
                    (prev) => {
                      const t = document.querySelector('table');
                      if (!t) return false;
                      const rows = t.querySelectorAll('tr');
                      if (rows.length < 2) return false;
                      const head = Array.from(rows[0].querySelectorAll('th,td'))
                        .map(c => c.innerText.replace(/\\s+/g, ' ').trim()).join('|');
                      const first = Array.from(rows[1].querySelectorAll('th,td'))
                        .map(c => c.innerText.replace(/\\s+/g, ' ').trim()).join('|');
                      const sig = head + '::' + first + '::' + rows.length;
                      return sig !== prev;
                    }
                    """,
                    arg=prev_sig,
                    timeout=15000,
                )
            except PlaywrightTimeout:
                pass

            page.wait_for_timeout(500)
            table = _extract_largest_table(page)
            sig = _table_signature(table)
            if sig == prev_sig and prev_sig:
                print(f"   ! table did not change for '{tab}'", flush=True)
            prev_sig = sig
            results[tab] = table

        browser.close()
        return results


def _write_csv(data_dir: Path, tab: str, table: list[list[str]]) -> Path | None:
    if not table:
        print(f"   ! no rows for {tab}", flush=True)
        return None
    fname = data_dir / f"team_stats_{tab.lower()}.csv"
    with open(fname, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for row in table:
            writer.writerow(row)
    print(f"   wrote {len(table)} rows -> {fname.name}", flush=True)
    return fname


def scrape(data_dir: Path | str | None = None) -> dict[str, list[list[str]]]:
    """Scrape every FIFA tab and write CSVs into ``data_dir``.

    Resolution order for the output directory:
    explicit ``data_dir`` argument > ``WC_DATA_DIR`` env var > ``./data``.
    """
    if data_dir is None:
        data_dir = Path(os.environ.get("WC_DATA_DIR", DEFAULT_DATA_DIR))
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    results = _scrape_all_tabs()
    for tab, table in results.items():
        _write_csv(data_dir, tab, table)
    print(f"Done. {len(results)} tabs scraped to {data_dir}.", flush=True)
    return results


if __name__ == "__main__":
    try:
        scrape()
    except Exception as exc:  # pragma: no cover
        print(f"Scrape failed: {exc}", file=sys.stderr)
        sys.exit(1)

"""Thread-safe in-memory store for the live dataframe + precomputed figures.

A single module-level ``STORE`` instance is shared across the Dash app.
``STORE.refresh()`` reloads CSVs from disk and rebuilds the persistent
regression figure atomically; callbacks always read from the latest snapshot.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from datetime import datetime, timezone

import pandas as pd
import plotly.graph_objects as go

from .charts import goals_vs_attempts_persistent
from .data_loader import load_team_data
from .features import build_factor_scores
from .models import OLSResult, build_magic_factor

log = logging.getLogger(__name__)


@dataclass
class Snapshot:
    df: pd.DataFrame
    used: dict[str, list[str]]
    regression_fig: go.Figure
    ols: OLSResult
    teams: list[str]
    refreshed_at: datetime


class DataStore:
    """Holds the latest data snapshot. ``refresh()`` is safe to call concurrently."""

    def __init__(self) -> None:
        self._snapshot: Snapshot | None = None
        self._lock = threading.Lock()

    def refresh(self) -> Snapshot:
        log.info("Refreshing store from disk")
        df = load_team_data()
        df, used = build_factor_scores(df)
        magic = build_magic_factor(df)
        df["magic_factor"] = magic.magic
        used["magic_factor"] = magic.used_regressors
        fig, ols = goals_vs_attempts_persistent(df)
        teams = sorted(df["Team"].dropna().tolist())

        snap = Snapshot(
            df=df, used=used, regression_fig=fig, ols=ols,
            teams=teams, refreshed_at=datetime.now(timezone.utc),
        )
        with self._lock:
            self._snapshot = snap
        log.info("Store refreshed: %d teams at %s", len(teams), snap.refreshed_at)
        return snap

    @property
    def snapshot(self) -> Snapshot:
        if self._snapshot is None:
            self.refresh()
        return self._snapshot  # type: ignore[return-value]

    # Convenience accessors
    @property
    def df(self) -> pd.DataFrame: return self.snapshot.df
    @property
    def used(self) -> dict[str, list[str]]: return self.snapshot.used
    @property
    def regression_fig(self) -> go.Figure: return self.snapshot.regression_fig
    @property
    def ols(self) -> OLSResult: return self.snapshot.ols
    @property
    def teams(self) -> list[str]: return self.snapshot.teams
    @property
    def refreshed_at(self) -> datetime: return self.snapshot.refreshed_at


STORE = DataStore()

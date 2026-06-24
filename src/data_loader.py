"""Load and merge the 7 FIFA tab CSVs into one team-level frame."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

TAB_FILES = [
    "team_stats_attacking.csv",
    "team_stats_distribution.csv",
    "team_stats_defending.csv",
    "team_stats_discipline.csv",
    "team_stats_goalkeeping.csv",
    "team_stats_movement.csv",
    "team_stats_physical.csv",
]


# ---------------------------------------------------------------------------
# Column-name helpers
# ---------------------------------------------------------------------------


def _norm(name: str) -> str:
    s = str(name).lower().strip()
    s = s.replace("%", "pct")
    s = re.sub(r"[\(\)\[\]\.]", " ", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def find_col(df: pd.DataFrame, candidates: Iterable[str]) -> str | None:
    """Locate a column by trying each candidate against normalized names."""
    norm_map = {_norm(c): c for c in df.columns}
    for cand in candidates:
        key = _norm(cand)
        if key in norm_map:
            return norm_map[key]
    # substring fallback
    for cand in candidates:
        key = _norm(cand)
        for k, original in norm_map.items():
            if key and key in k:
                return original
    return None


def safe_series(df: pd.DataFrame, candidates: Iterable[str]) -> pd.Series:
    """Return numeric series for the first matching column, else all-NaN."""
    col = find_col(df, candidates if isinstance(candidates, (list, tuple)) else [candidates])
    if col is None:
        return pd.Series([np.nan] * len(df), index=df.index, name=None)
    s = df[col]
    if s.dtype == object:
        s = s.astype(str).str.replace(r"[%x,]", "", regex=True).str.strip()
        s = pd.to_numeric(s, errors="coerce")
    else:
        s = pd.to_numeric(s, errors="coerce")
    return s


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


def _read(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = clean_columns(df)
    # Normalize first column to "Rank" if header was edited
    if "Rank" not in df.columns and "Team" not in df.columns[:1].tolist():
        df = df.rename(columns={df.columns[0]: "Rank"})
    return df


def load_team_data(data_dir: Path | str = DATA_DIR) -> pd.DataFrame:
    """Return one wide team-level DataFrame merging every tab CSV on Team."""
    data_dir = Path(data_dir)
    frames = []
    for fname in TAB_FILES:
        fpath = data_dir / fname
        if not fpath.exists():
            continue
        df = _read(fpath)
        if "Team" not in df.columns:
            continue
        keep = [c for c in df.columns if c != "Rank"]
        frames.append(df[keep])
    if not frames:
        raise FileNotFoundError(f"No team_stats_*.csv files found in {data_dir}")

    merged = frames[0]
    for nxt in frames[1:]:
        dup = [c for c in nxt.columns if c in merged.columns and c != "Team"]
        nxt = nxt.drop(columns=dup)
        merged = merged.merge(nxt, on="Team", how="outer")

    # Coerce numeric columns; clean xG Efficiency "1.36x"
    for col in merged.columns:
        if col == "Team":
            continue
        if merged[col].dtype == object:
            cleaned = (
                merged[col].astype(str).str.replace(",", "", regex=False)
                .str.replace("x", "", regex=False)
                .str.replace("%", "", regex=False)
                .str.strip()
            )
            num = pd.to_numeric(cleaned, errors="coerce")
            if num.notna().sum() >= max(1, int(0.5 * len(merged))):
                merged[col] = num

    merged = merged.sort_values("Team").reset_index(drop=True)
    return merged


# ---------------------------------------------------------------------------
# Canonical column candidates
# ---------------------------------------------------------------------------

CANDIDATES: dict[str, list[str]] = {
    "goals": ["Goals"],
    "assists": ["Assists"],
    "attempts_at_goal": ["Attempts At Goal"],
    "attempts_on_target": ["Attempts On Target"],
    "conv_rate": [
        "Attempts At Goal Conv. Rate (%)",
        "Attempt At Goal Conv. Rate (%)",
        "Conversion Rate",
    ],
    "xg": ["xG"],
    "xg_efficiency": ["xG Efficiency", "xG Efficiency (%)"],
    "corners": ["Corners"],
    "possession": ["Possession Control (%)", "Possession Control"],
    "passes": ["Passes"],
    "passing_acc": ["Passing Accuracy (%)", "Passing Accuracy"],
    "crosses": ["Crosses"],
    "crossing_acc": ["Crossing Accuracy (%)", "Crossing Accuracy"],
    "def_linebreaks_att": ["Defensive Linebreaks Attempted"],
    "def_linebreaks_acc": ["Defensive Linebreaks Acc (%)", "Defensive Linebreaks Acc"],
    "switches_att": ["Switches of Play Attempted", "Switches of Play Completed"],
    "switches_acc": ["Switches of Play Acc (%)", "Switches of Play Acc"],
    "own_goals": ["Own Goals"],
    "goals_conceded": ["Goals Conceded"],
    "forced_turnovers": ["Forced Turnovers"],
    "ball_recovery_time": ["Ball Recovery Time (s)", "Ball Recovery Time"],
    "def_pressures": ["Defensive Pressures Applied"],
    "def_pressures_direct": ["Defensive Pressures Directly Applied"],
    "fouls_against": ["Fouls Against"],
    "fouls_for": ["Fouls For"],
    "yellow_cards": ["Yellow Cards"],
    "red_cards": ["Red Cards"],
    "offsides": ["Offsides"],
    "clean_sheets": ["Clean Sheets"],
    "gk_saves": ["Goalkeeper Saves"],
    "gk_save_pct": ["Goalkeeper Save Percentage (%)", "Goalkeeper Save Percentage"],
    "gk_actions_in_box": ["Goalkeeper Actions Inside the Penalty Area"],
    "gk_actions_out_box": ["Goalkeeper Actions Outside the Penalty Area"],
    "offers_to_receive": ["Offers To Receive"],
    "offers_in_behind": ["Offers In Behind"],
    "offers_in_between": ["Offers In Between"],
    "offers_in_front": ["Offers In Front"],
    "receptions_in_behind": ["Receptions In Behind"],
    "receptions_mid_def": ["Receptions Between Midfield And Defensive Line"],
    "receptions_under_pressure": ["Receptions Under Pressure"],
    "avg_speed": ["Average Speed (km/h)", "Average Speed"],
    "high_speed_running": ["High Speed Running"],
    "sprints": ["Sprints"],
    "top_speed": ["Top Speed (km/h)", "Top Speed"],
    "total_distance": ["Total Distance (m)", "Total Distance (km)", "Total Distance"],
}


def get(df: pd.DataFrame, key: str) -> pd.Series:
    return safe_series(df, CANDIDATES.get(key, [key]))


def column_exists(df: pd.DataFrame, key: str) -> bool:
    return find_col(df, CANDIDATES.get(key, [key])) is not None

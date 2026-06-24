"""Factor scores, z-scores, percentile ranks."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .data_loader import column_exists, get


def zscore(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    mu = s.mean()
    sd = s.std(ddof=0)
    if not sd or np.isnan(sd):
        return pd.Series(np.zeros(len(s)), index=s.index)
    return (s - mu) / sd


def percentile_rank(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    return s.rank(pct=True, method="average") * 100.0


def per90(s: pd.Series, minutes: pd.Series | None) -> pd.Series:
    if minutes is None:
        return s
    minutes = pd.to_numeric(minutes, errors="coerce").replace(0, np.nan)
    return s * (90.0 / minutes)


def aggregate_to_team(df: pd.DataFrame) -> pd.DataFrame:
    """Pass-through: the FIFA tab CSVs are already team-level."""
    return df


# ---------------------------------------------------------------------------
# Factor construction
# ---------------------------------------------------------------------------


@dataclass
class FactorSpec:
    """A weighted sum of z-scores of available metric keys.

    Each entry: (canonical_key, sign).  Missing keys are skipped.
    """

    name: str
    components: list[tuple[str, float]] = field(default_factory=list)


FACTORS: dict[str, FactorSpec] = {
    "verticality": FactorSpec(
        "Verticality",
        [
            ("offers_in_behind", +1),
            ("receptions_in_behind", +1),
            ("def_linebreaks_att", +1),
            ("def_linebreaks_acc", +1),
            ("receptions_mid_def", +1),
        ],
    ),
    "pressing": FactorSpec(
        "Pressing",
        [
            ("def_pressures", +1),
            ("def_pressures_direct", +1),
            ("forced_turnovers", +1),
            ("ball_recovery_time", -1),
        ],
    ),
    "transition_threat": FactorSpec(
        "Transition Threat",
        [
            ("receptions_in_behind", +1),
            ("attempts_at_goal", +1),
            ("xg", +1),
            ("forced_turnovers", +1),
            ("ball_recovery_time", -1),
        ],
    ),
    "between_lines": FactorSpec(
        "Between-Lines Play",
        [
            ("offers_in_between", +1),
            ("receptions_mid_def", +1),
            ("receptions_under_pressure", +1),
        ],
    ),
    "chance_creation": FactorSpec(
        "Chance Creation",
        [
            ("xg", +1),
            ("attempts_at_goal", +1),
            ("attempts_on_target", +1),
            ("corners", +1),
        ],
    ),
    "finishing_efficiency": FactorSpec(
        "Finishing Efficiency",
        [
            ("goals", +1),
            ("conv_rate", +1),
            ("xg_efficiency", +1),
        ],
    ),
    "physical_intensity": FactorSpec(
        "Physical Intensity",
        [
            ("high_speed_running", +1),
            ("sprints", +1),
            ("top_speed", +1),
            ("total_distance", +1),
        ],
    ),
}

MFI_WEIGHTS = {
    "verticality": 0.25,
    "pressing": 0.20,
    "transition_threat": 0.20,
    "between_lines": 0.15,
    "chance_creation": 0.10,
    "physical_intensity": 0.10,
}


def _build_one_factor(df: pd.DataFrame, spec: FactorSpec) -> tuple[pd.Series, list[str]]:
    used = []
    total = pd.Series(np.zeros(len(df)), index=df.index)
    n_used = 0
    for key, sign in spec.components:
        if not column_exists(df, key):
            continue
        s = get(df, key)
        if s.notna().sum() == 0:
            continue
        z = zscore(s.fillna(s.mean()))
        total = total + sign * z
        used.append(key)
        n_used += 1
    if n_used > 0:
        total = total / np.sqrt(n_used)  # rescale fairly
    return total, used


def build_factor_scores(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, list[str]]]:
    """Return df with factor columns appended and a map factor → components used."""
    out = df.copy()
    used_map: dict[str, list[str]] = {}
    for key, spec in FACTORS.items():
        score, used = _build_one_factor(out, spec)
        out[f"factor_{key}"] = score
        used_map[key] = used

    # Modern Football Index — weighted sum of available factor z-scores
    mfi = pd.Series(np.zeros(len(out)), index=out.index)
    total_w = 0.0
    mfi_used: list[str] = []
    for key, w in MFI_WEIGHTS.items():
        col = f"factor_{key}"
        if col in out.columns and out[col].notna().any():
            mfi = mfi + w * out[col]
            total_w += w
            mfi_used.append(key)
    if total_w > 0:
        mfi = mfi / total_w
    out["factor_modern_index"] = mfi
    used_map["modern_index"] = mfi_used
    return out, used_map


# ---------------------------------------------------------------------------
# Percentile DNA frame
# ---------------------------------------------------------------------------


DNA_FIELDS: list[tuple[str, str]] = [
    ("Verticality", "factor_verticality"),
    ("Pressing", "factor_pressing"),
    ("Transition Threat", "factor_transition_threat"),
    ("Between-Lines Play", "factor_between_lines"),
    ("Chance Creation", "factor_chance_creation"),
    ("Finishing Efficiency", "factor_finishing_efficiency"),
    ("Physical Intensity", "factor_physical_intensity"),
    ("Modern Football Index", "factor_modern_index"),
    ("Magic Factor", "magic_factor"),
]


def build_dna_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Return long-form percentile table for each DNA field per team."""
    rows = []
    for label, col in DNA_FIELDS:
        if col not in df.columns:
            continue
        pct = percentile_rank(df[col])
        for team, val, raw in zip(df["Team"], pct, df[col]):
            rows.append({"Team": team, "Metric": label, "Percentile": val, "Raw": raw})
    return pd.DataFrame(rows)

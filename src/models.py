"""OLS regression helpers and the Magic Factor model."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.api as sm

from .data_loader import column_exists, get


@dataclass
class OLSResult:
    slope: float
    intercept: float
    r2: float
    n: int
    fitted: pd.Series
    residual: pd.Series

    def equation(self) -> str:
        return f"y = {self.slope:.3f}x + {self.intercept:.2f}"


def fit_ols_regression(x: pd.Series, y: pd.Series) -> OLSResult:
    """Simple univariate OLS (statsmodels) returning slope/intercept/R² + residuals."""
    df = pd.DataFrame({"x": pd.to_numeric(x, errors="coerce"),
                       "y": pd.to_numeric(y, errors="coerce")}).dropna()
    if len(df) < 3:
        zeros = pd.Series([np.nan] * len(x), index=x.index)
        return OLSResult(0.0, 0.0, float("nan"), len(df), zeros, zeros)
    X = sm.add_constant(df["x"].values)
    model = sm.OLS(df["y"].values, X).fit()
    intercept, slope = model.params
    fitted_full = pd.Series(slope * pd.to_numeric(x, errors="coerce") + intercept,
                            index=x.index)
    resid_full = pd.to_numeric(y, errors="coerce") - fitted_full
    return OLSResult(
        slope=float(slope),
        intercept=float(intercept),
        r2=float(model.rsquared),
        n=int(model.nobs),
        fitted=fitted_full,
        residual=resid_full,
    )


# ---------------------------------------------------------------------------
# Magic Factor — multivariate residual
# ---------------------------------------------------------------------------


MAGIC_REGRESSORS: list[tuple[str, str]] = [
    # (label, source) — source is either canonical key or factor_* column name
    ("xG", "xg"),
    ("Attempts At Goal", "attempts_at_goal"),
    ("Receptions In Behind", "receptions_in_behind"),
    ("Receptions Mid-Def", "receptions_mid_def"),
    ("Def Linebreaks Attempted", "def_linebreaks_att"),
    ("Pressing", "factor_pressing"),
    ("Verticality", "factor_verticality"),
]


def _resolve_regressor(df: pd.DataFrame, source: str) -> pd.Series | None:
    if source.startswith("factor_"):
        if source in df.columns and df[source].notna().any():
            return df[source]
        return None
    if column_exists(df, source):
        s = get(df, source)
        if s.notna().any():
            return s
    return None


@dataclass
class MagicFactorResult:
    coefficients: dict[str, float]
    r2: float
    n_obs: int
    used_regressors: list[str]
    magic: pd.Series  # residuals aligned to df.index


def build_magic_factor(df: pd.DataFrame) -> MagicFactorResult:
    y_series = get(df, "goals")
    parts: dict[str, pd.Series] = {}
    used: list[str] = []
    for label, source in MAGIC_REGRESSORS:
        s = _resolve_regressor(df, source)
        if s is None:
            continue
        parts[label] = pd.to_numeric(s, errors="coerce")
        used.append(label)

    if not parts:
        zeros = pd.Series([0.0] * len(df), index=df.index)
        return MagicFactorResult({}, float("nan"), 0, [], zeros)

    X = pd.DataFrame(parts)
    keep = X.dropna().index.intersection(y_series.dropna().index)
    if len(keep) < len(used) + 2:
        zeros = pd.Series([0.0] * len(df), index=df.index)
        return MagicFactorResult({}, float("nan"), 0, used, zeros)

    Xf = sm.add_constant(X.loc[keep].values)
    model = sm.OLS(y_series.loc[keep].values, Xf).fit()
    coefs = dict(zip(["const"] + used, [float(c) for c in model.params]))

    # Fitted/residuals for every team (impute missing with column means)
    X_imp = X.fillna(X.mean())
    Xa = sm.add_constant(X_imp.values, has_constant="add")
    fitted_all = Xa @ np.array([coefs["const"], *[coefs[u] for u in used]])
    fitted_all = pd.Series(fitted_all, index=df.index)
    magic = pd.to_numeric(y_series, errors="coerce") - fitted_all
    magic = magic.fillna(0.0)

    return MagicFactorResult(
        coefficients=coefs,
        r2=float(model.rsquared),
        n_obs=int(model.nobs),
        used_regressors=used,
        magic=magic,
    )

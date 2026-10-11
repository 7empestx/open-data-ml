"""High-resolution SCADA (1 s to < 10 min) -> canonical 10-minute bins.

Per turbine and 10-minute bin [t, t+10min) (bin label = start, UTC):
  <signal>            mean of the samples in the bin (circular mean for 0-360° directions)
  <signal>_min/_max/_std   for the "stats" signals (population std, ddof=0; circular std for directions)
  <state>_last, <state>_mode   for status / state-code columns (last sample in time; most frequent value)
  coverage            samples present / samples expected (10 min / native interval), capped at 1
  n_samples           samples present
A sample belongs to the bin that contains the START of its own interval: with `label: end` the loader first moves
each timestamp back by ONE NATIVE interval (not by 10 minutes). Bins with no samples are absent (a gap); bins with
coverage below `min_coverage` keep coverage / n_samples but their signal values are set to NaN.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from .schema import FREQ, SIGNALS

BIN = pd.Timedelta(FREQ)
STANDARD = [pd.Timedelta(s) for s in ("1s", "2s", "5s", "10s", "15s", "20s", "30s", "1min", "2min", "5min", "10min",
                                       "15min", "30min", "1h")]
DEFAULT_STATS = ["power_kw", "wind_speed_ms", "rotor_speed_rpm", "generator_speed_rpm", "pitch_a_deg", "pitch_b_deg",
                 "pitch_c_deg", "gear_oil_inlet_pressure_bar", "gear_oil_pump_pressure_bar", "nacelle_position_deg",
                 "wind_direction_deg"]
CIRCULAR = {"nacelle_position_deg", "wind_direction_deg"}


def fmt_interval(td) -> str:
    """Timedelta -> short label: 1s, 30s, 1min, 10min, 1h."""
    if td is None or pd.isna(td):
        return "unknown"
    sec = pd.Timedelta(td).total_seconds()
    if sec < 60 or sec % 60:
        return f"{sec:g}s"
    if sec < 3600 or sec % 3600:
        return f"{sec / 60:g}min"
    return f"{sec / 3600:g}h"


def detect_interval(ts: pd.Series) -> tuple[pd.Timedelta | None, float]:
    """Native sampling interval of one turbine's timestamps: the most common positive step, snapped to a standard
    interval when within 2%. Returns (interval, share of steps equal to it)."""
    t = pd.Series(ts.dropna().unique()).sort_values()
    if len(t) < 3:
        return None, 0.0
    d = t.diff().dropna()
    d = d[d > pd.Timedelta(0)]
    if d.empty:
        return None, 0.0
    mode = d.mode().iloc[0]
    share = float((d == mode).mean())
    for s in STANDARD:
        if abs(mode - s) <= 0.02 * s:
            mode = s
            break
    return mode, share


def _circ_mean(sin_m: pd.Series, cos_m: pd.Series) -> pd.Series:
    return (np.degrees(np.arctan2(sin_m, cos_m)) % 360).where(sin_m.notna())


def aggregate(df: pd.DataFrame, native: pd.Timedelta, signals: list[str], stats: list[str] | None = None,
              states: list[str] = (), min_coverage: float = 0.5) -> tuple[pd.DataFrame, dict]:
    """Aggregate one or more turbines of high-res canonical data (timestamp = sample start, UTC) to 10-min bins."""
    stats = [s for s in (DEFAULT_STATS if stats is None else stats) if s in signals]
    expected = BIN / native
    d = df.sort_values(["turbine_id", "timestamp"], kind="stable")
    n_before = len(d)
    d = d.assign(_n=d[signals].notna().sum(axis=1)).sort_values(["turbine_id", "timestamp", "_n"], ascending=[True, True, False],
                                                                  kind="stable")
    d = d.drop_duplicates(["turbine_id", "timestamp"]).sort_values(["turbine_id", "timestamp"], kind="stable")
    info = {"native": fmt_interval(native), "expected_per_bin": float(expected), "duplicates_dropped": n_before - len(d)}
    d["_bin"] = d["timestamp"].dt.floor(FREQ)
    key = [d["turbine_id"], d["_bin"]]
    lin = [s for s in signals if s not in CIRCULAR]
    circ = [s for s in signals if s in CIRCULAR]
    work = d[lin].astype("float64")
    for c in circ:
        r = np.radians(d[c].astype("float64"))
        work[f"{c}__sin"], work[f"{c}__cos"] = np.sin(r), np.cos(r)
    g = work.groupby(key, sort=True)
    out = g.mean()
    for c in circ:
        out[c] = _circ_mean(out.pop(f"{c}__sin"), out.pop(f"{c}__cos"))
        rlen = np.hypot(g[f"{c}__sin"].mean(), g[f"{c}__cos"].mean()).clip(upper=1.0)
        if c in stats:   # circular std (deg); min/max are not meaningful for directions
            out[f"{c}_std"] = np.degrees(np.sqrt(-2 * np.log(rlen.where(rlen > 0))))
    lin_stats = [s for s in stats if s in lin]
    if lin_stats:
        gs = d[lin_stats].astype("float64").groupby(key, sort=True)
        mn, mx, sd = gs.min(), gs.max(), gs.std(ddof=0)
        for c in lin_stats:
            out[f"{c}_min"], out[f"{c}_max"], out[f"{c}_std"] = mn[c], mx[c], sd[c]
    n = (d["_n"] > 0).groupby(key, sort=True).sum()
    out["n_samples"] = n.astype("int32")
    out["coverage"] = (n / expected).clip(upper=1.0).astype("float32")
    for s in states:
        gs = d[s].groupby(key, sort=True)
        out[f"{s}_last"] = gs.last()
        out[f"{s}_mode"] = gs.agg(lambda x: x.mode().iloc[0] if x.notna().any() else np.nan)
    low = out["coverage"] < min_coverage
    value_cols = [c for c in out.columns if c not in ("n_samples", "coverage") and not any(c == f"{s}_last" or c == f"{s}_mode" for s in states)]
    out.loc[low, value_cols] = np.nan
    info["bins"] = int(len(out))
    info["bins_below_min_coverage"] = int(low.sum())
    info["mean_coverage"] = float(out["coverage"].mean()) if len(out) else 0.0
    out.index.names = ["turbine_id", "timestamp"]
    out = out.reset_index()
    out["turbine_id"] = out["turbine_id"].astype(str)
    return out, info


def stat_columns(signals) -> list[str]:
    return [f"{s}_{k}" for s in signals for k in ("min", "max", "std") if s in SIGNALS]

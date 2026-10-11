"""Stage 3: per-turbine condition metrics from the prepared turbines, the NBM residuals and the alarm log.

Assessment window: the last `window_months` (default 24) of each turbine's record; "final year" = its last 12 months.
Everything is computed per turbine from parquet column subsets, so memory stays small.

Definitions (generalised from the hand-built reports/condition_report, scripts/condition_*.py):
- Coverage: share of 10-min slots in the window with power or wind data.
- Technical availability (alarm log only): 1 - (fault or maintenance stop time) / window time.
  Without an alarm log: "non-production at wind" share (SCADA-inferred stops), reported but not used for flags.
- Energy availability: export / (export + lost production to downtime), when the export has those counters.
- Downtime by cause: first-cause attribution of overlapping stops (as condition_metrics.first_cause).
- Oil-system / pitch trip episodes: fault stops matching trip_features rules, merged within 24 h.
- NBM abnormal day: daily median residual z (operating rows) beyond 3 in the alarming direction; per component.
  "Abnormal oil days" = max |z| over the four oil targets > 3 (as the hand-built report). Chronic: >= 30% abnormal
  days in a month, and the longest run of such months in the window.
- Oil trends: monthly medians at full load (power > 49% of rated, not in a stop) of inlet pressure, pump pressure and
  oil temperature; rise = last month with >= 50 rows minus the median of the months before the window (or of the
  first 6 months when the record is too short).
- Sensor drift: hourly turbine value minus the median of the other turbines (ambient temperature) or
  ratio (wind speed, 4-12 m/s); drift = |median of the last 3 months - median before the window|.
- Stuck sensors: rows flagged frozen (qc bit 4) by cleaning, window.
"""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from .. import trip_features as tf
from . import health as hl

STEP_H = 1 / 6
FULL_LOAD_FRAC = 0.49
ABN_Z = 3.0
CHRONIC_SHARE = 0.30
OIL = ["gear_oil_temp_c", "gear_oil_inlet_temp_c", "gear_oil_inlet_pressure_bar", "gear_oil_pump_pressure_bar"]
FLAGS = ["in_any_stop", "in_fault", "in_stop_maintenance", "in_stop_grid", "in_stop_weather", "in_stop_curtailment", "in_stop_routine"]
# sensors that measure the same outside quantity at every turbine (nacelle temperature is left out on purpose: it
# depends on how hard each turbine works, so its offset to the fleet is not a sensor property)
DRIFT = {"ambient_temp_c": ("diff", "°C"), "wind_speed_ms": ("ratio", "")}
PRIO = {"fault": 0, "maintenance": 1, "weather": 2, "grid": 3, "curtailment": 4, "routine": 5}


def first_cause(stops: pd.DataFrame, lo, hi) -> pd.DataFrame:
    """Clip stops to [lo, hi) and remove overlap: a minute already covered by an earlier-starting stop is not counted again."""
    s = stops.copy()
    s["a"] = s["start"].clip(lower=lo, upper=hi)
    s["b"] = s["end_filled"].clip(lower=lo, upper=hi)
    s = s[s["b"] > s["a"]].copy()
    if s.empty:
        return s.assign(a_eff=s["a"], hours=0.0)
    s["prio"] = s["event_class"].map(PRIO).fillna(9)
    s["neg_b"] = -(s["b"].astype("int64"))
    s = s.sort_values(["a", "prio", "neg_b"])
    covered = pd.Timestamp.min.tz_localize("UTC")
    a_eff = []
    for a, b in zip(s["a"], s["b"]):
        a2 = max(a, covered)
        a_eff.append(a2 if a2 < b else b)
        covered = max(covered, b)
    s["a_eff"] = a_eff
    s = s[s["b"] > s["a_eff"]].copy()
    s["hours"] = (s["b"] - s["a_eff"]).dt.total_seconds() / 3600
    return s


def _read(path: Path, want: list[str]) -> pd.DataFrame:
    have = set(pq.ParquetFile(path).schema.names)
    return pd.read_parquet(path, columns=[c for c in want if c in have])


def _abn(z: pd.Series, side: str) -> pd.Series:
    if side == "pos":
        return z > ABN_Z
    if side == "neg":
        return z < -ABN_Z
    return z.abs() > ABN_Z


def window_of(d: pd.DataFrame, months: int):
    have = d["row_in_source"] & ~d.get("row_empty", False)
    t = d.loc[have, "timestamp"]
    end = t.max() + pd.Timedelta("10min")
    start = max(t.min(), end - pd.DateOffset(months=months))
    fy = max(t.min(), end - pd.DateOffset(months=12))
    return t.min(), start, fy, end


def turbine(work: Path, tid: str, rated_kw: float, ev: pd.DataFrame | None, window_months: int) -> tuple[dict, dict]:
    p = work / "turbines" / f"{tid}.parquet"
    names = pq.ParquetFile(p).schema.names
    qc_cols = [c for c in names if c.startswith("qc_")]
    d = _read(p, ["timestamp", "row_in_source", "row_empty", "power_kw", "wind_speed_ms", "ambient_temp_c", "nacelle_temp_c",
                  "energy_export_kwh", "lost_prod_downtime_kwh"] + OIL + FLAGS + qc_cols)
    d = d.sort_values("timestamp").reset_index(drop=True)
    first, w0, fy0, end = window_of(d, window_months)
    r = {"turbine_id": tid, "first": first, "window_start": w0, "final_year_start": fy0, "end": end,
         "history_months": round((end - first) / pd.Timedelta(days=30.44), 1)}
    w = d[(d["timestamp"] >= w0) & (d["timestamp"] < end)]
    missing = ~w["row_in_source"] | w["row_empty"]
    r["coverage_window"] = float(1 - missing.mean())
    run = (missing != missing.shift()).cumsum()
    r["longest_gap_h_window"] = float(missing.groupby(run).sum().max() * STEP_H) if missing.any() else 0.0
    # signals and stuck sensors
    present = [c[3:] for c in qc_cols if c[3:] in d and d[c[3:]].notna().mean() > 0.05]
    r["signals"] = present
    fro = {c[3:]: int(((w[c] & 4) > 0).sum()) for c in qc_cols if c[3:] in present}
    r["frozen_rows_window"] = fro
    r["stuck_sensors"] = sorted(k for k, v in fro.items() if v >= 0.01 * len(w))
    tables = {}
    # availability and stops
    has_log = ev is not None
    if has_log:
        tech = (w["in_fault"] | w["in_stop_maintenance"]).astype(bool)
        r["avail_time"] = float(1 - tech.mean())
        if "energy_export_kwh" in w and "lost_prod_downtime_kwh" in w and w["energy_export_kwh"].notna().any():
            ex, lost = w["energy_export_kwh"].sum(), w["lost_prod_downtime_kwh"].sum()
            r["avail_energy"] = float(ex / (ex + lost)) if ex + lost > 0 else np.nan
        e = ev[ev["turbine_id"] == tid]
        stops = e[e["is_stop"]].copy()
        stops["cause"] = np.where(stops["event_class"] == "fault", "fault: " + stops["component"].astype(str), stops["event_class"].astype(str))
        st = first_cause(stops, w0, end)
        yrs = (end - w0) / pd.Timedelta(days=365.25)
        dt = st.groupby("cause")["hours"].agg(["sum", "size"]).rename(columns={"sum": "hours", "size": "n"}).sort_values("hours", ascending=False)
        tables["downtime"] = dt.reset_index().assign(turbine_id=tid)
        r["fault_h_per_yr"] = float(dt.loc[dt.index.str.startswith("fault"), "hours"].sum() / yrs)
        r["maint_h_per_yr"] = float(dt.loc[dt.index == "maintenance", "hours"].sum() / yrs)
        top = dt[dt.index.str.startswith("fault")]
        r["top_fault_cause"] = f"{top.index[0].replace('fault: ', '')} ({top['hours'].iloc[0]:.0f} h)" if len(top) else ""
        ws = stops[(stops["start"] >= w0) & (stops["start"] < end)]
        r["stops_window"] = ws["event_class"].value_counts().to_dict()
        r["major_faults_window"] = int(e[(e["start"] >= w0) & (e["start"] < end) & e["is_major_fault"]]["major_episode"].nunique())
        fc = ws[ws["is_fault_stop"]].groupby(["code", "message", "component"], dropna=False).agg(n=("start", "size"))
        tables["fault_codes"] = fc.sort_values("n", ascending=False).head(10).reset_index().assign(turbine_id=tid)
        for k in ("oil", "pitch"):
            trips = tf.trips(e, k)
            eps = tf.trip_episodes(trips) if len(trips) else pd.DataFrame(columns=["start"])
            r[f"{k}_ep_window"] = int(((eps["start"] >= w0) & (eps["start"] < end)).sum()) if len(eps) else 0
            r[f"{k}_trips_window"] = int(((trips["start"] >= w0) & (trips["start"] < end)).sum()) if len(trips) else 0
            s = eps["start"].sort_values() if len(eps) else pd.Series(dtype="datetime64[ns, UTC]")
            r[f"{k}_repeat30"] = float((s.diff() <= pd.Timedelta(days=30)).sum() / len(s)) if len(s) > 1 else np.nan
    else:
        r["nonprod_at_wind"] = float(w["in_any_stop"].astype(bool).mean())
    # monthly table: coverage, full-load oil medians
    d["month"] = d["timestamp"].dt.strftime("%Y-%m")
    stop = d["in_any_stop"].fillna(True).astype(bool)
    full = d[(d.get("power_kw", pd.Series(np.nan, index=d.index)) > FULL_LOAD_FRAC * rated_kw) & ~stop]
    mon = pd.DataFrame({"coverage": (d["row_in_source"] & ~d["row_empty"]).groupby(d["month"]).mean()})
    for c, lab in (("gear_oil_inlet_pressure_bar", "inlet"), ("gear_oil_pump_pressure_bar", "pump"), ("gear_oil_temp_c", "oil_t")):
        if c in full and full[c].notna().any():
            mon[lab] = full.groupby("month")[c].median()
            mon[f"n_{lab}"] = full.groupby("month")[c].count()
    if "nonprod_at_wind" in r or has_log:
        mon["stop_share"] = stop.groupby(d["month"]).mean()
    wm0 = f"{w0:%Y-%m}"
    for lab in ("pump", "inlet", "oil_t"):
        if lab not in mon:
            continue
        s = mon[lab].where(mon[f"n_{lab}"] >= 50).dropna()
        if len(s) < 3:
            continue
        pre = s[s.index < wm0]
        base = pre if len(pre) >= 6 else s.iloc[:6]
        r[f"{lab}_base"] = float(base.median())
        r[f"{lab}_base_period"] = f"{base.index[0]}..{base.index[-1]}"
        r[f"{lab}_last"] = float(s.iloc[-1])
        r[f"{lab}_last_month"] = s.index[-1]
        r[f"{lab}_rise"] = float(s.iloc[-1] - base.median())
        r[f"{lab}_peak_rise"] = float(s[s.index >= wm0].max() - base.median()) if (s.index >= wm0).any() else np.nan
    # hourly series for fleet drift
    hourly = {}
    for c in DRIFT:
        if c in d and d[c].notna().mean() > 0.2:
            hourly[c] = d.set_index("timestamp")[c].astype("float64").resample("1h").median()
    # NBM residual health
    zp = work / "health" / f"{tid}.parquet"
    if zp.exists():
        z = pd.read_parquet(zp)
        z = z[~z["stop"].astype(bool)]
        zc = [c for c in z.columns if c.startswith("z_") and z[c].notna().any()]
        if zc:
            z["date"] = z["timestamp"].dt.floor("D")
            dm = z.groupby("date")[zc].median()
            dm = dm[dm.notna().any(axis=1)]
            comp = {}
            for c in zc:
                t = c[2:]
                comp.setdefault(hl.COMPONENT.get(t, "other"), []).append(c)
            ab = pd.DataFrame(index=dm.index)
            for g, cs in comp.items():
                flags = pd.concat([_abn(dm[c], hl.SIDE.get(c[2:], "abs")).astype(float).where(dm[c].notna()) for c in cs], axis=1)
                ab[g] = flags.max(axis=1)
            oz = [f"z_{t}" for t in OIL if f"z_{t}" in dm]
            if oz:
                ab["oil"] = (dm[oz].abs().max(axis=1) > ABN_Z).astype(float).where(dm[oz].notna().any(axis=1))   # as the hand-built report
            day = ab.index
            fyr = ab[(day >= fy0.floor("D")) & (day < end)]
            win = ab[(day >= w0.floor("D")) & (day < end)]
            for g in ab.columns:
                r[f"abn_{g}_final_year"] = float(fyr[g].mean()) if fyr[g].notna().sum() >= 30 else np.nan
                r[f"abn_{g}_window"] = float(win[g].mean()) if win[g].notna().sum() >= 30 else np.nan
                r[f"scored_days_{g}_window"] = int(win[g].notna().sum())
                m = win[g].groupby(win.index.strftime("%Y-%m")).agg(["mean", "count"])
                m = m[m["count"] >= 10]["mean"]
                chronic = m >= CHRONIC_SHARE
                r[f"chronic_months_{g}"] = int(chronic.sum())
                runs = (chronic != chronic.shift()).cumsum()
                r[f"chronic_run_{g}"] = int(chronic.groupby(runs).sum().max()) if len(chronic) else 0
                mon[f"abn_{g}"] = ab[g].groupby(ab.index.strftime("%Y-%m")).mean()
            r["window_scored_share"] = float(dm[(dm.index >= w0.floor("D"))].shape[0] / max(1, (end - w0).days))
        mp = work / "health" / f"{tid}_meta.csv"
        meta = pd.read_csv(mp) if mp.exists() and mp.stat().st_size > 10 else pd.DataFrame()
        if len(meta) and "mae_test_healthy" in meta:
            mm = meta[(meta["target"] == "gear_oil_temp_c") & meta["mae_test_healthy"].notna()]
            if len(mm) >= 3 and mm["scheme"].iloc[0] == "walk-forward":
                last = mm.iloc[-1]
                prior = mm.iloc[:-2]   # the final block vs the blocks before the 2-year window
                r["oil_temp_mae_ratio"] = float(last["mae_test_healthy"] / prior["mae_test_healthy"].mean())
                r["oil_temp_mae_baseline"] = f"{prior['block'].iloc[0]}..{prior['block'].iloc[-1]}"
            fit = meta[meta.get("skipped", pd.Series("", index=meta.index)).fillna("") == ""]
            if "mae_val" in fit:
                r["model_fit"] = fit.groupby("target")["mae_val"].median().round(3).to_dict()
    mon = mon.reset_index().rename(columns={"index": "month"}).assign(turbine_id=tid)
    tables["monthly"] = mon
    tables["hourly"] = hourly
    return r, tables


def drift(hourly: dict[str, dict[str, pd.Series]], T: dict[str, dict]) -> pd.DataFrame:
    """Monthly offset of each turbine vs the median of the other turbines; sets drift_* in T."""
    rows = []
    for sig, (how, unit) in DRIFT.items():
        series = {tid: h[sig] for tid, h in hourly.items() if sig in h}
        if len(series) < 4:   # the median of >= 3 other turbines is robust to one drifting sensor
            continue
        df = pd.DataFrame(series)
        for tid in df.columns:
            others = df.drop(columns=tid).median(axis=1)
            if how == "diff":
                off = df[tid] - others
            else:
                ok = others.between(4, 12)
                off = (df[tid] / others).where(ok)
            mo = off.groupby(off.index.strftime("%Y-%m")).median().dropna()
            if len(mo) < 6:
                continue
            for mth, v in mo.items():
                rows.append({"turbine_id": tid, "signal": sig, "month": mth, "offset": float(v)})
            w0 = f"{T[tid]['window_start']:%Y-%m}"
            pre = mo[mo.index < w0]
            base = pre if len(pre) >= 6 else mo.iloc[:6]
            last = mo.iloc[-3:]
            dv = float(last.median() - base.median())
            T[tid][f"drift_{sig}"] = dv
    return pd.DataFrame(rows)


def compute(work: Path, prep: dict, window_months: int = 24, echo=print) -> dict:
    work = Path(work)
    ev = pd.read_parquet(work / "events.parquet") if prep["has_status_log"] and (work / "events.parquet").exists() else None
    T, tabs, hourly = {}, {"downtime": [], "fault_codes": [], "monthly": []}, {}
    for t in prep["turbines"]:
        tid = t["turbine_id"]
        r, tb = turbine(work, tid, float(t["rated_kw"]), ev, window_months)
        r["label_source"] = t["label_source"]
        r["native_interval"] = (t.get("native_interval") or {}).get("interval", "10min")
        T[tid] = r
        for k in ("downtime", "fault_codes", "monthly"):
            if k in tb and len(tb[k]):
                tabs[k].append(tb[k])
        hourly[tid] = tb["hourly"]
    dr = drift(hourly, T)
    out = {k: (pd.concat(v, ignore_index=True) if v else pd.DataFrame()) for k, v in tabs.items()}
    out["drift"] = dr
    out["turbines"] = T
    hp = work / "health" / "health.json"
    out["health"] = {h["turbine_id"]: h for h in json.loads(hp.read_text())} if hp.exists() else {}
    return out

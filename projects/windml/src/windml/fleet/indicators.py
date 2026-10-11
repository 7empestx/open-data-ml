"""As-of indicators per turbine and month, used both to calibrate the RAG rules on history and to rate the turbine at
the end of its record. Every indicator at month-end t uses only data up to t (the NBM residuals come from
walk-forward models trained on earlier years, or cross-fitted for short histories).

Per turbine and month-end:
  abn_<comp>_3m   share of abnormal operating days (daily median residual z beyond 3 in the harmful direction) in the
                  last 3 months, comp in oil / pitch / main_bearing / performance; abn_<comp>_months = how many of the
                  last 3 months had >= 30% abnormal days (persistence)
  pump_rise       full-load gear-oil pump pressure: median of the last 14 days minus the median of days -365..-60
                  (the slow build-up that precedes filter/pump service); inlet_rise likewise
  oil_ep_6m, pitch_ep_6m  trip episodes (fault stops matching trip_features, merged within 24 h) in the last 180 days
  avail_6m        1 - fault/maintenance stop share in the last 180 days (alarm log only)
  coverage_3m     share of 10-min slots with data in the last 3 months
Fleet-relative versions (<ind>_rel) = (value - median of the other turbines that month) / robust spread with a floor,
so a fleet-wide season or logger change does not flag everybody.
"""
from __future__ import annotations
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from .. import trip_features as tf
from . import health as hl

ABN_Z = 3.0
COMPS = ("oil", "pitch", "main_bearing", "performance")
OIL = ["gear_oil_temp_c", "gear_oil_inlet_temp_c", "gear_oil_inlet_pressure_bar", "gear_oil_pump_pressure_bar"]
FULL_LOAD_FRAC = 0.49
REL_FLOOR = {"abn_oil_3m": 0.05, "abn_pitch_3m": 0.05, "abn_main_bearing_3m": 0.05, "abn_performance_3m": 0.05,
             "pump_rise": 0.15, "inlet_rise": 0.05, "avail_6m": 0.01}


def _daily_abnormal(zp: Path) -> pd.DataFrame:
    z = pd.read_parquet(zp)
    z = z[~z["stop"].astype(bool)]
    zc = [c for c in z.columns if c.startswith("z_") and z[c].notna().any()]
    if not zc:
        return pd.DataFrame()
    dm = z.groupby(z["timestamp"].dt.floor("D"))[zc].median()
    out = pd.DataFrame(index=dm.index)
    groups = {}
    for c in zc:
        groups.setdefault(hl.COMPONENT.get(c[2:], "other"), []).append(c)
    for g, cs in groups.items():
        fl = []
        for c in cs:
            side = hl.SIDE.get(c[2:], "abs")
            v = dm[c]
            a = v > ABN_Z if side == "pos" else v < -ABN_Z if side == "neg" else v.abs() > ABN_Z
            fl.append(a.astype(float).where(v.notna()))
        out[g] = pd.concat(fl, axis=1).max(axis=1)
    oz = [f"z_{t}" for t in OIL if f"z_{t}" in dm]
    if oz:   # as the hand-built report: any oil target beyond |3|
        out["oil"] = (dm[oz].abs().max(axis=1) > ABN_Z).astype(float).where(dm[oz].notna().any(axis=1))
    return out


def turbine_panel(work: Path, tid: str, rated_kw: float, ev: pd.DataFrame | None) -> pd.DataFrame:
    p = work / "turbines" / f"{tid}.parquet"
    have = set(pq.ParquetFile(p).schema.names)
    cols = [c for c in ["timestamp", "row_in_source", "row_empty", "power_kw", "in_any_stop", "in_fault", "in_stop_maintenance",
                        "gear_oil_pump_pressure_bar", "gear_oil_inlet_pressure_bar"] if c in have]
    d = pd.read_parquet(p, columns=cols).sort_values("timestamp")
    d["day"] = d["timestamp"].dt.floor("D")
    ok = d["row_in_source"] & ~d["row_empty"]
    day = pd.DataFrame({"cov": ok.groupby(d["day"]).mean()})
    if "in_fault" in d and ev is not None:
        day["down"] = (d["in_fault"] | d["in_stop_maintenance"]).astype(float).groupby(d["day"]).mean()
    stop = d["in_any_stop"].fillna(True).astype(bool)
    full = d[(d["power_kw"] > FULL_LOAD_FRAC * rated_kw) & ~stop]
    for c, lab in (("gear_oil_pump_pressure_bar", "pump"), ("gear_oil_inlet_pressure_bar", "inlet")):
        if c in full and full[c].notna().any():
            g = full.groupby("day")[c]
            day[lab] = g.median().where(g.count() >= 6)
    zp = work / "health" / f"{tid}.parquet"
    if zp.exists():
        ab = _daily_abnormal(zp)
        for c in ab.columns:
            day[f"abn_{c}"] = ab[c]
    day = day.asfreq("D")
    first, last = d.loc[ok, "timestamp"].min(), d.loc[ok, "timestamp"].max()
    ends = pd.date_range(first.ceil("D") + pd.offsets.MonthEnd(0), last.floor("D"), freq="ME", tz="UTC")
    if len(ends) == 0 or last.floor("D") > ends[-1] + pd.Timedelta(days=14):   # as-of the end of the record too
        ends = ends.append(pd.DatetimeIndex([last.floor("D")]))
    if ev is not None:
        e = ev[ev["turbine_id"] == tid]
        eps = {}
        for k in ("oil", "pitch"):
            tr = tf.trips(e, k)
            eps[k] = tf.trip_episodes(tr)["start"].sort_values().reset_index(drop=True) if len(tr) else pd.Series(dtype="datetime64[ns, UTC]")
    rows = []
    for t in ends:
        t1 = t + pd.Timedelta(days=1)          # month-end day included
        w3 = day[(day.index > t1 - pd.Timedelta(days=91)) & (day.index < t1)]
        r = {"turbine_id": tid, "as_of": t, "history_days": float((t1 - first) / pd.Timedelta(days=1)),
             "coverage_3m": float(w3["cov"].mean()) if len(w3) else np.nan}
        for c in COMPS:
            col = f"abn_{c}"
            if col in w3 and w3[col].notna().sum() >= 20:
                r[f"abn_{c}_3m"] = float(w3[col].mean())
                m = [w3[col][(w3.index > t1 - pd.Timedelta(days=30 * (k + 1))) & (w3.index <= t1 - pd.Timedelta(days=30 * k))] for k in range(3)]
                r[f"abn_{c}_months"] = int(sum(1 for x in m if x.notna().sum() >= 8 and x.mean() >= 0.30))
        for lab in ("pump", "inlet"):
            if lab in day:
                recent = day[lab][(day.index > t1 - pd.Timedelta(days=15)) & (day.index < t1)].dropna()
                base = day[lab][(day.index > t1 - pd.Timedelta(days=366)) & (day.index <= t1 - pd.Timedelta(days=60))].dropna()
                if len(recent) >= 5 and len(base) >= 60:
                    r[f"{lab}_rise"] = float(recent.median() - base.median())
                    r[f"{lab}_now"] = float(recent.median())
        if ev is not None:
            w6 = day[(day.index > t1 - pd.Timedelta(days=181)) & (day.index < t1)]
            if "down" in w6 and w6["down"].notna().sum() >= 60:
                r["avail_6m"] = float(1 - w6["down"].mean())
            for k in ("oil", "pitch"):
                s = eps[k]
                r[f"{k}_ep_6m"] = int(((s > t1 - pd.Timedelta(days=180)) & (s <= t1)).sum()) if len(s) else 0
        rows.append(r)
    return pd.DataFrame(rows)


def fleet_relative(panel: pd.DataFrame) -> pd.DataFrame:
    """Add <ind>_rel: distance to the median of the OTHER turbines in the same month, in robust spreads (floored)."""
    panel = panel.copy()
    panel["month"] = panel["as_of"].dt.strftime("%Y-%m")
    for ind, floor in REL_FLOOR.items():
        if ind not in panel:
            continue
        rel = pd.Series(np.nan, index=panel.index)
        for _, g in panel.groupby("month"):
            v = g[ind]
            if v.notna().sum() < 4:
                continue
            for i in g.index:
                o = v.drop(i).dropna()
                if len(o) < 3 or pd.isna(v[i]):
                    continue
                med = o.median()
                spread = max(1.4826 * float((o - med).abs().median()), floor)
                rel[i] = (v[i] - med) / spread
        panel[f"{ind}_rel"] = rel
    return panel


def panel(work: Path, prep: dict) -> pd.DataFrame:
    work = Path(work)
    ev = pd.read_parquet(work / "events.parquet") if prep["has_status_log"] and (work / "events.parquet").exists() else None
    parts = [turbine_panel(work, t["turbine_id"], float(t["rated_kw"]), ev) for t in prep["turbines"]]
    return fleet_relative(pd.concat(parts, ignore_index=True))


def outcome_labels(panel: pd.DataFrame, ev: pd.DataFrame, horizon_days: int = 90) -> pd.DataFrame:
    """Events in (asof, asof + horizon]: oil-system trip episode or gearbox major fault ('oil'); pitch trip episode or
    pitch major fault ('pitch'); a major-fault episode of any component ('major'); a long service stop: maintenance
    >= 24 h ('service')."""
    out = panel.copy()
    major = ev[ev["is_major_fault"]].sort_values("start").groupby(["turbine_id", "major_episode"]).head(1)
    maint = ev[(ev["event_class"] == "maintenance") & ev["is_stop"] & (ev["duration"] >= pd.Timedelta(hours=24))]
    starts = {}
    for tid in out["turbine_id"].unique():
        e = ev[ev["turbine_id"] == tid]
        oil = tf.trip_episodes(tf.trips(e, "oil"))["start"] if len(tf.trips(e, "oil")) else pd.Series(dtype="datetime64[ns, UTC]")
        pit = tf.trip_episodes(tf.trips(e, "pitch"))["start"] if len(tf.trips(e, "pitch")) else pd.Series(dtype="datetime64[ns, UTC]")
        mj = major[major["turbine_id"] == tid]
        starts[tid] = {
            "oil": pd.concat([oil, mj[mj["component"] == "gearbox"]["start"]]),
            "pitch": pd.concat([pit, mj[mj["component"] == "pitch"]["start"]]),
            "major": mj["start"], "service": maint[maint["turbine_id"] == tid]["start"]}
    H = pd.Timedelta(days=horizon_days)
    for k in ("oil", "pitch", "major", "service"):
        vals = []
        for tid, t in zip(out["turbine_id"], out["as_of"]):
            s = starts[tid][k]
            t1 = t + pd.Timedelta(days=1)
            vals.append(bool(((s >= t1) & (s < t1 + H)).any()))
        out[f"y_{k}"] = vals
    return out

"""Short-term trip prediction: labels and features (hourly rows, causal features only).

Trips = fault-stop events (is_fault_stop) of one type:
  oil   : gearbox oil-system codes (missing gear oil, low gearbox oil pressure, gear-oil pump / cooler-fan overload,
          particle gear alarm)
  pitch : component == "pitch"
Trip episodes = trips of that type merged when they start < 24 h apart (first trip time kept).
Rows: one per hour (on the hour), excluding rows in a stop or fault. Label y_H = a trip of that type starts in (t, t+H].
All rolling sensor features use operating rows only (values are masked during stops), so they do not encode stop history.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

OIL_CODES = {"1550", "1510", "1800", "1815", "1924"}
OIL_MSG = ("missing gear oil", "low gearbox oil pressure", "overload gear oil pump", "overload fan oil cooler gear", "particle gear alarm")
LAB_COLS = ["timestamp", "power_kw", "wind_speed_ms", "ambient_temp_c", "rotor_speed_rpm", "gear_oil_temp_c",
            "gear_oil_inlet_temp_c", "pitch_a_deg", "pitch_b_deg", "pitch_c_deg", "in_any_stop", "in_fault"]
HORIZONS = (24, 48, 72)


def trips(events: pd.DataFrame, kind: str) -> pd.DataFrame:
    fs = events[events["is_fault_stop"]].copy()
    if kind == "oil":
        msg = fs["message"].fillna("").str.lower()
        m = fs["code"].astype(str).isin(OIL_CODES) | msg.str.contains("|".join(OIL_MSG))
        fs = fs[m & (fs["component"] == "gearbox")]
    else:
        fs = fs[fs["component"] == "pitch"]
    fs["start"] = pd.to_datetime(fs["start"], utc=True)
    return fs[["turbine_id", "start", "code", "message", "is_major_fault"]].sort_values(["turbine_id", "start"])


def trip_episodes(tr: pd.DataFrame, gap_h: float = 24) -> pd.DataFrame:
    out = []
    for tid, g in tr.groupby("turbine_id"):
        s = g["start"].sort_values()
        new = s.diff().isna() | (s.diff() > pd.Timedelta(hours=gap_h))
        ep = g.loc[new.values].copy()
        ep["n_trips"] = new.cumsum().value_counts().sort_index().values
        major = g.assign(k=new.cumsum().values).groupby("k")["is_major_fault"].any().values
        ep["any_major"] = major
        out.append(ep)
    e = pd.concat(out).reset_index(drop=True)
    e["year"] = e["start"].dt.year
    return e


def fix_units(d: pd.DataFrame, mean_col: str, cols) -> None:
    """Rows whose 10-min mean (or max, if mean is missing) exceeds 20 are logged x100 (kPa): divide all stats by 100."""
    flag = (d[mean_col] > 20) | (d[mean_col].isna() & (d[cols[1]] > 20))
    for c in cols:
        d[c] = d[c].where(~flag, d[c] / 100.0)


def load(farm: str, tid: str, data_dir, nbm_dir=None) -> pd.DataFrame:
    lab = pq.read_table(data_dir / f"{farm}_scada_labeled.parquet", columns=LAB_COLS, filters=[("turbine_id", "==", tid)]).to_pandas()
    st = pd.read_parquet(data_dir / f"{farm}_stats_{tid}.parquet")
    ex = pd.read_parquet(data_dir / f"{farm}_extra_{tid}.parquet", columns=["timestamp", "pitch_motor_temp_1_c", "pitch_motor_temp_2_c",
                                                                             "pitch_motor_temp_3_c", "hub_temp_c"])
    d = lab.sort_values("timestamp").merge(st, on="timestamp", how="left").merge(ex, on="timestamp", how="left").reset_index(drop=True)
    for c in d.columns:
        if d[c].dtype == "float64":
            d[c] = d[c].astype("float32")
    fix_units(d, "inlet_p_mean", ["inlet_p_mean", "inlet_p_max", "inlet_p_min", "inlet_p_std"])
    fix_units(d, "pump_p_mean", ["pump_p_mean", "pump_p_max", "pump_p_min", "pump_p_std"])
    for b in "ABC":
        for s in ("max", "min"):
            c = f"pitch{b}_{s}"; d[c] = d[c].where((d[c] > -10) & (d[c] < 100))
    for c in [f"mtemp{a}_max" for a in (1, 2, 3)] + ["pitch_motor_temp_1_c", "pitch_motor_temp_2_c", "pitch_motor_temp_3_c"]:
        d[c] = d[c].where((d[c] > -30) & (d[c] < 150))
    if nbm_dir is not None:
        z = pd.read_parquet(nbm_dir / f"{farm}_{tid}.parquet")
        zc = [c for c in z.columns if c.startswith("z_")]
        d = d.merge(z[["timestamp"] + zc], on="timestamp", how="left")
    return d


def _roll(s, w, how):
    r = s.rolling(w, min_periods=max(1, w // 6))
    return getattr(r, how)()


def sensor_features(d: pd.DataFrame) -> pd.DataFrame:
    run = (~d["in_any_stop"].fillna(True).astype(bool)) & (d["rotor_speed_rpm"].fillna(0) > 3)
    F = {}
    m = lambda c: d[c].where(run)  # mask non-operating rows
    # ---- 10-min statistics (current row)
    for p in ("inlet_p", "pump_p"):
        F[f"{p}_min"] = m(f"{p}_min"); F[f"{p}_max"] = m(f"{p}_max"); F[f"{p}_std"] = m(f"{p}_std"); F[f"{p}_mean"] = m(f"{p}_mean")
        F[f"{p}_drop"] = m(f"{p}_mean") - m(f"{p}_min")
    for c in ("oil_t_max", "oil_t_std", "inlet_t_max", "inlet_t_std", "gear_oil_temp_c", "gear_oil_inlet_temp_c", "rotor_rpm_std"):
        F[c] = m(c)
    cmax = pd.concat([m(f"cur{a}_max") for a in (1, 2, 3)], axis=1)
    cstd = pd.concat([m(f"cur{a}_std") for a in (1, 2, 3)], axis=1)
    for a in (1, 2, 3):
        F[f"cur{a}_max"] = cmax.iloc[:, a - 1]; F[f"cur{a}_std"] = cstd.iloc[:, a - 1]
    F["cur_max_max"] = cmax.max(axis=1); F["cur_max_spread"] = cmax.max(axis=1) - cmax.min(axis=1)
    F["cur_std_mean"] = cstd.mean(axis=1); F["cur_std_spread"] = cstd.max(axis=1) - cstd.min(axis=1)
    pmax = pd.concat([m(f"pitch{b}_max") for b in "ABC"], axis=1); pmin = pd.concat([m(f"pitch{b}_min") for b in "ABC"], axis=1)
    pstd = pd.concat([m(f"pitch{b}_std") for b in "ABC"], axis=1); pmean = pd.concat([m(f"pitch_{b.lower()}_deg") for b in "ABC"], axis=1)
    for i, b in enumerate("ABC"):
        F[f"pitch{b}_max"] = pmax.iloc[:, i]; F[f"pitch{b}_min"] = pmin.iloc[:, i]; F[f"pitch{b}_std"] = pstd.iloc[:, i]
        F[f"pitch{b}_range"] = pmax.iloc[:, i] - pmin.iloc[:, i]
    F["pitch_max_spread"] = pmax.max(axis=1) - pmax.min(axis=1); F["pitch_min_spread"] = pmin.max(axis=1) - pmin.min(axis=1)
    F["pitch_std_spread"] = pstd.max(axis=1) - pstd.min(axis=1); F["pitch_mean_spread"] = pmean.max(axis=1) - pmean.min(axis=1)
    F["pitch_std_mean"] = pstd.mean(axis=1); F["pitch_mean"] = pmean.mean(axis=1)
    mt = pd.concat([m(f"mtemp{a}_max") for a in (1, 2, 3)], axis=1)
    F["mtemp_max"] = mt.max(axis=1); F["mtemp_spread"] = mt.max(axis=1) - mt.min(axis=1); F["hub_temp"] = m("hub_temp_c")
    # ---- rolling 1 h / 6 h / 24 h (operating rows only)
    base = pd.DataFrame(F)
    R = {}
    for w, tag in ((6, "1h"), (36, "6h"), (144, "24h")):
        R[f"inlet_p_min_min_{tag}"] = _roll(base["inlet_p_min"], w, "min")
        R[f"pump_p_min_min_{tag}"] = _roll(base["pump_p_min"], w, "min")
        R[f"inlet_p_drop_max_{tag}"] = _roll(base["inlet_p_drop"], w, "max")
        R[f"inlet_p_std_mean_{tag}"] = _roll(base["inlet_p_std"], w, "mean")
        R[f"pump_p_std_mean_{tag}"] = _roll(base["pump_p_std"], w, "mean")
        R[f"oil_t_max_max_{tag}"] = _roll(base["oil_t_max"], w, "max")
        R[f"cur_max_max_{tag}"] = _roll(base["cur_max_max"], w, "max")
        R[f"cur_max_spread_max_{tag}"] = _roll(base["cur_max_spread"], w, "max")
        R[f"cur_std_spread_mean_{tag}"] = _roll(base["cur_std_spread"], w, "mean")
        R[f"pitch_max_spread_max_{tag}"] = _roll(base["pitch_max_spread"], w, "max")
        R[f"pitch_min_spread_max_{tag}"] = _roll(base["pitch_min_spread"], w, "max")
        R[f"pitch_mean_spread_max_{tag}"] = _roll(base["pitch_mean_spread"], w, "max")
        R[f"pitch_std_spread_mean_{tag}"] = _roll(base["pitch_std_spread"], w, "mean")
        R[f"mtemp_spread_max_{tag}"] = _roll(base["mtemp_spread"], w, "max")
    # dips / time below thresholds (counts over operating rows)
    ref_inlet = base["inlet_p_mean"].rolling(1008, min_periods=144).median().shift(1)
    ref_pump = base["pump_p_mean"].rolling(1008, min_periods=144).median().shift(1)
    dip_in = (base["inlet_p_min"] < 0.6 * ref_inlet).astype("float32").where(base["inlet_p_min"].notna())
    dip_pu = (base["pump_p_min"] < 0.6 * ref_pump).astype("float32").where(base["pump_p_min"].notna())
    low_in = (base["inlet_p_min"] < 0.5).astype("float32").where(base["inlet_p_min"].notna())
    big_spread = (base["pitch_max_spread"] > 1.0).astype("float32").where(base["pitch_max_spread"].notna())
    cur_hi = (base["cur_max_spread"] > 3.0).astype("float32").where(base["cur_max_spread"].notna())
    for w, tag in ((36, "6h"), (144, "24h")):
        R[f"inlet_dip_count_{tag}"] = _roll(dip_in, w, "sum"); R[f"pump_dip_count_{tag}"] = _roll(dip_pu, w, "sum")
        R[f"inlet_below05_frac_{tag}"] = _roll(low_in, w, "mean")
        R[f"pitch_spread_gt1_count_{tag}"] = _roll(big_spread, w, "sum"); R[f"cur_spread_gt3_count_{tag}"] = _roll(cur_hi, w, "sum")
    # variability trend: last 24 h vs last 7 d
    for c in ("inlet_p_std", "pump_p_std", "cur_std_mean", "pitch_std_spread", "pitch_max_spread"):
        R[f"{c}_trend"] = _roll(base[c], 144, "mean") / (_roll(base[c], 1008, "mean") + 1e-3)
    R["inlet_p_mean_rel7d"] = base["inlet_p_mean"] / (ref_inlet + 1e-3)
    R["pump_p_mean_rel7d"] = base["pump_p_mean"] / (ref_pump + 1e-3)
    ctx = pd.DataFrame({"power_kw": d["power_kw"], "wind_speed_ms": d["wind_speed_ms"], "ambient_temp_c": d["ambient_temp_c"],
                        "rotor_speed_rpm": d["rotor_speed_rpm"], "wind_mean_6h": _roll(d["wind_speed_ms"], 36, "mean"),
                        "running_frac_24h": _roll(run.astype("float32"), 144, "mean")})
    return pd.concat([base, pd.DataFrame(R), ctx], axis=1).astype("float32")


def nbm_features(d: pd.DataFrame) -> pd.DataFrame:
    zc = [c for c in d.columns if c.startswith("z_")]
    F = {}
    for c in zc:
        F[f"{c}_6h"] = _roll(d[c], 36, "mean"); F[f"{c}_24h"] = _roll(d[c], 144, "mean")
    return pd.DataFrame(F).astype("float32")


def history_features(ts: pd.Series, tid: str, tr_type: pd.DataFrame, tr_any: pd.DataFrame, stop: pd.Series) -> pd.DataFrame:
    """Only trips that STARTED before t are used (known at t)."""
    t = ts.values.astype("datetime64[ns]")
    F = {}
    for name, tr in (("type", tr_type), ("anyfault", tr_any)):
        s = np.sort(tr.loc[tr["turbine_id"] == tid, "start"].dt.tz_convert(None).values.astype("datetime64[ns]"))
        k = np.searchsorted(s, t, side="left")  # trips strictly before t
        if len(s):
            last = s[np.maximum(k - 1, 0)]
            h = (t - last) / np.timedelta64(1, "h")
            F[f"hours_since_last_{name}_trip"] = np.where(k > 0, np.minimum(h, 24 * 365), 24 * 365).astype("float32")
        else:
            F[f"hours_since_last_{name}_trip"] = np.full(len(t), 24 * 365, np.float32)
        for days in (1, 7, 30, 90, 365):
            k0 = np.searchsorted(s, t - np.timedelta64(days, "D"), side="left")
            F[f"n_{name}_trips_{days}d"] = (k - k0).astype("float32")
    st = stop.astype("float32")
    F["stop_frac_24h"] = st.rolling(144, min_periods=1).mean().to_numpy(np.float32)
    F["stop_frac_7d"] = st.rolling(1008, min_periods=1).mean().to_numpy(np.float32)
    return pd.DataFrame(F, index=ts.index)


def labels(ts: pd.Series, tid: str, tr_type: pd.DataFrame) -> dict:
    t = ts.values.astype("datetime64[ns]")
    s = np.sort(tr_type.loc[tr_type["turbine_id"] == tid, "start"].dt.tz_convert(None).values.astype("datetime64[ns]"))
    k = np.searchsorted(s, t, side="right")  # first trip strictly after t
    nxt = np.where(k < len(s), s[np.minimum(k, len(s) - 1)] if len(s) else t, np.datetime64("NaT"))
    hrs = (nxt - t) / np.timedelta64(1, "h")
    return {H: ((k < len(s)) & (hrs <= H)).astype(np.int8) for H in HORIZONS} | {"hours_to_next": np.where(k < len(s), hrs, np.nan).astype("float32")}

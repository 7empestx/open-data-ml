"""All-years normal-behaviour models (NBM) for gearbox oil-system and pitch faults.

Walk-forward by calendar year: the model scoring year Y is trained on healthy rows of all prior years
(ending 3 days before Jan 1 of Y), and only if that training history covers all 12 calendar months.
Healthy = not in any stop, not within 6 h after a stop, not in a fault, not in the 30 days before a major fault,
QC 0, sensor not stuck, base features present. Scoring (eligible) rows = operating rows with a valid target,
INCLUDING pre-fault periods (only training excludes them).

Signal groups
  gearbox : gear oil temp, gear oil inlet temp, gear oil inlet pressure, gear oil pump pressure,
            main bearing front/rear temps                  (LightGBM NBM residual z)
  pitch   : pitch motor temp axis 1-3, hub temp, mean pitch angle vs wind (LightGBM NBM residual z)
            + direct asymmetries: blade pitch-angle spread, pitch-motor temperature spread (robust z vs training years)
Pressure columns are logged in bar in some periods and in kPa (x100) in others (fleet-wide switch dates);
`normalize_pressure` converts row by row to bar.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import lightgbm as lgb

STEPS_H = 6  # 10-min steps per hour
BASE = ["power_kw", "wind_speed_ms", "ambient_temp_c", "nacelle_temp_c", "rotor_speed_rpm", "generator_speed_rpm"]
WIND_ONLY = ["wind_speed_ms", "ambient_temp_c"]
EXTRA = ["pitch_motor_temp_1_c", "pitch_motor_temp_2_c", "pitch_motor_temp_3_c", "hub_temp_c", "gear_oil_pump_pressure_bar"]
LABEL_COLS = ["timestamp", "turbine_id"] + BASE + [
    "gear_oil_temp_c", "gear_oil_inlet_temp_c", "gear_oil_inlet_pressure_bar", "main_bearing_front_temp_c",
    "main_bearing_rear_temp_c", "pitch_a_deg", "pitch_b_deg", "pitch_c_deg",
    "in_any_stop", "in_fault", "in_major_fault", "pre_fault_30d"]
QC_OF = {c: f"qc_{c}" for c in BASE + ["gear_oil_temp_c", "gear_oil_inlet_temp_c", "gear_oil_inlet_pressure_bar",
                                       "main_bearing_front_temp_c", "main_bearing_rear_temp_c", "pitch_a_deg", "pitch_b_deg", "pitch_c_deg"]}

# target -> (group, feature set, side). side: "pos" = only high residuals alarm; "abs" = both directions
NBM_TARGETS = {
    "gear_oil_temp_c": ("gearbox", "base", "pos"),
    "gear_oil_inlet_temp_c": ("gearbox", "base", "pos"),
    "gear_oil_inlet_pressure_bar": ("gearbox", "base", "abs"),
    "gear_oil_pump_pressure_bar": ("gearbox", "base", "abs"),
    "main_bearing_front_temp_c": ("gearbox", "base", "pos"),
    "main_bearing_rear_temp_c": ("gearbox", "base", "pos"),
    "pitch_motor_temp_1_c": ("pitch", "base", "pos"),
    "pitch_motor_temp_2_c": ("pitch", "base", "pos"),
    "pitch_motor_temp_3_c": ("pitch", "base", "pos"),
    "hub_temp_c": ("pitch", "base", "pos"),
    "pitch_mean_deg": ("pitch", "wind", "abs"),
}
DIRECT = {"pitch_angle_spread": ("pitch", "pos"), "pitch_motor_temp_spread": ("pitch", "pos")}
SUBGROUPS = {
    "gearbox": {"temps": ["gear_oil_temp_c", "gear_oil_inlet_temp_c", "main_bearing_front_temp_c", "main_bearing_rear_temp_c"],
                "pressure": ["gear_oil_inlet_pressure_bar", "gear_oil_pump_pressure_bar"],
                "oil": ["gear_oil_temp_c", "gear_oil_inlet_temp_c", "gear_oil_inlet_pressure_bar", "gear_oil_pump_pressure_bar"],
                "all": [t for t, v in NBM_TARGETS.items() if v[0] == "gearbox"]},
    "pitch": {"motor_temps": ["pitch_motor_temp_1_c", "pitch_motor_temp_2_c", "pitch_motor_temp_3_c", "hub_temp_c"],
              "asymmetry": ["pitch_angle_spread", "pitch_motor_temp_spread"],
              "pitch_curve": ["pitch_mean_deg"],
              "all": [t for t, v in NBM_TARGETS.items() if v[0] == "pitch"] + list(DIRECT)},
}
SIDE = {**{t: v[2] for t, v in NBM_TARGETS.items()}, **{t: v[1] for t, v in DIRECT.items()}}


def normalize_pressure(x: pd.Series, thr: float = 20.0) -> pd.Series:
    """Unit fix, row by row: readings above `thr` are in kPa-like units (x100) and are divided by 100.
    While running, bar readings never exceed ~3.7 (inlet) / ~12 (pump) and kPa readings are never below ~43 / ~211,
    so the split at 20 is unambiguous for operating rows (checked on KEL01, PEN01, PEN13)."""
    return x.where(~(x > thr), x / 100.0)


def load_turbine(labeled_path, extra_path, tid: str) -> pd.DataFrame:
    cols = LABEL_COLS + list(QC_OF.values())
    d = pq.read_table(labeled_path, columns=cols, filters=[("turbine_id", "==", tid)]).to_pandas()
    for c in d.columns:
        if d[c].dtype == "float64":
            d[c] = d[c].astype("float32")
    e = pd.read_parquet(extra_path).drop(columns=["turbine_id"])
    e = e[["timestamp"] + EXTRA]
    d = d.sort_values("timestamp").merge(e, on="timestamp", how="left").reset_index(drop=True)
    for c in ["pitch_motor_temp_1_c", "pitch_motor_temp_2_c", "pitch_motor_temp_3_c"]:
        d[c] = d[c].where((d[c] > -30) & (d[c] < 150))
    d["gear_oil_inlet_pressure_bar"] = normalize_pressure(d["gear_oil_inlet_pressure_bar"]).astype("float32")
    d["gear_oil_pump_pressure_bar"] = normalize_pressure(d["gear_oil_pump_pressure_bar"]).astype("float32")
    p = d[["pitch_a_deg", "pitch_b_deg", "pitch_c_deg"]]
    d["pitch_mean_deg"] = p.mean(axis=1, skipna=False).astype("float32")
    d["pitch_angle_spread"] = (p.max(axis=1, skipna=False) - p.min(axis=1, skipna=False)).astype("float32")
    m = d[["pitch_motor_temp_1_c", "pitch_motor_temp_2_c", "pitch_motor_temp_3_c"]]
    d["pitch_motor_temp_spread"] = (m.max(axis=1, skipna=False) - m.min(axis=1, skipna=False)).astype("float32")
    d["year"] = d["timestamp"].dt.year.astype("int16")
    return d


def add_features(d: pd.DataFrame) -> dict:
    """Causal features (lags / trailing means) on the regular 10-min grid. Returns {'base': cols, 'wind': cols}."""
    new = {}
    for c in BASE:
        s = d[c]
        for L in (1, 3, 6, 18):
            new[f"{c}_lag{L}"] = s.shift(L)
        for w in (6, 36, 144):
            new[f"{c}_rm{w}"] = s.rolling(w, min_periods=max(1, w // 3)).mean()
    new["power_std6"] = d["power_kw"].rolling(6, min_periods=3).std()
    new["wind_std6"] = d["wind_speed_ms"].rolling(6, min_periods=3).std()
    hr = d["timestamp"].dt.hour + d["timestamp"].dt.minute / 60
    new["hour_sin"] = np.sin(2 * np.pi * hr / 24); new["hour_cos"] = np.cos(2 * np.pi * hr / 24)
    doy = d["timestamp"].dt.dayofyear
    new["doy_sin"] = np.sin(2 * np.pi * doy / 365.25); new["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    f = pd.DataFrame(new).astype("float32")
    for c in f.columns:
        d[c] = f[c]
    base = BASE + list(f.columns)
    wind = WIND_ONLY + [c for c in f.columns if c.startswith(("wind_speed_ms_", "ambient_temp_c_"))] + \
        ["wind_std6", "hour_sin", "hour_cos", "doy_sin", "doy_cos"]
    return {"base": base, "wind": wind}


def masks(d: pd.DataFrame, target: str):
    """(eligible, healthy) boolean arrays for one target."""
    stop = d["in_any_stop"].fillna(True).astype(bool)
    recent_stop = stop.astype(float).rolling(6 * STEPS_H, min_periods=1).max().astype(bool)
    y = d[target]
    stuck = y.rolling(18, min_periods=18).std() < 1e-6
    qc_ok = pd.Series(True, index=d.index)
    srcs = {"pitch_mean_deg": ["pitch_a_deg", "pitch_b_deg", "pitch_c_deg"],
            "pitch_angle_spread": ["pitch_a_deg", "pitch_b_deg", "pitch_c_deg"]}.get(target, [target])
    for c in srcs + ["power_kw", "wind_speed_ms"]:
        if c in QC_OF:
            qc_ok &= d[QC_OF[c]].fillna(1) == 0
    base_ok = d[BASE].notna().all(axis=1)
    eligible = (~stop) & (~recent_stop) & y.notna() & (~stuck) & qc_ok & base_ok
    healthy = eligible & ~d["in_fault"].fillna(True).astype(bool) & ~d["in_major_fault"].fillna(True).astype(bool) \
        & ~d["pre_fault_30d"].fillna(True).astype(bool)
    return eligible.to_numpy(), healthy.to_numpy()


def covers_all_months(ts: pd.Series, min_rows: int = 300) -> bool:
    c = ts.dt.month.value_counts()
    return len(c) == 12 and int(c.min()) >= min_rows


def fit_predict(X, y, ts, train_idx, pred_idx, max_train=150_000, seed=0):
    """Time-ordered 80/20 train/val split of the training rows, LightGBM with early stopping.
    Returns predictions for pred_idx, robust residual centre (median) and scale (1.4826*MAD) on validation rows,
    validation MAE and best iteration."""
    tr = train_idx[: int(len(train_idx) * 0.8)]
    va = train_idx[int(len(train_idx) * 0.8):]
    rng = np.random.default_rng(seed)
    if len(tr) > max_train:
        tr = np.sort(rng.choice(tr, max_train, replace=False))
    if len(va) > max_train // 4:
        va = np.sort(rng.choice(va, max_train // 4, replace=False))
    m = lgb.LGBMRegressor(n_estimators=500, learning_rate=0.08, num_leaves=31, min_child_samples=100,
                          subsample=0.8, subsample_freq=1, colsample_bytree=0.8, n_jobs=4, verbose=-1, random_state=seed)
    m.fit(X[tr], y[tr], eval_X=(X[va],), eval_y=(y[va],), callbacks=[lgb.early_stopping(30, verbose=False)])
    rv = y[va] - m.predict(X[va])
    # robust location/scale of validation residuals (residuals are heavy-tailed, sd would shrink every z)
    med = float(np.median(rv)); mad = float(np.median(np.abs(rv - med)) * 1.4826)
    scale = max(mad, float(np.quantile(np.abs(rv - med), 0.9)) / 1.645 * 0.25, 1e-3)
    return m.predict(X[pred_idx]).astype("float32"), med, scale, float(np.mean(np.abs(rv))), m.best_iteration_


def robust_z(x: np.ndarray, train_idx: np.ndarray):
    ref = x[train_idx]
    med = np.nanmedian(ref)
    mad = np.nanmedian(np.abs(ref - med)) * 1.4826
    q = np.nanquantile(ref, 0.9) - med
    scale = max(mad, q / 1.2816, 1e-3)
    return med, scale


def ewma_held(z: pd.Series, halflife_steps: float) -> pd.Series:
    """EWMA over valid (non-NaN) rows only; value held across gaps (stops/ineligible rows)."""
    v = z.dropna()
    if v.empty:
        return pd.Series(np.nan, index=z.index, dtype="float32")
    e = v.ewm(halflife=halflife_steps, adjust=False).mean()
    return e.reindex(z.index).ffill().astype("float32")


def alarm_onsets(ts: np.ndarray, score: np.ndarray, thr: float, merge_gap_h: float = 24, min_dur_h: float = 1) -> np.ndarray:
    """Start times of alarm events (score > thr), runs merged across gaps < merge_gap, kept if >= min_dur."""
    on = np.nan_to_num(score, nan=-np.inf) > thr
    if not on.any():
        return np.array([], dtype="datetime64[ns]")
    d = np.diff(np.concatenate([[0], on.astype(np.int8), [0]]))
    st, en = np.where(d == 1)[0], np.where(d == -1)[0] - 1
    s_t, e_t = ts[st], ts[en]
    gap = np.timedelta64(int(merge_gap_h * 3600), "s")
    ms, me = [s_t[0]], [e_t[0]]
    for a, b in zip(s_t[1:], e_t[1:]):
        if a - me[-1] < gap:
            me[-1] = b
        else:
            ms.append(a); me.append(b)
    ms, me = np.array(ms), np.array(me)
    keep = (me - ms) >= np.timedelta64(int(min_dur_h * 3600) - 600, "s")
    return ms[keep]


def poisson_binomial_sf(k: int, ps) -> float:
    """P(X >= k) for a sum of independent Bernoulli(p_i)."""
    ps = np.clip(np.asarray(ps, float), 0, 1)
    dist = np.zeros(len(ps) + 1); dist[0] = 1.0
    for p in ps:
        dist[1:] = dist[1:] * (1 - p) + dist[:-1] * p
        dist[0] *= (1 - p)
    return float(dist[k:].sum()) if k <= len(ps) else 0.0

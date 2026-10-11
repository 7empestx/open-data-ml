"""Stage 2: normal-behaviour models (NBM) per turbine -> residual z-scores, for whatever signals the fleet has.

Generalises windml.nbm_years (same LightGBM model, robust residual scaling, masks and 3-day embargo):
- Targets: the gearbox/oil, main-bearing and pitch targets of nbm_years when the signal exists, plus a power-curve
  PERFORMANCE target (power from wind + ambient features only), so a fleet with only power/wind/pitch still gets a
  health view. Features use only the base signals the fleet actually has.
- Training scheme, chosen from the turbine's history:
  * walk-forward  (>= 24 months): each calendar year Y is scored by a model trained on healthy rows before
    Jan 1 Y minus 3 days, only if that training history covers all 12 calendar months (as nbm_years).
  * cross-fit     (12 to <24 months, or no calendar year scorable): the record is cut into 6 consecutive blocks; each
    block is scored by a model trained on the other blocks (3-day embargo on both sides). Seasonal cover is
    complete, but a slow change that spans the whole record is partly learned by the model, so drift that predates
    the window is invisible. The report says so.
  * none          (<12 months): no model; the report falls back to data quality, trends and stops.
Output: <work>/health/<TID>.parquet (timestamp, z_<target>, stop) and <TID>_meta.csv (per target and block).
"""
from __future__ import annotations
import gc
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from .. import nbm_years as ny

EMBARGO = pd.Timedelta(days=3)
MIN_TRAIN = 5000
MIN_HISTORY_DAYS = 360          # "12 months minimum" (a few days of slack for a record that starts/ends mid-day)
WALK_FORWARD_DAYS = 720         # >= ~24 months: score each calendar year with a model trained on earlier years only
CROSSFIT_BLOCKS = 6
PERF = "power_kw"
TARGET_GROUP = {**{t: v[0] for t, v in ny.NBM_TARGETS.items()}, **{t: v[0] for t, v in ny.DIRECT.items()}, PERF: "performance"}
SIDE = {**ny.SIDE, PERF: "neg"}  # under-performance only
COMPONENT = {  # report grouping
    "gear_oil_temp_c": "oil", "gear_oil_inlet_temp_c": "oil", "gear_oil_inlet_pressure_bar": "oil", "gear_oil_pump_pressure_bar": "oil",
    "main_bearing_front_temp_c": "main_bearing", "main_bearing_rear_temp_c": "main_bearing",
    "pitch_motor_temp_1_c": "pitch", "pitch_motor_temp_2_c": "pitch", "pitch_motor_temp_3_c": "pitch", "hub_temp_c": "pitch",
    "pitch_mean_deg": "pitch", "pitch_angle_spread": "pitch", "pitch_motor_temp_spread": "pitch", PERF: "performance",
}


def load(path: Path) -> pd.DataFrame:
    d = pd.read_parquet(path).sort_values("timestamp").reset_index(drop=True)
    for c in ("pitch_motor_temp_1_c", "pitch_motor_temp_2_c", "pitch_motor_temp_3_c"):
        if c in d:
            d[c] = d[c].where((d[c] > -30) & (d[c] < 150))
    pa = [c for c in ("pitch_a_deg", "pitch_b_deg", "pitch_c_deg") if c in d and d[c].notna().any()]
    if pa:
        p = d[pa]
        d["pitch_mean_deg"] = p.mean(axis=1, skipna=False).astype("float32")
        if len(pa) == 3:
            d["pitch_angle_spread"] = (p.max(axis=1, skipna=False) - p.min(axis=1, skipna=False)).astype("float32")
    pm = [c for c in ("pitch_motor_temp_1_c", "pitch_motor_temp_2_c", "pitch_motor_temp_3_c") if c in d and d[c].notna().any()]
    if len(pm) == 3:
        m = d[pm]
        d["pitch_motor_temp_spread"] = (m.max(axis=1, skipna=False) - m.min(axis=1, skipna=False)).astype("float32")
    d["year"] = d["timestamp"].dt.year.astype("int16")
    return d


def _present(d, c, min_share=0.2):
    return c in d and float(d[c].notna().mean()) >= min_share


def features(d: pd.DataFrame) -> tuple[dict, list[str]]:
    """Causal features on the 10-min grid from the base signals that exist. Returns ({'base','wind'}: cols, base)."""
    base = [c for c in ny.BASE if _present(d, c, 0.3)]
    new = {}
    for c in base:
        s = d[c]
        for L in (1, 3, 6, 18):
            new[f"{c}_lag{L}"] = s.shift(L)
        for w in (6, 36, 144):
            new[f"{c}_rm{w}"] = s.rolling(w, min_periods=max(1, w // 3)).mean()
    if "power_kw" in base:
        new["power_std6"] = d["power_kw"].rolling(6, min_periods=3).std()
    if "wind_speed_ms" in base:
        new["wind_std6"] = d["wind_speed_ms"].rolling(6, min_periods=3).std()
    hr = d["timestamp"].dt.hour + d["timestamp"].dt.minute / 60
    new["hour_sin"], new["hour_cos"] = np.sin(2 * np.pi * hr / 24), np.cos(2 * np.pi * hr / 24)
    doy = d["timestamp"].dt.dayofyear
    new["doy_sin"], new["doy_cos"] = np.sin(2 * np.pi * doy / 365.25), np.cos(2 * np.pi * doy / 365.25)
    f = pd.DataFrame(new).astype("float32")
    for c in f.columns:
        d[c] = f[c]
    wind_src = [c for c in ny.WIND_ONLY if c in base]
    wind = wind_src + [c for c in f.columns if c.startswith(tuple(f"{w}_" for w in wind_src))] + \
        [c for c in ("wind_std6", "hour_sin", "hour_cos", "doy_sin", "doy_cos") if c in f.columns]
    return {"base": base + list(f.columns), "wind": wind}, base


def targets(d: pd.DataFrame, base: list[str]) -> dict[str, str]:
    """target -> feature set ('base' / 'wind' / 'direct'), only for signals with data."""
    out = {}
    for t, (grp, fs, side) in ny.NBM_TARGETS.items():
        if _present(d, t) and (fs == "wind" or len(base) >= 3):
            out[t] = fs
    for t in ny.DIRECT:
        if _present(d, t):
            out[t] = "direct"
    if _present(d, PERF, 0.3) and "wind_speed_ms" in base:
        out[PERF] = "wind"
    return out


def masks(d: pd.DataFrame, target: str, base: list[str], rated_kw: float):
    """(eligible, healthy) as nbm_years.masks, with the base check on the signals that exist."""
    stop = d["in_any_stop"].fillna(True).astype(bool)
    recent = stop.astype(float).rolling(6 * ny.STEPS_H, min_periods=1).max().astype(bool)
    y = d[target]
    stuck = y.rolling(18, min_periods=18).std() < 1e-6
    qc_ok = pd.Series(True, index=d.index)
    srcs = {"pitch_mean_deg": ["pitch_a_deg", "pitch_b_deg", "pitch_c_deg"],
            "pitch_angle_spread": ["pitch_a_deg", "pitch_b_deg", "pitch_c_deg"]}.get(target, [target])
    for c in srcs + ["power_kw", "wind_speed_ms"]:
        if f"qc_{c}" in d:
            qc_ok &= d[f"qc_{c}"].fillna(1) == 0
    base_ok = d[base].notna().all(axis=1) if base else pd.Series(True, index=d.index)
    eligible = (~stop) & (~recent) & y.notna() & (~stuck) & qc_ok & base_ok
    if target == PERF:   # power curve: producing range only, no curtailment-like caps we can see
        w = d["wind_speed_ms"]
        eligible &= (w > 3.5) & (w < 20) & (d["power_kw"] > 0.01 * rated_kw)
        if "in_stop_curtailment" in d:
            eligible &= ~d["in_stop_curtailment"].fillna(False).astype(bool)
    healthy = eligible & ~d["in_fault"].fillna(True).astype(bool) & ~d["in_major_fault"].fillna(True).astype(bool) \
        & ~d["pre_fault_30d"].fillna(True).astype(bool)
    return eligible.to_numpy(), healthy.to_numpy()


def history_days(d: pd.DataFrame) -> float:
    have = d["row_in_source"] & ~d["row_empty"] if "row_empty" in d else d["row_in_source"]
    t = d.loc[have, "timestamp"]
    return float((t.max() - t.min()) / pd.Timedelta(days=1)) if len(t) else 0.0


def blocks(d: pd.DataFrame, scheme: str, score_years: int | None):
    """[(label, pred_mask, train_window_mask)] for the scheme."""
    ts = d["timestamp"]
    out = []
    if scheme == "walk-forward":
        years = sorted(d["year"].unique())[1:]
        if score_years:
            years = years[-score_years:]
        for Y in years:
            cut = pd.Timestamp(f"{Y}-01-01", tz="UTC") - EMBARGO
            out.append((str(Y), (d["year"] == Y).to_numpy(), (ts < cut).to_numpy()))
    elif scheme == "cross-fit":
        have = d["row_in_source"].to_numpy()
        t0, t1 = ts[have].min(), ts[have].max() + pd.Timedelta("10min")
        edges = [t0 + (t1 - t0) * k / CROSSFIT_BLOCKS for k in range(CROSSFIT_BLOCKS + 1)]
        for k in range(CROSSFIT_BLOCKS):
            a, b = edges[k], edges[k + 1]
            pred = ((ts >= a) & (ts < b)).to_numpy()
            train = ((ts < a - EMBARGO) | (ts >= b + EMBARGO)).to_numpy()
            out.append((f"{a:%Y-%m-%d}..{(b - pd.Timedelta('1s')):%Y-%m-%d}", pred, train))
    return out


def choose_scheme(d: pd.DataFrame, healthy_any: np.ndarray, score_years: int | None) -> str:
    days = history_days(d)
    if days < MIN_HISTORY_DAYS:
        return "none"
    if days < WALK_FORWARD_DAYS:
        return "cross-fit"
    ts = d["timestamp"]
    for lab, pred, train in blocks(d, "walk-forward", score_years):
        tr = healthy_any & train
        if tr.sum() >= MIN_TRAIN and ny.covers_all_months(ts[tr]):
            return "walk-forward"
    return "cross-fit"


def run_turbine(args) -> dict:
    path, out_dir, rated_kw, score_years, fast = args
    path, out_dir = Path(path), Path(out_dir)
    tid = path.stem
    t0 = time.time()
    d = load(path)
    fs, base = features(d)
    tg = targets(d, base)
    res = pd.DataFrame({"timestamp": d["timestamp"]})
    meta = []
    # scheme decided on the performance target if present (most rows), else the first target
    ref_t = PERF if PERF in tg else next(iter(tg), None)
    scheme = "none"
    if ref_t:
        _, h_ref = masks(d, ref_t, base, rated_kw)
        scheme = choose_scheme(d, h_ref, score_years)
    ts = d["timestamp"]
    Xs = {k: d[v].to_numpy(np.float32) for k, v in fs.items()}
    bl = blocks(d, scheme, score_years) if scheme != "none" else []
    for target, fset in tg.items():
        elig, healthy = masks(d, target, base, rated_kw)
        y = d[target].to_numpy(np.float32)
        z = np.full(len(d), np.nan, np.float32)
        for lab, pred, train in bl:
            tr = np.where(healthy & train)[0]
            pr = np.where(pred & elig)[0]
            row = dict(turbine_id=tid, target=target, block=lab, scheme=scheme, n_train=len(tr), n_test=len(pr))
            if len(pr) == 0:
                meta.append({**row, "skipped": "no rows to score"}); continue
            months = ts.iloc[tr].dt.month.nunique() if len(tr) else 0
            need12 = scheme == "walk-forward"
            if len(tr) < MIN_TRAIN or (need12 and not ny.covers_all_months(ts.iloc[tr])) or (not need12 and months < 10):
                meta.append({**row, "skipped": "training rows do not cover the seasons"}); continue
            if fset == "direct":
                med, sc = ny.robust_z(y, tr)
                z[pr] = (y[pr] - med) / sc
                meta.append({**row, "skipped": "", "center": med, "scale": sc}); continue
            X = Xs[fset]
            if fast:
                tr = tr[:: max(1, len(tr) // 20000)]
            pred_y, mu, sd, mae_val, it = ny.fit_predict(X, y, ts, tr, pr, max_train=40_000 if fast else 150_000)
            resid = y[pr] - pred_y
            z[pr] = (resid - mu) / sd
            h = healthy[pr]
            meta.append({**row, "skipped": "", "mae_val": mae_val, "resid_scale_val": sd, "best_iter": it,
                         "mae_test_healthy": float(np.mean(np.abs(resid[h]))) if h.any() else np.nan, "n_test_healthy": int(h.sum())})
        res[f"z_{target}"] = z
    res["stop"] = d["in_any_stop"].fillna(True).astype(bool).to_numpy()
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = out_dir / f"{tid}.parquet.tmp"
    res.to_parquet(tmp, index=False)
    tmp.rename(out_dir / f"{tid}.parquet")
    mcols = ["turbine_id", "target", "block", "scheme", "n_train", "n_test", "skipped"]
    pd.DataFrame(meta, columns=None if meta else mcols).to_csv(out_dir / f"{tid}_meta.csv", index=False)
    info = {"turbine_id": tid, "scheme": scheme, "targets": list(tg), "history_days": round(history_days(d), 1),
            "base_signals": base, "seconds": round(time.time() - t0, 1)}
    del d, Xs, res
    gc.collect()
    return info


def run(work: Path, rated: dict, workers: int = 2, score_years: int | None = None, force: bool = False, fast: bool = False,
        echo=print, only: list[str] | None = None) -> list[dict]:
    work = Path(work)
    out = work / "health"
    out.mkdir(parents=True, exist_ok=True)
    import json
    info_p = out / "health.json"
    old = {r["turbine_id"]: r for r in json.loads(info_p.read_text())} if info_p.exists() and not force else {}
    jobs, results = [], []
    for p in sorted((work / "turbines").glob("*.parquet")):
        tid = p.stem
        if only and tid not in only:
            continue
        z = out / f"{tid}.parquet"
        if tid in old and z.exists() and z.stat().st_mtime >= p.stat().st_mtime and old[tid].get("score_years") == score_years:
            results.append(old[tid]); continue
        jobs.append((str(p), str(out), float(rated.get(tid, 2050.0)), score_years, fast))
    if jobs:
        if workers > 1 and len(jobs) > 1:
            with ProcessPoolExecutor(min(workers, len(jobs))) as ex:
                for r in ex.map(run_turbine, jobs):
                    r["score_years"] = score_years
                    results.append(r)
                    echo(f"  health {r['turbine_id']}: {r['scheme']}, {len(r['targets'])} targets ({r['seconds']} s)")
        else:
            for j in jobs:
                r = run_turbine(j)
                r["score_years"] = score_years
                results.append(r)
                echo(f"  health {r['turbine_id']}: {r['scheme']}, {len(r['targets'])} targets ({r['seconds']} s)")
    keep = {r["turbine_id"] for r in results}
    results += [r for t, r in old.items() if t not in keep]   # turbines outside `only` stay cached
    results = sorted(results, key=lambda r: r["turbine_id"])
    info_p.write_text(json.dumps(results, indent=1))
    return results

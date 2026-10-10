"""Normal-behaviour models (NBM) for drivetrain temperatures + residual anomaly scoring.

Per turbine and per target temperature we learn  T_target = f(operating conditions)  on HEALTHY rows only,
then score residual drift. Everything is time-ordered:

* forward-chaining by calendar month: to score month M the model is trained only on healthy rows that end
  `embargo` before M starts; the last `val_frac` of that (time-ordered) training range is held out for
  early stopping and for the residual mean/std used to standardise residuals (z-scores).
* no autoregressive target lags are used as features (they would absorb the drift we want to detect).

Healthy-training mask: not in any stop / fault / major fault, not in the 30 days before a major-fault
episode, not within `recovery_steps` after any stop, target qc == 0 (no interpolated, missing, invalid or
frozen values), target not flat (stuck) over `stuck_steps`, and all base features present.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

BASE_FEATURES = ["power_kw", "wind_speed_ms", "ambient_temp_c", "nacelle_temp_c", "rotor_speed_rpm", "generator_speed_rpm"]
TARGETS = ["gear_oil_temp_c", "gear_oil_inlet_temp_c", "main_bearing_front_temp_c", "main_bearing_rear_temp_c",
           "rotor_bearing_temp_c", "gen_bearing_front_temp_c", "gen_bearing_rear_temp_c"]
LAGS = (1, 3, 6, 18)          # 10 min, 30 min, 1 h, 3 h
ROLL = (6, 36, 144)           # 1 h, 6 h, 24 h means (thermal inertia)


def add_features(g: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """g: one turbine, sorted by timestamp on a regular 10-min grid."""
    g = g.copy()
    feats = list(BASE_FEATURES)
    new = {}
    for c in ["power_kw", "wind_speed_ms", "ambient_temp_c", "rotor_speed_rpm"]:
        for L in LAGS:
            new[f"{c}_lag{L}"] = g[c].shift(L)
    for c in ["power_kw", "ambient_temp_c", "rotor_speed_rpm"]:
        for w in ROLL:
            new[f"{c}_mean{w}"] = g[c].rolling(w, min_periods=max(1, w // 2)).mean()
    new["power_std6"] = g["power_kw"].rolling(6, min_periods=3).std()
    new["hour_sin"] = np.sin(2 * np.pi * g["timestamp"].dt.hour / 24)
    new["hour_cos"] = np.cos(2 * np.pi * g["timestamp"].dt.hour / 24)
    g = pd.concat([g, pd.DataFrame(new, index=g.index)], axis=1)
    return g, feats + list(new)


def masks(g: pd.DataFrame, target: str, recovery_steps: int = 36, stuck_steps: int = 18) -> tuple[pd.Series, pd.Series]:
    """Returns (healthy_train_mask, eligible_score_mask) for one turbine/target."""
    stop = g["in_any_stop"].astype(bool)
    recent_stop = stop.astype(int).rolling(recovery_steps + 1, min_periods=1).max().astype(bool)
    tgt_ok = (g[f"qc_{target}"] == 0) & g[target].notna()
    stuck = g[target].rolling(stuck_steps, min_periods=stuck_steps).std().fillna(1.0) < 1e-6
    feat_ok = g[BASE_FEATURES].notna().all(axis=1)
    eligible = ~recent_stop & tgt_ok & ~stuck & feat_ok
    healthy = eligible & ~g["in_fault"].astype(bool) & ~g["in_major_fault"].astype(bool) & ~g["pre_fault_30d"].astype(bool)
    return healthy, eligible


def _lgbm(seed=0):
    import lightgbm as lgb
    return lgb.LGBMRegressor(n_estimators=600, learning_rate=0.05, num_leaves=31, min_child_samples=50,
                             subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0,
                             random_state=seed, n_jobs=8, verbose=-1)


def fit_one(X: pd.DataFrame, y: pd.Series, t: pd.Series, val_frac: float = 0.2, kind: str = "lgbm"):
    """Time-ordered split of the training rows into fit/val. Returns (model, val_resid_mu, val_resid_sd, n_fit, n_val)."""
    order = np.argsort(t.to_numpy())
    X, y = X.iloc[order], y.iloc[order]
    n_val = max(int(len(X) * val_frac), 1)
    Xf, yf, Xv, yv = X.iloc[:-n_val], y.iloc[:-n_val], X.iloc[-n_val:], y.iloc[-n_val:]
    if kind == "lgbm":
        import lightgbm as lgb
        m = _lgbm()
        m.fit(Xf, yf, eval_X=(Xv,), eval_y=(yv,), callbacks=[lgb.early_stopping(50, verbose=False)])
    else:
        from sklearn.linear_model import Ridge
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.impute import SimpleImputer
        m = make_pipeline(SimpleImputer(), StandardScaler(), Ridge(alpha=1.0)).fit(Xf, yf)
    rv = yv.to_numpy() - m.predict(Xv)
    return m, float(np.mean(rv)), float(np.std(rv) + 1e-6), len(Xf), len(Xv)


def month_starts(ts: pd.Series) -> list[pd.Timestamp]:
    return list(pd.date_range(ts.min().floor("D").replace(day=1), ts.max(), freq="MS", tz="UTC"))


def forward_chain(g: pd.DataFrame, feats: list[str], targets=TARGETS, embargo_days: int = 3,
                  min_train_days: int = 21, kinds=("lgbm", "ridge")) -> tuple[pd.DataFrame, list[dict]]:
    """Score every month after the first with models trained strictly on earlier healthy data.
    Returns per-row predictions/z for the scored months, and per-fold metadata."""
    out = pd.DataFrame(index=g.index)
    out["timestamp"] = g["timestamp"]
    out["scored_month"] = False
    meta = []
    ms = month_starts(g["timestamp"])
    for M in ms[1:]:
        M_end = M + pd.offsets.MonthBegin(1)
        test = (g["timestamp"] >= M) & (g["timestamp"] < M_end)
        cutoff = M - pd.Timedelta(days=embargo_days)
        out.loc[test, "scored_month"] = True
        for tgt in targets:
            healthy, eligible = masks(g, tgt)
            tr = healthy & (g["timestamp"] < cutoff)
            span_days = (g.loc[tr, "timestamp"].max() - g.loc[tr, "timestamp"].min()).days if tr.any() else 0
            if tr.sum() < 500 or span_days < min_train_days:
                meta.append({"month": M, "target": tgt, "skipped": True, "n_train": int(tr.sum())})
                continue
            for kind in kinds:
                m, mu, sd, nf, nv = fit_one(g.loc[tr, feats], g.loc[tr, tgt], g.loc[tr, "timestamp"], kind=kind)
                pred = m.predict(g.loc[test, feats])
                resid = g.loc[test, tgt].to_numpy() - pred
                sfx = "" if kind == "lgbm" else f"_{kind}"
                out.loc[test, f"pred_{tgt}{sfx}"] = pred
                out.loc[test, f"resid_{tgt}{sfx}"] = resid
                out.loc[test, f"z_{tgt}{sfx}"] = (resid - mu) / sd
                meta.append({"month": M, "target": tgt, "kind": kind, "skipped": False, "n_fit": nf, "n_val": nv,
                             "val_mu": mu, "val_sd": sd, "best_iter": getattr(m, "best_iteration_", None)})
            out.loc[test, f"eligible_{tgt}"] = eligible[test].to_numpy()
            out.loc[test, f"healthy_{tgt}"] = healthy[test].to_numpy()
    return out, meta


# ------------------------------------------------------------------------------------------- scoring
def anomaly_scores(res: pd.DataFrame, targets=TARGETS, halflife: str = "12h", cusum_k: float = 0.5,
                   cusum_decay: float = 0.995) -> pd.DataFrame:
    """Per-row turbine score from residual z-scores (only eligible rows contribute).
    ewma_<t>: time-based EWMA of z (hot = positive). score_ewma = max over targets of ewma_<t>.
    cusum_<t>: one-sided CUSUM S = max(0, decay*S + z - k) on eligible rows. score_cusum = max over targets."""
    s = pd.DataFrame({"timestamp": res["timestamp"]}, index=res.index)
    ew, cu = [], []
    for t in targets:
        if f"z_{t}" not in res:
            continue
        z = res[f"z_{t}"].where(res.get(f"eligible_{t}", True).fillna(False).astype(bool))
        e = z.copy()
        e.index = res["timestamp"]
        e = e.ewm(halflife=pd.Timedelta(halflife), times=res["timestamp"], ignore_na=True).mean()
        e[z.isna().to_numpy() & ~res["scored_month"].to_numpy()] = np.nan
        s[f"ewma_{t}"] = e.to_numpy()
        zz = z.to_numpy()
        S, acc = np.full(len(zz), np.nan), 0.0
        for i, v in enumerate(zz):
            if not np.isnan(v):
                acc = max(0.0, cusum_decay * acc + v - cusum_k)
            S[i] = acc if res["scored_month"].iat[i] else np.nan
        s[f"cusum_{t}"] = S
        ew.append(f"ewma_{t}"); cu.append(f"cusum_{t}")
    s["score_ewma"] = s[ew].max(axis=1)
    s["score_cusum"] = s[cu].max(axis=1)
    s.loc[~res["scored_month"].to_numpy(), ["score_ewma", "score_cusum"]] = np.nan
    s.loc[s["score_ewma"].isna(), "score_cusum"] = np.nan   # no model output yet -> no CUSUM either
    return s


def alarm_events(ts: pd.Series, score: pd.Series, thr: float, merge_gap: str = "24h", min_dur: str = "1h") -> pd.DataFrame:
    """Contiguous runs of score > thr, merged across gaps < merge_gap, keeping runs lasting >= min_dur."""
    on = (score > thr).fillna(False).to_numpy()
    t = ts.to_numpy()
    runs, i = [], 0
    while i < len(on):
        if on[i]:
            j = i
            while j + 1 < len(on) and on[j + 1]:
                j += 1
            runs.append([t[i], t[j]])
            i = j + 1
        else:
            i += 1
    merged = []
    for a, b in runs:
        if merged and (a - merged[-1][1]) < np.timedelta64(pd.Timedelta(merge_gap)):
            merged[-1][1] = b
        else:
            merged.append([a, b])
    ev = pd.DataFrame(merged, columns=["start", "end"])
    if len(ev):
        ev["start"] = pd.to_datetime(ev["start"], utc=True); ev["end"] = pd.to_datetime(ev["end"], utc=True)
        ev = ev[(ev["end"] - ev["start"]) >= pd.Timedelta(min_dur) - pd.Timedelta("10min")].reset_index(drop=True)
    return ev


def episodes(events: pd.DataFrame) -> pd.DataFrame:
    """One row per major-fault episode with start/end, codes and a heatwave flag."""
    mj = events[events["is_major_fault"]].copy()
    g = mj.groupby(["turbine_id", "major_episode"]).agg(start=("start", "min"), end=("end_filled", "max"),
                                                        codes=("code", lambda x: ",".join(sorted({str(v) for v in x}))),
                                                        component=("component", lambda x: ",".join(sorted(set(x)))),
                                                        n_events=("code", "size")).reset_index()
    g["heatwave_20220719"] = (g["codes"] == "3151") & (g["start"].dt.strftime("%Y-%m-%d") == "2022-07-19")
    return g


def evaluate(scores_by_turbine: dict, eps: pd.DataFrame, thr: float, score_col: str, horizon_days: int = 30) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Episode-level detection, per-turbine false alarms and chance baselines.

    detected_active: an alarm is active at any time in [start - H, start]  (counts chronic alarms)
    detected_onset : an alarm event STARTS inside [start - H, start]        (stricter, a real 'new' warning)
    lead_onset_days: start - first alarm onset in the window
    false alarm    : alarm event not active within [episode start - H, episode end] of any episode
    chance_active / chance_onset: share of fault-free days d whose window [d - H, d] contains an
                     active / starting unrelated alarm. This is the hit rate a random 'fault' would get.
    """
    H = pd.Timedelta(days=horizon_days)
    ep_rows, fa_rows = [], []
    for tid, s in scores_by_turbine.items():
        sc = s[s[score_col].notna()]
        if sc.empty:
            continue
        al = alarm_events(sc["timestamp"], sc[score_col], thr)
        e_t = eps[eps["turbine_id"] == tid]
        t0, t1 = sc["timestamp"].min(), sc["timestamp"].max()
        related = np.zeros(len(al), dtype=bool)
        for _, e in e_t.iterrows():
            w0 = e["start"] - H
            related |= ((al["end"] >= w0) & (al["start"] <= e["end"])).to_numpy()
            evaluable = (t0 < e["start"] <= t1 + pd.Timedelta("1D"))
            cover = max(pd.Timedelta(0), e["start"] - max(w0, t0)) if evaluable else pd.Timedelta(0)
            act = al[(al["end"] >= max(w0, t0)) & (al["start"] <= e["start"])]
            ons = al[(al["start"] >= max(w0, t0)) & (al["start"] <= e["start"])]
            lead = (e["start"] - ons["start"].min()).total_seconds() / 86400 if len(ons) else np.nan
            ep_rows.append({"turbine_id": tid, "episode": int(e["major_episode"]), "start": e["start"], "codes": e["codes"],
                            "component": e["component"], "heatwave": bool(e["heatwave_20220719"]),
                            "window_scored_days": round(cover.total_seconds() / 86400, 1),
                            "detected_active": bool(len(act)) and cover > pd.Timedelta(0),
                            "detected_onset": bool(len(ons)) and cover > pd.Timedelta(0),
                            "lead_onset_days": round(lead, 2) if lead == lead else np.nan})
        months = (t1 - t0).total_seconds() / 86400 / 30.44
        fa = int((~related).sum())
        days = pd.date_range(t0.ceil("D") + H, t1.floor("D"), freq="D")
        excl = np.zeros(len(days), dtype=bool)
        for _, e in e_t.iterrows():
            excl |= (days >= e["start"] - H) & (days <= e["end"] + H)
        alu = al[~related]
        ha, ho = [], []
        for d, x in zip(days, excl):
            if x:
                continue
            ha.append(bool(((alu["end"] >= d - H) & (alu["start"] <= d)).any()))
            ho.append(bool(((alu["start"] >= d - H) & (alu["start"] <= d)).any()))
        fa_rows.append({"turbine_id": tid, "scored_months": round(months, 2), "alarm_events": len(al), "false_alarms": fa,
                        "false_alarms_per_month": round(fa / months, 2) if months > 0 else np.nan,
                        "chance_active": round(float(np.mean(ha)), 3) if ha else np.nan,
                        "chance_onset": round(float(np.mean(ho)), 3) if ho else np.nan, "chance_days": len(ha)})
    return pd.DataFrame(ep_rows), pd.DataFrame(fa_rows)


def poisson_binomial_sf(k: int, ps) -> float:
    """P(X >= k) for X = sum of independent Bernoulli(p_i)."""
    dist = np.array([1.0])
    for p in ps:
        dist = np.convolve(dist, [1 - p, p])
    return float(dist[k:].sum())


def seasonal_chance(scores_by_turbine: dict, eps: pd.DataFrame, thr: float, score_col: str, horizon_days: int = 30,
                    halfwidth_days: int = 30) -> pd.DataFrame:
    """Season-matched chance baseline per episode: across ALL turbines of the farm, the share of fault-free days
    d within +-halfwidth of the episode start date whose window [d - H, d] contains an unrelated alarm
    (active / onset). Controls for the residual drift that comes from season (models trained on cooler months)."""
    H = pd.Timedelta(days=horizon_days)
    al_by, excl_by = {}, {}
    for tid, s in scores_by_turbine.items():
        sc = s[s[score_col].notna()]
        if sc.empty:
            continue
        al = alarm_events(sc["timestamp"], sc[score_col], thr)
        e_t = eps[eps["turbine_id"] == tid]
        rel = np.zeros(len(al), dtype=bool)
        for _, e in e_t.iterrows():
            rel |= ((al["end"] >= e["start"] - H) & (al["start"] <= e["end"])).to_numpy()
        al_by[tid] = (al[~rel], sc["timestamp"].min() + H, sc["timestamp"].max(), e_t)
    rows = []
    for _, ep in eps.iterrows():
        ha, ho = [], []
        days = pd.date_range(ep["start"].floor("D") - pd.Timedelta(days=halfwidth_days), ep["start"].floor("D") + pd.Timedelta(days=halfwidth_days), freq="D")
        for tid, (al, t0, t1, e_t) in al_by.items():
            for d in days:
                if d < t0 or d > t1:
                    continue
                if any((d >= e["start"] - H) & (d <= e["end"] + H) for _, e in e_t.iterrows()):
                    continue
                ha.append(bool(((al["end"] >= d - H) & (al["start"] <= d)).any()))
                ho.append(bool(((al["start"] >= d - H) & (al["start"] <= d)).any()))
        rows.append({"turbine_id": ep["turbine_id"], "episode": int(ep["major_episode"]),
                     "chance_active_seasonal": float(np.mean(ha)) if ha else np.nan,
                     "chance_onset_seasonal": float(np.mean(ho)) if ho else np.nan, "seasonal_days": len(ha)})
    return pd.DataFrame(rows)


def fleet_relative(res_by_turbine: dict, targets=TARGETS) -> dict:
    """Subtract, per timestamp and target, the median z across the farm's turbines (eligible rows only).
    Removes common-mode drift (weather, season, model extrapolation) shared by the whole farm."""
    out = {}
    med = {}
    for t in targets:
        cols = []
        for tid, r in res_by_turbine.items():
            if f"z_{t}" in r:
                z = r[f"z_{t}"].where(r[f"eligible_{t}"].fillna(False).astype(bool))
                cols.append(pd.Series(z.to_numpy(), index=r["timestamp"], name=tid))
        med[t] = pd.concat(cols, axis=1).median(axis=1, skipna=True)
    for tid, r in res_by_turbine.items():
        r2 = r.copy()
        for t in targets:
            if f"z_{t}" in r2:
                r2[f"z_{t}"] = r2[f"z_{t}"].to_numpy() - med[t].reindex(r2["timestamp"]).to_numpy()
        out[tid] = r2
    return out

"""Evaluate short-term trip classifiers (predictions from run_trip_models.py).

Row level (hourly operating rows): PR-AUC (average precision) and precision at a fixed alarm budget.
  Budget = one alarm EVENT per turbine-month: in every farm-year the score threshold is set so that the number of alarm
  events (flagged hours merged when < 24 h apart) equals the number of turbine-months (uses scores only, never labels).
  Event precision = share of alarm events with a trip within H hours of one of their flagged hours.
Episode level: trip episodes (trips merged < 24 h apart); detected if any flagged row falls in [start - H, start);
  lead = start - first flagged row in that window. Season-matched chance = share of H-hour windows (all turbines of the
  farm, ending within +-30 days of the episode) that contain a flagged row. Turbine-matched chance = the same on the
  episode's own turbine only (windows overlapping the episode's own window excluded): tests timing, not turbine choice.
Selection on DEV years (2017-2020, pooled farms): best of {sensors, sensors_nbm} (no trip history) and best of
  {sensors_hist, sensors_nbm_hist} (with history), by dev PR-AUC. Then HELD-OUT (2021-2024) reported once.
Primary tests (12 = 2 faults x 3 horizons x 2 comparisons, Bonferroni alpha 0.05/12):
  no-history pick vs season-only model; with-history pick vs history-only model. One-sided block bootstrap over
  turbine-months (1000 resamples) of the PR-AUC difference.
"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from windml import trip_features as tf
from windml import nbm_years as ny

P = ROOT / "data/trip_preds"; REP = ROOT / "reports"; DATA = ROOT / "data/processed/all_years"
FAULTS = ["oil", "pitch"]; HS = [24, 48, 72]
FSETS = ["season", "history", "sensors", "sensors_nbm", "sensors_hist", "sensors_nbm_hist"]
DEV, HELD = [2017, 2018, 2019, 2020], [2021, 2022, 2023, 2024]
NBOOT = 1000


def ap(score, y, w=None):
    """(Weighted) average precision; ties broken by order."""
    o = np.argsort(-score, kind="stable")
    y = y[o].astype(float); w = np.ones_like(y) if w is None else w[o]
    tp = np.cumsum(w * y); fp = np.cumsum(w * (1 - y))
    prec = tp / np.maximum(tp + fp, 1e-12)
    tot = tp[-1] if len(tp) else 0
    return float(np.sum(w * y * prec) / tot) if tot > 0 else np.nan


def _events(tid_codes, ts_ns, flags, gap_h=24):
    """Alarm events = flagged hours merged when < gap_h apart (per turbine). Returns event id per flagged row (-1 otherwise)."""
    idx = np.where(flags)[0]
    eid = np.full(len(flags), -1)
    if len(idx) == 0:
        return eid, 0
    o = idx[np.lexsort((ts_ns[idx], tid_codes[idx]))]
    new = np.ones(len(o), bool)
    new[1:] = (tid_codes[o][1:] != tid_codes[o][:-1]) | ((ts_ns[o][1:] - ts_ns[o][:-1]) > gap_h * 3600e9)
    eid[o] = np.cumsum(new) - 1
    return eid, int(new.sum())


def flag_budget(df, H, per_turbine_month=1.0):
    """Alarm budget = `per_turbine_month` alarm EVENTS per turbine-month. In every farm-year, choose the score threshold
    (from a grid of high quantiles) whose number of alarm events is closest to the budget. Uses scores only, never labels."""
    f = np.zeros(len(df), bool)
    tc = df["turbine_id"].astype("category").cat.codes.to_numpy()
    tsn = df["timestamp"].values.astype("datetime64[ns]").astype(np.int64)
    qs = 1 - np.logspace(-0.5, -5, 80)
    for (farm, yr), idx in df.groupby(["farm", "year"]).groups.items():
        idx = np.asarray(idx)
        s = df["score"].to_numpy()[idx]
        tm = df.iloc[idx].groupby(["turbine_id", df["timestamp"].iloc[idx].dt.month]).size()
        target = per_turbine_month * int((tm >= 100).sum())
        best, bestd = None, np.inf
        for thr in np.unique(np.quantile(s, qs)):
            fl = s >= thr
            _, n = _events(tc[idx], tsn[idx], fl)
            if abs(n - target) < bestd:
                best, bestd = fl, abs(n - target)
        f[idx] = best
    return f


def event_stats(df, flags, H):
    """Alarm events in df: count, true events (a flagged hour of the event has a trip within H h), per turbine-month."""
    tc = df["turbine_id"].astype("category").cat.codes.to_numpy()
    tsn = df["timestamp"].values.astype("datetime64[ns]").astype(np.int64)
    eid, n = _events(tc, tsn, flags)
    if n == 0:
        return 0, 0
    yy = df["y"].to_numpy()
    tp = int(pd.Series(yy[eid >= 0]).groupby(eid[eid >= 0]).max().sum())
    return n, tp


def episodes_all():
    out = {}
    for farm in ["kelmarsh", "penmanshiel"]:
        ev = pd.read_parquet(DATA / f"{farm}_events.parquet")
        for k in FAULTS:
            e = tf.trip_episodes(tf.trips(ev, k)); e["farm"] = farm; out[(farm, k)] = e
    return out


def episode_eval(df, flags, eps, H, years):
    """df rows (hourly, one fault/H/fs), flags bool. Returns per-episode DataFrame."""
    rows = []
    for farm, g in df.groupby("farm"):
        e = eps[(eps.farm == farm) & eps.year.isin(years)]
        if e.empty:
            continue
        t0 = g["timestamp"].min().floor("h"); t1 = g["timestamp"].max().floor("h")
        grid = pd.date_range(t0, t1, freq="h"); n = len(grid)
        tids = sorted(g.turbine_id.unique()); ti = {t: i for i, t in enumerate(tids)}
        F = np.zeros((len(tids), n), np.int32); R = np.zeros((len(tids), n), np.int32)
        gi = grid.get_indexer(g["timestamp"].dt.floor("h"))
        tix = g["turbine_id"].map(ti).to_numpy()
        R[tix, gi] = 1; F[tix, gi] = flags[g.index.to_numpy()].astype(np.int32)
        Fc = np.concatenate([np.zeros((len(tids), 1), np.int32), F.cumsum(1)], 1)
        Rc = np.concatenate([np.zeros((len(tids), 1), np.int32), R.cumsum(1)], 1)
        for _, x in e.iterrows():
            if x.turbine_id not in ti:
                continue
            i = ti[x.turbine_id]
            s = grid.get_indexer([x.start.floor("h")])[0]
            if s < 0:
                continue
            lo = max(0, s - H)
            rows_in = Rc[i, s] - Rc[i, lo]
            evaluable = rows_in >= H / 4  # at least a quarter of the window has operating rows
            fl = np.where(F[i, lo:s] > 0)[0]
            det = evaluable and len(fl) > 0
            lead = float(s - (lo + fl[0])) if det else np.nan
            ends = np.arange(s - 30 * 24, s + 30 * 24 + 1, 24)
            ends = ends[(ends - H >= 0) & (ends <= n)]
            okw = (Rc[:, ends] - Rc[:, ends - H]) >= H / 4
            hit = (Fc[:, ends] - Fc[:, ends - H]) > 0
            chance = float(hit[okw].mean()) if okw.any() else np.nan
            # turbine-matched chance: same turbine, windows ending within +-30 days, not overlapping this episode's window
            own = np.abs(ends - s) >= H
            okt = okw[i] & own
            chance_t = float(hit[i][okt].mean()) if okt.any() else np.nan
            rows.append(dict(farm=farm, turbine_id=x.turbine_id, start=x.start, year=int(x.year), n_trips=int(x.n_trips),
                             evaluable=bool(evaluable), detected=bool(det), lead_h=lead, chance=chance, chance_turbine=chance_t))
    return pd.DataFrame(rows)


def block_ids(df):
    return (df["turbine_id"] + "_" + df["timestamp"].dt.strftime("%Y-%m")).astype("category").cat.codes.to_numpy()


def boot_diff(sa, sb, y, blocks, n=NBOOT, seed=0):
    rng = np.random.default_rng(seed)
    nb = blocks.max() + 1
    oa = np.argsort(-sa, kind="stable"); ob = np.argsort(-sb, kind="stable")
    ya, yb = y[oa].astype(float), y[ob].astype(float); ba, bb = blocks[oa], blocks[ob]
    def wap(yy, w):
        tp = np.cumsum(w * yy); fp = np.cumsum(w * (1 - yy)); tot = tp[-1]
        return np.sum(w * yy * tp / np.maximum(tp + fp, 1e-12)) / tot if tot > 0 else np.nan
    d = []
    for _ in range(n):
        cnt = np.bincount(rng.integers(0, nb, nb), minlength=nb).astype(float)
        d.append(wap(ya, cnt[ba]) - wap(yb, cnt[bb]))
    d = np.array(d)
    return float(np.nanmean(d <= 0)), float(np.nanpercentile(d, 2.5)), float(np.nanpercentile(d, 97.5))


def main():
    EPS = episodes_all()
    rows, ep_rows, sel, tests = [], [], {}, []
    preds = {}
    for fault in FAULTS:
        eps = pd.concat([EPS[(f, fault)] for f in ["kelmarsh", "penmanshiel"]])
        for H in HS:
            for fs in FSETS:
                df = pd.read_parquet(P / f"{fault}_{H}_{fs}.parquet")
                df = df[df.year.between(2017, 2024) & df.score.notna()].reset_index(drop=True)
                flags = flag_budget(df, H)
                preds[(fault, H, fs)] = (df, flags)
                for split, yrs in (("dev", DEV), ("heldout", HELD)):
                    for farm in ["kelmarsh", "penmanshiel", "pooled"]:
                        m = df.year.isin(yrs) & ((df.farm == farm) if farm != "pooled" else True)
                        y = df.loc[m, "y"].to_numpy(); s = df.loc[m, "score"].to_numpy()
                        ee = episode_eval(df[m] if farm != "pooled" else df[m], flags, eps, H, yrs) if True else None
                        ev_ = ee[ee.evaluable] if len(ee) else ee
                        nd = int(ev_.detected.sum()) if len(ev_) else 0
                        rows.append(dict(fault=fault, horizon_h=H, feature_set=fs, split=split, farm=farm, rows=int(m.sum()),
                                         positives=int(y.sum()), prevalence=round(float(y.mean()), 5) if len(y) else np.nan,
                                         pr_auc=round(ap(s, y), 4) if y.sum() else np.nan,
                                         precision_at_budget=round(float(y[flags[m.to_numpy()]].mean()), 4) if flags[m.to_numpy()].any() else np.nan,
                                         **dict(zip(["alarm_events", "true_alarm_events"], event_stats(df[m].reset_index(drop=True), flags[m.to_numpy()], H))),
                                         turbine_months=int((df[m].groupby(["turbine_id", df.loc[m, "timestamp"].dt.to_period("M")]).size() >= 100).sum()),
                                         alarm_share=round(float(flags[m.to_numpy()].mean()), 4),
                                         episodes=len(ev_), detected=nd,
                                         detection_rate=round(nd / len(ev_), 3) if len(ev_) else np.nan,
                                         expected_chance=round(float(ev_.chance.sum()), 2) if len(ev_) else np.nan,
                                         p_episode=round(ny.poisson_binomial_sf(nd, ev_.chance.fillna(0).to_numpy()), 4) if len(ev_) else np.nan,
                                         expected_turbine_matched=round(float(ev_.chance_turbine.fillna(0).sum()), 2) if len(ev_) else np.nan,
                                         p_episode_turbine_matched=round(ny.poisson_binomial_sf(nd, ev_.chance_turbine.fillna(0).to_numpy()), 4) if len(ev_) else np.nan,
                                         median_lead_h=round(float(ev_.loc[ev_.detected, "lead_h"].median()), 1) if nd else np.nan))
                        if split == "heldout" and farm == "pooled":
                            ep_rows.append(ee.assign(fault=fault, horizon_h=H, feature_set=fs))
            print(fault, H, "done", flush=True)
    R = pd.DataFrame(rows); R.to_csv(REP / "trip_metrics.csv", index=False)
    pd.concat(ep_rows).to_csv(REP / "trip_heldout_episodes.csv", index=False)
    # ---- selection on dev (pooled) and primary tests on held-out
    dv = R[(R.split == "dev") & (R.farm == "pooled")].set_index(["fault", "horizon_h", "feature_set"])["pr_auc"]
    for fault in FAULTS:
        for H in HS:
            nohist = max(["sensors", "sensors_nbm"], key=lambda f: dv[(fault, H, f)])
            whist = max(["sensors_hist", "sensors_nbm_hist"], key=lambda f: dv[(fault, H, f)])
            sel[f"{fault}_{H}"] = dict(no_history=nohist, with_history=whist)
            for pick, base in ((nohist, "season"), (whist, "history")):
                da, fa = preds[(fault, H, pick)]; db, fb = preds[(fault, H, base)]
                ma = da.year.isin(HELD).to_numpy(); mb = db.year.isin(HELD).to_numpy()
                a = da[ma].reset_index(drop=True); b = db[mb].reset_index(drop=True)
                # align rows (same rows in both; models trained on the same table)
                key = ["timestamp", "turbine_id"]
                j = a[key + ["y", "score"]].merge(b[key + ["score"]], on=key, suffixes=("_a", "_b"))
                p, lo, hi = boot_diff(j.score_a.to_numpy(), j.score_b.to_numpy(), j.y.to_numpy(), block_ids(j))
                tests.append(dict(fault=fault, horizon_h=H, model=pick, baseline=base, rows=len(j), positives=int(j.y.sum()),
                                  pr_auc_model=round(ap(j.score_a.to_numpy(), j.y.to_numpy()), 4),
                                  pr_auc_baseline=round(ap(j.score_b.to_numpy(), j.y.to_numpy()), 4),
                                  prevalence=round(float(j.y.mean()), 5), diff_ci95_low=round(lo, 4), diff_ci95_high=round(hi, 4),
                                  p_one_sided=round(p, 4), significant_bonferroni_12=bool(p < 0.05 / 12)))
    T = pd.DataFrame(tests); T.to_csv(REP / "trip_primary_tests.csv", index=False)
    (REP / "trip_selected.json").write_text(json.dumps(sel, indent=1))
    print(json.dumps(sel, indent=1)); print(T.to_string())


if __name__ == "__main__":
    main()

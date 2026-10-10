"""Train forward-chained normal-behaviour models and compute residual anomaly scores (no evaluation here).
Outputs: data/nbm/*.parquet (ignored by git, regenerable), reports/nbm_*.csv|json, reports/figures/nbm_*.png.
Evaluation: scripts/eval_nbm.py. Write-up + figures: scripts/report_nbm.py."""
import json, sys, time
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from windml import nbm

P, OUT, REP = ROOT / "data/processed", ROOT / "data/nbm", ROOT / "reports"
OUT.mkdir(exist_ok=True, parents=True)
t00 = time.time()


def run_farm(farm):
    lab = pd.read_parquet(P / f"{farm}_scada_labeled.parquet")
    ev = pd.read_parquet(P / f"{farm}_events.parquet")
    scores, metas, mae_rows = {}, [], []
    for tid, g in lab.groupby("turbine_id", observed=True):
        g = g.sort_values("timestamp").reset_index(drop=True)
        g, feats = nbm.add_features(g)
        res, meta = nbm.forward_chain(g, feats)
        for m in meta:
            m["turbine_id"] = tid
        metas += meta
        sc = nbm.anomaly_scores(res)
        sc["turbine_id"] = tid
        scores[tid] = sc
        keep = res[[c for c in res.columns if c.startswith(("z_", "resid_", "eligible_", "healthy_")) or c in ("timestamp", "scored_month")]].copy()
        keep["turbine_id"] = tid
        pd.concat([keep, sc.drop(columns=["timestamp", "turbine_id"])], axis=1).to_parquet(OUT / f"{farm}_{tid}_nbm.parquet", index=False)
        for t in nbm.TARGETS:
            for sfx, kind in [("", "lgbm"), ("_ridge", "ridge")]:
                c = f"resid_{t}{sfx}"
                if c not in res:
                    continue
                h = res[f"healthy_{t}"].fillna(False).astype(bool) & res[c].notna()
                if h.sum():
                    mae_rows.append({"farm": farm, "turbine_id": tid, "target": t, "model": kind,
                                     "mae_healthy_test": float(res.loc[h, c].abs().mean()), "n": int(h.sum())})
        print(farm, tid, f"{time.time()-t00:.0f}s", flush=True)
    return lab, ev, scores, pd.DataFrame(metas), pd.DataFrame(mae_rows)


results = {}
EP, FA, MAE, META = [], [], [], []
for farm in ["kelmarsh", "penmanshiel"]:
    lab, ev, scores, meta, mae = run_farm(farm)
    eps = nbm.episodes(ev)
    eps = eps[eps["start"] >= lab["timestamp"].min()]  # episodes inside the SCADA window
    eps.to_csv(REP / f"nbm_episodes_{farm}.csv", index=False)
    MAE.append(mae); META.append(meta.assign(farm=farm))
    results[farm] = (lab, ev, scores, eps)

# ------------------------------------------------------------------ cross-farm: train Kelmarsh, apply to Penmanshiel
kel = results["kelmarsh"][0]
frames = []
for tid, g in kel.groupby("turbine_id", observed=True):
    g, feats = nbm.add_features(g.sort_values("timestamp").reset_index(drop=True))
    frames.append(g)
K = pd.concat(frames, ignore_index=True)
pen_lab, pen_ev, _, pen_eps = results["penmanshiel"]
cross_scores, cross_mae = {}, []
models = {}
for t in nbm.TARGETS:
    hmask = pd.concat([nbm.masks(g, t)[0] for _, g in K.groupby("turbine_id", observed=True)]).reindex(K.index)
    models[t] = nbm.fit_one(K.loc[hmask, feats], K.loc[hmask, t], K.loc[hmask, "timestamp"])
for tid, g in pen_lab.groupby("turbine_id", observed=True):
    g, feats = nbm.add_features(g.sort_values("timestamp").reset_index(drop=True))
    res = pd.DataFrame({"timestamp": g["timestamp"]})
    calib_end = nbm.month_starts(g["timestamp"])[1]          # first Penmanshiel month = calibration only
    res["scored_month"] = (g["timestamp"] >= calib_end).to_numpy()
    for t in nbm.TARGETS:
        m = models[t][0]
        healthy, eligible = nbm.masks(g, t)
        r = g[t].to_numpy() - m.predict(g[feats])
        cal = healthy & (g["timestamp"] < calib_end - pd.Timedelta(days=3))
        mu, sd = float(np.nanmean(r[cal])), float(np.nanstd(r[cal]) + 1e-6)
        res[f"resid_{t}"] = r
        res[f"z_{t}"] = (r - mu) / sd
        res[f"eligible_{t}"] = eligible.to_numpy()
        h = healthy.to_numpy() & res["scored_month"].to_numpy() & ~np.isnan(r)
        cross_mae.append({"turbine_id": tid, "target": t, "mae_raw": float(np.abs(r[h]).mean()),
                          "mae_after_offset": float(np.abs(r[h] - mu).mean()), "calib_offset": mu, "n": int(h.sum())})
    sc = nbm.anomaly_scores(res)
    cross_scores[tid] = sc
pd.DataFrame(cross_mae).to_csv(REP / "nbm_crossfarm_mae.csv", index=False)
for tid, sc in cross_scores.items():
    sc.to_parquet(OUT / f"crossfarm_{tid}_scores.parquet", index=False)

pd.concat(MAE).to_csv(REP / "nbm_mae.csv", index=False)
pd.concat(META).to_csv(OUT / "fold_meta.csv", index=False)
print("done", f"{time.time()-t00:.0f}s")

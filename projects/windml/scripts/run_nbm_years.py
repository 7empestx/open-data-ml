"""Train walk-forward-by-year NBMs for every turbine and save residual z-scores.
Output (git-ignored, cached per turbine; rerun skips finished turbines):
  data/nbm_years/<farm>_<TID>.parquet   timestamp, year, z_<target> (float32, NaN = not scored)
  data/nbm_years/<farm>_<TID>_meta.csv  one row per (target, test year): rows, MAE, best_iter, skipped reason
Usage: nohup python scripts/run_nbm_years.py [farm ...] > /workspace/logs/nbm_years.log 2>&1 &"""
import gc, sys, time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np, pandas as pd
import pyarrow.parquet as pq
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from windml import nbm_years as ny

DATA = ROOT / "data/processed/all_years"
OUT = ROOT / "data/nbm_years"; OUT.mkdir(parents=True, exist_ok=True)
EMBARGO = pd.Timedelta(days=3)


def run_turbine(args):
    farm, tid = args
    out = OUT / f"{farm}_{tid}.parquet"
    if out.exists():
        return f"{farm} {tid} cached"
    t0 = time.time()
    d = ny.load_turbine(DATA / f"{farm}_scada_labeled.parquet", DATA / f"{farm}_extra_{tid}.parquet", tid)
    fs = ny.add_features(d)
    ts = d["timestamp"]
    years = sorted(d["year"].unique())
    res = pd.DataFrame({"timestamp": ts, "year": d["year"]})
    meta = []
    Xs = {k: d[v].to_numpy(np.float32) for k, v in fs.items()}
    for target in list(ny.NBM_TARGETS) + list(ny.DIRECT):
        elig, healthy = ny.masks(d, target)
        y = d[target].to_numpy(np.float32)
        z = np.full(len(d), np.nan, np.float32)
        for Y in years[1:]:
            cut = pd.Timestamp(f"{Y}-01-01", tz="UTC") - EMBARGO
            tr = np.where(healthy & (ts < cut).to_numpy())[0]
            pr = np.where(((d["year"] == Y).to_numpy()) & elig)[0]
            row = dict(farm=farm, turbine_id=tid, target=target, test_year=Y, n_train=len(tr), n_test=len(pr))
            if len(pr) == 0:
                meta.append({**row, "skipped": "no test rows"}); continue
            if len(tr) < 5000 or not ny.covers_all_months(ts.iloc[tr]):
                meta.append({**row, "skipped": "training history does not cover all 12 months"}); continue
            if target in ny.DIRECT:
                med, sc = ny.robust_z(y, tr)
                z[pr] = (y[pr] - med) / sc
                meta.append({**row, "skipped": "", "center": med, "scale": sc}); continue
            X = Xs[ny.NBM_TARGETS[target][1]]
            pred, mu, sd, mae_val, it = ny.fit_predict(X, y, ts, tr, pr)
            resid = y[pr] - pred
            z[pr] = (resid - mu) / sd
            h_test = healthy[pr]
            meta.append({**row, "skipped": "", "mae_val": mae_val, "resid_median_val": mu, "resid_scale_val": sd, "best_iter": it,
                         "mae_test_healthy": float(np.mean(np.abs(resid[h_test]))) if h_test.any() else np.nan,
                         "n_test_healthy": int(h_test.sum())})
        res[f"z_{target}"] = z
    res["stop"] = d["in_any_stop"].fillna(True).astype(bool).to_numpy()
    tmp = out.with_suffix(".tmp")
    res.to_parquet(tmp, index=False); tmp.rename(out)
    pd.DataFrame(meta).to_csv(OUT / f"{farm}_{tid}_meta.csv", index=False)
    del d, Xs, res; gc.collect()
    return f"{farm} {tid} done in {time.time() - t0:.0f}s"


if __name__ == "__main__":
    jobs = []
    for farm in (sys.argv[1:] or ["kelmarsh", "penmanshiel"]):
        tids = sorted(pq.read_table(DATA / f"{farm}_scada_labeled.parquet", columns=["turbine_id"]).column(0).unique().to_pylist())
        jobs += [(farm, t) for t in tids]
    with ProcessPoolExecutor(2) as ex:
        for msg in ex.map(run_turbine, jobs):
            print(time.strftime("%H:%M:%S"), msg, flush=True)

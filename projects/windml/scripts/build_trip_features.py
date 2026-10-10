"""Build hourly feature/label tables for short-term trip prediction (cached per turbine, git-ignored).
Output: data/trip/<farm>_<TID>.parquet. Usage: nohup python scripts/build_trip_features.py > logs/trip_features.log 2>&1 &"""
import gc, sys, time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np, pandas as pd, pyarrow.parquet as pq
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from windml import config as cfg  # noqa: E402
from windml import trip_features as tf

DATA = cfg.ALL_YEARS_DIR; NBM = cfg.NBM_YEARS_DIR
OUT = cfg.TRIP_DIR; OUT.mkdir(parents=True, exist_ok=True)


def one(args):
    farm, tid = args
    out = OUT / f"{farm}_{tid}.parquet"
    if out.exists():
        return f"{farm} {tid} cached"
    t0 = time.time()
    ev = pd.read_parquet(DATA / f"{farm}_events.parquet")
    trs = {"oil": tf.trips(ev, "oil"), "pitch": tf.trips(ev, "pitch")}
    anyf = ev[ev["is_fault_stop"]].assign(start=lambda x: pd.to_datetime(x["start"], utc=True))
    d = tf.load(farm, tid, DATA, NBM)
    S = tf.sensor_features(d)
    N = tf.nbm_features(d)
    stop = d["in_any_stop"].fillna(True).astype(bool)
    H = {k: tf.history_features(d["timestamp"], tid, v, anyf, stop).add_prefix(f"hist_{k}_") for k, v in trs.items()}
    keep = (d["timestamp"].dt.minute == 0) & ~stop & ~d["in_fault"].fillna(True).astype(bool)
    ts = d.loc[keep, "timestamp"].reset_index(drop=True)
    out_df = pd.concat([S[keep].reset_index(drop=True), N[keep].reset_index(drop=True)] +
                       [h[keep].reset_index(drop=True) for h in H.values()], axis=1)
    for k, v in trs.items():
        lab = tf.labels(ts, tid, v)
        for h in tf.HORIZONS:
            out_df[f"y_{k}_{h}"] = lab[h]
        out_df[f"hours_to_next_{k}"] = lab["hours_to_next"]
    out_df.insert(0, "timestamp", ts); out_df.insert(1, "turbine_id", tid); out_df.insert(2, "farm", farm)
    out_df["year"] = ts.dt.year.astype("int16")
    doy = ts.dt.dayofyear
    out_df["season_sin"] = np.sin(2 * np.pi * doy / 365.25).astype("float32"); out_df["season_cos"] = np.cos(2 * np.pi * doy / 365.25).astype("float32")
    out_df["is_penmanshiel"] = np.float32(farm == "penmanshiel")
    tmp = out.with_suffix(".tmp"); out_df.to_parquet(tmp, index=False); tmp.rename(out)
    n = len(out_df); del d, S, N, H, out_df; gc.collect()
    return f"{farm} {tid} rows={n} {time.time() - t0:.0f}s"


if __name__ == "__main__":
    jobs = []
    for farm in (sys.argv[1:] or ["kelmarsh", "penmanshiel"]):
        if not (DATA / f"{farm}_scada_labeled.parquet").exists():
            print("skip", farm, "(no labeled parquet; run run_all_years.py first)", flush=True); continue
        tids = sorted(pq.read_table(DATA / f"{farm}_scada_labeled.parquet", columns=["turbine_id"]).column(0).unique().to_pylist())
        jobs += [(farm, t) for t in tids]
    with ProcessPoolExecutor(cfg.workers(3)) as ex:
        for msg in ex.map(one, jobs):
            print(time.strftime("%H:%M:%S"), msg, flush=True)

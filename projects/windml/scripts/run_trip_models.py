"""Walk-forward-by-year LightGBM trip classifiers. For each fault type (oil, pitch), horizon (24/48/72 h) and feature set,
train on all years < Y (rows ending H hours before Jan 1 of Y; negatives subsampled 20%) and predict every row of year Y.
Cached per (fault, horizon, feature set): data/trip_preds/<fault>_<H>_<fs>.parquet (git-ignored).
Usage: nohup python scripts/run_trip_models.py > logs/trip_models.log 2>&1 &"""
import gc, os, sys, time
from pathlib import Path
import numpy as np, pandas as pd
import lightgbm as lgb
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from windml import config as cfg  # noqa: E402
TRIP = cfg.TRIP_DIR; OUT = cfg.TRIP_PREDS_DIR; OUT.mkdir(parents=True, exist_ok=True)
FAULTS = ["oil", "pitch"]; HS = [24, 48, 72]
# Test years: every year after the first one in the data (2017-2024 for the full download).
# A model is only fitted when the training years hold at least MIN_POS positive rows (WINDML_TRIP_MIN_POS, default 10).
MIN_POS = int(os.environ.get("WINDML_TRIP_MIN_POS", "10"))
PARAMS = dict(n_estimators=300, learning_rate=0.05, num_leaves=31, min_child_samples=50, subsample=0.8, subsample_freq=1,
              colsample_bytree=0.7, reg_lambda=1.0, n_jobs=cfg.workers(8), verbose=-1)


def feature_sets(cols, fault):
    meta = {"timestamp", "turbine_id", "farm", "year"}
    y = {c for c in cols if c.startswith(("y_", "hours_to_next_"))}
    hist = [c for c in cols if c.startswith(f"hist_{fault}_")]
    nbm = [c for c in cols if c.startswith("z_")]
    season = ["season_sin", "season_cos", "is_penmanshiel"]
    sensor = [c for c in cols if c not in meta | y and not c.startswith(("hist_", "z_")) and c not in season]
    return {"season": season, "history": hist + ["is_penmanshiel"], "sensors": sensor + season, "sensors_nbm": sensor + nbm + season,
            "sensors_hist": sensor + hist + season, "sensors_nbm_hist": sensor + nbm + hist + season}, sensor, nbm, hist


def main():
    D = pd.concat([pd.read_parquet(f) for f in sorted(TRIP.glob("*.parquet"))], ignore_index=True)
    for c in D.columns:
        if D[c].dtype == "float64":
            D[c] = D[c].astype("float32")
    print("rows", len(D), "cols", D.shape[1], flush=True)
    ts = D["timestamp"]; yr = D["year"].to_numpy()
    YEARS = sorted(int(y) for y in np.unique(yr))[1:]
    for fault in FAULTS:
        FS, sensor, nbm, hist = feature_sets(D.columns, fault)
        print(fault, "n_sensor", len(sensor), "n_nbm", len(nbm), "n_hist", len(hist), flush=True)
        for H in HS:
            y = D[f"y_{fault}_{H}"].to_numpy()
            for fs, cols in FS.items():
                out = OUT / f"{fault}_{H}_{fs}.parquet"
                if out.exists():
                    continue
                t0 = time.time()
                X = D[cols].to_numpy(np.float32)
                score = np.full(len(D), np.nan, np.float32)
                imp = np.zeros(len(cols))
                for Y in YEARS:
                    cut = pd.Timestamp(f"{Y}-01-01", tz="UTC") - pd.Timedelta(hours=H)
                    tr = np.where((ts < cut).to_numpy())[0]
                    rng = np.random.default_rng(Y)
                    neg = tr[y[tr] == 0]; pos = tr[y[tr] == 1]
                    tr = np.sort(np.concatenate([pos, rng.choice(neg, int(len(neg) * 0.2), replace=False)]))
                    te = np.where(yr == Y)[0]
                    if len(pos) < MIN_POS or len(te) == 0:
                        continue
                    m = lgb.LGBMRegressor if False else lgb.LGBMClassifier
                    mdl = m(random_state=Y, **PARAMS).fit(X[tr], y[tr])
                    score[te] = mdl.predict_proba(X[te])[:, 1]
                    imp += mdl.booster_.feature_importance("gain")
                pd.DataFrame({"timestamp": ts, "turbine_id": D["turbine_id"], "farm": D["farm"], "year": D["year"], "y": y, "score": score}).to_parquet(out, index=False)
                pd.DataFrame({"feature": cols, "gain": imp}).sort_values("gain", ascending=False).to_csv(OUT / f"{fault}_{H}_{fs}_importance.csv", index=False)
                print(time.strftime("%H:%M:%S"), fault, H, fs, f"{time.time() - t0:.0f}s", flush=True)
                del X; gc.collect()


if __name__ == "__main__":
    main()

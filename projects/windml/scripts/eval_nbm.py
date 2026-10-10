"""Evaluate saved NBM anomaly scores (data/nbm) against major-fault episodes.
Outputs: reports/nbm_episode_detection.csv, reports/nbm_false_alarms.csv, reports/nbm_summary.csv"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from windml import nbm

D, REP = ROOT / "data/nbm", ROOT / "reports"
THRESH = {"score_ewma": [2.0, 3.0, 4.0], "score_cusum": [25.0, 50.0, 100.0]}
HORIZONS = (7, 30)


def load(farm, setting):
    out = {}
    if setting == "in_farm_fleet_relative":
        res = {f.stem.split("_")[1]: pd.read_parquet(f) for f in sorted(D.glob(f"{farm}_*_nbm.parquet"))}
        for tid, r in nbm.fleet_relative(res).items():
            out[tid] = nbm.anomaly_scores(r)[["timestamp", "score_ewma", "score_cusum"]]
        return out
    pat = f"{farm}_*_nbm.parquet" if setting == "in_farm" else "crossfarm_*_scores.parquet"
    for f in sorted(D.glob(pat)):
        s = pd.read_parquet(f)
        tid = f.stem.split("_")[1]
        s = s[["timestamp", "score_ewma", "score_cusum"]].copy()
        s.loc[s["score_ewma"].isna(), "score_cusum"] = np.nan  # same rule as nbm.anomaly_scores (older saved files)
        out[tid] = s
    return out


EP, FA = [], []
for farm, setting in [("kelmarsh", "in_farm"), ("penmanshiel", "in_farm"), ("penmanshiel", "cross_farm_kel_to_pen"),
                      ("kelmarsh", "in_farm_fleet_relative"), ("penmanshiel", "in_farm_fleet_relative")]:
    scores = load(farm, setting)
    eps = pd.read_csv(REP / f"nbm_episodes_{farm}.csv", parse_dates=["start", "end"])
    for col, ths in THRESH.items():
        for thr in ths:
            for H in HORIZONS:
                ep, fa = nbm.evaluate(scores, eps, thr, col, horizon_days=H)
                sea = nbm.seasonal_chance(scores, eps, thr, col, horizon_days=H)
                ep = ep.merge(sea, on=["turbine_id", "episode"], how="left")
                tag = dict(farm=farm, setting=setting, score=col, thr=thr, horizon=H)
                EP.append(ep.assign(**tag)); FA.append(fa.assign(**tag))
EP, FA = pd.concat(EP, ignore_index=True), pd.concat(FA, ignore_index=True)
EP.to_csv(REP / "nbm_episode_detection.csv", index=False)
FA.to_csv(REP / "nbm_false_alarms.csv", index=False)

keys = ["farm", "setting", "score", "thr", "horizon"]
rows = []
for k, e in EP.groupby(keys):
    f = FA[(FA[keys] == pd.Series(dict(zip(keys, k)))).all(axis=1)]
    ch = f.set_index("turbine_id")
    for subset, ee in [("all", e), ("no_heatwave", e[~e["heatwave"]])]:
        ee = ee[ee["window_scored_days"] > 0]
        if ee.empty:
            continue
        p_act = ee["turbine_id"].map(ch["chance_active"]).astype(float).fillna(0).to_numpy()
        p_on = ee["turbine_id"].map(ch["chance_onset"]).astype(float).fillna(0).to_numpy()
        n_act, n_on = int(ee["detected_active"].sum()), int(ee["detected_onset"].sum())
        ps_act = ee["chance_active_seasonal"].astype(float).fillna(0).to_numpy()
        ps_on = ee["chance_onset_seasonal"].astype(float).fillna(0).to_numpy()
        rows.append(dict(zip(keys, k), subset=subset, episodes=len(ee),
                         detected_active=n_act, expected_by_chance_active=round(p_act.sum(), 2),
                         p_value_active=round(nbm.poisson_binomial_sf(n_act, p_act), 3),
                         detected_onset=n_on, expected_by_chance_onset=round(p_on.sum(), 2),
                         p_value_onset=round(nbm.poisson_binomial_sf(n_on, p_on), 3),
                         expected_seasonal_active=round(ps_act.sum(), 2), p_value_seasonal_active=round(nbm.poisson_binomial_sf(n_act, ps_act), 3),
                         expected_seasonal_onset=round(ps_on.sum(), 2), p_value_seasonal_onset=round(nbm.poisson_binomial_sf(n_on, ps_on), 3),
                         median_lead_onset_days=ee.loc[ee["detected_onset"], "lead_onset_days"].median(),
                         false_alarms_per_turbine_month=round(float(f["false_alarms"].sum() / f["scored_months"].sum()), 2)))
S = pd.DataFrame(rows)
S.to_csv(REP / "nbm_summary.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(S[(S.score == "score_ewma") & (S.thr == 3.0)].to_string(index=False))

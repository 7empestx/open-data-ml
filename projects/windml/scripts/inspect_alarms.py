"""List alarm events (EWMA > thr) for the fleet-relative Kelmarsh setting with the target that drove each one,
and whether it falls in a 30-day pre-fault window. Writes reports/nbm_alarm_events_kelmarsh_fleetrel.csv."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from windml import nbm
THR = float(sys.argv[1]) if len(sys.argv) > 1 else 4.0
NBM = ROOT / "data" / "nbm"
res = {p.stem.split("_")[1]: pd.read_parquet(p) for p in sorted(NBM.glob("kelmarsh_*_nbm.parquet"))}
fr = nbm.fleet_relative(res)
eps = pd.read_csv(ROOT / "reports" / "nbm_episodes_kelmarsh.csv", parse_dates=["start"])
rows = []
for tid, r in fr.items():
    s = nbm.anomaly_scores(r)
    ew = s[[c for c in s.columns if c.startswith("ewma_")]]
    for st, en in nbm.alarm_events(s["timestamp"], s["score_ewma"], THR).itertuples(index=False):
        seg = (s["timestamp"] >= st) & (s["timestamp"] <= en)
        drv = ew[seg].max().sort_values(ascending=False)
        e = eps[(eps.turbine_id == tid) & (eps.start > st) & (eps.start - pd.Timedelta(days=30) <= st)]
        rows.append(dict(turbine_id=tid, alarm_start=st, alarm_end=en, peak=round(float(s.loc[seg, "score_ewma"].max()), 2),
                         driver=drv.index[0].replace("ewma_", ""), driver2=drv.index[1].replace("ewma_", ""),
                         pre_fault_episode=(int(e.major_episode.iloc[0]) if len(e) else None),
                         lead_days=(round((e.start.iloc[0] - st).total_seconds() / 86400, 2) if len(e) else None)))
out = pd.DataFrame(rows).sort_values(["turbine_id", "alarm_start"])
out.to_csv(ROOT / "reports" / "nbm_alarm_events_kelmarsh_fleetrel.csv", index=False)
print(out.to_string())

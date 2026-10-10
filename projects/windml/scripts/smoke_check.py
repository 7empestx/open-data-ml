"""Sanity checks after `make smoke`: every pipeline stage produced non-empty, plausible output.
Exit code 1 on any failure. Usage: python scripts/smoke_check.py [farm ...] (paths from WINDML_* env vars)."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from windml import config as cfg  # noqa: E402

fails = []


def check(ok, msg):
    print(("PASS " if ok else "FAIL ") + msg, flush=True)
    if not ok:
        fails.append(msg)


for farm in (sys.argv[1:] or ["kelmarsh"]):
    lab = cfg.ALL_YEARS_DIR / f"{farm}_scada_labeled.parquet"
    check(lab.exists(), f"{farm}: labeled SCADA {lab.name}")
    if not lab.exists():
        continue
    t = pq.read_table(lab, columns=["timestamp", "turbine_id", "power_kw", "in_any_stop"]).to_pandas()
    tids = sorted(t["turbine_id"].unique())
    years = sorted(t["timestamp"].dt.year.unique())
    check(len(t) > 10_000, f"{farm}: {len(t):,} labeled 10-min rows, turbines {tids}, years {[int(y) for y in years]}")
    check(t["power_kw"].notna().mean() > 0.5, f"{farm}: power_kw present in {t['power_kw'].notna().mean():.0%} of rows")
    ev = pd.read_parquet(cfg.ALL_YEARS_DIR / f"{farm}_events.parquet")
    check(len(ev) > 0, f"{farm}: {len(ev):,} status-log events, {int(ev['is_fault_stop'].sum())} fault stops")
    for tid in tids:
        for kind in ("extra", "stats"):
            p = cfg.ALL_YEARS_DIR / f"{farm}_{kind}_{tid}.parquet"
            check(p.exists() and pq.ParquetFile(p).metadata.num_rows > 0, f"{farm} {tid}: {kind} signals")
        z = cfg.NBM_YEARS_DIR / f"{farm}_{tid}.parquet"
        if z.exists():
            zd = pd.read_parquet(z)
            zc = [c for c in zd.columns if c.startswith("z_")]
            scored = {c: int(np.isfinite(zd[c]).sum()) for c in zc}
            n = sum(v > 0 for v in scored.values())
            check(n > 0, f"{farm} {tid}: NBM scored {n}/{len(zc)} targets for test year(s) {[int(y) for y in sorted(zd.loc[np.isfinite(zd[zc]).any(axis=1), 'year'].unique())]}")
            meta = pd.read_csv(cfg.NBM_YEARS_DIR / f"{farm}_{tid}_meta.csv")
            if "mae_test_healthy" in meta:
                m = meta.dropna(subset=["mae_test_healthy"])
                check(len(m) > 0 and (m["mae_test_healthy"] < 50).all(),
                      f"{farm} {tid}: NBM healthy test MAE median {m['mae_test_healthy'].median():.2f} over {len(m)} models")
        else:
            check(False, f"{farm} {tid}: NBM output {z.name}")
        tr = cfg.TRIP_DIR / f"{farm}_{tid}.parquet"
        check(tr.exists() and pq.ParquetFile(tr).metadata.num_rows > 0, f"{farm} {tid}: hourly trip features")

preds = sorted(cfg.TRIP_PREDS_DIR.glob("*.parquet"))
check(len(preds) == 36, f"trip predictions: {len(preds)}/36 (fault x horizon x feature set) files")
scored = 0
for p in preds:
    d = pd.read_parquet(p, columns=["y", "score"])
    scored += int(d["score"].notna().any())
print(f"INFO {scored}/{len(preds)} trip models had enough positives in the training years to be fitted "
      f"(the smoke subset has few trips; the full data fits all of them)")
print("SMOKE OK" if not fails else f"SMOKE FAILED ({len(fails)} checks)")
sys.exit(1 if fails else 0)

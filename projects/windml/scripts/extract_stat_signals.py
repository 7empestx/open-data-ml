"""Extract 10-min Min/Max/StdDev statistics for oil-system and pitch signals from the Greenbyte CSVs already on the box.
Writes data/processed/all_years/<farm>_stats_<TID>.parquet (one per turbine, cached; git-ignored). No downloads.
Usage: nohup python scripts/extract_stat_signals.py [farm ...] > logs/extract_stats.log 2>&1 &"""
import re, sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from windml import config as cfg  # noqa: E402
from windml import greenbyte as gb
gb.use_all_years()
OUT = cfg.ALL_YEARS_DIR
OUT.mkdir(parents=True, exist_ok=True)
COLS = {"Gear oil inlet pressure (bar)": "inlet_p_mean", "Gear oil inlet pressure, Min (bar)": "inlet_p_min",
        "Gear oil inlet pressure, Max (bar)": "inlet_p_max", "Gear oil inlet pressure, StdDev (bar)": "inlet_p_std",
        "Gear oil pump pressure (bar)": "pump_p_mean", "Gear oil pump pressure, Min (bar)": "pump_p_min",
        "Gear oil pump pressure, Max (bar)": "pump_p_max", "Gear oil pump pressure, StdDev (bar)": "pump_p_std",
        "Gear oil temperature, Max (°C)": "oil_t_max", "Gear oil temperature, Standard deviation (°C)": "oil_t_std",
        "Gear oil inlet temperature, Max (°C)": "inlet_t_max", "Gear oil inlet temperature, StdDev (°C)": "inlet_t_std",
        "Rotor speed, Standard deviation (RPM)": "rotor_rpm_std"}
for ax in (1, 2, 3):
    COLS.update({f"Motor current axis {ax} (A)": f"cur{ax}_mean", f"Motor current axis {ax}, Max (A)": f"cur{ax}_max",
                 f"Motor current axis {ax}, Min (A)": f"cur{ax}_min", f"Motor current axis {ax}, StdDev (A)": f"cur{ax}_std",
                 f"Temperature motor axis {ax}, Max (°C)": f"mtemp{ax}_max"})
for b in "ABC":
    COLS.update({f"Blade angle (pitch position) {b}, Max (°)": f"pitch{b}_max", f"Blade angle (pitch position) {b}, Min (°)": f"pitch{b}_min",
                 f"Blade angle (pitch position) {b}, Standard deviation (°)": f"pitch{b}_std"})


def _tid(p):
    m = re.search(r"_(Kelmarsh|Penmanshiel)_(\d+)_", p.name)
    return f"{m.group(1)[:3].upper()}{int(m.group(2)):02d}"


def one(args):
    farm, tid, files = args
    out = OUT / f"{farm}_stats_{tid}.parquet"
    if out.exists():
        return f"{tid} cached"
    parts = []
    for f in files:
        df, _ = gb.read_turbine(f, usecols=list(COLS))
        df = df.rename(columns=COLS)
        for c in COLS.values():
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float32") if c in df else np.float32(np.nan)
        parts.append(df[["timestamp"] + list(COLS.values())])
    d = pd.concat(parts).drop_duplicates("timestamp", keep="first").sort_values("timestamp")
    tmp = out.with_suffix(".tmp"); d.to_parquet(tmp, index=False); tmp.rename(out)
    return f"{tid} rows={len(d)}"


if __name__ == "__main__":
    for farm in (sys.argv[1:] or ["kelmarsh", "penmanshiel"]):
        by_t = defaultdict(list)
        for f in gb.turbine_files(farm):
            by_t[_tid(f)].append(f)
        with ProcessPoolExecutor(cfg.workers(4)) as ex:
            for msg in ex.map(one, [(farm, t, by_t[t]) for t in sorted(by_t)]):
                print(farm, msg, flush=True)

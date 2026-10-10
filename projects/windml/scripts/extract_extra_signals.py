"""Extract extra raw signals not kept by the cleaning step (pitch motor temperatures/currents, hub temperature,
gear oil pump pressure, per-blade pitch std) from the already-downloaded Greenbyte CSVs.
Writes data/processed/all_years/<farm>_extra_<TID>.parquet (one per turbine; cached = skipped on rerun).
No new downloads: reads $WINDML_RAW_DIR only. Usage: extract_extra_signals.py [farm ...]"""
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
COLS = {
    "Temperature motor axis 1 (°C)": "pitch_motor_temp_1_c", "Temperature motor axis 2 (°C)": "pitch_motor_temp_2_c",
    "Temperature motor axis 3 (°C)": "pitch_motor_temp_3_c", "Motor current axis 1 (A)": "pitch_motor_current_1_a",
    "Motor current axis 2 (A)": "pitch_motor_current_2_a", "Motor current axis 3 (A)": "pitch_motor_current_3_a",
    "Hub temperature (°C)": "hub_temp_c", "Gear oil pump pressure (bar)": "gear_oil_pump_pressure_bar",
    "Blade angle (pitch position) A, Standard deviation (°)": "pitch_a_std_deg",
    "Blade angle (pitch position) B, Standard deviation (°)": "pitch_b_std_deg",
    "Blade angle (pitch position) C, Standard deviation (°)": "pitch_c_std_deg",
}


def _tid(p):
    m = re.search(r"_(Kelmarsh|Penmanshiel)_(\d+)_", p.name)
    return f"{m.group(1)[:3].upper()}{int(m.group(2)):02d}"


def one(args):
    farm, tid, files = args
    out = OUT / f"{farm}_extra_{tid}.parquet"
    if out.exists():
        return f"{tid} cached"
    parts = []
    for f in files:
        df, _ = gb.read_turbine(f, usecols=list(COLS))
        df = df.rename(columns=COLS)
        for c in COLS.values():
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float32") if c in df else np.float32(np.nan)
        parts.append(df[["timestamp", "turbine_id"] + list(COLS.values())])
    d = pd.concat(parts).drop_duplicates("timestamp", keep="first").sort_values("timestamp")
    tmp = out.with_suffix(".tmp")
    d.to_parquet(tmp, index=False); tmp.rename(out)
    return f"{tid} rows={len(d)} files={len(files)}"


if __name__ == "__main__":
    for farm in (sys.argv[1:] or ["kelmarsh", "penmanshiel"]):
        by_t = defaultdict(list)
        for f in gb.turbine_files(farm):
            by_t[_tid(f)].append(f)
        with ProcessPoolExecutor(cfg.workers(4)) as ex:
            for msg in ex.map(one, [(farm, t, by_t[t]) for t in sorted(by_t)]):
                print(farm, msg, flush=True)

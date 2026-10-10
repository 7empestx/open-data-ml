"""Monthly full-load gear-oil pressure and temperature table for the sample condition report.

For each turbine and calendar month (UTC), over 10-min rows with power > 1000 kW and no logged stop:
  inlet  = median gear-oil inlet pressure (bar, unit-corrected with nbm_years.normalize_pressure)
  pump   = median gear-oil pump pressure (bar, unit-corrected)
  oil_t  = median gear-oil sump temperature (°C)
  n      = number of such rows
  oil_t_nan = share of ALL 10-min rows in the month with no gear-oil temperature (data-gap indicator)
Inputs: data/processed/all_years/{farm}_scada_labeled.parquet and {farm}_extra_<TID>.parquet.
Output: reports/condition_report/tables/oil_pressure_monthly.csv (read by condition_scorecard.py and condition_figures.py).
Usage: python scripts/condition_oil_pressure.py [farm ...]"""
import sys
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from windml import config as cfg, nbm_years as ny  # noqa: E402

OUT = cfg.REPORTS_DIR / "condition_report/tables"
COLS = ["timestamp", "turbine_id", "power_kw", "in_any_stop", "gear_oil_inlet_pressure_bar", "gear_oil_temp_c"]


def turbine_months(farm: str, tid: str) -> pd.DataFrame:
    d = pq.read_table(cfg.ALL_YEARS_DIR / f"{farm}_scada_labeled.parquet", columns=COLS,
                      filters=[("turbine_id", "==", tid)]).to_pandas()
    e = pd.read_parquet(cfg.ALL_YEARS_DIR / f"{farm}_extra_{tid}.parquet", columns=["timestamp", "gear_oil_pump_pressure_bar"])
    d = d.merge(e, on="timestamp", how="left")
    d["month"] = d["timestamp"].dt.strftime("%Y-%m")
    nan_share = d.groupby("month")["gear_oil_temp_c"].apply(lambda s: s.isna().mean()).rename("oil_t_nan")
    run = d[(d["power_kw"] > 1000) & ~d["in_any_stop"].fillna(True).astype(bool)].copy()
    run["inlet"] = ny.normalize_pressure(run["gear_oil_inlet_pressure_bar"])
    run["pump"] = ny.normalize_pressure(run["gear_oil_pump_pressure_bar"])
    o = run.groupby("month").agg(inlet=("inlet", "median"), pump=("pump", "median"), oil_t=("gear_oil_temp_c", "median"),
                                 n=("power_kw", "size"))
    o = o.join(nan_share, how="left").reset_index()
    return o.assign(farm=farm, turbine_id=tid)


def main(farms):
    parts = []
    for farm in farms:
        src = cfg.ALL_YEARS_DIR / f"{farm}_scada_labeled.parquet"
        if not src.exists():
            print("skip", farm, "(no labeled parquet)"); continue
        tids = sorted(pq.read_table(src, columns=["turbine_id"]).column(0).unique().to_pylist())
        parts += [turbine_months(farm, t) for t in tids]
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.concat(parts, ignore_index=True)[["month", "inlet", "pump", "oil_t", "n", "oil_t_nan", "farm", "turbine_id"]]
    df.to_csv(OUT / "oil_pressure_monthly.csv", index=False)
    print("wrote", OUT / "oil_pressure_monthly.csv", len(df), "rows")


if __name__ == "__main__":
    main(sys.argv[1:] or ["kelmarsh", "penmanshiel"])

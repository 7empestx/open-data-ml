"""Per-turbine scorecard + RAG flag for the sample condition report. Reads reports/condition_report/tables/*.csv
(written by condition_metrics.py and the oil-pressure monthly table) and writes scorecard.csv.

Assessment window = the turbine's last two full calendar years of data
(Kelmarsh and PEN11-15: 2023-2024; PEN01-10: 2022-2023, their record ends 2023-12).

RAG rules (fixed before looking at the per-turbine results; heuristic, not a calibrated risk score):
  RED   if any: time-based technical availability < 95% (window mean); >= 8 oil-system or >= 8 pitch trip episodes in the
        window; full-load gear-oil pump pressure in the last month of record >= 2.0 bar above the turbine's 2017-2021 baseline;
        abnormal oil state on >= 30% of operating days in the final year.
  AMBER if any: availability < 97%; >= 4 oil or >= 4 pitch episodes; pump pressure rise >= 1.0 bar; abnormal oil state
        >= 10% of days in final year; gear-oil temperature model error in final year >= 1.5x its 2018-2022 mean;
        data missing > 2% in the window.
  GREEN otherwise.
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / "reports/condition_report/tables"


def window(farm, tid):
    return (2023, 2024) if farm == "kelmarsh" or tid >= "PEN11" else (2022, 2023)


def main():
    ty = pd.read_csv(T / "turbine_year.csv")
    ep = pd.read_csv(T / "trip_episodes.csv", parse_dates=["start"])
    tr = pd.read_csv(T / "trips.csv", parse_dates=["start"])
    nb = pd.read_csv(T / "nbm_turbine_year.csv")
    op = pd.read_csv(T / "oil_pressure_monthly.csv")
    dt = pd.read_csv(T / "downtime_by_cause.csv")
    sh = pd.read_csv(T / "sensor_health.csv")
    meta = pd.concat(pd.read_csv(f) for f in (ROOT / "data/nbm_years").glob("*_meta.csv"))
    sw = pd.read_csv(T / "oil_pressure_unit_switches.csv")
    rows = []
    for (farm, tid), g in ty.groupby(["farm", "turbine_id"]):
        y0, y1 = window(farm, tid)
        w = g[g["year"].between(y0, y1)]
        r = {"farm": farm, "turbine_id": tid, "window": f"{y0}-{y1}"}
        r["avail_time"] = w["avail_time"].mean()
        r["avail_energy"] = (w["export_mwh"].sum() / (w["export_mwh"].sum() + w["lost_downtime_mwh"].sum()))
        r["avail_time_2017_2021"] = g[g["year"].between(2017, 2021)]["avail_time"].mean()
        d = dt[(dt["turbine_id"] == tid) & dt["year"].between(y0, y1)]
        r["fault_h_per_yr"] = d[d["cause"].str.startswith("fault")]["hours"].sum() / 2
        r["maint_h_per_yr"] = d[d["cause"] == "maintenance"]["hours"].sum() / 2
        top = d[d["cause"].str.startswith("fault")].groupby("cause")["hours"].sum().sort_values(ascending=False)
        r["top_fault_cause"] = f"{top.index[0].replace('fault: ', '')} ({top.iloc[0]:.0f} h)" if len(top) else ""
        for k in ("oil", "pitch"):
            e = ep[(ep["turbine_id"] == tid) & (ep["kind"] == k)]
            r[f"{k}_ep_window"] = int(e["year"].between(y0, y1).sum())
            r[f"{k}_trips_window"] = int(tr[(tr["turbine_id"] == tid) & (tr["kind"] == k) & tr["start"].dt.year.between(y0, y1)].shape[0])
            r[f"{k}_ep_all"] = len(e)
            # repeat tendency (all years): share of episodes that follow another episode of the same type within 30 days
            s = e["start"].sort_values()
            r[f"{k}_repeat30"] = float((s.diff() <= pd.Timedelta(days=30)).sum() / len(s)) if len(s) > 1 else np.nan
        n = nb[(nb["turbine_id"] == tid)]
        r["oil_abn_final_year"] = n.loc[n["year"] == y1, "oil_days_abs_z_gt3"].max()
        r["oil_abn_window"] = n.loc[n["year"].between(y0, y1), "oil_days_abs_z_gt3"].mean()
        mm = meta[(meta["turbine_id"] == tid) & (meta["target"] == "gear_oil_temp_c")].set_index("test_year")["mae_test_healthy"]
        r["oil_temp_mae_ratio"] = mm.get(y1, np.nan) / mm.loc[2018:2022].mean()
        o = op[op["turbine_id"] == tid].copy(); o["year"] = o["month"].str[:4].astype(int)
        base = o[o["year"].between(2017, 2021)]["pump"].median()
        last = o.dropna(subset=["pump"]).iloc[-1]["pump"]  # last month of record
        r["pump_base_bar"], r["pump_last_month_bar"] = base, last
        r["pump_rise_bar"] = last - base
        r["pump_peak_rise_bar"] = o[o["year"] >= 2018]["pump"].max() - base
        r["inlet_base_bar"] = o[o["year"].between(2017, 2021)]["inlet"].median()
        r["inlet_last_month_bar"] = o.dropna(subset=["inlet"]).iloc[-1]["inlet"]
        r["missing_window"] = (w["missing"] * w["rows"]).sum() / w["rows"].sum()
        r["longest_gap_h_window"] = w["longest_gap_h"].max()
        qc = [c for c in g.columns if c.startswith("qc4_")]
        r["frozen_or_invalid_rows_all"] = int(g[qc].sum().sum())
        r["oil_unit_switches"] = int((sw["turbine_id"] == tid).sum())
        # flags
        red, amb = [], []
        if r["avail_time"] < 0.95: red.append(f"availability {r['avail_time']:.1%}")
        elif r["avail_time"] < 0.97: amb.append(f"availability {r['avail_time']:.1%}")
        for k, lab in (("oil", "oil-system"), ("pitch", "pitch")):
            v = r[f"{k}_ep_window"]
            if v >= 8: red.append(f"{v} {lab} trip episodes")
            elif v >= 4: amb.append(f"{v} {lab} trip episodes")
        pr = r["pump_rise_bar"]
        if pr >= 2.0: red.append(f"pump pressure +{pr:.1f} bar")
        elif pr >= 1.0: amb.append(f"pump pressure +{pr:.1f} bar")
        a = r["oil_abn_final_year"]
        if a >= 0.30: red.append(f"abnormal oil state {a:.0%} of days in {y1}")
        elif a >= 0.10: amb.append(f"abnormal oil state {a:.0%} of days in {y1}")
        if r["oil_temp_mae_ratio"] >= 1.5: amb.append(f"oil-temp model error {r['oil_temp_mae_ratio']:.1f}x baseline")
        if r["missing_window"] > 0.02: amb.append(f"data missing {r['missing_window']:.1%}")
        r["flag"] = "RED" if red else ("AMBER" if amb else "GREEN")
        r["reasons"] = "; ".join(red + amb) if (red or amb) else "no trigger"
        rows.append(r)
    sc = pd.DataFrame(rows)
    sc.to_csv(T / "scorecard.csv", index=False)
    return sc


if __name__ == "__main__":
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 50); pd.set_option("display.max_colwidth", 120)
    sc = main()
    print(sc[["turbine_id", "avail_time", "avail_energy", "fault_h_per_yr", "top_fault_cause", "oil_ep_window", "pitch_ep_window",
              "oil_repeat30", "pitch_repeat30", "oil_abn_final_year", "oil_temp_mae_ratio", "pump_base_bar", "pump_last_month_bar",
              "pump_rise_bar", "pump_peak_rise_bar"]].round(3).to_string())
    print(sc[["turbine_id", "missing_window", "longest_gap_h_window", "frozen_or_invalid_rows_all", 
              "oil_unit_switches", "flag", "reasons"]].to_string())

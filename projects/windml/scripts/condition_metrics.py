"""Compute per-turbine-year condition metrics for the sample condition report (Kelmarsh, Penmanshiel).

Inputs (all already on the box): data/processed/all_years/{farm}_scada_labeled.parquet, {farm}_events.parquet,
{farm}_stats_<TID>.parquet, {farm}_extra_<TID>.parquet, data/nbm_years/{farm}_<TID>.parquet.
Outputs: reports/condition_report/tables/*.csv

Definitions
- Period: 10-min grid rows from the turbine's first to last SCADA row present in the source files.
- Time-based technical availability = 1 - (rows in a fault stop or maintenance stop) / period rows.
  Grid, weather, curtailment and routine stops are not counted against the turbine.
- Energy-based availability = export / (export + lost production to downtime), SCADA counters.
- Downtime by cause: stop events (status log) are clipped to the period and overlap is removed by first-cause
  attribution (a minute already covered by an earlier-starting stop is not counted again).
- Lost production by cause: the SCADA lost_prod_downtime_kwh of each 10-min row goes to the stop active at that row
  (first-cause), or 'no logged stop' if none.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from windml import config as cfg  # noqa: E402
from windml import trip_features as tf  # noqa: E402

D = cfg.ALL_YEARS_DIR
NBM = cfg.NBM_YEARS_DIR
OUT = cfg.REPORTS_DIR / "condition_report/tables"
OUT.mkdir(parents=True, exist_ok=True)
FARMS = {"kelmarsh": [f"KEL0{i}" for i in range(1, 7)],
         "penmanshiel": [f"PEN{i:02d}" for i in range(1, 16) if i != 3]}
FLAGS = ["in_any_stop", "in_fault", "in_stop_maintenance", "in_stop_grid", "in_stop_weather", "in_stop_curtailment", "in_stop_routine"]
FROZEN_CH = ["wind_speed_ms", "ambient_temp_c", "nacelle_temp_c", "gear_oil_temp_c", "main_bearing_front_temp_c",
             "main_bearing_rear_temp_c", "rotor_bearing_temp_c", "gen_bearing_front_temp_c", "gen_bearing_rear_temp_c",
             "converter_inlet_temp_c"]
OIL_Z = ["z_gear_oil_temp_c", "z_gear_oil_inlet_temp_c", "z_gear_oil_inlet_pressure_bar", "z_gear_oil_pump_pressure_bar"]
TEMP_Z = ["z_gear_oil_temp_c", "z_gear_oil_inlet_temp_c", "z_main_bearing_front_temp_c", "z_main_bearing_rear_temp_c"]


PRIO = {"fault": 0, "maintenance": 1, "weather": 2, "grid": 3, "curtailment": 4, "routine": 5}


def first_cause(stops: pd.DataFrame, lo, hi) -> pd.DataFrame:
    s = stops.copy()
    s["a"] = s["start"].clip(lower=lo, upper=hi)
    s["b"] = s["end_filled"].clip(lower=lo, upper=hi)
    s = s[s["b"] > s["a"]].copy()
    # ties at the same start: fault before maintenance before external causes, then the longer stop
    s["prio"] = s["event_class"].map(PRIO).fillna(9)
    s["neg_b"] = -(s["b"].astype("int64"))
    s = s.sort_values(["a", "prio", "neg_b"])
    covered = pd.Timestamp.min.tz_localize("UTC")
    a_eff = []
    for a, b in zip(s["a"], s["b"]):
        a2 = max(a, covered)
        a_eff.append(a2 if a2 < b else b)
        covered = max(covered, b)
    s["a_eff"] = a_eff
    s = s[s["b"] > s["a_eff"]].copy()
    s["hours"] = (s["b"] - s["a_eff"]).dt.total_seconds() / 3600
    return s


def cause_label(df):
    return np.where(df["event_class"] == "fault", "fault: " + df["component"].astype(str), df["event_class"].astype(str))


def main():
    ty_rows, dt_rows, lost_rows, sens_rows, nbm_rows, ev_rows, unit_rows, trip_rows, temp_rows = [], [], [], [], [], [], [], [], []
    for farm, tids in FARMS.items():
        ev = pd.read_parquet(D / f"{farm}_events.parquet")
        ev = ev[ev["turbine_id"].isin(tids)]
        stops = ev[ev["is_stop"]].copy()
        stops["cause"] = cause_label(stops)
        oil = tf.trip_episodes(tf.trips(ev, "oil")); oil["kind"] = "oil"
        pit = tf.trip_episodes(tf.trips(ev, "pitch")); pit["kind"] = "pitch"
        for t in (tf.trips(ev, "oil").assign(kind="oil"), tf.trips(ev, "pitch").assign(kind="pitch")):
            trip_rows.append(t.assign(farm=farm))
        eps = pd.concat([oil, pit]); eps["farm"] = farm
        for tid in tids:
            cols = ["timestamp", "row_in_source", "row_empty", "energy_export_kwh", "lost_prod_downtime_kwh", "ambient_temp_c", "power_kw",
                    "gear_oil_inlet_pressure_bar"] + FLAGS + [f"qc_{c}" for c in FROZEN_CH]
            d = pq.read_table(D / f"{farm}_scada_labeled.parquet", columns=cols, filters=[("turbine_id", "==", tid)]).to_pandas()
            d = d.sort_values("timestamp").reset_index(drop=True)
            src = d.index[d["row_in_source"]]
            d = d.loc[src.min():src.max()].reset_index(drop=True)
            lo, hi = d["timestamp"].iloc[0], d["timestamp"].iloc[-1] + pd.Timedelta(minutes=10)
            d["year"] = d["timestamp"].dt.year
            d["missing"] = (~d["row_in_source"]) | d["row_empty"]
            # per-year time/energy metrics
            g = d.groupby("year")
            ty = g.agg(rows=("timestamp", "size"), missing=("missing", "mean"),
                       export_mwh=("energy_export_kwh", lambda x: x.sum() / 1000),
                       lost_downtime_mwh=("lost_prod_downtime_kwh", lambda x: x.sum() / 1000),
                       **{f"h_{f}": (f, lambda x: x.sum() / 6) for f in FLAGS})
            tech = (d["in_fault"] | d["in_stop_maintenance"])
            ty["h_fault_or_maint"] = tech.groupby(d["year"]).sum() / 6
            ty["avail_time"] = 1 - ty["h_fault_or_maint"] / (ty["rows"] / 6)
            ty["avail_energy"] = ty["export_mwh"] / (ty["export_mwh"] + ty["lost_downtime_mwh"])
            # longest data gap per year
            run = (d["missing"] != d["missing"].shift()).cumsum()
            gaps = d[d["missing"]].groupby(run).agg(year=("year", "first"), n=("year", "size"))
            ty["longest_gap_h"] = gaps.groupby("year")["n"].max().reindex(ty.index).fillna(0) / 6
            for c in FROZEN_CH:
                ty[f"qc4_{c}"] = ((d[f"qc_{c}"] & 4) > 0).groupby(d["year"]).sum()
            ty = ty.reset_index(); ty.insert(0, "turbine_id", tid); ty.insert(0, "farm", farm)
            ty_rows.append(ty)
            # downtime by cause (first-cause)
            st = first_cause(stops[stops["turbine_id"] == tid], lo, hi)
            st["year"] = st["a_eff"].dt.year
            dt_rows.append(st.groupby(["year", "cause"])["hours"].agg(["sum", "size"]).reset_index()
                           .assign(farm=farm, turbine_id=tid))
            # lost production by cause: assign each row to the active first-cause stop
            iv = st.sort_values("a_eff")[["a_eff", "b", "cause"]].rename(columns={"a_eff": "timestamp"})
            iv["timestamp"] = iv["timestamp"].astype(d["timestamp"].dtype); iv["b"] = iv["b"].astype(d["timestamp"].dtype)
            # a row [t, t+10) belongs to a stop if the stop covers its midpoint
            mid = d[["timestamp", "lost_prod_downtime_kwh", "year"]].copy()
            mid["m"] = mid["timestamp"] + pd.Timedelta(minutes=5)
            mm = pd.merge_asof(mid.sort_values("m"), iv.rename(columns={"timestamp": "m0"}).sort_values("m0"),
                               left_on="m", right_on="m0", direction="backward")
            inside = mm["m"] < mm["b"]
            mm["cause"] = np.where(inside, mm["cause"], "no logged stop")
            lost_rows.append(mm.groupby(["year", "cause"])["lost_prod_downtime_kwh"].sum().div(1000).rename("lost_mwh")
                             .reset_index().assign(farm=farm, turbine_id=tid))
            # temperature exposure and fault-stop starts by ambient temperature
            d["tbin"] = pd.cut(d["ambient_temp_c"], [-30, 0, 5, 10, 15, 20, 25, 30, 45])
            expo = d.groupby("tbin", observed=False).size() / 6
            fs = stops[(stops["turbine_id"] == tid) & stops["is_fault_stop"]][["start", "component"]].copy()
            fs["timestamp"] = fs["start"].dt.floor("10min").astype(d["timestamp"].dtype)
            fs = fs.merge(d[["timestamp", "tbin"]], on="timestamp", how="inner")
            cnt = fs.groupby(["tbin", "component"], observed=False).size().rename("n").reset_index()
            temp_rows.append(cnt.merge(expo.rename("hours").reset_index(), on="tbin").assign(farm=farm, turbine_id=tid))
            # oil pressure unit periods: raw 10-min inlet mean on producing rows (power > 500 kW), daily median > 20 = kPa;
            # runs shorter than 7 days are absorbed into the surrounding state before counting switches
            stt = pd.read_parquet(D / f"{farm}_stats_{tid}.parquet", columns=["timestamp", "inlet_p_mean", "pump_p_mean"])
            stt = stt.merge(d[["timestamp", "power_kw"]], on="timestamp", how="left")
            stt = stt[stt["power_kw"] > 500]
            stt["date"] = stt["timestamp"].dt.floor("D")
            day = stt.groupby("date").agg(inlet=("inlet_p_mean", "median"), pump=("pump_p_mean", "median"))
            day["kpa"] = np.where(day["inlet"].notna(), day["inlet"] > 20, np.nan)
            k = day["kpa"].dropna().astype(int)
            for _ in range(3):
                r_ = (k != k.shift()).cumsum(); ln = k.groupby(r_).transform("size")
                k = k.where(ln >= 7).ffill().bfill().astype(int)
            sw = k[(k != k.shift()) & k.shift().notna()]
            unit_rows.append(pd.DataFrame({"farm": farm, "turbine_id": tid, "date": sw.index, "to_kpa": sw.values.astype(bool)}))
            dd = day.reset_index(); dd["year"] = dd["date"].dt.year
            u = dd.groupby("year").agg(days=("kpa", "size"), kpa_days=("kpa", "sum"), nan_days=("inlet", lambda x: x.isna().sum()))
            u = u.reset_index().assign(farm=farm, turbine_id=tid)
            # stuck pressure / pitch channels from stats: 10-min std == 0 over 6 h while values present
            stx = pd.read_parquet(D / f"{farm}_stats_{tid}.parquet", columns=["timestamp", "inlet_p_std", "pitchA_std", "pitchB_std", "pitchC_std",
                                                                                "cur1_mean", "cur2_mean", "cur3_mean"])
            stx["year"] = stx["timestamp"].dt.year
            ex = pd.read_parquet(D / f"{farm}_extra_{tid}.parquet", columns=["timestamp", "pitch_motor_temp_1_c", "pitch_motor_temp_2_c",
                                                                              "pitch_motor_temp_3_c", "hub_temp_c", "gear_oil_pump_pressure_bar"])
            ex["year"] = ex["timestamp"].dt.year
            def frozen_rows(s):
                same = s.diff().eq(0) & s.notna()
                r = (same != same.shift()).cumsum()
                ln = same.groupby(r).transform("size")
                return (same & (ln >= 36))
            for c in ["pitch_motor_temp_1_c", "pitch_motor_temp_2_c", "pitch_motor_temp_3_c", "hub_temp_c"]:
                u[f"frozen_{c}"] = frozen_rows(ex[c]).groupby(ex["year"]).sum().reindex(u["year"]).fillna(0).values
                u[f"nan_{c}"] = ex[c].isna().groupby(ex["year"]).mean().reindex(u["year"]).values
            sens_rows.append(u)
            # NBM residuals (walk-forward z), operating rows only
            zf = NBM / f"{farm}_{tid}.parquet"
            if zf.exists():
                z = pd.read_parquet(zf, columns=["timestamp", "year", "stop"] + sorted(set(OIL_Z + TEMP_Z)))
                z = z[~z["stop"].astype(bool)]
                z["date"] = z["timestamp"].dt.floor("D")
                dm = z.groupby("date")[sorted(set(OIL_Z + TEMP_Z))].median()
                dm = dm[dm.notna().sum(axis=1) > 0]
                dm["year"] = dm.index.year
                rec = []
                for y, gy in dm.groupby("year"):
                    r = {"farm": farm, "turbine_id": tid, "year": y, "days": len(gy)}
                    oz = gy[OIL_Z].abs().max(axis=1)
                    r["oil_days_abs_z_gt3"] = float((oz > 3).mean())
                    for c in sorted(set(OIL_Z + TEMP_Z)):
                        r[f"med_{c}"] = float(gy[c].median())
                    rec.append(r)
                nbm_rows.append(pd.DataFrame(rec))
            print(farm, tid, "done", flush=True)
        ev_rows.append(eps)
        # stop counts by class and fault stops by component, per turbine-year
        stops["year"] = stops["start"].dt.year
        a = stops.groupby(["turbine_id", "year", "event_class"]).size().unstack(fill_value=0).add_prefix("stops_")
        b = stops[stops["is_fault_stop"]].groupby(["turbine_id", "year", "component"]).size().unstack(fill_value=0).add_prefix("fs_")
        c = stops[stops["is_major_fault"]].groupby(["turbine_id", "year"]).size().rename("major_faults")
        a.join(b, how="outer").join(c, how="outer").fillna(0).astype(int).reset_index().assign(farm=farm) \
            .to_csv(OUT / f"stop_counts_{farm}.csv", index=False)
    pd.concat(ty_rows).to_csv(OUT / "turbine_year.csv", index=False)
    pd.concat(dt_rows).rename(columns={"sum": "hours", "size": "n_stops"}).to_csv(OUT / "downtime_by_cause.csv", index=False)
    pd.concat(lost_rows).to_csv(OUT / "lost_by_cause.csv", index=False)
    pd.concat(sens_rows).to_csv(OUT / "sensor_health.csv", index=False)
    pd.concat(nbm_rows).to_csv(OUT / "nbm_turbine_year.csv", index=False)
    pd.concat(ev_rows).to_csv(OUT / "trip_episodes.csv", index=False)
    pd.concat(trip_rows).to_csv(OUT / "trips.csv", index=False)
    pd.concat(unit_rows).to_csv(OUT / "oil_pressure_unit_switches.csv", index=False)
    t = pd.concat(temp_rows); t["tbin"] = t["tbin"].astype(str); t.to_csv(OUT / "faults_by_ambient_temp.csv", index=False)


if __name__ == "__main__":
    main()

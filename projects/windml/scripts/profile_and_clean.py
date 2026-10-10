"""Schema reports (reports/schema_<name>.md) for all in-scope datasets, plus light cleaning to parquet
for the non-wind datasets. Wind cleaning lives in run_wind_clean.py."""
import glob, sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from windml import greenbyte as gb
from windml.profile import profile

RAW = Path("/workspace/industrial-data")
REP, OUT = ROOT / "reports", ROOT / "data/processed"
W = lambda name, txt: (REP / f"schema_{name}.md").write_text(txt)

# ---------------- wind (raw schema, all columns) ----------------
for farm, label in [("kelmarsh", "Kelmarsh 2022"), ("penmanshiel", "Penmanshiel H1 2021 (WT11-15)")]:
    frames, meta = [], None
    for f in gb.turbine_files(farm):
        d, meta = gb.read_turbine(f)
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    W(farm, profile(df, f"{label} SCADA (raw Greenbyte export, all columns)", time_col="timestamp", entity_col="turbine_id", notes=[
        f"Header: turbine type {meta.get('Turbine type')}, 'Time zone: {meta.get('Time zone')}', '{meta.get('Time interval')}'",
        "Timestamps are UTC and mark the START of each 10-minute averaging interval (file runs 00:00 to 23:50 of the last day for an interval ending 00:00 next day).",
        "Units are taken from the column names; signal descriptions in *_WT_dataSignalMapping.* next to the raw data.",
        "Missing/erroneous values are exported as NaN by Greenbyte.",
        "Cleaned output: data/processed/%s_scada_10min.parquet (29 key columns + qc flags); labels in %s_scada_labeled.parquet" % (farm, farm)]))
    print("schema", farm, df.shape)
    del df, frames

# ---------------- NREL PVDAQ sample ----------------
files = sorted(glob.glob(str(RAW / "nrel-pvdaq-sample/system_10_2008/*.csv")))
pv = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
raw_sentinel = {c: int((pv[c] == -99999).sum()) for c in pv.columns if pv[c].dtype != object}
pv = pv.replace(-99999.0, np.nan)
pv["measured_on"] = pd.to_datetime(pv["measured_on"])
pv["timestamp_utc"] = (pv["measured_on"] + pd.Timedelta(hours=7)).dt.tz_localize("UTC")  # MST (UTC-7), no DST
pv = pv.drop_duplicates("measured_on").sort_values("measured_on")
pv.columns = [c.split("__")[0] if "__" in c else c for c in pv.columns]
pv_units = {"ac_current": "A", "ac_power": "W", "ac_voltage": "V", "ambient_temp": "degC", "das_battery_voltage": "V", "das_temp": "degC",
            "dc_pos_current": "A", "dc_pos_voltage": "V", "dc_power": "W", "inverter_temp": "degC", "module_temp_1": "degC",
            "module_temp_2": "degC", "module_temp_3": "degC", "poa_irradiance": "W/m2"}
W("nrel_pvdaq", profile(pv, "NREL PVDAQ system 10 (NREL CIS-1, Golden CO, 1.12 kW), 2008", time_col="timestamp_utc", units=pv_units, notes=[
    f"Source: {len(files)} daily CSVs; -99999 is a missing-value sentinel (replaced with NaN). Sentinel counts: " +
    ", ".join(f"{k.split('__')[0]} {v}" for k, v in raw_sentinel.items() if v),
    "Time zone: measured_on is local STANDARD time (no DST). Verified: irradiance-weighted daily centroid stays at about 12:00 in every month and DST-change days have 96 rows. Converted to UTC with +7 h.",
    "Units: PVDAQ documentation convention (W, V, A, degC, W/m2); not stated in the CSV header. inverter_temp is entirely missing in 2008.",
    "Night-time small negative irradiance/power values are sensor offsets, kept as is."]))
pv.to_parquet(OUT / "nrel_pvdaq_system10_2008.parquet", index=False)

# ---------------- CoMoPI ----------------
cm = {}
for k in ["sensors", "alarm", "warnings"]:
    d = pd.read_csv(RAW / f"comopi-packaging/industrial_dataset_{k}_10m_agg.csv")
    d = d.drop(columns=[c for c in d.columns if c.startswith("Unnamed")])
    d["_time"] = pd.to_datetime(d["_time"], utc=True)
    d = d.drop_duplicates(["_serial", "_time"]).sort_values(["_serial", "_time"])
    cm[k] = d
    d.to_parquet(OUT / f"comopi_{k}_10min.parquet", index=False)
txt = profile(cm["sensors"], "CoMoPI packaging machines: sensors (10-minute averages)", time_col="_time", entity_col="_serial", notes=[
    "Timestamps carry +00:00 (UTC). Sensor names are anonymized (A*/B* = two redundant closure elements); no units published.",
    "Targets per readme: alarms AL_53 and AL_54 indicate faulty component conditions."])
for k in ["alarm", "warnings"]:
    d = cm[k]; cols = [c for c in d.columns if c not in ("_serial", "_time")]
    nz = (d[cols] > 0).sum().sort_values(ascending=False)
    txt += f"\n## {k} file\n\n- Rows {len(d):,}, {len(cols)} counter columns, span {d['_time'].min()} to {d['_time'].max()}, missing {d[cols].isna().mean().mean()*100:.2f}%\n"
    txt += "- Most frequent (rows with count > 0): " + ", ".join(f"{c} {v:,}" for c, v in nz.head(12).items()) + "\n"
    if k == "alarm":
        txt += f"- Target alarms: AL_53 rows>0 = {int((d.get('AL_53', 0) > 0).sum())}, AL_54 rows>0 = {int((d.get('AL_54', 0) > 0).sum())}\n"
W("comopi", txt)

# ---------------- PIADE ----------------
pr = pd.read_csv(RAW / "piade-packaging/raw_data.csv")
pr["interval_start"] = pd.to_datetime(pr["interval_start"], utc=True, format="ISO8601")
for c in ["start", "end"]:
    pr[c + "_utc"] = pd.to_datetime(pr[c], unit="s", utc=True)
pr = pr.drop_duplicates().sort_values(["equipment_ID", "interval_start"])
pr.to_parquet(OUT / "piade_raw_events.parquet", index=False)
ps = pd.read_csv(RAW / "piade-packaging/sequences_1h_data.csv")
ps["interval_start"] = pd.to_datetime(ps["interval_start"], utc=True)
ps = ps.drop_duplicates().sort_values(["equipment_ID", "interval_start"])
ps.to_parquet(OUT / "piade_sequences_1h.parquet", index=False)
txt = profile(pr, "PIADE packaging machines: raw state/alarm intervals", time_col="interval_start", entity_col="equipment_ID", units={"elapsed": "ms", "start": "unix s", "end": "unix s", "pi": "counter (pieces in)", "po": "counter (pieces out)", "speed": "machine speed (unspecified)"}, notes=[
    "Event-based (irregular) intervals: each row is a machine state/alarm interval, not a fixed sampling grid. Times carry +00:00 (UTC).",
    "type values: " + ", ".join(f"{k} {v:,}" for k, v in pr["type"].value_counts().items())])
txt += "\n" + profile(ps, "PIADE sequences_1h (hourly alarm counts per machine)", time_col="interval_start", entity_col="equipment_ID", max_cols=25).replace("# Schema:", "## Schema:")
W("piade", txt)

# ---------------- Beverage bottling ----------------
xl = pd.read_excel(RAW / "beverage-bottling-line/production_raw.xlsx", sheet_name=None)
txt = "# Schema: Beverage bottling line (production_raw.xlsx)\n\n- Time zone: not stated; times are plant-local wall clock. Kept naive (no UTC conversion possible).\n- No raw sensor channels; production, operation time, downtime and efficiency only.\n\n"
for sh, d in xl.items():
    d = d.copy()
    if "date" in d:
        d["date"] = pd.to_datetime(d["date"])
    for c in d.columns:
        if c.endswith("_time") and d[c].dtype == object:
            d[c] = pd.to_timedelta(d[c].astype(str), errors="coerce")
    d.to_parquet(OUT / f"bottling_{sh}.parquet", index=False)
    txt += profile(d, f"sheet {sh}", time_col="date" if "date" in d else None).replace("# Schema:", "## Schema:") + "\n"
W("beverage_bottling", txt)

# ---------------- NASA C-MAPSS ----------------
cols = ["unit", "cycle", "op_setting_1", "op_setting_2", "op_setting_3"] + [f"s{i}" for i in range(1, 22)]
parts = []
for fd in ["FD001", "FD002", "FD003", "FD004"]:
    for split in ["train", "test"]:
        d = pd.read_csv(RAW / f"nasa-cmapss/{split}_{fd}.txt", sep=r"\s+", header=None, names=cols)
        d.insert(0, "subset", fd); d.insert(1, "split", split)
        if split == "train":
            d["rul"] = d.groupby("unit")["cycle"].transform("max") - d["cycle"]
        else:
            r = pd.read_csv(RAW / f"nasa-cmapss/RUL_{fd}.txt", header=None)[0]
            last = d.groupby("unit")["cycle"].transform("max")
            d["rul"] = d["unit"].map(dict(zip(range(1, len(r) + 1), r))) + (last - d["cycle"])
        parts.append(d)
cm_df = pd.concat(parts, ignore_index=True)
cm_df.to_parquet(OUT / "cmapss_all.parquet", index=False)
sens = {"s1": "T2 fan inlet temp (degR)", "s2": "T24 LPC outlet temp (degR)", "s3": "T30 HPC outlet temp (degR)", "s4": "T50 LPT outlet temp (degR)",
        "s5": "P2 fan inlet pressure (psia)", "s6": "P15 bypass duct pressure (psia)", "s7": "P30 HPC outlet pressure (psia)", "s8": "Nf fan speed (rpm)",
        "s9": "Nc core speed (rpm)", "s10": "epr engine pressure ratio", "s11": "Ps30 HPC static pressure (psia)", "s12": "phi fuel flow/Ps30 (pps/psi)",
        "s13": "NRf corrected fan speed (rpm)", "s14": "NRc corrected core speed (rpm)", "s15": "BPR bypass ratio", "s16": "farB burner fuel-air ratio",
        "s17": "htBleed bleed enthalpy", "s18": "Nf_dmd demanded fan speed (rpm)", "s19": "PCNfR_dmd demanded corrected fan speed (rpm)",
        "s20": "W31 HPT coolant bleed (lbm/s)", "s21": "W32 LPT coolant bleed (lbm/s)", "rul": "cycles"}
g = cm_df.groupby(["subset", "split"]).agg(rows=("unit", "size"), units=("unit", "nunique"), max_cycle=("cycle", "max"))
W("nasa_cmapss", profile(cm_df, "NASA C-MAPSS (FD001-FD004, train+test)", entity_col="subset", units=sens, notes=[
    "No wall-clock time: one row per engine operating cycle. Simulated data.",
    "Sensor names/units follow Saxena et al. 2008 (Damage Propagation Modeling.pdf); file columns are unlabeled.",
    "rul added: train = max cycle - cycle; test = RUL_FDxxx value + (last cycle - cycle).",
    "Per subset: " + "; ".join(f"{a}/{b}: {r.rows:,} rows, {r.units} units, max cycle {r.max_cycle}" for (a, b), r in g.iterrows())]))

# ---------------- MetroPT-3 ----------------
mp = pd.read_csv(RAW / "uci-metropt3/MetroPT3(AirCompressor).csv")
mp = mp.drop(columns=[c for c in mp.columns if c.startswith("Unnamed")])
mp["timestamp"] = pd.to_datetime(mp["timestamp"])
dups = int(mp.duplicated("timestamp").sum())
mp = mp.drop_duplicates("timestamp").sort_values("timestamp")
units_mp = {"TP2": "bar", "TP3": "bar", "H1": "bar", "DV_pressure": "bar", "Reservoirs": "bar", "Oil_temperature": "degC", "Motor_current": "A"}
# failure windows from UCI page (air leaks)
fails = [("2020-04-18 00:00", "2020-04-18 23:59"), ("2020-05-29 23:30", "2020-05-30 06:00"), ("2020-06-05 10:00", "2020-06-07 14:30"), ("2020-07-15 14:30", "2020-07-15 19:00")]
mp["in_failure"] = False
for a, b in fails:
    mp.loc[mp["timestamp"].between(a, b), "in_failure"] = True
mp.to_parquet(OUT / "metropt3.parquet", index=False)
W("metropt3", profile(mp, "MetroPT-3 metro train air compressor (APU)", time_col="timestamp", units=units_mp, notes=[
    f"Duplicate timestamps removed: {dups}. Time zone not stated (Porto operator, likely local Portugal time); kept naive.",
    "UCI text mentions both 1 Hz and 0.1 Hz; the file is 0.1 Hz (10 s spacing for 88% of rows) with gaps up to 2 days. Digital signals are 0/1.",
    "in_failure added from the 4 air-leak failure reports on the UCI page (Apr 18, May 29-30, Jun 5-7, Jul 15 2020): %d rows." % int(mp["in_failure"].sum())]))

# ---------------- UCI hydraulic ----------------
H = RAW / "uci-hydraulic-systems"
rates = {"PS1": 100, "PS2": 100, "PS3": 100, "PS4": 100, "PS5": 100, "PS6": 100, "EPS1": 100, "FS1": 10, "FS2": 10,
         "TS1": 1, "TS2": 1, "TS3": 1, "TS4": 1, "VS1": 1, "CE": 1, "CP": 1, "SE": 1}
hu = {"PS": "bar", "EPS1": "W", "FS": "l/min", "TS": "degC", "VS1": "mm/s", "CE": "%", "CP": "kW", "SE": "%"}
prof = pd.read_csv(H / "profile.txt", sep="\t", header=None, names=["cooler_condition_pct", "valve_condition_pct", "pump_leakage", "accumulator_pressure_bar", "stable_flag"])
feat = {"cycle": np.arange(len(prof))}
qlines = []
for s, hz in rates.items():
    a = np.loadtxt(H / f"{s}.txt")
    qlines.append(f"{s}: {a.shape[1]} values/cycle ({hz} Hz x 60 s), unit {next(v for k, v in hu.items() if s.startswith(k))}, NaN {np.isnan(a).sum()}, min {a.min():.4g}, max {a.max():.4g}")
    for fn, f in [("mean", np.mean), ("std", np.std), ("min", np.min), ("max", np.max)]:
        feat[f"{s}_{fn}"] = f(a, axis=1)
hf = pd.concat([pd.DataFrame(feat), prof], axis=1)
hf.to_parquet(OUT / "hydraulic_cycle_features.parquet", index=False)
txt = profile(hf, "UCI hydraulic systems test rig: per-cycle features (mean/std/min/max per sensor) + condition labels", notes=[
    "Raw data: 2,205 load cycles of 60 s each; one text file per sensor, one row per cycle. No wall-clock time.",
    "Labels (profile.txt): cooler 3/20/100 %, valve 100/90/80/73 %, pump leakage 0/1/2, accumulator 130/115/100/90 bar, stable flag 0/1.",
    "Label distribution: " + "; ".join(f"{c}: {prof[c].value_counts().sort_index().to_dict()}" for c in prof.columns)], max_cols=20)
txt += "\n## Raw sensor files\n\n" + "\n".join(f"- {q}" for q in qlines) + "\n"
W("uci_hydraulic", txt)
print("done")

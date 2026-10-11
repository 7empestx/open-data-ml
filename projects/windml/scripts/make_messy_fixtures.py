"""Generate synthetic "messy operator" exports from real Kelmarsh data (KEL01-02, 2022) for the ingest proof.

Writes three differently shaped exports under $WINDML_RAW_DIR/ingest-fixtures/ (raw data: git-ignored, never committed):

  acme/    wide CSV, one file per turbine per MONTH, ';' delimiter, decimal comma, latin-1, 2-line preamble, vendor tag
           names, power in W, ambient in °F, oil pressure in kPa, Europe/London LOCAL time with DST, dd.mm.yyyy,
           timestamps marking the END of the interval; plus a vendor alarm log (German column names, local time).
  longco/  long tag/value parquet, one file per month for both turbines, IEC 61400-25 style tags, epoch-ms UTC,
           asset ids like "WTG-01", oil pressure in kPa.
  xlsx/    one Excel workbook (March 2022), one sheet per turbine ("WEA 1", "WEA 2"), title rows above the header,
           German column names, native Excel datetimes in UTC.

The matching mappings live in mappings/examples/. scripts/ingest_proof.py loads each one and checks it reproduces the
canonical Kelmarsh load (mappings/kelmarsh.yaml) for the same turbines and period.
"""
from __future__ import annotations
import argparse
import copy
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from windml import config as cfg  # noqa: E402
from windml.ingest import loader, mapping  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TURBINES = ("1", "2")


def reference(raw_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Canonical Kelmarsh load restricted to KEL01-02 (the ground truth the fixtures are derived from)."""
    m = mapping.load_mapping(ROOT / "mappings" / "kelmarsh.yaml")
    m = copy.deepcopy(m)
    pat = "[" + "".join(TURBINES) + "]"
    for src in (m["scada"], m["status"]):
        src["files"] = [{**f, "glob": f["glob"].replace("_Kelmarsh_*", f"_Kelmarsh_{pat}_*")} for f in src["files"]]
    df, log = loader.load_scada(m, raw_dir)
    ev = loader.load_status(m, raw_dir, log)
    return df, ev, m


ACME = {  # canonical -> (vendor column, unit transform)
    "power_kw": ("WTG_ActPwr_Mean [W]", lambda x: x * 1000.0),
    "wind_speed_ms": ("WindSpd_Avg [m/s]", None),
    "ambient_temp_c": ("AmbTmp_Avg [°F]", lambda x: x * 9 / 5 + 32),
    "nacelle_temp_c": ("NacTmp_Avg [°F]", lambda x: x * 9 / 5 + 32),
    "rotor_speed_rpm": ("RotorSpd_Avg [rpm]", None),
    "generator_speed_rpm": ("GenSpd_Avg [rpm]", None),
    "gear_oil_temp_c": ("GbxOilSumpTmp_Avg [°F]", lambda x: x * 9 / 5 + 32),
    "gear_oil_inlet_pressure_bar": ("GbxOilInletPrs_Avg [kPa]", lambda x: x * 100.0),
    "main_bearing_front_temp_c": ("MainBrgTmp1_Avg [°F]", lambda x: x * 9 / 5 + 32),
    "pitch_a_deg": ("Blade1PitchAng_Avg [deg]", None),
    "nacelle_position_deg": ("NacDir_Avg [deg]", None),
    "wind_direction_deg": ("WindDirAbs_Avg [deg]", None),
}
ACME_EXTRA = {"WindSpd_Min [m/s]": "wind_speed_ms", "WTG_ActPwr_Max [W]": "power_kw"}  # noise columns a vendor would include

LONG = {"power_kw": "WTUR.W", "wind_speed_ms": "WNAC.WdSpd", "ambient_temp_c": "WNAC.ExTmp", "rotor_speed_rpm": "WROT.RotSpd",
        "gear_oil_temp_c": "WTRM.TrmTmp.GbxOil", "gear_oil_inlet_pressure_bar": "WTRM.GbxOilPres", "pitch_a_deg": "WROT.BlPthAngVal1"}

XLSX = {"power_kw": "Leistung (kW)", "wind_speed_ms": "Windgeschwindigkeit (m/s)", "ambient_temp_c": "Aussentemperatur (°C)",
        "rotor_speed_rpm": "Rotordrehzahl (U/min)", "generator_speed_rpm": "Generatordrehzahl (U/min)",
        "gear_oil_temp_c": "Getriebeoeltemperatur (°C)", "nacelle_position_deg": "Gondelposition (°)"}


def make_acme(df: pd.DataFrame, ev: pd.DataFrame, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    for tid, g in df.groupby("turbine_id"):
        n = int(tid[-2:])
        w = pd.DataFrame()
        local_end = (g["timestamp"] + pd.Timedelta("10min")).dt.tz_convert("Europe/London")
        w["Zeitstempel"] = local_end.dt.strftime("%d.%m.%Y %H:%M")
        for c, (vc, f) in ACME.items():
            w[vc] = f(g[c]) if f else g[c]
        for vc, c in ACME_EXTRA.items():
            w[vc] = g[c] * (1000.0 if "[W]" in vc else 1.0)
        month = local_end.dt.strftime("%Y-%m")
        for mth, part in w.groupby(month.to_numpy()):
            p = out / f"WTG{n:02d}_{mth}.csv"
            with open(p, "w", encoding="latin-1", newline="") as fh:
                fh.write(f"ACME Turbine Export v3.2;Anlage WTG{n:02d}\n")
                fh.write("Zeitzone: lokale Zeit (Europe/London);Intervall 10 min, Zeitstempel = Intervallende\n")
                part.to_csv(fh, sep=";", decimal=",", index=False, float_format="%.6g", na_rep="")
    # alarm log: local time, German headers, vendor wording for the status type
    typ = {"Stop": "Halt", "Warning": "Warnung", "Informational": "Info"}
    for tid, g in ev.groupby("turbine_id"):
        n = int(tid[-2:])
        a = pd.DataFrame({
            "Beginn": g["start"].dt.tz_convert("Europe/London").dt.strftime("%d.%m.%Y %H:%M:%S"),
            "Ende": g["end"].dt.tz_convert("Europe/London").dt.strftime("%d.%m.%Y %H:%M:%S").fillna(""),
            "Typ": g["status"].map(lambda s: typ.get(s, s)),
            "Fehlercode": g["code"],
            "Meldung": g["message"],
            "Kategorie": g["service_category"],
            "IEC": g["iec_category"]})
        a.to_csv(out / f"Alarme_WTG{n:02d}_2022.csv", sep=";", index=False, encoding="latin-1", errors="replace")


def make_long(df: pd.DataFrame, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    d = df.copy()
    d["gear_oil_inlet_pressure_bar"] = d["gear_oil_inlet_pressure_bar"] * 100.0  # kPa
    lg = d.melt(id_vars=["timestamp", "turbine_id"], value_vars=list(LONG), var_name="sig", value_name="value").dropna(subset=["value"])
    lg["tag"] = lg["sig"].map(LONG)
    lg["asset"] = "WTG-" + lg["turbine_id"].str[-2:]
    lg["ts"] = lg["timestamp"].dt.tz_convert(None).astype("datetime64[ms]").astype("int64")  # epoch ms, UTC
    lg = lg[["ts", "asset", "tag", "value"]]
    month = pd.to_datetime(lg["ts"], unit="ms").dt.strftime("%Y-%m")
    for mth, part in lg.groupby(month.to_numpy()):
        part.sample(frac=1.0, random_state=0).to_parquet(out / f"scada_long_{mth}.parquet", index=False)  # unsorted on purpose


def make_xlsx(df: pd.DataFrame, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    d = df[(df["timestamp"] >= "2022-03-01") & (df["timestamp"] < "2022-04-01")]
    p = out / "Betriebsdaten_2022-03.xlsx"
    with pd.ExcelWriter(p, engine="openpyxl") as xw:
        for tid, g in d.groupby("turbine_id"):
            n = int(tid[-2:])
            w = pd.DataFrame({"Datum/Uhrzeit (UTC)": g["timestamp"].dt.tz_convert(None)})
            for c, vc in XLSX.items():
                w[vc] = g[c].to_numpy()
            sheet = f"WEA {n}"
            pd.DataFrame([[f"Betriebsdaten WEA {n}, Maerz 2022"], [""]]).to_excel(xw, sheet_name=sheet, index=False, header=False)
            w.to_excel(xw, sheet_name=sheet, index=False, startrow=2)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--raw-dir", default=str(cfg.RAW_DIR))
    a = ap.parse_args()
    raw = Path(a.raw_dir)
    df, ev, _ = reference(raw)
    out = raw / "ingest-fixtures"
    make_acme(df, ev, out / "acme")
    make_long(df, out / "longco")
    make_xlsx(df, out / "xlsx")
    for sub in ("acme", "longco", "xlsx"):
        files = sorted((out / sub).iterdir())
        print(f"{sub}: {len(files)} files, {sum(f.stat().st_size for f in files) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()

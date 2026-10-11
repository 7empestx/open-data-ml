"""Synthetic HIGH-RES exports upsampled from real Kelmarsh 10-min data (KEL01-02), for the ingest high-res proof.

Each 10-min Kelmarsh record (mean and, where Greenbyte logs it, standard deviation) is expanded into n samples whose
mean and population std equal the 10-min values exactly (Gaussian shape; min/max are NOT the Greenbyte min/max).

  highres/1min/WTG0<n>_2022-03.csv   1-min samples, KEL01-02, March 2022: ';' + decimal comma, Europe/London LOCAL
                                     time (spring DST change on 27 March), stamps at the END of each minute, an operating
                                     state code; 5% of samples dropped at random, a 2-h outage on KEL02, a sparse hour on KEL01
  highres/1s/KEL01_2022-03-10.parquet  1-s samples, KEL01, 10-11 March 2022 (172,800 rows), UTC sample-start stamps
  highres/truth_*.parquet            per-bin truth computed from the samples actually written (for the proof)

Output under $WINDML_RAW_DIR/ingest-fixtures/ (git-ignored). Mappings: mappings/examples/highres_1min.yaml, highres_1s.yaml.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from windml import config as cfg  # noqa: E402

# canonical signal -> Greenbyte std column (None = synthetic small std)
STD = {"power_kw": "Power, Standard deviation (kW)", "wind_speed_ms": "Wind speed, Standard deviation (m/s)",
       "rotor_speed_rpm": "Rotor speed, Standard deviation (RPM)", "pitch_a_deg": "Blade angle (pitch position) A, Standard deviation (°)",
       "nacelle_position_deg": "Nacelle position, Standard deviation (°)", "gear_oil_temp_c": "Gear oil temperature, Standard deviation (°C)",
       "gear_oil_inlet_pressure_bar": None, "ambient_temp_c": None}
VENDOR = {"power_kw": "P_mean [kW]", "wind_speed_ms": "WS_mean [m/s]", "rotor_speed_rpm": "RotSpd [rpm]", "pitch_a_deg": "Pitch1 [deg]",
          "nacelle_position_deg": "NacPos [deg]", "gear_oil_temp_c": "GbxOilT [degC]", "gear_oil_inlet_pressure_bar": "GbxOilP [bar]",
          "ambient_temp_c": "AmbT [degC]"}


def _ref(raw: Path, t0: str, t1: str) -> pd.DataFrame:
    from make_messy_fixtures import reference
    df, _, _ = reference(raw)
    df = df[(df["timestamp"] >= pd.Timestamp(t0, tz="UTC")) & (df["timestamp"] < pd.Timestamp(t1, tz="UTC"))]
    parts = []
    for n, tid in ((1, "KEL01"), (2, "KEL02")):
        f = sorted((raw / "kelmarsh-wind-scada" / "scada_2022").glob(f"Turbine_Data_Kelmarsh_{n}_*.csv"))[0]
        cols = ["# Date and time"] + [c for c in STD.values() if c]
        s = pd.read_csv(f, skiprows=9, usecols=cols)
        s["timestamp"] = pd.to_datetime(s.pop("# Date and time")).dt.tz_localize("UTC")
        s = s.rename(columns={v: f"{k}__std" for k, v in STD.items() if v})
        parts.append(df[df["turbine_id"] == tid].merge(s, on="timestamp", how="left"))
    out = pd.concat(parts, ignore_index=True)
    out["gear_oil_inlet_pressure_bar__std"] = (0.02 * out["gear_oil_inlet_pressure_bar"]).abs()
    out["ambient_temp_c__std"] = 0.0
    return out


def expand(ref: pd.DataFrame, step: str, seed: int = 0) -> pd.DataFrame:
    """n samples per 10-min record with exactly the record's mean and population std."""
    n = int(pd.Timedelta("10min") / pd.Timedelta(step))
    rng = np.random.default_rng(seed)
    out = {"turbine_id": np.repeat(ref["turbine_id"].to_numpy(), n),
           "t_start": (np.repeat(ref["timestamp"].dt.tz_convert(None).to_numpy("datetime64[ns]"), n)
                       + np.tile(np.arange(n) * np.timedelta64(pd.Timedelta(step)), len(ref)))}
    for c in STD:
        z = rng.standard_normal((len(ref), n))
        z -= z.mean(axis=1, keepdims=True)
        z /= z.std(axis=1, keepdims=True)
        mu = ref[c].to_numpy(float)[:, None]
        sd = np.nan_to_num(ref[f"{c}__std"].to_numpy(float), nan=0.0)[:, None]
        x = mu + sd * z
        if c == "nacelle_position_deg":
            x = x % 360
        out[c] = x.ravel()
    d = pd.DataFrame(out)
    d["t_start"] = pd.to_datetime(d["t_start"], utc=True)
    return d


def truth(samples: pd.DataFrame, n_expected: int) -> pd.DataFrame:
    """Independent per-bin truth from the written samples (plain groupby on UTC sample starts)."""
    s = samples.copy()
    s["timestamp"] = s["t_start"].dt.floor("10min")
    lin = [c for c in STD if c != "nacelle_position_deg"]
    g = s.groupby(["turbine_id", "timestamp"])
    t = g[lin].mean()
    t["power_kw_std"] = g["power_kw"].std(ddof=0)
    t["power_kw_min"], t["power_kw_max"] = g["power_kw"].min(), g["power_kw"].max()
    t["n_samples"] = g.size()
    t["coverage"] = (t["n_samples"] / n_expected).clip(upper=1)
    return t.reset_index()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--raw-dir", default=str(cfg.RAW_DIR))
    a = ap.parse_args()
    raw = Path(a.raw_dir)
    out = raw / "ingest-fixtures" / "highres"
    (out / "1min").mkdir(parents=True, exist_ok=True)
    (out / "1s").mkdir(parents=True, exist_ok=True)
    # ---- 1-min, KEL01-02, March 2022, local time, end labels, dropouts
    ref = _ref(raw, "2022-03-01", "2022-04-01")
    ref.to_parquet(out / "ref_10min_2022-03.parquet", index=False)
    s = expand(ref, "1min", seed=1)
    rng = np.random.default_rng(2)
    keep = rng.random(len(s)) > 0.05
    outage = (s["turbine_id"] == "KEL02") & (s["t_start"] >= "2022-03-15 06:00Z") & (s["t_start"] < "2022-03-15 08:00Z")
    sparse = (s["turbine_id"] == "KEL01") & (s["t_start"] >= "2022-03-20 12:00Z") & (s["t_start"] < "2022-03-20 13:00Z") & \
             (s["t_start"].dt.minute % 10 >= 3)
    s = s[keep & ~outage & ~sparse].reset_index(drop=True)
    s["state"] = np.where(s["power_kw"] > 20, 2, np.where(s["wind_speed_ms"] > 3, 1, 0))
    truth(s, 10).to_parquet(out / "truth_1min.parquet", index=False)
    for tid, g in s.groupby("turbine_id"):
        loc_end = (g["t_start"] + pd.Timedelta("1min")).dt.tz_convert("Europe/London")
        w = pd.DataFrame({"Zeit": loc_end.dt.strftime("%d.%m.%Y %H:%M"), **{VENDOR[c]: g[c].to_numpy() for c in STD},
                          "Betriebszustand": g["state"].to_numpy()})
        w.to_csv(out / "1min" / f"WTG{tid[-2:]}_2022-03.csv", sep=";", decimal=",", index=False, float_format="%.9g")
    # ---- 1-s, KEL01, 10-11 March 2022, UTC, start labels, complete
    r1 = ref[(ref["turbine_id"] == "KEL01") & (ref["timestamp"] >= "2022-03-10") & (ref["timestamp"] < "2022-03-12")]
    s1 = expand(r1, "1s", seed=3)
    truth(s1, 600).to_parquet(out / "truth_1s.parquet", index=False)
    w1 = s1.rename(columns={"t_start": "time_utc"}).rename(columns=VENDOR)
    w1.to_parquet(out / "1s" / "KEL01_2022-03-10.parquet", index=False)
    print(f"1-min: {len(s):,} samples; 1-s: {len(s1):,} samples -> {out}")


if __name__ == "__main__":
    main()

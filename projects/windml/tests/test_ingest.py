"""windml.ingest on tiny synthetic exports (no downloads): units, mapping checks, every layout, DST, suggest, quality, CLI."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from windml.ingest import cli, loader, mapping, quality, suggest, units

UTC_START = "2022-10-29 22:00"   # spans the Europe/London autumn DST change (2022-10-30 01:00-02:00 repeats)
N = 72


def _truth(n_turbines=2, n=N, start=UTC_START, seed=0):
    rng = np.random.default_rng(seed)
    ts = pd.date_range(start, periods=n, freq="10min", tz="UTC")
    rows = []
    for t in range(1, n_turbines + 1):
        ws = rng.uniform(3, 14, n)
        rows.append(pd.DataFrame({"timestamp": ts, "turbine_id": f"KEL{t:02d}", "wind_speed_ms": ws.round(3),
                                  "power_kw": np.clip((ws - 3) * 180, 0, 2050).round(2), "ambient_temp_c": rng.normal(10, 2, n).round(2),
                                  "gear_oil_inlet_pressure_bar": rng.uniform(1, 2.5, n).round(3)}))
    return pd.concat(rows, ignore_index=True)


def _write_mapping(tmp_path, m: dict) -> Path:
    p = tmp_path / "m.yaml"
    p.write_text(yaml.safe_dump(m, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return p


def _messy_csv(raw: Path, truth: pd.DataFrame):
    """';' + decimal comma, preamble, °F, W, kPa, Europe/London local time, interval-END labels, one file per turbine."""
    raw.mkdir(parents=True, exist_ok=True)
    for tid, g in truth.groupby("turbine_id"):
        loc = (g["timestamp"] + pd.Timedelta("10min")).dt.tz_convert("Europe/London")
        w = pd.DataFrame({"Zeit": loc.dt.strftime("%d.%m.%Y %H:%M"), "ActPwr_Avg [W]": g["power_kw"] * 1000,
                          "WindSpd_Avg [m/s]": g["wind_speed_ms"], "AmbTmp_Avg [°F]": g["ambient_temp_c"] * 9 / 5 + 32,
                          "GbxOilPrs_Avg [kPa]": g["gear_oil_inlet_pressure_bar"] * 100, "WindSpd_Max [m/s]": g["wind_speed_ms"] + 1})
        with open(raw / f"WTG{tid[-2:]}_2022-10.csv", "w", encoding="latin-1", newline="") as fh:
            fh.write("Vendor export v1\nZeitzone: Europe/London; Zeitstempel = Intervallende\n")
            w.to_csv(fh, sep=";", decimal=",", index=False, float_format="%.6g")


MESSY = {
    "name": "messy", "rated_power_kw": 2050,
    "scada": {"files": ["WTG*_*.csv"], "csv": {"delimiter": ";", "decimal": ",", "encoding": "latin-1", "header_match": "^Zeit;"},
              "turbine_id": {"from": "filename", "regex": r"WTG(\d+)_", "format": "KEL{:02d}"},
              "timestamp": {"column": "Zeit", "format": "%d.%m.%Y %H:%M", "timezone": "Europe/London", "label": "end"},
              "signals": {"power_kw": {"column": "ActPwr_Avg [W]", "unit": "W"}, "wind_speed_ms": "WindSpd_Avg [m/s]",
                          "ambient_temp_c": {"column": "AmbTmp_Avg [°F]", "unit": "degF"},
                          "gear_oil_inlet_pressure_bar": {"column": "GbxOilPrs_Avg [kPa]", "unit": "kPa"}}}}


def _assert_matches(df, truth, sigs, tol=1e-4):
    j = truth.merge(df, on=["turbine_id", "timestamp"], how="outer", suffixes=("_t", "_l"), indicator=True)
    assert (j["_merge"] == "both").all(), j["_merge"].value_counts()
    for s in sigs:
        np.testing.assert_allclose(j[s + "_l"], j[s + "_t"], rtol=tol, atol=tol)


# ---------------------------------------------------------------- units
def test_unit_conversions():
    s = pd.Series([32.0, 212.0])
    assert units.convert(s, "°F", "degC").tolist() == pytest.approx([0, 100])
    assert units.convert(pd.Series([1500.0]), "W", "kW").iloc[0] == pytest.approx(1.5)
    assert units.convert(pd.Series([250.0]), "kPa", "bar").iloc[0] == pytest.approx(2.5)
    assert units.unit_from_name("AmbTmp_Avg [°F]") in ("degF", "°F") and units.normalize_unit(units.unit_from_name("Power (kW)")) == "kW"
    with pytest.raises(ValueError):
        units.convert(s, "kW", "degC")


def test_unit_switch_and_guess():
    x = pd.Series([1.5, 2.0, 150.0, 210.0, np.nan])
    out, hi = units.split_switch(x, "bar", "kPa", "bar", 20)
    assert out.tolist()[:4] == pytest.approx([1.5, 2.0, 1.5, 2.1]) and hi.tolist() == [False, False, True, True, False]
    f = pd.Series(np.random.default_rng(0).normal(60, 15, 500))   # summer ambient in °F
    u, score, _ = units.guess_unit(f, "temperature", "degC", (-45, 55))
    assert units.normalize_unit(u) == "degF" and score > 0.5
    w = pd.Series(np.random.default_rng(1).uniform(0, 2.0e6, 500))  # power in W
    assert units.normalize_unit(units.guess_unit(w, "power", "kW", (-200, 10_000))[0]) == "W"


# ---------------------------------------------------------------- mapping validation
def test_mapping_validation_errors():
    good = yaml.safe_load(yaml.safe_dump(MESSY))
    assert mapping.validate(good)["scada"]["signals"]["wind_speed_ms"] == {"column": "WindSpd_Avg [m/s]"}
    for mutate, msg in [
        (lambda m: m["scada"].pop("turbine_id"), "turbine_id"),
        (lambda m: m["scada"]["signals"].update({"not_a_signal": "x"}), "not a canonical signal"),
        (lambda m: m["scada"]["timestamp"].update({"label": "middle"}), "label"),
        (lambda m: m["scada"].update({"typo_key": 1}), "typo_key"),
        (lambda m: m["scada"].update({"layout": "long"}), "long"),
    ]:
        m = yaml.safe_load(yaml.safe_dump(MESSY))
        mutate(m)
        with pytest.raises(mapping.MappingError, match=msg):
            mapping.validate(m)


# ---------------------------------------------------------------- layouts
def test_messy_wide_csv_local_time_dst(tmp_path):
    truth = _truth()
    _messy_csv(tmp_path, truth)
    m = mapping.load_mapping(_write_mapping(tmp_path, MESSY))
    df, log = loader.load_scada(m, tmp_path)
    _assert_matches(df, truth, ["power_kw", "wind_speed_ms", "ambient_temp_c", "gear_oil_inlet_pressure_bar"])
    assert log.dst["scada"]["ambiguous_rows"] > 0          # the repeated hour was present and resolved
    assert df["timestamp"].dt.tz is not None and str(df["timestamp"].dt.tz) == "UTC"


def test_long_parquet(tmp_path):
    truth = _truth()
    tags = {"power_kw": "WTUR.W", "wind_speed_ms": "WNAC.WdSpd", "gear_oil_inlet_pressure_bar": "WTRM.GbxOilPres"}
    lg = truth.melt(id_vars=["timestamp", "turbine_id"], value_vars=list(tags), var_name="s", value_name="value")
    lg["value"] = np.where(lg["s"] == "gear_oil_inlet_pressure_bar", lg["value"] * 100, lg["value"])
    lg = pd.DataFrame({"ts": lg["timestamp"].dt.tz_convert(None).astype("datetime64[ms]").astype("int64"),
                       "asset": "WTG-" + lg["turbine_id"].str[-2:], "tag": lg["s"].map(tags), "value": lg["value"]})
    lg.sample(frac=1, random_state=0).to_parquet(tmp_path / "long.parquet", index=False)
    m = {"name": "lg", "scada": {"files": ["*.parquet"], "layout": "long", "long": {"tag_column": "tag", "value_column": "value"},
                                 "turbine_id": {"from": "column", "column": "asset", "regex": r"WTG-(\d+)", "format": "KEL{:02d}"},
                                 "timestamp": {"column": "ts", "format": "epoch_ms"},
                                 "signals": {"power_kw": "WTUR.W", "wind_speed_ms": "WNAC.WdSpd",
                                             "gear_oil_inlet_pressure_bar": {"tag": "WTRM.GbxOilPres", "unit": "kPa"}}}}
    df, log = loader.load_scada(mapping.load_mapping(_write_mapping(tmp_path, m)), tmp_path)
    _assert_matches(df, truth, list(tags))


def test_excel_sheet_per_turbine(tmp_path):
    truth = _truth(n=30, start="2022-03-01")
    with pd.ExcelWriter(tmp_path / "book.xlsx", engine="openpyxl") as xw:
        for tid, g in truth.groupby("turbine_id"):
            w = pd.DataFrame({"Datum": g["timestamp"].dt.tz_convert(None), "Leistung (kW)": g["power_kw"].to_numpy(),
                              "Windgeschwindigkeit (m/s)": g["wind_speed_ms"].to_numpy()})
            sheet = f"WEA {int(tid[-2:])}"
            pd.DataFrame([["title row"]]).to_excel(xw, sheet_name=sheet, index=False, header=False)
            w.to_excel(xw, sheet_name=sheet, index=False, startrow=1)
    m = {"name": "x", "scada": {"files": ["*.xlsx"], "excel": {"sheets": "all", "header_row": 1},
                                "turbine_id": {"from": "sheet", "regex": r"WEA (\d+)", "format": "KEL{:02d}"},
                                "timestamp": {"column": "Datum"},
                                "signals": {"power_kw": "Leistung (kW)", "wind_speed_ms": "Windgeschwindigkeit (m/s)"}}}
    df, _ = loader.load_scada(mapping.load_mapping(_write_mapping(tmp_path, m)), tmp_path)
    _assert_matches(df, truth, ["power_kw", "wind_speed_ms"])


def test_duplicates_offgrid_and_offsets(tmp_path):
    ts = ["2022-06-01T00:00:00+02:00", "2022-06-01T00:10:00+02:00", "2022-06-01T00:10:00+02:00", "2022-06-01T00:21:30+02:00"]
    pd.DataFrame({"name": "T1", "time": ts, "P": [1.0, 2.0, np.nan, 4.0], "W": [5.0, 6.0, 7.0, 8.0]}).to_csv(tmp_path / "a.csv", index=False)
    m = {"name": "o", "scada": {"files": ["a.csv"], "turbine_id": {"from": "column", "column": "name"},
                                "timestamp": {"column": "time", "format": "iso"}, "signals": {"power_kw": "P", "wind_speed_ms": "W"}}}
    df, log = loader.load_scada(mapping.load_mapping(_write_mapping(tmp_path, m)), tmp_path)
    assert df["timestamp"].min() == pd.Timestamp("2022-05-31 22:00", tz="UTC")
    assert len(df) == 3 and sum(log.duplicates.values()) == 1
    assert df.loc[df["timestamp"] == pd.Timestamp("2022-05-31 22:10", tz="UTC"), "power_kw"].item() == 2.0  # most complete row kept
    assert log.off_grid  # 00:21:30 snapped to 00:20


# ---------------------------------------------------------------- status log -> labels
def test_status_mapping_and_classes(tmp_path):
    pd.DataFrame({"Beginn": ["01.01.2022 02:00:00", "01.01.2022 08:00:00", "01.01.2022 09:00:00"],
                  "Ende": ["01.01.2022 05:00:00", "01.01.2022 08:20:00", ""],
                  "Typ": ["Halt", "Halt", "Info"], "Code": [611, 9999, 100030],
                  "Text": ["Gear oil pressure too low", "Vendor specific 9999", "Brake program"]}).to_csv(tmp_path / "Alarme_WTG01.csv", sep=";", index=False)
    _messy_csv(tmp_path, _truth(n_turbines=1))
    m = yaml.safe_load(yaml.safe_dump(MESSY))
    m["status"] = {"files": ["Alarme_WTG*.csv"], "csv": {"delimiter": ";"},
                   "turbine_id": {"from": "filename", "regex": r"WTG(\d+)", "format": "KEL{:02d}"},
                   "start": {"column": "Beginn", "format": "%d.%m.%Y %H:%M:%S", "timezone": "Europe/London"},
                   "end": {"column": "Ende", "format": "%d.%m.%Y %H:%M:%S", "timezone": "Europe/London"}, "end_missing": [""],
                   "status": {"column": "Typ", "map": {"Halt": "Stop", "Info": "Informational"}}, "code": "Code", "message": "Text",
                   "class_by_code": {9999: "maintenance", 611: "fault"}}
    m = mapping.load_mapping(_write_mapping(tmp_path, m))
    ev = loader.classify(loader.load_status(m, tmp_path), m)
    assert len(ev) == 3 and ev["turbine_id"].unique().tolist() == ["KEL01"]
    by = ev.set_index("code")
    assert by.loc[611, "event_class"] == "fault" and bool(by.loc[611, "is_stop"]) and bool(by.loc[611, "is_major_fault"])
    assert by.loc[9999, "event_class"] == "maintenance" and by.loc[100030, "event_class"] == "info"
    assert by.loc[611, "duration"] == pd.Timedelta("3h")


# ---------------------------------------------------------------- suggest
def test_suggest_drafts_a_valid_mapping(tmp_path):
    truth = _truth(n=200, start="2022-10-29 00:00")
    _messy_csv(tmp_path, truth)
    s = suggest.suggest(tmp_path / "WTG01_2022-10.csv", raw_dir=tmp_path)
    assert s.read_opts["delimiter"] == ";" and s.read_opts["decimal"] == ","
    assert s.timestamp["column"] == "Zeit" and s.timestamp["timezone"] == "Europe/London" and s.timestamp["label"] == "end"
    assert s.turbine_id["from"] == "filename"
    got = {k: v["source"] for k, v in s.signals.items()}
    assert got["power_kw"] == "ActPwr_Avg [W]" and got["wind_speed_ms"] == "WindSpd_Avg [m/s]"
    assert got["ambient_temp_c"] == "AmbTmp_Avg [°F]" and units.normalize_unit(s.signals["ambient_temp_c"]["unit"]) == "degF"
    assert units.normalize_unit(s.signals["power_kw"]["unit"]) == "W"
    assert all(0 <= v["confidence"] <= 1 for v in s.signals.values())
    text = suggest.to_yaml(s, "draft")
    m = mapping.validate(yaml.safe_load(text))
    m["scada"]["turbine_id"]["format"] = "KEL{:02d}"
    df, _ = loader.load_scada(m, tmp_path)
    _assert_matches(df[df["turbine_id"] == "KEL01"], truth[truth["turbine_id"] == "KEL01"], ["power_kw", "wind_speed_ms", "ambient_temp_c"])


def test_suggest_long_layout(tmp_path):
    truth = _truth(n=50)
    lg = truth.melt(id_vars=["timestamp", "turbine_id"], value_vars=["power_kw", "wind_speed_ms", "ambient_temp_c"], var_name="tag")
    lg["tag"] = lg["tag"].map({"power_kw": "WTUR.W", "wind_speed_ms": "WNAC.WdSpd", "ambient_temp_c": "WNAC.ExTmp"})
    lg["timestamp"] = lg["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    lg.rename(columns={"turbine_id": "asset"}).to_csv(tmp_path / "long.csv", index=False)
    s = suggest.suggest(tmp_path / "long.csv")
    assert s.layout == "long" and s.long == {"tag_column": "tag", "value_column": "value"}
    assert s.turbine_id == {**s.turbine_id, "from": "column", "column": "asset"}
    assert {k: v["source"] for k, v in s.signals.items()} == {"power_kw": "WTUR.W", "wind_speed_ms": "WNAC.WdSpd", "ambient_temp_c": "WNAC.ExTmp"}


# ---------------------------------------------------------------- quality report + CLI
def test_quality_report_flags_problems(tmp_path):
    df = _truth(n=200, start="2022-01-01")
    df.loc[df["turbine_id"] == "KEL01", "ambient_temp_c"] = 7.123          # stuck for 33 h
    df.loc[df.index[:5], "gear_oil_inlet_pressure_bar"] = 150.0          # out of range (kPa left in)
    gap = (df["turbine_id"] == "KEL02") & (df["timestamp"] >= pd.Timestamp("2022-01-01 05:00", tz="UTC")) & \
          (df["timestamp"] < pd.Timestamp("2022-01-01 10:00", tz="UTC"))
    df = df[~gap]
    md, summary = quality.build(df.reset_index(drop=True), loader.LoadLog(), None, {"name": "t"})
    text = " ".join(summary["findings"])
    assert "Stuck" in text and "KEL01 ambient_temp_c" in text
    assert "gear_oil_inlet_pressure_bar" in text
    assert "## Coverage" in md or "Coverage" in md
    quality.write(md, tmp_path / "dq.md")
    assert (tmp_path / "dq.md").exists() and (tmp_path / "dq.html").read_text().startswith("<!")


def test_cli_suggest_validate_load(tmp_path, capsys):
    truth = _truth()
    _messy_csv(tmp_path / "raw", truth)
    mp = _write_mapping(tmp_path, MESSY)
    assert cli.main(["validate", "-m", str(mp), "--raw-dir", str(tmp_path / "raw"), "--report", str(tmp_path / "r" / "dq.md")]) == 0
    assert (tmp_path / "r" / "dq.html").exists()
    assert cli.main(["load", "-m", str(mp), "--raw-dir", str(tmp_path / "raw"), "--out", str(tmp_path / "out")]) == 0
    out = pd.read_parquet(tmp_path / "out" / "messy_canonical.parquet")
    assert len(out) == len(truth)
    assert cli.main(["suggest", str(tmp_path / "raw" / "WTG01_2022-10.csv"), "--out", str(tmp_path / "draft.yaml")]) == 0
    mapping.validate(yaml.safe_load((tmp_path / "draft.yaml").read_text(encoding="utf-8")))
    assert cli.main(["validate", "-m", str(tmp_path / "draft.yaml"), "--schema-only"]) == 0
    bad = _write_mapping(tmp_path, {"name": "b", "scada": {"files": ["x"]}})
    assert cli.main(["validate", "-m", str(bad), "--schema-only"]) == 1

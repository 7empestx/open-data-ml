"""High-res (1-min, 30-s) ingest: native-interval detection, 10-min aggregation, coverage, gaps, labels, raw kept."""
import numpy as np
import pandas as pd
import pytest
import yaml

from windml.ingest import loader, mapping, pipeline, resample


def _m(tmp_path, m):
    p = tmp_path / "m.yaml"
    p.write_text(yaml.safe_dump(m, sort_keys=False), encoding="utf-8")
    return mapping.load_mapping(p)


def _one_min(tmp_path):
    """2 h of 1-min samples for one turbine, stamped at the END of each minute, with: a duplicate sample, a 30-min gap,
    a sparse bin (3 samples), a nacelle direction wrapping through north and a status-code column."""
    start = pd.Timestamp("2022-05-01 00:00", tz="UTC")
    t_start = pd.date_range(start, periods=120, freq="1min")
    rng = np.random.default_rng(0)
    d = pd.DataFrame({"t_start": t_start, "P": rng.uniform(100, 2000, 120).round(1), "WS": rng.uniform(3, 15, 120).round(2),
                      "NAC": np.where(np.arange(120) % 2 == 0, 358.0, 2.0), "STATE": np.where(np.arange(120) % 10 < 7, 2, 5)})
    d.loc[d.index[:10], "STATE"] = [2, 2, 2, 5, 5, 5, 5, 6, 6, 6]          # bin 00:00: mode 5, last 6
    gap = (d["t_start"] >= start + pd.Timedelta("40min")) & (d["t_start"] < start + pd.Timedelta("70min"))
    sparse = (d["t_start"] >= start + pd.Timedelta("80min")) & (d["t_start"] < start + pd.Timedelta("87min"))
    d = d[~gap & ~sparse]
    d = pd.concat([d, d.iloc[[5]]])                                         # duplicate sample
    out = pd.DataFrame({"time": (d["t_start"] + pd.Timedelta("1min")).dt.strftime("%Y-%m-%d %H:%M:%S"), "P": d["P"], "WS": d["WS"],
                        "NAC": d["NAC"], "STATE": d["STATE"]})
    out.to_csv(tmp_path / "WTG01_1min.csv", index=False)
    m = {"name": "hr", "scada": {"files": ["WTG*_1min.csv"], "turbine_id": {"from": "filename", "regex": r"WTG(\d+)", "format": "T{:02d}"},
                                 "timestamp": {"column": "time", "label": "end"},
                                 "signals": {"power_kw": "P", "wind_speed_ms": "WS", "nacelle_position_deg": "NAC"},
                                 "states": {"operating_state": "STATE"}, "aggregate": {"min_coverage": 0.5}}}
    return d, _m(tmp_path, m)


def test_detect_interval():
    t = pd.Series(pd.date_range("2022-01-01", periods=50, freq="30s"))
    assert resample.detect_interval(t) == (pd.Timedelta("30s"), 1.0)
    t2 = pd.Series(pd.date_range("2022-01-01", periods=50, freq="10min").delete([3, 4, 20]))
    iv, share = resample.detect_interval(t2)
    assert iv == pd.Timedelta("10min") and share > 0.9


def test_one_minute_end_labels_coverage_gaps_states(tmp_path):
    d, m = _one_min(tmp_path)
    keep = tmp_path / "raw_hr.parquet"
    df, log = loader.load_scada(m, tmp_path, keep_raw=keep)
    assert log.native_interval["T01"]["interval"] == "1min"
    b = df.set_index("timestamp")
    t0 = pd.Timestamp("2022-05-01 00:00", tz="UTC")
    # bin 00:00 holds exactly the samples that START in [00:00, 00:10) (end-labelled 00:01 .. 00:10)
    first = d.drop_duplicates("t_start").set_index("t_start").loc[t0:t0 + pd.Timedelta("9min")]
    assert b.loc[t0, "n_samples"] == 10 and b.loc[t0, "coverage"] == pytest.approx(1.0)
    assert b.loc[t0, "power_kw"] == pytest.approx(first["P"].mean())
    assert b.loc[t0, "power_kw_min"] == first["P"].min() and b.loc[t0, "power_kw_max"] == first["P"].max()
    assert b.loc[t0, "power_kw_std"] == pytest.approx(first["P"].std(ddof=0))
    # circular mean of 358/2 is north, not 180
    nac = b.loc[t0, "nacelle_position_deg"]
    assert min(nac, 360 - nac) < 1e-6 and b.loc[t0, "nacelle_position_deg_std"] < 3
    assert b.loc[t0, "operating_state_mode"] == 5 and b.loc[t0, "operating_state_last"] == 6
    # 30-min gap: bins 00:40, 00:50, 01:00 absent (00:40-01:10 removed); sparse bin 01:20 has 3 samples -> values blanked
    for k in ("40min", "50min", "60min"):
        assert t0 + pd.Timedelta(k) not in b.index
    sp = b.loc[t0 + pd.Timedelta("80min")]
    assert sp["n_samples"] == 3 and sp["coverage"] == pytest.approx(0.3) and np.isnan(sp["power_kw"])
    assert any("below 0.5" in w for w in log.warnings)
    assert log.aggregation["groups"][0]["duplicates_dropped"] == 1
    raw = pd.read_parquet(keep)
    assert len(raw) == len(d) and raw["timestamp"].min() == t0      # raw samples kept, shifted to sample start


def test_thirty_seconds_long_parquet_and_export(tmp_path):
    ts = pd.date_range("2022-05-01", periods=240, freq="30s", tz="UTC")   # 2 h
    rows = []
    for tid in ("WTG-01", "WTG-02"):
        rng = np.random.default_rng(len(rows))
        for tag, vals in (("P", rng.uniform(0, 2000, 240)), ("WS", rng.uniform(3, 14, 240)), ("OILP", rng.uniform(150, 250, 240))):
            rows.append(pd.DataFrame({"ts": ts.tz_convert(None).astype("datetime64[ms]").astype("int64"), "asset": tid, "tag": tag, "value": vals}))
    lg = pd.concat(rows).sample(frac=1, random_state=1)
    lg.to_parquet(tmp_path / "hr.parquet", index=False)
    m = _m(tmp_path, {"name": "hr30", "scada": {"files": ["hr.parquet"], "layout": "long", "long": {"tag_column": "tag", "value_column": "value"},
                                                "turbine_id": {"from": "column", "column": "asset", "regex": r"WTG-(\d+)", "format": "T{:02d}"},
                                                "timestamp": {"column": "ts", "format": "epoch_ms"},
                                                "signals": {"power_kw": "P", "wind_speed_ms": "WS",
                                                            "gear_oil_inlet_pressure_bar": {"tag": "OILP", "unit": "kPa"}}}})
    df, log = loader.load_scada(m, tmp_path)
    assert len(df) == 2 * 12 and (df["n_samples"] == 20).all() and (df["coverage"] == 1).all()
    src = lg[(lg["asset"] == "WTG-01") & (lg["tag"] == "OILP")].sort_values("ts").head(20)["value"]
    first = df[df["turbine_id"] == "T01"].iloc[0]
    assert first["gear_oil_inlet_pressure_bar"] == pytest.approx(src.mean() / 100)
    assert first["gear_oil_inlet_pressure_bar_max"] == pytest.approx(src.max() / 100)
    res = pipeline.export(df, None, "hr30", tmp_path / "out", 2050)
    assert res["stats_files"] == 2
    st = pd.read_parquet(tmp_path / "out" / "hr30_stats_T01.parquet")
    assert st["inlet_p_max"].iloc[0] == pytest.approx(src.max() / 100, rel=1e-6)


def test_interval_validation():
    bad = {"name": "x", "scada": {"files": ["a.csv"], "turbine_id": {"from": "constant", "value": "T1"}, "timestamp": "t",
                                  "signals": {"power_kw": "P"}, "interval": "sometimes"}}
    with pytest.raises(mapping.MappingError, match="interval"):
        mapping.validate(bad)
    bad["scada"]["interval"] = "auto"
    bad["scada"]["aggregate"] = {"stats": ["wind_speed_ms"]}
    with pytest.raises(mapping.MappingError, match="not a mapped signal"):
        mapping.validate(bad)


def test_turbine_in_columns_and_pre_aggregated_stats(tmp_path):
    """SMARTEOLE-style export: one file, turbine number inside the column names, 1-min avg/min/max/std/count of 1-Hz
    samples. Bins must equal the statistics of the underlying 1-Hz samples (count-weighted mean, pooled std)."""
    rng = np.random.default_rng(1)
    t0 = pd.Timestamp("2020-03-01 00:00")
    hz = {n: rng.normal(1000 * n, 50, 20 * 60) for n in (1, 2)}          # 20 min of 1-Hz power per turbine
    rows = []
    for i in range(20):
        r = {"time": (t0 + pd.Timedelta(minutes=i)).strftime("%Y-%m-%d %H:%M:%S")}
        for n, x in hz.items():
            k = 60 if not (n == 2 and i == 3) else 1                      # one minute with a single sample (std NaN)
            s = x[i * 60:i * 60 + k]
            r |= {f"P_{n}_avg": s.mean(), f"P_{n}_min": s.min(), f"P_{n}_max": s.max(),
                  f"P_{n}_std": s.std() if k > 1 else np.nan, f"P_{n}_count": k, f"flag_{n}": int(i >= 13)}
        rows.append(r)
    pd.DataFrame(rows).to_csv(tmp_path / "farm.csv", index=False)
    m = _m(tmp_path, {"name": "cols", "scada": {
        "files": ["farm.csv"], "turbine_id": {"from": "columns", "values": [1, 2], "format": "S{}"},
        "timestamp": {"column": "time", "timezone": "UTC"},
        "signals": {"power_kw": {"column": "P_{turbine}_avg", "min": "P_{turbine}_min", "max": "P_{turbine}_max",
                                 "std": "P_{turbine}_std", "count": "P_{turbine}_count", "unit": "kW"}},
        "states": {"derate_flag": "flag_{turbine}"}, "aggregate": {"stats": ["power_kw"]}}})
    df, log = loader.load_scada(m, tmp_path)
    assert sorted(df["turbine_id"].unique()) == ["S1", "S2"] and log.native_interval["S1"]["interval"] == "1min"
    b = df.set_index(["turbine_id", "timestamp"])
    for n in (1, 2):
        for j in range(2):
            x = hz[n][j * 600:(j + 1) * 600]
            if n == 2 and j == 0:
                x = np.concatenate([x[:180], x[180:181], x[240:]])         # minute 3 kept only its first sample
            row = b.loc[(f"S{n}", pd.Timestamp(t0, tz="UTC") + pd.Timedelta(minutes=10 * j))]
            assert row["power_kw"] == pytest.approx(x.mean())
            assert row["power_kw_min"] == pytest.approx(x.min()) and row["power_kw_max"] == pytest.approx(x.max())
            assert row["power_kw_std"] == pytest.approx(x.std(), rel=1e-6)
    assert b.loc[("S1", pd.Timestamp("2020-03-01 00:10", tz="UTC")), "derate_flag_mode"] == 1
    assert not any("__" in c for c in df.columns)
    with pytest.raises(mapping.MappingError):
        _m(tmp_path, {"name": "x", "scada": {"files": ["farm.csv"], "turbine_id": {"from": "columns"},
                                             "timestamp": {"column": "time"}, "signals": {"power_kw": "P_{turbine}_avg"}}})

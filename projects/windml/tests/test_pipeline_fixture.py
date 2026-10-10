"""Run the reading, cleaning and labeling code on the tiny fixture tree."""
import pandas as pd


def test_year_and_turbine_filters(raw_tree):
    raw, reload = raw_tree
    _, gb = reload()
    gb.use_all_years()
    assert len(gb.turbine_files("kelmarsh")) == 4
    _, gb = reload(WINDML_YEARS="2017")
    gb.use_all_years()
    files = gb.turbine_files("kelmarsh")
    assert len(files) == 2 and all("scada_2017" in str(f) for f in files)
    _, gb = reload(WINDML_TURBINES="KEL02")
    gb.use_all_years()
    assert [gb._turbine_id(f) for f in gb.turbine_files("kelmarsh")] == ["KEL02", "KEL02"]
    assert len(gb.status_files("kelmarsh")) == 2


def test_read_and_clean(raw_tree):
    from windml import clean_wind as cw
    _, reload = raw_tree
    _, gb = reload(WINDML_YEARS="2016", WINDML_TURBINES="KEL01")
    gb.use_all_years()
    (f,) = gb.turbine_files("kelmarsh")
    df, meta = gb.read_turbine(f, usecols=list(cw.KEY_COLUMNS.values()))
    assert meta["Time zone"] == "UTC" and str(meta["interval_start"]) == "2016-01-01 00:00:00+00:00"
    assert df["turbine_id"].unique().tolist() == ["KEL01"] and len(df) == 144
    assert str(df["timestamp"].dt.tz) == "UTC"
    assert gb.rated_power("kelmarsh") == {"KEL01": 2050.0, "KEL02": 2050.0}
    clean, stats = cw.clean_turbine(df, meta, 2050.0)
    assert len(clean) == 144
    assert {"power_kw", "qc_power_kw", "wind_speed_ms"} <= set(clean.columns)
    assert clean["wind_speed_ms"].notna().all()  # the 2-step gap is interpolated
    assert (clean["qc_wind_speed_ms"] & 1).sum() == 2


def test_events_and_labels(raw_tree):
    from windml import clean_wind as cw, labeling as lb
    _, reload = raw_tree
    _, gb = reload(WINDML_TURBINES="KEL01")
    gb.use_all_years()
    ev = lb.classify_events(lb.parse_events("kelmarsh"), major_min_duration="1h")
    assert len(ev) == 6 and set(ev["status"]) == {"Stop", "Warning"}
    gear = ev[ev["code"] == 611]
    assert gear["is_major_fault"].all() and (gear["component"] == "gearbox").all()
    assert (ev.loc[ev["code"] == 611, "duration"] == pd.Timedelta("3h")).all()
    parts = []
    for f in gb.turbine_files("kelmarsh"):
        df, meta = gb.read_turbine(f, usecols=list(cw.KEY_COLUMNS.values()))
        parts.append(cw.clean_turbine(df, meta, 2050.0)[0])
    lab = lb.label_grid(pd.concat(parts, ignore_index=True), ev, (7,))
    hit = lab["timestamp"].between(pd.Timestamp("2016-01-01 02:00", tz="UTC"), pd.Timestamp("2016-01-01 04:50", tz="UTC"))
    assert lab.loc[hit, "in_major_fault"].all()
    assert not lab.loc[lab["timestamp"] < pd.Timestamp("2016-01-01 02:00", tz="UTC"), "in_major_fault"].any()
    assert lab.loc[lab["timestamp"] < pd.Timestamp("2016-01-01 02:00", tz="UTC"), "pre_fault_7d"].all()

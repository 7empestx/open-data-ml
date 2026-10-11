"""`windml report` end to end on a tiny synthetic fleet (no downloads): flags, short-history handling, no alarm log."""
import json

import numpy as np
import pandas as pd
import yaml

from windml.fleet import cli


def _fleet(tmp_path, months=13, n=4):
    rng = np.random.default_rng(0)
    t = pd.date_range("2023-01-01", periods=int(months * 30.4 * 144), freq="10min", tz="UTC")
    doy = t.dayofyear.to_numpy()
    ambient = 10 + 8 * np.sin(2 * np.pi * (doy - 110) / 365) + rng.normal(0, 1.5, len(t))
    wind = np.clip(rng.weibull(2.0, len(t)) * 8.5, 0, 30)
    for i in range(1, n + 1):
        w = np.clip(wind + rng.normal(0, 0.4, len(t)), 0, 30)
        p = 2050 * np.clip((w - 3) / 9, 0, 1) ** 3 + rng.normal(0, 15, len(t))
        oil = 40 + 0.006 * p + 0.5 * ambient + rng.normal(0, 0.8, len(t))
        pump = 6.5 + 0.0003 * p + rng.normal(0, 0.1, len(t))
        amb = ambient + rng.normal(0, 0.3, len(t))
        if i == 1:      # oil circuit restriction building up over the last 2 months
            pump = pump + 2.6 * (t > t[-1] - pd.Timedelta(days=45))
        if i == 2:      # ambient sensor drifting in the last 4 months
            amb = amb + 3.0 * (t > t[-1] - pd.Timedelta(days=120))
        p[rng.random(len(t)) < 0.01] = 0.0
        df = pd.DataFrame({"time": t.strftime("%Y-%m-%d %H:%M"), "P": p.round(1), "WS": w.round(2), "TA": amb.round(2),
                           "OIL": oil.round(2), "PUMP": pump.round(3)})
        df.to_csv(tmp_path / f"T{i}.csv", index=False)
    m = {"name": "synth", "description": "synthetic 4-turbine fleet", "rated_power_kw": 2050,
         "scada": {"files": ["T*.csv"], "turbine_id": {"from": "filename", "regex": r"T(\d+)", "format": "S{:02d}"},
                   "timestamp": {"column": "time", "timezone": "UTC"},
                   "signals": {"power_kw": "P", "wind_speed_ms": "WS", "ambient_temp_c": "TA", "gear_oil_temp_c": "OIL",
                               "gear_oil_pump_pressure_bar": "PUMP"}}}
    mp = tmp_path / "synth.yaml"
    mp.write_text(yaml.safe_dump(m, sort_keys=False))
    return mp


def _run(tmp_path, mp):
    out = tmp_path / "report"
    args = cli.build_parser().parse_args(["--mapping", str(mp), "--out", str(out), "--raw-dir", str(tmp_path),
                                          "--work", str(tmp_path / "work"), "--workers", "1", "--fast", "--no-pdf"])
    info = cli.run(args)
    return info, out


def test_report_short_history_no_alarm_log(tmp_path):
    info, out = _run(tmp_path, _fleet(tmp_path))
    assert info["flags"]["S01"] == "RED"                       # pump pressure +2.6 bar
    assert info["flags"]["S02"] in ("AMBER", "RED")            # ambient sensor drift
    assert info["flags"]["S03"] == "GREEN" and info["flags"]["S04"] == "GREEN"
    sc = pd.read_csv(out / "tables" / "scorecard.csv").set_index("turbine_id")
    assert sc.loc["S01", "pump_rise"] > 2.0 and "pump pressure" in sc.loc["S01", "reasons"]
    assert sc.loc["S02", "drift_ambient_temp_c"] > 1.5
    assert set(sc["scheme"]) == {"cross-fit"}
    md = (out / "condition_report.md").read_text()
    assert md.index("## Executive summary") < md.index("1. Data quality")
    assert "no alarm log" in md and "cross-fitted" in md
    assert "Suggested check" in md and "bar above its own 12-month baseline" in md and "How the ratings work" in md
    assert (out / "condition_report.html").exists() and json.loads((out / "run.json").read_text())["turbines"] == 4
    # second run reuses the cache
    info2, _ = _run(tmp_path, tmp_path / "synth.yaml")
    assert info2["times"]["prepare_s"] < info["times"]["prepare_s"] + 1 and info2["flags"] == info["flags"]


def test_report_under_12_months_skips_models(tmp_path):
    info, out = _run(tmp_path, _fleet(tmp_path, months=6))
    sc = pd.read_csv(out / "tables" / "scorecard.csv")
    assert set(sc["scheme"]) == {"none"}
    md = (out / "condition_report.md").read_text()
    assert "less than 12 months" in md
    assert info["flags"]["S01"] == "RED"                       # trends still work without models

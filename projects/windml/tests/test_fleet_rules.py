"""Calibrated amber/red rules on a hand-made as-of panel (no data files needed)."""
import numpy as np
import pandas as pd

from windml.fleet import indicators, rules


def _panel(n_turb=6, months=4, over=None):
    rows = []
    for k in range(n_turb):
        for m in range(months):
            rows.append({"turbine_id": f"T{k:02d}", "as_of": pd.Timestamp("2024-01-31", tz="UTC") + pd.offsets.MonthEnd(m),
                         "pump_rise": 0.05 * ((k % 3) - 1), "oil_ep_6m": 0, "oil_ep_1m": 0, "pitch_ep_6m": 0, "pitch_ep_1m": 0,
                         "avail_6m": 0.99, "abn_oil_3m": 0.0, "abn_oil_months": 0})
    p = pd.DataFrame(rows)
    for (tid, m), vals in (over or {}).items():
        idx = p.index[(p["turbine_id"] == tid) & (p["as_of"] == p["as_of"].min() + pd.offsets.MonthEnd(m))]
        for c, v in vals.items():
            p.loc[idx, c] = v
    return indicators.fleet_relative(p)


def _rating(p, tid):
    r = rules.apply(p)
    return r.loc[p.index[(p["turbine_id"] == tid) & (p["as_of"] == p["as_of"].max())], "rating"].iloc[0]


def test_quiet_fleet_is_green():
    p = _panel()
    assert (rules.apply(p)["rating"] == "GREEN").all()


def test_pump_build_up_amber_then_red():
    assert _rating(_panel(over={("T01", 3): {"pump_rise": 1.2}}), "T01") == "AMBER"
    assert _rating(_panel(over={("T01", 3): {"pump_rise": 2.4}}), "T01") == "RED"


def test_pump_rise_shared_by_the_fleet_is_not_flagged():
    p = _panel()
    p["pump_rise"] = 1.5 + 0.02 * np.arange(len(p)) % 0.1   # everyone rose (e.g. a fleet-wide oil change)
    p = indicators.fleet_relative(p.drop(columns=[c for c in p if c.endswith("_rel")]))
    assert (rules.apply(p)["rating"] == "GREEN").all()


def test_repeat_trips_red_needs_persistence_and_recent_trip():
    many = {"oil_ep_6m": 10, "oil_ep_1m": 2}
    assert _rating(_panel(over={("T02", 3): many}), "T02") == "AMBER"                     # one month only
    assert _rating(_panel(over={("T02", 2): many, ("T02", 3): many}), "T02") == "RED"     # persistent and still tripping
    stopped = {"oil_ep_6m": 10, "oil_ep_1m": 0}
    assert _rating(_panel(over={("T02", 2): many, ("T02", 3): stopped}), "T02") == "AMBER"  # trips stopped: confirm repair


def test_low_availability_is_a_note_not_a_flag():
    assert _rating(_panel(over={("T03", 3): {"avail_6m": 0.80}}), "T03") == "GREEN"


def test_small_fleet_pump_needs_twice_the_rise():
    p = _panel(n_turb=3, over={("T00", 3): {"pump_rise": 1.2}})
    assert p["pump_rise_rel"].isna().all()
    assert _rating(p, "T00") == "GREEN"
    assert _rating(_panel(n_turb=3, over={("T00", 3): {"pump_rise": 2.2}}), "T00") == "RED"


def test_calibration_file_is_loaded():
    assert rules.CALIBRATION, "src/windml/fleet/calibration.json missing"
    assert rules.CALIBRATION["selected_on"] == "2017-2020" and rules.CALIBRATION["checked_on"] == "2021-2024"
    assert set(rules.ACTIVE) <= set(rules.PARAMS)
    share = rules.CALIBRATION["validation"]["test_share"]
    assert share["RED"] < 0.05 and share["GREEN"] > 0.8

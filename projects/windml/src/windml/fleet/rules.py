"""Calibrated amber/red rules on the as-of indicator panel (see indicators.py and scripts/calibrate_flags.py).

Each rule *family* looks at one specific failure signature and fires AMBER when the turbine is clearly unusual
both in absolute terms and against its peers in the same month. Families whose amber flag did not concentrate
before real events in the 2017-2020 selection period are kept as information only (they never set the flag).

RED is deliberately rare. A family turns RED only when its amber condition has held at three consecutive
month-ends (persistent, not a one-off) AND the turbine is a strong peer outlier, or when two independent
families agree, or when the gear-oil pump pressure build-up is large (the signature that preceded the
Penmanshiel gearbox service events).

The thresholds in PARAMS are the ones selected by scripts/calibrate_flags.py on as-of dates 2017-2020
(Kelmarsh + Penmanshiel) and checked on 2021-2024; reports/fleet_proof/calibration.md has the hit rates.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

# family -> parameters. Keys: a = absolute minimum, r = fleet-relative minimum (robust z vs the other turbines),
# k = minimum number of the last three 30-day blocks with >= 30% abnormal days, n = trip episodes in 6 months.
PARAMS: dict[str, dict] = {
    "oil_abn": {"a": 0.20, "r": 3.0, "k": 2},
    "pump": {"a": 0.5, "r": 3.0},
    "oil_trips": {"n": 3},
    "pitch_abn": {"a": 0.20, "r": 3.0, "k": 2},
    "pitch_trips": {"n": 3},
    "bearing_abn": {"a": 0.20, "r": 3.0, "k": 2},
    "perf_abn": {"a": 0.20, "r": 3.0, "k": 2},
    "avail": {"a": 0.95, "r": 3.0},
}
# families that set the flag (others are reported as information only)
ACTIVE: set[str] = {"pump", "oil_trips", "pitch_trips"}
RED_PERSIST = 2          # consecutive month-ends
RED_REL = 5.0            # robust z vs peers, for a persistent amber to become red
RED_PUMP_BAR = 2.0       # pump build-up (bar) that is red on its own when also a peer outlier
RED_TRIP_MULT = 3.0      # repeat trips: persistent AND at least this multiple of the amber count
NEVER_RED = {"avail"}    # past downtime is history, not a forecast
INFO_ONLY = {"avail"}    # by design: low availability is reported as a note, never a flag (see calibration.md)

CALIBRATION_FILE = Path(__file__).with_name("calibration.json")
CALIBRATION: dict = {}
if CALIBRATION_FILE.exists():   # written by scripts/calibrate_flags.py; overrides the defaults above
    CALIBRATION = json.loads(CALIBRATION_FILE.read_text())
    PARAMS = {**PARAMS, **CALIBRATION["params"]}
    ACTIVE = set(CALIBRATION["active"])
    RED_PERSIST, RED_REL = CALIBRATION["red"]["persist"], CALIBRATION["red"]["rel"]
    RED_PUMP_BAR, RED_TRIP_MULT = CALIBRATION["red"]["pump"], CALIBRATION["red"]["trip_mult"]

TARGET = {"oil_abn": "y_oil", "pump": "y_oil_service", "oil_trips": "y_oil", "pitch_abn": "y_pitch",
          "pitch_trips": "y_pitch", "bearing_abn": "y_major", "perf_abn": "y_major", "avail": "y_major"}
REL_COL = {"oil_abn": "abn_oil_3m_rel", "pump": "pump_rise_rel", "pitch_abn": "abn_pitch_3m_rel",
           "bearing_abn": "abn_main_bearing_3m_rel", "perf_abn": "abn_performance_3m_rel", "avail": "avail_6m_rel"}
_ABN = {"oil_abn": "oil", "pitch_abn": "pitch", "bearing_abn": "main_bearing", "perf_abn": "performance"}


def _col(p: pd.DataFrame, c: str) -> pd.Series:
    return p[c].astype(float) if c in p else pd.Series(np.nan, index=p.index)


def family_fires(p: pd.DataFrame, fam: str, prm: dict) -> pd.Series:
    """Boolean per panel row: amber condition for one family (NaN indicators never fire)."""
    if fam in _ABN:
        c = _ABN[fam]
        return ((_col(p, f"abn_{c}_3m") >= prm["a"]) & (_col(p, f"abn_{c}_3m_rel") >= prm["r"])
                & (_col(p, f"abn_{c}_months") >= prm["k"]))
    if fam == "pump":
        return (_col(p, "pump_rise") >= prm["a"]) & (_col(p, "pump_rise_rel") >= prm["r"])
    if fam in ("oil_trips", "pitch_trips"):
        return _col(p, f"{fam.split('_')[0]}_ep_6m") >= prm["n"]
    if fam == "avail":
        return (_col(p, "avail_6m") < prm["a"]) & (_col(p, "avail_6m_rel") <= -prm["r"])
    raise KeyError(fam)


def _run_length(fires: pd.Series, p: pd.DataFrame) -> pd.Series:
    """Number of consecutive as-of rows (per turbine, in time order) up to and including this one where it fired."""
    out = pd.Series(0, index=p.index)
    for _, g in p.sort_values("as_of").groupby("turbine_id"):
        n = 0
        for i in g.index:
            n = n + 1 if bool(fires[i]) else 0
            out[i] = n
    return out


def apply(p: pd.DataFrame, params: dict | None = None, active: set | None = None) -> pd.DataFrame:
    """Per row: <fam> (amber condition), <fam>_run (consecutive months), <fam>_red, and the overall 'rating'."""
    params = params or PARAMS
    active = (ACTIVE if active is None else set(active)) - INFO_ONLY
    out = pd.DataFrame(index=p.index)
    for fam, prm in params.items():
        f = family_fires(p, fam, prm).fillna(False).astype(bool)
        out[fam] = f
        out[f"{fam}_run"] = _run_length(f, p)
        persistent = f & (out[f"{fam}_run"] >= RED_PERSIST)
        if fam in ("oil_trips", "pitch_trips"):
            red = persistent & (_col(p, f"{fam.split('_')[0]}_ep_6m") >= RED_TRIP_MULT * prm["n"])
        else:
            red = persistent & (_col(p, REL_COL[fam]).abs() >= RED_REL)
        if fam == "pump":
            red |= f & (_col(p, "pump_rise") >= RED_PUMP_BAR)
        if fam in NEVER_RED:
            red &= False
        out[f"{fam}_red"] = red
    act = [f for f in params if f in active]
    n_amber = out[act].sum(axis=1) if act else pd.Series(0, index=p.index)
    # two independent signatures agreeing (trip repeats of the same system as an abnormal-state family don't count twice)
    groups = {"oil": ["oil_abn", "pump", "oil_trips"], "pitch": ["pitch_abn", "pitch_trips"], "bearing": ["bearing_abn"],
              "perf": ["perf_abn"]}
    n_sys = sum(out[[f for f in fs if f in act]].any(axis=1).astype(int) for fs in groups.values() if any(f in act for f in fs))
    any_red = out[[f"{f}_red" for f in act]].any(axis=1) if act else pd.Series(False, index=p.index)
    out["rating"] = np.where(any_red | (n_sys >= 2), "RED", np.where(n_amber > 0, "AMBER", "GREEN"))
    return out

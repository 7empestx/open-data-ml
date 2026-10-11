"""Stage 4: amber/red rating, one-line plain-English reasons, a suggested check and a confidence level per turbine.

The rating comes from the calibrated rules in rules.py, applied to each turbine's latest as-of row of the indicator
panel (indicators.py). Only rule families whose flags concentrated before real events in 2017-2020 (and were checked
on 2021-2024, see reports/fleet_proof/calibration.md) set the flag:

  pump         full-load gear-oil pump pressure risen >= 1 bar above the turbine's own 12-month baseline AND a clear
               outlier vs the other turbines (robust z >= 5)                                 -> AMBER; >= 2 bar -> RED
  oil_trips    >= 3 oil-system trip episodes in 6 months                                     -> AMBER
  pitch_trips  >= 6 pitch trip episodes in 6 months                                          -> AMBER
  RED also when an amber trip rule held 2 month-ends running with 3x the amber count and a trip in the last 30
  days, or two independent systems are amber at once.
Sensor problems (drift vs the fleet over the last 3 months, a sensor frozen on > 2% of the last 90 days) are AMBER too: they are not failure predictions but are directly
checkable and hide faults. Everything else (availability, model-based abnormal days, missing data) is reported as a
note: shown with its numbers, but it does not set the colour, because it showed no reliable lead on events.

Confidence (how much to trust the rating, or the absence of one):
  points: history >= 36 months +2, 24-35 +1; window coverage >= 95% +1; walk-forward models +1 (cross-fit 0,
  none -1); alarm log +1 (the trip rules need it); fleet of 4+ turbines +1 (peer comparison possible).
  High >= 5, Medium 3-4, Low <= 2.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import rules

MONITORED = {"gear_oil_temp_c", "gear_oil_inlet_temp_c", "gear_oil_inlet_pressure_bar", "main_bearing_front_temp_c",
             "main_bearing_rear_temp_c", "wind_speed_ms", "ambient_temp_c", "nacelle_temp_c"}
COMP = {"oil": "gearbox oil system", "pitch": "pitch system", "main_bearing": "main bearing", "performance": "power curve"}


def _v(r, k):
    v = r.get(k) if hasattr(r, "get") else None
    return None if v is None or (isinstance(v, float) and np.isnan(v)) else v


def _months(n: int) -> str:
    return f"{n} month{'s' if n != 1 else ''}"


def _trip_detail(ev: pd.DataFrame | None, tid: str, kind: str, asof: pd.Timestamp) -> tuple[str, str]:
    """Most frequent trip message in the last 6 months, and the date of the last trip."""
    if ev is None:
        return "", ""
    from .. import trip_features as tf
    tr = tf.trips(ev[ev["turbine_id"] == tid], kind)
    tr = tr[(tr["start"] > asof - pd.Timedelta(days=180)) & (tr["start"] <= asof + pd.Timedelta(days=1))]
    if not len(tr):
        return "", ""
    top = tr["message"].fillna(tr["code"].astype(str)).value_counts()
    return f"'{top.index[0]}' ({top.iloc[0]} trips)", f"{tr['start'].max():%d %b %Y}"


def _pump_precedent(P: pd.DataFrame, ev: pd.DataFrame | None, tid: str, run_start: pd.Timestamp) -> str:
    """Earlier pump build-ups of >= RED_PUMP_BAR anywhere in the fleet (before this one started) and what followed."""
    prior = P[(P["pump_rise"] >= rules.RED_PUMP_BAR) & (P["as_of"] < run_start)]
    if not len(prior):
        return ""
    from .. import trip_features as tf
    out = []
    for t, g in prior.sort_values("as_of").groupby("turbine_id"):
        first, top = g["as_of"].iloc[0], g["pump_rise"].max()
        after = ""
        if ev is not None:
            e = ev[ev["turbine_id"] == t]
            tr = tf.trips(e, "oil")
            tr = tr[(tr["start"] > first - pd.Timedelta(days=30)) & (tr["start"] <= first + pd.Timedelta(days=120))]
            mt = e[(e["event_class"] == "maintenance") & e["is_stop"] & (e["duration"] >= pd.Timedelta(hours=24))
                   & (e["start"] > first) & (e["start"] <= first + pd.Timedelta(days=120))]
            bits = []
            if len(tr):
                bits.append(f"{len(tf.trip_episodes(tr))} oil-pressure trip episodes")
            if len(mt):
                bits.append(f"a {mt['duration'].iloc[0].total_seconds() / 3600:.0f} h service stop on {mt['start'].iloc[0]:%d %b %Y}")
            after = " followed by " + " and ".join(bits) if bits else ""
        out.append(f"{'this turbine' if t == tid else t} (+{top:.1f} bar, {first:%b %Y}{after})")
    return "; ".join(out[:3])


def assess(P: pd.DataFrame, R: pd.DataFrame, metrics_turbines: dict, health: dict, has_log: bool,
           ev: pd.DataFrame | None, n_turbines: int) -> dict:
    """Rating, reasons and confidence for every turbine in metrics_turbines. P = indicator panel, R = rules.apply(P)."""
    act = rules.ACTIVE - rules.INFO_ONLY
    out = {}
    for tid, r in metrics_turbines.items():
        rows = P.index[P["turbine_id"] == tid]
        red, amb, notes = [], [], []          # (category, technical text, plain reason, suggested check)
        rating = "GREEN"
        if len(rows):
            i = P.loc[rows, "as_of"].idxmax()
            x, f = P.loc[i], R.loc[i]
            asof = x["as_of"]
            peers = P[(P["month"] == x["month"]) & (P["turbine_id"] != tid)]

            def peer_med(c):
                v = peers[c].dropna() if c in peers else pd.Series(dtype=float)
                return float(v.median()) if len(v) >= 3 else None
            rating = f["rating"]
            if "pump" in act and f["pump"]:
                rise, now, run = x["pump_rise"], x["pump_now"], int(f["pump_run"])
                start = P.loc[rows][P.loc[rows, "as_of"] <= asof].sort_values("as_of")
                start = start[start["pump_rise"] >= 0.5]
                pm = peer_med("pump_rise")
                prec = _pump_precedent(P, ev, tid, asof - pd.Timedelta(days=31 * run))
                is_red = bool(f["pump_red"])
                plain = (f"Gear-oil pump pressure at full load is {rise:.1f} bar above its own 12-month baseline (now {now:.1f} bar)"
                         + (f", while the other turbines are at {pm + 0.0:+.1f} bar" if pm is not None else "")
                         + (f"; flagged {_months(run)} running" if run > 1 else "") + ".")
                chk = ("Inspect the gearbox oil filter and pump: read the filter differential pressure, check the bypass "
                       "and pressure-relief valve, take an oil sample for particles")
                chk += f". The same build-up was seen before in {prec}." if prec else "."
                (red if is_red else amb).append(("oil", f"pump pressure +{rise:.1f} bar vs baseline (peer z {x['pump_rise_rel']:.1f})", plain, chk))
            for k, lab, chk0 in (("oil", "oil-system", "Inspect the gearbox oil circuit: filter, pump, cooler, oil level and the pressure switch"),
                                 ("pitch", "pitch", "Inspect the pitch system: drives, batteries/accumulators, slip ring and blade-bearing play")):
                fam = f"{k}_trips"
                if fam in act and f[fam]:
                    n, n1, run = int(x[f"{k}_ep_6m"]), int(x.get(f"{k}_ep_1m", 0) or 0), int(f[f"{fam}_run"])
                    top, last = _trip_detail(ev, tid, k, asof)
                    pm = peer_med(f"{k}_ep_6m")
                    plain = (f"Tripped on {lab} faults in {n} separate episodes in the last 6 months"
                             + (f" (other turbines: median {pm:.0f})" if pm is not None else "")
                             + (f"; most often {top}" if top else "") + (f"; last on {last}" if last else "") + ".")
                    chk = chk0
                    if n1 == 0:
                        chk = "No trip in the last 30 days: confirm in the work orders that the cause was repaired. " + chk0
                        if k == "oil" and _v(x, "pump_rise") is not None and x["pump_rise"] <= -1.0:
                            chk = (f"No trip in the last 30 days and pump pressure dropped {abs(x['pump_rise']):.1f} bar, which "
                                   "looks like a repair or oil/filter change: confirm it in the work orders. If not repaired: " + chk0[0].lower() + chk0[1:])
                    is_red = bool(f[f"{fam}_red"])
                    if is_red:
                        plain = plain[:-1] + f", for {_months(run)} running and still tripping."
                    (red if is_red else amb).append((k, f"{n} {lab} trip episodes in 6 months", plain, chk + "."))
            # notes: shown, never colour-setting
            a6, ar = _v(x, "avail_6m"), _v(x, "avail_6m_rel")
            if a6 is not None and a6 < 0.95 and (ar is None or ar <= -3):
                pm = peer_med("avail_6m")
                cause = r.get("top_fault_cause")
                notes.append(("availability", f"availability {a6:.1%} (6 months)",
                              f"Availability was {a6:.1%} over the last 6 months" + (f" vs {pm:.1%} for the other turbines" if pm else "")
                              + (f"; largest fault cause: {cause}" if cause else "") + ". This is past downtime, not a forecast.",
                              "Check that the cause of the long stops is closed out."))
            for c in ("oil", "pitch", "main_bearing", "performance"):
                v, rel, k3 = _v(x, f"abn_{c}_3m"), _v(x, f"abn_{c}_3m_rel"), _v(x, f"abn_{c}_months")
                if v is not None and v >= 0.2 and (rel or 0) >= 3 and (k3 or 0) >= 2:
                    extra = ""
                    pr = _v(x, "pump_rise")
                    if c == "oil" and pr is not None and pr <= -1.0:
                        extra = f", probably because pump pressure dropped {abs(pr):.1f} bar (oil or filter change?)"
                    elif c == "oil" and pr is not None and pr >= 1.0:
                        extra = ", in line with the pump-pressure build-up"
                    notes.append((c, f"abnormal {COMP[c]} model residuals on {v:.0%} of days (3 months)",
                                  f"Its {COMP[c]} behaved unlike its own normal-behaviour model on {v:.0%} of days in the last "
                                  f"3 months{extra}.",
                                  "Compare with the trends in sections 3-4 at the next routine visit."))
        cov = _v(r, "coverage_window")
        if cov is not None and 1 - cov > 0.02:
            notes.append(("data", f"data missing {1 - cov:.1%}", f"{1 - cov:.1%} of its SCADA data is missing in the window.",
                          "Ask the SCADA provider about the gaps (communication or logger problems hide faults)."))
        for sig, thr, unit, lab in (("ambient_temp_c", 1.5, "°C", "ambient temperature"), ("wind_speed_ms", 0.05, "", "wind speed")):
            v = _v(r, f"drift_{sig}")
            if v is not None and abs(v) >= thr:
                txt = f"{v:+.1f} {unit}" if unit else f"{v:+.0%}"
                amb.append(("sensor", f"{lab} sensor drift {txt} vs fleet",
                            f"Its {lab} sensor has drifted {txt} away from the other turbines over the last 3 months.",
                            "Recalibrate or replace the sensor (the models and power-curve checks rely on it)."))
        stuck = [s for s in r.get("stuck_sensors_recent", []) if s in MONITORED]
        if stuck:
            amb.append(("sensor", f"stuck sensor(s) in the last 90 days: {', '.join(stuck)}",
                        f"Sensor(s) {', '.join(stuck)} have been frozen at a constant value for over 2% of the last 90 days.",
                        "Check the sensor, its wiring and the logger channel."))
        old = [s for s in r.get("stuck_sensors", []) if s in MONITORED and s not in stuck]
        if old:
            notes.append(("data", f"stuck sensor(s) earlier in the window: {', '.join(old)}",
                          f"Sensor(s) {', '.join(old)} were frozen for a while earlier in the window but read normally now.",
                          "None needed if the readings stay live."))
        if rating == "GREEN" and amb:
            rating = "AMBER"
        if rating == "RED" and not red:       # two independent systems amber at once
            red, amb = amb, []
            red[-1] = (*red[-1][:2], red[-1][2][:-1] + "; two independent systems are flagged at once.", red[-1][3])
        # confidence
        pts, why = 0, []
        hm = r.get("history_months", 0)
        pts += 2 if hm >= 36 else 1 if hm >= 24 else 0
        why.append(f"{hm:.0f} months of history")
        if (cov or 0) >= 0.95:
            pts += 1
        else:
            why.append(f"only {cov:.0%} data coverage")
        sch = (health or {}).get(tid, {}).get("scheme", "none")
        pts += {"walk-forward": 1, "cross-fit": 0}.get(sch, -1)
        why.append({"walk-forward": "models trained on earlier years", "cross-fit": "short-history models (cross-fit)",
                    "none": "no models (history too short)"}.get(sch, sch))
        if has_log:
            pts += 1
        else:
            why.append("no alarm log (trip rules unavailable)")
        if n_turbines >= 4:
            pts += 1
        else:
            why.append(f"only {n_turbines} turbines (no peer comparison)")
        conf = "High" if pts >= 5 else "Medium" if pts >= 3 else "Low"
        out[tid] = {"flag": rating, "red": red, "amber": amb, "notes": notes, "confidence": conf, "confidence_points": pts,
                    "confidence_notes": why, "reasons": "; ".join(t[1] for t in red + amb) or "no trigger",
                    "notes_text": "; ".join(t[1] for t in notes)}
    return out

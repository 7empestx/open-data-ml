"""Stage 4: RAG flag, plain-language reasons and a confidence level per turbine.

Rules (the hand-built report's rules, applied to each turbine's last 24 months; heuristics, not a calibrated risk):
  RED   technical availability < 95% (alarm log needed); >= 8 oil-system or >= 8 pitch trip episodes; full-load
        gear-oil pump pressure in the last month >= 2.0 bar above its baseline; abnormal oil state on >= 30% of
        operating days in the final year.
  AMBER availability < 97%; >= 4 oil or pitch episodes; pump pressure rise >= 1.0 bar; abnormal oil days >= 10%;
        gear-oil temperature model error in the final year >= 1.5x its pre-window level; data missing > 2%.
  AMBER (new, generic triggers, never RED on their own): under-performance vs the turbine's own power-curve model on
        >= 20% of final-year days; abnormal main-bearing or pitch residuals on >= 30% of final-year days; a sensor
        drifting vs the fleet (ambient temperature >= 1.5 °C, wind speed >= 5%); a stuck sensor (>= 1% of
        window rows frozen) on a monitored signal.
Confidence (how much to trust the flag, or the absence of one):
  points: history >= 36 months +2, 24-35 +1; window coverage >= 95% +1; walk-forward models +1 (cross-fit 0,
  none -1); alarm log +1; for a flagged turbine, two or more independent triggers +1.
  High >= 4, Medium 2-3, Low <= 1.
"""
from __future__ import annotations
import numpy as np

MONITORED = {"gear_oil_temp_c", "gear_oil_inlet_temp_c", "gear_oil_inlet_pressure_bar", "main_bearing_front_temp_c",
             "main_bearing_rear_temp_c", "wind_speed_ms", "ambient_temp_c", "nacelle_temp_c"}


def _v(r, k):
    v = r.get(k)
    return None if v is None or (isinstance(v, float) and np.isnan(v)) else v


def score(r: dict, health: dict | None, has_log: bool) -> dict:
    red, amb = [], []          # (category, technical text, plain text, action)
    a = _v(r, "avail_time")
    if a is not None:
        t = (f"technical availability {a:.1%}", f"was down for faults or maintenance {1 - a:.1%} of the time",
             "review the fault history below and the open work orders")
        (red if a < 0.95 else amb if a < 0.97 else []).append(("availability", *t))
    for k, lab in (("oil", "oil-system"), ("pitch", "pitch")):
        v = _v(r, f"{k}_ep_window")
        if v is not None and v >= 4:
            t = (f"{v} {lab} trip episodes", f"tripped on {lab} faults in {v} separate episodes in two years",
                 "inspect the oil circuit (filter, pump, cooler, level)" if k == "oil" else "inspect pitch drives, batteries and slip ring")
            (red if v >= 8 else amb).append((k, *t))
    pr = _v(r, "pump_rise")
    if pr is not None and pr >= 1.0:
        t = (f"pump pressure +{pr:.1f} bar vs baseline", f"needs {pr:.1f} bar more gear-oil pump pressure at full load than earlier in its life",
             "check the oil filter differential pressure and cooler; take an oil sample")
        (red if pr >= 2.0 else amb).append(("oil", *t))
    ab = _v(r, "abn_oil_final_year")
    if ab is not None and ab >= 0.10:
        t = (f"abnormal oil state {ab:.0%} of final-year days", f"behaved abnormally in the gearbox oil system on {ab:.0%} of days last year",
             "trend oil temperature and pressure against the sister turbines; take an oil sample")
        (red if ab >= 0.30 else amb).append(("oil", *t))
    mr = _v(r, "oil_temp_mae_ratio")
    if mr is not None and mr >= 1.5:
        amb.append(("oil", f"oil-temp model error {mr:.1f}x baseline", f"gear-oil temperature has become {mr:.1f}x harder to predict than before",
                    "check the oil cooler fan and thermostat"))
    cov = _v(r, "coverage_window")
    if cov is not None and 1 - cov > 0.02:
        amb.append(("data", f"data missing {1 - cov:.1%}", f"has {1 - cov:.1%} of its SCADA data missing",
                    "ask the SCADA provider about the gaps (communication or logger problems hide faults)"))
    perf = _v(r, "abn_performance_final_year")
    if perf is not None and perf >= 0.20:
        amb.append(("performance", f"under-performance {perf:.0%} of final-year days",
                    f"produced clearly less than its own power curve predicts on {perf:.0%} of days last year",
                    "check for derating, pitch or yaw misalignment and anemometer problems"))
    for g, lab, act in (("main_bearing", "main-bearing temperature", "check main-bearing grease and vibration (CMS) data"),
                        ("pitch", "pitch system", "check pitch motor temperatures and blade-angle asymmetry")):
        v = _v(r, f"abn_{g}_final_year")
        if v is not None and v >= 0.30:
            amb.append((g, f"abnormal {lab} residuals {v:.0%} of final-year days", f"ran with an abnormal {lab} on {v:.0%} of days last year", act))
    for sig, thr, unit, lab in (("ambient_temp_c", 1.5, "°C", "ambient temperature"), ("wind_speed_ms", 0.05, "", "wind speed")):
        v = _v(r, f"drift_{sig}")
        if v is not None and abs(v) >= thr:
            txt = f"{v:+.1f} {unit}" if unit else f"{v:+.0%}"
            amb.append(("sensor", f"{lab} sensor drift {txt} vs fleet", f"has a {lab} sensor that drifted {txt} away from the other turbines",
                        "recalibrate or replace the sensor (models and power-curve checks rely on it)"))
    stuck = [s for s in r.get("stuck_sensors", []) if s in MONITORED]
    if stuck:
        amb.append(("sensor", f"stuck sensor(s): {', '.join(stuck)}", f"has sensors that stopped changing ({', '.join(stuck)})",
                    "check the sensor wiring and logger"))
    flag = "RED" if red else "AMBER" if amb else "GREEN"
    # confidence
    pts, why = 0, []
    hm = r.get("history_months", 0)
    pts += 2 if hm >= 36 else 1 if hm >= 24 else 0
    why.append(f"{hm:.0f} months of history")
    if (cov or 0) >= 0.95:
        pts += 1
    else:
        why.append(f"only {cov:.0%} data coverage")
    sch = (health or {}).get("scheme", "none")
    pts += {"walk-forward": 1, "cross-fit": 0}.get(sch, -1)
    why.append({"walk-forward": "models trained on earlier years", "cross-fit": "short-history models (cross-fit)",
                "none": "no models (history too short)"}.get(sch, sch))
    if has_log:
        pts += 1
    else:
        why.append("no alarm log")
    cats = {c for c, *_ in red + amb}
    if flag != "GREEN" and len(cats) >= 2:
        pts += 1
        why.append("several independent indicators agree")
    conf = "High" if pts >= 4 else "Medium" if pts >= 2 else "Low"
    return {"flag": flag, "red": red, "amber": amb, "confidence": conf, "confidence_points": pts, "confidence_notes": why,
            "reasons": "; ".join(t[1] for t in red + amb) or "no trigger"}

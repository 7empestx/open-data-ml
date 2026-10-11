"""Unit normalisation, conversion to the canonical units, and unit-suspicion heuristics."""
from __future__ import annotations
import re
import numpy as np
import pandas as pd

# alias -> normalised unit token
_ALIASES = {
    "c": "degC", "°c": "degC", "degc": "degC", "deg_c": "degC", "celsius": "degC", "℃": "degC",
    "f": "degF", "°f": "degF", "degf": "degF", "deg_f": "degF", "fahrenheit": "degF",
    "k": "K", "kelvin": "K",
    "w": "W", "kw": "kW", "mw": "MW",
    "wh": "Wh", "kwh": "kWh", "mwh": "MWh",
    "bar": "bar", "mbar": "mbar", "kpa": "kPa", "pa": "Pa", "psi": "psi", "mpa": "MPa", "hpa": "hPa",
    "m/s": "m/s", "ms": "m/s", "m s-1": "m/s", "km/h": "km/h", "kmh": "km/h", "kph": "km/h", "mph": "mph", "kn": "kn", "kt": "kn", "knots": "kn",
    "rpm": "rpm", "1/min": "rpm", "u/min": "rpm", "min-1": "rpm", "rad/s": "rad/s",
    "°": "deg", "deg": "deg", "degree": "deg", "degrees": "deg", "rad": "rad",
    "%": "percent", "percent": "percent", "fraction": "fraction", "1": "fraction",
}

# (from, to) -> function
_CONV = {
    ("degF", "degC"): lambda x: (x - 32.0) * 5.0 / 9.0,
    ("K", "degC"): lambda x: x - 273.15,
    ("W", "kW"): lambda x: x / 1000.0, ("MW", "kW"): lambda x: x * 1000.0,
    ("Wh", "kWh"): lambda x: x / 1000.0, ("MWh", "kWh"): lambda x: x * 1000.0,
    ("kPa", "bar"): lambda x: x / 100.0, ("Pa", "bar"): lambda x: x / 1e5, ("mbar", "bar"): lambda x: x / 1000.0,
    ("hPa", "bar"): lambda x: x / 1000.0, ("MPa", "bar"): lambda x: x * 10.0, ("psi", "bar"): lambda x: x * 0.0689475729,
    ("km/h", "m/s"): lambda x: x / 3.6, ("mph", "m/s"): lambda x: x * 0.44704, ("kn", "m/s"): lambda x: x * 0.514444,
    ("rad/s", "rpm"): lambda x: x * 60.0 / (2 * np.pi),
    ("rad", "deg"): np.rad2deg,
    ("percent", "fraction"): lambda x: x / 100.0,
}

# candidate units per quantity, used by auto-detection
CANDIDATES = {
    "temperature": ["degC", "degF", "K"], "power": ["kW", "W", "MW"], "energy": ["kWh", "Wh", "MWh"],
    "pressure": ["bar", "kPa", "mbar", "psi", "Pa"], "speed": ["m/s", "km/h", "mph"],
    "rotational_speed": ["rpm", "rad/s"], "angle": ["deg", "rad"], "fraction": ["fraction", "percent"],
}


def normalize_unit(u: str | None) -> str | None:
    if u is None:
        return None
    t = str(u).strip()
    if t in KNOWN_UNITS:
        return t
    return _ALIASES.get(t.lower().replace(" ", ""), t)


_CONV_TARGETS = {b for _, b in _CONV} | {"degC", "kW", "kWh", "bar", "m/s", "rpm", "deg", "fraction"}
KNOWN_UNITS = _CONV_TARGETS | {a for a, _ in _CONV}

_UNIT_IN_NAME = re.compile(r"[\(\[]\s*([^\)\]]+?)\s*[\)\]]\s*$|[_\s](degC|degF|kW|MW|W|kPa|bar|psi|rpm|m/s|ms|deg|C|F)$", re.I)


def unit_from_name(col: str) -> str | None:
    """Unit token written in a column name: 'Power (kW)', 'Temp [°F]', 'Oil_Temp_degF'."""
    m = _UNIT_IN_NAME.search(str(col))
    if not m:
        return None
    u = normalize_unit(m.group(1) or m.group(2))
    return u if u in KNOWN_UNITS else None


def convert(x: pd.Series, src: str, dst: str) -> pd.Series:
    src, dst = normalize_unit(src), normalize_unit(dst)
    if src == dst or src is None:
        return x
    f = _CONV.get((src, dst))
    if f is None:
        raise ValueError(f"no conversion from {src!r} to {dst!r}")
    return f(x)


def split_switch(x: pd.Series, low_unit: str, high_unit: str, dst: str, threshold: float) -> tuple[pd.Series, pd.Series]:
    """Per-row unit for signals whose logging unit changes over time (e.g. oil pressure bar <-> kPa).
    Rows with |x| > threshold are taken as `high_unit`, others as `low_unit`. Returns (converted, is_high)."""
    hi = x.abs() > threshold
    out = convert(x.where(~hi), low_unit, dst).fillna(convert(x.where(hi), high_unit, dst))
    return out, hi.fillna(False)


def guess_unit(x: pd.Series, quantity: str, canonical: str, plausible: tuple[float, float]) -> tuple[str, float, str]:
    """Pick the candidate unit whose converted values best fit the plausible range.
    Returns (unit, score 0-1, reason). Uses robust percentiles so a few spikes don't decide."""
    v = pd.to_numeric(x, errors="coerce").dropna()
    if len(v) == 0:
        return canonical, 0.0, "no numeric values"
    lo, hi = plausible
    q = v.quantile([0.01, 0.5, 0.99]).to_numpy()
    best = (canonical, -1.0, "")
    for u in CANDIDATES.get(quantity, [canonical]):
        try:
            c = convert(pd.Series(q), u, canonical).to_numpy()
        except ValueError:
            continue
        inside = float(np.mean((c >= lo) & (c <= hi)))
        # prefer units that put the median in a "typical" part of the range (not squashed near zero)
        span = hi - max(lo, 0)
        typical = 1.0 if span <= 0 else float(min(1.0, abs(c[1]) / (0.02 * span) if c[1] != 0 else 0.0))
        score = inside * (0.7 + 0.3 * typical) * (1.0 if u == canonical else 0.97)
        if score > best[1]:
            best = (u, score, f"p1/p50/p99 = {q[0]:.3g}/{q[1]:.3g}/{q[2]:.3g} -> {c[0]:.3g}/{c[1]:.3g}/{c[2]:.3g} {canonical}")
    return best[0], max(best[1], 0.0), best[2]


def unit_suspicions(name: str, x: pd.Series, quantity: str, canonical: str, plausible: tuple[float, float],
                    ts: pd.Series | None = None) -> list[str]:
    """Human-readable warnings about values that look like the wrong unit AFTER conversion."""
    out = []
    v = pd.to_numeric(x, errors="coerce")
    vv = v.dropna()
    if len(vv) < 50:
        return out
    lo, hi = plausible
    p50, p99 = vv.median(), vv.quantile(0.99)
    if quantity == "temperature":
        if name == "ambient_temp_c" and p50 > 35:
            out.append(f"{name}: median {p50:.1f} °C is implausible for ambient air; data may be in °F")
        elif p50 > 150:
            out.append(f"{name}: median {p50:.1f}; looks like Kelvin or °F")
    if quantity == "power" and p99 > 0 and p99 < 10 and name == "power_kw":
        out.append(f"{name}: p99 {p99:.3g} kW; data may be in MW")
    if quantity == "power" and p99 > 50_000:
        out.append(f"{name}: p99 {p99:.3g} kW; data may be in W")
    if quantity == "pressure":
        big = vv.abs() > max(hi * 2, 20)
        share = float(big.mean())
        if 0.02 < share < 0.98:
            msg = f"{name}: {share:.0%} of values exceed {max(hi * 2, 20):g} bar; the logging unit probably switches between bar and kPa"
            if ts is not None:
                t = ts.loc[vv.index]
                flips = big.astype(int).diff().fillna(0).ne(0)
                dates = t[flips].dt.strftime("%Y-%m-%d").unique()[:6]
                if len(dates):
                    msg += f" (switches around {', '.join(dates)})"
            out.append(msg + "; use `unit_switch` in the mapping")
        elif share >= 0.98:
            out.append(f"{name}: almost all values exceed {max(hi * 2, 20):g} bar; data is probably in kPa")
    if quantity == "speed" and p99 > hi:
        out.append(f"{name}: p99 {p99:.3g} m/s; data may be in km/h or mph")
    if quantity == "angle" and name.startswith("pitch") and p99 < 2 and vv.max() < 1.6 and vv.min() > -0.2:
        out.append(f"{name}: all values within 0-1.6; pitch may be in radians")
    if quantity == "fraction" and p99 > 1.5:
        out.append(f"{name}: values up to {p99:.3g}; probably percent rather than 0-1")
    return out

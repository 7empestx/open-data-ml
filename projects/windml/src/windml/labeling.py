"""Failure labeling from Greenbyte status/alarm logs (Kelmarsh, Penmanshiel).

Pipeline
  1. parse_events(farm)      -> one row per log event (start, end, duration, code, message, categories)
  2. classify_events(events) -> adds `event_class` (fault / curtailment / maintenance / grid / weather /
                                routine / other / info), `component`, `is_major_fault`
  3. label_grid(scada, events, windows) -> adds in_any_stop, in_fault, in_major_fault,
                                pre_fault_<N>d and days_to_next_major_fault to the 10-minute grid

Classification is rule based and transparent: first the message keyword rules, then the
manufacturer's 'Service contract category', then the 'IEC category'. Edit the rule tables
below to tune it. Only `Status == 'Stop'` events define stops; Warnings and Informational
events are kept (event_class 'info' / original class) but do not set stop labels.
"""
from __future__ import annotations
import re
import numpy as np
import pandas as pd
from . import greenbyte as gb

# --- component keyword rules (regex on message, case-insensitive) -----------------------------
COMPONENT_RULES = [
    ("gearbox", r"gear|drive train|drivetrain"),
    ("generator", r"generator|gen\.|brushes|slip ring"),
    ("bearing", r"bearing"),
    ("pitch", r"pitch|blade|axis \d|charging circuit|\bBP\s?\d+|battery charge cycle"),
    ("converter", r"converter|conv\.|inverter|igbt|chopper"),
    ("yaw", r"\byaw|uncontrolled yaw|cable twist|autounwind"),
    ("hydraulics", r"hydraulic|accumulator"),
    ("brake", r"brake"),
    ("sensor_met", r"anemometer|vane|wind speed sensor"),
    ("tower", r"tower oscillation|tower resonance|vibration"),
    ("rotor", r"overspeed|rotor"),
    ("electrical", r"safety chain|smoke|overvoltage|undervoltage|transformer|switchgear|fuse"),
    ("control_comm", r"comm\.|communication|time synchronization|timeout"),
]
MAJOR_COMPONENTS = {"gearbox", "generator", "bearing", "converter", "pitch", "yaw", "hydraulics"}

# --- event class rules ---------------------------------------------------------------------------
MSG_CLASS_RULES = [  # checked first, in order
    ("routine", r"battery test|stop battery test|cable autounwind|oil flushing|test brake program|brake program|charging cycle"),
    ("maintenance", r"manual stop|manual brake|service|maintenance"),
    ("curtailment", r"externally stopped|externally reduced|curtail|remote stop|power limitation|noise|shadow|bat |bird"),
    ("grid", r"grid loss|grid|mains|overvoltage|undervoltage|frequency (high|low)|ready for connection|load rejection"),
    ("weather", r"icing|ice|max\. wind speed|wind < power|deviation.*wind ?dir|low wind|storm|temperature low|cold"),
]
SERVICE_CLASS = {
    "External stop (grid)": "grid", "External stop (climate)": "weather", "External stop (low wind speed)": "weather",
    "Manual stop (service)": "maintenance", "Remote stop": "curtailment", "Techical Curtailments": "curtailment",
    "Operating states": "routine", "System OK": "other",
    "Sensor error": "fault", "Electrical error": "fault", "Generator and Converter errors": "fault",
    "Pitch errors": "fault", "Temperature error": "fault", "Mechanical error": "fault", "Safety stop of WEC": "fault",
    "Safety chain": "fault", "Overspeed": "fault", "Repeated error": "fault", "Warnings": "fault",
}
IEC_CLASS = {
    "Forced outage": "fault", "Scheduled Maintenance": "maintenance", "Out of Electrical Specification": "grid",
    "Out of Environmental Specification": "weather", "Technical Standby": "routine", "Partial Performance": "curtailment",
}


def _parse_duration(s: pd.Series) -> pd.Series:
    s = s.where(s.str.match(r"^\d+:\d{2}:\d{2}$", na=False))
    parts = s.str.split(":", expand=True)
    if parts.shape[1] < 3:
        return pd.Series(pd.NaT, index=s.index, dtype="timedelta64[ns]")
    secs = parts[0].astype(float) * 3600 + parts[1].astype(float) * 60 + parts[2].astype(float)
    return pd.to_timedelta(secs, unit="s")


def parse_events(farm: str) -> pd.DataFrame:
    frames = []
    for f in gb.status_files(farm):
        raw = gb.read_status(f)
        meta = raw.attrs.get("meta", {})
        tz = meta.get("Time zone", "UTC")
        end_of_file = meta.get("interval_end")
        df = pd.DataFrame({
            "farm": farm,
            "turbine_id": raw["turbine_id"],
            "start": pd.to_datetime(raw["Timestamp start"], errors="coerce").dt.tz_localize(tz).dt.tz_convert("UTC"),
            "end": pd.to_datetime(raw["Timestamp end"].replace("-", None), errors="coerce").dt.tz_localize(tz).dt.tz_convert("UTC"),
            "duration_logged": _parse_duration(raw["Duration"].fillna("")),
            "status": raw["Status"],
            "code": pd.to_numeric(raw["Code"], errors="coerce").astype("Int64"),
            "message": raw["Message"].fillna(""),
            "comment": raw["Comment"] if "Comment" in raw else None,
            "service_category": raw.get("Service contract category"),
            "iec_category": raw.get("IEC category"),
        })
        df["instantaneous"] = df["end"].isna() & df["duration_logged"].isna()
        # open-ended stops (no end, but not marked instantaneous with '-') run to the end of the file
        df["end_filled"] = df["end"]
        if end_of_file is not None:
            df.loc[df["end"].isna() & (df["status"] == "Stop") & ~df["instantaneous"], "end_filled"] = end_of_file
        df["end_filled"] = df["end_filled"].fillna(df["start"])
        df["duration"] = df["end_filled"] - df["start"]
        frames.append(df)
    ev = pd.concat(frames, ignore_index=True).sort_values(["turbine_id", "start"]).reset_index(drop=True)
    ev["service_category_clean"] = ev["service_category"].fillna("").str.replace(r"\s*\(\d+\)\s*$", "", regex=True).str.strip()
    return ev


def _first_match(msg: str, rules) -> str | None:
    for name, pat in rules:
        if re.search(pat, msg, flags=re.I):
            return name
    return None


def classify_events(ev: pd.DataFrame, major_min_duration: str = "1h", episode_gap: str = "24h") -> pd.DataFrame:
    ev = ev.copy()
    ev["component"] = ev["message"].map(lambda m: _first_match(m, COMPONENT_RULES) or "unspecified")

    def cls(row) -> str:
        if row["status"] == "Informational":
            return "info"
        if row["status"] == "Communication":
            return "other"
        if row["status"] == "Curtailment":
            return "curtailment"
        c = _first_match(row["message"], MSG_CLASS_RULES)
        if c:
            return c
        c = SERVICE_CLASS.get(row["service_category_clean"])
        if c and c != "other":
            return c
        c = IEC_CLASS.get(row["iec_category"] if isinstance(row["iec_category"], str) else "")
        if c:
            return c
        return "fault" if row["status"] == "Warning" else "other"

    ev["event_class"] = ev.apply(cls, axis=1)
    ev["is_stop"] = ev["status"].eq("Stop")
    ev["is_fault_stop"] = ev["is_stop"] & ev["event_class"].eq("fault")
    ev["is_major_component"] = ev["component"].isin(MAJOR_COMPONENTS)
    ev["is_major_fault"] = ev["is_fault_stop"] & ev["is_major_component"] & (ev["duration"] >= pd.Timedelta(major_min_duration))
    # merge major faults on the same turbine that start within `episode_gap` of the previous one's end
    ev["major_episode"] = pd.NA
    ep = 0
    for tid, g in ev[ev["is_major_fault"]].sort_values("start").groupby("turbine_id"):
        last_end = None
        for i, r in g.iterrows():
            if last_end is None or r["start"] - last_end > pd.Timedelta(episode_gap):
                ep += 1
            ev.at[i, "major_episode"] = ep
            last_end = r["end_filled"] if last_end is None else max(last_end, r["end_filled"])
    ev["major_episode"] = ev["major_episode"].astype("Int64")
    return ev


def _mark(grid_ts: np.ndarray, starts: np.ndarray, ends: np.ndarray, step: np.timedelta64) -> np.ndarray:
    """Bins [t, t+step) overlapping any [start, end] (end inclusive for instantaneous events)."""
    m = np.zeros(len(grid_ts), dtype=bool)
    for s, e in zip(starts, ends):
        i0 = np.searchsorted(grid_ts, s - step, side="right")
        i1 = np.searchsorted(grid_ts, e, side="right")
        m[i0:i1] = True
    return m


def label_grid(scada: pd.DataFrame, ev: pd.DataFrame, windows_days=(7, 14, 30), freq: str = "10min") -> pd.DataFrame:
    step = np.timedelta64(pd.Timedelta(freq))
    out = []
    for tid, g in scada.groupby("turbine_id", observed=True, sort=False):
        g = g.sort_values("timestamp").copy()
        ts = g["timestamp"].dt.tz_convert("UTC").dt.tz_localize(None).to_numpy("datetime64[ns]")
        e = ev[ev["turbine_id"] == tid]
        s_ = lambda d: d["start"].dt.tz_localize(None).to_numpy("datetime64[ns]")
        e_ = lambda d: d["end_filled"].dt.tz_localize(None).to_numpy("datetime64[ns]")
        stops, faults, majors = e[e["is_stop"]], e[e["is_fault_stop"]], e[e["is_major_fault"]]
        g["in_any_stop"] = _mark(ts, s_(stops), e_(stops), step)
        g["in_fault"] = _mark(ts, s_(faults), e_(faults), step)
        g["in_major_fault"] = _mark(ts, s_(majors), e_(majors), step)
        for cname in ["curtailment", "maintenance", "grid", "weather", "routine"]:
            sub = stops[stops["event_class"] == cname]
            g[f"in_stop_{cname}"] = _mark(ts, s_(sub), e_(sub), step)
        # days to next major fault start (NaN if none ahead in the record -> right-censored)
        # pre-failure windows count back from the START of each major-fault episode
        mstarts = np.sort(s_(majors.sort_values("start").groupby("major_episode").head(1)))
        idx = np.searchsorted(mstarts, ts, side="left")
        if len(mstarts):
            nxt = np.where(idx < len(mstarts), mstarts[np.minimum(idx, len(mstarts) - 1)], np.datetime64("NaT"))
        else:
            nxt = np.full(len(ts), np.datetime64("NaT"), dtype="datetime64[ns]")
        days = (nxt - ts) / np.timedelta64(1, "D")
        g["days_to_next_major_fault"] = days
        for w in windows_days:
            g[f"pre_fault_{w}d"] = (days > 0) & (days <= w) & ~g["in_major_fault"].to_numpy()
        out.append(g)
    return pd.concat(out, ignore_index=True)


def summarize(ev: pd.DataFrame, top_n: int = 15) -> dict:
    stops = ev[ev["is_stop"]]
    return {
        "events_total": len(ev),
        "events_by_status": ev["status"].value_counts().to_dict(),
        "stops_by_class": stops["event_class"].value_counts().to_dict(),
        "fault_stops_by_component": stops[stops["event_class"] == "fault"]["component"].value_counts().to_dict(),
        "major_faults": int(ev["is_major_fault"].sum()),
        "major_fault_episodes": int(ev["major_episode"].nunique()),
        "major_faults_by_component": ev[ev["is_major_fault"]]["component"].value_counts().to_dict(),
        "stop_hours_by_class": (stops.groupby("event_class")["duration"].sum().dt.total_seconds() / 3600).round(1).to_dict(),
        "top_stop_codes": stops.groupby(["code", "message", "event_class", "component"]).size().sort_values(ascending=False).head(top_n),
        "top_fault_codes_by_hours": (stops[stops["is_fault_stop"]].groupby(["code", "message", "component"])["duration"].sum().dt.total_seconds() / 3600).sort_values(ascending=False).head(top_n).round(1),
    }

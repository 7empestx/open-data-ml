"""Load an operator export into the canonical windml format using a mapping (see mapping.py / schema.py)."""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np
import pandas as pd
from . import readers, resample, units
from .schema import SIGNALS, FREQ

_OFFSET_RX = re.compile(r"(?:Z|[+-]\d{2}:?\d{2})$")


@dataclass
class LoadLog:
    """Everything the loader noticed; feeds the data-quality report."""
    files: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    units: dict = field(default_factory=dict)          # signal -> how the unit was decided
    duplicates: dict = field(default_factory=dict)     # turbine -> duplicate timestamps collapsed
    off_grid: dict = field(default_factory=dict)       # turbine -> {count, offsets(min) histogram}
    dst: dict = field(default_factory=dict)            # ambiguous / nonexistent local times
    unparsed_timestamps: int = 0
    unmapped_columns: list[str] = field(default_factory=list)
    duplicate_dates: dict = field(default_factory=dict)  # turbine -> {date: n} (helps spot DST / clock issues)
    native_interval: dict = field(default_factory=dict)  # turbine -> {"interval": "1min", "regular_share": 0.99}
    aggregation: dict = field(default_factory=dict)      # high-res -> 10-min summary (resample.aggregate info)

    def warn(self, msg: str):
        if msg not in self.warnings:
            self.warnings.append(msg)


# ----------------------------------------------------------------------------- helpers
def turbine_ids(df: pd.DataFrame, spec: dict, path: Path) -> pd.Series:
    how = spec["from"]
    if how == "column":
        raw = df[spec["column"]].astype(str).str.strip()
    elif how == "sheet":
        raw = df["_sheet"].astype(str)
    elif how == "constant":
        raw = pd.Series(str(spec["value"]), index=df.index)
    else:  # filename
        m = re.search(spec["regex"], path.name)
        if not m:
            raise ValueError(f"turbine_id.regex {spec['regex']!r} does not match file name {path.name}")
        raw = pd.Series(m.group(1) if m.groups() else m.group(0), index=df.index)
    if how in ("column", "sheet") and spec.get("regex"):
        raw = raw.str.extract(spec["regex"], expand=False).fillna(raw)
    mp = {str(k): str(v) for k, v in (spec.get("map") or {}).items()}
    if mp:
        raw = raw.map(lambda v: mp.get(v, v))
    fmt = spec.get("format")
    if fmt:
        uniq = {v: (fmt.format(int(v)) if re.fullmatch(r"\d+", v) else fmt.format(v)) for v in raw.unique()}
        raw = raw.map(uniq)
    return raw


def _localize(t: pd.Series, groups: pd.Series, spec: dict, log: LoadLog, what: str) -> pd.Series:
    tz = spec["timezone"]
    if tz in ("UTC", "utc", "Z"):
        return t.dt.tz_localize("UTC")
    amb = {"infer": "infer", "earliest": True, "latest": False, "drop": "NaT"}[spec["ambiguous"]]
    non = {"drop": "NaT", "shift_forward": "shift_forward"}[spec["nonexistent"]]
    out = pd.Series(pd.NaT, index=t.index, dtype=f"datetime64[ns, {tz}]")
    n_amb = n_non = 0
    for _, idx in t.groupby(groups, sort=False).groups.items():
        s = t.loc[idx]
        naive_ok = s.notna()
        try:
            loc = s.dt.tz_localize(tz, ambiguous=amb if amb != "infer" else "infer", nonexistent=non)
        except Exception as e:  # infer fails on gaps/duplicates around the change: fall back to NaT for the ambiguous hour
            log.warn(f"{what}: could not infer DST for the repeated autumn hour ({type(e).__name__}); those rows are dropped. "
                     "Set ambiguous: earliest|latest if the export repeats the hour in a known order.")
            loc = s.dt.tz_localize(tz, ambiguous="NaT", nonexistent=non)
        try:
            n_amb += int((s.dt.tz_localize(tz, ambiguous="NaT", nonexistent="shift_forward").isna() & naive_ok).sum())
            n_non += int((s.dt.tz_localize(tz, ambiguous=False, nonexistent="NaT").isna() & naive_ok).sum())
        except Exception:
            pass
        out.loc[idx] = loc
    log.dst[what] = {"timezone": tz, "ambiguous_rows": n_amb, "nonexistent_rows": n_non, "ambiguous_policy": spec["ambiguous"],
                     "nonexistent_policy": spec["nonexistent"]}
    return out.dt.tz_convert("UTC")


def parse_time(df: pd.DataFrame, spec: dict, groups: pd.Series, log: LoadLog, what: str = "scada",
               step: pd.Timedelta | None = None) -> pd.Series:
    """Parse to UTC. `label: end` moves stamps back by `step` (the native interval; default 10 min)."""
    if "columns" in spec:
        s = df[spec["columns"][0]].astype(str).str.strip() + " " + df[spec["columns"][1]].astype(str).str.strip()
    else:
        s = df[spec["column"]]
    fmt = spec["format"]
    if fmt in ("epoch_s", "epoch_ms"):
        t = pd.to_datetime(pd.to_numeric(s, errors="coerce"), unit="s" if fmt == "epoch_s" else "ms", utc=True)
    elif fmt == "excel":
        t = pd.to_datetime(pd.to_numeric(s, errors="coerce"), unit="D", origin="1899-12-30")
    elif pd.api.types.is_datetime64_any_dtype(s):
        t = s
    else:
        s = s.astype("string").str.strip()
        sample = s.dropna().head(200)
        has_offset = len(sample) > 0 and sample.str.contains(_OFFSET_RX).mean() > 0.9
        if has_offset:
            t = pd.to_datetime(s, utc=True, errors="coerce", format="ISO8601" if fmt in ("auto", "iso") else fmt)
            if spec["timezone"] not in ("UTC", "utc"):
                log.warn(f"{what}: timestamps carry UTC offsets; `timezone: {spec['timezone']}` is ignored")
        elif fmt in ("auto", "iso"):
            t = pd.to_datetime(s, errors="coerce", dayfirst=bool(spec["dayfirst"]), format="mixed" if fmt == "auto" else "ISO8601")
        else:
            t = pd.to_datetime(s, errors="coerce", format=fmt)
    bad = int(t.isna().sum() - s.isna().sum()) if hasattr(s, "isna") else 0
    if bad > 0:
        log.unparsed_timestamps += bad
        log.warn(f"{what}: {bad:,} timestamps could not be parsed with format {fmt!r} and were dropped")
    if getattr(t.dt, "tz", None) is None:
        t = _localize(t, groups, spec, log, what)
    else:
        t = t.dt.tz_convert("UTC")
    shift = pd.Timedelta(spec.get("shift") or "0min")
    if spec["label"] == "end":
        shift -= pd.Timedelta(step or FREQ)
    return t + shift if shift else t


def _needed_columns(sc: dict) -> set[str]:
    need = set()
    ts = sc["timestamp"]
    need |= set(ts.get("columns") or [ts.get("column")])
    if sc["turbine_id"] and sc["turbine_id"]["from"] == "column":
        need.add(sc["turbine_id"]["column"])
    if sc["layout"] == "long":
        need |= {sc["long"]["tag_column"], sc["long"]["value_column"]}
    else:
        need |= {s["column"] for s in sc["signals"].values()}
        need |= set((sc.get("states") or {}).values())
    return need


def _header(path: Path, sc: dict) -> list[str]:
    lines = readers._head_lines(path, sc["csv"]["encoding"])
    hi = readers.header_index(lines, sc["csv"].get("header_match"), sc["csv"].get("header_row", 0))
    delim = sc["csv"]["delimiter"]
    if delim in (None, "auto"):
        delim = readers.sniff_delimiter(lines[hi:])
    import csv as _csv
    return next(_csv.reader([lines[hi]], delimiter=delim))


def _numeric(s: pd.Series, decimal: str) -> pd.Series:
    if pd.api.types.is_numeric_dtype(s):
        return s.astype("float64")
    x = s.astype("string").str.strip()
    if decimal == ",":
        x = x.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(x, errors="coerce").astype("float64")


# ----------------------------------------------------------------------------- SCADA
def read_raw(sc: dict, raw_dir: Path, log: LoadLog, limit_files: int | None = None, only: list[Path] | None = None) -> pd.DataFrame:
    hits = readers.expand(sc["files"], raw_dir)
    if only is not None:
        keep = {Path(p).resolve() for p in only}
        hits = [h for h in hits if h[0].resolve() in keep]
    if not hits:
        raise FileNotFoundError(f"no files match {[f['glob'] for f in sc['files']]} under {raw_dir}")
    if limit_files:
        hits = hits[:limit_files]
    need = _needed_columns(sc)
    if sc["layout"] == "wide" and readers.file_format(hits[0][0], sc["format"]) == "csv":
        try:
            cols = _header(hits[0][0], sc)
            log.unmapped_columns = [c for c in cols if c not in need][:500]
        except Exception:
            pass
    frames = []
    for path, fspec in hits:
        df = readers.read_any(path, sc, usecols=need if readers.file_format(path, sc["format"]) != "excel" else None)
        tspec = fspec.get("turbine_id") or sc["turbine_id"]
        df["turbine_id"] = turbine_ids(df, tspec, path)
        missing = [c for c in need if c not in df.columns and c != "turbine_id"]
        log.files.append({"file": str(path.relative_to(raw_dir)) if path.is_relative_to(raw_dir) else str(path), "rows": len(df),
                          "turbines": sorted(df["turbine_id"].unique().tolist())[:20], "missing_columns": missing})
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    df["_order"] = np.arange(len(df))
    return df


def load_scada(m: dict, raw_dir: Path, limit_files: int | None = None, keep_raw: Path | None = None,
               files: list[Path] | None = None) -> tuple[pd.DataFrame, LoadLog]:
    """Load the SCADA part of a mapping into the canonical 10-min frame.
    High-res data (native interval < 10 min) is aggregated by resample.aggregate; `keep_raw` writes the
    un-aggregated canonical samples (UTC, sample-start stamps) to that parquet file first. `files` restricts the
    read to these paths (used to process one turbine at a time)."""
    sc = m["scada"]
    log = LoadLog()
    df = read_raw(sc, raw_dir, log, limit_files, only=files)
    groups = df["turbine_id"].astype(str) + "|" + df["_file"].astype(str) + "|" + df.get("_sheet", pd.Series("", index=df.index)).astype(str)
    tspec = {**sc["timestamp"], "label": "start"}       # the end-label shift is applied after the native interval is known
    states = sc.get("states") or {}
    if sc["layout"] == "long":
        df = _long_to_wide(df, {**sc, "timestamp": tspec}, groups, log)
    else:
        df["timestamp"] = parse_time(df, tspec, groups, log)
        out = pd.DataFrame({"timestamp": df["timestamp"], "turbine_id": df["turbine_id"].astype(str)})
        for name, spec in sc["signals"].items():
            col = spec["column"]
            out[name] = _numeric(df[col], sc["csv"]["decimal"]) if col in df.columns else np.nan
            if col not in df.columns:
                log.warn(f"{name}: column {col!r} not found in any file")
        for name, col in states.items():
            out[name] = df[col] if col in df.columns else np.nan
        df = out
    df = df.dropna(subset=["timestamp"])
    native = _native_intervals(df, sc, log)
    if sc["timestamp"]["label"] == "end":
        step = df["turbine_id"].map({t: v or pd.Timedelta(FREQ) for t, v in native.items()})
        df["timestamp"] = df["timestamp"] - pd.to_timedelta(step)
    _apply_units(df, sc, log)
    hi = [t for t, v in native.items() if v is not None and v < pd.Timedelta(FREQ)]
    if keep_raw is not None and hi:
        Path(keep_raw).parent.mkdir(parents=True, exist_ok=True)
        df[df["turbine_id"].isin(hi)].sort_values(["turbine_id", "timestamp"]).to_parquet(keep_raw, index=False)
        log.aggregation["raw_file"] = Path(keep_raw).name
    parts = []
    if hi:
        agg = sc.get("aggregate") or {}
        h = df[df["turbine_id"].isin(hi)]
        for iv, tids in pd.Series(hi).groupby(pd.Series([native[t] for t in hi])):
            a, info = resample.aggregate(h[h["turbine_id"].isin(tids)], iv, list(sc["signals"]), agg.get("stats"),
                                         list(states), float(agg.get("min_coverage", 0.5)))
            parts.append(a)
            log.aggregation.setdefault("groups", []).append({"turbines": sorted(tids), **info})
            if info["bins_below_min_coverage"]:
                log.warn(f"high-res aggregation: {info['bins_below_min_coverage']:,} of {info['bins']:,} 10-min bins have coverage "
                         f"below {agg.get('min_coverage', 0.5)} and were set to NaN (coverage column kept)")
    lo = df[~df["turbine_id"].isin(hi)]
    if len(lo):
        parts.append(_to_grid(lo, log))
    df = pd.concat(parts, ignore_index=True) if len(parts) > 1 else parts[0]
    return df.sort_values(["turbine_id", "timestamp"]).reset_index(drop=True), log


def _native_intervals(df: pd.DataFrame, sc: dict, log: LoadLog) -> dict:
    conf = str(sc.get("interval") or "auto")
    out = {}
    for tid, g in df.groupby("turbine_id", sort=True):
        iv, share = resample.detect_interval(g["timestamp"])
        if conf != "auto":
            if iv is not None and iv != pd.Timedelta(conf):
                log.warn(f"{tid}: mapping says interval {conf} but the timestamps step by {iv} ({share:.0%} of steps); using {conf}")
            iv = pd.Timedelta(conf)
        out[tid] = iv
        log.native_interval[tid] = {"interval": resample.fmt_interval(iv), "regular_share": round(share, 4)}
        if iv is not None and iv > pd.Timedelta(FREQ):
            log.warn(f"{tid}: native interval {iv} is coarser than 10 min; rows are placed on the 10-min grid, nothing is interpolated")
        elif iv is not None and share < 0.5:
            log.warn(f"{tid}: irregular sampling (only {share:.0%} of steps equal the most common step {iv})")
    return out


def _long_to_wide(df, sc, groups, log):
    tagc, valc = sc["long"]["tag_column"], sc["long"]["value_column"]
    tag2sig = {}
    for name, spec in sc["signals"].items():
        tag2sig[str(spec["tag"])] = name
    for name, tag in (sc.get("states") or {}).items():
        tag2sig[str(tag)] = name
    tags = df[tagc].astype(str)
    log.unmapped_columns = sorted(set(tags.unique()) - set(tag2sig))[:200]
    keep = tags.isin(tag2sig)
    d = df.loc[keep].copy()
    d["timestamp"] = parse_time(d, sc["timestamp"], groups.loc[keep], log)
    d["signal"] = tags.loc[keep].map(tag2sig)
    d["value"] = _numeric(d[valc], sc["csv"]["decimal"])
    n_dup = int(d.duplicated(["turbine_id", "timestamp", "signal"]).sum())
    if n_dup:
        log.warn(f"long layout: {n_dup:,} repeated (turbine, timestamp, tag) values; the first one is kept")
    w = d.pivot_table(index=["turbine_id", "timestamp"], columns="signal", values="value", aggfunc="first").reset_index()
    w.columns.name = None
    for name in sc["signals"]:
        if name not in w:
            w[name] = np.nan
            log.warn(f"{name}: tag {sc['signals'][name]['tag']!r} not found")
    for name in sc.get("states") or {}:
        if name not in w:
            w[name] = np.nan
    return w[["timestamp", "turbine_id"] + list(sc["signals"]) + list(sc.get("states") or {})]


def _apply_units(df: pd.DataFrame, sc: dict, log: LoadLog):
    for name, spec in sc["signals"].items():
        sig = SIGNALS[name]
        x = df[name]
        if "unit_switch" in spec:
            us = spec["unit_switch"]
            conv, hi = units.split_switch(x, us["low"], us["high"], sig.unit, float(us.get("threshold", 20)))
            df[name] = conv
            share = float(hi[x.notna()].mean()) if x.notna().any() else 0.0
            log.units[name] = f"per-row switch: |x| > {us.get('threshold', 20)} read as {us['high']}, else {us['low']} ({share:.0%} {us['high']})"
        else:
            u = spec.get("unit")
            src = "mapping"
            if u is None:
                u = units.unit_from_name(spec.get("column", "")) or sig.unit
                src = "column name" if units.unit_from_name(spec.get("column", "")) else "canonical default"
            if u == "auto":
                u, score, why = units.guess_unit(x, sig.quantity, sig.unit, sig.plausible)
                src = f"auto-detected (score {score:.2f}; {why})"
                if u != sig.unit:
                    log.warn(f"{name}: unit auto-detected as {u} and converted to {sig.unit}; confirm and pin it in the mapping")
            df[name] = units.convert(x, u, sig.unit)
            log.units[name] = f"{units.normalize_unit(u)} -> {sig.unit} ({src})"
        if spec.get("scale") is not None:
            df[name] = df[name] * float(spec["scale"])
        if spec.get("offset") is not None:
            df[name] = df[name] + float(spec["offset"])
        for w in units.unit_suspicions(name, df[name], sig.quantity, sig.unit, sig.plausible, df["timestamp"]):
            log.warn("unit suspicion: " + w)


def _to_grid(df: pd.DataFrame, log: LoadLog) -> pd.DataFrame:
    sig = [c for c in df.columns if c not in ("timestamp", "turbine_id")]
    parts = []
    for tid, g in df.groupby("turbine_id", sort=True):
        g = g.sort_values("timestamp", kind="stable")
        fl = g["timestamp"].dt.floor(FREQ)
        off = (g["timestamp"] - fl).dt.total_seconds() / 60
        n_off = int((off != 0).sum())
        if n_off:
            log.off_grid[tid] = {"count": n_off, "share": round(n_off / len(g), 4),
                                 "offsets_min": {f"{k:g}": int(v) for k, v in off[off != 0].round(1).value_counts().head(5).items()}}
        g = g.assign(timestamp=fl, _n=g[sig].notna().sum(axis=1))
        dup = g.duplicated("timestamp", keep=False)
        n_dup = int(g.duplicated("timestamp").sum())
        if n_dup:
            log.duplicates[tid] = n_dup
            dd = g.loc[g.duplicated("timestamp"), "timestamp"].dt.strftime("%Y-%m-%d").value_counts().head(10)
            log.duplicate_dates[tid] = {k: int(v) for k, v in dd.items()}
            # keep the most complete row per timestamp (ties: first in file order)
            g = g.sort_values(["timestamp", "_n"], ascending=[True, False], kind="stable").drop_duplicates("timestamp")
        del dup
        parts.append(g.drop(columns="_n"))
    out = pd.concat(parts, ignore_index=True) if parts else df.iloc[0:0]
    out["turbine_id"] = out["turbine_id"].astype(str)
    return out.sort_values(["turbine_id", "timestamp"]).reset_index(drop=True)


# ----------------------------------------------------------------------------- status / alarms
def load_status(m: dict, raw_dir: Path, log: LoadLog | None = None) -> pd.DataFrame:
    st = m.get("status")
    if not st:
        return pd.DataFrame()
    log = log or LoadLog()
    hits = readers.expand(st["files"], raw_dir)
    if not hits:
        raise FileNotFoundError(f"status: no files match {[f['glob'] for f in st['files']]}")
    frames = []
    for path, fspec in hits:
        df = readers.read_any(path, {**st, "format": st["format"]})
        df["turbine_id"] = turbine_ids(df, fspec.get("turbine_id") or st["turbine_id"], path)
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    groups = df["turbine_id"].astype(str) + "|" + df["_file"].astype(str)

    def col(key, default=None):
        spec = st.get(key)
        if not spec:
            return pd.Series(default, index=df.index, dtype="object")
        s = df[spec["column"]] if spec.get("column") in df.columns else pd.Series(spec.get("default"), index=df.index, dtype="object")
        if spec.get("map"):
            mp = {str(k): v for k, v in spec["map"].items()}
            s = s.astype("string").map(lambda v: mp.get(v, v) if v is not pd.NA else v)
        if spec.get("default") is not None:
            s = s.fillna(spec["default"])
        return s

    start = parse_time(df, {**st["start"], "label": "start"}, groups, log, "status.start")
    end = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns, UTC]")
    if st.get("end"):
        e = df.copy()
        ecol = st["end"].get("column")
        if ecol in e:
            e[ecol] = e[ecol].replace(list(st.get("end_missing") or ["-"]), None)
        end = parse_time(e, {**st["end"], "label": "start"}, groups, LoadLog(), "status.end")
    dur = None
    if st.get("duration"):
        d = df[st["duration"]["column"]].astype("string")
        hms = d.str.extract(r"^(\d+):(\d{2}):(\d{2})$").astype(float)
        dur = pd.to_timedelta(hms[0] * 3600 + hms[1] * 60 + hms[2], unit="s")
        end = end.fillna(start + dur)
    ev = pd.DataFrame({"farm": m["name"], "turbine_id": df["turbine_id"].astype(str), "start": start, "end": end,
                       "status": col("status", "Stop").astype("string").fillna("Stop"),
                       "code": pd.to_numeric(col("code"), errors="coerce").astype("Int64"),
                       "message": col("message", "").astype("string").fillna(""),
                       "service_category": col("service_category"), "iec_category": col("iec_category")})
    ev["comment"] = None
    ev["duration_logged"] = dur if dur is not None else pd.NaT
    ev = ev.dropna(subset=["start"])
    ev["instantaneous"] = ev["end"].isna()
    ev["end_filled"] = ev["end"].fillna(ev["start"])
    ev["duration"] = ev["end_filled"] - ev["start"]
    ev["service_category_clean"] = ev["service_category"].astype("string").fillna("").str.replace(r"\s*\(\d+\)\s*$", "", regex=True).str.strip()
    ev["message"] = ev["message"].astype(str)
    ev["status"] = ev["status"].astype(str)
    return ev.sort_values(["turbine_id", "start"]).reset_index(drop=True)


def classify(ev: pd.DataFrame, m: dict, major_min_duration: str = "1h") -> pd.DataFrame:
    """labeling.classify_events plus the mapping's class_by_code / class_rules overrides."""
    from .. import labeling as lb
    if ev.empty:
        return ev
    st = m["status"]
    out = lb.classify_events(ev, major_min_duration=major_min_duration)
    over = pd.Series(pd.NA, index=out.index, dtype="object")
    for r in st.get("class_rules") or []:
        fld = r.get("field", "message")
        hit = out[fld].astype(str).str.contains(r["match"], case=False, regex=True, na=False) & over.isna()
        over[hit] = r["class"]
    for code, c in (st.get("class_by_code") or {}).items():
        over[(out["code"] == int(code)) & over.isna()] = c
    if over.notna().any():
        out.loc[over.notna(), "event_class"] = over[over.notna()]
        out["is_fault_stop"] = out["is_stop"] & out["event_class"].eq("fault")
        out["is_major_fault"] = out["is_fault_stop"] & out["is_major_component"] & (out["duration"] >= pd.Timedelta(major_min_duration))
    return out

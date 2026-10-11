"""Draft a mapping YAML from a sample export: fuzzy column-name matching + value-range heuristics.

The output is a *draft for human review*: every guess carries a confidence score and a short reason as a YAML
comment, and columns that could not be matched are listed at the end. Run ``windml ingest validate`` on the
reviewed mapping before loading.
"""
from __future__ import annotations
import difflib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
import pandas as pd
from . import readers, units
from .schema import SIGNALS

AGG_PENALTY = re.compile(r"(?:^|[\s_.\-(])(min|max|std|stdev|sdev|sd|minimum|maximum|deviation|count|cnt)(?:$|[\s_.\-)])", re.I)
MEAN_HINT = re.compile(r"(?:^|[\s_.\-(])(avg|mean|average)(?:$|[\s_.\-)])", re.I)
TID_NAME = re.compile(r"turbine|wtg|\bwt\b|asset|unit|device|machine|wind_turbine|station|plant|\bname\b|\bid\b|anlage|wea", re.I)
TIME_NAME = re.compile(r"time|date|stamp|zeit|datum|\bts\b|period", re.I)
TAG_NAME = re.compile(r"tag|signal|variable|channel|point|metric|measurement|param|name", re.I)
VALUE_NAME = re.compile(r"value|val|reading|measure|wert", re.I)
STRF_CANDIDATES = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M",
                   "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M", "%m/%d/%Y %I:%M:%S %p",
                   "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M", "%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M"]


# vendor abbreviations and a few common non-English words -> the vocabulary used in schema descriptions/aliases
VOCAB = {
    "act": "active", "actv": "active", "pwr": "power", "pow": "power", "p": "power", "spd": "speed", "sped": "speed",
    "tmp": "temperature", "temp": "temperature", "brg": "bearing", "bear": "bearing", "gbx": "gearbox", "gear": "gearbox",
    "nac": "nacelle", "amb": "ambient", "ext": "ambient", "outdoor": "ambient", "gen": "generator", "dir": "direction",
    "prs": "pressure", "pres": "pressure", "press": "pressure", "ang": "angle", "wd": "wind", "rtr": "rotor", "rot": "rotor",
    "bl": "blade", "blds": "blade", "pos": "position", "avail": "available", "cap": "capacity", "exp": "export",
    "leistung": "active power", "wirkleistung": "active power", "windgeschwindigkeit": "wind speed", "aussentemperatur": "ambient temperature",
    "rotordrehzahl": "rotor speed", "generatordrehzahl": "generator speed", "drehzahl": "speed", "getriebeoeltemperatur": "gearbox oil temperature",
    "gondelposition": "nacelle position", "gondeltemperatur": "nacelle temperature", "windrichtung": "wind direction",
    "blattwinkel": "blade pitch angle", "pitchwinkel": "pitch angle", "puissance": "active power", "vitesse": "speed", "vent": "wind",
}


def _norm(s: str) -> str:
    s = re.sub(r"[\(\[][^\)\]]*[\)\]]", " ", str(s))          # drop "(kW)", "[°C]"
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", s)                 # camelCase -> camel case
    s = re.sub(r"([A-Za-z])(\d)", r"\1 \2", s)                 # Brg1 -> Brg 1
    s = re.sub(r"[^0-9a-zA-Z]+", " ", s).lower()
    s = re.sub(r"\b(avg|mean|average|value|val|mw|wtg|wtur|wnac|wrot|wgen|wtrm|wyaw)\b", " ", s)
    s = " ".join(VOCAB.get(w, w) for w in s.split())
    s = s.replace("gearbox gearbox", "gearbox")
    return " ".join(s.split())


def _sig_names(sig) -> list[str]:
    base = sig.name.rsplit("_", 1)[0] if sig.name.count("_") else sig.name
    return [base.replace("_", " "), sig.description] + list(sig.aliases)


_SIG_NORM = {name: [_norm(a) for a in _sig_names(sig)] + [a.lower() for a in sig.aliases] for name, sig in SIGNALS.items()}


def name_score(col: str, signal: str) -> float:
    c = _norm(col)
    if not c:
        return 0.0
    raw = str(col).strip().lower()
    best = 0.0
    for a in _SIG_NORM[signal]:
        if not a:
            continue
        if raw == a or c == a:
            return 1.0
        r = difflib.SequenceMatcher(None, c, a).ratio()
        ct, at = set(c.split()), set(a.split())
        if ct and at:
            r = max(r, len(ct & at) / len(ct | at))
        best = max(best, r)
    return best


def _is_text(x: pd.Series) -> bool:
    return pd.api.types.is_object_dtype(x) or pd.api.types.is_string_dtype(x)


def _parse_rate(s: pd.Series) -> tuple[float, dict]:
    """Share of values that parse as timestamps, plus detected format info."""
    x = s.dropna()
    if len(x) == 0:
        return 0.0, {}
    if pd.api.types.is_datetime64_any_dtype(x):
        return 1.0, {"format": "auto", "native": True}
    if pd.api.types.is_numeric_dtype(x):
        v = pd.to_numeric(x, errors="coerce")
        med = float(v.median())
        if 9e8 < med < 4e9:
            return 1.0, {"format": "epoch_s"}
        if 9e11 < med < 4e12:
            return 1.0, {"format": "epoch_ms"}
        if 30_000 < med < 80_000 and (v % 1 != 0).mean() > 0.5:
            return 0.9, {"format": "excel"}
        return 0.0, {}
    x = x.astype(str).str.strip().head(500)
    if not x.str.contains(r"\d{1,4}[-./]\d{1,2}[-./]\d{1,4}", regex=True).mean() > 0.9:
        return 0.0, {}
    offset = bool(x.str.contains(r"(?:Z|[+-]\d{2}:?\d{2})$", regex=True).mean() > 0.9)
    if offset:
        rate = pd.to_datetime(x, errors="coerce", utc=True, format="ISO8601").notna().mean()
        return float(rate), {"format": "iso", "offset": True}
    for f in STRF_CANDIDATES:
        rate = pd.to_datetime(x, errors="coerce", format=f).notna().mean()
        if rate > 0.98:
            return float(rate), {"format": f}
    first = x.str.extract(r"^(\d{1,2})[./-](\d{1,2})[./-]\d{4}")
    dayfirst = bool(first[0].dropna().astype(int).gt(12).any()) if first[0].notna().any() else False
    rate = pd.to_datetime(x, errors="coerce", format="mixed", dayfirst=dayfirst).notna().mean()
    return float(rate), {"format": "auto", "dayfirst": dayfirst}


@dataclass
class Suggestion:
    sample: str
    read_opts: dict
    timestamp: dict = field(default_factory=dict)
    turbine_id: dict = field(default_factory=dict)
    layout: str = "wide"
    long: dict = field(default_factory=dict)
    signals: dict = field(default_factory=dict)       # name -> {column|tag, unit, confidence, reason, ...}
    unmapped: list = field(default_factory=list)
    notes: list = field(default_factory=list)
    files_glob: str = ""


def _detect_time(df: pd.DataFrame, exclude=()) -> tuple[str | None, dict]:
    best = (None, 0.0, {})
    for c in df.columns:
        if c in exclude or str(c).startswith("_"):
            continue
        rate, info = _parse_rate(df[c])
        rate += 0.05 if TIME_NAME.search(str(c)) else 0.0
        if rate > best[1]:
            best = (c, rate, info)
    return (best[0], best[2]) if best[1] >= 0.85 else (None, {})


def _local_time_hint(t: pd.Series, tid: pd.Series | None) -> str | None:
    """Look for DST fingerprints in naive timestamps: a repeated hour (autumn) or a missing hour (spring)."""
    t = pd.to_datetime(t, errors="coerce", format="mixed")
    g = tid if tid is not None else pd.Series("x", index=t.index)
    for _, s in t.groupby(g):
        s = s.dropna().sort_values()
        if len(s) < 50:
            continue
        d = s.diff().dropna()
        step = d.mode().iloc[0] if len(d) else pd.Timedelta("10min")
        dup = s[s.duplicated()]
        if len(dup) and (dup.dt.month.isin([10, 11]).mean() > 0.5):
            return f"repeated timestamps around {dup.iloc[0]:%Y-%m-%d %H:%M} (autumn DST change?)"
        jumps = s[1:][(d == step + pd.Timedelta("1h")).to_numpy()]
        if len(jumps) and jumps.dt.month.isin([3, 4]).any():
            return f"a 1-hour hole at {jumps.iloc[0]:%Y-%m-%d %H:%M} (spring DST change?)"
    return None


def _detect_turbine(df: pd.DataFrame, path: Path, opts: dict, exclude=()) -> dict:
    cands = []
    for c in df.columns:
        if c in exclude or str(c).startswith("_"):
            continue
        x = df[c].dropna()
        if len(x) == 0:
            continue
        nu = x.nunique()
        if 1 <= nu <= 500 and (not pd.api.types.is_float_dtype(x)) and nu < 0.2 * len(x) + 1:
            score = (2 if TID_NAME.search(str(c)) else 0) + (1 if _is_text(x) else 0) + (1 if 2 <= nu <= 300 else 0)
            if pd.api.types.is_numeric_dtype(x) and not TID_NAME.search(str(c)):
                score -= 2
            cands.append((score, c, nu))
    cands.sort(key=lambda t: -t[0])
    if cands and cands[0][0] >= 2:
        _, c, nu = cands[0]
        ids = sorted(map(str, df[c].dropna().unique()))[:50]
        return {"from": "column", "column": c, "_ids": ids, "_why": f"{nu} distinct values in column {c!r}"}
    if opts.get("format") == "excel" and opts.get("n_sheets", 1) > 1:
        return {"from": "sheet", "_ids": sorted(df["_sheet"].unique().tolist()), "_why": "one sheet per turbine"}
    m = re.search(r"(?i)(?:wtg|wt|turbine|t|unit|_)[_\- ]?(\d{1,3})(?=[_\-. ])", path.name)
    if m:
        pre = re.escape(path.name[max(0, m.start()):m.start(1)])
        return {"from": "filename", "regex": f"{pre}(\\d+)", "format": "T{:02d}", "_ids": [m.group(1)],
                "_why": f"turbine number {m.group(1)} in the file name"}
    return {"from": "constant", "value": path.stem, "_why": "no turbine id found; one file = one turbine?"}


def _detect_long(df: pd.DataFrame, tcol, tidcol) -> dict | None:
    rest = [c for c in df.columns if c not in (tcol, tidcol) and not str(c).startswith("_")]
    if len(rest) > 6:
        return None
    tags = [c for c in rest if _is_text(df[c]) and 3 <= df[c].nunique() <= 5000]
    vals = [c for c in rest if pd.api.types.is_numeric_dtype(df[c]) or pd.to_numeric(df[c], errors="coerce").notna().mean() > 0.9]
    if not tags or not vals:
        return None
    tag = max(tags, key=lambda c: (bool(TAG_NAME.search(str(c))), df[c].nunique()))
    val = max(vals, key=lambda c: (bool(VALUE_NAME.search(str(c))), df[c].notna().mean()))
    return {"tag_column": tag, "value_column": val}


def _numeric(s: pd.Series, decimal: str) -> pd.Series:
    if pd.api.types.is_numeric_dtype(s):
        return s.astype(float)
    s = s.astype(str).str.strip()
    if decimal == ",":
        s = s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


def score_columns(series: dict[str, pd.Series], min_conf: float = 0.45) -> tuple[dict, list]:
    """Greedy one-to-one assignment of source columns/tags to canonical signals."""
    rows = []
    for col, x in series.items():
        if x.notna().mean() < 0.05:
            continue
        hinted = units.normalize_unit(units.unit_from_name(str(col)))
        for name, sig in SIGNALS.items():
            ns = name_score(col, name)
            if ns < 0.35:
                continue
            if hinted and hinted in units.KNOWN_UNITS:
                try:
                    units.convert(pd.Series([1.0]), hinted, sig.unit)
                except ValueError:  # the column's own unit is for another quantity (e.g. °C vs kW)
                    continue
                u, rs, why = hinted, *units.guess_unit(units.convert(x, hinted, sig.unit), sig.quantity, sig.unit, sig.plausible)[1:]
                why = f"unit from column name; {why}"
            else:
                u, rs, why = units.guess_unit(x, sig.quantity, sig.unit, sig.plausible)
            conf = 0.6 * ns + 0.4 * rs
            if AGG_PENALTY.search(str(col)):   # min / max / std columns: only mapped if nothing better exists
                conf *= 0.55
            if MEAN_HINT.search(str(col)):
                conf = min(1.0, conf + 0.03)
            rows.append((conf, col, name, ns, rs, u, why))
    rows.sort(key=lambda r: -r[0])
    used_c, used_s, out = set(), set(), {}
    for conf, col, name, ns, rs, u, why in rows:
        if conf < min_conf or col in used_c or name in used_s:
            continue
        used_c.add(col)
        used_s.add(name)
        x = series[col]
        rec = {"source": col, "unit": u, "confidence": round(conf, 2), "name_score": round(ns, 2), "range_score": round(rs, 2), "reason": why}
        sig = SIGNALS[name]
        if sig.quantity == "pressure":
            v = x.dropna()
            hi_share = float((v.abs() > 20).mean()) if len(v) else 0.0
            if 0.01 < hi_share < 0.99:
                rec["unit_switch"] = {"low": "bar", "high": "kPa", "threshold": 20}
                rec["reason"] += f"; {hi_share:.0%} of values > 20 -> mixed bar/kPa"
        out[name] = rec
    unmapped = [c for c in series if c not in used_c]
    return out, unmapped


def _glob_for(path: Path, raw_dir: Path | None) -> str:
    rel = path.relative_to(raw_dir) if raw_dir and path.resolve().is_relative_to(Path(raw_dir).resolve()) else path
    name = re.sub(r"\d+", "*", rel.name)
    name = re.sub(r"\*(?:[^/*A-Za-z]*\*)+", "*", name)
    return str(rel.parent / name) if str(rel.parent) != "." else name


def suggest(path: str | Path, raw_dir: str | Path | None = None, nrows: int = 20_000) -> Suggestion:
    path = Path(path)
    df, opts = readers.read_sample(path, nrows=nrows)
    df.columns = [str(c).strip() for c in df.columns]
    s = Suggestion(sample=str(path), read_opts=opts, files_glob=_glob_for(path, Path(raw_dir) if raw_dir else None))
    tcol, tinfo = _detect_time(df)
    if tcol is None:
        s.notes.append("No timestamp column detected; set scada.timestamp by hand (or `columns: [date, time]`).")
    tid = _detect_turbine(df, path, opts, exclude=(tcol,))
    s.turbine_id = tid
    long = _detect_long(df, tcol, tid.get("column"))
    dec = opts.get("decimal", ".")
    if long:
        s.layout, s.long = "long", long
        tagc, valc = long["tag_column"], long["value_column"]
        v = _numeric(df[valc], dec)
        series = {t: v[df[tagc] == t].reset_index(drop=True) for t in df[tagc].dropna().unique()[:2000]}
    else:
        skip = {tcol, tid.get("column")}
        series = {}
        for c in df.columns:
            if c in skip or c.startswith("_"):
                continue
            x = _numeric(df[c], dec)
            if x.notna().mean() > 0.5 * df[c].notna().mean() and df[c].notna().any():
                series[c] = x
    s.signals, s.unmapped = score_columns(series)
    if long:
        s.unmapped = s.unmapped  # tags
    else:
        s.unmapped = [c for c in df.columns if c not in {r["source"] for r in s.signals.values()} | {tcol, tid.get("column")} and not c.startswith("_")]
    ts = {"column": tcol, **{k: v for k, v in tinfo.items() if k in ("format", "dayfirst")}}
    if tinfo.get("offset"):
        ts["timezone"] = "UTC"
        ts["_why"] = "timestamps carry UTC offsets (converted exactly; DST-safe)"
    elif tcol is not None:
        hint = _local_time_hint(df[tcol] if not tinfo.get("native") else df[tcol].astype(str),
                                df[tid["column"]] if tid.get("from") == "column" else None)
        ptz = s.read_opts.get("preamble_timezone")
        ts["timezone"] = ptz if ptz and not hint else "UTC"
        if ptz and not hint:
            ts["_why"] = f"file preamble says 'Time zone: {ptz}'"
        else:
            ts["_why"] = ("CHECK: looks like LOCAL time with DST - " + hint + "; set timezone to the site zone, e.g. Europe/London") if hint \
                else "CHECK: no offset in the data; confirm the export is UTC (else set the IANA zone, e.g. Europe/Berlin)"
    pre = (s.read_opts.get("preamble") or "") + " " + " ".join(map(str, df.columns[:3]))
    iana = re.search(r"\b((?:Europe|America|Asia|Australia|Africa|Pacific|Atlantic)/[A-Za-z_]+)\b", pre)
    if iana and not tinfo.get("offset"):
        ts["timezone"] = iana.group(1)
        ts["_why"] = f"export header names the zone {iana.group(1)!r}; DST is handled on load"
    ends = re.search(r"(?i)interval\s*end|period\s*end|end of (?:the )?interval|intervallende|ende des intervalls|fin de p[ée]riode", pre)
    ts["label"] = "end" if ends else "start"
    if ends:
        ts["_label_why"] = f"header says {ends.group(0)!r}"
    s.timestamp = ts
    if not any(n in s.signals for n in ("power_kw", "wind_speed_ms")):
        s.notes.append("Neither power nor wind speed was matched: check the export / map them by hand.")
    return s


def _q(v) -> str:
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    return json.dumps(v)


def _rx(v: str) -> str:
    return "'" + v.replace("'", "''") + "'"


def to_yaml(s: Suggestion, name: str = "new_operator") -> str:
    o = s.read_opts
    L = [f"# DRAFT mapping generated by `windml ingest suggest` from {Path(s.sample).name}",
         "# Review every line marked CHECK and every signal with confidence < 0.8, then run `windml ingest validate`.",
         f"name: {_q(name)}",
         "description: \"TODO: operator, site, turbine model\"",
         "license: \"TODO: data license / NDA reference\"",
         "rated_power_kw: 2000   # CHECK: nameplate rating (used by cleaning)",
         "",
         "scada:",
         "  files:",
         f"    - {_q(s.files_glob)}   # relative to WINDML_RAW_DIR; widen the glob to cover every turbine / month"]
    if o.get("format") == "csv":
        L += ["  format: csv", "  csv:", f"    delimiter: {_q(o['delimiter'])}", f"    decimal: {_q(o['decimal'])}"]
        if o.get("thousands"):
            L.append(f"    thousands: {_q(o['thousands'])}")
        if o.get("encoding") not in (None, "utf-8"):
            L.append(f"    encoding: {_q(o['encoding'])}")
        if o.get("header_match"):
            L.append(f"    header_match: {_rx(o['header_match'])}   # header line follows a preamble")
    elif o.get("format") == "excel":
        L += ["  format: excel", "  excel:", f"    sheets: {_q(o['sheets'])}"]
        if o.get("header_row"):
            L.append(f"    header_row: {o['header_row']}   # rows above the header are titles")
    else:
        L.append(f"  format: {o.get('format', 'auto')}")
    L.append(f"  layout: {s.layout}")
    if s.layout == "long":
        L += ["  long:", f"    tag_column: {_q(s.long['tag_column'])}", f"    value_column: {_q(s.long['value_column'])}"]
    t = s.turbine_id
    L += [f"  turbine_id:   # {t.get('_why', '')}", f"    from: {t['from']}"]
    for k in ("column", "value"):
        if k in t:
            L.append(f"    {k}: {_q(t[k])}")
    if "regex" in t:
        L.append(f"    regex: {_rx(t['regex'])}")
    if "format" in t:
        L.append(f"    format: {_q(t['format'])}   # CHECK: canonical id pattern")
    ids = t.get("_ids") or []
    if t["from"] in ("column", "sheet") and ids and len(ids) <= 50:
        L.append("    map:   # CHECK: raw id -> canonical id")
        for i, v in enumerate(ids, 1):
            L.append(f"      {_q(str(v))}: {_q(f'T{i:02d}')}")
    ts = s.timestamp
    L += [f"  timestamp:   # {ts.get('_why', '')}", f"    column: {_q(ts.get('column') or 'TODO')}"]
    if ts.get("format"):
        L.append(f"    format: {_q(ts['format'])}")
    if ts.get("dayfirst"):
        L.append("    dayfirst: true")
    L += [f"    timezone: {ts.get('timezone', 'UTC')}", "    ambiguous: infer   # repeated autumn hour: infer | earliest | latest | drop",
          f"    label: {ts.get('label', 'start')}   # " + (ts["_label_why"] if ts.get("_label_why") else
                                                   "CHECK: does the timestamp mark the START or the END of the 10-min interval?")]
    L.append("  signals:")
    for name in sorted(s.signals, key=lambda n: -s.signals[n]["confidence"]):
        r = s.signals[name]
        sig = SIGNALS[name]
        flag = "" if r["confidence"] >= 0.8 else "  CHECK"
        key = "column" if s.layout == "wide" else "tag"
        L.append(f"    {name}:   # confidence {r['confidence']:.2f} (name {r['name_score']:.2f}, range {r['range_score']:.2f}){flag}")
        L.append(f"      {key}: {_q(r['source'])}")
        if "unit_switch" in r:
            us = r["unit_switch"]
            L.append(f"      unit_switch: {{low: {us['low']}, high: {us['high']}, threshold: {us['threshold']}}}   # mixed units per row")
        else:
            u = units.normalize_unit(r["unit"]) or sig.unit
            tag = "" if u == sig.unit else f"  CHECK: converted to {sig.unit}"
            L.append(f"      unit: {_q(u)}   # {r['reason']}{tag}")
    if s.unmapped:
        L.append("  # Unmapped columns/tags (add any that matter; min/max/std columns are usually ignored):")
        for c in s.unmapped[:200]:
            L.append(f"  #   {c}")
        if len(s.unmapped) > 200:
            L.append(f"  #   ... and {len(s.unmapped) - 200} more")
    L += ["",
          "# status:   # optional alarm / status log -> stop & fault labels; see mappings/README.md",
          "#   files: [\"TODO/Status_*.csv\"]",
          "#   turbine_id: {from: filename, regex: '(\\d+)', format: \"T{:02d}\"}",
          "#   start: {column: \"TODO start\", timezone: UTC}",
          "#   end: {column: \"TODO end\", timezone: UTC}",
          "#   code: \"TODO code\"",
          "#   message: \"TODO message\"",
          "#   class_by_code: {}   # e.g. {\"1234\": fault}",
          ]
    if s.notes:
        L += ["", "notes:"] + [f"  - {_q(n)}" for n in s.notes]
    return "\n".join(L) + "\n"

"""Per-operator mapping files (YAML): load, validate, fill defaults. The format is documented in
mappings/README.md and in the module docstring of windml.ingest."""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import yaml
from .schema import SIGNALS, EVENT_CLASSES

TOP_KEYS = {"name", "description", "license", "source", "rated_power_kw", "scada", "status", "notes"}
SOURCE_KEYS = {"files", "format", "csv", "excel", "layout", "long", "turbine_id", "timestamp"}
SCADA_KEYS = SOURCE_KEYS | {"signals", "interval", "aggregate", "states"}
STATUS_KEYS = SOURCE_KEYS | {"start", "end", "duration", "status", "code", "message", "service_category", "iec_category",
                             "class_by_code", "class_rules", "end_missing"}
SIGNAL_KEYS = {"column", "tag", "unit", "unit_switch", "scale", "offset", "comment"}
TIME_KEYS = {"column", "columns", "format", "dayfirst", "timezone", "ambiguous", "nonexistent", "label", "shift"}
TID_KEYS = {"from", "column", "regex", "value", "map", "format"}


class MappingError(ValueError):
    pass


def _check(d, allowed, where):
    if not isinstance(d, dict):
        raise MappingError(f"{where}: expected a mapping, got {type(d).__name__}")
    extra = set(d) - allowed
    if extra:
        raise MappingError(f"{where}: unknown key(s) {sorted(extra)}; allowed: {sorted(allowed)}")


def _time(spec, where):
    if isinstance(spec, str):
        spec = {"column": spec}
    _check(spec, TIME_KEYS, where)
    if "column" not in spec and "columns" not in spec:
        raise MappingError(f"{where}: needs `column` or `columns`")
    out = {"format": "auto", "dayfirst": False, "timezone": "UTC", "ambiguous": "infer", "nonexistent": "drop",
           "label": "start", "shift": "0min", **spec}
    if out["label"] not in ("start", "end"):
        raise MappingError(f"{where}.label must be start or end")
    if out["ambiguous"] not in ("infer", "earliest", "latest", "drop"):
        raise MappingError(f"{where}.ambiguous must be infer, earliest, latest or drop")
    if out["nonexistent"] not in ("drop", "shift_forward"):
        raise MappingError(f"{where}.nonexistent must be drop or shift_forward")
    return out


def _source(d, allowed, where):
    _check(d, allowed, where)
    files = d.get("files")
    if not files:
        raise MappingError(f"{where}.files: give at least one file glob")
    if isinstance(files, (str, dict)):
        files = [files]
    files = [{"glob": f} if isinstance(f, str) else f for f in files]
    for i, f in enumerate(files):
        _check(f, {"glob", "turbine_id", "exclude"}, f"{where}.files[{i}]")
        if isinstance(f.get("exclude"), str):
            f["exclude"] = [f["exclude"]]
    tid = d.get("turbine_id")
    if tid is None and not all("turbine_id" in f for f in files):
        raise MappingError(f"{where}.turbine_id is required (from: column | filename | sheet | constant)")
    if tid is not None:
        _check(tid, TID_KEYS, f"{where}.turbine_id")
        if tid.get("from") not in ("column", "filename", "sheet", "constant"):
            raise MappingError(f"{where}.turbine_id.from must be column, filename, sheet or constant")
    layout = d.get("layout", "wide")
    if layout not in ("wide", "long"):
        raise MappingError(f"{where}.layout must be wide or long")
    if layout == "long":
        _check(d.get("long", {}), {"tag_column", "value_column"}, f"{where}.long")
        if not {"tag_column", "value_column"} <= set(d.get("long", {})):
            raise MappingError(f"{where}.long needs tag_column and value_column")
    csv = {"delimiter": "auto", "decimal": ".", "thousands": None, "encoding": "utf-8", "header_match": None,
           "header_row": 0, "na_values": ["NaN", "nan", "NA", "N/A", "", "-", "#N/A"], **(d.get("csv") or {})}
    _check(csv, {"delimiter", "decimal", "thousands", "encoding", "header_match", "header_row", "na_values"}, f"{where}.csv")
    excel = {"sheets": 0, "header_row": 0, **(d.get("excel") or {})}
    _check(excel, {"sheets", "header_row"}, f"{where}.excel")
    fmt = d.get("format", "auto")
    if fmt not in ("auto", "csv", "excel", "parquet"):
        raise MappingError(f"{where}.format must be auto, csv, excel or parquet")
    return {**d, "files": files, "turbine_id": tid, "layout": layout, "csv": csv, "excel": excel, "format": fmt}


def validate(m: dict) -> dict:
    _check(m, TOP_KEYS, "mapping")
    if "name" not in m or "scada" not in m:
        raise MappingError("mapping needs `name` and `scada`")
    sc = _source(m["scada"], SCADA_KEYS, "scada")
    sc["timestamp"] = _time(sc.get("timestamp") or {}, "scada.timestamp") if sc.get("timestamp") else None
    if sc["timestamp"] is None:
        raise MappingError("scada.timestamp is required")
    sigs = {}
    for name, spec in (sc.get("signals") or {}).items():
        if name not in SIGNALS:
            raise MappingError(f"scada.signals.{name}: not a canonical signal (see windml.ingest.schema.SIGNALS)")
        if isinstance(spec, str):
            spec = {"column": spec} if sc["layout"] == "wide" else {"tag": spec}
        _check(spec, SIGNAL_KEYS, f"scada.signals.{name}")
        key = "column" if sc["layout"] == "wide" else "tag"
        if key not in spec:
            raise MappingError(f"scada.signals.{name}: needs `{key}` for a {sc['layout']} layout")
        if "unit_switch" in spec:
            _check(spec["unit_switch"], {"low", "high", "threshold"}, f"scada.signals.{name}.unit_switch")
        sigs[name] = spec
    if not sigs:
        raise MappingError("scada.signals: map at least one signal")
    sc["signals"] = sigs
    sc["interval"] = str(sc.get("interval", "auto"))
    if sc["interval"] != "auto":
        try:
            pd.Timedelta(sc["interval"])
        except ValueError as e:
            raise MappingError(f"scada.interval: {sc['interval']!r} is not auto or a duration like 1s, 30s, 1min, 10min") from e
    agg = sc.get("aggregate") or {}
    _check(agg, {"min_coverage", "stats"}, "scada.aggregate")
    if not 0 <= float(agg.get("min_coverage", 0.5)) <= 1:
        raise MappingError("scada.aggregate.min_coverage must be between 0 and 1")
    for st in agg.get("stats") or []:
        if st not in sigs:
            raise MappingError(f"scada.aggregate.stats: {st!r} is not a mapped signal")
    for name in sc.get("states") or {}:
        if name in SIGNALS or not str(name).isidentifier():
            raise MappingError(f"scada.states.{name}: use a new identifier (e.g. operating_state), not a canonical signal")
    out = {**m, "scada": sc}
    if m.get("status"):
        st = _source(m["status"], STATUS_KEYS, "status")
        st["start"] = _time(st.get("start") or {}, "status.start")
        st["end"] = _time(st["end"], "status.end") if st.get("end") else None
        for k in ("status", "code", "message", "service_category", "iec_category", "duration"):
            v = st.get(k)
            if isinstance(v, str):
                st[k] = {"column": v}
            elif v is not None:
                _check(v, {"column", "map", "default"}, f"status.{k}")
        for code, c in (st.get("class_by_code") or {}).items():
            if c not in EVENT_CLASSES:
                raise MappingError(f"status.class_by_code.{code}: {c!r} is not one of {EVENT_CLASSES}")
        for i, r in enumerate(st.get("class_rules") or []):
            _check(r, {"match", "class", "field"}, f"status.class_rules[{i}]")
            if r.get("class") not in EVENT_CLASSES:
                raise MappingError(f"status.class_rules[{i}].class must be one of {EVENT_CLASSES}")
        out["status"] = st
    return out


def load_mapping(path: str | Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        m = yaml.safe_load(fh)
    try:
        return validate(m)
    except MappingError as e:
        raise MappingError(f"{path}: {e}") from None

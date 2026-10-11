"""Stage 1: raw operator export -> one canonical, cleaned, labelled 10-min parquet per turbine.

Reads only through the mapping (windml.ingest), one turbine at a time when the turbine id comes from the file name,
so a 9-year, 15-turbine farm fits in a few GB. Output in <work>/turbines/<TID>.parquet plus <work>/events.parquet and
<work>/prepare.json (ingest warnings, native interval, cleaning stats, label source per turbine).

Without an alarm/status log, stops are inferred from SCADA (see `infer_stops`): the labels then mark non-production
at wind, not faults, and the report says so.
"""
from __future__ import annotations
import hashlib
import json
import re
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from .. import labeling as lb
from ..ingest import loader, pipeline, readers
from ..ingest.schema import FREQ

INFER_POWER_FRAC = 0.01     # inferred stop: power below 1% of rated ...
INFER_WIND_MS = 4.5         # ... while the wind is above 4.5 m/s (well above cut-in) ...
INFER_CUTOUT_MS = 25.0      # ... and below cut-out (above it a stop is normal)
LABEL_COLS = ["in_any_stop", "in_fault", "in_major_fault", "in_stop_maintenance", "in_stop_grid", "in_stop_weather",
              "in_stop_curtailment", "in_stop_routine", "pre_fault_7d", "pre_fault_14d", "pre_fault_30d"]


def mapping_hash(m: dict) -> str:
    return hashlib.sha256(json.dumps(m, sort_keys=True, default=str).encode()).hexdigest()[:16]


def turbine_file_groups(m: dict, raw_dir: Path) -> dict[str, list[Path] | None]:
    """{turbine id: files} when ids come from file names (one turbine per read); {'*': None} otherwise (one read)."""
    sc = m["scada"]
    hits = readers.expand(sc["files"], raw_dir)
    if not hits:
        raise FileNotFoundError(f"no SCADA files match {[f['glob'] for f in sc['files']]} under {raw_dir}")
    groups: dict[str, list[Path]] = {}
    for path, fspec in hits:
        spec = fspec.get("turbine_id") or sc["turbine_id"]
        if spec["from"] not in ("filename", "constant"):
            return {"*": None}
        tid = loader.turbine_ids(pd.DataFrame(index=[0]), spec, path).iloc[0]
        groups.setdefault(str(tid), []).append(path)
    return dict(sorted(groups.items()))


def infer_stops(d: pd.DataFrame, rated_kw: float) -> pd.Series:
    """Rows where the turbine is not producing although the wind is in the production range."""
    p, w = d.get("power_kw"), d.get("wind_speed_ms")
    if p is None or w is None:
        return pd.Series(False, index=d.index)
    return ((p < INFER_POWER_FRAC * rated_kw) & (w > INFER_WIND_MS) & (w < INFER_CUTOUT_MS)).fillna(False)


def _label(cleaned: pd.DataFrame, ev: pd.DataFrame | None, rated_kw: float) -> tuple[pd.DataFrame, str]:
    if ev is not None and len(ev):
        lab = lb.label_grid(cleaned, ev)
        src = "alarm log"
    else:
        lab = cleaned.copy()
        for c in LABEL_COLS:
            lab[c] = False
        lab["days_to_next_major_fault"] = np.nan
        lab["in_any_stop"] = infer_stops(lab, rated_kw).to_numpy()
        src = "inferred from SCADA (no alarm log)" if ev is None else "alarm log (no events for this turbine)"
    for c in LABEL_COLS:
        if c not in lab:
            lab[c] = False
    return lab, src


def _rated(m: dict, tid: str) -> float:
    r = m.get("rated_power_kw", 2050.0)
    return float(r.get(tid, 2050.0)) if isinstance(r, dict) else float(r)


def _one_group(args) -> list[dict]:
    m, raw_dir, files, work, ev_path = args
    t0 = time.time()
    df, log = loader.load_scada(m, Path(raw_dir), files=files)
    ev = pd.read_parquet(ev_path) if ev_path else None
    out = []
    key = [c for c in pipeline.cw.KEY_COLUMNS]
    for tid, g in df.groupby("turbine_id", sort=True):
        g = g.reset_index(drop=True)
        rk = _rated(m, tid)
        cleaned, stats = pipeline.clean(g, rk)
        e = ev[ev["turbine_id"] == tid] if ev is not None else None
        lab, src = _label(cleaned, e, rk)
        extra = [c for c in g.columns if c not in key and c not in ("timestamp", "turbine_id")]
        if extra:   # signals the cleaner does not know (pitch motor temps, pump pressure, high-res stats, states)
            x = g[["timestamp"] + extra].drop_duplicates("timestamp")
            x["timestamp"] = x["timestamp"].dt.floor(FREQ)
            x = x.drop_duplicates("timestamp")
            lab = lab.merge(x, on="timestamp", how="left")
        for c in lab.columns:
            if lab[c].dtype == "float64":
                lab[c] = lab[c].astype("float32")
        tmp = Path(work) / "turbines" / f"{tid}.parquet.tmp"
        lab.to_parquet(tmp, index=False)
        tmp.rename(tmp.with_suffix(""))
        out.append({"turbine_id": tid, "rows": len(lab), "label_source": src, "rated_kw": rk,
                    "signals": sorted(c for c in g.columns if c not in ("timestamp", "turbine_id") and g[c].notna().any()),
                    "native_interval": log.native_interval.get(tid, {}), "clean": {k: v for k, v in stats[0].items()
                                                                                   if k not in ("invalid_counts", "missing_pct_raw")},
                    "warnings": [w for w in log.warnings if tid in w or not re.search(r"\b[A-Z]{2,5}\d{1,3}\b", w)][:30],
                    "files": [f["file"] for f in log.files if tid in f["turbines"]],
                    "seconds": round(time.time() - t0, 1)})
    return out


def prepare(m: dict, raw_dir: Path, work: Path, workers: int = 2, force: bool = False, turbines: list[str] | None = None,
            echo=print) -> dict:
    work = Path(work)
    (work / "turbines").mkdir(parents=True, exist_ok=True)
    man_p = work / "prepare.json"
    h = mapping_hash(m)
    old = json.loads(man_p.read_text()) if man_p.exists() else {}
    if old.get("mapping_hash") != h:
        force = True
    groups = turbine_file_groups(m, raw_dir)
    if turbines:
        groups = {k: v for k, v in groups.items() if k in turbines or k == "*"}
    t0 = time.time()
    ev_path = None
    n_events = 0
    if m.get("status"):
        ev_path = work / "events.parquet"
        if force or not ev_path.exists():
            ev = loader.classify(loader.load_status(m, raw_dir), m)
            ev.to_parquet(ev_path, index=False)
        n_events = len(pd.read_parquet(ev_path, columns=["turbine_id"]))
    done = {t["turbine_id"]: t for t in old.get("turbines", [])} if not force else {}
    def cached(tid):
        if tid == "*":
            return bool(done) and all((work / "turbines" / f"{t}.parquet").exists() for t in done)
        return tid in done and (work / "turbines" / f"{tid}.parquet").exists()
    todo = [(m, str(raw_dir), files, str(work), str(ev_path) if ev_path else None)
            for tid, files in groups.items() if force or not cached(tid)]
    results = list(done.values())
    if todo:
        if workers > 1 and len(todo) > 1:
            with ProcessPoolExecutor(min(workers, len(todo))) as ex:
                for r in ex.map(_one_group, todo):
                    results = [x for x in results if x["turbine_id"] not in {y["turbine_id"] for y in r}] + r
                    for y in r:
                        echo(f"  prepare {y['turbine_id']}: {y['rows']:,} rows, labels: {y['label_source']} ({y['seconds']} s)")
        else:
            for a in todo:
                r = _one_group(a)
                results = [x for x in results if x["turbine_id"] not in {y["turbine_id"] for y in r}] + r
                for y in r:
                    echo(f"  prepare {y['turbine_id']}: {y['rows']:,} rows, labels: {y['label_source']} ({y['seconds']} s)")
    results = sorted(results, key=lambda r: r["turbine_id"])
    if turbines:
        results = [r for r in results if r["turbine_id"] in turbines]
    man = {"mapping_hash": h, "farm": m["name"], "description": m.get("description", ""), "license": m.get("license", ""),
           "has_status_log": bool(m.get("status")), "events": n_events, "turbines": results,
           "seconds": round(time.time() - t0, 1)}
    man_p.write_text(json.dumps(man, indent=1, default=str))
    return man

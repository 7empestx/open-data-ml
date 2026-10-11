"""`windml report --mapping mappings/<farm>.yaml --out reports/<farm>/`: one command from a raw export to the report."""
from __future__ import annotations
import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="windml report", description=__doc__)
    p.add_argument("--mapping", "-m", required=True, help="windml.ingest mapping YAML")
    p.add_argument("--out", "-o", required=True, help="report directory (md, html, pdf, figures/, tables/)")
    p.add_argument("--raw-dir", help="raw data root (default: WINDML_RAW_DIR / data/raw)")
    p.add_argument("--work", help="cache for prepared turbines and models (default: data/fleet/<farm>)")
    p.add_argument("--workers", type=int, default=2, help="parallel turbines (each needs ~1.5 GB for a 9-year record)")
    p.add_argument("--window-months", type=int, default=24)
    p.add_argument("--score-years", type=int, default=None, help="walk-forward: score only the last N calendar years (default all)")
    p.add_argument("--turbines", help="comma-separated subset, e.g. KEL01,KEL02")
    p.add_argument("--force", action="store_true", help="ignore the cache and redo every stage")
    p.add_argument("--fast", action="store_true", help="smaller models (tests / quick looks)")
    p.add_argument("--no-pdf", action="store_true")
    return p


def run(a) -> dict:
    from .. import config as cfg
    from ..ingest import mapping
    from . import health, metrics, prepare, render, scoring
    m = mapping.load_mapping(a.mapping)
    farm = m["name"]
    raw = Path(a.raw_dir) if a.raw_dir else cfg.RAW_DIR
    work = Path(a.work) if a.work else cfg.DATA_DIR / "fleet" / farm
    out = Path(a.out)
    tids = a.turbines.split(",") if a.turbines else None
    times = {}
    t_all = time.time()
    print(f"windml report: {farm} -> {out} (work: {work})", flush=True)
    t = time.time()
    prep = prepare.prepare(m, raw, work, workers=a.workers, force=a.force, turbines=tids,
                           echo=lambda s: print(s, flush=True))
    times["prepare_s"] = round(time.time() - t, 1)
    print(f"prepare: {len(prep['turbines'])} turbines in {times['prepare_s']} s", flush=True)
    rated = {x["turbine_id"]: x["rated_kw"] for x in prep["turbines"]}
    t = time.time()
    health.run(work, rated, workers=a.workers, score_years=a.score_years, force=a.force, fast=a.fast,
               echo=lambda s: print(s, flush=True), only=tids)
    times["health_s"] = round(time.time() - t, 1)
    print(f"health models in {times['health_s']} s", flush=True)
    t = time.time()
    M = metrics.compute(work, prep, a.window_months)
    S = {tid: scoring.score(r, M["health"].get(tid), prep["has_status_log"]) for tid, r in M["turbines"].items()}
    times["metrics_s"] = round(time.time() - t, 1)
    t = time.time()
    figs = render.figures(M, S, out, rated)
    md = render.markdown_report(M, S, prep, {"window_months": a.window_months, "mapping_name": Path(a.mapping).name}, figs)
    files = render.write(md, out, f"Fleet condition report: {farm}", pdf=not a.no_pdf)
    times["render_s"] = round(time.time() - t, 1)
    # tables
    td = out / "tables"
    td.mkdir(parents=True, exist_ok=True)
    rows = []
    for tid, r in M["turbines"].items():
        flat = {k: (v if not isinstance(v, (list, dict)) else json.dumps(v, default=str)) for k, v in r.items()}
        rows.append({**flat, "flag": S[tid]["flag"], "confidence": S[tid]["confidence"], "reasons": S[tid]["reasons"],
                     "scheme": M["health"].get(tid, {}).get("scheme", "none")})
    sc = pd.DataFrame(rows)
    sc.to_csv(td / "scorecard.csv", index=False)
    for k in ("monthly", "drift", "downtime", "fault_codes"):
        if len(M[k]):
            M[k].to_csv(td / f"{k}.csv", index=False)
    times["total_s"] = round(time.time() - t_all, 1)
    run_info = {"farm": farm, "mapping": Path(a.mapping).name, "turbines": len(M["turbines"]), "window_months": a.window_months,
                "score_years": a.score_years, "workers": a.workers, "times": times, "files": {k: (Path(v).name if v else v) for k, v in files.items()
                                                                                               if k in ("md", "html", "pdf")},
                "flags": {tid: S[tid]["flag"] for tid in sorted(S)}, "generated": pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d %H:%M UTC")}
    (out / "run.json").write_text(json.dumps(run_info, indent=1))
    print(f"flags: {', '.join(f'{k} {v}' for k, v in run_info['flags'].items())}")
    print(f"wrote {files['md']}, {files['html']}" + (f", {files['pdf']}" if files.get("pdf") else f" ({files.get('pdf_note', 'no pdf')})"))
    print(f"total {times['total_s']} s ({', '.join(f'{k} {v}' for k, v in times.items() if k != 'total_s')})")
    return run_info


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    np.seterr(all="ignore")
    run(a)
    return 0

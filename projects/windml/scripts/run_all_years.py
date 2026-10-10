"""Clean + label EVERY downloaded year of Kelmarsh / Penmanshiel SCADA (all-years mode).

Reads every scada_<year>* folder under /workspace/industrial-data/<farm>-wind-scada (see greenbyte.use_all_years),
runs the same cleaning (clean_wind.clean_turbine) and labeling (labeling.*) rules as run_wind_clean.py /
run_labeling.py, and writes to data/processed/all_years/ so the single-period files are untouched:
  all_years/<farm>_scada_10min.parquet, all_years/<farm>_events.parquet, all_years/<farm>_scada_labeled.parquet
  reports/cleaning_stats_<farm>_all_years.json, reports/labels_<farm>_all_years.md
Memory-light: processes one turbine at a time and streams to Parquet.
Usage: python scripts/run_all_years.py [kelmarsh|penmanshiel ...]
"""
import gc, json, re, sys
from collections import defaultdict
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from windml import greenbyte as gb, clean_wind as cw, labeling as lb

gb.use_all_years()
OUT = ROOT / "data/processed/all_years"
OUT.mkdir(parents=True, exist_ok=True)
WINDOWS = (7, 14, 30)
KEYS = list(cw.KEY_COLUMNS)


def _tid(path):
    m = re.search(r"_(Kelmarsh|Penmanshiel)_(\d+)_", path.name)
    return f"{m.group(1)[:3].upper()}{int(m.group(2)):02d}"


def _normalize(df):
    """Same column set/dtypes for every turbine-year (some years lack a few signals)."""
    for k in KEYS:
        if k not in df:
            df[k] = np.nan
            df[f"qc_{k}"] = np.int8(2)
    cols = ["timestamp", "farm", "turbine_id", "row_in_source", "row_empty", "gap_steps"] + \
           [x for k in KEYS for x in (k, f"qc_{k}")] + ["power_above_rated", "rated_kw"]
    df = df[cols].copy()
    df["turbine_id"] = df["turbine_id"].astype(str)
    df["gap_steps"] = df["gap_steps"].astype("int32")
    for k in KEYS:
        df[k] = df[k].astype("float64"); df[f"qc_{k}"] = df[f"qc_{k}"].astype("int8")
    df["power_above_rated"] = df["power_above_rated"].astype(bool)
    return df


def clean(farm):
    rated = gb.rated_power(farm)
    by_t = defaultdict(list)
    for f in gb.turbine_files(farm):
        by_t[_tid(f)].append(f)
    path = OUT / f"{farm}_scada_10min.parquet"
    writer, stats = None, []
    for tid in sorted(by_t):
        parts = []
        for f in by_t[tid]:
            raw, meta = gb.read_turbine(f, usecols=list(cw.KEY_COLUMNS.values()))
            c, st = cw.clean_turbine(raw, meta, rated.get(tid, 2050.0))
            st["source_file"] = f.name; st["source_dir"] = f.parent.name; st["time_zone_in_header"] = meta.get("Time zone")
            c.insert(1, "farm", farm)
            parts.append(_normalize(c)); stats.append(st)
            del raw; gc.collect()
        df = pd.concat(parts, ignore_index=True)
        # overlapping exports (e.g. monthly + quarterly files): prefer the row that actually has data
        df["_score"] = df["row_in_source"].astype(int) + (~df["row_empty"]).astype(int)
        n0 = len(df)
        df = df.sort_values(["timestamp", "_score"], ascending=[True, False]).drop_duplicates("timestamp").drop(columns="_score")
        stats.append({"turbine_id": tid, "overlap_rows_dropped": int(n0 - len(df)),
                      "first": str(df["timestamp"].min()), "last": str(df["timestamp"].max()), "rows": len(df)})
        t = pa.Table.from_pandas(df, preserve_index=False)
        if writer is None:
            writer = pq.ParquetWriter(path, t.schema, compression="zstd")
        writer.write_table(t, row_group_size=200_000)
        print(farm, tid, len(df), "rows", df["timestamp"].min(), "->", df["timestamp"].max(), flush=True)
        del df, parts, t; gc.collect()
    writer.close()
    (ROOT / f"reports/cleaning_stats_{farm}_all_years.json").write_text(json.dumps(stats, indent=1, default=str))
    return path


def events(farm):
    ev = lb.parse_events(farm)
    n0 = len(ev)
    # stops open at a file boundary appear in both files; keep the occurrence with the latest end
    ev = ev.sort_values("end_filled").drop_duplicates(["turbine_id", "start", "status", "code", "message"], keep="last")
    ev = ev.sort_values(["turbine_id", "start"]).reset_index(drop=True)
    ev = lb.classify_events(ev, major_min_duration="1h")
    ev.attrs["dups_dropped"] = n0 - len(ev)
    return ev


def label(farm, ev):
    src = OUT / f"{farm}_scada_10min.parquet"
    path = OUT / f"{farm}_scada_labeled.parquet"
    tids = sorted(pq.read_table(src, columns=["turbine_id"]).column(0).unique().to_pylist())
    writer, rows = None, []
    for tid in tids:
        sc = pq.read_table(src, filters=[("turbine_id", "=", tid)]).to_pandas()
        lab = lb.label_grid(sc, ev, WINDOWS)
        lcols = ["in_any_stop", "in_fault", "in_major_fault"] + [f"pre_fault_{w}d" for w in WINDOWS] + \
                [c for c in lab.columns if c.startswith("in_stop_")]
        r = lab[lcols].sum(); r.name = tid; rows.append(r)
        t = pa.Table.from_pandas(lab, preserve_index=False)
        if writer is None:
            writer = pq.ParquetWriter(path, t.schema, compression="zstd")
        writer.write_table(t, row_group_size=200_000)
        del sc, lab, t; gc.collect()
    writer.close()
    rows = pd.DataFrame(rows); rows.loc["ALL"] = rows.sum()
    return rows


def report(farm, ev, rows, n_rows):
    s = lb.summarize(ev)
    majors = ev[ev["is_major_fault"]][["turbine_id", "major_episode", "start", "end_filled", "duration", "code", "message", "component"]]
    per_year = ev[ev["is_major_fault"]].assign(year=lambda d: d["start"].dt.year)
    by_year = per_year.groupby("year").agg(major_faults=("code", "size"), episodes=("major_episode", "nunique"))
    L = [f"# Failure labels: {farm} (all years)", "",
         f"Source: Greenbyte status logs ({ev['start'].min():%Y-%m-%d} to {ev['start'].max():%Y-%m-%d}, UTC), all downloaded years. "
         "Same rules as the single-period report (src/windml/labeling.py); generated by scripts/run_all_years.py.",
         "Major fault = Stop classified as fault, component in gearbox/generator/bearing/converter/pitch/yaw/hydraulics, duration >= 1 h; "
         "major faults on the same turbine within 24 h are merged into one episode. Pre-fault windows count back from each episode start "
         "and now cross calendar-year boundaries.", "",
         f"- Events: {s['events_total']:,} ({', '.join(f'{k} {v:,}' for k, v in s['events_by_status'].items())}); "
         f"{ev.attrs.get('dups_dropped', 0):,} exact-duplicate events removed (repeated rows within a log and stops repeated across year files)",
         f"- Stops by class: {s['stops_by_class']}",
         f"- Stop hours by class: {s['stop_hours_by_class']}",
         f"- Fault stops by component: {s['fault_stops_by_component']}",
         f"- Major faults: {s['major_faults']} events in {s['major_fault_episodes']} episodes; by component {s['major_faults_by_component']}", "",
         "## Major faults by year", "", by_year.to_markdown(), "",
         "## Top stop codes (count)", "", s["top_stop_codes"].rename("count").reset_index().to_markdown(index=False), "",
         "## Top fault codes by downtime hours", "", s["top_fault_codes_by_hours"].rename("hours").reset_index().to_markdown(index=False), "",
         "## Major fault events", "", majors.to_markdown(index=False), "",
         "## Labeled 10-minute rows per turbine", "", rows.to_markdown(), "",
         f"Total rows: {n_rows:,}. Rows within the last 30 days of the record without a later major fault are right-censored (days_to_next_major_fault is NaN)."]
    (ROOT / f"reports/labels_{farm}_all_years.md").write_text("\n".join(L))
    update_main_report(farm, ev, s, by_year, n_rows)
    return s, by_year


BEGIN, END = "<!-- all-years:begin -->", "<!-- all-years:end -->"


def update_main_report(farm, ev, s, by_year, n_rows):
    """Insert/refresh an all-years summary block near the top of reports/labels_<farm>.md (single-period text kept below)."""
    p = ROOT / f"reports/labels_{farm}.md"
    txt = p.read_text()
    turbines = sorted(ev["turbine_id"].unique())
    block = "\n".join([BEGIN, f"## All years ({ev['start'].min():%Y-%m-%d} to {ev['start'].max():%Y-%m-%d})", "",
        f"Re-run of the same rules on every downloaded year, {len(turbines)} turbines ({', '.join(turbines)}), {n_rows:,} labeled 10-minute rows. "
        f"Full detail: [labels_{farm}_all_years.md](labels_{farm}_all_years.md); data in data/processed/all_years/ (not committed, files > 90 MB; rebuild with scripts/run_all_years.py).", "",
        f"- Events: {s['events_total']:,}; fault stops: {int(ev['is_fault_stop'].sum()):,}",
        f"- Major faults: **{s['major_faults']} events in {s['major_fault_episodes']} episodes**; by component {s['major_faults_by_component']}", "",
        by_year.to_markdown(), "", "The section below is the original single-period report.", END, ""])
    if BEGIN in txt:
        pre, rest = txt.split(BEGIN, 1); txt = pre + block + rest.split(END, 1)[1].lstrip("\n")
    else:
        lines = txt.split("\n"); txt = "\n".join(lines[:2]) + "\n" + block + "\n".join(lines[2:])
    p.write_text(txt)


if __name__ == "__main__":
    farms = sys.argv[1:] or ["kelmarsh", "penmanshiel"]
    sp = OUT / "summary.json"
    summary = json.loads(sp.read_text()) if sp.exists() else {}
    for farm in farms:
        clean(farm)
        ev = events(farm)
        ev.to_parquet(OUT / f"{farm}_events.parquet", index=False)
        rows = label(farm, ev)
        n = pq.ParquetFile(OUT / f"{farm}_scada_labeled.parquet").metadata.num_rows
        s, by_year = report(farm, ev, rows, n)
        summary[farm] = {"rows": n, "events": s["events_total"], "fault_stops": int(ev["is_fault_stop"].sum()),
                         "major_faults": s["major_faults"], "episodes": s["major_fault_episodes"],
                         "by_component": s["major_faults_by_component"], "by_year": by_year.to_dict()}
        print(json.dumps(summary[farm], default=str), flush=True)
        del ev; gc.collect()
    sp.write_text(json.dumps(summary, indent=1, default=str))

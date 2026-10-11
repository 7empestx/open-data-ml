"""Day-1 data-quality report for a loaded (canonical) dataset: coverage, gaps, stuck sensors, out-of-range values,
unit suspicions, duplicates, off-grid / DST / clock-drift checks and a status-log summary. Markdown + HTML."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from .schema import SIGNALS, FREQ

STEP = pd.Timedelta(FREQ)
STUCK_STEPS = 36                      # >= 6 h of identical values
STUCK_STEPS_COARSE = 144              # >= 24 h for coarse-resolution sensors
STUCK_SIGNALS = {"temperature", "pressure"} | {"speed"}
GAP_REPORT_H = 1.0


def _runs(mask: np.ndarray):
    d = np.diff(np.concatenate([[0], mask.astype(np.int8), [0]]))
    return np.where(d == 1)[0], np.where(d == -1)[0]


def coverage(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    t0, t1 = df["timestamp"].min(), df["timestamp"].max()
    expected = int((t1 - t0) / STEP) + 1
    rows, gaps = [], []
    for tid, g in df.groupby("turbine_id"):
        grid = pd.date_range(t0, t1, freq=FREQ)
        g = g.set_index("timestamp").reindex(grid)
        core = [c for c in ("power_kw", "wind_speed_ms") if c in g]
        empty = g[core].isna().all(axis=1).to_numpy() if core else g.drop(columns="turbine_id").isna().all(axis=1).to_numpy()
        s, e = _runs(empty)
        hours = (e - s) / 6
        for a, b, h in zip(s, e, hours):
            if h >= GAP_REPORT_H:
                gaps.append({"turbine_id": tid, "gap_start": grid[a], "gap_end": grid[b - 1] + STEP, "hours": round(float(h), 1)})
        present = ~empty
        first = grid[present.argmax()] if present.any() else pd.NaT
        last = grid[len(present) - 1 - present[::-1].argmax()] if present.any() else pd.NaT
        rows.append({"turbine_id": tid, "first": first, "last": last, "expected_rows": expected, "rows_with_data": int(present.sum()),
                     "coverage": present.mean(), "gaps_ge_1h": int((hours >= 1).sum()), "longest_gap_h": round(float(hours.max()), 1) if len(hours) else 0.0})
    return pd.DataFrame(rows), pd.DataFrame(gaps)


def completeness(df: pd.DataFrame) -> pd.DataFrame:
    sig = [c for c in df.columns if c in SIGNALS]
    return df.groupby("turbine_id")[sig].apply(lambda g: g.notna().mean()).T


def stuck(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    for tid, g in df.groupby("turbine_id"):
        g = g.sort_values("timestamp")
        ts = g["timestamp"].to_numpy()
        for c in g.columns:
            if c not in SIGNALS or SIGNALS[c].quantity not in STUCK_SIGNALS:
                continue
            v = g[c].to_numpy(dtype=float)
            fin = v[np.isfinite(v)]
            # share of readings on a 0.5-unit grid: coarse sensors (e.g. 1 °C hub temperature) legitimately sit still for hours
            res = float(np.mean(np.isclose(fin * 2, np.round(fin * 2)))) if len(fin) else 0.0
            min_steps = STUCK_STEPS_COARSE if res >= 0.6 else STUCK_STEPS
            same = np.zeros(len(v), bool)
            same[1:] = (v[1:] == v[:-1]) & ~np.isnan(v[1:]) & (np.diff(ts) == np.timedelta64(STEP))
            s, e = _runs(same)
            ln = e - s + 1
            keep = ln >= min_steps
            if keep.any():
                i = int(np.argmax(np.where(keep, ln, 0)))
                out.append({"turbine_id": tid, "signal": c, "coarse_share": round(res, 2), "min_run_h": min_steps / 6, "runs": int(keep.sum()), "hours_stuck": round(float(ln[keep].sum() / 6), 1),
                            "longest_h": round(float(ln[i] / 6), 1), "longest_from": pd.Timestamp(ts[s[i] - 1]), "value": v[s[i]]})
    return pd.DataFrame(out)


def out_of_range(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    for c in df.columns:
        if c not in SIGNALS:
            continue
        lo, hi = SIGNALS[c].plausible
        v = df[c]
        n = int(((v < lo) | (v > hi)).sum())
        nn = int(v.notna().sum())
        if nn:
            out.append({"signal": c, "unit": SIGNALS[c].unit, "plausible": f"{lo:g} to {hi:g}", "values": nn, "out_of_range": n,
                        "share": n / nn, "min": v.min(), "p1": v.quantile(0.01), "p99": v.quantile(0.99), "max": v.max()})
    return pd.DataFrame(out)


def lag_check(df: pd.DataFrame, signal: str = "wind_speed_ms", max_lag: int = 12) -> pd.DataFrame:
    """Clock offset between turbines: lag (in 10-min steps) that maximises the correlation of each turbine's signal changes
    with the fleet median of the other turbines, per calendar quarter. A stable non-zero lag = clock offset; a lag that
    changes over time = clock drift."""
    if signal not in df or df["turbine_id"].nunique() < 2:
        return pd.DataFrame()
    w = df.pivot_table(index="timestamp", columns="turbine_id", values=signal).asfreq(FREQ)
    out = []
    for q, wq in w.groupby(w.index.tz_localize(None).to_period("Q")):
        if len(wq) < 2000:
            continue
        for tid in w.columns:
            x = wq[tid].diff()
            ref = wq.drop(columns=tid).median(axis=1).diff()
            if x.notna().sum() < 1000:
                continue
            cors = {k: x.corr(ref.shift(k)) for k in range(-max_lag, max_lag + 1)}
            best = max(cors, key=lambda k: -np.inf if pd.isna(cors[k]) else cors[k])
            out.append({"quarter": str(q), "turbine_id": tid, "best_lag_steps": best, "corr_at_best": round(cors[best], 3),
                        "corr_at_0": round(cors[0], 3)})
    return pd.DataFrame(out)


def dst_signature(df: pd.DataFrame, log) -> list[str]:
    """Data that is local time but labelled UTC shows a 1-hour gap on the spring DST date and repeated timestamps on the
    autumn date (EU: last Sunday of March / October)."""
    msgs = []
    years = sorted(df["timestamp"].dt.year.unique())
    def last_sunday(y, m):
        d = pd.Timestamp(year=y, month=m, day=31 if m in (3, 10) else 30)
        return (d - pd.Timedelta(days=(d.weekday() + 1) % 7)).date()
    autumn = {str(last_sunday(y, 10)) for y in years}
    spring = {str(last_sunday(y, 3)) for y in years}
    aut, spr = {}, {}
    for tid, dd in (log.duplicate_dates if log else {}).items():
        for target, dates in ((aut, autumn), (spr, spring)):
            hit = sum(n for d, n in dd.items() if d in dates)
            if hit >= 3:
                target[tid] = hit
    if aut:
        msgs.append(f"duplicate timestamps on the autumn DST date(s) ({', '.join(f'{k} {v}' for k, v in aut.items())}): "
                    "the export is probably local time with DST, not UTC")
    if spr:
        msgs.append(f"duplicate timestamps on the spring DST date(s) ({', '.join(f'{k} {v}' for k, v in spr.items())}): the exporter "
                    "probably stamped the skipped local hour with the summer-time offset (02:xx written as 03:xx), so one copy of each "
                    "pair is an hour early. The most complete row was kept; confirm with the operator")
    return msgs


def status_summary(ev: pd.DataFrame, df: pd.DataFrame) -> dict:
    if ev is None or ev.empty:
        return {}
    t0, t1 = df["timestamp"].min(), df["timestamp"].max()
    return {"events": len(ev), "stops": int(ev["status"].eq("Stop").sum()),
            "by_class": ev.loc[ev["status"].eq("Stop"), "event_class"].value_counts().to_dict() if "event_class" in ev else {},
            "fault_stops": int(ev.get("is_fault_stop", pd.Series(dtype=bool)).sum()),
            "major_faults": int(ev.get("is_major_fault", pd.Series(dtype=bool)).sum()),
            "outside_scada_period": int(((ev["start"] < t0 - pd.Timedelta(days=1)) | (ev["start"] > t1 + pd.Timedelta(days=1))).sum()),
            "end_before_start": int((ev["end"] < ev["start"]).sum()),
            "turbines_without_events": sorted(set(df["turbine_id"]) - set(ev["turbine_id"])),
            "top_stop_codes": ev[ev["status"].eq("Stop")].groupby(["code", "message"]).size().sort_values(ascending=False).head(10)}


def _fmt(df: pd.DataFrame, pct=(), floatfmt=".3g") -> str:
    if df is None or len(df) == 0:
        return "_none_"
    d = df.copy()
    for c in pct:
        if c in d:
            d[c] = d[c].map(lambda v: "" if pd.isna(v) else f"{v:.1%}")
    for c in d.columns:
        if pd.api.types.is_datetime64_any_dtype(d[c]):
            d[c] = d[c].dt.strftime("%Y-%m-%d %H:%M")
    return d.to_markdown(index=False, floatfmt=floatfmt)


def build(df: pd.DataFrame, log=None, ev: pd.DataFrame | None = None, mapping: dict | None = None) -> tuple[str, dict]:
    name = (mapping or {}).get("name", "dataset")
    cov, gaps = coverage(df)
    comp = completeness(df)
    st = stuck(df)
    oor = out_of_range(df)
    lag = lag_check(df)
    dst = dst_signature(df, log)
    ss = status_summary(ev, df)
    findings = []
    low = cov[cov["coverage"] < 0.95]
    for _, r in low.iterrows():
        findings.append(f"**Coverage** {r['turbine_id']}: {r['coverage']:.1%} of 10-min slots have data (longest gap {r['longest_gap_h']} h)")
    for _, r in comp.T.mean().loc[lambda s: s < 0.5].items() if len(comp) else []:
        pass
    empty_sig = comp.index[(comp.max(axis=1) == 0)].tolist() if len(comp) else []
    if empty_sig:
        findings.append(f"**Empty signals** (mapped but no values): {', '.join(empty_sig)}")
    for _, r in oor[oor["share"] > 0.001].iterrows() if len(oor) else []:
        findings.append(f"**Out of range** {r['signal']}: {r['share']:.2%} of values outside {r['plausible']} {r['unit']} (min {r['min']:.3g}, max {r['max']:.3g})")
    if len(st):
        top = st.sort_values("hours_stuck", ascending=False).head(5)
        findings.append("**Stuck sensors** (constant >= 6 h, or >= 24 h for coarse sensors): " + "; ".join(f"{r.turbine_id} {r.signal} {r.hours_stuck} h" for r in top.itertuples()))
    for w in (log.warnings if log else []):
        if w.startswith("unit suspicion") or "auto-detected" in w:
            findings.append("**Units** " + w.replace("unit suspicion: ", ""))
    if log and log.duplicates:
        findings.append(f"**Duplicate timestamps**: {sum(log.duplicates.values()):,} collapsed ({', '.join(f'{k} {v}' for k, v in log.duplicates.items())})")
    if log and log.off_grid:
        findings.append(f"**Off-grid timestamps** on {len(log.off_grid)} turbine(s) (snapped down to the 10-min grid): " +
                        "; ".join(f"{k} {v['share']:.1%} (offsets {v['offsets_min']} min)" for k, v in log.off_grid.items()))
    findings += [f"**DST** {m}" for m in dst]
    if len(lag):
        off = lag[(lag["best_lag_steps"] != 0) & (lag["corr_at_best"] - lag["corr_at_0"] > 0.02)]
        if len(off):
            g = off.groupby("turbine_id")["best_lag_steps"].agg(lambda s: sorted(set(s)))
            findings.append("**Clock offset/drift**: " + "; ".join(f"{t} lags the fleet by {v} x 10 min in {int((off['turbine_id'] == t).sum())} quarter(s)" for t, v in g.items()))
    for gr in ((log.aggregation or {}).get("groups", []) if log else []):
        if gr["bins_below_min_coverage"]:
            findings.append(f"**Sparse high-res bins**: {gr['bins_below_min_coverage']:,} of {gr['bins']:,} 10-min bins "
                            f"({', '.join(gr['turbines'])}, native {gr['native']}) had too few samples and were blanked")
    if log and log.unparsed_timestamps:
        findings.append(f"**Timestamps**: {log.unparsed_timestamps:,} could not be parsed")
    if ss and ss.get("turbines_without_events"):
        findings.append(f"**Status log**: no events for {', '.join(ss['turbines_without_events'])}")
    t0, t1 = df["timestamp"].min(), df["timestamp"].max()
    L = [f"# Data-quality report: {name}", "",
         f"{(mapping or {}).get('description', '')}".strip(), "",
         f"- Period (UTC): {t0:%Y-%m-%d %H:%M} to {t1:%Y-%m-%d %H:%M}; {df['turbine_id'].nunique()} turbines; {len(df):,} 10-min rows",
         f"- Signals mapped: {len([c for c in df.columns if c in SIGNALS])} of {len(SIGNALS)} canonical signals",
         f"- Source files: {len(log.files) if log else 'n/a'}", "",
         "## Day-1 findings", ""]
    L += [f"{i}. {f}" for i, f in enumerate(findings, 1)] or ["No issues above the thresholds."]
    L += ["", "## Coverage per turbine", "", "Coverage = 10-min slots with power or wind speed present, over the farm-wide period.", "",
          _fmt(cov, pct=("coverage",)), "", "## Signal completeness (share of rows with a value)", "",
          _fmt(comp.reset_index().rename(columns={"index": "signal"}), pct=tuple(comp.columns)) if len(comp) else "_none_", "",
          f"## Gaps of {GAP_REPORT_H:g} h or more (20 longest)", "", f"{len(gaps)} gaps in total.", "",
          _fmt(gaps.sort_values("hours", ascending=False).head(20) if len(gaps) else gaps), "",
          "## Stuck sensors (identical value for 6 h or more, 24 h for coarse sensors where >= 60% of readings sit on a 0.5-unit grid; temperatures, pressures, wind speed)", "", _fmt(st), "",
          "## Value ranges vs plausible physical range (canonical units)", "", _fmt(oor, pct=("share",)), "",
          "## Units", "", "| signal | decision |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in (log.units.items() if log else [])]
    if log and log.native_interval:
        L += ["", "## Sampling interval and aggregation", "",
              "Native interval = most common step between a turbine's timestamps. Data finer than 10 minutes is aggregated to "
              "10-minute bins (mean; min/max/std for key signals; coverage = samples present / samples expected).", "",
              pd.DataFrame([{"turbine_id": k, **v} for k, v in log.native_interval.items()]).to_markdown(index=False), ""]
        for gr in (log.aggregation or {}).get("groups", []):
            L.append(f"- Aggregated {', '.join(gr['turbines'])} from {gr['native']} ({gr['expected_per_bin']:g} samples per bin): "
                     f"{gr['bins']:,} bins, mean coverage {gr['mean_coverage']:.1%}, {gr['bins_below_min_coverage']:,} bins below the "
                     f"minimum coverage (values set to NaN), {gr['duplicates_dropped']:,} duplicate samples dropped")
        if "coverage" in df:
            cv = df.groupby("turbine_id")["coverage"].agg(mean="mean", bins_lt_90pct=lambda x: float((x < 0.9).mean()))
            L += ["", "Bin coverage per turbine:", "", _fmt(cv.reset_index(), pct=("mean", "bins_lt_90pct")), ""]
        if (log.aggregation or {}).get("raw_file"):
            L.append(f"- Raw high-res samples kept in `{log.aggregation['raw_file']}`")
    L += ["", "## Timestamps and clocks", "",
          f"- Duplicate timestamps collapsed (most complete row kept): {log.duplicates or 'none'}" if log else "",
          f"- Duplicate dates (top): {log.duplicate_dates or 'none'}" if log else "",
          f"- Off-grid timestamps: {log.off_grid or 'none'}" if log else "",
          f"- Local-time conversion: {log.dst or 'timestamps were UTC or carried offsets'}" if log else "", ""]
    if len(lag):
        piv = lag.pivot(index="turbine_id", columns="quarter", values="best_lag_steps")
        L += ["Best lag vs fleet (10-min steps; 0 = clocks agree), from wind-speed changes:", "", piv.reset_index().to_markdown(index=False), ""]
    if ss:
        L += ["## Status / alarm log", "", f"- Events: {ss['events']:,}; stops: {ss['stops']:,}; fault stops: {ss['fault_stops']:,}; "
              f"major faults: {ss['major_faults']}", f"- Stops by class: {ss['by_class']}",
              f"- Events outside the SCADA period: {ss['outside_scada_period']}; end before start: {ss['end_before_start']}", "",
              "Top stop codes:", "", ss["top_stop_codes"].rename("count").reset_index().to_markdown(index=False), ""]
    if log and log.warnings:
        L += ["## Loader warnings", ""] + [f"- {w}" for w in log.warnings] + [""]
    if log and log.unmapped_columns:
        L += ["## Columns in the export that are not mapped", "", ", ".join(f"`{c}`" for c in log.unmapped_columns[:150]) +
              (" ..." if len(log.unmapped_columns) > 150 else ""), ""]
    if log:
        L += ["## Files read", "", _fmt(pd.DataFrame(log.files)), ""]
    L += ["---", "Generated by `windml ingest validate` (projects/windml/src/windml/ingest). Thresholds: gaps >= 1 h, stuck >= 6 h, "
          "coverage < 95%, out-of-range share > 0.1%."]
    summary = {"name": name, "turbines": int(df["turbine_id"].nunique()), "rows": len(df), "findings": findings,
               "coverage_min": float(cov["coverage"].min()) if len(cov) else None}
    return "\n".join(L), summary


CSS = """body{font-family:system-ui,Arial,sans-serif;max-width:1200px;margin:2em auto;color:#1d2733;font-size:14px}
table{border-collapse:collapse;font-size:12px;margin:8px 0}th{background:#12324d;color:#fff;padding:3px 6px;text-align:left}
td{border-bottom:1px solid #d5dde5;padding:2px 6px}h1{color:#12324d}h2{color:#12324d;border-bottom:1px solid #b8c4d0}code{background:#eef2f6}"""


def write(md: str, out_md: Path) -> Path:
    import markdown
    out_md = Path(out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(md, encoding="utf-8")
    html = markdown.markdown(md, extensions=["tables"])
    out_html = out_md.with_suffix(".html")
    out_html.write_text(f"<!doctype html><html><head><meta charset='utf-8'><title>Data-quality report</title><style>{CSS}</style></head>"
                        f"<body>{html}</body></html>", encoding="utf-8")
    return out_html

"""Prove windml.ingest on differently shaped inputs and write reports/ingest/proof.md + day-1 data-quality reports.

Inputs (all must be present under $WINDML_RAW_DIR; nothing is downloaded here):
  kelmarsh, penmanshiel   Greenbyte wide CSVs (make download)        -> must reproduce data/processed/*_scada_10min + events
  la_haute_borne          ENGIE single-file, tag names, ISO offsets  (make download-lhb) -> checked against the raw file
  acme_messy, longco_long, xlsx_sheets  synthetic messy exports from Kelmarsh (scripts/make_messy_fixtures.py)
                          -> must reproduce the canonical Kelmarsh load for the same turbines / period
"""
from __future__ import annotations
import argparse
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from windml import config as cfg  # noqa: E402
from windml import nbm_years  # noqa: E402
from windml.ingest import loader, mapping, pipeline, quality  # noqa: E402

PROCESSED = ROOT / "data" / "processed"


def _cmp(a: pd.Series, b: pd.Series, rtol=1e-9, atol=1e-9) -> int:
    if pd.api.types.is_numeric_dtype(a) and not pd.api.types.is_bool_dtype(a):
        ok = np.isclose(a.astype(float), b.astype(float), equal_nan=True, rtol=rtol, atol=atol)
    else:
        ok = (a.astype(str) == b.astype(str)) | (a.isna() & b.isna())
    return int((~ok).sum())


def load(name, raw, mpath=None):
    m = mapping.load_mapping(mpath or ROOT / "mappings" / f"{name}.yaml")
    t0 = time.time()
    df, log = loader.load_scada(m, raw)
    ev = loader.classify(loader.load_status(m, raw, log), m) if m.get("status") else None
    return m, df, log, ev, time.time() - t0


def dq(name, m, df, log, ev, out_dir):
    md, summary = quality.build(df, log, ev, m)
    quality.write(md, out_dir / f"dq_{name}.md")
    return summary


def prove_reference(farm, raw, out_dir, L):
    m, df, log, ev, secs = load(farm, raw)
    s = dq(farm, m, df, log, ev, out_dir)
    c, _ = pipeline.clean(df, m["rated_power_kw"])
    ref = pd.read_parquet(PROCESSED / f"{farm}_scada_10min.parquet")
    ref["turbine_id"] = ref["turbine_id"].astype(str)
    k = ["turbine_id", "timestamp"]
    j = ref.merge(c, on=k, suffixes=("_r", "_n"), how="outer", indicator=True)
    both = j[j["_merge"] == "both"]
    cols = [x for x in ref.columns if x not in k + ["farm"] and x + "_n" in j]
    diffs, interp = {}, 0
    for col in cols:
        a, b = both[col + "_r"], both[col + "_n"]
        if col == "gear_oil_inlet_pressure_bar":  # committed file keeps the raw bar/kPa mix; ingest converts per row
            a = nbm_years.normalize_pressure(a)
            # the reference interpolated short gaps BEFORE the unit fix, so a gap between a bar and a kPa reading was
            # filled with a meaningless mid value; ingest converts first, then interpolates. Those rows (qc=1) differ.
            ok = np.isclose(a.astype(float), b.astype(float), equal_nan=True, rtol=1e-9, atol=1e-9)
            interp = int((~ok & (both["qc_" + col + "_r"] == 1)).sum())
            n = int((~ok & (both["qc_" + col + "_r"] != 1)).sum())
        else:
            n = _cmp(a, b)
        if n:
            diffs[col] = n
    r = pd.read_parquet(PROCESSED / f"{farm}_events.parquet")
    key = ["turbine_id", "start", "code"]
    cls = (r.sort_values(key)["event_class"].to_numpy() == ev.sort_values(key)["event_class"].to_numpy()).mean() if len(r) == len(ev) else float("nan")
    ok = not diffs and len(j) == len(both) and len(r) == len(ev) and cls == 1.0
    L += [f"### {farm} ({'PASS' if ok else 'CHECK'})", "",
          f"- Mapping `mappings/{farm}.yaml`; {len(log.files)} files, {len(df):,} rows, {df['turbine_id'].nunique()} turbines, loaded in {secs:.1f} s",
          f"- vs `data/processed/{farm}_scada_10min.parquet` after `pipeline.clean`: {len(ref):,} reference rows, {len(c):,} new, "
          f"{len(both):,} matched on (turbine, timestamp); {len(cols)} columns compared (values + QC flags), "
          f"{'all identical' if not diffs else 'differences: ' + str(diffs)}. Oil pressure compared against "
          "`nbm_years.normalize_pressure(reference)` (the committed file keeps the raw bar/kPa mix; ingest converts it per row)"
          + (f"; {interp} interpolated oil-pressure rows differ because the reference interpolated across a bar/kPa switch "
             "before converting (ingest converts first, so its values are the physically meaningful ones)." if interp else "."),
          f"- Events vs `data/processed/{farm}_events.parquet`: {len(r):,} reference, {len(ev):,} new; major faults "
          f"{int(r['is_major_fault'].sum())} / {int(ev['is_major_fault'].sum())}; event_class agreement {cls:.4f}",
          f"- Day-1 report: [dq_{farm}.md](dq_{farm}.md) ({len(s['findings'])} findings)", ""]
    return ok


def prove_lhb(raw, out_dir, L):
    name = "la_haute_borne"
    m, df, log, ev, secs = load(name, raw)
    s = dq(name, m, df, log, ev, out_dir)
    src = pd.read_csv(raw / "la-haute-borne" / "la-haute-borne-data-2014-2015.csv")
    src["timestamp"] = pd.to_datetime(src["Date_time"], utc=True, format="ISO8601")
    src["turbine_id"] = src["Wind_turbine_name"].map(m["scada"]["turbine_id"]["map"])
    dup = src.duplicated(["turbine_id", "timestamp"], keep=False)
    uniq = src[~dup]
    j = uniq.merge(df, on=["turbine_id", "timestamp"], how="left")
    checks = {sig: _cmp(j[spec["column"]], j[sig]) for sig, spec in m["scada"]["signals"].items()}
    with tempfile.TemporaryDirectory() as td:
        res = pipeline.export(df, None, name, Path(td), m["rated_power_kw"])
        lab = pd.read_parquet(Path(td) / f"{name}_scada_labeled.parquet")
        qc_ok = float((lab["qc_power_kw"] == 0).mean()) if "qc_power_kw" in lab else float("nan")
    ok = all(v == 0 for v in checks.values()) and len(df) == len(uniq) + dup.sum() // 2
    L += [f"### la_haute_borne ({'PASS' if ok else 'CHECK'})", "",
          "- Different shape: ONE file for all turbines (turbine id column), short tag names, ISO-8601 timestamps with local "
          "UTC offsets (+01:00/+02:00), no status log. Licence Ouverte 2.0 (CC BY 4.0-compatible), ENGIE, via NREL OpenOA.",
          f"- Mapping `mappings/la_haute_borne.yaml`; {len(src):,} raw rows -> {len(df):,} canonical rows, 4 turbines, {secs:.1f} s",
          f"- Every non-duplicated raw row is present with identical values for all {len(checks)} mapped signals: "
          f"{'yes' if all(v == 0 for v in checks.values()) else checks}",
          f"- {int(dup.sum()) // 2} pairs of raw rows share a UTC timestamp (spring DST dates: the exporter wrote the skipped 02:xx hour "
          "as 03:xx+02:00); collapsed to one row each and flagged in the report",
          f"- Hand-off: `pipeline.export` (clean_wind + labeling layout) ran: {res['rows']:,} labeled rows on the full 10-min grid, "
          f"{qc_ok:.1%} of power values QC-good; no events, so no stop/fault labels for this farm",
          f"- Day-1 report: [dq_{name}.md](dq_{name}.md) ({len(s['findings'])} findings)", ""]
    return ok


def kel_reference(raw):
    from make_messy_fixtures import reference
    df, ev, m = reference(raw)
    return df, loader.classify(ev, m)


def prove_messy(name, raw, out_dir, ref, ref_ev, L, desc):
    m, df, log, ev, secs = load(name, raw, ROOT / "mappings" / "examples" / f"{name}.yaml")
    s = dq(name, m, df, log, ev, out_dir)
    sigs = list(m["scada"]["signals"])
    r = ref[(ref["timestamp"] >= df["timestamp"].min()) & (ref["timestamp"] <= df["timestamp"].max())]
    r = r.dropna(subset=sigs, how="all")
    df = df.dropna(subset=sigs, how="all")   # rows with none of this export's signals carry no information to compare
    j = r[["turbine_id", "timestamp"] + sigs].merge(df, on=["turbine_id", "timestamp"], how="outer", suffixes=("_r", "_n"), indicator=True)
    both = j[j["_merge"] == "both"]
    worst = {}
    for sg in sigs:
        d = (both[sg + "_r"] - both[sg + "_n"]).abs()
        rel = d / both[sg + "_r"].abs().clip(lower=1.0)
        worst[sg] = float(rel.max()) if len(rel.dropna()) else 0.0
        if (both[sg + "_r"].isna() != both[sg + "_n"].isna()).any():
            worst[sg] = float("inf")
    missing, extra = int((j["_merge"] == "left_only").sum()), int((j["_merge"] == "right_only").sum())
    ok = max(worst.values()) < 1e-4 and missing == 0 and extra == 0
    L += [f"### {name} ({'PASS' if ok else 'CHECK'})", "", f"- Shape: {desc}",
          f"- Mapping `mappings/examples/{name}.yaml`; {len(log.files)} files, {len(df):,} rows, {secs:.1f} s",
          f"- vs canonical Kelmarsh load (KEL01-02, same period, rows with at least one of the exported signals): {len(both):,} rows matched, {missing} missing, {extra} extra; "
          f"worst relative difference per signal (float formatting / unit round-trip) {max(worst.values()):.1e}"]
    if log.dst:
        d = log.dst.get("scada")
        if d:
            L.append(f"- DST: {d['ambiguous_rows']} rows in the repeated autumn hour resolved with `ambiguous: {d['ambiguous_policy']}`, "
                     f"{d['nonexistent_rows']} non-existent spring rows")
    if ev is not None:
        key = ["turbine_id", "start", "code"]
        a, b = ref_ev.sort_values(key), ev.sort_values(key)
        cls = (a["event_class"].to_numpy() == b["event_class"].to_numpy()).mean() if len(a) == len(b) else float("nan")
        st_ok = len(a) == len(b) and cls == 1.0 and (a["start"].to_numpy() == b["start"].to_numpy()).all()
        ok = ok and st_ok
        L.append(f"- Alarm log (German headers, vendor status words, local time): {len(ev):,} events vs {len(ref_ev):,} reference; "
                 f"identical start times: {'yes' if len(a) == len(b) and (a['start'].to_numpy() == b['start'].to_numpy()).all() else 'no'}; "
                 f"event_class agreement {cls:.4f}; major faults {int(ev['is_major_fault'].sum())} / {int(ref_ev['is_major_fault'].sum())}")
    L += [f"- Day-1 report: [dq_{name}.md](dq_{name}.md) ({len(s['findings'])} findings)", ""]
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--raw-dir", default=str(cfg.RAW_DIR))
    ap.add_argument("--out", default=str(ROOT / "reports" / "ingest"))
    a = ap.parse_args()
    raw, out = Path(a.raw_dir), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if not (raw / "ingest-fixtures" / "acme").exists():
        import subprocess
        subprocess.run([sys.executable, str(ROOT / "scripts" / "make_messy_fixtures.py"), "--raw-dir", str(raw)], check=True)
    L = ["# windml.ingest proof", "",
         "Generated by `scripts/ingest_proof.py` (`make ingest-proof`). Each input is loaded only through its mapping YAML and "
         "compared with an independent reference. Day-1 data-quality reports sit next to this file.", "",
         "| input | shape | reference | result |", "|---|---|---|---|"]
    body, results = [], {}
    results["kelmarsh"] = prove_reference("kelmarsh", raw, out, body)
    results["penmanshiel"] = prove_reference("penmanshiel", raw, out, body)
    results["la_haute_borne"] = prove_lhb(raw, out, body)
    ref, ref_ev = kel_reference(raw)
    ref_ev = ref_ev.copy()
    shapes = {
        "acme_messy": "wide CSV per turbine per month, ';' + decimal comma, latin-1, preamble, vendor tags, W / °F / kPa, "
                      "Europe/London local time with DST, dd.mm.yyyy, interval-END timestamps, vendor alarm log",
        "longco_long": "long tag/value parquet per month, IEC 61400-25 tags, epoch-ms UTC, asset ids 'WTG-01', kPa, unsorted rows",
        "xlsx_sheets": "Excel workbook, one sheet per turbine, title rows above the header, German names, native datetimes",
    }
    for n, d in shapes.items():
        results[n] = prove_messy(n, raw, out, ref, ref_ev, body, d)
    table = {
        "kelmarsh": ("Greenbyte wide CSV, 1 file/turbine, preamble", "data/processed (existing pipeline)"),
        "penmanshiel": ("Greenbyte wide CSV, 1 file/turbine, preamble", "data/processed (existing pipeline)"),
        "la_haute_borne": ("1 file for all turbines, tag names, ISO offsets", "raw file values"),
        "acme_messy": ("messy vendor CSV, local time, W/°F/kPa", "canonical Kelmarsh load"),
        "longco_long": ("long tag/value parquet", "canonical Kelmarsh load"),
        "xlsx_sheets": ("Excel, sheet per turbine", "canonical Kelmarsh load"),
    }
    for n, ok in results.items():
        L.append(f"| {n} | {table[n][0]} | {table[n][1]} | {'PASS' if ok else 'CHECK'} |")
    L += [""] + body
    (out / "proof.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:12 + len(results)]))
    print(f"wrote {out / 'proof.md'}")
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())

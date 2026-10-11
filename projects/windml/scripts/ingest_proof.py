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


def prove_highres(name, raw, out_dir, L, desc):
    """High-res fixture: aggregated bins vs (a) an independent groupby of the written samples and (b) the original
    Kelmarsh 10-min record the samples were generated from."""
    hr = raw / "ingest-fixtures" / "highres"
    tag = name.split("_")[1]
    m, df, log, ev, secs = load(name, raw, ROOT / "mappings" / "examples" / f"{name}.yaml")
    s = dq(name, m, df, log, ev, out_dir)
    tr = pd.read_parquet(hr / f"truth_{tag}.parquet")
    ref = pd.read_parquet(hr / "ref_10min_2022-03.parquet")
    mc = float((m["scada"].get("aggregate") or {}).get("min_coverage", 0.5))
    j = tr.merge(df, on=["turbine_id", "timestamp"], how="outer", suffixes=("_t", ""), indicator=True)
    both = j[j["_merge"] == "both"]
    full = both[both["coverage_t"] >= mc]
    lin = ["power_kw", "wind_speed_ms", "rotor_speed_rpm", "pitch_a_deg", "gear_oil_temp_c", "gear_oil_inlet_pressure_bar", "ambient_temp_c"]
    worst = max(float(((full[c] - full[c + "_t"]).abs() / full[c + "_t"].abs().clip(lower=1)).max()) for c in lin + ["power_kw_std", "power_kw_min", "power_kw_max"])
    n_ok = bool((both["n_samples"] == both["n_samples_t"]).all())
    blank = both[both["coverage_t"] < mc]
    blank_ok = bool(blank["power_kw"].isna().all())
    r = ref.merge(df, on=["turbine_id", "timestamp"], suffixes=("_ref", ""))
    rf = r[r["coverage"] >= 1.0]
    mean_err = float(((rf["power_kw"] - rf["power_kw_ref"]).abs() / rf["power_kw_ref"].abs().clip(lower=1)).max())
    std_err = float((rf["power_kw_std"] - rf["power_kw__std"].fillna(0)).abs().max())
    dn = (rf["nacelle_position_deg"] - rf["nacelle_position_deg_ref"] + 180) % 360 - 180
    ok = (j["_merge"] == "both").all() and worst < 1e-6 and n_ok and blank_ok and mean_err < 1e-6 and std_err < 1e-4
    iv = ", ".join(sorted({v["interval"] for v in log.native_interval.values()}))
    L += [f"### {name} ({'PASS' if ok else 'CHECK'})", "", f"- Shape: {desc}",
          f"- Mapping `mappings/examples/{name}.yaml`; native interval detected: {iv}; {len(df):,} 10-min bins from "
          f"{sum(f['rows'] for f in log.files):,} samples in {secs:.1f} s",
          f"- vs an independent groupby of the samples actually written: {int((j['_merge'] == 'both').sum()):,} bins matched, "
          f"{int((j['_merge'] != 'both').sum())} unmatched; sample counts identical: {'yes' if n_ok else 'no'}; worst relative difference "
          f"(means, power min/max/std) {worst:.1e}; {len(blank)} bins under {mc:.0%} coverage blanked: {'yes' if blank_ok else 'no'}",
          f"- vs the original Kelmarsh 10-min record ({len(rf):,} complete bins): power mean max rel. error {mean_err:.1e}, "
          f"power std vs Greenbyte std max abs. error {std_err:.1e} kW; nacelle circular mean vs the 10-min value: median "
          f"{float(dn.abs().median()):.2f}°, 99th percentile {float(dn.abs().quantile(0.99)):.2f}° (bins with large in-bin yaw "
          "movement differ because the generator spreads samples linearly; the loader uses the circular mean)",
          f"- Day-1 report: [dq_{name}.md](dq_{name}.md) ({len(s['findings'])} findings)", ""]
    return ok


def prove_smarteole(raw, out_dir, L):
    """Real open 1-min data (SMARTEOLE, ENGIE): the loader's 10-min bins vs an independent pandas computation from the
    raw CSV columns (count-weighted mean, min of minima, max of maxima, pooled std of the underlying ~1 Hz samples)."""
    m, df, log, ev, secs = load("smarteole", raw, ROOT / "mappings" / "smarteole.yaml")
    s = dq("smarteole", m, df, log, ev, out_dir)
    mc = float(m["scada"]["aggregate"]["min_coverage"])
    raw_csv = raw / "smarteole" / "SMARTEOLE_WakeSteering_SCADA_1minData.csv"
    worst, nb, nblank_ok = 0.0, 0, True
    for n in (1, 3, 6):
        c = {k: f"active_power_{n}_{k}" for k in ("avg", "min", "max", "std", "count")}
        r = pd.read_csv(raw_csv, usecols=["time", *c.values()])
        r = r.dropna(subset=[c["avg"]]).drop_duplicates("time")
        r["bin"] = pd.to_datetime(r["time"]).dt.floor("10min")   # canonical stamps = interval start (as Greenbyte)
        w = r[c["count"]].fillna(0)
        r[c["std"]] = r[c["std"]].mask(r[c["std"]].isna() & (w <= 1), 0.0)   # one underlying sample: std 0
        g = r.assign(w=w, mw=w * r[c["avg"]], m2=w * (r[c["std"]] ** 2 + r[c["avg"]] ** 2)).groupby("bin")
        ref = pd.DataFrame({"n": g.size(), "mean": g["mw"].sum() / g["w"].sum(), "mn": g[c["min"]].min(), "mx": g[c["max"]].max()})
        ref["std"] = np.sqrt((g["m2"].sum() / g["w"].sum() - ref["mean"] ** 2).clip(lower=0))
        ref = ref[ref["n"] >= mc * 10]
        d = df[df["turbine_id"] == f"SMV{n}"].set_index("timestamp")
        d.index = d.index.tz_localize(None) if d.index.tz is not None else d.index
        j = ref.join(d[["power_kw", "power_kw_min", "power_kw_max", "power_kw_std"]], how="left")
        nblank_ok &= bool(j["power_kw"].notna().all())
        for a, b in (("mean", "power_kw"), ("mn", "power_kw_min"), ("mx", "power_kw_max"), ("std", "power_kw_std")):
            worst = max(worst, float(((j[a] - j[b]).abs() / j[a].abs().clip(lower=1)).max()))
        nb += len(j)
    within = df["power_kw_std"] ** 2
    iv = ", ".join(sorted({v["interval"] for v in log.native_interval.values()}))
    ok = worst < 1e-6 and nblank_ok
    L += [f"### smarteole ({'PASS' if ok else 'CHECK'})", "",
          "- Real open high-res data: SMARTEOLE wind-farm-control dataset (ENGIE / SMARTEOLE consortium, Zenodo 7342466, "
          "Licence Ouverte 2.0), 7x Senvion MM82, Feb-May 2020. One CSV, turbine number inside each column name, 1-min "
          "avg/min/max/std/count of ~1 Hz samples. Time zone/stamp convention not documented: UTC + interval-start assumed.",
          f"- Mapping `mappings/smarteole.yaml`; native interval detected: {iv}; {len(df):,} 10-min bins, 7 turbines, in {secs:.1f} s",
          f"- vs an independent pandas computation from the raw columns (SMV1, SMV3, SMV6 power; {nb:,} bins with >= {mc:.0%} "
          f"of minutes): worst relative difference of mean / min / max / pooled std {worst:.1e}; all such bins present: "
          f"{'yes' if nblank_ok else 'no'}",
          f"- The pooled 10-min power std (median {float(np.sqrt(within).median()):.0f} kW) describes the underlying 1-Hz signal; "
          "a std of the ten 1-min means alone would understate it.",
          f"- Day-1 report: [dq_smarteole.md](dq_smarteole.md) ({len(s['findings'])} findings)", ""]
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--raw-dir", default=str(cfg.RAW_DIR))
    ap.add_argument("--out", default=str(ROOT / "reports" / "ingest"))
    a = ap.parse_args()
    raw, out = Path(a.raw_dir), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    import subprocess
    if not (raw / "ingest-fixtures" / "acme").exists():
        subprocess.run([sys.executable, str(ROOT / "scripts" / "make_messy_fixtures.py"), "--raw-dir", str(raw)], check=True)
    if not (raw / "ingest-fixtures" / "highres" / "truth_1s.parquet").exists():
        subprocess.run([sys.executable, str(ROOT / "scripts" / "make_highres_fixtures.py"), "--raw-dir", str(raw)], check=True)
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
    hr_shapes = {
        "highres_1min": "1-min CSV, ';' + decimal comma, Europe/London local time across the spring DST change, END-of-minute stamps, "
                        "state code, 5% random dropouts, a 2-h outage, a sparse hour",
        "highres_1s": "1-s wide parquet (172,800 samples), UTC, start stamps",
    }
    for n, d in hr_shapes.items():
        results[n] = prove_highres(n, raw, out, body, d)
    if (raw / "smarteole" / "SMARTEOLE_WakeSteering_SCADA_1minData.csv").exists():   # optional: scripts/download_smarteole.py
        results["smarteole"] = prove_smarteole(raw, out, body)
    table = {
        "kelmarsh": ("Greenbyte wide CSV, 1 file/turbine, preamble", "data/processed (existing pipeline)"),
        "penmanshiel": ("Greenbyte wide CSV, 1 file/turbine, preamble", "data/processed (existing pipeline)"),
        "la_haute_borne": ("1 file for all turbines, tag names, ISO offsets", "raw file values"),
        "acme_messy": ("messy vendor CSV, local time, W/°F/kPa", "canonical Kelmarsh load"),
        "longco_long": ("long tag/value parquet", "canonical Kelmarsh load"),
        "xlsx_sheets": ("Excel, sheet per turbine", "canonical Kelmarsh load"),
        "highres_1min": ("1-min CSV, local time, dropouts -> 10-min", "sample groupby + Kelmarsh 10-min"),
        "highres_1s": ("1-s parquet -> 10-min", "sample groupby + Kelmarsh 10-min"),
        "smarteole": ("real 1-min avg/min/max/std/count, turbine in column names", "raw-column pandas computation"),
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

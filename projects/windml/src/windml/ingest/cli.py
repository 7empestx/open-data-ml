"""windml ingest suggest | validate | load | schema"""
from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path

from .. import config as cfg


def _raw(a) -> Path:
    return Path(a.raw_dir) if a.raw_dir else cfg.RAW_DIR


def cmd_suggest(a) -> int:
    from . import suggest, mapping
    import yaml
    s = suggest.suggest(a.sample, raw_dir=_raw(a), nrows=a.nrows)
    text = suggest.to_yaml(s, a.name or Path(a.sample).stem.split("_")[0].lower())
    mapping.validate(yaml.safe_load(text))  # the draft must at least be structurally valid
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")
        low = [n for n, r in s.signals.items() if r["confidence"] < 0.8]
        print(f"wrote {a.out}: {len(s.signals)} signals mapped ({len(low)} below 0.8 confidence: {', '.join(low) or '-'}), "
              f"{len(s.unmapped)} columns unmapped. Review every CHECK line, then: windml ingest validate --mapping {a.out}")
    else:
        sys.stdout.write(text)
    return 0


def _load(a):
    from . import mapping, loader
    m = mapping.load_mapping(a.mapping)
    t0 = time.time()
    keep = None
    if getattr(a, "keep_raw", False):
        keep = Path(a.out) / f"{a.farm or m['name']}_raw_highres.parquet"
    df, log = loader.load_scada(m, _raw(a), limit_files=a.limit_files, keep_raw=keep)
    ev = None
    if m.get("status") and not a.no_status:
        ev = loader.classify(loader.load_status(m, _raw(a), log), m)
    print(f"loaded {len(df):,} rows, {df['turbine_id'].nunique()} turbines, {len(log.files)} files"
          + (f", {len(ev):,} events" if ev is not None else "") + f" in {time.time() - t0:.1f}s")
    return m, df, log, ev


def _report(m, df, log, ev, out_md: Path):
    from . import quality
    md, summary = quality.build(df, log, ev, m)
    quality.write(md, out_md)
    print(f"data-quality report: {out_md} (+ .html)")
    for f in summary["findings"]:
        print("  - " + f.replace("**", ""))
    return summary


def cmd_validate(a) -> int:
    from . import mapping
    try:
        m = mapping.load_mapping(a.mapping)
    except mapping.MappingError as e:
        print(f"mapping error: {e}", file=sys.stderr)
        return 1
    print(f"mapping OK: {m['name']} ({len(m['scada']['signals'])} signals, status log: {'yes' if m.get('status') else 'no'})")
    if a.schema_only:
        return 0
    m, df, log, ev = _load(a)
    out = Path(a.report or (cfg.REPORTS_DIR / "ingest" / f"dq_{m['name']}.md"))
    _report(m, df, log, ev, out)
    return 0


def cmd_load(a) -> int:
    from . import pipeline
    m, df, log, ev = _load(a)
    farm = a.farm or m["name"]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out / f"{farm}_canonical.parquet", index=False)
    if ev is not None:
        ev.to_parquet(out / f"{farm}_canonical_events.parquet", index=False)
    print(f"wrote {out / f'{farm}_canonical.parquet'}")
    if a.export:
        res = pipeline.export(df, ev, farm, out, m.get("rated_power_kw", 2050.0))
        print(f"exported pipeline layout ({farm}_scada_10min / _events / _scada_labeled / _extra_<TID>.parquet): "
              f"{res['rows']:,} rows, {res['events']:,} events")
    _report(m, df, log, ev, out / f"dq_{farm}.md")
    (out / f"{farm}_load_log.json").write_text(json.dumps(log.__dict__, default=str, indent=1))
    return 0


def cmd_schema(a) -> int:
    from .schema import schema_markdown
    sys.stdout.write(schema_markdown())
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="windml ingest", description="Map an operator SCADA export onto the canonical windml format.")
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("--raw-dir", help="root for relative file globs (default: WINDML_RAW_DIR)")

    s = sub.add_parser("suggest", help="draft a mapping YAML from a sample export")
    s.add_argument("sample")
    s.add_argument("--out", "-o", help="write the draft here (default: stdout)")
    s.add_argument("--name", help="mapping name (default: from the file name)")
    s.add_argument("--nrows", type=int, default=20_000)
    common(s)
    s.set_defaults(fn=cmd_suggest)

    for name, fn, hlp in (("validate", cmd_validate, "check a mapping, load the data and write the data-quality report"),
                          ("load", cmd_load, "load to canonical parquet (+ --export to the pipeline layout)")):
        v = sub.add_parser(name, help=hlp)
        v.add_argument("--mapping", "-m", required=True)
        v.add_argument("--limit-files", type=int, help="only read the first N files (quick look)")
        v.add_argument("--no-status", action="store_true", help="skip the status/alarm log")
        common(v)
        v.set_defaults(fn=fn)
        if name == "validate":
            v.add_argument("--report", help="report path (.md; .html written next to it). Default: $WINDML_REPORTS_DIR/ingest/dq_<name>.md")
            v.add_argument("--schema-only", action="store_true", help="only check the YAML, do not read data")
        else:
            v.add_argument("--out", required=True, help="output directory")
            v.add_argument("--farm", help="farm name for output files (default: mapping name)")
            v.add_argument("--export", action="store_true", help="also clean + label and write the all-years pipeline layout")
            v.add_argument("--keep-raw", action="store_true",
                           help="for high-res input (< 10 min): also write the un-aggregated canonical samples (<farm>_raw_highres.parquet)")

    sc = sub.add_parser("schema", help="print the canonical schema (markdown)")
    sc.set_defaults(fn=cmd_schema)
    return p


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())

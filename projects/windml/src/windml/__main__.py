"""`python -m windml ingest ...` (the bin/windml wrapper calls this)."""
import sys


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print("usage: windml ingest {suggest,validate,load,schema} ...\n       windml report --mapping M --out DIR [...]")
        return 0
    if argv[0] == "ingest":
        from .ingest.cli import main as ingest_main
        return ingest_main(argv[1:])
    if argv[0] == "report":
        from .fleet.cli import main as report_main
        return report_main(argv[1:])
    print(f"windml: unknown command {argv[0]!r} (try: windml ingest --help, windml report --help)", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

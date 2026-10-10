"""Central path and run configuration for windml.

Every script reads its paths from here, so nothing is tied to one machine. Override with environment variables:

    WINDML_RAW_DIR      raw downloads (Zenodo zips + extracted CSVs)   default: projects/windml/data/raw
    WINDML_DATA_DIR     derived data (processed/, nbm_years/, trip/...)  default: projects/windml/data
    WINDML_REPORTS_DIR  generated reports, tables, figures              default: projects/windml/reports
    WINDML_LOG_DIR      logs from long (nohup) jobs                     default: projects/windml/logs

Optional subset filters (used by the smoke test, empty = everything):

    WINDML_YEARS        e.g. "2016-2017" or "2016,2018"  SCADA folders whose year is in the set
    WINDML_TURBINES     e.g. "KEL01,KEL02"              turbine ids to read
    WINDML_WORKERS      max worker processes for the per-turbine jobs (default: script-specific)

Expected raw layout (what scripts/download_wind_data.py creates):

    $WINDML_RAW_DIR/kelmarsh-wind-scada/Kelmarsh_WT_static.csv
    $WINDML_RAW_DIR/kelmarsh-wind-scada/scada_<year>/Turbine_Data_*.csv, Status_*.csv
    $WINDML_RAW_DIR/penmanshiel-wind-scada/Penmanshiel_WT_static.csv
    $WINDML_RAW_DIR/penmanshiel-wind-scada/scada_<period>_<turbines>/...
"""
from __future__ import annotations
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # projects/windml


def _path(env: str, default: Path) -> Path:
    v = os.environ.get(env, "").strip()
    return Path(v).expanduser().resolve() if v else default


def _years(spec: str) -> set[int] | None:
    spec = spec.strip()
    if not spec:
        return None
    out: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            out.update(range(int(a), int(b) + 1))
        elif part:
            out.add(int(part))
    return out


def _list(spec: str) -> set[str] | None:
    items = {s.strip().upper() for s in spec.split(",") if s.strip()}
    return items or None


RAW_DIR = _path("WINDML_RAW_DIR", PROJECT_ROOT / "data" / "raw")
DATA_DIR = _path("WINDML_DATA_DIR", PROJECT_ROOT / "data")
REPORTS_DIR = _path("WINDML_REPORTS_DIR", PROJECT_ROOT / "reports")
LOG_DIR = _path("WINDML_LOG_DIR", PROJECT_ROOT / "logs")

PROCESSED_DIR = DATA_DIR / "processed"
ALL_YEARS_DIR = PROCESSED_DIR / "all_years"
NBM_DIR = DATA_DIR / "nbm"
NBM_YEARS_DIR = DATA_DIR / "nbm_years"
TRIP_DIR = DATA_DIR / "trip"
TRIP_PREDS_DIR = DATA_DIR / "trip_preds"

# Source files that live in the repo (templates), never redirected by WINDML_REPORTS_DIR.
CONDITION_TEMPLATE_DIR = PROJECT_ROOT / "reports" / "condition_report" / "src"

YEARS = _years(os.environ.get("WINDML_YEARS", ""))
TURBINES = _list(os.environ.get("WINDML_TURBINES", ""))


def workers(default: int) -> int:
    v = os.environ.get("WINDML_WORKERS", "").strip()
    return max(1, int(v)) if v else default


def describe() -> str:
    return "\n".join(f"{k:<14} {v}" for k, v in [
        ("RAW_DIR", RAW_DIR), ("DATA_DIR", DATA_DIR), ("REPORTS_DIR", REPORTS_DIR), ("LOG_DIR", LOG_DIR),
        ("YEARS", sorted(YEARS) if YEARS else "all"), ("TURBINES", sorted(TURBINES) if TURBINES else "all")])


if __name__ == "__main__":
    print(describe())

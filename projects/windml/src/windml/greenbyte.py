"""Readers for Greenbyte CSV exports (Kelmarsh / Penmanshiel open data)."""
from __future__ import annotations
import re
from pathlib import Path
import pandas as pd

RAW = Path("/workspace/industrial-data")
FARMS = {
    "kelmarsh": {"dir": RAW / "kelmarsh-wind-scada/scada_2022", "static": RAW / "kelmarsh-wind-scada/Kelmarsh_WT_static.csv"},
    "penmanshiel": {"dir": RAW / "penmanshiel-wind-scada/scada_2021_wt11-15", "static": RAW / "penmanshiel-wind-scada/Penmanshiel_WT_static.csv"},
}

# All-years mode: every per-year SCADA folder under each farm's raw dir (scada_<year>[_suffix]/).
# Folders listed in ALL_YEARS_EXCLUDE are superseded by a newer Zenodo version and skipped.
ALL_YEARS_EXCLUDE = {"penmanshiel": {"scada_2021_wt11-15"}}  # H1-2021 file from record 5946808, replaced by full-2021 v4461


def use_all_years() -> None:
    """Switch turbine_files/status_files to read every year folder (call once before cleaning/labeling)."""
    for farm, cfg in FARMS.items():
        root = cfg["static"].parent
        dirs = sorted(d for d in root.glob("scada_*") if d.is_dir() and d.name not in ALL_YEARS_EXCLUDE.get(farm, set()))
        cfg["dirs"] = dirs


def _dirs(farm: str):
    return FARMS[farm].get("dirs") or [FARMS[farm]["dir"]]


def read_header(path: Path) -> dict:
    """Parse the '# key: value' comment header (turbine, type, time zone, interval)."""
    meta = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.startswith("#"):
                break
            m = re.match(r"#\s*([^:]+):\s*(.+)", line.strip())
            if m and "Date and time" not in line:
                meta[m.group(1).strip()] = m.group(2).strip()
    if "Time interval" in meta:
        a, b = re.findall(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", meta["Time interval"])[:2]
        meta["interval_start"], meta["interval_end"] = pd.Timestamp(a, tz=meta.get("Time zone", "UTC")), pd.Timestamp(b, tz=meta.get("Time zone", "UTC"))
    return meta


def _turbine_id(path: Path) -> str:
    m = re.search(r"_(Kelmarsh|Penmanshiel)_(\d+)_", path.name)
    return f"{m.group(1)[:3].upper()}{int(m.group(2)):02d}"


def _skiprows(path: Path) -> int:
    with open(path, encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            if line.startswith("# Date and time") or line.startswith("Timestamp start"):
                return i
            if not line.startswith("#") and line.strip():
                return i
    return 0


def turbine_files(farm: str):
    return sorted(f for d in _dirs(farm) for f in d.glob("Turbine_Data_*.csv"))


def status_files(farm: str):
    return sorted(f for d in _dirs(farm) for f in d.glob("Status_*.csv"))


def read_turbine(path: Path, usecols=None) -> tuple[pd.DataFrame, dict]:
    meta = read_header(path)
    df = pd.read_csv(path, skiprows=_skiprows(path), low_memory=False)
    df = df.rename(columns={df.columns[0]: "timestamp"})
    if usecols is not None:
        df = df[["timestamp"] + [c for c in usecols if c in df.columns]]
    tz = meta.get("Time zone", "UTC")
    df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_localize(tz).dt.tz_convert("UTC")
    df = df.copy()
    df.insert(0, "turbine_id", _turbine_id(path))
    return df, meta


def read_status(path: Path) -> pd.DataFrame:
    meta = read_header(path)
    df = pd.read_csv(path, skiprows=_skiprows(path), dtype=str)
    df.insert(0, "turbine_id", _turbine_id(path))
    df.attrs["meta"] = meta
    return df


def rated_power(farm: str) -> dict:
    s = pd.read_csv(FARMS[farm]["static"])
    out = {}
    for _, r in s.dropna(subset=["Title"]).iterrows():
        num = int(re.search(r"(\d+)$", r["Title"]).group(1))
        out[f"{farm[:3].upper()}{num:02d}"] = float(r["Rated power (kW)"])
    return out

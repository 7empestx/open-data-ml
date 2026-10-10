"""Shared fixtures: a tiny fake raw-data tree in the Greenbyte export format (no downloads)."""
import importlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))


def _turbine_csv(path: Path, n: int, year: int, start: str, end: str, seed: int):
    from windml import clean_wind as cw
    rng = np.random.default_rng(seed)
    ts = pd.date_range(f"{year}-01-01", periods=n, freq="10min")
    wind = rng.uniform(3, 14, n)
    cols = {"Wind speed (m/s)": wind, "Power (kW)": np.clip((wind - 3) * 180, 0, 2050)}
    for name, col in cw.KEY_COLUMNS.items():
        cols.setdefault(col, rng.normal(40, 3, n))
    df = pd.DataFrame(cols)
    df.iloc[5:7, 0] = np.nan  # short gap -> interpolated
    lines = ["# This file was exported by Greenbyte (test fixture).", "#", f"# Turbine: {path.stem}",
             "# Turbine type: Senvion MM92", "# Time zone: UTC", f"# Time interval: {start} - {end} (1 days)", "#",
             '# Data that is missing or is erroneous has been marked with the value "NaN"', "#"]
    body = df.to_csv(index=False, na_rep="NaN").splitlines()
    header = "# Date and time," + body[0]
    rows = [f"{t:%Y-%m-%d %H:%M:%S},{r}" for t, r in zip(ts, body[1:])]
    path.write_text("\n".join(lines + [header] + rows) + "\n", encoding="utf-8")


def _status_csv(path: Path, year: int, start: str, end: str):
    lines = ["# Greenbyte status export (test fixture)", "#", "# Turbine: test", "# Time zone: UTC",
             f"# Time interval: {start} - {end} (1 days)", "#",
             "Timestamp start,Timestamp end,Duration,Status,Code,Message,Comment,Service contract category,IEC category",
             f"{year}-01-01 02:00:00,{year}-01-01 05:00:00,03:00:00,Stop,611,Gear oil pressure too low,,Gearbox (5),Forced outage",
             f"{year}-01-01 08:00:00,{year}-01-01 08:20:00,00:20:00,Stop,111,Emergency stop nacelle,,Emergency stop switch (Nacelle) (11),Forced outage",
             f"{year}-01-01 09:00:00,-,-,Warning,5720,Brake accumulator defect,,Warnings (27),"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


@pytest.fixture
def raw_tree(tmp_path, monkeypatch):
    """Two Kelmarsh turbines x two years, 1 day of 10-min data each. Returns (raw_dir, reload) where reload(**env)
    re-imports windml.config/greenbyte with the given WINDML_* environment."""
    raw = tmp_path / "raw"
    base = raw / "kelmarsh-wind-scada"
    for year in (2016, 2017):
        d = base / f"scada_{year}"
        d.mkdir(parents=True)
        start, end = f"{year}-01-01 00:00:00", f"{year}-01-02 00:00:00"
        for t in (1, 2):
            sid = 227 + t
            _turbine_csv(d / f"Turbine_Data_Kelmarsh_{t}_{year}-01-01_-_{year}-01-02_{sid}.csv", 144, year, start, end, seed=year * 10 + t)
            _status_csv(d / f"Status_Kelmarsh_{t}_{year}-01-01_-_{year}-01-02_{sid}.csv", year, start, end)
    (base / "Kelmarsh_WT_static.csv").write_text(
        "Wind Farm,Title,Rated power (kW)\nKelmarsh,Kelmarsh 1,2050\nKelmarsh,Kelmarsh 2,2050\n", encoding="utf-8")

    def reload(**env):
        for k in ("WINDML_YEARS", "WINDML_TURBINES"):
            monkeypatch.delenv(k, raising=False)
        monkeypatch.setenv("WINDML_RAW_DIR", str(raw))
        monkeypatch.setenv("WINDML_DATA_DIR", str(tmp_path / "data"))
        monkeypatch.setenv("WINDML_REPORTS_DIR", str(tmp_path / "reports"))
        for k, v in env.items():
            monkeypatch.setenv(k, v)
        from windml import config, greenbyte
        importlib.reload(config)
        importlib.reload(greenbyte)
        return config, greenbyte

    yield raw, reload
    # restore module state for other tests
    monkeypatch.undo()
    from windml import config, greenbyte
    importlib.reload(config)
    importlib.reload(greenbyte)

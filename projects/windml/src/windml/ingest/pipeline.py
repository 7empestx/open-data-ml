"""Hand a canonical dataset to the existing windml pipeline (cleaning, labeling, all-years file layout)."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from .. import clean_wind as cw
from .schema import FREQ

EXTRA = ["pitch_motor_temp_1_c", "pitch_motor_temp_2_c", "pitch_motor_temp_3_c", "pitch_motor_current_1_a", "pitch_motor_current_2_a",
         "pitch_motor_current_3_a", "hub_temp_c", "gear_oil_pump_pressure_bar", "pitch_a_std_deg", "pitch_b_std_deg", "pitch_c_std_deg"]


def clean(df: pd.DataFrame, rated_kw: float | dict = 2050.0, interval: tuple | None = None) -> tuple[pd.DataFrame, list[dict]]:
    """Run clean_wind.clean_turbine on each turbine of a canonical frame. Pressures are already in bar here."""
    inv = {k: v for k, v in cw.KEY_COLUMNS.items()}
    parts, stats = [], []
    for tid, g in df.groupby("turbine_id", sort=True):
        raw = g.rename(columns=inv)[["timestamp", "turbine_id"] + [v for k, v in inv.items() if k in g.columns]].copy()
        if interval:
            start, end = interval
        else:
            start, end = g["timestamp"].min(), g["timestamp"].max() + pd.Timedelta(FREQ)
        rk = rated_kw.get(tid, 2050.0) if isinstance(rated_kw, dict) else float(rated_kw)
        c, st = cw.clean_turbine(raw, {"interval_start": start, "interval_end": end, "Time zone": "UTC"}, rk)
        parts.append(c)
        stats.append(st)
    return pd.concat(parts, ignore_index=True), stats


def export(df: pd.DataFrame, ev: pd.DataFrame, farm: str, out_dir: Path, rated_kw: float | dict = 2050.0,
           windows=(7, 14, 30)) -> dict:
    """Write the all-years layout the NBM / trip scripts read:
    {farm}_scada_10min.parquet, {farm}_events.parquet, {farm}_scada_labeled.parquet, {farm}_extra_<TID>.parquet."""
    from .. import labeling as lb
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cleaned, stats = clean(df, rated_kw)
    cleaned.insert(1, "farm", farm)
    for k in cw.KEY_COLUMNS:  # same column set for every farm (missing signals -> NaN, qc 2)
        if k not in cleaned:
            cleaned[k] = np.nan
            cleaned[f"qc_{k}"] = np.int8(2)
    cleaned.to_parquet(out_dir / f"{farm}_scada_10min.parquet", index=False)
    if ev is None or ev.empty:
        ev = pd.DataFrame({c: pd.Series(dtype=t) for c, t in [
            ("turbine_id", "str"), ("start", "datetime64[ns, UTC]"), ("end_filled", "datetime64[ns, UTC]"), ("status", "str"),
            ("event_class", "str"), ("is_stop", bool), ("is_fault_stop", bool), ("is_major_fault", bool),
            ("major_episode", "Int64"), ("component", "str"), ("code", "Int64"), ("message", "str")]})
    ev.to_parquet(out_dir / f"{farm}_events.parquet", index=False)
    lab = lb.label_grid(cleaned, ev, windows) if len(ev) else _empty_labels(cleaned, windows)
    lab.to_parquet(out_dir / f"{farm}_scada_labeled.parquet", index=False)
    for tid, g in df.groupby("turbine_id"):
        e = g[["timestamp", "turbine_id"]].copy()
        for c in EXTRA:
            e[c] = g[c].astype("float32") if c in g else np.float32(np.nan)
        e.to_parquet(out_dir / f"{farm}_extra_{tid}.parquet", index=False)
    return {"rows": len(lab), "turbines": sorted(df["turbine_id"].unique()), "events": len(ev), "clean_stats": stats}


def _empty_labels(scada, windows):
    lab = scada.copy()
    for c in ["in_any_stop", "in_fault", "in_major_fault"] + [f"pre_fault_{w}d" for w in windows]:
        lab[c] = False
    lab["days_to_next_major_fault"] = np.nan
    return lab

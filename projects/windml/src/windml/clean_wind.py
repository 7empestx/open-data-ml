"""Clean Greenbyte 10-minute SCADA into a tidy, regular per-turbine grid.

Conventions (verified from the export headers):
* 'Time zone: UTC' in every file header -> timestamps are UTC already.
* Timestamps mark the START of the 10-minute averaging interval: each file runs
  from <interval_start> 00:00 to <interval_end - 10 min> (e.g. 2022-01-01 00:00 to
  2022-12-31 23:50 for 'Time interval: 2022-01-01 00:00:00 - 2023-01-01 00:00:00').

QC bit flags per key column (column `qc_<name>`, int8):
  1 = value interpolated (short gap <= MAX_INTERP_STEPS)
  2 = value missing after cleaning (long gap, left as NaN)
  4 = original value was physically impossible / frozen and was removed
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from . import greenbyte as gb

FREQ = "10min"
MAX_INTERP_STEPS = 3          # 30 minutes
FROZEN_STEPS = 36             # identical value for >= 6 hours -> frozen sensor

# tidy name -> Greenbyte column
KEY_COLUMNS = {
    "power_kw": "Power (kW)",
    "wind_speed_ms": "Wind speed (m/s)",
    "wind_speed_1_ms": "Wind speed Sensor 1 (m/s)",
    "wind_speed_2_ms": "Wind speed Sensor 2 (m/s)",
    "ambient_temp_c": "Nacelle ambient temperature (°C)",
    "nacelle_temp_c": "Nacelle temperature (°C)",
    "rotor_speed_rpm": "Rotor speed (RPM)",
    "generator_speed_rpm": "Generator RPM (RPM)",
    "gear_oil_temp_c": "Gear oil temperature (°C)",
    "gear_oil_inlet_temp_c": "Gear oil inlet temperature (°C)",
    "gear_oil_inlet_pressure_bar": "Gear oil inlet pressure (bar)",
    "main_bearing_front_temp_c": "Front bearing temperature (°C)",   # 'Axle bearing temperature 1'
    "main_bearing_rear_temp_c": "Rear bearing temperature (°C)",     # 'Axle bearing temperature 2'
    "rotor_bearing_temp_c": "Rotor bearing temp (°C)",
    "gen_bearing_front_temp_c": "Generator bearing front temperature (°C)",
    "gen_bearing_rear_temp_c": "Generator bearing rear temperature (°C)",
    "converter_inlet_temp_c": "Ambient temperature (converter) (°C)",
    "pitch_a_deg": "Blade angle (pitch position) A (°)",
    "pitch_b_deg": "Blade angle (pitch position) B (°)",
    "pitch_c_deg": "Blade angle (pitch position) C (°)",
    "nacelle_position_deg": "Nacelle position (°)",
    "yaw_bearing_angle_deg": "Yaw bearing angle (°)",
    "wind_direction_deg": "Wind direction (°)",
    "power_setpoint_kw": "Turbine Power setpoint (kW)",
    "available_capacity_kw": "Available Capacity for Production (kW)",
    "data_availability": "Data Availability",
    "energy_export_kwh": "Energy Export (kWh)",
    "lost_prod_curtail_total_kwh": "Lost Production to Curtailment (Total) (kWh)",
    "lost_prod_downtime_kwh": "Lost Production to Downtime (kWh)",
}
ANGLE_COLS = {"nacelle_position_deg", "yaw_bearing_angle_deg", "wind_direction_deg"}
# continuous sensors checked for frozen values
FROZEN_CHECK = ["wind_speed_ms", "ambient_temp_c", "nacelle_temp_c", "gear_oil_temp_c", "main_bearing_front_temp_c",
                "main_bearing_rear_temp_c", "rotor_bearing_temp_c", "gen_bearing_front_temp_c", "gen_bearing_rear_temp_c",
                "converter_inlet_temp_c"]
NO_INTERP = {"energy_export_kwh", "lost_prod_curtail_total_kwh", "lost_prod_downtime_kwh", "data_availability"}


def _run_lengths(mask: np.ndarray) -> np.ndarray:
    """For each True position, length of the consecutive True run it belongs to."""
    out = np.zeros(len(mask), dtype=np.int64)
    if not mask.any():
        return out
    d = np.diff(np.concatenate([[0], mask.astype(np.int8), [0]]))
    starts, ends = np.where(d == 1)[0], np.where(d == -1)[0]
    for s, e in zip(starts, ends):
        out[s:e] = e - s
    return out


def _frozen_mask(s: pd.Series, steps: int) -> np.ndarray:
    v = s.to_numpy()
    same = np.zeros(len(v), dtype=bool)
    same[1:] = (v[1:] == v[:-1]) & ~np.isnan(v[1:])
    # a run of k equal diffs means k+1 equal values; include the first value of the run
    runs = _run_lengths(same)
    m = runs >= steps - 1
    first = np.where(m & ~np.concatenate([[False], m[:-1]]))[0] - 1
    m[first[first >= 0]] = True
    return m


def physical_limits(rated_kw: float) -> dict:
    temp = (-40.0, 150.0)
    return {
        "power_kw": (-100.0, 1.15 * rated_kw), "power_setpoint_kw": (-1.0, 1.15 * rated_kw),
        "available_capacity_kw": (-1.0, 1.15 * rated_kw),
        "wind_speed_ms": (0.0, 50.0), "wind_speed_1_ms": (0.0, 50.0), "wind_speed_2_ms": (0.0, 50.0),
        "rotor_speed_rpm": (0.0, 30.0), "generator_speed_rpm": (-10.0, 2500.0),
        "pitch_a_deg": (-10.0, 100.0), "pitch_b_deg": (-10.0, 100.0), "pitch_c_deg": (-10.0, 100.0),
        "gear_oil_inlet_pressure_bar": (-5.0, 500.0), "data_availability": (0.0, 1.0),  # pressure: header says bar but values 0-400, unit suspect
        **{k: temp for k in KEY_COLUMNS if k.endswith("_temp_c")},
        **{k: (0.0, 360.0) for k in ANGLE_COLS - {"yaw_bearing_angle_deg"}},
    }


def clean_turbine(df: pd.DataFrame, meta: dict, rated_kw: float) -> tuple[pd.DataFrame, dict]:
    tid = df["turbine_id"].iloc[0]
    stats = {"turbine_id": tid, "raw_rows": len(df)}
    df = df.rename(columns={v: k for k, v in KEY_COLUMNS.items()})
    keep = [k for k in KEY_COLUMNS if k in df.columns]
    stats["missing_key_columns"] = [k for k in KEY_COLUMNS if k not in df.columns]
    df = df[["timestamp"] + keep]
    for c in keep:
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")
    dups = df.duplicated("timestamp").sum()
    stats["duplicate_timestamps"] = int(dups)
    df = df.drop_duplicates("timestamp", keep="first").set_index("timestamp").sort_index()
    off_grid = (df.index != df.index.floor(FREQ)).sum()
    stats["off_grid_timestamps"] = int(off_grid)
    df.index = df.index.floor(FREQ)
    df = df[~df.index.duplicated()]
    start = meta.get("interval_start", df.index.min())
    end = meta.get("interval_end", df.index.max() + pd.Timedelta(FREQ)) - pd.Timedelta(FREQ)
    grid = pd.date_range(start.tz_convert("UTC"), end.tz_convert("UTC"), freq=FREQ, name="timestamp")
    present = pd.Series(True, index=df.index).reindex(grid, fill_value=False)
    df = df.reindex(grid)
    stats["grid_rows"] = len(grid)
    stats["rows_absent_in_source"] = int((~present).sum())
    out = pd.DataFrame(index=grid)
    out["turbine_id"] = tid
    out["row_in_source"] = present.to_numpy()
    # all-NaN row (present but empty) also counts as gap
    core = [c for c in ("power_kw", "wind_speed_ms") if c in keep]
    allnan = df[core].isna().all(axis=1).to_numpy()   # no power and no wind speed -> SCADA gap
    out["row_empty"] = allnan
    gap_runs = _run_lengths(allnan)
    out["gap_steps"] = gap_runs.astype("int32")
    stats["empty_rows"] = int(allnan.sum())
    d = np.diff(np.concatenate([[0], allnan.astype(np.int8), [0]]))
    run_len = np.where(d == -1)[0] - np.where(d == 1)[0]
    stats["empty_row_runs"] = int(len(run_len))
    stats["long_gaps_gt_30min"] = int((run_len > MAX_INTERP_STEPS).sum())
    stats["longest_gap_hours"] = round(float(run_len.max() / 6), 1) if len(run_len) else 0.0
    limits = physical_limits(rated_kw)
    stats["invalid_counts"], stats["frozen_counts"], stats["missing_pct_raw"], stats["missing_pct_clean"] = {}, {}, {}, {}
    for c in keep:
        s = df[c].copy()
        stats["missing_pct_raw"][c] = round(float(s.isna().mean() * 100), 2)
        bad = np.zeros(len(s), dtype=bool)
        if c in limits:
            lo, hi = limits[c]
            bad |= ((s < lo) | (s > hi)).fillna(False).to_numpy()
        if c in FROZEN_CHECK:
            fz = _frozen_mask(s, FROZEN_STEPS)
            stats["frozen_counts"][c] = int((fz & ~bad).sum())
            bad |= fz
        stats["invalid_counts"][c] = int(bad.sum())
        s[bad] = np.nan
        qc = np.where(bad, 4, 0).astype(np.int8)
        na = s.isna().to_numpy()
        runs = _run_lengths(na)
        if c not in NO_INTERP:
            short = na & (runs <= MAX_INTERP_STEPS)
            if c in ANGLE_COLS:
                rad = np.deg2rad(s)
                si = np.sin(rad).interpolate(limit_area="inside")
                co = np.cos(rad).interpolate(limit_area="inside")
                filled = (np.rad2deg(np.arctan2(si, co)) % 360)
            else:
                filled = s.interpolate(limit_area="inside")
            s = s.where(~short, filled)
            qc |= np.where(short & s.notna().to_numpy(), 1, 0).astype(np.int8)
        qc |= np.where(s.isna().to_numpy(), 2, 0).astype(np.int8)
        out[c] = s.to_numpy()
        out[f"qc_{c}"] = qc
        stats["missing_pct_clean"][c] = round(float(s.isna().mean() * 100), 2)
    # derived convenience flags
    out["power_above_rated"] = (out.get("power_kw") > 1.02 * rated_kw).fillna(False)
    out["rated_kw"] = rated_kw
    out.index.name = "timestamp"
    return out.reset_index(), stats


def clean_farm(farm: str) -> tuple[pd.DataFrame, list[dict]]:
    rated = gb.rated_power(farm)
    frames, all_stats = [], []
    for f in gb.turbine_files(farm):
        raw, meta = gb.read_turbine(f, usecols=list(KEY_COLUMNS.values()))
        tid = raw["turbine_id"].iloc[0]
        cleaned, st = clean_turbine(raw, meta, rated.get(tid, 2050.0))
        st["source_file"] = f.name
        st["time_zone_in_header"] = meta.get("Time zone")
        frames.append(cleaned)
        all_stats.append(st)
    df = pd.concat(frames, ignore_index=True)
    df["turbine_id"] = df["turbine_id"].astype("category")
    df.insert(1, "farm", farm)
    return df, all_stats

# Results: data cleaning and failure labeling

This is a summary of the cleaning and failure-labeling work so far. Every number below comes from the reports in `reports/` (`cleaning_wind.md`, `cleaning_stats_*.json`, `labels_*.md`, `schema_*.md`). See those files for full per-column detail. Sources and licenses are in [DATA_SOURCES.md](DATA_SOURCES.md).

## 1. What got cleaned

### Wind SCADA (main focus)

| Wind farm | Turbines | Period (UTC) | 10-minute rows | Outputs |
|---|---|---|---|---|
| Kelmarsh | 6 x Senvion MM92, 2,050 kW (KEL01 to KEL06) | 2022 full year | 315,360 (52,560 per turbine) | `kelmarsh_scada_10min.parquet`, `kelmarsh_events.parquet`, `kelmarsh_scada_labeled.parquet` |
| Penmanshiel | 5 x Senvion MM82, 2,050 kW (PEN11 to PEN15) | 2021-01-01 to 2021-07-01 | 130,320 (26,064 per turbine) | `penmanshiel_scada_10min.parquet`, `penmanshiel_events.parquet`, `penmanshiel_scada_labeled.parquet` |

Cleaning steps (`src/windml/clean_wind.py`):

- Timestamps stored as tz-aware UTC. Every Greenbyte header says UTC. A row at time t covers [t, t+10 min).
- Deduplicated and snapped to a regular 10-minute grid per turbine. No duplicate or off-grid timestamps were found.
- Gap flags added: `row_in_source`, `row_empty`, `gap_steps`.
- Physical-limit checks. Out-of-range values are set to NaN (qc bit 4).
- Frozen-sensor check: an identical value for 6 h or more on wind speed and temperature channels is set to NaN.
- Gaps of 30 min or less are linearly interpolated (angles via sin/cos). Longer gaps are left as NaN. Energy and lost-production counters are never interpolated.
- 29 key columns kept, out of 303 in the source export.

Coverage after cleaning: about 0.4% of power values are still missing, and only 0.01% needed interpolation. Longest outages: KEL01 48.8 h, PEN11 44.8 h, KEL04 25.5 h.

### The other seven datasets (light cleaning and schema profiling)

These were profiled, typed, and saved as parquet. Each one has a `reports/schema_<name>.md`.

| Dataset | Output parquet | What was done |
|---|---|---|
| NREL PVDAQ system 10 (2008) | `nrel_pvdaq_system10_2008.parquet` | 35,130 rows at 15 min. Missing-value sentinel -99999 replaced with NaN. Local standard time converted to UTC (+7 h). `inverter_temp` is entirely missing in 2008. |
| CoMoPI packaging | `comopi_sensors_10min.parquet`, `comopi_alarm_10min.parquet`, `comopi_warnings_10min.parquet` | 8 machines, 10-minute aggregates, UTC. Sensors: 15,704 rows, 0.55% missing. Alarms AL_53 and AL_54 are the fault targets. |
| PIADE packaging | `piade_raw_events.parquet`, `piade_sequences_1h.parquet` | 429,394 state/alarm intervals across 5 machines (2020 to 2021), UTC. Hourly alarm-count sequences: 23,376 rows. |
| Beverage bottling line | `bottling_*.parquet` (4 files) | Production, operating time, and downtime sheets. No sensor channels. Plant-local time kept naive. Downtime event log has 1,388 rows. |
| MetroPT-3 (metro air compressor) | `metropt3.parquet` | 1,516,948 rows at 0.1 Hz. `in_failure` added from the 4 documented air-leak failures (29,954 rows). |
| NASA C-MAPSS (simulated) | `cmapss_all.parquet` | FD001 to FD004 train and test combined: 265,256 rows. RUL column added. |
| UCI hydraulic systems | `hydraulic_cycle_features.parquet` | 2,205 cycles reduced to mean/std/min/max per sensor, with the 5 condition labels. |

## 2. Data problems found

- **Gear oil inlet pressure unit.** It is labeled "bar" but ranges from 0 to about 400, so the unit or scale is wrong (likely 0.01 bar or a raw count). The column is kept, but its absolute values shouldn't be trusted.
- **Negative generator speeds.** A few rows per turbine have negative 10-minute average generator speeds (down to -575 rpm). These were removed.
- **Stuck (frozen) bearing sensors.** Rotor-bearing and generator-bearing temperature channels froze on KEL01, KEL02, KEL04, KEL05, and KEL06, with 36 to 133 rows each set to NaN.
- **No gearbox bearing temperature.** The export only has gear oil temperatures. It also has no time-based availability flag, so use `available_capacity_kw`, `data_availability`, `lost_prod_downtime_kwh`, and the stop labels instead.
- **May pitch-angle week matches a logged fault.** KEL06 pitch C reported impossible angles (down to -187 deg) for 1,013 rows from 12 to 19 May 2022. That is exactly the logged major "Pitch angle deviation" stop (code 555, 2022-05-12 to 2022-05-19), so the sensor data and the event log agree.
- **2022-07-19 heatwave converter stops.** During the UK heatwave on 19 July 2022, four Kelmarsh turbines stopped on converter inlet over-temperature (code 3151). The rules count these as major converter faults, but the cause is weather. Consider excluding them from early-warning targets.
- Smaller issues: wind speed sensor 2 has a -15 m/s fill value on several turbines (removed), and PEN13 has 56 invalid sensor-2 rows. One Kelmarsh row has a converter inlet temperature of -113 C (removed). The Penmanshiel status logs start on 2020-12-21, before the SCADA window. Those events stay in the events table but don't label any rows.

## 3. Failure labels

A major fault is a Stop classified as a fault, on a major component (gearbox, generator, bearing, converter, pitch, yaw, or hydraulics), lasting at least 1 h. Major faults on the same turbine within 24 h of each other are merged into one episode. The rules are in `src/windml/labeling.py`.

| Wind farm | Status events | Stops | Fault stops | Major faults | Major-fault episodes | Major faults by component |
|---|---|---|---|---|---|---|
| Kelmarsh (2022) | 69,850 | 919 | 170 | 12 | 9 | converter 6, pitch 4, hydraulics 1, yaw 1 |
| Penmanshiel (2021 H1) | 26,658 | 453 | 44 | 2 | 2 | pitch 2 |

Notes:
- 4 of the 6 Kelmarsh converter major faults are code 3151 heatwave stops on 2022-07-19 (KEL03 twice, KEL05, KEL06).
- Kelmarsh rows inside a major fault: 3,006 (KEL06 accounts for 2,526 of them). Penmanshiel: 189.

## 4. Pre-failure windows (7, 14, 30 days)

`label_grid` adds `pre_fault_7d`, `pre_fault_14d`, and `pre_fault_30d`. Each flag marks a row that falls inside N days before a major-fault episode start and isn't already in the fault. It also adds `days_to_next_major_fault`, which is NaN when right-censored.

| Wind farm | pre_fault_7d rows | pre_fault_14d rows | pre_fault_30d rows | Total rows |
|---|---|---|---|---|
| Kelmarsh | 9,063 | 18,135 | 36,709 | 315,360 |
| Penmanshiel | 2,014 | 4,030 | 8,638 | 130,320 |

At Penmanshiel only PEN11 and PEN14 have pre-fault rows.

## 5. Next steps

1. **Add more years.** 9 + 2 major-fault episodes is too few to train a reliable early-warning model. Kelmarsh 2016 to 2024 and Penmanshiel 2016 to 2021 are on Zenodo under CC BY 4.0.
2. **Build a normal-behavior model.** Predict component temperatures (gear oil, bearings, converter) from operating conditions on healthy data, and use the residuals as an anomaly score.
3. **Evaluate against the labels.** Check whether the residuals rise inside the 7, 14, and 30 day pre-fault windows. Report the results both with and without the 2022-07-19 heatwave converter stops.
4. Tune the classification rules in `src/windml/labeling.py` as more years are added.

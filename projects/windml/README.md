# windml: wind/solar O&M ML prototype

- **[RESULTS.md](RESULTS.md)**: what got cleaned, the data problems found, failure-label counts, pre-failure windows, and next steps.
- **[DATA_SOURCES.md](DATA_SOURCES.md)**: source, license, and required attribution for each dataset (IMS and SKAB are excluded).

Raw data stays in /workspace/industrial-data (read only). Everything here can be regenerated.

    cd projects/windml
    .venv/bin/python scripts/run_wind_clean.py      # wind SCADA -> data/processed/<farm>_scada_10min.parquet
    .venv/bin/python scripts/run_labeling.py        # status logs -> <farm>_events.parquet, <farm>_scada_labeled.parquet
    .venv/bin/python scripts/profile_and_clean.py   # reports/schema_*.md + parquet for the other datasets

Layout
- src/windml/greenbyte.py: readers for the Greenbyte exports (Kelmarsh, Penmanshiel)
- src/windml/clean_wind.py: 10-minute grid, physical/frozen checks, short-gap interpolation, qc bit flags
- src/windml/labeling.py: event parsing, classification, component tagging, label join (also importable as src/labeling.py)
- src/windml/profile.py: schema/missingness markdown
- data/processed/: parquet outputs
- reports/: schema_<name>.md, cleaning_wind.md, cleaning_stats_<farm>.json, labels_<farm>.md

Environment: uv venv at .venv (pandas 3, pyarrow, numpy, scikit-learn, matplotlib, openpyxl, tabulate).

Licenses: Kelmarsh, Penmanshiel, PVDAQ, CoMoPI, PIADE, bottling, MetroPT-3 and UCI hydraulic are CC BY 4.0; C-MAPSS is a US government work. Credit the sources in any published demo (see DATA_SOURCES.md).

## Failure labeling (src/windml/labeling.py)

    import sys; sys.path.insert(0, "projects/windml/src")
    from windml import labeling as lb
    ev  = lb.classify_events(lb.parse_events("kelmarsh"), major_min_duration="1h", episode_gap="24h")
    lab = lb.label_grid(scada_df, ev, windows_days=(7, 14, 30))
    lb.summarize(ev)

- parse_events: one row per status-log event (start, end, end_filled, duration, status, code, message, service and IEC category). Instantaneous events ('-' end) get end = start; open-ended stops run to the end of the file.
- classify_events: event_class is one of fault, curtailment, maintenance, grid, weather, routine (battery test, cable unwind, oil flushing), other, or info. Rules are checked in order: message keywords, then the manufacturer's service-contract category, then the IEC category. component comes from message keywords (gearbox, generator, bearing, converter, pitch, yaw, hydraulics, brake, sensor_met, tower, rotor, electrical, control_comm). is_major_fault means a fault Stop on a major component lasting at least major_min_duration. Major faults within episode_gap of each other are merged into a major_episode.
- label_grid adds these to the 10-minute grid: in_any_stop, in_fault, in_major_fault, in_stop_<class>, days_to_next_major_fault (NaN if right-censored), and pre_fault_<N>d (inside N days before an episode start and not already in the fault).
- Rule tables (COMPONENT_RULES, MSG_CLASS_RULES, SERVICE_CLASS, IEC_CLASS, MAJOR_COMPONENTS) sit at the top of the file. Tune them there.
- Caveats: one year at Kelmarsh and half a year at Penmanshiel gives only 9 + 2 major-fault episodes, which is too few to train a reliable early-warning model. Use these for anomaly-detection evaluation and add more years (Kelmarsh 2016 to 2024 and Penmanshiel 2016 to 2021 are on Zenodo under CC BY 4.0).

## Normal-behaviour model (src/windml/nbm.py)

The NBM learns per-turbine healthy drivetrain temperatures from operating conditions and scores residual drift. It is forward-chained by month, uses no leakage, and runs on CPU only.

```
.venv/bin/python scripts/run_nbm.py          # train (~7 min on 8 cores) -> data/nbm/ (git-ignored, regenerable)
.venv/bin/python scripts/eval_nbm.py         # detection, lead time, false alarms, chance baselines -> reports/nbm_*.csv
.venv/bin/python scripts/report_nbm.py       # figures in reports/figures/ + reports/nbm_tables.md
.venv/bin/python scripts/inspect_alarms.py 4 # fleet-relative alarm events with driving target
```

Results and caveats: [reports/nbm_baseline.md](reports/nbm_baseline.md).

## All-years NBM (src/windml/nbm_years.py)

Walk-forward-by-year normal-behaviour models for gearbox oil-system and pitch faults, using 2016–2024 data. Long jobs run under nohup with logs in /workspace/logs/. Results are cached per turbine, so a rerun resumes where it stopped.

```
.venv/bin/python scripts/extract_extra_signals.py      # pitch-motor temps, hub temp, oil pump pressure from the raw CSVs already on the box
nohup .venv/bin/python scripts/run_nbm_years.py > /workspace/logs/nbm_years.log 2>&1 &   # ~23 min -> data/nbm_years/ (git-ignored)
.venv/bin/python scripts/eval_nbm_years.py             # grid, selection on 2017-2020, held-out 2021-2024 -> reports/nbmy_*.csv
.venv/bin/python scripts/report_nbm_years.py           # figures + reports/nbmy_tables.md
```

Results: [reports/nbm_all_years.md](reports/nbm_all_years.md).

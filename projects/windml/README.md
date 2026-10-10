# windml: wind/solar O&M ML prototype

- **[RESULTS.md](RESULTS.md)**: what got cleaned, the data problems found, failure-label counts, pre-failure windows, and next steps.
- **[DATA_SOURCES.md](DATA_SOURCES.md)**: source, license, and required attribution for each dataset (IMS and SKAB are excluded).

## Reproduce

Everything below runs from `projects/windml`. Raw data is downloaded from Zenodo (CC BY 4.0) and never committed.

**Prerequisites**
- Linux or macOS, Python 3.11+ (tested with 3.13), `make`, `curl`/internet access to zenodo.org.
- Full run: 8 CPU cores and 16 GB RAM recommended (jobs stream one turbine at a time). The smoke test runs on a laptop.
- Optional: Google Chrome or Chromium for the condition-report PDF (`WINDML_CHROME=/path/to/chrome`); without it the markdown report is still built.

**Disk space**

| | Download | On disk |
|---|---|---|
| Smoke test (Kelmarsh 2016-2018) | ~535 MB | ~2.6 GB |
| Full data (Kelmarsh + Penmanshiel 2016-2024) | ~9.7 GB of zips | ~40 GB raw (~30 GB with `--delete-zips`) + ~4.5 GB derived |

**Commands**

```bash
git clone https://github.com/7empestx/open-data-ml && cd open-data-ml/projects/windml
make setup        # .venv with the pinned requirements.txt
make smoke        # download Kelmarsh 2016-2018, run preprocess -> NBM -> trip models on KEL01/KEL02, check outputs
make test         # unit tests on tiny fixtures (no data)

# full reproduction, step by step (each step is cached/resumable and logs to logs/<step>.log)
make download     # Kelmarsh + Penmanshiel from Zenodo, MD5-verified
make preprocess   # clean + label all years, extract extra and 10-min statistic signals
make nbm          # walk-forward-by-year normal-behaviour models
make nbm-eval     # selection on 2017-2020, held out 2021-2024 -> reports/nbmy_*
make trip         # hourly trip features + 24/48/72 h classifiers
make trip-eval    # -> reports/trip_*
make report       # sample condition report -> reports/condition_report/
# or all of it in the background:
nohup make all > logs/all.log 2>&1 &
```

**Expected runtimes** (8-core Linux box; download speed depends on Zenodo, typically 1-3 MB/s per file)

| Step | Time |
|---|---|
| `make setup` | ~1 min |
| `make smoke` | ~7 min, most of it the 535 MB download; ~1 min of compute |
| `make download` (full) | 1-3 h download + ~1 h extraction (the padded 2023/2024 files are de-duplicated) |
| `make preprocess` | ~1 h |
| `make nbm` | ~25 min |
| `make trip` | ~25 min (features ~5 min, 36 model sets ~20 min) |
| `make nbm-eval`, `make trip-eval`, `make report` | a few minutes each |

The smoke test is a real check, not a mock. Its 2018 NBM z-scores for KEL01 and KEL02 are identical (max difference 0.0) to the full run's 2018 scores, because both train on 2016-2017 only.

**Paths and subsets** (see `src/windml/config.py`; `make config` prints the resolved values)

| Variable | Default | Meaning |
|---|---|---|
| `WINDML_RAW_DIR` | `data/raw` | Zenodo zips and extracted CSVs |
| `WINDML_DATA_DIR` | `data` | derived data: `processed/`, `nbm_years/`, `trip/`, `trip_preds/` |
| `WINDML_REPORTS_DIR` | `reports` | generated tables, figures and markdown |
| `WINDML_LOG_DIR` | `logs` | step logs |
| `WINDML_YEARS`, `WINDML_TURBINES` | all | subset, e.g. `2016-2018`, `KEL01,KEL02` |
| `WINDML_WORKERS` | per script | max parallel processes (lower it on small machines) |

`make smoke` writes everything under `data/smoke/` and never touches the committed `data/processed/` or `reports/`.
NASA C-MAPSS (a side dataset, not used by windml) has its own script: `make download-cmapss`.

### Single-period sets (Kelmarsh 2022, Penmanshiel H1-2021)

The first labeling and NBM baseline used one period per farm (`data/processed/<farm>_*.parquet`, committed):

    .venv/bin/python scripts/run_wind_clean.py      # wind SCADA -> data/processed/<farm>_scada_10min.parquet
    .venv/bin/python scripts/run_labeling.py        # status logs -> <farm>_events.parquet, <farm>_scada_labeled.parquet
    .venv/bin/python scripts/profile_and_clean.py   # reports/schema_*.md + parquet for the other (non-wind) datasets

These read `$WINDML_RAW_DIR/kelmarsh-wind-scada/scada_2022` and `$WINDML_RAW_DIR/penmanshiel-wind-scada/scada_2021_wt11-15`
(the H1-2021 file from the older Zenodo record 5946808, which `make download` does not fetch).

Layout
- src/windml/config.py: all paths (WINDML_* environment variables) and optional year/turbine subsets
- src/windml/greenbyte.py: readers for the Greenbyte exports (Kelmarsh, Penmanshiel)
- src/windml/clean_wind.py: 10-minute grid, physical/frozen checks, short-gap interpolation, qc bit flags
- src/windml/labeling.py: event parsing, classification, component tagging, label join (also importable as src/labeling.py)
- src/windml/profile.py: schema/missingness markdown
- data/processed/: parquet outputs
- reports/: schema_<name>.md, cleaning_wind.md, cleaning_stats_<farm>.json, labels_<farm>.md

Environment: `.venv` from `make setup` (pinned in requirements.txt: pandas 3, pyarrow, numpy, LightGBM, scikit-learn, matplotlib, tabulate, markdown). `scripts/profile_and_clean.py` (the side datasets) also needs `openpyxl` for the bottling-line Excel file.

Licenses: Kelmarsh, Penmanshiel, PVDAQ, CoMoPI, PIADE, bottling, MetroPT-3 and UCI hydraulic are CC BY 4.0; C-MAPSS has no stated license, so it is not committed (fetch it with `scripts/download_cmapss.sh`). Credit the sources in any published demo (see DATA_SOURCES.md).

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

Walk-forward-by-year normal-behaviour models for gearbox oil-system and pitch faults, using 2016–2024 data. Long jobs run under nohup with logs in logs/. Results are cached per turbine, so a rerun resumes where it stopped.

```
.venv/bin/python scripts/extract_extra_signals.py      # pitch-motor temps, hub temp, oil pump pressure from the raw CSVs
nohup .venv/bin/python scripts/run_nbm_years.py > logs/nbm_years.log 2>&1 &   # ~23 min -> data/nbm_years/ (git-ignored)
.venv/bin/python scripts/eval_nbm_years.py             # grid, selection on 2017-2020, held-out 2021-2024 -> reports/nbmy_*.csv
.venv/bin/python scripts/report_nbm_years.py           # figures + reports/nbmy_tables.md
```

Results: [reports/nbm_all_years.md](reports/nbm_all_years.md).

## Short-term trip prediction (src/windml/trip_features.py)

24 / 48 / 72 h oil-system and pitch trip classifiers. All steps are cached, run under nohup and log to logs/.

```
nohup .venv/bin/python scripts/extract_stat_signals.py > logs/extract_stats.log 2>&1 &   # 10-min min/max/std from raw CSVs
nohup .venv/bin/python scripts/build_trip_features.py > logs/trip_features.log 2>&1 &    # -> data/trip/ (git-ignored)
nohup .venv/bin/python scripts/run_trip_models.py > logs/trip_models.log 2>&1 &          # -> data/trip_preds/ (git-ignored)
.venv/bin/python scripts/eval_trip.py && .venv/bin/python scripts/report_trip.py
```

Results: [reports/trip_shortterm.md](reports/trip_shortterm.md).

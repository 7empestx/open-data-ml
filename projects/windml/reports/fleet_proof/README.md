# `windml report`: proof runs

One command per farm, each from the raw files through its mapping to `condition_report.{md,html,pdf}` + `figures/`,
`tables/` and `run.json` (8-core Linux box, `--workers 2`, cold cache, wall-clock from `time`):

| farm | command | turbines, history | labels | models | flags | cold run | PDF |
|---|---|---|---|---|---|---|---|
| Kelmarsh | `bin/windml report --mapping mappings/kelmarsh_all_years.yaml --out reports/kelmarsh` | 6, 2016-2024 | alarm log | walk-forward, 14 targets | 6 GREEN (was 2 RED, 2 AMBER, 2 GREEN) | 9 min 53 s (prepare 47 s, models 529 s, metrics 14 s, render 2 s) | [9 pages](../kelmarsh/condition_report.pdf) |
| Penmanshiel | `bin/windml report --mapping mappings/penmanshiel_all_years.yaml --out reports/penmanshiel` | 14, 2016-2023/2024 | alarm log | walk-forward, 14 targets | 1 RED, 3 AMBER, 10 GREEN (was 8 RED, 4 AMBER, 2 GREEN) | 16 min 42 s (prepare 103 s, models 864 s, metrics 31 s, render 3 s) | [13 pages](../penmanshiel/condition_report.pdf) |
| La Haute Borne | `bin/windml report --mapping mappings/la_haute_borne.yaml --out reports/la_haute_borne` | 4, 2014-2015 | **none** (inferred from SCADA) | walk-forward, 2 targets (power curve, pitch) | 4 GREEN | 7 s | [7 pages](../la_haute_borne/condition_report.pdf) |
| acme_messy (synthetic) | `bin/windml report --mapping mappings/examples/acme_messy.yaml --out reports/acme_messy` | 2, 12 months (2022) | German alarm log | **cross-fit** (short history), 5 targets | 2 GREEN | 17 s | [8 pages](../acme_messy/condition_report.pdf) |

Flags in the table are from the calibrated rules (below); "was" = the first version's fixed heuristic rules. A rerun
with a warm cache (`data/fleet/<farm>/`) takes 2-45 s (indicators, metrics and render only). Peak memory is ~1.3 GB per
worker on a 9-year turbine.

## Calibrated ratings

The first version reused the hand-built report's fixed RAG rules and put 8 of 14 Penmanshiel turbines on red. The
ratings are now calibrated against the alarm-log events ([calibration.md](calibration.md),
`scripts/calibrate_flags.py`): one row per turbine per month-end, outcome = a logged event in the next 90 days,
thresholds selected on 2017-2020 and checked on 2021-2024. Only rule families whose flags concentrated before events
set the colour (gear-oil pump build-up vs peers, repeat oil or pitch trips, sensor faults); availability and
model-based abnormal-day rates are shown as notes. On the held-out years 89% of turbine-months are green, 9% amber,
2% red; amber or red turbine-months were followed by an event 76% of the time vs 50% for random turbines in the same
months (recall 19%). Red alone did not beat chance by much (65% vs 58%, 17 turbine-months): it marks a strong or
persistent signal, not a much higher probability.

| farm | old rules (red / amber / green) | calibrated (red / amber / green) | now flagged |
|---|---|---|---|
| Kelmarsh | 2 / 2 / 2 | 0 / 0 / 6 | none (KEL06: availability 89.6% shown as a note) |
| Penmanshiel | 8 / 4 / 2 | 1 / 3 / 10 | PEN14 red (pump +2.3 bar vs peers); PEN02, PEN04, PEN09 amber (5, 9, 4 oil-trip episodes in 6 months, trips stopped by Dec 2023) |
| La Haute Borne | 0 / 0 / 4 | 0 / 0 / 4 | none (no alarm log, no oil pressure: only sensor checks can flag) |
| acme_messy | 0 / 0 / 2 | 0 / 0 / 2 | none |

## Consistency with the hand-built report

[consistency.md](consistency.md) (`scripts/fleet_consistency.py`) compares every metric with the hand-built report.
Availability, fault hours, trip episodes, abnormal-oil-day shares and oil-temperature model-error ratios match to the
printed precision; pump-pressure rises differ by up to 0.05 bar (baseline = all months before the window instead of
2017-2021). With the first version's rules the flags were identical for all 20 turbines; with the calibrated rules
they differ by design (2 of 6 Kelmarsh and 4 of 14 Penmanshiel turbines keep the same colour). Other differences:

- Penmanshiel WT01-10 show ~4.4% missing data instead of 0.2%: the published data has no January 2023 for those
  turbines (no `scada_2023_01` folder). The hand-built pipeline stitched files per period and never saw the gap; the
  new path builds one continuous grid per turbine and reports it.
- The apparent -5% wind-speed drift on PEN11 and PEN15 was an artefact: in 2024 only WT11-15 report, so the peer
  median changed composition. Drift now uses the same peer set before and during the last 3 months.
- KEL04's frozen gear-oil temperature sensors were a single 11-day freeze in July 2023 during a stop; only sensors
  frozen in the last 90 days now flag.

## NBM on an exported farm

[nbm_on_export.md](nbm_on_export.md) (`make nbm-on-export`): KEL01 2016-2018 exported with
`windml ingest load --export`, then the unchanged `scripts/run_nbm_years.py` run on the export. Its z-scores are
identical to the reference run (max difference 0.0, same scored rows).

## Short histories and missing inputs

- 24+ months: walk-forward by calendar year (models trained only on earlier years).
- 12-23 months: cross-fit in 6 blocks with a 3-day embargo (acme_messy). It cannot see a slow change that started
  before the record.
- Under 12 months: no models; trends, drift, data quality and stops remain (`tests/test_fleet_report.py`).
- No alarm log (La Haute Borne): stops inferred from SCADA (power < 1% of rated, wind 4.5-25 m/s); availability,
  trips and fault history are replaced by a note, and confidence is lowered.

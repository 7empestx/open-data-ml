# `windml report`: proof runs

One command per farm, each from the raw files through its mapping to `condition_report.{md,html,pdf}` + `figures/`,
`tables/` and `run.json` (8-core Linux box, `--workers 2`, cold cache, wall-clock from `time`):

| farm | command | turbines, history | labels | models | flags | cold run | PDF |
|---|---|---|---|---|---|---|---|
| Kelmarsh | `bin/windml report --mapping mappings/kelmarsh_all_years.yaml --out reports/kelmarsh` | 6, 2016-2024 | alarm log | walk-forward, 14 targets | 2 RED, 2 AMBER, 2 GREEN | 9 min 53 s (prepare 47 s, models 529 s, metrics 14 s, render 2 s) | [9 pages](../kelmarsh/condition_report.pdf) |
| Penmanshiel | `bin/windml report --mapping mappings/penmanshiel_all_years.yaml --out reports/penmanshiel` | 14, 2016-2023/2024 | alarm log | walk-forward, 14 targets | 8 RED, 4 AMBER, 2 GREEN | 16 min 42 s (prepare 103 s, models 864 s, metrics 31 s, render 3 s) | [13 pages](../penmanshiel/condition_report.pdf) |
| La Haute Borne | `bin/windml report --mapping mappings/la_haute_borne.yaml --out reports/la_haute_borne` | 4, 2014-2015 | **none** (inferred from SCADA) | walk-forward, 2 targets (power curve, pitch) | 4 GREEN | 7 s | [7 pages](../la_haute_borne/condition_report.pdf) |
| acme_messy (synthetic) | `bin/windml report --mapping mappings/examples/acme_messy.yaml --out reports/acme_messy` | 2, 12 months (2022) | German alarm log | **cross-fit** (short history), 5 targets | 2 GREEN | 17 s | [8 pages](../acme_messy/condition_report.pdf) |

A rerun with a warm cache (`data/fleet/<farm>/`) takes 3-35 s (metrics and render only). Peak memory is ~1.3 GB per
worker on a 9-year turbine.

## Consistency with the hand-built report

[consistency.md](consistency.md) (`scripts/fleet_consistency.py`): **same RED/AMBER/GREEN flag for all 6 Kelmarsh and
all 14 Penmanshiel turbines**. Availability, fault hours, trip episodes, abnormal-oil-day shares and oil-temperature
model-error ratios match to the printed precision; pump-pressure rises differ by up to 0.05 bar (baseline = all months
before the window instead of 2017-2021). Two differences worth knowing:

- Penmanshiel WT01-10 show ~4.4% missing data instead of 0.2%: the published data has no January 2023 for those
  turbines (no `scada_2023_01` folder). The hand-built pipeline stitched files per period and never saw the gap; the
  new path builds one continuous grid per turbine and reports it. It does not change any flag.
- New generic triggers (AMBER only) add reasons but no flag changes here: KEL04 stuck gear-oil temperature sensors,
  KEL05 abnormal pitch residuals (37% of final-year days, matching its 11 pitch trip episodes), wind-speed sensor
  drift of about -5% vs the fleet on PEN11 and PEN15.

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

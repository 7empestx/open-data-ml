---
title: windml overview
description: windml tests whether wind turbine faults can be predicted from open 10-minute SCADA data.
---

windml is the first open-data-ml project. It uses 10-minute SCADA data and turbine status logs from two UK wind farms to test whether component faults can be predicted.

## The data

| Wind farm | Turbines | Period | 10-minute rows | Major faults (episodes) |
|---|---|---|---|---|
| Kelmarsh | 6 x Senvion MM92, 2,050 kW (KEL01 to KEL06) | 2016 to 2024 | 2,840,832 | 97 (72) |
| Penmanshiel | 14 x Senvion MM82, 2,050 kW (PEN01, PEN02, PEN04 to PEN15) | 2016 to 2023 for PEN01 to PEN10, 2016 to 2024 for PEN11 to PEN15 | 6,114,096 | 318 (232) |

The first pass used one year of Kelmarsh (2022, 315,360 rows, 12 major faults) and half a year of Penmanshiel (5 turbines, 130,320 rows, 2 major faults). Those single-period sets are still described on the [cleaning](/windml/cleaning/) and [labels](/windml/labels/) pages.

Both datasets were released by Cubico Sustainable Investments on Zenodo under CC BY 4.0. See [Data sources and licenses](/windml/data-sources/).

## Where it stands

1. **Cleaned.** Timestamps aligned to UTC, gaps flagged, bad and frozen sensor values removed, oil-pressure units fixed. See [Cleaning notes](/windml/cleaning/).
2. **Labeled.** Major faults identified from the status logs. See [Failure labels](/windml/labels/).
3. **Tested.** Normal-behavior models and short-term trip models, under a strict walk-forward test. Neither beat chance. See [Results](/windml/results/).
4. **Condition report.** A retrospective health review built from the same data. See the [sample condition report](/windml/condition-report/).

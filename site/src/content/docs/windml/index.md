---
title: windml overview
description: windml looks for early signs of wind turbine faults in open 10-minute SCADA data.
---

windml is the first open-data-ml project. It uses 10-minute SCADA data and turbine event logs from two UK wind farms to look for early signs of component faults.

## The data

| Wind farm | Turbines | Period (UTC) | 10-minute rows |
|---|---|---|---|
| Kelmarsh | 6 x Senvion MM92, 2,050 kW (KEL01 to KEL06) | 2022, full year | 315,360 (52,560 per turbine) |
| Penmanshiel | 5 x Senvion MM82, 2,050 kW (PEN11 to PEN15) | 2021-01-01 to 2021-07-01 | 130,320 (26,064 per turbine) |

Both datasets were released by Cubico Sustainable Investments on Zenodo under CC BY 4.0. See [Data sources and licenses](/windml/data-sources/).

## Where it stands

1. **Cleaned.** Timestamps aligned to UTC, gaps flagged, bad and frozen sensor values removed, short gaps filled. See [Cleaning notes](/windml/cleaning/).
2. **Labeled.** Major faults identified from the event logs: 12 at Kelmarsh (in 9 episodes) and 2 at Penmanshiel. See [Failure labels](/windml/labels/).
3. **Modeling.** Not started in public yet. No results are published. See [Results](/windml/results/).

## The approach

The plan is a normal-behavior model. It learns what each turbine's component temperatures look like under healthy operating conditions, then flags when readings drift away from that. The labels let us test whether those flags appear in the 7, 14, or 30 days before a logged fault.

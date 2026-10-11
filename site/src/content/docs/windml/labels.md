---
title: Failure labels
description: How major faults were labeled from the turbine event logs.
---

## Definition

A **major fault** is a stop that:

- is classified as a fault,
- is on a major component (gearbox, generator, bearing, converter, pitch, yaw, or hydraulics), and
- lasts at least 1 hour.

Major faults on the same turbine within 24 hours of each other are merged into one **episode**.

## All years (used for the results)

The same rules were run on every year published on Zenodo.

| Wind farm | Turbines and years | 10-minute rows | Fault stops | Major faults | Episodes | Major faults by component |
|---|---|---|---|---|---|---|
| Kelmarsh | KEL01 to KEL06, 2016 to 2024 | 2,840,832 | 1,196 | 97 | 72 | converter 44, pitch 28, gearbox 8, generator 7, hydraulics 6, yaw 4 |
| Penmanshiel | PEN01, PEN02, PEN04 to PEN10: 2016 to 2023; PEN11 to PEN15: 2016 to 2024 | 6,114,096 | 3,246 | 318 | 232 | pitch 146, converter 87, gearbox 76, generator 6, hydraulics 3 |

**Still no confirmed mechanical failures.** The status logs record stops, not component replacements.

- Kelmarsh: the 8 gearbox major faults are oil-system and protection stops (low oil pressure 3, oil-cooler fan overload 2, oil-pump overload 1, drivetrain oscillation 1, particle alarm 1). The 7 generator ones are overspeed and speed-sensor stops. There are no bearing stops.
- Penmanshiel: the 76 gearbox major faults (52 episodes) are mostly lubrication stops (missing gear oil 45, low oil pressure 14, pump overload 5, cooler fan overload 3), plus gear-speed sensor 7 and particle alarm 2. The only bearing stops are 4 generator-bearing over-temperature stops on PEN04.
- Kelmarsh has only 1 major fault in 2017 and 1 in 2019, against 5 to 28 in other years. The status logs are complete for those years, so this is real year-to-year variation, not missing data.

## First pass: single periods

The first pass used one year of Kelmarsh and half a year of Penmanshiel. Those counts are kept here for reference.

| Wind farm | Status events | Stops | Fault stops | Major faults | Episodes | Major faults by component |
|---|---|---|---|---|---|---|
| Kelmarsh (2022) | 69,850 | 919 | 170 | 12 | 9 | converter 6, pitch 4, hydraulics 1, yaw 1 |
| Penmanshiel (2021, first half) | 26,658 | 453 | 44 | 2 | 2 | pitch 2 |

Notes:

- 4 of the 6 Kelmarsh converter major faults are code 3151 heatwave stops on 19 July 2022 (KEL03 twice, KEL05, KEL06). The cause was weather, so they may be excluded from early-warning targets.
- Kelmarsh has 3,006 ten-minute rows inside a major fault, and KEL06 accounts for 2,526 of them. Penmanshiel has 189.
- At Penmanshiel, the two major faults are pitch faults on PEN11 (4 to 5 March 2021) and PEN14 (4 to 5 April 2021).

## Pre-fault windows

Each row is also flagged if it falls within 7, 14, or 30 days before the start of a major-fault episode and isn't already inside the fault. These windows are what a model would try to flag early.

| Wind farm | 7-day rows | 14-day rows | 30-day rows | Total rows |
|---|---|---|---|---|
| Kelmarsh | 9,063 | 18,135 | 36,709 | 315,360 |
| Penmanshiel | 2,014 | 4,030 | 8,638 | 130,320 |

9 episodes at Kelmarsh and 2 at Penmanshiel were too few to train or judge an early-warning model, which is why every published year was added. See [Results](/windml/results/) for what the full data showed.

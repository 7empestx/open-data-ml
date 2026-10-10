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

## Counts

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

## Why more data is needed

9 episodes at Kelmarsh and 2 at Penmanshiel are too few to train or judge a reliable early-warning model. More years are available on Zenodo under the same license. See the [Roadmap](/roadmap/).

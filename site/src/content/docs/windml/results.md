---
title: Results
description: What windml found when it tried to predict wind turbine faults from public 10-minute SCADA data.
---

**Short version:** under a strict test, fault prediction from public 10-minute SCADA data, with labels taken from the turbines' stop logs, did not beat chance on the held-out years 2021 to 2024.

That's a negative result, and we're publishing it as one. The data was still useful for a different job: a retrospective [condition report](/windml/condition-report/).

## What was tested

**Data:** every year published on Zenodo.
- Kelmarsh: 6 turbines, 2016 to 2024, 2,840,832 ten-minute rows, 97 major faults in 72 episodes.
- Penmanshiel: 14 turbines, 2016 to 2024 (2016 to 2023 for PEN01 to PEN10), 6,114,096 rows, 318 major faults in 232 episodes.

**Protocol:**
- Walk-forward by year. Each model trains only on earlier years and is tested on the next year.
- All settings were chosen on 2017 to 2020. They were then scored once on 2021 to 2024, with no further tuning.
- Every hit rate is compared with what chance would give, matched for season and for each turbine's usual fault rate.
- For the short-term models, 12 tests were registered in advance with a Bonferroni-corrected threshold of p < 0.0042.

## Normal-behavior models (30-day warning)

These models learn each turbine's normal temperatures and oil pressures from operating conditions, then flag when readings drift.

- **Fit is good.** Healthy gear-oil temperature error is about 0.8 to 1.4 °C, and inlet pressure about 0.2 to 0.3 bar.
- **Gearbox oil-system faults:** 8 of 27 held-out episodes were flagged within 30 days. Chance would give 9.57 (p = 0.82), with 0.72 false alarms per turbine-month.
- **Pitch faults:** 1 of 48 flagged, against 2.22 expected by chance (p = 0.91).
- Across all 168 settings tried per farm and fault type, fewer reached p < 0.05 on the held-out years than chance alone would produce.

## Short-term trip models (24, 48 and 72 hours)

These are supervised models on 1.43 million hourly rows from 20 turbines. They use 10-minute min, max and standard deviation of oil pressures, pitch currents and blade angles, plus trip history and season.

- **Oil-system trips:** PR-AUC 0.011, 0.018 and 0.027 at 24, 48 and 72 hours, against 0.008, 0.013 and 0.020 for a model that only knows the season. The best test had p = 0.006, which doesn't pass the corrected threshold.
- At 48 hours the sensor model caught 19 to 20 of 105 episodes, about twice the turbine-matched chance of about 10. But a season-only model caught 19, and only about 3% of alarms were followed by a trip.
- **Pitch trips:** the sensor signals were at chance. Trip history alone reached PR-AUC 0.12 at 24 hours (prevalence 0.005), and adding sensors gave 0.18 (p = 0.046, not significant). Most of that came from repeat trips at Kelmarsh.

## Likely reasons it didn't work

- **The labels are stops, not failures.** The status logs record what the controller did, such as a low-oil-pressure trip. They don't confirm component damage. Only a handful of real failures, such as a gearbox exchange or a generator bearing replacement, show up in operator comments, which is too few to train or test on.
- **Most faults are fast.** Pitch and converter faults are often electrical or control events. They don't build slowly in temperature or pressure.
- **10-minute averages hide short events.** A trip can come from a few seconds of low pressure that a 10-minute mean smooths away.
- **Season explains most of what looks like signal.** Oil trips peak in cold months. A model that only knows the calendar does nearly as well as one that sees the sensors.
- **Repeat trips are the main predictable pattern.** A turbine that just tripped is more likely to trip again soon. That's useful to know, but it isn't an early warning from the sensors.
- **The test was strict on purpose.** Looser tests, such as tuning on the test years or ignoring seasonal chance, would have produced better-looking numbers that don't hold up.

## What could change the answer

- Higher-resolution data (1 second to 1 minute).
- Maintenance and work-order records, so labels mean physical failures rather than stops.
- Vibration and oil-lab data.

## Full write-ups

The detailed reports are in the project repository (`projects/windml/RESULTS.md`, sections 6 to 9, and `reports/`). The repository is private for now.

*This is research on public data. It's not engineering advice.*

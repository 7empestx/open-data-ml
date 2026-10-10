---
title: Sample condition report
description: A retrospective health report for Kelmarsh and Penmanshiel, built only from public data.
---

The fault-prediction tests [didn't beat chance](/windml/results/). The same public data still supports a useful retrospective review: where downtime came from, which turbines stand out, and which abnormal states lasted for months.

This sample shows what a wind farm health assessment could look like.

**[Download the sample report (PDF)](/condition-report/windml-sample-condition-report.pdf)**

:::caution[Not a failure prediction]
This is a retrospective review of public data, not engineering advice. Any finding should be checked by a qualified engineer, with site records and inspections, before anyone acts on it.
:::

## Sites and data

- **Kelmarsh:** 6 Senvion MM92 turbines (2,050 kW), 2016 to 2024.
- **Penmanshiel:** 14 Senvion MM82 turbines (2,050 kW), mid-2016 to 2023 for PEN01 to PEN10 and to 2024 for PEN11 to PEN15.
- Public 10-minute SCADA and turbine status logs from Cubico Sustainable Investments on Zenodo (CC BY 4.0). No site visits, vibration or oil-lab data.

## What's in it

- A per-turbine scorecard with a red, amber or green flag.
- Downtime and lost production by cause.
- Seasonal and weather patterns.
- Chronic abnormal states, such as gear-oil pump pressure build-ups.
- Model drift and sensor health.
- Recommended actions.

## Kelmarsh highlights

- Technical availability over 2016 to 2024 was 97.9%. It was 99.2% to 99.6% in 2017 to 2020 and fell to 96.5% to 97.6% in 2021 to 2024.
- Three turbines, KEL04, KEL05 and KEL06, account for 83% of fault and maintenance downtime since 2021.
- Gearbox oil-system trips were rare: 14 trips in 10 episodes over nine years.
- The temperature models fit worse at every turbine in 2023 and 2024. At KEL04 this followed a logged gearbox exchange. At the other five there's no logged explanation, so it should be checked before temperature alarms are trusted.

![Kelmarsh model drift](/condition-report/fig6_kelmarsh_drift.png)

## Penmanshiel highlights

- Technical availability over 2017 to 2024 was 98.0%.
- Gearbox lubrication is the signature issue: 440 oil-system trips in 235 episodes, against 14 at Kelmarsh.
- Full-load gear-oil pump pressure built up by 1.8 to 3.7 bar over several months on seven turbines in 2022 and 2023. Six of these ended at a logged oil change, filter inspection or the fleet-wide oil exchange in late 2023.
- PEN14's pump pressure was still rising at the end of the record: 9.9 bar in December 2024, against 7.4 to 8.1 bar in the same month of 2019 to 2023.

![Penmanshiel gear-oil pump pressure](/condition-report/fig5_pen_pump_pressure.png)

## Downtime and seasonality

![Availability by year](/condition-report/fig1_availability.png)

![Downtime by cause](/condition-report/fig2_downtime_by_cause.png)

![Trip seasonality](/condition-report/fig3_trip_seasonality.png)

---

*Data credit: Kelmarsh and Penmanshiel wind farm data, Cubico Sustainable Investments Ltd, published on Zenodo under CC BY 4.0. Figures and tables are derived from that data.*

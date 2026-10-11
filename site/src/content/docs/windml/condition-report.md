---
title: Sample condition report
description: A retrospective health report for Kelmarsh and Penmanshiel, built only from public data.
---

The fault-prediction tests [didn't beat chance](/windml/results/). The same public data still supports a useful retrospective review: where downtime came from, which turbines stand out, and which abnormal states lasted for months.

This sample shows what a wind farm health assessment looks like. The full report has a per-turbine scorecard, the evidence behind every flag and 12 recommended actions.

**[Download the full sample report (PDF, 1.2 MB)](/condition-report/windml-sample-condition-report.pdf)**

Want one for your own fleet? See [Work with us](/work-with-us/).

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

![Two line charts of Kelmarsh model error by test year, 2018 to 2024. Gear-oil temperature error stays between about 0.7 and 0.95 °C at all six turbines through 2022, then rises at every turbine in 2023 and 2024. KEL04 jumps to about 2.0 °C in 2023 and 2.4 °C in 2024 after its July 2023 gearbox exchange. Main-bearing temperature error shows the same pattern.](../../../assets/condition-report/fig6_kelmarsh_drift.png)

*Model error on healthy data, by test year. Each year's model is trained only on earlier years.*

## Penmanshiel highlights

- Technical availability over 2017 to 2024 was 98.0%.
- Gearbox lubrication is the signature issue: 440 oil-system trips in 235 episodes, against 14 at Kelmarsh.
- Full-load gear-oil pump pressure built up by 1.8 to 3.7 bar over several months on seven turbines in 2022 and 2023. Six of these ended at a logged oil change, filter inspection or the fleet-wide oil exchange in late 2023.
- PEN14's pump pressure was still rising at the end of the record: 9.9 bar in December 2024, against 7.4 to 8.1 bar in the same month of 2019 to 2023.

![Line chart of Penmanshiel monthly median gear-oil pump pressure at full load, 2017 to 2024. Most turbines sit between about 7 and 8 bar. In 2022 and 2023 several turbines, including PEN04, PEN05 and PEN15, climb to about 10 to 11.5 bar over several months and drop back at logged services: the PEN15 oil change, the PEN05 and PEN06 filter inspection, and the fleet-wide oil exchange in late 2023. PEN14 rises from about 7.7 bar in August 2024 to 9.9 bar in December 2024, at the end of the record. PEN09 and PEN10 read about half of normal from 2018 to late 2019.](../../../assets/condition-report/fig5_pen_pump_pressure.png)

*Full-load gear-oil pump pressure, monthly median, unit-corrected. Dotted lines mark logged services.*

## Downtime and seasonality

![Heat maps of technical availability per turbine and year. Kelmarsh turbines are mostly at 98 to 100% through 2020, with dips in 2021 to 2024: KEL05 93% and KEL06 91% in 2021, KEL04 91% in 2022, and KEL04 and KEL05 94% in 2023. Penmanshiel is mostly 97 to 99% from 2017, with 2016 low because it was the partial first year, and dips such as PEN04 89% and PEN10 81% in 2023.](../../../assets/condition-report/fig1_availability.png)

*Technical availability: time not in a fault or maintenance stop, per turbine and calendar year.*

![Horizontal bar charts of downtime by cause over all years. At Kelmarsh the largest causes are maintenance (4,720 turbine-hours), grid (2,709) and weather (1,812), followed by converter faults (1,653) and curtailment (1,431). At Penmanshiel the largest are maintenance (15,908), curtailment (7,335) and pitch faults (3,397), followed by weather (3,092) and grid (3,022).](../../../assets/condition-report/fig2_downtime_by_cause.png)

*Downtime by first cause, in turbine-hours and lost production. Red bars are fault stops by component.*

![Bar charts of oil and pitch trip episodes per 100 turbine-months by calendar month, 2017 to 2024. At Kelmarsh, pitch trips dominate and peak in January to March, and oil trips are rare. At Penmanshiel, oil trips are common all year and highest in January, October and November, and pitch trips peak in June and November.](../../../assets/condition-report/fig3_trip_seasonality.png)

*Trip episodes per 100 turbine-months, by calendar month. Both panels use the same scale.*

---

Code for every figure and table is in the [repository](https://github.com/7empestx/open-data-ml/tree/main/projects/windml/reports/condition_report), and [Reproduce it](/windml/reproduce/) shows how to rebuild the report with `make report`.

*Data credit: Kelmarsh and Penmanshiel wind farm data, Cubico Sustainable Investments Ltd, published on Zenodo under CC BY 4.0. Figures and tables are derived from that data.*

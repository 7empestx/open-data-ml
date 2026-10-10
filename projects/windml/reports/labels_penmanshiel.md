# Failure labels: penmanshiel

<!-- all-years:begin -->
## All years (2016-06-02 to 2024-12-31)

Re-run of the same rules on every downloaded year, 14 turbines (PEN01, PEN02, PEN04, PEN05, PEN06, PEN07, PEN08, PEN09, PEN10, PEN11, PEN12, PEN13, PEN14, PEN15), 6,114,096 labeled 10-minute rows. Full detail: [labels_penmanshiel_all_years.md](labels_penmanshiel_all_years.md); data in data/processed/all_years/ (not committed, files > 90 MB; rebuild with scripts/run_all_years.py).

- Events: 1,053,535; fault stops: 3,246
- Major faults: **318 events in 232 episodes**; by component {'pitch': 146, 'converter': 87, 'gearbox': 76, 'generator': 6, 'hydraulics': 3}

|   year |   major_faults |   episodes |
|-------:|---------------:|-----------:|
|   2016 |             52 |         35 |
|   2017 |             29 |         24 |
|   2018 |             20 |         17 |
|   2019 |             47 |         39 |
|   2020 |             63 |         48 |
|   2021 |             30 |         24 |
|   2022 |             32 |         18 |
|   2023 |             33 |         20 |
|   2024 |             12 |          8 |

The section below is the original single-period report.
<!-- all-years:end -->
Source: Greenbyte status logs (2020-12-21 to 2021-06-30, UTC). Rules in src/windml/labeling.py.
Major fault = Stop classified as fault, component in gearbox/generator/bearing/converter/pitch/yaw/hydraulics, duration >= 1 h; major faults on the same turbine within 24 h are merged into one episode. Pre-fault windows count back from each episode start.

- Events: 26,658 (Informational 25,771, Stop 453, Warning 385, Communication 49)
- Stops by class: {'routine': 228, 'weather': 67, 'maintenance': 64, 'curtailment': 50, 'fault': 44}
- Stop hours by class: {'curtailment': 0.8, 'fault': 269.0, 'maintenance': 85.1, 'routine': 85.9, 'weather': 132.4}
- Fault stops by component: {'sensor_met': 19, 'converter': 5, 'pitch': 5, 'electrical': 4, 'gearbox': 4, 'brake': 4, 'tower': 3}
- Major faults: 2 events in 2 episodes; by component {'pitch': 2}

## Top stop codes (count)

|   code | message                          | event_class   | component   |   count |
|-------:|:---------------------------------|:--------------|:------------|--------:|
|    710 | Battery test                     | routine       | unspecified |     130 |
|   6200 | Cable autounwind                 | routine       | yaw         |      63 |
|     64 | Max. wind speed                  | weather       | unspecified |      51 |
|   9210 | Externally stopped               | curtailment   | unspecified |      50 |
|     20 | Manual stop - on site            | maintenance   | unspecified |      46 |
|   5760 | Hydraulic oil flushing operation | routine       | hydraulics  |      32 |
|   6530 | Anemometer defect                | fault         | sensor_met  |      14 |
|     21 | Manual stop - remote             | maintenance   | unspecified |       8 |
|   6540 | Icing (anemometer)               | weather       | sensor_met  |       8 |
|     25 | Manual stop without login        | maintenance   | unspecified |       6 |
|   6620 | Vane defect                      | fault         | sensor_met  |       5 |
|   3000 | Frequency converter not ready    | fault         | converter   |       5 |
|   1550 | Missing gear oil (high rpm)      | fault         | gearbox     |       4 |
|   2100 | Feedback brake 1                 | fault         | brake       |       4 |
|   4215 | Smoke warning nacelle stop       | fault         | electrical  |       4 |

## Top fault codes by downtime hours

|   code | message                       | component   |   hours |
|-------:|:------------------------------|:------------|--------:|
|   4215 | Smoke warning nacelle stop    | electrical  |   136.5 |
|   6530 | Anemometer defect             | sensor_met  |    94   |
|    658 | Error pitch converter 3       | pitch       |    18.1 |
|    715 | Charging circuit pitch        | pitch       |    13.2 |
|   2100 | Feedback brake 1              | brake       |     2.6 |
|   3000 | Frequency converter not ready | converter   |     1.5 |
|    455 | Repeating error BP52          | pitch       |     1.4 |
|   4530 | Tower oscillation Y level 2   | tower       |     0.7 |
|   6620 | Vane defect                   | sensor_met  |     0.5 |
|   4510 | Tower oscillation Y level 1   | tower       |     0.3 |
|   1550 | Missing gear oil (high rpm)   | gearbox     |     0.1 |

## Major fault events

| turbine_id   |   major_episode | start                     | end_filled                | duration        |   code | message                 | component   |
|:-------------|----------------:|:--------------------------|:--------------------------|:----------------|-------:|:------------------------|:------------|
| PEN11        |               1 | 2021-03-04 22:24:34+00:00 | 2021-03-05 11:38:21+00:00 | 0 days 13:13:47 |    715 | Charging circuit pitch  | pitch       |
| PEN14        |               2 | 2021-04-04 14:05:17+00:00 | 2021-04-05 08:09:15+00:00 | 0 days 18:03:58 |    658 | Error pitch converter 3 | pitch       |

## Labeled 10-minute rows per turbine

| turbine_id   |   in_any_stop |   in_fault |   in_major_fault |   pre_fault_7d |   pre_fault_14d |   pre_fault_30d |   in_stop_curtailment |   in_stop_maintenance |   in_stop_grid |   in_stop_weather |   in_stop_routine |
|:-------------|--------------:|-----------:|-----------------:|---------------:|----------------:|----------------:|----------------------:|----------------------:|---------------:|------------------:|------------------:|
| PEN11        |           882 |        507 |               80 |           1007 |            2015 |            4319 |                    12 |                   117 |              0 |               163 |                87 |
| PEN12        |           766 |        422 |                0 |              0 |               0 |               0 |                    12 |                    70 |              0 |               166 |               101 |
| PEN13        |           978 |        592 |                0 |              0 |               0 |               0 |                    12 |                   122 |              0 |               163 |                97 |
| PEN14        |           531 |        109 |              109 |           1007 |            2015 |            4319 |                    12 |                   163 |              0 |               172 |                78 |
| PEN15        |           683 |         20 |                0 |              0 |               0 |               0 |                    12 |                    83 |              0 |               187 |               388 |
| ALL          |          3840 |       1650 |              189 |           2014 |            4030 |            8638 |                    60 |                   555 |              0 |               851 |               751 |

Total rows: 130,320. Rows within the last 30 days of the record without a later major fault are right-censored (days_to_next_major_fault is NaN).
# Failure labels: kelmarsh

Source: Greenbyte status logs (2022-01-02 to 2022-12-31, UTC). Rules in src/windml/labeling.py.
Major fault = Stop classified as fault, component in gearbox/generator/bearing/converter/pitch/yaw/hydraulics, duration >= 1 h; major faults on the same turbine within 24 h are merged into one episode. Pre-fault windows count back from each episode start.

- Events: 69,850 (Informational 67,810, Warning 1,030, Stop 919, Communication 54, Curtailment 37)
- Stops by class: {'routine': 464, 'maintenance': 171, 'fault': 170, 'grid': 86, 'weather': 28}
- Stop hours by class: {'fault': 530.1, 'grid': 206.6, 'maintenance': 1162.4, 'routine': 44.8, 'weather': 637.0}
- Fault stops by component: {'sensor_met': 96, 'tower': 38, 'converter': 13, 'pitch': 8, 'gearbox': 8, 'hydraulics': 2, 'electrical': 2, 'yaw': 2, 'rotor': 1}
- Major faults: 12 events in 9 episodes; by component {'converter': 6, 'pitch': 4, 'hydraulics': 1, 'yaw': 1}

## Top stop codes (count)

|   code | message                          | event_class   | component    |   count |
|-------:|:---------------------------------|:--------------|:-------------|--------:|
|    710 | Battery test                     | routine       | unspecified  |     299 |
|     20 | Manual stop - on site            | maintenance   | unspecified  |     110 |
|   6200 | Cable autounwind                 | routine       | yaw          |     101 |
|   6530 | Anemometer defect                | fault         | sensor_met   |      92 |
|   3125 | Timeout ready for connection     | grid          | control_comm |      65 |
|   5760 | Hydraulic oil flushing operation | routine       | hydraulics   |      55 |
|     25 | Manual stop without login        | maintenance   | unspecified  |      41 |
|   4540 | Tower oscillation X level 2      | fault         | tower        |      19 |
|   3500 | Grid loss                        | grid          | unspecified  |      17 |
|   4520 | Tower oscillation X level 1      | fault         | tower        |      10 |
|    210 | Manual brake                     | maintenance   | brake        |      10 |
|     21 | Manual stop - remote             | maintenance   | unspecified  |      10 |
|     61 | Wind < power                     | weather       | unspecified  |       9 |
|   3110 | Frequency converter error        | fault         | converter    |       9 |
|   4510 | Tower oscillation Y level 1      | fault         | tower        |       9 |

## Top fault codes by downtime hours

|   code | message                        | component   |   hours |
|-------:|:-------------------------------|:------------|--------:|
|    550 | Pitch current asymmetry        | pitch       |   234.7 |
|    555 | Pitch angle deviation          | pitch       |   177.2 |
|   3110 | Frequency converter error      | converter   |    67.8 |
|   6530 | Anemometer defect              | sensor_met  |    15.4 |
|   3151 | Max.temp.conv.inl.>perm.out.t. | converter   |    10.2 |
|   5510 | Low hydraulic pressure         | hydraulics  |     8   |
|   4540 | Tower oscillation X level 2    | tower       |     6.3 |
|   4510 | Tower oscillation Y level 1    | tower       |     2.7 |
|    672 | Max. pitch speed encoder B     | pitch       |     2.7 |
|   4520 | Tower oscillation X level 1    | tower       |     2.1 |
|   6300 | Yaw error                      | yaw         |     1.1 |
|    100 | Safety chain open              | electrical  |     0.8 |
|    455 | Repeating error BP52           | pitch       |     0.4 |
|    815 | Rotor overspeed nacelle        | rotor       |     0.3 |
|   6620 | Vane defect                    | sensor_met  |     0.2 |

## Major fault events

| turbine_id   |   major_episode | start                     | end_filled                | duration        |   code | message                        | component   |
|:-------------|----------------:|:--------------------------|:--------------------------|:----------------|-------:|:-------------------------------|:------------|
| KEL01        |               1 | 2022-05-16 05:46:21+00:00 | 2022-05-16 13:42:22+00:00 | 0 days 07:56:01 |   5510 | Low hydraulic pressure         | hydraulics  |
| KEL02        |               2 | 2022-11-30 10:21:28+00:00 | 2022-11-30 16:01:11+00:00 | 0 days 05:39:43 |   3110 | Frequency converter error      | converter   |
| KEL03        |               3 | 2022-07-19 13:51:34+00:00 | 2022-07-19 15:13:20+00:00 | 0 days 01:21:46 |   3151 | Max.temp.conv.inl.>perm.out.t. | converter   |
| KEL03        |               3 | 2022-07-19 15:45:37+00:00 | 2022-07-19 17:17:36+00:00 | 0 days 01:31:59 |   3151 | Max.temp.conv.inl.>perm.out.t. | converter   |
| KEL04        |               4 | 2022-02-08 22:56:57+00:00 | 2022-02-11 11:05:15+00:00 | 2 days 12:08:18 |   3110 | Frequency converter error      | converter   |
| KEL05        |               5 | 2022-07-19 12:36:00+00:00 | 2022-07-19 14:59:28+00:00 | 0 days 02:23:28 |   3151 | Max.temp.conv.inl.>perm.out.t. | converter   |
| KEL06        |               6 | 2022-03-18 04:13:32+00:00 | 2022-03-18 17:59:49+00:00 | 0 days 13:46:17 |    550 | Pitch current asymmetry        | pitch       |
| KEL06        |               6 | 2022-03-19 06:00:02+00:00 | 2022-03-19 08:42:20+00:00 | 0 days 02:42:18 |    672 | Max. pitch speed encoder B     | pitch       |
| KEL06        |               6 | 2022-03-19 08:44:31+00:00 | 2022-03-28 13:40:42+00:00 | 9 days 04:56:11 |    550 | Pitch current asymmetry        | pitch       |
| KEL06        |               7 | 2022-04-12 16:46:52+00:00 | 2022-04-12 17:53:59+00:00 | 0 days 01:07:07 |   6300 | Yaw error                      | yaw         |
| KEL06        |               8 | 2022-05-12 02:37:43+00:00 | 2022-05-19 11:19:38+00:00 | 7 days 08:41:55 |    555 | Pitch angle deviation          | pitch       |
| KEL06        |               9 | 2022-07-19 13:17:02+00:00 | 2022-07-19 18:11:27+00:00 | 0 days 04:54:25 |   3151 | Max.temp.conv.inl.>perm.out.t. | converter   |

## Labeled 10-minute rows per turbine

| turbine_id   |   in_any_stop |   in_fault |   in_major_fault |   pre_fault_7d |   pre_fault_14d |   pre_fault_30d |   in_stop_curtailment |   in_stop_maintenance |   in_stop_grid |   in_stop_weather |   in_stop_routine |
|:-------------|--------------:|-----------:|-----------------:|---------------:|----------------:|----------------:|----------------------:|----------------------:|---------------:|------------------:|------------------:|
| KEL01        |          1916 |        171 |               49 |           1007 |            2015 |            4319 |                     0 |                   645 |            359 |               629 |               125 |
| KEL02        |          2417 |        100 |               35 |           1007 |            2015 |            4319 |                     0 |                  1331 |            310 |               558 |               125 |
| KEL03        |          1103 |         28 |               19 |           1007 |            2015 |            4319 |                     0 |                   262 |            148 |               545 |               123 |
| KEL04        |          5631 |        378 |              362 |           1007 |            2015 |            4319 |                     0 |                  4281 |             10 |               859 |               109 |
| KEL05        |          1385 |         70 |               15 |           1007 |            2015 |            4319 |                     0 |                   381 |            197 |               630 |               115 |
| KEL06        |          3805 |       2583 |             2526 |           4028 |            8060 |           15114 |                     0 |                   218 |            279 |               623 |               116 |
| ALL          |         16257 |       3330 |             3006 |           9063 |           18135 |           36709 |                     0 |                  7118 |           1303 |              3844 |               713 |

Total rows: 315,360. Rows within the last 30 days of the record without a later major fault are right-censored (days_to_next_major_fault is NaN).
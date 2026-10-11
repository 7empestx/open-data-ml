# Data-quality report: acme_messy

Synthetic ACME-style vendor export generated from Kelmarsh KEL01-02, 2022

- Period (UTC): 2022-01-01 00:00 to 2022-12-31 23:50; 2 turbines; 105,120 10-min rows
- Signals mapped: 12 of 34 canonical signals
- Source files: 26

## Day-1 findings

1. **Out of range** gear_oil_inlet_pressure_bar: 2.36% of values outside 0 to 15 bar (min -3.03, max 20)

## Coverage per turbine

Coverage = 10-min slots with power or wind speed present, over the farm-wide period.

| turbine_id   | first            | last             |   expected_rows |   rows_with_data | coverage   |   gaps_ge_1h |   longest_gap_h |
|:-------------|:-----------------|:-----------------|----------------:|-----------------:|:-----------|-------------:|----------------:|
| KEL01        | 2022-01-01 00:00 | 2022-12-31 23:50 |           52560 |            52010 | 99.0%      |            6 |            48.8 |
| KEL02        | 2022-01-01 00:00 | 2022-12-31 23:50 |           52560 |            52488 | 99.9%      |            2 |             5   |

## Signal completeness (share of rows with a value)

| signal                      | KEL01   | KEL02   |
|:----------------------------|:--------|:--------|
| power_kw                    | 99.0%   | 99.9%   |
| wind_speed_ms               | 98.9%   | 99.9%   |
| ambient_temp_c              | 98.9%   | 99.8%   |
| nacelle_temp_c              | 98.9%   | 99.8%   |
| rotor_speed_rpm             | 99.0%   | 99.9%   |
| generator_speed_rpm         | 99.0%   | 99.9%   |
| gear_oil_temp_c             | 99.0%   | 99.9%   |
| gear_oil_inlet_pressure_bar | 99.0%   | 99.9%   |
| main_bearing_front_temp_c   | 98.9%   | 99.8%   |
| pitch_a_deg                 | 98.9%   | 99.8%   |
| nacelle_position_deg        | 99.0%   | 99.9%   |
| wind_direction_deg          | 99.0%   | 99.9%   |

## Gaps of 1 h or more (20 longest)

8 gaps in total.

| turbine_id   | gap_start        | gap_end          |   hours |
|:-------------|:-----------------|:-----------------|--------:|
| KEL01        | 2022-09-08 08:10 | 2022-09-10 09:00 |    48.8 |
| KEL01        | 2022-06-20 10:00 | 2022-06-21 09:30 |    23.5 |
| KEL01        | 2022-06-06 10:30 | 2022-06-06 16:30 |     6   |
| KEL01        | 2022-06-07 10:00 | 2022-06-07 15:20 |     5.3 |
| KEL02        | 2022-06-07 10:10 | 2022-06-07 15:10 |     5   |
| KEL01        | 2022-09-01 07:50 | 2022-09-01 12:20 |     4.5 |
| KEL02        | 2022-09-01 07:50 | 2022-09-01 12:20 |     4.5 |
| KEL01        | 2022-05-23 10:40 | 2022-05-23 12:30 |     1.8 |

## Stuck sensors (identical value for 6 h or more, 24 h for coarse sensors where >= 60% of readings sit on a 0.5-unit grid; temperatures, pressures, wind speed)

_none_

## Value ranges vs plausible physical range (canonical units)

| signal                      | unit   | plausible     |   values |   out_of_range | share   |        min |     p1 |        p99 |        max |
|:----------------------------|:-------|:--------------|---------:|---------------:|:--------|-----------:|-------:|-----------:|-----------:|
| power_kw                    | kW     | -200 to 10000 |   104498 |              0 | 0.0%    |  -17.6     | -5     |   2.05e+03 |   2.08e+03 |
| wind_speed_ms               | m/s    | 0 to 60       |   104494 |              0 | 0.0%    |    0       |  1.08  |  13.5      |  23.7      |
| ambient_temp_c              | degC   | -45 to 55     |   104412 |              0 | 0.0%    |   -4.4     | -0.215 |  29.3      |  39.2      |
| nacelle_temp_c              | degC   | -40 to 80     |   104412 |              0 | 0.0%    |   -0.6     |  4.93  |  34.9      |  42        |
| rotor_speed_rpm             | rpm    | 0 to 40       |   104498 |              0 | 0.0%    |    0       |  0     |  15.2      |  15.4      |
| generator_speed_rpm         | rpm    | -50 to 3000   |   104498 |              4 | 0.0%    | -572       |  1     |   1.8e+03  |   1.82e+03 |
| gear_oil_temp_c             | degC   | -30 to 110    |   104498 |              0 | 0.0%    |    8.6     | 12     |  59.7      |  65        |
| gear_oil_inlet_pressure_bar | bar    | 0 to 15       |   104498 |           2463 | 2.4%    |   -3.03    | -0.581 |   3.45     |  20        |
| main_bearing_front_temp_c   | degC   | -30 to 110    |   104412 |              0 | 0.0%    |    7.8     | 10.8   |  75.3      |  81.1      |
| pitch_a_deg                 | deg    | -10 to 100    |   104412 |              1 | 0.0%    | -173       |  0     |  92        |  92.6      |
| nacelle_position_deg        | deg    | 0 to 360      |   104498 |              0 | 0.0%    |    0.0173  |  4.95  | 354        | 360        |
| wind_direction_deg          | deg    | 0 to 360      |   104498 |              0 | 0.0%    |    0.00506 |  7.58  | 354        | 360        |

## Units

| signal | decision |
|---|---|
| power_kw | W -> kW (mapping) |
| wind_speed_ms | m/s -> m/s (mapping) |
| ambient_temp_c | degF -> degC (mapping) |
| nacelle_temp_c | degF -> degC (mapping) |
| rotor_speed_rpm | rpm -> rpm (mapping) |
| generator_speed_rpm | rpm -> rpm (mapping) |
| gear_oil_temp_c | degF -> degC (mapping) |
| gear_oil_inlet_pressure_bar | kPa -> bar (mapping) |
| main_bearing_front_temp_c | degF -> degC (mapping) |
| pitch_a_deg | deg -> deg (mapping) |
| nacelle_position_deg | deg -> deg (mapping) |
| wind_direction_deg | deg -> deg (mapping) |

## Timestamps and clocks

- Duplicate timestamps collapsed (most complete row kept): none
- Duplicate dates (top): none
- Off-grid timestamps: none
- Local-time conversion: {'scada': {'timezone': 'Europe/London', 'ambiguous_rows': 24, 'nonexistent_rows': 0, 'ambiguous_policy': 'infer', 'nonexistent_policy': 'drop'}, 'status.start': {'timezone': 'Europe/London', 'ambiguous_rows': 0, 'nonexistent_rows': 0, 'ambiguous_policy': 'earliest', 'nonexistent_policy': 'shift_forward'}}

Best lag vs fleet (10-min steps; 0 = clocks agree), from wind-speed changes:

| turbine_id   |   2022Q1 |   2022Q2 |   2022Q3 |   2022Q4 |
|:-------------|---------:|---------:|---------:|---------:|
| KEL01        |        0 |        0 |        0 |        0 |
| KEL02        |        0 |        0 |        0 |        0 |

## Status / alarm log

- Events: 22,124; stops: 375; fault stops: 110; major faults: 2
- Stops by class: {'routine': 162, 'fault': 110, 'maintenance': 66, 'grid': 22, 'weather': 15}
- Events outside the SCADA period: 0; end before start: 0

Top stop codes:

|   code | message                          |   count |
|-------:|:---------------------------------|--------:|
|    710 | Battery test                     |     102 |
|   6530 | Anemometer defect                |      70 |
|     20 | Manual stop - on site            |      39 |
|   6200 | Cable autounwind                 |      36 |
|     25 | Manual stop without login        |      20 |
|   5760 | Hydraulic oil flushing operation |      18 |
|   3125 | Timeout ready for connection     |      12 |
|   4540 | Tower oscillation X level 2      |      12 |
|     61 | Wind < power                     |       8 |
|   3500 | Grid loss                        |       6 |

## Columns in the export that are not mapped

`WindSpd_Min [m/s]`, `WTG_ActPwr_Max [W]`

## Files read

| file                                   |   rows | turbines   | missing_columns   |
|:---------------------------------------|-------:|:-----------|:------------------|
| ingest-fixtures/acme/WTG01_2022-01.csv |   4463 | ['KEL01']  | []                |
| ingest-fixtures/acme/WTG01_2022-02.csv |   4032 | ['KEL01']  | []                |
| ingest-fixtures/acme/WTG01_2022-03.csv |   4458 | ['KEL01']  | []                |
| ingest-fixtures/acme/WTG01_2022-04.csv |   4320 | ['KEL01']  | []                |
| ingest-fixtures/acme/WTG01_2022-05.csv |   4464 | ['KEL01']  | []                |
| ingest-fixtures/acme/WTG01_2022-06.csv |   4320 | ['KEL01']  | []                |
| ingest-fixtures/acme/WTG01_2022-07.csv |   4464 | ['KEL01']  | []                |
| ingest-fixtures/acme/WTG01_2022-08.csv |   4464 | ['KEL01']  | []                |
| ingest-fixtures/acme/WTG01_2022-09.csv |   4320 | ['KEL01']  | []                |
| ingest-fixtures/acme/WTG01_2022-10.csv |   4470 | ['KEL01']  | []                |
| ingest-fixtures/acme/WTG01_2022-11.csv |   4320 | ['KEL01']  | []                |
| ingest-fixtures/acme/WTG01_2022-12.csv |   4464 | ['KEL01']  | []                |
| ingest-fixtures/acme/WTG01_2023-01.csv |      1 | ['KEL01']  | []                |
| ingest-fixtures/acme/WTG02_2022-01.csv |   4463 | ['KEL02']  | []                |
| ingest-fixtures/acme/WTG02_2022-02.csv |   4032 | ['KEL02']  | []                |
| ingest-fixtures/acme/WTG02_2022-03.csv |   4458 | ['KEL02']  | []                |
| ingest-fixtures/acme/WTG02_2022-04.csv |   4320 | ['KEL02']  | []                |
| ingest-fixtures/acme/WTG02_2022-05.csv |   4464 | ['KEL02']  | []                |
| ingest-fixtures/acme/WTG02_2022-06.csv |   4320 | ['KEL02']  | []                |
| ingest-fixtures/acme/WTG02_2022-07.csv |   4464 | ['KEL02']  | []                |
| ingest-fixtures/acme/WTG02_2022-08.csv |   4464 | ['KEL02']  | []                |
| ingest-fixtures/acme/WTG02_2022-09.csv |   4320 | ['KEL02']  | []                |
| ingest-fixtures/acme/WTG02_2022-10.csv |   4470 | ['KEL02']  | []                |
| ingest-fixtures/acme/WTG02_2022-11.csv |   4320 | ['KEL02']  | []                |
| ingest-fixtures/acme/WTG02_2022-12.csv |   4464 | ['KEL02']  | []                |
| ingest-fixtures/acme/WTG02_2023-01.csv |      1 | ['KEL02']  | []                |

---
Generated by `windml ingest validate` (projects/windml/src/windml/ingest). Thresholds: gaps >= 1 h, stuck >= 6 h, coverage < 95%, out-of-range share > 0.1%.
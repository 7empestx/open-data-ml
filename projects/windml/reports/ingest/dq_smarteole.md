# Data-quality report: smarteole

SMARTEOLE wind-farm-control open dataset, 7x Senvion MM82 (ENGIE), 1-min SCADA, Feb-May 2020

- Period (UTC): 2020-02-17 16:30 to 2020-05-24 23:50; 7 turbines; 94,318 10-min rows
- Signals mapped: 7 of 34 canonical signals
- Source files: 1

## Day-1 findings

1. **Coverage** SMV1: 93.4% of 10-min slots have data (longest gap 65.2 h)
2. **Coverage** SMV2: 93.3% of 10-min slots have data (longest gap 65.3 h)
3. **Coverage** SMV3: 87.1% of 10-min slots have data (longest gap 122.5 h)
4. **Coverage** SMV4: 94.2% of 10-min slots have data (longest gap 68.5 h)
5. **Coverage** SMV5: 93.6% of 10-min slots have data (longest gap 65.2 h)
6. **Coverage** SMV6: 93.3% of 10-min slots have data (longest gap 65.2 h)
7. **Coverage** SMV7: 93.4% of 10-min slots have data (longest gap 65.3 h)
8. **Stuck sensors** (constant >= 6 h, or >= 24 h for coarse sensors): SMV6 ambient_temp_c 29.5 h; SMV6 wind_speed_ms 29.3 h
9. **Sparse high-res bins**: 3,071 of 94,318 10-min bins (SMV1, SMV2, SMV3, SMV4, SMV5, SMV6, SMV7, native 1min) had too few samples and were blanked

## Coverage per turbine

Coverage = 10-min slots with power or wind speed present, over the farm-wide period.

| turbine_id   | first            | last             |   expected_rows |   rows_with_data | coverage   |   gaps_ge_1h |   longest_gap_h |
|:-------------|:-----------------|:-----------------|----------------:|-----------------:|:-----------|-------------:|----------------:|
| SMV1         | 2020-02-17 16:30 | 2020-05-24 23:50 |           14013 |            13082 | 93.4%      |           11 |            65.2 |
| SMV2         | 2020-02-17 16:30 | 2020-05-24 23:50 |           14013 |            13080 | 93.3%      |           12 |            65.3 |
| SMV3         | 2020-02-17 16:30 | 2020-05-24 23:50 |           14013 |            12211 | 87.1%      |            7 |           122   |
| SMV4         | 2020-02-17 16:30 | 2020-05-24 23:50 |           14013 |            13198 | 94.2%      |            8 |            68.5 |
| SMV5         | 2020-02-17 16:30 | 2020-05-24 23:50 |           14013 |            13123 | 93.6%      |            6 |            65.2 |
| SMV6         | 2020-02-17 16:30 | 2020-05-24 23:50 |           14013 |            13075 | 93.3%      |           10 |            65.2 |
| SMV7         | 2020-02-17 16:30 | 2020-05-24 23:50 |           14013 |            13088 | 93.4%      |            9 |            65.3 |

## Signal completeness (share of rows with a value)

| signal               | SMV1   | SMV2   | SMV3   | SMV4   | SMV5   | SMV6   | SMV7   |
|:---------------------|:-------|:-------|:-------|:-------|:-------|:-------|:-------|
| power_kw             | 96.6%  | 96.7%  | 90.5%  | 97.5%  | 96.8%  | 95.7%  | 96.7%  |
| wind_speed_ms        | 97.1%  | 97.1%  | 90.6%  | 98.0%  | 97.4%  | 97.0%  | 97.1%  |
| generator_speed_rpm  | 97.1%  | 97.1%  | 90.6%  | 98.0%  | 97.4%  | 97.0%  | 97.1%  |
| pitch_a_deg          | 97.1%  | 97.1%  | 90.6%  | 98.0%  | 97.4%  | 97.0%  | 97.1%  |
| ambient_temp_c       | 97.1%  | 97.1%  | 90.6%  | 98.0%  | 97.4%  | 97.0%  | 97.1%  |
| nacelle_position_deg | 97.1%  | 97.1%  | 90.6%  | 98.0%  | 97.4%  | 99.9%  | 97.1%  |
| wind_direction_deg   | 97.1%  | 97.1%  | 90.6%  | 98.0%  | 97.4%  | 99.9%  | 97.1%  |

## Gaps of 1 h or more (20 longest)

63 gaps in total.

| turbine_id   | gap_start        | gap_end          |   hours |
|:-------------|:-----------------|:-----------------|--------:|
| SMV3         | 2020-02-20 07:50 | 2020-02-25 10:20 |   122   |
| SMV4         | 2020-05-16 15:40 | 2020-05-19 12:10 |    68.5 |
| SMV2         | 2020-05-16 15:40 | 2020-05-19 09:00 |    65.3 |
| SMV7         | 2020-05-16 15:40 | 2020-05-19 09:00 |    65.3 |
| SMV6         | 2020-05-16 15:40 | 2020-05-19 08:50 |    65.2 |
| SMV3         | 2020-05-16 15:40 | 2020-05-19 08:50 |    65.2 |
| SMV1         | 2020-05-16 15:40 | 2020-05-19 08:50 |    65.2 |
| SMV5         | 2020-05-16 15:40 | 2020-05-19 08:50 |    65.2 |
| SMV5         | 2020-05-06 11:10 | 2020-05-07 12:10 |    25   |
| SMV4         | 2020-05-06 11:10 | 2020-05-07 12:10 |    25   |
| SMV6         | 2020-05-06 11:20 | 2020-05-07 12:10 |    24.8 |
| SMV7         | 2020-05-06 11:20 | 2020-05-07 12:10 |    24.8 |
| SMV2         | 2020-05-06 11:20 | 2020-05-07 12:10 |    24.8 |
| SMV1         | 2020-05-06 11:20 | 2020-05-07 12:10 |    24.8 |
| SMV3         | 2020-05-06 11:20 | 2020-05-07 12:10 |    24.8 |
| SMV3         | 2020-02-25 13:00 | 2020-02-26 13:30 |    24.5 |
| SMV6         | 2020-02-20 13:10 | 2020-02-21 13:00 |    23.8 |
| SMV3         | 2020-04-02 14:20 | 2020-04-03 12:00 |    21.7 |
| SMV2         | 2020-05-22 14:20 | 2020-05-23 11:10 |    20.8 |
| SMV3         | 2020-05-22 14:20 | 2020-05-23 11:10 |    20.8 |

## Stuck sensors (identical value for 6 h or more, 24 h for coarse sensors where >= 60% of readings sit on a 0.5-unit grid; temperatures, pressures, wind speed)

| turbine_id   | signal         |   coarse_share |   min_run_h |   runs |   hours_stuck |   longest_h | longest_from     |   value |
|:-------------|:---------------|---------------:|------------:|-------:|--------------:|------------:|:-----------------|--------:|
| SMV6         | wind_speed_ms  |              0 |           6 |      1 |          29.3 |        29.3 | 2020-02-25 09:50 |     8.2 |
| SMV6         | ambient_temp_c |              0 |           6 |      1 |          29.5 |        29.5 | 2020-02-25 09:50 |     8.6 |

## Value ranges vs plausible physical range (canonical units)

| signal               | unit   | plausible     |   values |   out_of_range | share   |      min |     p1 |        p99 |        max |
|:---------------------|:-------|:--------------|---------:|---------------:|:--------|---------:|-------:|-----------:|-----------:|
| power_kw             | kW     | -200 to 10000 |    90342 |              0 | 0.0%    | -17.1    | -5.75  |   2.05e+03 |   2.06e+03 |
| wind_speed_ms        | m/s    | 0 to 60       |    90857 |              0 | 0.0%    |   0      |  0.857 |  14.7      |  19.5      |
| generator_speed_rpm  | rpm    | -50 to 3000   |    90858 |              0 | 0.0%    |  -3.69   |  0.58  |   1.8e+03  |   1.81e+03 |
| pitch_a_deg          | deg    | -10 to 100    |    90858 |              7 | 0.0%    | -88.6    | -1.01  |  90        |   1.31e+30 |
| ambient_temp_c       | degC   | -45 to 55     |    90858 |              2 | 0.0%    |  -0.176  |  3.18  |  28.4      |   3.13e+17 |
| nacelle_position_deg | deg    | 0 to 360      |    91247 |              0 | 0.0%    |   0.0106 |  7.07  | 350        | 360        |
| wind_direction_deg   | deg    | 0 to 360      |    91247 |              0 | 0.0%    |   0.0338 |  7.17  | 350        | 360        |

## Units

| signal | decision |
|---|---|
| power_kw | kW -> kW (mapping) |
| wind_speed_ms | m/s -> m/s (mapping) |
| generator_speed_rpm | rpm -> rpm (mapping) |
| pitch_a_deg | deg -> deg (mapping) |
| nacelle_position_deg | deg -> deg (mapping) |
| wind_direction_deg | deg -> deg (mapping) |
| ambient_temp_c | degC -> degC (mapping) |

## Sampling interval and aggregation

Native interval = most common step between a turbine's timestamps. Data finer than 10 minutes is aggregated to 10-minute bins (mean; min/max/std for key signals; coverage = samples present / samples expected).

| turbine_id   | interval   |   regular_share |
|:-------------|:-----------|----------------:|
| SMV1         | 1min       |          0.9998 |
| SMV2         | 1min       |          0.9998 |
| SMV3         | 1min       |          0.9998 |
| SMV4         | 1min       |          0.9998 |
| SMV5         | 1min       |          0.9998 |
| SMV6         | 1min       |          0.9998 |
| SMV7         | 1min       |          0.9998 |

- Aggregated SMV1, SMV2, SMV3, SMV4, SMV5, SMV6, SMV7 from 1min (10 samples per bin): 94,318 bins, mean coverage 96.7%, 3,071 bins below the minimum coverage (values set to NaN), 0 duplicate samples dropped

Bin coverage per turbine:

| turbine_id   | mean   | bins_lt_90pct   |
|:-------------|:-------|:----------------|
| SMV1         | 97.1%  | 3.6%            |
| SMV2         | 97.2%  | 3.4%            |
| SMV3         | 90.6%  | 9.7%            |
| SMV4         | 98.0%  | 2.6%            |
| SMV5         | 97.3%  | 3.4%            |
| SMV6         | 99.9%  | 0.2%            |
| SMV7         | 97.2%  | 3.5%            |


## Timestamps and clocks

- Duplicate timestamps collapsed (most complete row kept): none
- Duplicate dates (top): none
- Off-grid timestamps: none
- Local-time conversion: timestamps were UTC or carried offsets

Best lag vs fleet (10-min steps; 0 = clocks agree), from wind-speed changes:

| turbine_id   |   2020Q1 |   2020Q2 |
|:-------------|---------:|---------:|
| SMV1         |        0 |        0 |
| SMV2         |        0 |        0 |
| SMV3         |        0 |        0 |
| SMV4         |        0 |        0 |
| SMV5         |        0 |        0 |
| SMV6         |        0 |        0 |
| SMV7         |        0 |        0 |

## Loader warnings

- high-res aggregation: 3,071 of 94,318 10-min bins have coverage below 0.5 and were set to NaN (coverage column kept)

## Columns in the export that are not mapped

`nacelle_position_1_min`, `nacelle_position_1_max`, `nacelle_position_1_std`, `nacelle_position_1_count`, `nacelle_position_2_min`, `nacelle_position_2_max`, `nacelle_position_2_std`, `nacelle_position_2_count`, `nacelle_position_3_min`, `nacelle_position_3_max`, `nacelle_position_3_std`, `nacelle_position_3_count`, `nacelle_position_4_min`, `nacelle_position_4_max`, `nacelle_position_4_std`, `nacelle_position_4_count`, `nacelle_position_5_min`, `nacelle_position_5_max`, `nacelle_position_5_std`, `nacelle_position_5_count`, `nacelle_position_6_min`, `nacelle_position_6_max`, `nacelle_position_6_std`, `nacelle_position_6_count`, `nacelle_position_7_min`, `nacelle_position_7_max`, `nacelle_position_7_std`, `nacelle_position_7_count`, `wind_vane_1_avg`, `wind_vane_1_min`, `wind_vane_1_max`, `wind_vane_1_std`, `wind_vane_1_count`, `wind_vane_2_avg`, `wind_vane_2_min`, `wind_vane_2_max`, `wind_vane_2_std`, `wind_vane_2_count`, `wind_vane_3_avg`, `wind_vane_3_min`, `wind_vane_3_max`, `wind_vane_3_std`, `wind_vane_3_count`, `wind_vane_4_avg`, `wind_vane_4_min`, `wind_vane_4_max`, `wind_vane_4_std`, `wind_vane_4_count`, `wind_vane_5_avg`, `wind_vane_5_min`, `wind_vane_5_max`, `wind_vane_5_std`, `wind_vane_5_count`, `wind_vane_6_avg`, `wind_vane_6_min`, `wind_vane_6_max`, `wind_vane_6_std`, `wind_vane_6_count`, `wind_vane_7_avg`, `wind_vane_7_min`, `wind_vane_7_max`, `wind_vane_7_std`, `wind_vane_7_count`, `wind_direction_1_min`, `wind_direction_1_max`, `wind_direction_1_std`, `wind_direction_1_count`, `wind_direction_2_min`, `wind_direction_2_max`, `wind_direction_2_std`, `wind_direction_2_count`, `wind_direction_3_min`, `wind_direction_3_max`, `wind_direction_3_std`, `wind_direction_3_count`, `wind_direction_4_min`, `wind_direction_4_max`, `wind_direction_4_std`, `wind_direction_4_count`, `wind_direction_5_min`, `wind_direction_5_max`, `wind_direction_5_std`, `wind_direction_5_count`, `wind_direction_6_min`, `wind_direction_6_max`, `wind_direction_6_std`, `wind_direction_6_count`, `wind_direction_7_min`, `wind_direction_7_max`, `wind_direction_7_std`, `wind_direction_7_count`, `temperature_1_min`, `temperature_1_max`, `temperature_1_std`, `temperature_1_count`, `temperature_2_min`, `temperature_2_max`, `temperature_2_std`, `temperature_2_count`, `temperature_3_min`, `temperature_3_max`, `temperature_3_std`, `temperature_3_count`, `temperature_4_min`, `temperature_4_max`, `temperature_4_std`, `temperature_4_count`, `temperature_5_min`, `temperature_5_max`, `temperature_5_std`, `temperature_5_count`, `temperature_6_min`, `temperature_6_max`, `temperature_6_std`, `temperature_6_count`, `temperature_7_min`, `temperature_7_max`, `temperature_7_std`, `temperature_7_count`

## Files read

| file                                                |   rows | turbines                                                 | missing_columns   |
|:----------------------------------------------------|-------:|:---------------------------------------------------------|:------------------|
| smarteole/SMARTEOLE_WakeSteering_SCADA_1minData.csv | 942627 | ['SMV1', 'SMV2', 'SMV3', 'SMV4', 'SMV5', 'SMV6', 'SMV7'] | []                |

---
Generated by `windml ingest validate` (projects/windml/src/windml/ingest). Thresholds: gaps >= 1 h, stuck >= 6 h, coverage < 95%, out-of-range share > 0.1%.
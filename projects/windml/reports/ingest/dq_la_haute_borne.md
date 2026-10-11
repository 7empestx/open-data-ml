# Data-quality report: la_haute_borne

La Haute Borne wind farm (4x Senvion MM82 2050 kW, France), ENGIE open data via NREL OpenOA

- Period (UTC): 2014-01-01 00:00 to 2015-12-31 23:50; 4 turbines; 420,432 10-min rows
- Signals mapped: 6 of 34 canonical signals
- Source files: 1

## Day-1 findings

1. **Stuck sensors** (constant >= 6 h, or >= 24 h for coarse sensors): LHB02 ambient_temp_c 18.7 h; LHB03 wind_speed_ms 7.0 h
2. **Duplicate timestamps**: 48 collapsed (LHB01 12, LHB02 12, LHB03 12, LHB04 12)
3. **DST** duplicate timestamps on the spring DST date(s) (LHB01 12, LHB02 12, LHB03 12, LHB04 12): the exporter probably stamped the skipped local hour with the summer-time offset (02:xx written as 03:xx), so one copy of each pair is an hour early. The most complete row was kept; confirm with the operator

## Coverage per turbine

Coverage = 10-min slots with power or wind speed present, over the farm-wide period.

| turbine_id   | first            | last             |   expected_rows |   rows_with_data | coverage   |   gaps_ge_1h |   longest_gap_h |
|:-------------|:-----------------|:-----------------|----------------:|-----------------:|:-----------|-------------:|----------------:|
| LHB01        | 2014-01-01 00:00 | 2015-12-31 23:50 |          105120 |           104633 | 99.5%      |           14 |            34.3 |
| LHB02        | 2014-01-01 00:00 | 2015-12-31 23:50 |          105120 |           103899 | 98.8%      |           13 |           133   |
| LHB03        | 2014-01-01 00:00 | 2015-12-31 23:50 |          105120 |           104673 | 99.6%      |           10 |            34.2 |
| LHB04        | 2014-01-01 00:00 | 2015-12-31 23:50 |          105120 |           104658 | 99.6%      |           12 |            34.3 |

## Signal completeness (share of rows with a value)

| signal               | LHB01   | LHB02   | LHB03   | LHB04   |
|:---------------------|:--------|:--------|:--------|:--------|
| power_kw             | 99.5%   | 98.8%   | 99.6%   | 99.6%   |
| wind_speed_ms        | 99.5%   | 98.8%   | 99.6%   | 99.6%   |
| pitch_a_deg          | 99.5%   | 98.8%   | 99.6%   | 99.6%   |
| nacelle_position_deg | 99.5%   | 98.8%   | 99.6%   | 99.6%   |
| wind_direction_deg   | 99.5%   | 98.8%   | 99.6%   | 99.6%   |
| ambient_temp_c       | 99.5%   | 98.8%   | 99.6%   | 99.6%   |

## Gaps of 1 h or more (20 longest)

49 gaps in total.

| turbine_id   | gap_start        | gap_end          |   hours |
|:-------------|:-----------------|:-----------------|--------:|
| LHB02        | 2015-02-27 01:40 | 2015-03-04 14:30 |   133   |
| LHB02        | 2015-06-16 00:40 | 2015-06-17 11:00 |    34.3 |
| LHB04        | 2015-06-16 00:40 | 2015-06-17 11:00 |    34.3 |
| LHB01        | 2015-06-16 00:40 | 2015-06-17 11:00 |    34.3 |
| LHB03        | 2015-06-16 00:40 | 2015-06-17 10:50 |    34.2 |
| LHB03        | 2015-02-27 04:10 | 2015-02-27 15:40 |    11.5 |
| LHB01        | 2015-02-27 04:10 | 2015-02-27 14:50 |    10.7 |
| LHB04        | 2015-02-27 04:10 | 2015-02-27 14:50 |    10.7 |
| LHB03        | 2014-10-29 07:10 | 2014-10-29 17:20 |    10.2 |
| LHB01        | 2014-10-29 07:30 | 2014-10-29 17:20 |     9.8 |
| LHB02        | 2014-10-29 07:20 | 2014-10-29 17:00 |     9.7 |
| LHB04        | 2014-10-29 07:20 | 2014-10-29 17:00 |     9.7 |
| LHB04        | 2014-06-18 05:00 | 2014-06-18 10:40 |     5.7 |
| LHB01        | 2014-06-18 05:20 | 2014-06-18 10:40 |     5.3 |
| LHB03        | 2014-06-18 05:20 | 2014-06-18 10:40 |     5.3 |
| LHB04        | 2015-04-17 05:30 | 2015-04-17 10:30 |     5   |
| LHB02        | 2015-04-17 05:30 | 2015-04-17 10:10 |     4.7 |
| LHB03        | 2015-04-17 05:40 | 2015-04-17 10:20 |     4.7 |
| LHB01        | 2015-04-17 05:40 | 2015-04-17 10:10 |     4.5 |
| LHB02        | 2014-06-18 05:10 | 2014-06-18 09:10 |     4   |

## Stuck sensors (identical value for 6 h or more, 24 h for coarse sensors where >= 60% of readings sit on a 0.5-unit grid; temperatures, pressures, wind speed)

| turbine_id   | signal         |   coarse_share |   min_run_h |   runs |   hours_stuck |   longest_h | longest_from     |   value |
|:-------------|:---------------|---------------:|------------:|-------:|--------------:|------------:|:-----------------|--------:|
| LHB02        | ambient_temp_c |           0.03 |           6 |      2 |          18.7 |        12.2 | 2014-06-09 12:00 |    34.5 |
| LHB03        | wind_speed_ms  |           0.04 |           6 |      1 |           7   |         7   | 2014-10-27 01:30 |     0   |

## Value ranges vs plausible physical range (canonical units)

| signal               | unit   | plausible     |   values |   out_of_range | share   |    min |    p1 |        p99 |        max |
|:---------------------|:-------|:--------------|---------:|---------------:|:--------|-------:|------:|-----------:|-----------:|
| power_kw             | kW     | -200 to 10000 |   417863 |              0 | 0.0%    |  -17.9 | -4.59 |   1.87e+03 |   2.05e+03 |
| wind_speed_ms        | m/s    | 0 to 60       |   417863 |              0 | 0.0%    |    0   |  0    |  12.4      |  19.3      |
| pitch_a_deg          | deg    | -10 to 100    |   417863 |             40 | 0.0%    | -121   | -1.01 |  90        | 263        |
| nacelle_position_deg | deg    | 0 to 360      |   417863 |              0 | 0.0%    |    0   |  4.84 | 354        | 360        |
| wind_direction_deg   | deg    | 0 to 360      |   417863 |              0 | 0.0%    |    0   |  5.18 | 354        | 360        |
| ambient_temp_c       | degC   | -45 to 55     |   417863 |             34 | 0.0%    | -273   | -0.74 |  31.2      |  39.9      |

## Units

| signal | decision |
|---|---|
| power_kw | kW -> kW (mapping) |
| wind_speed_ms | m/s -> m/s (mapping) |
| pitch_a_deg | deg -> deg (mapping) |
| nacelle_position_deg | deg -> deg (mapping) |
| wind_direction_deg | deg -> deg (mapping) |
| ambient_temp_c | degC -> degC (mapping) |

## Sampling interval and aggregation

Native interval = most common step between a turbine's timestamps. Data finer than 10 minutes is aggregated to 10-minute bins (mean; min/max/std for key signals; coverage = samples present / samples expected).

| turbine_id   | interval   |   regular_share |
|:-------------|:-----------|----------------:|
| LHB01        | 10min      |               1 |
| LHB02        | 10min      |               1 |
| LHB03        | 10min      |               1 |
| LHB04        | 10min      |               1 |


## Timestamps and clocks

- Duplicate timestamps collapsed (most complete row kept): {'LHB01': 12, 'LHB02': 12, 'LHB03': 12, 'LHB04': 12}
- Duplicate dates (top): {'LHB01': {'2014-03-30': 6, '2015-03-29': 6}, 'LHB02': {'2014-03-30': 6, '2015-03-29': 6}, 'LHB03': {'2014-03-30': 6, '2015-03-29': 6}, 'LHB04': {'2014-03-30': 6, '2015-03-29': 6}}
- Off-grid timestamps: none
- Local-time conversion: timestamps were UTC or carried offsets

Best lag vs fleet (10-min steps; 0 = clocks agree), from wind-speed changes:

| turbine_id   |   2014Q1 |   2014Q2 |   2014Q3 |   2014Q4 |   2015Q1 |   2015Q2 |   2015Q3 |   2015Q4 |
|:-------------|---------:|---------:|---------:|---------:|---------:|---------:|---------:|---------:|
| LHB01        |        0 |        0 |        0 |        0 |        0 |        0 |        0 |        0 |
| LHB02        |        0 |        0 |        0 |        0 |        0 |        0 |        0 |        0 |
| LHB03        |        0 |        0 |        0 |        0 |        0 |        0 |        0 |        0 |
| LHB04        |        0 |        0 |        0 |        0 |        0 |        0 |        0 |        0 |

## Columns in the export that are not mapped

`Va_avg`

## Files read

| file                                             |   rows | turbines                             | missing_columns   |
|:-------------------------------------------------|-------:|:-------------------------------------|:------------------|
| la-haute-borne/la-haute-borne-data-2014-2015.csv | 420480 | ['LHB01', 'LHB02', 'LHB03', 'LHB04'] | []                |

---
Generated by `windml ingest validate` (projects/windml/src/windml/ingest). Thresholds: gaps >= 1 h, stuck >= 6 h, coverage < 95%, out-of-range share > 0.1%.
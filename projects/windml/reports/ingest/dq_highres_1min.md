# Data-quality report: highres_1min

Synthetic 1-min SCADA upsampled from Kelmarsh KEL01-02, March 2022

- Period (UTC): 2022-03-01 00:00 to 2022-03-31 23:50; 2 turbines; 8,916 10-min rows
- Signals mapped: 8 of 34 canonical signals
- Source files: 2

## Day-1 findings

1. **Out of range** gear_oil_inlet_pressure_bar: 1.00% of values outside 0 to 15 bar (min -1.54, max 19.4)
2. **Sparse high-res bins**: 6 of 8,916 10-min bins (KEL01, KEL02, native 1min) had too few samples and were blanked

## Coverage per turbine

Coverage = 10-min slots with power or wind speed present, over the farm-wide period.

| turbine_id   | first            | last             |   expected_rows |   rows_with_data | coverage   |   gaps_ge_1h |   longest_gap_h |
|:-------------|:-----------------|:-----------------|----------------:|-----------------:|:-----------|-------------:|----------------:|
| KEL01        | 2022-03-01 00:00 | 2022-03-31 23:50 |            4464 |             4458 | 99.9%      |            1 |               1 |
| KEL02        | 2022-03-01 00:00 | 2022-03-31 23:50 |            4464 |             4452 | 99.7%      |            1 |               2 |

## Signal completeness (share of rows with a value)

| signal                      | KEL01   | KEL02   |
|:----------------------------|:--------|:--------|
| power_kw                    | 99.9%   | 100.0%  |
| wind_speed_ms               | 99.8%   | 100.0%  |
| rotor_speed_rpm             | 99.9%   | 100.0%  |
| pitch_a_deg                 | 99.9%   | 100.0%  |
| gear_oil_temp_c             | 99.9%   | 100.0%  |
| gear_oil_inlet_pressure_bar | 99.9%   | 100.0%  |
| ambient_temp_c              | 99.9%   | 100.0%  |
| nacelle_position_deg        | 99.9%   | 100.0%  |

## Gaps of 1 h or more (20 longest)

2 gaps in total.

| turbine_id   | gap_start        | gap_end          |   hours |
|:-------------|:-----------------|:-----------------|--------:|
| KEL02        | 2022-03-15 06:00 | 2022-03-15 08:00 |       2 |
| KEL01        | 2022-03-20 12:00 | 2022-03-20 13:00 |       1 |

## Stuck sensors (identical value for 6 h or more, 24 h for coarse sensors where >= 60% of readings sit on a 0.5-unit grid; temperatures, pressures, wind speed)

_none_

## Value ranges vs plausible physical range (canonical units)

| signal                      | unit   | plausible     |   values |   out_of_range | share   |      min |     p1 |        p99 |        max |
|:----------------------------|:-------|:--------------|---------:|---------------:|:--------|---------:|-------:|-----------:|-----------:|
| power_kw                    | kW     | -200 to 10000 |     8910 |              0 | 0.0%    | -17.2    | -4.17  |   2.01e+03 |   2.07e+03 |
| wind_speed_ms               | m/s    | 0 to 60       |     8908 |              0 | 0.0%    |   0      |  1.19  |  10.9      |  14.7      |
| rotor_speed_rpm             | rpm    | 0 to 40       |     8910 |              0 | 0.0%    |   0      |  0     |  15.2      |  15.3      |
| pitch_a_deg                 | deg    | -10 to 100    |     8910 |              0 | 0.0%    |  -0.0188 |  0     |  90        |  92.1      |
| gear_oil_temp_c             | degC   | -30 to 110    |     8910 |              0 | 0.0%    |  27      | 29.4   |  59.6      |  59.9      |
| gear_oil_inlet_pressure_bar | bar    | 0 to 15       |     8910 |             89 | 1.0%    |  -1.54   |  0.229 |   2.59     |  19.4      |
| ambient_temp_c              | degC   | -45 to 55     |     8910 |              0 | 0.0%    |  -0.5    |  0.761 |  18.6      |  20.5      |
| nacelle_position_deg        | deg    | 0 to 360      |     8910 |              0 | 0.0%    |   0.241  |  4.63  | 358        | 360        |

## Units

| signal | decision |
|---|---|
| power_kw | kW -> kW (column name) |
| wind_speed_ms | m/s -> m/s (column name) |
| rotor_speed_rpm | rpm -> rpm (column name) |
| pitch_a_deg | deg -> deg (column name) |
| nacelle_position_deg | deg -> deg (column name) |
| gear_oil_temp_c | degC -> degC (column name) |
| gear_oil_inlet_pressure_bar | bar -> bar (column name) |
| ambient_temp_c | degC -> degC (column name) |

## Sampling interval and aggregation

Native interval = most common step between a turbine's timestamps. Data finer than 10 minutes is aggregated to 10-minute bins (mean; min/max/std for key signals; coverage = samples present / samples expected).

| turbine_id   | interval   |   regular_share |
|:-------------|:-----------|----------------:|
| KEL01        | 1min       |          0.9508 |
| KEL02        | 1min       |          0.9489 |

- Aggregated KEL01, KEL02 from 1min (10 samples per bin): 8,916 bins, mean coverage 94.9%, 6 bins below the minimum coverage (values set to NaN), 0 duplicate samples dropped

Bin coverage per turbine:

| turbine_id   | mean   | bins_lt_90pct   |
|:-------------|:-------|:----------------|
| KEL01        | 95.0%  | 8.5%            |
| KEL02        | 94.8%  | 8.8%            |


## Timestamps and clocks

- Duplicate timestamps collapsed (most complete row kept): none
- Duplicate dates (top): none
- Off-grid timestamps: none
- Local-time conversion: {'scada': {'timezone': 'Europe/London', 'ambiguous_rows': 0, 'nonexistent_rows': 0, 'ambiguous_policy': 'infer', 'nonexistent_policy': 'drop'}}

Best lag vs fleet (10-min steps; 0 = clocks agree), from wind-speed changes:

| turbine_id   |   2022Q1 |
|:-------------|---------:|
| KEL01        |        0 |
| KEL02        |        0 |

## Loader warnings

- high-res aggregation: 6 of 8,916 10-min bins have coverage below 0.5 and were set to NaN (coverage column kept)

## Files read

| file                                           |   rows | turbines   | missing_columns   |
|:-----------------------------------------------|-------:|:-----------|:------------------|
| ingest-fixtures/highres/1min/WTG01_2022-03.csv |  42411 | ['KEL01']  | []                |
| ingest-fixtures/highres/1min/WTG02_2022-03.csv |  42225 | ['KEL02']  | []                |

---
Generated by `windml ingest validate` (projects/windml/src/windml/ingest). Thresholds: gaps >= 1 h, stuck >= 6 h, coverage < 95%, out-of-range share > 0.1%.
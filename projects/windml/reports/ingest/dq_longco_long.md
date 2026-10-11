# Data-quality report: longco_long

Synthetic long-format (tag/value) export generated from Kelmarsh KEL01-02, 2022

- Period (UTC): 2022-01-01 00:00 to 2022-12-31 23:50; 2 turbines; 104,498 10-min rows
- Signals mapped: 7 of 34 canonical signals
- Source files: 12

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
| power_kw                    | 100.0%  | 100.0%  |
| wind_speed_ms               | 100.0%  | 100.0%  |
| ambient_temp_c              | 99.9%   | 99.9%   |
| rotor_speed_rpm             | 100.0%  | 100.0%  |
| gear_oil_temp_c             | 100.0%  | 100.0%  |
| gear_oil_inlet_pressure_bar | 100.0%  | 100.0%  |
| pitch_a_deg                 | 99.9%   | 99.9%   |

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

| signal                      | unit   | plausible     |   values |   out_of_range | share   |     min |     p1 |       p99 |       max |
|:----------------------------|:-------|:--------------|---------:|---------------:|:--------|--------:|-------:|----------:|----------:|
| power_kw                    | kW     | -200 to 10000 |   104498 |              0 | 0.0%    |  -17.6  | -5     |  2.05e+03 |  2.08e+03 |
| wind_speed_ms               | m/s    | 0 to 60       |   104494 |              0 | 0.0%    |    0    |  1.08  | 13.5      | 23.7      |
| ambient_temp_c              | degC   | -45 to 55     |   104412 |              0 | 0.0%    |   -4.4  | -0.215 | 29.3      | 39.2      |
| rotor_speed_rpm             | rpm    | 0 to 40       |   104498 |              0 | 0.0%    |    0    |  0     | 15.2      | 15.4      |
| gear_oil_temp_c             | degC   | -30 to 110    |   104498 |              0 | 0.0%    |    8.6  | 12     | 59.7      | 65        |
| gear_oil_inlet_pressure_bar | bar    | 0 to 15       |   104498 |           2463 | 2.4%    |   -3.03 | -0.581 |  3.45     | 20        |
| pitch_a_deg                 | deg    | -10 to 100    |   104412 |              1 | 0.0%    | -173    |  0     | 92        | 92.6      |

## Units

| signal | decision |
|---|---|
| power_kw | kW -> kW (mapping) |
| wind_speed_ms | m/s -> m/s (mapping) |
| ambient_temp_c | degC -> degC (mapping) |
| rotor_speed_rpm | rpm -> rpm (mapping) |
| gear_oil_temp_c | degC -> degC (mapping) |
| gear_oil_inlet_pressure_bar | kPa -> bar (mapping) |
| pitch_a_deg | deg -> deg (mapping) |

## Sampling interval and aggregation

Native interval = most common step between a turbine's timestamps. Data finer than 10 minutes is aggregated to 10-minute bins (mean; min/max/std for key signals; coverage = samples present / samples expected).

| turbine_id   | interval   |   regular_share |
|:-------------|:-----------|----------------:|
| KEL01        | 10min      |          0.9998 |
| KEL02        | 10min      |          0.9999 |


## Timestamps and clocks

- Duplicate timestamps collapsed (most complete row kept): none
- Duplicate dates (top): none
- Off-grid timestamps: none
- Local-time conversion: timestamps were UTC or carried offsets

Best lag vs fleet (10-min steps; 0 = clocks agree), from wind-speed changes:

| turbine_id   |   2022Q1 |   2022Q2 |   2022Q3 |   2022Q4 |
|:-------------|---------:|---------:|---------:|---------:|
| KEL01        |        0 |        0 |        0 |        0 |
| KEL02        |        0 |        0 |        0 |        0 |

## Files read

| file                                              |   rows | turbines           | missing_columns   |
|:--------------------------------------------------|-------:|:-------------------|:------------------|
| ingest-fixtures/longco/scada_long_2022-01.parquet |  62496 | ['KEL01', 'KEL02'] | []                |
| ingest-fixtures/longco/scada_long_2022-02.parquet |  56448 | ['KEL01', 'KEL02'] | []                |
| ingest-fixtures/longco/scada_long_2022-03.parquet |  62494 | ['KEL01', 'KEL02'] | []                |
| ingest-fixtures/longco/scada_long_2022-04.parquet |  60478 | ['KEL01', 'KEL02'] | []                |
| ingest-fixtures/longco/scada_long_2022-05.parquet |  62247 | ['KEL01', 'KEL02'] | []                |
| ingest-fixtures/longco/scada_long_2022-06.parquet |  58744 | ['KEL01', 'KEL02'] | []                |
| ingest-fixtures/longco/scada_long_2022-07.parquet |  62496 | ['KEL01', 'KEL02'] | []                |
| ingest-fixtures/longco/scada_long_2022-08.parquet |  62496 | ['KEL01', 'KEL02'] | []                |
| ingest-fixtures/longco/scada_long_2022-09.parquet |  58051 | ['KEL01', 'KEL02'] | []                |
| ingest-fixtures/longco/scada_long_2022-10.parquet |  62419 | ['KEL01', 'KEL02'] | []                |
| ingest-fixtures/longco/scada_long_2022-11.parquet |  60445 | ['KEL01', 'KEL02'] | []                |
| ingest-fixtures/longco/scada_long_2022-12.parquet |  62496 | ['KEL01', 'KEL02'] | []                |

---
Generated by `windml ingest validate` (projects/windml/src/windml/ingest). Thresholds: gaps >= 1 h, stuck >= 6 h, coverage < 95%, out-of-range share > 0.1%.
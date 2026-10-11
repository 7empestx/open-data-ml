# Data-quality report: kelmarsh

Kelmarsh wind farm (6x Senvion MM92, UK), Cubico, Greenbyte export

- Period (UTC): 2022-01-01 00:00 to 2022-12-31 23:50; 6 turbines; 315,360 10-min rows
- Signals mapped: 34 of 34 canonical signals
- Source files: 6

## Day-1 findings

1. **Out of range** gear_oil_inlet_pressure_bar: 1.84% of values outside 0 to 15 bar (min -3.03, max 20)
2. **Out of range** pitch_c_deg: 0.33% of values outside -10 to 100 deg (min -198, max 212)
3. **Stuck sensors** (constant >= 6 h, or >= 24 h for coarse sensors): KEL04 pitch_motor_temp_2_c 194.2 h; KEL02 pitch_motor_temp_2_c 177.5 h; KEL04 pitch_motor_temp_3_c 153.3 h; KEL04 pitch_motor_temp_1_c 147.2 h; KEL02 pitch_motor_temp_3_c 137.7 h

## Coverage per turbine

Coverage = 10-min slots with power or wind speed present, over the farm-wide period.

| turbine_id   | first            | last             |   expected_rows |   rows_with_data | coverage   |   gaps_ge_1h |   longest_gap_h |
|:-------------|:-----------------|:-----------------|----------------:|-----------------:|:-----------|-------------:|----------------:|
| KEL01        | 2022-01-01 00:00 | 2022-12-31 23:50 |           52560 |            52010 | 99.0%      |            6 |            48.8 |
| KEL02        | 2022-01-01 00:00 | 2022-12-31 23:50 |           52560 |            52488 | 99.9%      |            2 |             5   |
| KEL03        | 2022-01-01 00:00 | 2022-12-31 23:50 |           52560 |            52448 | 99.8%      |            4 |             5.3 |
| KEL04        | 2022-01-01 00:00 | 2022-12-31 23:50 |           52560 |            52327 | 99.6%      |            5 |            25.5 |
| KEL05        | 2022-01-01 00:00 | 2022-12-31 23:50 |           52560 |            52449 | 99.8%      |            4 |             5.7 |
| KEL06        | 2022-01-01 00:00 | 2022-12-31 23:50 |           52560 |            52324 | 99.6%      |            5 |            15.8 |

## Signal completeness (share of rows with a value)

| signal                      | KEL01   | KEL02   | KEL03   | KEL04   | KEL05   | KEL06   |
|:----------------------------|:--------|:--------|:--------|:--------|:--------|:--------|
| power_kw                    | 99.0%   | 99.9%   | 99.8%   | 99.6%   | 99.8%   | 99.6%   |
| wind_speed_ms               | 98.9%   | 99.9%   | 99.8%   | 99.6%   | 99.8%   | 99.5%   |
| wind_speed_1_ms             | 98.5%   | 99.4%   | 99.3%   | 99.1%   | 99.1%   | 99.1%   |
| wind_speed_2_ms             | 99.0%   | 99.9%   | 99.8%   | 99.6%   | 99.8%   | 99.6%   |
| ambient_temp_c              | 98.9%   | 99.8%   | 99.7%   | 99.5%   | 99.7%   | 99.5%   |
| nacelle_temp_c              | 98.9%   | 99.8%   | 99.7%   | 99.5%   | 99.7%   | 99.5%   |
| rotor_speed_rpm             | 99.0%   | 99.9%   | 99.8%   | 99.6%   | 99.8%   | 99.6%   |
| generator_speed_rpm         | 99.0%   | 99.9%   | 99.8%   | 99.6%   | 99.8%   | 99.6%   |
| gear_oil_temp_c             | 99.0%   | 99.9%   | 99.8%   | 99.6%   | 99.8%   | 99.6%   |
| gear_oil_inlet_temp_c       | 99.0%   | 99.9%   | 99.8%   | 99.6%   | 99.8%   | 99.6%   |
| gear_oil_inlet_pressure_bar | 99.0%   | 99.9%   | 99.8%   | 99.6%   | 99.8%   | 99.6%   |
| main_bearing_front_temp_c   | 98.9%   | 99.8%   | 99.7%   | 99.5%   | 99.7%   | 99.5%   |
| main_bearing_rear_temp_c    | 98.9%   | 99.8%   | 99.7%   | 99.5%   | 99.7%   | 99.5%   |
| rotor_bearing_temp_c        | 99.0%   | 99.9%   | 99.8%   | 99.6%   | 99.8%   | 99.6%   |
| gen_bearing_front_temp_c    | 99.0%   | 99.9%   | 99.8%   | 99.6%   | 99.8%   | 99.6%   |
| gen_bearing_rear_temp_c     | 99.0%   | 99.9%   | 99.8%   | 99.6%   | 99.8%   | 99.6%   |
| converter_inlet_temp_c      | 98.9%   | 99.9%   | 99.8%   | 99.6%   | 99.8%   | 99.6%   |
| pitch_a_deg                 | 98.9%   | 99.8%   | 99.7%   | 99.5%   | 99.7%   | 99.5%   |
| pitch_b_deg                 | 98.9%   | 99.8%   | 99.7%   | 99.5%   | 99.7%   | 99.5%   |
| pitch_c_deg                 | 98.9%   | 99.8%   | 99.7%   | 99.5%   | 99.7%   | 99.5%   |
| nacelle_position_deg        | 99.0%   | 99.9%   | 99.8%   | 99.6%   | 99.8%   | 99.6%   |
| yaw_bearing_angle_deg       | 98.9%   | 99.8%   | 99.7%   | 99.5%   | 99.7%   | 99.5%   |
| wind_direction_deg          | 99.0%   | 99.9%   | 99.8%   | 99.6%   | 99.8%   | 99.6%   |
| power_setpoint_kw           | 98.9%   | 99.8%   | 99.7%   | 99.5%   | 99.7%   | 99.5%   |
| available_capacity_kw       | 99.9%   | 99.9%   | 99.9%   | 99.9%   | 99.9%   | 99.9%   |
| data_availability           | 100.0%  | 100.0%  | 100.0%  | 100.0%  | 100.0%  | 100.0%  |
| energy_export_kwh           | 100.0%  | 100.0%  | 100.0%  | 100.0%  | 100.0%  | 98.5%   |
| lost_prod_curtail_total_kwh | 100.0%  | 100.0%  | 100.0%  | 100.0%  | 100.0%  | 100.0%  |
| lost_prod_downtime_kwh      | 99.9%   | 99.9%   | 99.9%   | 99.9%   | 99.9%   | 99.9%   |
| gear_oil_pump_pressure_bar  | 99.0%   | 99.9%   | 99.8%   | 99.6%   | 99.8%   | 99.6%   |
| hub_temp_c                  | 99.0%   | 99.9%   | 99.8%   | 99.6%   | 99.8%   | 99.6%   |
| pitch_motor_temp_1_c        | 99.0%   | 99.9%   | 99.8%   | 99.6%   | 99.8%   | 99.6%   |
| pitch_motor_temp_2_c        | 99.0%   | 99.9%   | 99.8%   | 99.6%   | 99.8%   | 99.6%   |
| pitch_motor_temp_3_c        | 99.0%   | 99.9%   | 99.8%   | 99.6%   | 99.8%   | 99.6%   |

## Gaps of 1 h or more (20 longest)

26 gaps in total.

| turbine_id   | gap_start        | gap_end          |   hours |
|:-------------|:-----------------|:-----------------|--------:|
| KEL01        | 2022-09-08 08:10 | 2022-09-10 09:00 |    48.8 |
| KEL04        | 2022-03-10 10:20 | 2022-03-11 11:50 |    25.5 |
| KEL01        | 2022-06-20 10:00 | 2022-06-21 09:30 |    23.5 |
| KEL06        | 2022-10-23 18:10 | 2022-10-24 10:00 |    15.8 |
| KEL06        | 2022-06-07 06:50 | 2022-06-07 16:00 |     9.2 |
| KEL06        | 2022-10-31 09:30 | 2022-10-31 16:20 |     6.8 |
| KEL01        | 2022-06-06 10:30 | 2022-06-06 16:30 |     6   |
| KEL05        | 2022-06-06 11:10 | 2022-06-06 16:50 |     5.7 |
| KEL03        | 2022-06-07 10:00 | 2022-06-07 15:20 |     5.3 |
| KEL01        | 2022-06-07 10:00 | 2022-06-07 15:20 |     5.3 |
| KEL04        | 2022-06-07 10:10 | 2022-06-07 15:30 |     5.3 |
| KEL05        | 2022-06-07 10:00 | 2022-06-07 15:20 |     5.3 |
| KEL03        | 2022-06-06 11:10 | 2022-06-06 16:20 |     5.2 |
| KEL02        | 2022-06-07 10:10 | 2022-06-07 15:10 |     5   |
| KEL03        | 2022-09-01 07:50 | 2022-09-01 12:20 |     4.5 |
| KEL05        | 2022-09-01 07:50 | 2022-09-01 12:20 |     4.5 |
| KEL01        | 2022-09-01 07:50 | 2022-09-01 12:20 |     4.5 |
| KEL02        | 2022-09-01 07:50 | 2022-09-01 12:20 |     4.5 |
| KEL06        | 2022-09-01 07:50 | 2022-09-01 12:20 |     4.5 |
| KEL04        | 2022-09-01 07:50 | 2022-09-01 12:20 |     4.5 |

## Stuck sensors (identical value for 6 h or more, 24 h for coarse sensors where >= 60% of readings sit on a 0.5-unit grid; temperatures, pressures, wind speed)

| turbine_id   | signal                      |   coarse_share |   min_run_h |   runs |   hours_stuck |   longest_h | longest_from     |   value |
|:-------------|:----------------------------|---------------:|------------:|-------:|--------------:|------------:|:-----------------|--------:|
| KEL01        | rotor_bearing_temp_c        |           0.02 |           6 |      1 |           6.7 |         6.7 | 2022-12-15 02:10 |    1.4  |
| KEL01        | hub_temp_c                  |           0.8  |          24 |      2 |          59.8 |        34.8 | 2022-03-01 22:20 |   15    |
| KEL01        | pitch_motor_temp_1_c        |           0.31 |           6 |      8 |          52.3 |         7.7 | 2022-09-28 21:20 |   22    |
| KEL01        | pitch_motor_temp_2_c        |           0.33 |           6 |      9 |          62.2 |         8   | 2022-12-01 16:50 |   20    |
| KEL01        | pitch_motor_temp_3_c        |           0.32 |           6 |      6 |          44.7 |         8   | 2022-04-13 00:00 |   24    |
| KEL02        | gen_bearing_front_temp_c    |           0.01 |           6 |      1 |          13.2 |        13.2 | 2022-11-27 04:00 |   12.8  |
| KEL02        | gen_bearing_rear_temp_c     |           0.01 |           6 |      1 |          22   |        22   | 2022-11-28 12:40 |  324    |
| KEL02        | hub_temp_c                  |           0.79 |          24 |      2 |          54.7 |        27.3 | 2022-03-06 18:50 |   13    |
| KEL02        | pitch_motor_temp_1_c        |           0.33 |           6 |     13 |         112   |        17.5 | 2022-12-08 17:40 |   15    |
| KEL02        | pitch_motor_temp_2_c        |           0.34 |           6 |     24 |         178   |        12.8 | 2022-12-13 01:50 |   13    |
| KEL02        | pitch_motor_temp_3_c        |           0.35 |           6 |     17 |         138   |        10.3 | 2022-12-12 01:50 |   12    |
| KEL03        | hub_temp_c                  |           0.79 |          24 |      2 |          50   |        25.2 | 2022-11-09 01:20 |   18    |
| KEL03        | pitch_motor_temp_1_c        |           0.24 |           6 |      5 |          33.7 |         7.2 | 2022-12-15 04:00 |   10    |
| KEL03        | pitch_motor_temp_2_c        |           0.25 |           6 |      4 |          31.8 |         9.7 | 2022-01-24 13:20 |   19    |
| KEL03        | pitch_motor_temp_3_c        |           0.25 |           6 |      3 |          19.8 |         7   | 2022-12-13 03:40 |   12    |
| KEL04        | rotor_bearing_temp_c        |           0.03 |           6 |      2 |          13.8 |         7.7 | 2022-02-13 06:40 |    7.9  |
| KEL04        | gen_bearing_front_temp_c    |           0.02 |           6 |      3 |          22.2 |         8.5 | 2022-02-24 23:10 |    8.9  |
| KEL04        | gen_bearing_rear_temp_c     |           0.02 |           6 |      1 |           6   |         6   | 2022-02-24 23:20 |    7.7  |
| KEL04        | hub_temp_c                  |           0.77 |          24 |      1 |          27.5 |        27.5 | 2022-11-16 12:00 |   17    |
| KEL04        | pitch_motor_temp_1_c        |           0.35 |           6 |     18 |         147   |        11.5 | 2022-03-08 23:30 |   17    |
| KEL04        | pitch_motor_temp_2_c        |           0.37 |           6 |     25 |         194   |        16.2 | 2022-03-03 13:30 |   21    |
| KEL04        | pitch_motor_temp_3_c        |           0.37 |           6 |     19 |         153   |        11.8 | 2022-03-09 12:50 |   19    |
| KEL05        | rotor_bearing_temp_c        |           0.01 |           6 |      1 |           6.5 |         6.5 | 2022-12-14 15:00 |    1.9  |
| KEL05        | gen_bearing_front_temp_c    |           0.01 |           6 |      1 |           9.3 |         9.3 | 2022-12-15 01:00 |    5.7  |
| KEL05        | gen_bearing_rear_temp_c     |           0.01 |           6 |      1 |           8   |         8   | 2022-12-15 00:30 |    3.4  |
| KEL05        | hub_temp_c                  |           0.77 |          24 |      1 |          24.8 |        24.8 | 2022-12-04 07:00 |   14    |
| KEL05        | pitch_motor_temp_1_c        |           0.28 |           6 |      8 |          60.5 |        10.8 | 2022-12-05 14:10 |   19    |
| KEL05        | pitch_motor_temp_2_c        |           0.31 |           6 |      8 |          53.5 |         7.7 | 2022-01-21 04:10 |   16    |
| KEL05        | pitch_motor_temp_3_c        |           0.31 |           6 |      6 |          55.3 |        11   | 2022-12-01 10:20 |   20    |
| KEL06        | gear_oil_inlet_pressure_bar |           0    |           6 |      1 |           7.2 |         7.2 | 2022-05-17 22:50 |    0.01 |
| KEL06        | rotor_bearing_temp_c        |           0.04 |           6 |      1 |           6   |         6   | 2022-12-14 22:50 |    2    |
| KEL06        | hub_temp_c                  |           0.82 |          24 |      2 |          55.5 |        30.7 | 2022-03-02 01:10 |   15    |
| KEL06        | pitch_motor_temp_1_c        |           0.24 |           6 |     10 |          72   |        10.3 | 2022-12-13 07:50 |   13    |
| KEL06        | pitch_motor_temp_2_c        |           0.27 |           6 |      8 |          69.8 |        14.5 | 2022-01-10 11:30 |   20    |
| KEL06        | pitch_motor_temp_3_c        |           0.26 |           6 |     15 |         123   |        14.7 | 2022-12-13 02:50 |   12    |

## Value ranges vs plausible physical range (canonical units)

| signal                      | unit     | plausible     |   values |   out_of_range | share   |        min |      p1 |        p99 |        max |
|:----------------------------|:---------|:--------------|---------:|---------------:|:--------|-----------:|--------:|-----------:|-----------:|
| power_kw                    | kW       | -200 to 10000 |   314046 |              0 | 0.0%    |  -17.8     |  -5.67  |   2.05e+03 |   2.08e+03 |
| wind_speed_ms               | m/s      | 0 to 60       |   314018 |              0 | 0.0%    |    0       |   1.04  |  13.4      |  24.2      |
| wind_speed_1_ms             | m/s      | 0 to 60       |   312444 |              0 | 0.0%    |    0       |   0.491 |  13.6      |  24.5      |
| wind_speed_2_ms             | m/s      | 0 to 60       |   314046 |             51 | 0.0%    |  -15       |   1.04  |  13.4      |  23.3      |
| ambient_temp_c              | degC     | -45 to 55     |   313788 |              0 | 0.0%    |   -4.8     |  -0.442 |  28.9      |  39.3      |
| nacelle_temp_c              | degC     | -40 to 80     |   313788 |              0 | 0.0%    |   -0.6     |   4.25  |  34.6      |  42.7      |
| rotor_speed_rpm             | rpm      | 0 to 40       |   314046 |              0 | 0.0%    |    0       |   0     |  15.2      |  15.4      |
| generator_speed_rpm         | rpm      | -50 to 3000   |   314046 |             12 | 0.0%    | -572       |  -0.105 |   1.8e+03  |   1.82e+03 |
| gear_oil_temp_c             | degC     | -30 to 110    |   314046 |              0 | 0.0%    |    8.6     |  11.2   |  59.7      |  65        |
| gear_oil_inlet_temp_c       | degC     | -30 to 110    |   314046 |              0 | 0.0%    |    3.37    |  10.6   |  58.7      |  60.2      |
| gear_oil_inlet_pressure_bar | bar      | 0 to 15       |   314046 |           5784 | 1.8%    |   -3.03    |  -0.327 |   4.08     |  20        |
| main_bearing_front_temp_c   | degC     | -30 to 110    |   313788 |              0 | 0.0%    |    7.2     |  10.3   |  75.8      |  83.1      |
| main_bearing_rear_temp_c    | degC     | -30 to 110    |   313788 |              0 | 0.0%    |    7.7     |  10.9   |  73        |  81.5      |
| rotor_bearing_temp_c        | degC     | -30 to 110    |   314046 |              0 | 0.0%    |    0.105   |   6     |  38.4      |  48.6      |
| gen_bearing_front_temp_c    | degC     | -30 to 130    |   314046 |              0 | 0.0%    |    5       |   9.2   |  48.3      |  66.2      |
| gen_bearing_rear_temp_c     | degC     | -30 to 130    |   314046 |            134 | 0.0%    |    1.9     |   7.5   |  54.8      | 324        |
| converter_inlet_temp_c      | degC     | -30 to 80     |   314044 |              1 | 0.0%    | -113       |   1.57  |  32.5      |  46.5      |
| pitch_a_deg                 | deg      | -10 to 100    |   313788 |              1 | 0.0%    | -173       |   0     |  91.9      |  92.9      |
| pitch_b_deg                 | deg      | -10 to 100    |   313788 |              3 | 0.0%    | -159       |   0     |  92        |  92.8      |
| pitch_c_deg                 | deg      | -10 to 100    |   313788 |           1024 | 0.3%    | -198       |   0     |  91.9      | 212        |
| nacelle_position_deg        | deg      | 0 to 360      |   314046 |              0 | 0.0%    |    0.00219 |   6.59  | 354        | 360        |
| yaw_bearing_angle_deg       | deg      | -1500 to 1500 |   313788 |              0 | 0.0%    |    0.0137  |   6.59  | 354        | 360        |
| wind_direction_deg          | deg      | 0 to 360      |   314046 |              0 | 0.0%    |    0.0016  |   7.67  | 354        | 360        |
| power_setpoint_kw           | kW       | -10 to 10000  |   313788 |              0 | 0.0%    |  205       | 412     |   2.06e+03 |   2.06e+03 |
| available_capacity_kw       | kW       | -10 to 10000  |   315177 |              0 | 0.0%    |    0       |   0     |   2.05e+03 |   2.05e+03 |
| data_availability           | fraction | 0 to 1        |   315360 |              0 | 0.0%    |    0       |   1     |   1        |   1        |
| energy_export_kwh           | kWh      | -100 to 2000  |   314563 |              0 | 0.0%    |    0       |   0     | 401        | 412        |
| lost_prod_curtail_total_kwh | kWh      | 0 to 2000     |   315360 |              0 | 0.0%    |    0       |   0     |   0        | 160        |
| lost_prod_downtime_kwh      | kWh      | 0 to 2000     |   315177 |              0 | 0.0%    |    0       |   0     | 213        | 343        |
| gear_oil_pump_pressure_bar  | bar      | 0 to 25       |   314046 |              0 | 0.0%    |    0.1     |   0.403 |   8.15     |  20        |
| hub_temp_c                  | degC     | -40 to 70     |   314046 |              0 | 0.0%    |    0       |   9.37  |  33        |  41.9      |
| pitch_motor_temp_1_c        | degC     | -40 to 150    |   314046 |              0 | 0.0%    |    0       |  12.6   |  80.1      |  85.3      |
| pitch_motor_temp_2_c        | degC     | -40 to 150    |   314046 |              0 | 0.0%    |    0       |  13     |  81        |  95.5      |
| pitch_motor_temp_3_c        | degC     | -40 to 150    |   314046 |              0 | 0.0%    |    0       |  12     |  80.9      |  85        |

## Units

| signal | decision |
|---|---|
| power_kw | kW -> kW (column name) |
| wind_speed_ms | m/s -> m/s (column name) |
| wind_speed_1_ms | m/s -> m/s (column name) |
| wind_speed_2_ms | m/s -> m/s (column name) |
| ambient_temp_c | degC -> degC (column name) |
| nacelle_temp_c | degC -> degC (column name) |
| rotor_speed_rpm | rpm -> rpm (column name) |
| generator_speed_rpm | rpm -> rpm (column name) |
| gear_oil_temp_c | degC -> degC (column name) |
| gear_oil_inlet_temp_c | degC -> degC (column name) |
| gear_oil_inlet_pressure_bar | per-row switch: |x| > 20 read as kPa, else bar (94% kPa) |
| main_bearing_front_temp_c | degC -> degC (column name) |
| main_bearing_rear_temp_c | degC -> degC (column name) |
| rotor_bearing_temp_c | degC -> degC (column name) |
| gen_bearing_front_temp_c | degC -> degC (column name) |
| gen_bearing_rear_temp_c | degC -> degC (column name) |
| converter_inlet_temp_c | degC -> degC (column name) |
| pitch_a_deg | deg -> deg (column name) |
| pitch_b_deg | deg -> deg (column name) |
| pitch_c_deg | deg -> deg (column name) |
| nacelle_position_deg | deg -> deg (column name) |
| yaw_bearing_angle_deg | deg -> deg (column name) |
| wind_direction_deg | deg -> deg (column name) |
| power_setpoint_kw | kW -> kW (column name) |
| available_capacity_kw | kW -> kW (column name) |
| data_availability | fraction -> fraction (canonical default) |
| energy_export_kwh | kWh -> kWh (column name) |
| lost_prod_curtail_total_kwh | kWh -> kWh (column name) |
| lost_prod_downtime_kwh | kWh -> kWh (column name) |
| gear_oil_pump_pressure_bar | per-row switch: |x| > 20 read as kPa, else bar (99% kPa) |
| hub_temp_c | degC -> degC (column name) |
| pitch_motor_temp_1_c | degC -> degC (column name) |
| pitch_motor_temp_2_c | degC -> degC (column name) |
| pitch_motor_temp_3_c | degC -> degC (column name) |

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
| KEL03        |        0 |        0 |        0 |        0 |
| KEL04        |        0 |        0 |        0 |        0 |
| KEL05        |        0 |        0 |        0 |        0 |
| KEL06        |        0 |        0 |        0 |        0 |

## Status / alarm log

- Events: 69,850; stops: 919; fault stops: 170; major faults: 12
- Stops by class: {'routine': 464, 'maintenance': 171, 'fault': 170, 'grid': 86, 'weather': 28}
- Events outside the SCADA period: 0; end before start: 0

Top stop codes:

|   code | message                          |   count |
|-------:|:---------------------------------|--------:|
|    710 | Battery test                     |     299 |
|     20 | Manual stop - on site            |     110 |
|   6200 | Cable autounwind                 |     101 |
|   6530 | Anemometer defect                |      92 |
|   3125 | Timeout ready for connection     |      65 |
|   5760 | Hydraulic oil flushing operation |      55 |
|     25 | Manual stop without login        |      41 |
|   4540 | Tower oscillation X level 2      |      19 |
|   3500 | Grid loss                        |      17 |
|   4520 | Tower oscillation X level 1      |      10 |

## Columns in the export that are not mapped

`Wind speed, Standard deviation (m/s)`, `Wind speed, Minimum (m/s)`, `Wind speed, Maximum (m/s)`, `Long Term Wind (m/s)`, `Wind speed Sensor 1, Standard deviation (m/s)`, `Wind speed Sensor 1, Minimum (m/s)`, `Wind speed Sensor 1, Maximum (m/s)`, `Wind speed Sensor 2, Standard deviation (m/s)`, `Wind speed Sensor 2, Minimum (m/s)`, `Wind speed Sensor 2, Maximum (m/s)`, `Density adjusted wind speed (m/s)`, `Wind direction, Standard deviation (°)`, `Wind direction, Minimum (°)`, `Wind direction, Maximum (°)`, `Nacelle position, Standard deviation (°)`, `Nacelle position, Minimum (°)`, `Nacelle position, Maximum (°)`, `Vane position 1+2 (°)`, `Vane position 1+2, Max (°)`, `Vane position 1+2, Min (°)`, `Vane position 1+2, StdDev (°)`, `Energy Export counter (kWh)`, `Energy Import (kWh)`, `Energy Import counter (kWh)`, `Lost Production (Contractual) (kWh)`, `Lost Production (Time-based IEC B.2.2) (kWh)`, `Lost Production (Time-based IEC B.2.3) (kWh)`, `Lost Production (Time-based IEC B.2.4) (kWh)`, `Lost Production (Time-based IEC B.3.2) (kWh)`, `Lost Production (Production-based IEC B.2.2) (kWh)`, `Lost Production (Production-based IEC B.2.3) (kWh)`, `Lost Production (Production-based IEC B.3.2) (kWh)`, `Energy Budget - Default (kWh)`, `Energy Theoretical (kWh)`, `Lost Production to Performance (kWh)`, `Lost Production Total (kWh)`, `Lost Production to Curtailment (Grid) (kWh)`, `Lost Production to Curtailment (Noise) (kWh)`, `Lost Production to Curtailment (Shadow) (kWh)`, `Lost Production to Curtailment (Bats) (kWh)`, `Lost Production to Curtailment (Birds) (kWh)`, `Lost Production to Curtailment (Ice) (kWh)`, `Lost Production to Curtailment (Sector Management) (kWh)`, `Lost Production to Curtailment (Technical) (kWh)`, `Lost Production to Curtailment (Marketing) (kWh)`, `Lost Production to Curtailment (Boat Action) (kWh)`, `Compensated Lost Production (kWh)`, `Virtual Production (kWh)`, `Lost Production to Curtailment (Grid Constraint) (kWh)`, `Lost Production to Downtime and Curtailment Total (kWh)`, `Lost Production (Contractual Global) (kWh)`, `Lost Production (Contractual Custom) (kWh)`, `Potential power default PC (kW)`, `Power, Standard deviation (kW)`, `Power, Minimum (kW)`, `Power, Maximum (kW)`, `Potential power learned PC (kW)`, `Potential power reference turbines (kW)`, `Cascading potential power (kW)`, `Cascading potential power for performance (kW)`, `Potential power met mast anemometer (kW)`, `Potential power primary reference turbines (kW)`, `Potential power secondary reference turbines (kW)`, `Potential power estimated (kW)`, `Potential power MPC (kW)`, `Potential power met mast anemometer MPC (kW)`, `Potential Power Energy Budget (kW)`, `Turbine Power setpoint, Max (kW)`, `Turbine Power setpoint, Min (kW)`, `Turbine Power setpoint, StdDev (kW)`, `Available Capacity for Production (Planned) (kW)`, `Manufacturer Potential Power (SCADA) (kW)`, `Power factor (cosphi)`, `Power factor (cosphi), Max`, `Power factor (cosphi), Min`, `Power factor (cosphi), Standard deviation`, `Reactive power (kvar)`, `Reactive power, Max (kvar)`, `Reactive power, Min (kvar)`, `Reactive power, Standard deviation (kvar)`, `Stator temperature 1 (°C)`, `Transformer temperature (°C)`, `Temp. top box (°C)`, `Transformer cell temperature (°C)`, `Front bearing temperature, Max (°C)`, `Front bearing temperature, Min (°C)`, `Front bearing temperature, Standard deviation (°C)`, `Rear bearing temperature, Max (°C)`, `Rear bearing temperature, Min (°C)`, `Rear bearing temperature, Standard deviation (°C)`, `CPU temperature (°C)`, `Nacelle temperature, Max (°C)`, `Nacelle temperature, Min (°C)`, `Generator bearing front temperature, Max (°C)`, `Generator bearing front temperature, Min (°C)`, `Generator bearing rear temperature, Max (°C)`, `Generator bearing rear temperature, Min (°C)`, `Generator bearing front temperature, Std (°C)`, `Generator bearing rear temperature, Std (°C)`, `Nacelle temperature, Standard deviation (°C)`, `Gear oil temperature, Max (°C)`, `Gear oil temperature, Min (°C)`, `Gear oil temperature, Standard deviation (°C)`, `Hub temperature, min (°C)`, `Hub temperature, max (°C)`, `Hub temperature, standard deviation (°C)`, `Ambient temperature (converter), Max (°C)`, `Ambient temperature (converter), Min (°C)`, `Ambient temperature (converter), StdDev (°C)`, `Gear oil inlet temperature, Max (°C)`, `Gear oil inlet temperature, Min (°C)`, `Gear oil inlet temperature, StdDev (°C)`, `Nacelle ambient temperature, Max (°C)`, `Nacelle ambient temperature, Min (°C)`, `Nacelle ambient temperature, StdDev (°C)`, `Rotor bearing temp, Max (°C)`, `Rotor bearing temp, Min (°C)`, `Rotor bearing temp, StdDev (°C)`, `CPU temperature, Max (°C)`, `CPU temperature, Min (°C)`, `CPU temperature, StdDev (°C)`, `Transformer cell temperature, Max (°C)`, `Transformer cell temperature, Min (°C)`, `Transformer cell temperature, StdDev (°C)`, `Transformer temperature, Max (°C)`, `Transformer temperature, Min (°C)`, `Transformer temperature, StdDev (°C)`, `Stator temperature 1, Max (°C)`, `Stator temperature 1, Min (°C)`, `Stator temperature 1, StdDev (°C)`, `Temp. top box, Max (°C)`, `Temp. top box, Min (°C)`, `Temp. top box, StdDev (°C)`, `Temperature motor axis 1, Max (°C)`, `Temperature motor axis 1, Min (°C)`, `Temperature motor axis 1, StdDev (°C)`, `Temperature motor axis 2, Max (°C)`, `Temperature motor axis 2, Min (°C)`, `Temperature motor axis 2, StdDev (°C)`, `Temperature motor axis 3, Max (°C)`, `Temperature motor axis 3, Min (°C)`, `Temperature motor axis 3, StdDev (°C)`, `Voltage L1 / U (V)`, `Voltage L2 / V (V)`, `Voltage L3 / W (V)`, `Grid voltage (V)`, `Grid voltage, Max (V)`, `Grid voltage, Min (V)`, `Grid voltage, Standard deviation (V)`, `Voltage L1 / U, Min (V)` ...

## Files read

| file                                                                                   |   rows | turbines   | missing_columns   |
|:---------------------------------------------------------------------------------------|-------:|:-----------|:------------------|
| kelmarsh-wind-scada/scada_2022/Turbine_Data_Kelmarsh_1_2022-01-01_-_2023-01-01_228.csv |  52560 | ['KEL01']  | []                |
| kelmarsh-wind-scada/scada_2022/Turbine_Data_Kelmarsh_2_2022-01-01_-_2023-01-01_229.csv |  52560 | ['KEL02']  | []                |
| kelmarsh-wind-scada/scada_2022/Turbine_Data_Kelmarsh_3_2022-01-01_-_2023-01-01_230.csv |  52560 | ['KEL03']  | []                |
| kelmarsh-wind-scada/scada_2022/Turbine_Data_Kelmarsh_4_2022-01-01_-_2023-01-01_231.csv |  52560 | ['KEL04']  | []                |
| kelmarsh-wind-scada/scada_2022/Turbine_Data_Kelmarsh_5_2022-01-01_-_2023-01-01_232.csv |  52560 | ['KEL05']  | []                |
| kelmarsh-wind-scada/scada_2022/Turbine_Data_Kelmarsh_6_2022-01-01_-_2023-01-01_233.csv |  52560 | ['KEL06']  | []                |

---
Generated by `windml ingest validate` (projects/windml/src/windml/ingest). Thresholds: gaps >= 1 h, stuck >= 6 h, coverage < 95%, out-of-range share > 0.1%.
# Data-quality report: penmanshiel

Penmanshiel wind farm (14x Senvion MM82, UK), Cubico, Greenbyte export

- Period (UTC): 2021-01-01 00:00 to 2021-06-30 23:50; 5 turbines; 130,320 10-min rows
- Signals mapped: 34 of 34 canonical signals
- Source files: 5

## Day-1 findings

1. **Out of range** gear_oil_inlet_pressure_bar: 3.19% of values outside 0 to 15 bar (min -2.65, max 20)
2. **Stuck sensors** (constant >= 6 h, or >= 24 h for coarse sensors): PEN15 hub_temp_c 81.8 h; PEN13 pitch_motor_temp_3_c 33.2 h; PEN13 hub_temp_c 31.8 h; PEN11 hub_temp_c 30.5 h; PEN14 hub_temp_c 30.0 h

## Coverage per turbine

Coverage = 10-min slots with power or wind speed present, over the farm-wide period.

| turbine_id   | first            | last             |   expected_rows |   rows_with_data | coverage   |   gaps_ge_1h |   longest_gap_h |
|:-------------|:-----------------|:-----------------|----------------:|-----------------:|:-----------|-------------:|----------------:|
| PEN11        | 2021-01-01 00:00 | 2021-06-30 23:50 |           26064 |            25646 | 98.4%      |            3 |            44.8 |
| PEN12        | 2021-01-01 00:00 | 2021-06-30 23:50 |           26064 |            26045 | 99.9%      |            1 |             3   |
| PEN13        | 2021-01-01 00:00 | 2021-06-30 23:50 |           26064 |            26045 | 99.9%      |            1 |             3   |
| PEN14        | 2021-01-01 00:00 | 2021-06-30 23:50 |           26064 |            26045 | 99.9%      |            1 |             3   |
| PEN15        | 2021-01-01 00:00 | 2021-06-30 23:50 |           26064 |            26016 | 99.8%      |            3 |             3.7 |

## Signal completeness (share of rows with a value)

| signal                      | PEN11   | PEN12   | PEN13   | PEN14   | PEN15   |
|:----------------------------|:--------|:--------|:--------|:--------|:--------|
| power_kw                    | 98.4%   | 99.9%   | 99.9%   | 99.9%   | 99.8%   |
| wind_speed_ms               | 98.4%   | 99.9%   | 97.9%   | 99.9%   | 99.8%   |
| wind_speed_1_ms             | 97.8%   | 99.6%   | 99.4%   | 99.4%   | 99.3%   |
| wind_speed_2_ms             | 98.4%   | 99.9%   | 99.9%   | 99.9%   | 99.8%   |
| ambient_temp_c              | 97.8%   | 99.3%   | 99.3%   | 99.4%   | 99.3%   |
| nacelle_temp_c              | 97.8%   | 99.3%   | 99.3%   | 99.4%   | 99.3%   |
| rotor_speed_rpm             | 98.4%   | 99.9%   | 99.9%   | 99.9%   | 99.8%   |
| generator_speed_rpm         | 98.4%   | 99.9%   | 99.9%   | 99.9%   | 99.8%   |
| gear_oil_temp_c             | 97.8%   | 99.3%   | 99.3%   | 99.4%   | 99.3%   |
| gear_oil_inlet_temp_c       | 97.8%   | 99.3%   | 99.3%   | 99.4%   | 99.3%   |
| gear_oil_inlet_pressure_bar | 98.4%   | 99.9%   | 99.9%   | 99.9%   | 99.8%   |
| main_bearing_front_temp_c   | 97.8%   | 99.3%   | 99.3%   | 99.4%   | 99.3%   |
| main_bearing_rear_temp_c    | 97.8%   | 99.3%   | 99.3%   | 99.4%   | 99.3%   |
| rotor_bearing_temp_c        | 98.4%   | 99.9%   | 99.9%   | 99.9%   | 99.8%   |
| gen_bearing_front_temp_c    | 98.4%   | 99.9%   | 99.9%   | 99.9%   | 99.8%   |
| gen_bearing_rear_temp_c     | 98.4%   | 99.9%   | 99.9%   | 99.9%   | 99.8%   |
| converter_inlet_temp_c      | 98.4%   | 99.9%   | 99.9%   | 99.9%   | 99.8%   |
| pitch_a_deg                 | 97.8%   | 99.3%   | 99.3%   | 99.4%   | 99.3%   |
| pitch_b_deg                 | 97.8%   | 99.3%   | 99.3%   | 99.4%   | 99.3%   |
| pitch_c_deg                 | 97.8%   | 99.3%   | 99.3%   | 99.4%   | 99.3%   |
| nacelle_position_deg        | 98.4%   | 99.9%   | 99.9%   | 99.9%   | 99.8%   |
| yaw_bearing_angle_deg       | 97.8%   | 99.3%   | 99.3%   | 99.4%   | 99.3%   |
| wind_direction_deg          | 98.4%   | 99.9%   | 99.9%   | 99.9%   | 99.8%   |
| power_setpoint_kw           | 97.8%   | 99.3%   | 99.3%   | 99.4%   | 99.3%   |
| available_capacity_kw       | 99.9%   | 99.9%   | 99.9%   | 99.9%   | 99.8%   |
| data_availability           | 100.0%  | 100.0%  | 100.0%  | 100.0%  | 100.0%  |
| energy_export_kwh           | 99.9%   | 99.8%   | 99.9%   | 99.9%   | 100.0%  |
| lost_prod_curtail_total_kwh | 100.0%  | 100.0%  | 100.0%  | 100.0%  | 100.0%  |
| lost_prod_downtime_kwh      | 99.9%   | 99.9%   | 99.9%   | 99.9%   | 99.8%   |
| gear_oil_pump_pressure_bar  | 98.4%   | 99.9%   | 99.9%   | 99.9%   | 99.8%   |
| hub_temp_c                  | 98.4%   | 99.9%   | 99.9%   | 99.9%   | 99.8%   |
| pitch_motor_temp_1_c        | 98.4%   | 99.9%   | 99.9%   | 99.9%   | 99.8%   |
| pitch_motor_temp_2_c        | 98.4%   | 99.9%   | 99.9%   | 99.9%   | 99.8%   |
| pitch_motor_temp_3_c        | 98.4%   | 99.9%   | 99.9%   | 99.9%   | 99.8%   |

## Gaps of 1 h or more (20 longest)

9 gaps in total.

| turbine_id   | gap_start        | gap_end          |   hours |
|:-------------|:-----------------|:-----------------|--------:|
| PEN11        | 2021-01-16 14:40 | 2021-01-18 11:30 |    44.8 |
| PEN11        | 2021-01-18 15:30 | 2021-01-19 13:10 |    21.7 |
| PEN15        | 2021-01-26 06:00 | 2021-01-26 09:40 |     3.7 |
| PEN12        | 2021-02-26 05:50 | 2021-02-26 08:50 |     3   |
| PEN11        | 2021-02-26 05:50 | 2021-02-26 08:50 |     3   |
| PEN13        | 2021-02-26 05:50 | 2021-02-26 08:50 |     3   |
| PEN14        | 2021-02-26 05:50 | 2021-02-26 08:50 |     3   |
| PEN15        | 2021-02-26 05:50 | 2021-02-26 08:50 |     3   |
| PEN15        | 2021-01-03 22:30 | 2021-01-03 23:30 |     1   |

## Stuck sensors (identical value for 6 h or more, 24 h for coarse sensors where >= 60% of readings sit on a 0.5-unit grid; temperatures, pressures, wind speed)

| turbine_id   | signal               |   coarse_share |   min_run_h |   runs |   hours_stuck |   longest_h | longest_from     |   value |
|:-------------|:---------------------|---------------:|------------:|-------:|--------------:|------------:|:-----------------|--------:|
| PEN11        | hub_temp_c           |           0.78 |          24 |      1 |          30.5 |        30.5 | 2021-02-05 13:00 |      13 |
| PEN11        | pitch_motor_temp_2_c |           0.2  |           6 |      2 |          13   |         6.7 | 2021-05-26 03:30 |      21 |
| PEN11        | pitch_motor_temp_3_c |           0.18 |           6 |      3 |          21.2 |         7.8 | 2021-03-01 01:10 |      20 |
| PEN12        | pitch_motor_temp_2_c |           0.2  |           6 |      2 |          17.2 |        10.3 | 2021-06-26 22:00 |      26 |
| PEN12        | pitch_motor_temp_3_c |           0.19 |           6 |      2 |          15.8 |         8.7 | 2021-03-01 00:50 |      22 |
| PEN13        | hub_temp_c           |           0.78 |          24 |      1 |          31.8 |        31.8 | 2021-02-05 16:40 |      13 |
| PEN13        | pitch_motor_temp_1_c |           0.21 |           6 |      2 |          12.5 |         6.5 | 2021-02-28 21:50 |      23 |
| PEN13        | pitch_motor_temp_2_c |           0.21 |           6 |      3 |          22.5 |         8.5 | 2021-01-25 01:30 |      11 |
| PEN13        | pitch_motor_temp_3_c |           0.2  |           6 |      4 |          33.2 |        10   | 2021-01-20 05:30 |      18 |
| PEN14        | hub_temp_c           |           0.76 |          24 |      1 |          30   |        30   | 2021-02-02 10:40 |      12 |
| PEN14        | pitch_motor_temp_1_c |           0.19 |           6 |      1 |           6.5 |         6.5 | 2021-01-13 11:40 |      18 |
| PEN14        | pitch_motor_temp_3_c |           0.19 |           6 |      2 |          14.5 |         7.8 | 2021-02-28 22:50 |      22 |
| PEN15        | hub_temp_c           |           0.79 |          24 |      3 |          81.8 |        30.5 | 2021-02-07 14:50 |       9 |
| PEN15        | pitch_motor_temp_1_c |           0.2  |           6 |      2 |          15.8 |         9   | 2021-01-13 11:10 |      18 |
| PEN15        | pitch_motor_temp_2_c |           0.19 |           6 |      3 |          19.5 |         7.5 | 2021-01-13 11:20 |      18 |

## Value ranges vs plausible physical range (canonical units)

| signal                      | unit     | plausible     |   values |   out_of_range | share   |        min |        p1 |        p99 |        max |
|:----------------------------|:---------|:--------------|---------:|---------------:|:--------|-----------:|----------:|-----------:|-----------:|
| power_kw                    | kW       | -200 to 10000 |   129793 |              0 | 0.0%    |  -17.9     |  -5.24    |   2.05e+03 |   2.07e+03 |
| wind_speed_ms               | m/s      | 0 to 60       |   129260 |              0 | 0.0%    |    0       |   1.11    |  19.3      |  26.5      |
| wind_speed_1_ms             | m/s      | 0 to 60       |   129152 |              0 | 0.0%    |    0       |   0.424   |  17.8      |  26.2      |
| wind_speed_2_ms             | m/s      | 0 to 60       |   129797 |             56 | 0.0%    |   -9.28    |   1.09    |  19.2      |  26        |
| ambient_temp_c              | degC     | -45 to 55     |   129077 |              0 | 0.0%    |   -3.49    |  -1.33    |  18.7      |  22.9      |
| nacelle_temp_c              | degC     | -40 to 80     |   129077 |              0 | 0.0%    |    1.2     |   4.62    |  28.1      |  35.6      |
| rotor_speed_rpm             | rpm      | 0 to 40       |   129793 |              0 | 0.0%    |    0       |   0       |  17.1      |  17.2      |
| generator_speed_rpm         | rpm      | -50 to 3000   |   129795 |              8 | 0.0%    | -575       |  -0.737   |   1.8e+03  |   1.82e+03 |
| gear_oil_temp_c             | degC     | -30 to 110    |   129075 |              0 | 0.0%    |   10       |  23.3     |  59.6      |  60        |
| gear_oil_inlet_temp_c       | degC     | -30 to 110    |   129077 |              0 | 0.0%    |    3.05    |  18.6     |  56.4      |  58.1      |
| gear_oil_inlet_pressure_bar | bar      | 0 to 15       |   129797 |           4141 | 3.2%    |   -2.65    |  -0.789   |   3.17     |  20        |
| main_bearing_front_temp_c   | degC     | -30 to 110    |   129074 |              0 | 0.0%    |    6.6     |  20.8     |  74.5      |  75.4      |
| main_bearing_rear_temp_c    | degC     | -30 to 110    |   129074 |              0 | 0.0%    |    7.62    |  22.2     |  65.7      |  66.9      |
| rotor_bearing_temp_c        | degC     | -30 to 110    |   129794 |              0 | 0.0%    |    4.35    |  12.6     |  36        |  38.6      |
| gen_bearing_front_temp_c    | degC     | -30 to 130    |   129796 |              0 | 0.0%    |    6.4     |  16.9     |  65.6      |  75.5      |
| gen_bearing_rear_temp_c     | degC     | -30 to 130    |   129796 |              0 | 0.0%    |    7.01    |  14.5     |  52.7      |  72.1      |
| converter_inlet_temp_c      | degC     | -30 to 80     |   129797 |              0 | 0.0%    |   -1.25    |   0.908   |  21.9      |  26        |
| pitch_a_deg                 | deg      | -10 to 100    |   129073 |              2 | 0.0%    |  -19       |   0       |  90        |  93.1      |
| pitch_b_deg                 | deg      | -10 to 100    |   129073 |              4 | 0.0%    |  -17.2     |   0       |  90        | 139        |
| pitch_c_deg                 | deg      | -10 to 100    |   129073 |              2 | 0.0%    |  -17.3     |   0       |  90        | 101        |
| nacelle_position_deg        | deg      | 0 to 360      |   129797 |              0 | 0.0%    |    0.0174  |   4.1     | 357        | 360        |
| yaw_bearing_angle_deg       | deg      | -1500 to 1500 |   129077 |              0 | 0.0%    |    0.00682 |   4.08    | 358        | 360        |
| wind_direction_deg          | deg      | 0 to 360      |   129797 |              0 | 0.0%    |    0.00412 |   4.1     | 356        | 360        |
| power_setpoint_kw           | kW       | -10 to 10000  |   129077 |              0 | 0.0%    |  206       | 206       |   2.06e+03 |   2.06e+03 |
| available_capacity_kw       | kW       | -10 to 10000  |   130196 |              0 | 0.0%    |    0       |   0       |   2.05e+03 |   2.05e+03 |
| data_availability           | fraction | 0 to 1        |   130320 |              0 | 0.0%    |    0       |   1       |   1        |   1        |
| energy_export_kwh           | kWh      | -100 to 2000  |   130175 |              0 | 0.0%    |    0       |   0.00794 | 409        | 413        |
| lost_prod_curtail_total_kwh | kWh      | 0 to 2000     |   130320 |              0 | 0.0%    |    0       |   0       |   0        |   0        |
| lost_prod_downtime_kwh      | kWh      | 0 to 2000     |   130196 |              0 | 0.0%    |    0       |   0       | 129        | 343        |
| gear_oil_pump_pressure_bar  | bar      | 0 to 25       |   129797 |              0 | 0.0%    |    0.2     |   0.46    |   9.6      |  20        |
| hub_temp_c                  | degC     | -40 to 70     |   129793 |              0 | 0.0%    |    5.96    |   9       |  24.8      |  27        |
| pitch_motor_temp_1_c        | degC     | -40 to 150    |   129797 |              0 | 0.0%    |    6       |  15       |  81.2      |  85.4      |
| pitch_motor_temp_2_c        | degC     | -40 to 150    |   129797 |              0 | 0.0%    |    6.59    |  15       |  80.7      |  83.5      |
| pitch_motor_temp_3_c        | degC     | -40 to 150    |   129797 |              0 | 0.0%    |    5.16    |  14       |  79        |  83        |

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
| gear_oil_inlet_pressure_bar | per-row switch: |x| > 20 read as kPa, else bar (95% kPa) |
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
| gear_oil_pump_pressure_bar | per-row switch: |x| > 20 read as kPa, else bar (98% kPa) |
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

| turbine_id   |   2021Q1 |   2021Q2 |
|:-------------|---------:|---------:|
| PEN11        |        0 |        0 |
| PEN12        |        0 |        0 |
| PEN13        |        0 |        0 |
| PEN14        |        0 |        0 |
| PEN15        |        0 |        0 |

## Status / alarm log

- Events: 26,658; stops: 453; fault stops: 44; major faults: 2
- Stops by class: {'routine': 228, 'weather': 67, 'maintenance': 64, 'curtailment': 50, 'fault': 44}
- Events outside the SCADA period: 1; end before start: 0

Top stop codes:

|   code | message                          |   count |
|-------:|:---------------------------------|--------:|
|    710 | Battery test                     |     130 |
|   6200 | Cable autounwind                 |      63 |
|     64 | Max. wind speed                  |      51 |
|   9210 | Externally stopped               |      50 |
|     20 | Manual stop - on site            |      46 |
|   5760 | Hydraulic oil flushing operation |      32 |
|   6530 | Anemometer defect                |      14 |
|     21 | Manual stop - remote             |       8 |
|   6540 | Icing (anemometer)               |       8 |
|     25 | Manual stop without login        |       6 |

## Columns in the export that are not mapped

`Wind speed, Standard deviation (m/s)`, `Wind speed, Minimum (m/s)`, `Wind speed, Maximum (m/s)`, `Long Term Wind (m/s)`, `Wind speed Sensor 1, Standard deviation (m/s)`, `Wind speed Sensor 1, Minimum (m/s)`, `Wind speed Sensor 1, Maximum (m/s)`, `Wind speed Sensor 2, Standard deviation (m/s)`, `Wind speed Sensor 2, Minimum (m/s)`, `Wind speed Sensor 2, Maximum (m/s)`, `Density adjusted wind speed (m/s)`, `Wind direction, Standard deviation (°)`, `Wind direction, Minimum (°)`, `Wind direction, Maximum (°)`, `Nacelle position, Standard deviation (°)`, `Nacelle position, Minimum (°)`, `Nacelle position, Maximum (°)`, `Vane position 1+2 (°)`, `Vane position 1+2, Max (°)`, `Vane position 1+2, Min (°)`, `Vane position 1+2, StdDev (°)`, `Energy Export counter (kWh)`, `Energy Import (kWh)`, `Energy Import counter (kWh)`, `Lost Production (Contractual) (kWh)`, `Lost Production (Time-based IEC B.2.2) (kWh)`, `Lost Production (Time-based IEC B.2.3) (kWh)`, `Lost Production (Time-based IEC B.2.4) (kWh)`, `Lost Production (Time-based IEC B.3.2) (kWh)`, `Lost Production (Production-based IEC B.2.2) (kWh)`, `Lost Production (Production-based IEC B.2.3) (kWh)`, `Lost Production (Production-based IEC B.3.2) (kWh)`, `Energy Budget - Default (kWh)`, `Energy Theoretical (kWh)`, `Lost Production to Performance (kWh)`, `Lost Production Total (kWh)`, `Lost Production to Curtailment (Grid) (kWh)`, `Lost Production to Curtailment (Noise) (kWh)`, `Lost Production to Curtailment (Shadow) (kWh)`, `Lost Production to Curtailment (Bats) (kWh)`, `Lost Production to Curtailment (Birds) (kWh)`, `Lost Production to Curtailment (Ice) (kWh)`, `Lost Production to Curtailment (Sector Management) (kWh)`, `Lost Production to Curtailment (Technical) (kWh)`, `Lost Production to Curtailment (Marketing) (kWh)`, `Lost Production to Curtailment (Boat Action) (kWh)`, `Compensated Lost Production (kWh)`, `Virtual Production (kWh)`, `Lost Production to Curtailment (Grid Constraint) (kWh)`, `Lost Production to Downtime and Curtailment Total (kWh)`, `Lost Production (Contractual Global) (kWh)`, `Lost Production (Contractual Custom) (kWh)`, `Potential power default PC (kW)`, `Power, Standard deviation (kW)`, `Power, Minimum (kW)`, `Power, Maximum (kW)`, `Potential power learned PC (kW)`, `Potential power reference turbines (kW)`, `Cascading potential power (kW)`, `Cascading potential power for performance (kW)`, `Potential power met mast anemometer (kW)`, `Potential power primary reference turbines (kW)`, `Potential power secondary reference turbines (kW)`, `Potential power estimated (kW)`, `Potential power MPC (kW)`, `Potential power met mast anemometer MPC (kW)`, `Turbine Power setpoint, Max (kW)`, `Turbine Power setpoint, Min (kW)`, `Turbine Power setpoint, StdDev (kW)`, `Available Capacity for Production (Planned) (kW)`, `APE-2 (kW)`, `Power factor (cosphi)`, `Power factor (cosphi), Max`, `Power factor (cosphi), Min`, `Power factor (cosphi), Standard deviation`, `Reactive power (kvar)`, `Reactive power, Max (kvar)`, `Reactive power, Min (kvar)`, `Reactive power, Standard deviation (kvar)`, `Stator temperature 1 (°C)`, `Transformer temperature (°C)`, `Temp. top box (°C)`, `Transformer cell temperature (°C)`, `Front bearing temperature, Max (°C)`, `Front bearing temperature, Min (°C)`, `Front bearing temperature, Standard deviation (°C)`, `Rear bearing temperature, Max (°C)`, `Rear bearing temperature, Min (°C)`, `Rear bearing temperature, Standard deviation (°C)`, `CPU temperature (°C)`, `Nacelle temperature, Max (°C)`, `Nacelle temperature, Min (°C)`, `Generator bearing front temperature, Max (°C)`, `Generator bearing front temperature, Min (°C)`, `Generator bearing rear temperature, Max (°C)`, `Generator bearing rear temperature, Min (°C)`, `Generator bearing front temperature, Std (°C)`, `Generator bearing rear temperature, Std (°C)`, `Nacelle temperature, Standard deviation (°C)`, `Gear oil temperature, Max (°C)`, `Gear oil temperature, Min (°C)`, `Gear oil temperature, Standard deviation (°C)`, `Hub temperature, min (°C)`, `Hub temperature, max (°C)`, `Hub temperature, standard deviation (°C)`, `Ambient temperature (converter), Max (°C)`, `Ambient temperature (converter), Min (°C)`, `Ambient temperature (converter), StdDev (°C)`, `Gear oil inlet temperature, Max (°C)`, `Gear oil inlet temperature, Min (°C)`, `Gear oil inlet temperature, StdDev (°C)`, `Nacelle ambient temperature, Max (°C)`, `Nacelle ambient temperature, Min (°C)`, `Nacelle ambient temperature, StdDev (°C)`, `Rotor bearing temp, Max (°C)`, `Rotor bearing temp, Min (°C)`, `Rotor bearing temp, StdDev (°C)`, `CPU temperature, Max (°C)`, `CPU temperature, Min (°C)`, `CPU temperature, StdDev (°C)`, `Transformer cell temperature, Max (°C)`, `Transformer cell temperature, Min (°C)`, `Transformer cell temperature, StdDev (°C)`, `Transformer temperature, Max (°C)`, `Transformer temperature, Min (°C)`, `Transformer temperature, StdDev (°C)`, `Stator temperature 1, Max (°C)`, `Stator temperature 1, Min (°C)`, `Stator temperature 1, StdDev (°C)`, `Temp. top box, Max (°C)`, `Temp. top box, Min (°C)`, `Temp. top box, StdDev (°C)`, `Temperature motor axis 1, Max (°C)`, `Temperature motor axis 1, Min (°C)`, `Temperature motor axis 1, StdDev (°C)`, `Temperature motor axis 2, Max (°C)`, `Temperature motor axis 2, Min (°C)`, `Temperature motor axis 2, StdDev (°C)`, `Temperature motor axis 3, Max (°C)`, `Temperature motor axis 3, Min (°C)`, `Temperature motor axis 3, StdDev (°C)`, `Voltage L1 / U (V)`, `Voltage L2 / V (V)`, `Voltage L3 / W (V)`, `Grid voltage (V)`, `Grid voltage, Max (V)`, `Grid voltage, Min (V)`, `Grid voltage, Standard deviation (V)`, `Voltage L1 / U, Min (V)`, `Voltage L1 / U, Max (V)` ...

## Files read

| file                                                                                                   |   rows | turbines   | missing_columns   |
|:-------------------------------------------------------------------------------------------------------|-------:|:-----------|:------------------|
| penmanshiel-wind-scada/scada_2021_wt11-15/Turbine_Data_Penmanshiel_11_2021-01-01_-_2021-07-01_1051.csv |  26064 | ['PEN11']  | []                |
| penmanshiel-wind-scada/scada_2021_wt11-15/Turbine_Data_Penmanshiel_12_2021-01-01_-_2021-07-01_1052.csv |  26064 | ['PEN12']  | []                |
| penmanshiel-wind-scada/scada_2021_wt11-15/Turbine_Data_Penmanshiel_13_2021-01-01_-_2021-07-01_1053.csv |  26064 | ['PEN13']  | []                |
| penmanshiel-wind-scada/scada_2021_wt11-15/Turbine_Data_Penmanshiel_14_2021-01-01_-_2021-07-01_1054.csv |  26064 | ['PEN14']  | []                |
| penmanshiel-wind-scada/scada_2021_wt11-15/Turbine_Data_Penmanshiel_15_2021-01-01_-_2021-07-01_1056.csv |  26064 | ['PEN15']  | []                |

---
Generated by `windml ingest validate` (projects/windml/src/windml/ingest). Thresholds: gaps >= 1 h, stuck >= 6 h, coverage < 95%, out-of-range share > 0.1%.
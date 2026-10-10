### Table 1. Selected settings (chosen on 2017-2020, pooled farms, H = 30 d)

|         | variant   |   halflife_h | subgroup   |   thr |   n_candidates |   n_eligible |
|:--------|:----------|-------------:|:-----------|------:|---------------:|-------------:|
| gearbox | raw       |           24 | oil        |     3 |            168 |           28 |
| pitch   | fleet     |           24 | all        |     8 |            168 |           42 |

### Table 2. Selected setting, H = 30 days

| fault   | farm        | split   | subset   |   episodes |   detected |   expected_chance |   p_value |   median_lead_days |   fa_per_turbine_month |   turbine_months |
|:--------|:------------|:--------|:---------|-----------:|-----------:|------------------:|----------:|-------------------:|-----------------------:|-----------------:|
| gearbox | kelmarsh    | dev     | all      |          1 |          1 |              0.31 |    0.3087 |              28.86 |                  0.826 |            211.8 |
| gearbox | kelmarsh    | dev     | isolated |          1 |          1 |              0.31 |    0.3087 |              28.86 |                  0.826 |            211.8 |
| gearbox | penmanshiel | dev     | all      |         16 |          9 |              6.79 |    0.1804 |              23.19 |                  0.745 |            422.6 |
| gearbox | penmanshiel | dev     | isolated |         13 |          7 |              5.35 |    0.2417 |              23.19 |                  0.745 |            422.6 |
| gearbox | pooled      | dev     | all      |         17 |         10 |              7.1  |    0.1078 |              23.73 |                  0.772 |            634.4 |
| gearbox | pooled      | dev     | isolated |         14 |          8 |              5.65 |    0.1437 |              23.73 |                  0.772 |            634.4 |
| gearbox | kelmarsh    | heldout | all      |          4 |          3 |              2.29 |    0.4141 |              17.32 |                  1.128 |            273.9 |
| gearbox | kelmarsh    | heldout | isolated |          2 |          2 |              1.06 |    0.2618 |              14.64 |                  1.128 |            273.9 |
| gearbox | penmanshiel | heldout | all      |         23 |          5 |              7.28 |    0.9164 |               9.31 |                  0.508 |            537.5 |
| gearbox | penmanshiel | heldout | isolated |         17 |          4 |              5.56 |    0.879  |              11.52 |                  0.508 |            537.5 |
| gearbox | pooled      | heldout | all      |         27 |          8 |              9.57 |    0.8212 |              14.15 |                  0.717 |            811.3 |
| gearbox | pooled      | heldout | isolated |         19 |          6 |              6.62 |    0.7173 |              14.15 |                  0.717 |            811.3 |
| pitch   | kelmarsh    | dev     | all      |          3 |          1 |              0.34 |    0.3203 |               4.11 |                  0.199 |            211.6 |
| pitch   | kelmarsh    | dev     | isolated |          3 |          1 |              0.34 |    0.3203 |               4.11 |                  0.199 |            211.6 |
| pitch   | penmanshiel | dev     | all      |         25 |          2 |              0.35 |    0.0422 |              14.41 |                  0.024 |            422.5 |
| pitch   | penmanshiel | dev     | isolated |         15 |          1 |              0.23 |    0.2149 |              26.85 |                  0.024 |            422.5 |
| pitch   | pooled      | dev     | all      |         28 |          3 |              0.69 |    0.0213 |               4.11 |                  0.082 |            634   |
| pitch   | pooled      | dev     | isolated |         18 |          2 |              0.57 |    0.096  |              15.48 |                  0.082 |            634   |
| pitch   | kelmarsh    | heldout | all      |         12 |          0 |              0.19 |    1      |             nan    |                  0.102 |            273.8 |
| pitch   | kelmarsh    | heldout | isolated |          8 |          0 |              0.19 |    1      |             nan    |                  0.102 |            273.8 |
| pitch   | penmanshiel | heldout | all      |         36 |          1 |              2.03 |    0.8869 |              27.47 |                  0.065 |            537.3 |
| pitch   | penmanshiel | heldout | isolated |         29 |          1 |              1.56 |    0.8119 |              27.47 |                  0.065 |            537.3 |
| pitch   | pooled      | heldout | all      |         48 |          1 |              2.22 |    0.9078 |              27.47 |                  0.078 |            811.1 |
| pitch   | pooled      | heldout | isolated |         37 |          1 |              1.75 |    0.8465 |              27.47 |                  0.078 |            811.1 |

### Table 3. Selected setting, H = 7 days

| fault   | farm        | split   | subset   |   episodes |   detected |   expected_chance |   p_value |   median_lead_days |   fa_per_turbine_month |   turbine_months |
|:--------|:------------|:--------|:---------|-----------:|-----------:|------------------:|----------:|-------------------:|-----------------------:|-----------------:|
| gearbox | kelmarsh    | dev     | all      |          1 |          0 |              0.06 |    1      |             nan    |                  0.831 |            211.8 |
| gearbox | penmanshiel | dev     | all      |         14 |          2 |              2.26 |    0.7021 |               2.71 |                  0.774 |            422.6 |
| gearbox | pooled      | dev     | all      |         15 |          2 |              2.31 |    0.7152 |               2.71 |                  0.793 |            634.4 |
| gearbox | kelmarsh    | heldout | all      |          4 |          0 |              0.73 |    1      |             nan    |                  1.143 |            273.9 |
| gearbox | penmanshiel | heldout | all      |         23 |          3 |              2.56 |    0.4846 |               3.7  |                  0.515 |            537.5 |
| gearbox | pooled      | heldout | all      |         27 |          3 |              3.29 |    0.6662 |               3.7  |                  0.727 |            811.3 |
| pitch   | kelmarsh    | dev     | all      |          3 |          1 |              0.1  |    0.0948 |               4.11 |                  0.199 |            211.6 |
| pitch   | penmanshiel | dev     | all      |         25 |          1 |              0.07 |    0.065  |               1.97 |                  0.026 |            422.5 |
| pitch   | pooled      | dev     | all      |         28 |          2 |              0.16 |    0.0088 |               3.04 |                  0.084 |            634   |
| pitch   | kelmarsh    | heldout | all      |         13 |          0 |              0.12 |    1      |             nan    |                  0.102 |            273.8 |
| pitch   | penmanshiel | heldout | all      |         36 |          0 |              0.61 |    1      |             nan    |                  0.067 |            537.3 |
| pitch   | pooled      | heldout | all      |         49 |          0 |              0.73 |    1      |             nan    |                  0.079 |            811.1 |

### Table 4. By test year (selected setting, H = 30 d)

| fault   | farm        | split   |   year |   episodes |   detected |   expected_chance |   p_value |   median_lead_days |   fa_per_turbine_month |
|:--------|:------------|:--------|-------:|-----------:|-----------:|------------------:|----------:|-------------------:|-----------------------:|
| gearbox | kelmarsh    | dev     |   2017 |          0 |          0 |            nan    |  nan      |             nan    |                nan     |
| gearbox | kelmarsh    | dev     |   2018 |          1 |          1 |              0.31 |    0.3087 |              28.86 |                  0.115 |
| gearbox | kelmarsh    | dev     |   2019 |          0 |          0 |            nan    |  nan      |             nan    |                  1.29  |
| gearbox | kelmarsh    | dev     |   2020 |          0 |          0 |            nan    |  nan      |             nan    |                  1.055 |
| gearbox | penmanshiel | dev     |   2017 |          0 |          0 |            nan    |  nan      |             nan    |                nan     |
| gearbox | penmanshiel | dev     |   2018 |          4 |          4 |              2.06 |    0.0468 |              20.09 |                  1.022 |
| gearbox | penmanshiel | dev     |   2019 |          6 |          3 |              2.28 |    0.4152 |              23.19 |                  0.59  |
| gearbox | penmanshiel | dev     |   2020 |          6 |          2 |              2.45 |    0.7914 |              23.46 |                  0.735 |
| gearbox | kelmarsh    | heldout |   2021 |          1 |          1 |              0.84 |    0.8352 |              27.91 |                  1.393 |
| gearbox | kelmarsh    | heldout |   2022 |          0 |          0 |            nan    |  nan      |             nan    |                  0.929 |
| gearbox | kelmarsh    | heldout |   2023 |          2 |          1 |              0.78 |    0.6304 |              17.32 |                  0.873 |
| gearbox | kelmarsh    | heldout |   2024 |          1 |          1 |              0.67 |    0.6749 |              11.96 |                  1.332 |
| gearbox | penmanshiel | heldout |   2021 |          7 |          2 |              2.24 |    0.7533 |               4.86 |                  0.484 |
| gearbox | penmanshiel | heldout |   2022 |          6 |          1 |              2    |    0.9235 |               6.7  |                  0.505 |
| gearbox | penmanshiel | heldout |   2023 |          6 |          1 |              1.55 |    0.8381 |              16.34 |                  0.528 |
| gearbox | penmanshiel | heldout |   2024 |          4 |          1 |              1.48 |    0.8925 |              25.57 |                  0.529 |
| pitch   | kelmarsh    | dev     |   2017 |          0 |          0 |            nan    |  nan      |             nan    |                nan     |
| pitch   | kelmarsh    | dev     |   2018 |          1 |          1 |              0.26 |    0.2596 |               4.11 |                  0.592 |
| pitch   | kelmarsh    | dev     |   2019 |          0 |          0 |            nan    |  nan      |             nan    |                  0     |
| pitch   | kelmarsh    | dev     |   2020 |          2 |          0 |              0.08 |    1      |             nan    |                  0.014 |
| pitch   | penmanshiel | dev     |   2017 |          0 |          0 |            nan    |  nan      |             nan    |                nan     |
| pitch   | penmanshiel | dev     |   2018 |          3 |          0 |              0    |    1      |             nan    |                  0     |
| pitch   | penmanshiel | dev     |   2019 |         12 |          0 |              0    |    1      |             nan    |                  0     |
| pitch   | penmanshiel | dev     |   2020 |         10 |          2 |              0.35 |    0.0422 |              14.41 |                  0.063 |
| pitch   | kelmarsh    | heldout |   2021 |          2 |          0 |              0.14 |    1      |             nan    |                  0.303 |
| pitch   | kelmarsh    | heldout |   2022 |          2 |          0 |              0    |    1      |             nan    |                  0     |
| pitch   | kelmarsh    | heldout |   2023 |          1 |          0 |              0.05 |    1      |             nan    |                  0.115 |
| pitch   | kelmarsh    | heldout |   2024 |          7 |          0 |              0    |    1      |             nan    |                  0     |
| pitch   | penmanshiel | heldout |   2021 |         16 |          0 |              0.58 |    1      |             nan    |                  0.054 |
| pitch   | penmanshiel | heldout |   2022 |         10 |          0 |              0.2  |    1      |             nan    |                  0.031 |
| pitch   | penmanshiel | heldout |   2023 |          7 |          0 |              0.99 |    1      |             nan    |                  0.124 |
| pitch   | penmanshiel | heldout |   2024 |          3 |          1 |              0.25 |    0.2382 |              27.47 |                  0.034 |

### Table 5. Whole grid (168 settings per farm and fault, H = 30 d): how many settings reach p < 0.05

| farm        | fault   | split   |   configs |   n_p_below_005 |   expected_by_chance_if_independent |   min_p | best_config                  | best_detected     |
|:------------|:--------|:--------|----------:|----------------:|------------------------------------:|--------:|:-----------------------------|:------------------|
| kelmarsh    | gearbox | dev     |       126 |               0 |                                 6.3 |  0.3087 | raw/oil/hl24/thr3.0          | 1/1 (exp 0.31)    |
| kelmarsh    | gearbox | heldout |       168 |               2 |                                 8.4 |  0.0178 | raw/temps/hl6/thr3.0         | 3/4 (exp 0.87)    |
| kelmarsh    | pitch   | dev     |       168 |               0 |                                 8.4 |  0.288  | raw/all/hl72/thr2.0          | 3/3 (exp 2.01)    |
| kelmarsh    | pitch   | heldout |       168 |               3 |                                 8.4 |  0.019  | raw/all/hl24/thr2.0          | 12/12 (exp 9.03)  |
| penmanshiel | gearbox | dev     |       168 |               0 |                                 8.4 |  0.0506 | raw/pressure/hl6/thr4.0      | 15/16 (exp 12.21) |
| penmanshiel | gearbox | heldout |       168 |               0 |                                 8.4 |  0.0582 | raw/pressure/hl24/thr8.0     | 3/23 (exp 0.93)   |
| penmanshiel | pitch   | dev     |       168 |              12 |                                 8.4 |  0.0306 | raw/all/hl72/thr6.0          | 3/25 (exp 0.86)   |
| penmanshiel | pitch   | heldout |       168 |               1 |                                 8.4 |  0.041  | fleet/motor_temps/hl6/thr5.0 | 1/36 (exp 0.04)   |

### Table 6. Turbine-level ranking check (Spearman rank correlation)

| farm        | fault   |   turbines |   spearman_alarmtime_dev_vs_episodes_heldout |   spearman_episodes_dev_vs_episodes_heldout |
|:------------|:--------|-----------:|---------------------------------------------:|--------------------------------------------:|
| kelmarsh    | gearbox |          6 |                                       -0.062 |                                       0.283 |
| kelmarsh    | pitch   |          6 |                                       -0.441 |                                      -0.302 |
| penmanshiel | gearbox |         14 |                                       -0.04  |                                       0.089 |
| penmanshiel | pitch   |         14 |                                       -0.072 |                                      -0.021 |

### Table 7. Healthy test-period MAE by test year (median over turbines; deg C, bar, or deg)

| farm        | target                      |   2018 |   2019 |   2020 |   2021 |   2022 |   2023 |   2024 |
|:------------|:----------------------------|-------:|-------:|-------:|-------:|-------:|-------:|-------:|
| kelmarsh    | gear_oil_inlet_pressure_bar | nan    |   0.2  |   0.19 |   0.23 |   0.22 |   0.19 |   0.22 |
| kelmarsh    | gear_oil_inlet_temp_c       |   2.07 |   1.91 |   1.82 |   1.72 |   1.85 |   2.12 |   2.57 |
| kelmarsh    | gear_oil_pump_pressure_bar  | nan    |   0.24 |   0.22 |   0.24 |   0.25 |   0.27 |   0.33 |
| kelmarsh    | gear_oil_temp_c             |   0.84 |   0.79 |   0.73 |   0.79 |   0.78 |   1.1  |   1.38 |
| kelmarsh    | hub_temp_c                  |   0.43 |   0.38 |   0.37 |   0.39 |   0.37 |   0.37 |   0.36 |
| kelmarsh    | main_bearing_front_temp_c   |   0.85 |   0.82 |   0.79 |   0.83 |   0.86 |   1.13 |   1.29 |
| kelmarsh    | main_bearing_rear_temp_c    |   0.77 |   0.74 |   0.69 |   0.75 |   0.74 |   0.97 |   1.19 |
| kelmarsh    | pitch_mean_deg              |   1.7  |   1.52 |   1.48 |   1.88 |   1.74 |   1.47 |   1.48 |
| kelmarsh    | pitch_motor_temp_1_c        | nan    |   3.4  |   3.25 |   3.21 |   3.19 |   3.24 |   3.35 |
| kelmarsh    | pitch_motor_temp_2_c        | nan    |   3.43 |   3.3  |   3.19 |   3.23 |   3.35 |   3.28 |
| kelmarsh    | pitch_motor_temp_3_c        | nan    | nan    |   3.42 |   3.29 |   3.25 |   3.24 |   3.23 |
| penmanshiel | gear_oil_inlet_pressure_bar |   0.2  |   0.25 |   0.24 |   0.28 |   0.24 |   0.28 |   0.25 |
| penmanshiel | gear_oil_inlet_temp_c       | nan    | nan    |   2.57 |   2.49 |   2.67 |   2.62 |   2.75 |
| penmanshiel | gear_oil_pump_pressure_bar  |   0.48 |   0.48 |   0.45 |   0.49 |   0.52 |   0.7  |   0.7  |
| penmanshiel | gear_oil_temp_c             | nan    | nan    |   1.01 |   1.05 |   0.98 |   1.04 |   1.19 |
| penmanshiel | hub_temp_c                  |   0.44 |   0.37 |   0.36 |   0.39 |   0.41 |   0.44 |   0.51 |
| penmanshiel | main_bearing_front_temp_c   | nan    | nan    |   1.32 |   1.46 |   1.36 |   1.39 |   1.09 |
| penmanshiel | main_bearing_rear_temp_c    | nan    | nan    |   1.01 |   1.16 |   1.04 |   1.1  |   1.07 |
| penmanshiel | pitch_mean_deg              | nan    | nan    |   1.15 |   1.23 |   1.09 |   1.16 |   1.01 |
| penmanshiel | pitch_motor_temp_1_c        |   4.22 |   3.97 |   3.91 |   3.66 |   3.79 |   3.81 |   3.9  |
| penmanshiel | pitch_motor_temp_2_c        |   4.29 |   4    |   3.72 |   3.65 |   3.74 |   3.87 |   4.07 |
| penmanshiel | pitch_motor_temp_3_c        |   4.24 |   3.97 |   3.79 |   3.68 |   3.79 |   3.75 |   4.08 |

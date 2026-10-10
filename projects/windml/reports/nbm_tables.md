### Table A. Primary setting: EWMA (12 h half-life) of residual z, alarm when max over targets > 3

| farm        | setting                |   horizon | subset      |   episodes |   detected (onset) |   chance (flat) |   chance (season-matched) |   p (season-matched) |   detected (any active alarm) |   median lead (d) |   false alarms / turbine-month |
|:------------|:-----------------------|----------:|:------------|-----------:|-------------------:|----------------:|--------------------------:|---------------------:|------------------------------:|------------------:|-------------------------------:|
| kelmarsh    | in_farm                |         7 | all         |          8 |                  5 |            1.08 |                      1.95 |                0.019 |                             6 |             1.59  |                           0.78 |
| kelmarsh    | in_farm                |         7 | no_heatwave |          5 |                  2 |            0.67 |                      0.83 |                0.194 |                             3 |             4.22  |                           0.78 |
| kelmarsh    | in_farm                |        30 | all         |          8 |                  6 |            2.91 |                      6.05 |                0.721 |                             7 |            26.89  |                           0.64 |
| kelmarsh    | in_farm                |        30 | no_heatwave |          5 |                  3 |            1.68 |                      3.09 |                0.739 |                             4 |            24.03  |                           0.64 |
| kelmarsh    | in_farm_fleet_relative |         7 | all         |          8 |                  1 |            0.7  |                      0.49 |                0.401 |                             2 |             1.97  |                           0.3  |
| kelmarsh    | in_farm_fleet_relative |         7 | no_heatwave |          5 |                  1 |            0.5  |                      0.34 |                0.296 |                             2 |             1.97  |                           0.3  |
| kelmarsh    | in_farm_fleet_relative |        30 | all         |          8 |                  4 |            2.31 |                      1.49 |                0.043 |                             5 |            24.78  |                           0.19 |
| kelmarsh    | in_farm_fleet_relative |        30 | no_heatwave |          5 |                  3 |            1.65 |                      0.99 |                0.054 |                             4 |            24.01  |                           0.19 |
| penmanshiel | cross_farm_kel_to_pen  |         7 | all         |          2 |                  0 |            0.34 |                      0.15 |                1     |                             0 |           nan     |                           0.53 |
| penmanshiel | cross_farm_kel_to_pen  |         7 | no_heatwave |          2 |                  0 |            0.34 |                      0.15 |                1     |                             0 |           nan     |                           0.53 |
| penmanshiel | cross_farm_kel_to_pen  |        30 | all         |          2 |                  1 |            1.09 |                      0.14 |                0.135 |                             1 |            29.96  |                           0.49 |
| penmanshiel | cross_farm_kel_to_pen  |        30 | no_heatwave |          2 |                  1 |            1.09 |                      0.14 |                0.135 |                             1 |            29.96  |                           0.49 |
| penmanshiel | in_farm                |         7 | all         |          2 |                  2 |            0.83 |                      0.32 |                0.024 |                             2 |             4.535 |                           1.26 |
| penmanshiel | in_farm                |         7 | no_heatwave |          2 |                  2 |            0.83 |                      0.32 |                0.024 |                             2 |             4.535 |                           1.26 |
| penmanshiel | in_farm                |        30 | all         |          2 |                  2 |            1.75 |                      0.63 |                0.076 |                             2 |             4.535 |                           1.26 |
| penmanshiel | in_farm                |        30 | no_heatwave |          2 |                  2 |            1.75 |                      0.63 |                0.076 |                             2 |             4.535 |                           1.26 |
| penmanshiel | in_farm_fleet_relative |         7 | all         |          2 |                  0 |            0.31 |                      0.17 |                1     |                             0 |           nan     |                           0.57 |
| penmanshiel | in_farm_fleet_relative |         7 | no_heatwave |          2 |                  0 |            0.31 |                      0.17 |                1     |                             0 |           nan     |                           0.57 |
| penmanshiel | in_farm_fleet_relative |        30 | all         |          2 |                  0 |            1.06 |                      0.18 |                1     |                             0 |           nan     |                           0.57 |
| penmanshiel | in_farm_fleet_relative |        30 | no_heatwave |          2 |                  0 |            1.06 |                      0.18 |                1     |                             0 |           nan     |                           0.57 |

### Table B. Sensitivity: all score types and thresholds, 30-day horizon, all episodes

| farm        | setting                | score       |   thr |   episodes |   detected_onset |   expected_seasonal_onset |   p_value_seasonal_onset |   false_alarms_per_turbine_month |
|:------------|:-----------------------|:------------|------:|-----------:|-----------------:|--------------------------:|-------------------------:|---------------------------------:|
| kelmarsh    | in_farm                | score_cusum |    25 |          8 |                6 |                      7.35 |                    0.983 |                             2.61 |
| kelmarsh    | in_farm                | score_cusum |    50 |          8 |                6 |                      7.49 |                    0.991 |                             2.35 |
| kelmarsh    | in_farm                | score_cusum |   100 |          8 |                6 |                      7.6  |                    0.996 |                             1.64 |
| kelmarsh    | in_farm                | score_ewma  |     2 |          8 |                8 |                      6.85 |                    0.275 |                             0.97 |
| kelmarsh    | in_farm                | score_ewma  |     3 |          8 |                6 |                      6.05 |                    0.721 |                             0.64 |
| kelmarsh    | in_farm                | score_ewma  |     4 |          8 |                7 |                      5.07 |                    0.088 |                             0.44 |
| kelmarsh    | in_farm_fleet_relative | score_cusum |    25 |          8 |                7 |                      7.44 |                    0.896 |                             2.77 |
| kelmarsh    | in_farm_fleet_relative | score_cusum |    50 |          8 |                7 |                      7.65 |                    0.956 |                             2.02 |
| kelmarsh    | in_farm_fleet_relative | score_cusum |   100 |          8 |                8 |                      6.49 |                    0.181 |                             1.19 |
| kelmarsh    | in_farm_fleet_relative | score_ewma  |     2 |          8 |                5 |                      3.9  |                    0.333 |                             0.53 |
| kelmarsh    | in_farm_fleet_relative | score_ewma  |     3 |          8 |                4 |                      1.49 |                    0.043 |                             0.19 |
| kelmarsh    | in_farm_fleet_relative | score_ewma  |     4 |          8 |                4 |                      0.55 |                    0     |                             0.13 |
| penmanshiel | cross_farm_kel_to_pen  | score_cusum |    25 |          2 |                2 |                      1.97 |                    0.965 |                             2.47 |
| penmanshiel | cross_farm_kel_to_pen  | score_cusum |    50 |          2 |                2 |                      1.98 |                    0.975 |                             3.37 |
| penmanshiel | cross_farm_kel_to_pen  | score_cusum |   100 |          2 |                2 |                      1.97 |                    0.966 |                             2.88 |
| penmanshiel | cross_farm_kel_to_pen  | score_ewma  |     2 |          2 |                0 |                      1.08 |                    1     |                             1.18 |
| penmanshiel | cross_farm_kel_to_pen  | score_ewma  |     3 |          2 |                1 |                      0.14 |                    0.135 |                             0.49 |
| penmanshiel | cross_farm_kel_to_pen  | score_ewma  |     4 |          2 |                0 |                      0.14 |                    1     |                             0.24 |
| penmanshiel | in_farm                | score_cusum |    25 |          2 |                2 |                      1.98 |                    0.975 |                             2.31 |
| penmanshiel | in_farm                | score_cusum |    50 |          2 |                2 |                      2    |                    1     |                             2.35 |
| penmanshiel | in_farm                | score_cusum |   100 |          2 |                2 |                      2    |                    1     |                             2.11 |
| penmanshiel | in_farm                | score_ewma  |     2 |          2 |                2 |                      1.97 |                    0.971 |                             2.39 |
| penmanshiel | in_farm                | score_ewma  |     3 |          2 |                2 |                      0.63 |                    0.076 |                             1.26 |
| penmanshiel | in_farm                | score_ewma  |     4 |          2 |                0 |                      0.35 |                    1     |                             0.65 |
| penmanshiel | in_farm_fleet_relative | score_cusum |    25 |          2 |                2 |                      1.98 |                    0.975 |                             3.77 |
| penmanshiel | in_farm_fleet_relative | score_cusum |    50 |          2 |                2 |                      1.99 |                    0.985 |                             2.31 |
| penmanshiel | in_farm_fleet_relative | score_cusum |   100 |          2 |                2 |                      1.78 |                    0.79  |                             1.7  |
| penmanshiel | in_farm_fleet_relative | score_ewma  |     2 |          2 |                0 |                      0.89 |                    1     |                             1.1  |
| penmanshiel | in_farm_fleet_relative | score_ewma  |     3 |          2 |                0 |                      0.18 |                    1     |                             0.57 |
| penmanshiel | in_farm_fleet_relative | score_ewma  |     4 |          2 |                0 |                      0.18 |                    1     |                             0.32 |

### Table C. Per-episode result (EWMA > 3, 30-day horizon)

| setting                | turbine_id   |   episode | start                     |   codes | component   | heatwave   |   window_scored_days | detected_onset   |   lead_onset_days | detected_active   |
|:-----------------------|:-------------|----------:|:--------------------------|--------:|:------------|:-----------|---------------------:|:-----------------|------------------:|:------------------|
| in_farm                | KEL01        |         1 | 2022-05-16 05:46:21+00:00 |    5510 | hydraulics  | False      |                   30 | True             |             24.03 | True              |
| in_farm                | KEL02        |         2 | 2022-11-30 10:21:28+00:00 |    3110 | converter   | False      |                   30 | False            |            nan    | True              |
| in_farm                | KEL03        |         3 | 2022-07-19 13:51:34+00:00 |    3151 | converter   | True       |                   30 | True             |             26.81 | True              |
| in_farm                | KEL04        |         4 | 2022-02-08 22:56:57+00:00 |    3110 | converter   | False      |                    0 | False            |            nan    | False             |
| in_farm                | KEL05        |         5 | 2022-07-19 12:36:00+00:00 |    3151 | converter   | True       |                   30 | True             |             26.97 | True              |
| in_farm                | KEL06        |         6 | 2022-03-18 04:13:32+00:00 | 550,672 | pitch       | False      |                   30 | False            |            nan    | False             |
| in_farm                | KEL06        |         7 | 2022-04-12 16:46:52+00:00 |    6300 | yaw         | False      |                   30 | True             |             14.66 | True              |
| in_farm                | KEL06        |         8 | 2022-05-12 02:37:43+00:00 |     555 | pitch       | False      |                   30 | True             |             28.08 | True              |
| in_farm                | KEL06        |         9 | 2022-07-19 13:17:02+00:00 |    3151 | converter   | True       |                   30 | True             |             27.41 | True              |
| in_farm                | PEN11        |         1 | 2021-03-04 22:24:34+00:00 |     715 | pitch       | False      |                   30 | True             |              4.46 | True              |
| in_farm                | PEN14        |         2 | 2021-04-04 14:05:17+00:00 |     658 | pitch       | False      |                   30 | True             |              4.61 | True              |
| cross_farm_kel_to_pen  | PEN11        |         1 | 2021-03-04 22:24:34+00:00 |     715 | pitch       | False      |                   30 | True             |             29.96 | True              |
| cross_farm_kel_to_pen  | PEN14        |         2 | 2021-04-04 14:05:17+00:00 |     658 | pitch       | False      |                   30 | False            |            nan    | False             |
| in_farm_fleet_relative | KEL01        |         1 | 2022-05-16 05:46:21+00:00 |    5510 | hydraulics  | False      |                   30 | True             |             24.01 | True              |
| in_farm_fleet_relative | KEL02        |         2 | 2022-11-30 10:21:28+00:00 |    3110 | converter   | False      |                   30 | False            |            nan    | True              |
| in_farm_fleet_relative | KEL03        |         3 | 2022-07-19 13:51:34+00:00 |    3151 | converter   | True       |                   30 | False            |            nan    | False             |
| in_farm_fleet_relative | KEL04        |         4 | 2022-02-08 22:56:57+00:00 |    3110 | converter   | False      |                    0 | False            |            nan    | False             |
| in_farm_fleet_relative | KEL05        |         5 | 2022-07-19 12:36:00+00:00 |    3151 | converter   | True       |                   30 | False            |            nan    | False             |
| in_farm_fleet_relative | KEL06        |         6 | 2022-03-18 04:13:32+00:00 | 550,672 | pitch       | False      |                   30 | False            |            nan    | False             |
| in_farm_fleet_relative | KEL06        |         7 | 2022-04-12 16:46:52+00:00 |    6300 | yaw         | False      |                   30 | True             |             14.42 | True              |
| in_farm_fleet_relative | KEL06        |         8 | 2022-05-12 02:37:43+00:00 |     555 | pitch       | False      |                   30 | True             |             27.92 | True              |
| in_farm_fleet_relative | KEL06        |         9 | 2022-07-19 13:17:02+00:00 |    3151 | converter   | True       |                   30 | True             |             25.55 | True              |
| in_farm_fleet_relative | PEN11        |         1 | 2021-03-04 22:24:34+00:00 |     715 | pitch       | False      |                   30 | False            |            nan    | False             |
| in_farm_fleet_relative | PEN14        |         2 | 2021-04-04 14:05:17+00:00 |     658 | pitch       | False      |                   30 | False            |            nan    | False             |

### Table D. Healthy test-period MAE (deg C), forward-chained, mean over turbines

| farm        | target                    |   lgbm |   ridge |
|:------------|:--------------------------|-------:|--------:|
| kelmarsh    | gear_oil_inlet_temp_c     |   2.28 |    3.47 |
| kelmarsh    | gear_oil_temp_c           |   1.21 |    2.31 |
| kelmarsh    | gen_bearing_front_temp_c  |   1.79 |    2.08 |
| kelmarsh    | gen_bearing_rear_temp_c   |   2    |    2.26 |
| kelmarsh    | main_bearing_front_temp_c |   1.18 |    2.43 |
| kelmarsh    | main_bearing_rear_temp_c  |   1.13 |    2.07 |
| kelmarsh    | rotor_bearing_temp_c      |   1.2  |    0.67 |
| penmanshiel | gear_oil_inlet_temp_c     |   3.46 |    5.13 |
| penmanshiel | gear_oil_temp_c           |   1.43 |    2.35 |
| penmanshiel | gen_bearing_front_temp_c  |   3.49 |    3.58 |
| penmanshiel | gen_bearing_rear_temp_c   |   2.12 |    2.37 |
| penmanshiel | main_bearing_front_temp_c |   1.51 |    2.31 |
| penmanshiel | main_bearing_rear_temp_c  |   1.34 |    2.28 |
| penmanshiel | rotor_bearing_temp_c      |   1.49 |    0.97 |

### Table E. Cross-farm MAE on Penmanshiel healthy rows Feb-Jun (deg C), Kelmarsh-trained model, mean over turbines

| target                    |   mae_raw |   mae_after_offset |   calib_offset |   in_farm_lgbm_mae |
|:--------------------------|----------:|-------------------:|---------------:|-------------------:|
| gear_oil_inlet_temp_c     |      4.73 |               5.08 |           1.31 |               3.46 |
| gear_oil_temp_c           |      4.02 |               3.36 |           3.42 |               1.43 |
| gen_bearing_front_temp_c  |      4.7  |               3.59 |           3.55 |               3.49 |
| gen_bearing_rear_temp_c   |      2.01 |               1.95 |           0.21 |               2.12 |
| main_bearing_front_temp_c |      5.02 |               3.26 |          -2.69 |               1.51 |
| main_bearing_rear_temp_c  |      6.2  |               3.09 |          -5.7  |               1.34 |
| rotor_bearing_temp_c      |      1.88 |               1.17 |           1.71 |               1.49 |

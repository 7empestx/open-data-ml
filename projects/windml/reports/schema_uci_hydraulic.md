# Schema: UCI hydraulic systems test rig: per-cycle features (mean/std/min/max per sensor) + condition labels

- Rows: 2,205
- Columns: 74
- Overall missing cells: 0.00%
- Raw data: 2,205 load cycles of 60 s each; one text file per sensor, one row per cycle. No wall-clock time.
- Labels (profile.txt): cooler 3/20/100 %, valve 100/90/80/73 %, pump leakage 0/1/2, accumulator 130/115/100/90 bar, stable flag 0/1.
- Label distribution: cooler_condition_pct: {3: 732, 20: 732, 100: 741}; valve_condition_pct: {73: 360, 80: 360, 90: 360, 100: 1125}; pump_leakage: {0: 1221, 1: 492, 2: 492}; accumulator_pressure_bar: {90: 808, 100: 399, 115: 399, 130: 599}; stable_flag: {0: 1449, 1: 756}

| column | dtype | unit | missing % | min | max |
|---|---|---|---|---|---|
| cycle | int64 |  | 0.00 | 0 | 2204 |
| PS1_mean | float64 |  | 0.00 | 155.4 | 180.9 |
| PS1_std | float64 |  | 0.00 | 13.93 | 22.14 |
| PS1_min | float64 |  | 0.00 | 133.1 | 146.7 |
| PS1_max | float64 |  | 0.00 | 189.6 | 191.9 |
| PS2_mean | float64 |  | 0.00 | 104.4 | 131.6 |
| PS2_std | float64 |  | 0.00 | 45.2 | 59.55 |
| PS2_min | float64 |  | 0.00 | 0 | 0 |
| PS2_max | float64 |  | 0.00 | 155 | 167.8 |
| PS3_mean | float64 |  | 0.00 | 0.8403 | 2.023 |
| PS3_std | float64 |  | 0.00 | 0.7284 | 1.049 |
| PS3_min | float64 |  | 0.00 | 0 | 0 |
| PS3_max | float64 |  | 0.00 | 9.109 | 18.83 |
| PS4_mean | float64 |  | 0.00 | 0 | 10.21 |
| PS4_std | float64 |  | 0.00 | 0 | 4.529 |
| PS4_min | float64 |  | 0.00 | 0 | 10.13 |
| PS4_max | float64 |  | 0.00 | 0 | 10.27 |
| PS5_mean | float64 |  | 0.00 | 8.366 | 9.979 |
| PS5_std | float64 |  | 0.00 | 0.02014 | 0.08815 |
| PS5_min | float64 |  | 0.00 | 8.318 | 9.915 |
| ... 54 more columns omitted | | | | | |

## Raw sensor files

- PS1: 6000 values/cycle (100 Hz x 60 s), unit bar, NaN 0, min 133.1, max 191.9
- PS2: 6000 values/cycle (100 Hz x 60 s), unit bar, NaN 0, min 0, max 167.8
- PS3: 6000 values/cycle (100 Hz x 60 s), unit bar, NaN 0, min 0, max 18.83
- PS4: 6000 values/cycle (100 Hz x 60 s), unit bar, NaN 0, min 0, max 10.27
- PS5: 6000 values/cycle (100 Hz x 60 s), unit bar, NaN 0, min 8.318, max 10.04
- PS6: 6000 values/cycle (100 Hz x 60 s), unit bar, NaN 0, min 8.268, max 9.91
- EPS1: 6000 values/cycle (100 Hz x 60 s), unit W, NaN 0, min 2098, max 2995
- FS1: 600 values/cycle (10 Hz x 60 s), unit l/min, NaN 0, min 0, max 20.48
- FS2: 600 values/cycle (10 Hz x 60 s), unit l/min, NaN 0, min 8.764, max 10.45
- TS1: 60 values/cycle (1 Hz x 60 s), unit degC, NaN 0, min 34.98, max 58.21
- TS2: 60 values/cycle (1 Hz x 60 s), unit degC, NaN 0, min 40.71, max 62.18
- TS3: 60 values/cycle (1 Hz x 60 s), unit degC, NaN 0, min 38.15, max 59.54
- TS4: 60 values/cycle (1 Hz x 60 s), unit degC, NaN 0, min 30.36, max 53.15
- VS1: 60 values/cycle (1 Hz x 60 s), unit mm/s, NaN 0, min 0.483, max 2.546
- CE: 60 values/cycle (1 Hz x 60 s), unit %, NaN 0, min 17.04, max 48.78
- CP: 60 values/cycle (1 Hz x 60 s), unit kW, NaN 0, min 1.016, max 2.909
- SE: 60 values/cycle (1 Hz x 60 s), unit %, NaN 0, min 0, max 100.6

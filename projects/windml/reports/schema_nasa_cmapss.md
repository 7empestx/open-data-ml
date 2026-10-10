# Schema: NASA C-MAPSS (FD001-FD004, train+test)

- Rows: 265,256
- Columns: 29
- Entities (subset): 4 -> FD001: 33,727, FD002: 87,750, FD003: 41,316, FD004: 102,463
- Overall missing cells: 0.00%
- No wall-clock time: one row per engine operating cycle. Simulated data.
- Sensor names/units follow Saxena et al. 2008 (Damage Propagation Modeling.pdf); file columns are unlabeled.
- rul added: train = max cycle - cycle; test = RUL_FDxxx value + (last cycle - cycle).
- Per subset: FD001/test: 13,096 rows, 100 units, max cycle 303; FD001/train: 20,631 rows, 100 units, max cycle 362; FD002/test: 33,991 rows, 259 units, max cycle 367; FD002/train: 53,759 rows, 260 units, max cycle 378; FD003/test: 16,596 rows, 100 units, max cycle 475; FD003/train: 24,720 rows, 100 units, max cycle 525; FD004/test: 41,214 rows, 248 units, max cycle 486; FD004/train: 61,249 rows, 249 units, max cycle 543

| column | dtype | unit | missing % | min | max |
|---|---|---|---|---|---|
| subset | str |  | 0.00 |  |  |
| split | str |  | 0.00 |  |  |
| unit | int64 |  | 0.00 | 1 | 260 |
| cycle | int64 |  | 0.00 | 1 | 543 |
| op_setting_1 | float64 |  | 0.00 | -0.0087 | 42.01 |
| op_setting_2 | float64 |  | 0.00 | -0.0006 | 0.842 |
| op_setting_3 | float64 |  | 0.00 | 60 | 100 |
| s1 | float64 | T2 fan inlet temp (degR) | 0.00 | 445 | 518.7 |
| s2 | float64 | T24 LPC outlet temp (degR) | 0.00 | 535.4 | 645.1 |
| s3 | float64 | T30 HPC outlet temp (degR) | 0.00 | 1241 | 1617 |
| s4 | float64 | T50 LPT outlet temp (degR) | 0.00 | 1024 | 1441 |
| s5 | float64 | P2 fan inlet pressure (psia) | 0.00 | 3.91 | 14.62 |
| s6 | float64 | P15 bypass duct pressure (psia) | 0.00 | 5.66 | 21.61 |
| s7 | float64 | P30 HPC outlet pressure (psia) | 0.00 | 136.1 | 570.8 |
| s8 | float64 | Nf fan speed (rpm) | 0.00 | 1915 | 2389 |
| s9 | float64 | Nc core speed (rpm) | 0.00 | 7985 | 9245 |
| s10 | float64 | epr engine pressure ratio | 0.00 | 0.93 | 1.32 |
| s11 | float64 | Ps30 HPC static pressure (psia) | 0.00 | 36.03 | 48.53 |
| s12 | float64 | phi fuel flow/Ps30 (pps/psi) | 0.00 | 128.3 | 537.5 |
| s13 | float64 | NRf corrected fan speed (rpm) | 0.00 | 2028 | 2390 |
| s14 | float64 | NRc corrected core speed (rpm) | 0.00 | 7846 | 8294 |
| s15 | float64 | BPR bypass ratio | 0.00 | 8.156 | 11.07 |
| s16 | float64 | farB burner fuel-air ratio | 0.00 | 0.02 | 0.03 |
| s17 | int64 | htBleed bleed enthalpy | 0.00 | 302 | 400 |
| s18 | int64 | Nf_dmd demanded fan speed (rpm) | 0.00 | 1915 | 2388 |
| s19 | float64 | PCNfR_dmd demanded corrected fan speed (rpm) | 0.00 | 84.93 | 100 |
| s20 | float64 | W31 HPT coolant bleed (lbm/s) | 0.00 | 10.16 | 39.89 |
| s21 | float64 | W32 LPT coolant bleed (lbm/s) | 0.00 | 6.011 | 23.95 |
| rul | int64 | cycles | 0.00 | 0 | 553 |

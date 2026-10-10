# Schema: MetroPT-3 metro train air compressor (APU)

- Rows: 1,516,948
- Columns: 17
- Time span: 2020-02-01 00:00:00 to 2020-09-01 03:59:50
- Sampling interval: median 0 days 00:00:10, most common 0 days 00:00:10, share at mode 88.2%, max gap 2 days 00:01:58
- Overall missing cells: 0.00%
- Duplicate timestamps removed: 0. Time zone not stated (Porto operator, likely local Portugal time); kept naive.
- UCI text mentions both 1 Hz and 0.1 Hz; the file is 0.1 Hz (10 s spacing for 88% of rows) with gaps up to 2 days. Digital signals are 0/1.
- in_failure added from the 4 air-leak failure reports on the UCI page (Apr 18, May 29-30, Jun 5-7, Jul 15 2020): 29954 rows.

| column | dtype | unit | missing % | min | max |
|---|---|---|---|---|---|
| timestamp | datetime64[us] |  | 0.00 | 2020-02-01 00:00:00 | 2020-09-01 03:59:50 |
| TP2 | float64 | bar | 0.00 | -0.032 | 10.68 |
| TP3 | float64 | bar | 0.00 | 0.73 | 10.3 |
| H1 | float64 | bar | 0.00 | -0.036 | 10.29 |
| DV_pressure | float64 | bar | 0.00 | -0.032 | 9.844 |
| Reservoirs | float64 | bar | 0.00 | 0.712 | 10.3 |
| Oil_temperature | float64 | degC | 0.00 | 15.4 | 89.05 |
| Motor_current | float64 | A | 0.00 | 0.02 | 9.295 |
| COMP | float64 |  | 0.00 | 0 | 1 |
| DV_eletric | float64 |  | 0.00 | 0 | 1 |
| Towers | float64 |  | 0.00 | 0 | 1 |
| MPG | float64 |  | 0.00 | 0 | 1 |
| LPS | float64 |  | 0.00 | 0 | 1 |
| Pressure_switch | float64 |  | 0.00 | 0 | 1 |
| Oil_level | float64 |  | 0.00 | 0 | 1 |
| Caudal_impulses | float64 |  | 0.00 | 0 | 1 |
| in_failure | bool |  | 0.00 | False | True |

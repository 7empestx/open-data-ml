# Schema: NREL PVDAQ system 10 (NREL CIS-1, Golden CO, 1.12 kW), 2008

- Rows: 35,130
- Columns: 17
- Time span: 2008-01-01 07:00:00+00:00 to 2009-01-01 06:45:00+00:00
- Sampling interval: median 0 days 00:15:00, most common 0 days 00:15:00, share at mode 100.0%, max gap 0 days 01:00:00
- Overall missing cells: 6.69%
- Source: 366 daily CSVs; -99999 is a missing-value sentinel (replaced with NaN). Sentinel counts: inverter_temp 35122, poa_irradiance 4805
- Time zone: measured_on is local STANDARD time (no DST). Verified: irradiance-weighted daily centroid stays at about 12:00 in every month and DST-change days have 96 rows. Converted to UTC with +7 h.
- Units: PVDAQ documentation convention (W, V, A, degC, W/m2); not stated in the CSV header. inverter_temp is entirely missing in 2008.
- Night-time small negative irradiance/power values are sensor offsets, kept as is.

| column | dtype | unit | missing % | min | max |
|---|---|---|---|---|---|
| measured_on | datetime64[us] |  | 0.00 | 2008-01-01 00:00:00 | 2008-12-31 23:45:00 |
| ac_current | float64 | A | 0.00 | -0.0037 | 9.283 |
| ac_power | float64 | W | 0.00 | -2.891 | 1164 |
| ac_voltage | float64 | V | 0.00 | -0.0015 | 128.6 |
| ambient_temp | float64 | degC | 0.00 | -24.29 | 36.8 |
| das_battery_voltage | float64 | V | 0.00 | 13.01 | 14.49 |
| das_temp | float64 | degC | 0.00 | -24.3 | 45.75 |
| dc_pos_current | float64 | A | 0.00 | -0.026 | 5.494 |
| dc_pos_voltage | float64 | V | 0.00 | -0.9571 | 316.6 |
| dc_power | float64 | W | 0.00 | -5.362 | 1234 |
| inverter_temp | float64 | degC | 99.98 | -7.928 | 4.138 |
| module_temp_1 | float64 | degC | 0.00 | -27.1 | 62.66 |
| module_temp_2 | float64 | degC | 0.00 | -25.21 | 66.22 |
| module_temp_3 | float64 | degC | 0.00 | -26.86 | 67.28 |
| poa_irradiance | float64 | W/m2 | 13.68 | -975.2 | 1335 |
| system_id | int64 |  | 0.00 | 10 | 10 |
| timestamp_utc | datetime64[us, UTC] |  | 0.00 | 2008-01-01 07:00:00+00:00 | 2009-01-01 06:45:00+00:00 |

# Schema: Kelmarsh 2022 SCADA (raw Greenbyte export, all columns)

- Rows: 315,360
- Columns: 304
- Entities (turbine_id): 6 -> KEL01: 52,560, KEL02: 52,560, KEL03: 52,560, KEL04: 52,560, KEL05: 52,560, KEL06: 52,560
- Time span: 2022-01-01 00:00:00+00:00 to 2022-12-31 23:50:00+00:00
- Sampling interval: median 0 days 00:10:00, most common 0 days 00:10:00, share at mode 100.0%, max gap 0 days 00:10:00
- Overall missing cells: 2.93%
- Header: turbine type Senvion MM92, 'Time zone: UTC', '2022-01-01 00:00:00 - 2023-01-01 00:00:00 (365 days)'
- Timestamps are UTC and mark the START of each 10-minute averaging interval (file runs 00:00 to 23:50 of the last day for an interval ending 00:00 next day).
- Units are taken from the column names; signal descriptions in *_WT_dataSignalMapping.* next to the raw data.
- Missing/erroneous values are exported as NaN by Greenbyte.
- Cleaned output: data/processed/kelmarsh_scada_10min.parquet (29 key columns + qc flags); labels in kelmarsh_scada_labeled.parquet

| column | dtype | unit | missing % | min | max |
|---|---|---|---|---|---|
| turbine_id | str |  | 0.00 |  |  |
| timestamp | datetime64[us, UTC] |  | 0.00 | 2022-01-01 00:00:00+00:00 | 2022-12-31 23:50:00+00:00 |
| Wind speed (m/s) | float64 | m/s | 0.43 | 0 | 24.15 |
| Wind speed, Standard deviation (m/s) | float64 | m/s | 0.42 | 0 | 8.656 |
| Wind speed, Minimum (m/s) | float64 | m/s | 0.42 | -15 | 17.77 |
| Wind speed, Maximum (m/s) | float64 | m/s | 0.42 | 0 | 31.93 |
| Long Term Wind (m/s) | float64 | m/s | 0.00 | 5.26 | 7.21 |
| Wind speed Sensor 1 (m/s) | float64 | m/s | 0.92 | 0 | 24.55 |
| Wind speed Sensor 1, Standard deviation (m/s) | float64 | m/s | 0.92 | 0 | 7.613 |
| Wind speed Sensor 1, Minimum (m/s) | float64 | m/s | 2.45 | -11.44 | 18.35 |
| Wind speed Sensor 1, Maximum (m/s) | float64 | m/s | 0.92 | 0 | 33.38 |
| Wind speed Sensor 2 (m/s) | float64 | m/s | 0.42 | -15 | 23.35 |
| Wind speed Sensor 2, Standard deviation (m/s) | float64 | m/s | 0.42 | 0 | 15.16 |
| Wind speed Sensor 2, Minimum (m/s) | float64 | m/s | 0.42 | -15 | 17.76 |
| Wind speed Sensor 2, Maximum (m/s) | float64 | m/s | 0.42 | -15 | 31.86 |
| Density adjusted wind speed (m/s) | float64 | m/s | 0.51 | 0 | 24.14 |
| Wind direction (°) | float64 | ° | 0.42 | 0.001602 | 360 |
| Nacelle position (°) | float64 | ° | 0.42 | 0.002195 | 360 |
| Wind direction, Standard deviation (°) | float64 | ° | 0.42 | 0 | 113.8 |
| Wind direction, Minimum (°) | float64 | ° | 0.42 | 4.864e-05 | 352.2 |
| Wind direction, Maximum (°) | float64 | ° | 0.42 | 5.462 | 360 |
| Nacelle position, Standard deviation (°) | float64 | ° | 0.42 | 0 | 96.28 |
| Nacelle position, Minimum (°) | float64 | ° | 0.42 | 0 | 360 |
| Nacelle position, Maximum (°) | float64 | ° | 0.42 | 0.1164 | 360 |
| Vane position 1+2 (°) | float64 | ° | 0.50 | -177.9 | 177.9 |
| Vane position 1+2, Max (°) | float64 | ° | 0.50 | -176.3 | 180 |
| Vane position 1+2, Min (°) | float64 | ° | 0.50 | -180 | 176 |
| Vane position 1+2, StdDev (°) | float64 | ° | 0.50 | 0 | 177.3 |
| Energy Export (kWh) | float64 | kWh | 0.25 | 0 | 412 |
| Energy Export counter (kWh) | float64 | kWh | 15.37 | 2.527e+07 | 4.09e+07 |
| Energy Import (kWh) | float64 | kWh | 0.17 | 0 | 3 |
| Energy Import counter (kWh) | float64 | kWh | 93.43 | 1.029e+04 | 2.917e+04 |
| Lost Production (Contractual) (kWh) | float64 | kWh | 0.01 | 0 | 341.8 |
| Lost Production (Time-based IEC B.2.2) (kWh) | float64 | kWh | 0.01 | 0 | 342.9 |
| Lost Production (Time-based IEC B.2.3) (kWh) | float64 | kWh | 0.57 | 0 | 342.9 |
| Lost Production (Time-based IEC B.2.4) (kWh) | float64 | kWh | 0.30 | 0 | 342.9 |
| Lost Production (Time-based IEC B.3.2) (kWh) | float64 | kWh | 1.27 | 0 | 342.8 |
| Lost Production (Production-based IEC B.2.2) (kWh) | float64 | kWh | 0.57 | 0 | 342.9 |
| Lost Production (Production-based IEC B.2.3) (kWh) | float64 | kWh | 13.72 | 0 | 342.9 |
| Lost Production (Production-based IEC B.3.2) (kWh) | float64 | kWh | 1.27 | 0 | 342.8 |
| Energy Budget - Default (kWh) | float64 | kWh | 0.00 | 33.66 | 140.5 |
| Energy Theoretical (kWh) | float64 | kWh | 0.00 | 0 | 342.9 |
| Lost Production to Downtime (kWh) | float64 | kWh | 0.06 | 0 | 342.9 |
| Lost Production to Performance (kWh) | float64 | kWh | 0.06 | -170.8 | 255.7 |
| Lost Production Total (kWh) | float64 | kWh | 0.00 | -170.8 | 342.9 |
| Lost Production to Curtailment (Total) (kWh) | float64 | kWh | 0.00 | 0 | 159.6 |
| Lost Production to Curtailment (Grid) (kWh) | int64 | kWh | 0.00 | 0 | 0 |
| Lost Production to Curtailment (Noise) (kWh) | int64 | kWh | 0.00 | 0 | 0 |
| Lost Production to Curtailment (Shadow) (kWh) | int64 | kWh | 0.00 | 0 | 0 |
| Lost Production to Curtailment (Bats) (kWh) | int64 | kWh | 0.00 | 0 | 0 |
| Lost Production to Curtailment (Birds) (kWh) | int64 | kWh | 0.00 | 0 | 0 |
| Lost Production to Curtailment (Ice) (kWh) | int64 | kWh | 0.00 | 0 | 0 |
| Lost Production to Curtailment (Sector Management) (kWh) | int64 | kWh | 0.00 | 0 | 0 |
| Lost Production to Curtailment (Technical) (kWh) | float64 | kWh | 0.00 | 0 | 159.6 |
| Lost Production to Curtailment (Marketing) (kWh) | int64 | kWh | 0.00 | 0 | 0 |
| Lost Production to Curtailment (Boat Action) (kWh) | int64 | kWh | 0.00 | 0 | 0 |
| Compensated Lost Production (kWh) | int64 | kWh | 0.00 | 0 | 0 |
| Virtual Production (kWh) | float64 | kWh | 0.00 | 0 | 412 |
| Lost Production to Curtailment (Grid Constraint) (kWh) | int64 | kWh | 0.00 | 0 | 0 |
| Lost Production to Downtime and Curtailment Total (kWh) | float64 | kWh | 0.00 | 0 | 342.9 |
| Lost Production (Contractual Global) (kWh) | float64 | kWh | 0.06 | 0 | 342.9 |
| Lost Production (Contractual Custom) (kWh) | float64 | kWh | 0.42 | 0 | 341.7 |
| Power (kW) | float64 | kW | 0.42 | -17.78 | 2083 |
| Potential power default PC (kW) | float64 | kW | 0.43 | 0 | 2050 |
| Power, Standard deviation (kW) | float64 | kW | 0.42 | 0 | 1042 |
| Power, Minimum (kW) | float64 | kW | 0.42 | -98.64 | 2051 |
| Power, Maximum (kW) | float64 | kW | 0.42 | -13.52 | 2255 |
| Potential power learned PC (kW) | float64 | kW | 0.43 | 0 | 2057 |
| Potential power reference turbines (kW) | float64 | kW | 0.46 | 0 | 2062 |
| Cascading potential power (kW) | float64 | kW | 0.00 | 0 | 2057 |
| Cascading potential power for performance (kW) | float64 | kW | 0.00 | 0 | 2057 |
| Potential power met mast anemometer (kW) | float64 | kW | 100.00 |  |  |
| Potential power primary reference turbines (kW) | float64 | kW | 1.69 | 0 | 2067 |
| Potential power secondary reference turbines (kW) | float64 | kW | 1.14 | 0 | 2065 |
| Turbine Power setpoint (kW) | float64 | kW | 0.50 | 205 | 2060 |
| Potential power estimated (kW) | float64 | kW | 99.58 | -3.113 | 1722 |
| Potential power MPC (kW) | float64 | kW | 0.43 | 0 | 2050 |
| Potential power met mast anemometer MPC (kW) | float64 | kW | 100.00 |  |  |
| Potential Power Energy Budget (kW) | float64 | kW | 0.00 | 202 | 842.7 |
| Turbine Power setpoint, Max (kW) | float64 | kW | 0.50 | 205 | 2060 |
| Turbine Power setpoint, Min (kW) | float64 | kW | 0.50 | 205 | 2060 |
| Turbine Power setpoint, StdDev (kW) | float64 | kW | 0.50 | 0 | 831.5 |
| Available Capacity for Production (kW) | float64 | kW | 0.06 | 0 | 2050 |
| Available Capacity for Production (Planned) (kW) | int64 | kW | 0.00 | 2050 | 2050 |
| Manufacturer Potential Power (SCADA) (kW) | float64 | kW | 100.00 |  |  |
| Power factor (cosphi) | float64 | cosphi | 0.42 | -1 | 1 |
| Power factor (cosphi), Max | float64 |  | 0.42 | -1 | 1 |
| Power factor (cosphi), Min | float64 |  | 0.42 | -1 | 1 |
| Power factor (cosphi), Standard deviation | float64 |  | 0.42 | 0 | 1 |
| Reactive power (kvar) | float64 | kvar | 0.42 | -747.2 | 5.049 |
| Reactive power, Max (kvar) | float64 | kvar | 0.42 | -663 | 252.6 |
| Reactive power, Min (kvar) | float64 | kvar | 0.42 | -842.3 | 0.05335 |
| Reactive power, Standard deviation (kvar) | float64 | kvar | 0.42 | 0 | 326 |
| Front bearing temperature (°C) | float64 | °C | 0.50 | 7.2 | 83.13 |
| Rear bearing temperature (°C) | float64 | °C | 0.50 | 7.702 | 81.46 |
| Stator temperature 1 (°C) | float64 | °C | 0.42 | 5.202 | 101 |
| Nacelle ambient temperature (°C) | float64 | °C | 0.50 | -4.8 | 39.33 |
| Nacelle temperature (°C) | float64 | °C | 0.50 | -0.6 | 42.7 |
| Transformer temperature (°C) | float64 | °C | 0.50 | -273.2 | 116 |
| Gear oil inlet temperature (°C) | float64 | °C | 0.42 | 3.365 | 60.22 |
| Generator bearing rear temperature (°C) | float64 | °C | 0.42 | 1.9 | 324.1 |
| Generator bearing front temperature (°C) | float64 | °C | 0.42 | 5 | 66.16 |
| Gear oil temperature (°C) | float64 | °C | 0.42 | 8.6 | 65 |
| Temp. top box (°C) | float64 | °C | 0.42 | 6.7 | 46.2 |
| Hub temperature (°C) | float64 | °C | 0.42 | 0 | 41.95 |
| Ambient temperature (converter) (°C) | float64 | °C | 0.42 | -113.3 | 46.49 |
| Rotor bearing temp (°C) | float64 | °C | 0.42 | 0.105 | 48.63 |
| Transformer cell temperature (°C) | float64 | °C | 0.50 | -273.2 | 46.79 |
| Front bearing temperature, Max (°C) | float64 | °C | 0.50 | 7.2 | 84.3 |
| Front bearing temperature, Min (°C) | float64 | °C | 0.50 | 7.2 | 82.5 |
| Front bearing temperature, Standard deviation (°C) | float64 | °C | 0.50 | 0 | 15.22 |
| Rear bearing temperature, Max (°C) | float64 | °C | 0.50 | 7.75 | 81.9 |
| Rear bearing temperature, Min (°C) | float64 | °C | 0.50 | 7.7 | 81.1 |
| Rear bearing temperature, Standard deviation (°C) | float64 | °C | 0.50 | 0 | 13.01 |
| Temperature motor axis 1 (°C) | float64 | °C | 0.42 | 0 | 85.28 |
| Temperature motor axis 2 (°C) | float64 | °C | 0.42 | 0 | 95.52 |
| Temperature motor axis 3 (°C) | float64 | °C | 0.42 | 0 | 84.95 |
| CPU temperature (°C) | float64 | °C | 0.42 | 29.5 | 78 |
| Nacelle temperature, Max (°C) | float64 | °C | 0.50 | -0.6 | 42.9 |
| Nacelle temperature, Min (°C) | float64 | °C | 0.50 | -0.6 | 42.6 |
| Generator bearing front temperature, Max (°C) | float64 | °C | 0.42 | 5 | 66.7 |
| Generator bearing front temperature, Min (°C) | float64 | °C | 0.42 | 5 | 65.35 |
| Generator bearing rear temperature, Max (°C) | float64 | °C | 0.42 | 1.9 | 324.1 |
| Generator bearing rear temperature, Min (°C) | float64 | °C | 0.42 | 1.9 | 324.1 |
| Generator bearing front temperature, Std (°C) | float64 | °C | 0.42 | 0 | 3.292 |
| Generator bearing rear temperature, Std (°C) | float64 | °C | 0.42 | 0 | 150.5 |
| Nacelle temperature, Standard deviation (°C) | float64 | °C | 0.50 | 0 | 3.788 |
| Gear oil temperature, Max (°C) | float64 | °C | 0.42 | 8.6 | 65.3 |
| Gear oil temperature, Min (°C) | float64 | °C | 0.42 | 8.6 | 64.65 |
| Gear oil temperature, Standard deviation (°C) | float64 | °C | 0.42 | 0 | 3.674 |
| Hub temperature, min (°C) | float64 | °C | 0.42 | -40 | 41.48 |
| Hub temperature, max (°C) | float64 | °C | 0.42 | 0 | 42 |
| Hub temperature, standard deviation (°C) | float64 | °C | 0.42 | 0 | 12.53 |
| Ambient temperature (converter), Max (°C) | float64 | °C | 0.42 | -2.4 | 46.65 |
| Ambient temperature (converter), Min (°C) | float64 | °C | 0.42 | -2.55 | 46.25 |
| Ambient temperature (converter), StdDev (°C) | float64 | °C | 0.42 | 0 | 4.663 |
| Gear oil inlet temperature, Max (°C) | float64 | °C | 0.42 | 4.1 | 60.8 |
| Gear oil inlet temperature, Min (°C) | float64 | °C | 0.42 | 2.1 | 60.05 |
| Gear oil inlet temperature, StdDev (°C) | float64 | °C | 0.42 | 0 | 16.82 |
| Nacelle ambient temperature, Max (°C) | float64 | °C | 0.50 | -4.8 | 39.6 |
| Nacelle ambient temperature, Min (°C) | float64 | °C | 0.50 | -4.8 | 39 |
| Nacelle ambient temperature, StdDev (°C) | float64 | °C | 0.50 | 0 | 1.793 |
| Rotor bearing temp, Max (°C) | float64 | °C | 0.42 | 0.2 | 48.7 |
| Rotor bearing temp, Min (°C) | float64 | °C | 0.42 | 0.1 | 48.6 |
| Rotor bearing temp, StdDev (°C) | float64 | °C | 0.42 | 0 | 0.5097 |
| CPU temperature, Max (°C) | float64 | °C | 0.42 | 30 | 78 |
| CPU temperature, Min (°C) | float64 | °C | 0.42 | 27 | 78 |
| CPU temperature, StdDev (°C) | float64 | °C | 0.42 | 0 | 2.743 |
| Transformer cell temperature, Max (°C) | float64 | °C | 0.50 | -273.2 | 48.75 |
| Transformer cell temperature, Min (°C) | float64 | °C | 0.50 | -273.2 | 46.5 |
| Transformer cell temperature, StdDev (°C) | float64 | °C | 0.50 | 0 | 145.7 |
| Transformer temperature, Max (°C) | float64 | °C | 0.50 | -273.2 | 116.8 |
| Transformer temperature, Min (°C) | float64 | °C | 0.50 | -273.2 | 115.6 |
| Transformer temperature, StdDev (°C) | float64 | °C | 0.50 | 0 | 155.6 |
| Stator temperature 1, Max (°C) | float64 | °C | 0.42 | 5.25 | 101.7 |
| Stator temperature 1, Min (°C) | float64 | °C | 0.42 | 5.2 | 100.4 |
| Stator temperature 1, StdDev (°C) | float64 | °C | 0.42 | 0 | 3.323 |
| Temp. top box, Max (°C) | float64 | °C | 0.42 | 6.7 | 46.2 |
| Temp. top box, Min (°C) | float64 | °C | 0.42 | 6.7 | 46.2 |
| Temp. top box, StdDev (°C) | float64 | °C | 0.42 | 0 | 2.295 |
| Temperature motor axis 1, Max (°C) | float64 | °C | 0.42 | 0 | 88 |
| Temperature motor axis 1, Min (°C) | float64 | °C | 0.42 | -40 | 85 |
| Temperature motor axis 1, StdDev (°C) | float64 | °C | 0.42 | 0 | 15.6 |
| Temperature motor axis 2, Max (°C) | float64 | °C | 0.42 | 0 | 215 |
| Temperature motor axis 2, Min (°C) | float64 | °C | 0.42 | -40 | 86.8 |
| Temperature motor axis 2, StdDev (°C) | float64 | °C | 0.42 | 0 | 93.72 |
| Temperature motor axis 3, Max (°C) | float64 | °C | 0.42 | 0 | 88 |
| Temperature motor axis 3, Min (°C) | float64 | °C | 0.42 | -40 | 84.01 |
| Temperature motor axis 3, StdDev (°C) | float64 | °C | 0.42 | 0 | 15.6 |
| Voltage L1 / U (V) | float64 | V | 0.50 | 0 | 414.6 |
| Voltage L2 / V (V) | float64 | V | 0.50 | 0 | 414.7 |
| Voltage L3 / W (V) | float64 | V | 0.50 | 0 | 414.8 |
| Grid voltage (V) | float64 | V | 0.42 | 0 | 711.7 |
| Grid voltage, Max (V) | float64 | V | 0.42 | 0 | 718.8 |
| Grid voltage, Min (V) | float64 | V | 0.42 | 0 | 711.2 |
| Grid voltage, Standard deviation (V) | float64 | V | 0.42 | 0 | 203.3 |
| Voltage L1 / U, Min (V) | float64 | V | 0.50 | 0 | 413.5 |
| Voltage L1 / U, Max (V) | float64 | V | 0.50 | 0 | 417.1 |
| Voltage L1 / U, Standard deviation (V) | float64 | V | 0.50 | 0 | 202.8 |
| Voltage L2 / V, Min (V) | float64 | V | 0.50 | 0 | 413.6 |
| Voltage L2 / V, Max (V) | float64 | V | 0.50 | 0 | 419.6 |
| Voltage L2 / V, Standard deviation (V) | float64 | V | 0.50 | 0 | 203.4 |
| Voltage L3 / W, Min (V) | float64 | V | 0.50 | 0 | 413.7 |
| Voltage L3 / W, Max (V) | float64 | V | 0.50 | 0 | 417.2 |
| Voltage L3 / W, Standard deviation (V) | float64 | V | 0.50 | 0 | 203.6 |
| Current L1 / U (A) | float64 | A | 0.50 | 0 | 1831 |
| Current L2 / V (A) | float64 | A | 0.50 | 0 | 1828 |
| Current L3 / W (A) | float64 | A | 0.50 | 0 | 1824 |
| Grid current (A) | float64 | A | 0.42 | 0 | 1825 |
| Motor current axis 1 (A) | float64 | A | 0.42 | -0.4902 | 8.409 |
| Motor current axis 2 (A) | float64 | A | 0.42 | -0.4902 | 7.76 |
| Motor current axis 3 (A) | float64 | A | 0.42 | -0.4902 | 7.232 |
| Current L1 / U, min (A) | float64 | A | 0.50 | 0 | 1805 |
| Current L1 / U, max (A) | float64 | A | 0.50 | 0 | 1970 |
| Current L1 / U, StdDev (A) | float64 | A | 0.50 | 0 | 888.7 |
| Current L2 / V, max (A) | float64 | A | 0.50 | 0 | 1970 |
| Current L3 / W, max (A) | float64 | A | 0.50 | 0 | 1967 |
| Current L2 / V, min (A) | float64 | A | 0.50 | 0 | 1799 |
| Current L2 / V, StdDev (A) | float64 | A | 0.50 | 0 | 889.8 |
| Current L3 / W, min (A) | float64 | A | 0.50 | 0 | 1798 |
| Current L3 / W, StdDev (A) | float64 | A | 0.50 | 0 | 888.6 |
| Grid current, Max (A) | float64 | A | 0.42 | 0 | 1954 |
| Grid current, Min (A) | float64 | A | 0.42 | 0 | 1794 |
| Grid current, StdDev (A) | float64 | A | 0.42 | 0 | 891.8 |
| Motor current axis 1, Max (A) | float64 | A | 0.42 | -0.4902 | 24 |
| Motor current axis 1, Min (A) | float64 | A | 0.42 | -0.4902 | 4.034 |
| Motor current axis 1, StdDev (A) | float64 | A | 0.42 | 0 | 6.458 |
| Motor current axis 2, Max (A) | float64 | A | 0.42 | -0.4902 | 55.65 |
| Motor current axis 2, Min (A) | float64 | A | 0.42 | -0.4902 | 5.118 |
| Motor current axis 2, StdDev (A) | float64 | A | 0.42 | 0 | 12.19 |
| Motor current axis 3, Max (A) | float64 | A | 0.42 | -0.4902 | 28.37 |
| Motor current axis 3, Min (A) | float64 | A | 0.42 | -0.4902 | 5 |
| Motor current axis 3, StdDev (A) | float64 | A | 0.42 | 0 | 6.549 |
| Rotor speed (RPM) | float64 | RPM | 0.42 | 0 | 15.36 |
| Generator RPM (RPM) | float64 | RPM | 0.42 | -571.6 | 1825 |
| Gearbox speed (RPM) | float64 | RPM | 0.42 | 0 | 1828 |
| Generator RPM, Max (RPM) | float64 | RPM | 0.42 | -571.6 | 1974 |
| Generator RPM, Min (RPM) | float64 | RPM | 0.42 | -591 | 1798 |
| Generator RPM, Standard deviation (RPM) | float64 | RPM | 0.42 | 0 | 913.1 |
| Rotor speed, Max (RPM) | float64 | RPM | 0.42 | 0 | 20.29 |
| Rotor speed, Min (RPM) | float64 | RPM | 0.42 | 0 | 15.16 |
| Rotor speed, Standard deviation (RPM) | float64 | RPM | 0.42 | 0 | 7.465 |
| Gearbox speed, Max (RPM) | float64 | RPM | 0.42 | 0 | 2823 |
| Gearbox speed, Min (RPM) | float64 | RPM | 0.42 | 0 | 1802 |
| Gearbox speed, StdDev (RPM) | float64 | RPM | 0.42 | 0 | 1099 |
| Capacity factor | float64 |  | 0.25 | 0 | 1.206 |
| Data Availability | int64 |  | 0.00 | 0 | 1 |
| Time-based Contractual Avail. | float64 |  | 0.01 | 0 | 1 |
| Time-based IEC B.2.2 (Users View) | float64 | Users View | 0.01 | 0 | 1 |
| Time-based IEC B.2.3 (Users View) | float64 | Users View | 0.01 | 0 | 1 |
| Time-based IEC B.2.4 (Users View) | float64 | Users View | 0.30 | 0 | 1 |
| Time-based IEC B.3.2 (Manufacturers View) | float64 | Manufacturers View | 1.27 | 0 | 1 |
| Production-based IEC B.2.2 (Users View) | float64 | Users View | 0.82 | 0 | 1 |
| Production-based IEC B.2.3 (Users View) | float64 | Users View | 13.98 | 0 | 1 |
| Production-based IEC B.3.2 (Manufacturers View) | float64 | Manufacturers View | 1.53 | 0 | 1 |
| Time-based System Avail. | float64 |  | 0.06 | 0 | 1 |
| Production-based System Avail. | float64 |  | 0.31 | 0 | 1 |
| Production-based Contractual Avail. | float64 |  | 0.26 | 0 | 1 |
| Time-based System Avail. (Planned) | int64 | Planned | 0.00 | 1 | 1 |
| Production-based System Avail. (virtual) | float64 | virtual | 0.06 | 0 | 1 |
| Time-based Contractual Avail. (Global) | float64 | Global | 0.06 | 0 | 1 |
| Time-based Contractual Avail. (Custom) | float64 | Custom | 0.42 | 0 | 1 |
| Production-based Contractual Avail. (Global) | float64 | Global | 0.06 | 0 | 1 |
| Production-based Contractual Avail. (Custom) | float64 | Custom | 0.42 | 0 | 1 |
| Reactive Energy Export (kvarh) | float64 | kvarh | 1.29 | 0 | 1 |
| Reactive Energy Export counter (kvarh) | float64 | kvarh | 97.28 | 8.284e+04 | 1.494e+05 |
| Reactive Energy Import (kvarh) | float64 | kvarh | 0.25 | 0 | 134 |
| Reactive Energy Import counter (kvarh) | float64 | kvarh | 17.23 | 9.639e+06 | 1.41e+07 |
| Blade angle (pitch position) A (°) | float64 | ° | 0.50 | -172.9 | 92.89 |
| Blade angle (pitch position) B (°) | float64 | ° | 0.50 | -159.1 | 92.83 |
| Blade angle (pitch position) C (°) | float64 | ° | 0.50 | -198.5 | 211.7 |
| Yaw bearing angle (°) | float64 | ° | 0.50 | 0.01368 | 360 |
| Blade angle (pitch position) A, Max (°) | float64 | ° | 0.50 | -89.36 | 92.93 |
| Blade angle (pitch position) A, Min (°) | float64 | ° | 0.50 | -243 | 92.89 |
| Blade angle (pitch position) A, Standard deviation (°) | float64 | ° | 0.50 | 0 | 91.8 |
| Blade angle (pitch position) B, Max (°) | float64 | ° | 0.50 | -111 | 92.92 |
| Blade angle (pitch position) B, Min (°) | float64 | ° | 0.50 | -226.6 | 92.83 |
| Blade angle (pitch position) B, Standard deviation (°) | float64 | ° | 0.50 | 0 | 119 |
| Blade angle (pitch position) C, Max (°) | float64 | ° | 0.50 | -198.5 | 302.7 |
| Blade angle (pitch position) C, Min (°) | float64 | ° | 0.50 | -315.7 | 105.1 |
| Blade angle (pitch position) C, Standard deviation (°) | float64 | ° | 0.50 | 0 | 293.1 |
| Yaw bearing angle, Max (°) | float64 | ° | 0.50 | 0.1164 | 360 |
| Yaw bearing angle, Min (°) | float64 | ° | 0.50 | 0 | 360 |
| Yaw bearing angle, StdDev (°) | float64 | ° | 0.50 | 0 | 96.28 |
| Gear oil inlet pressure (bar) | float64 | bar | 0.42 | -3.027 | 427.1 |
| Gear oil pump pressure (bar) | float64 | bar | 0.42 | 0.1 | 1238 |
| Gear oil inlet pressure, Max (bar) | float64 | bar | 0.42 | -2.002 | 524.5 |
| Gear oil inlet pressure, Min (bar) | float64 | bar | 0.42 | -5.402 | 405.1 |
| Gear oil inlet pressure, StdDev (bar) | float64 | bar | 0.42 | 0 | 224.8 |
| Gear oil pump pressure, Max (bar) | float64 | bar | 0.42 | 0.1 | 1382 |
| Gear oil pump pressure, Min (bar) | float64 | bar | 0.42 | -3.412 | 1224 |
| Gear oil pump pressure, StdDev (bar) | float64 | bar | 0.42 | 0 | 585.7 |
| Grid frequency (Hz) | float64 | Hz | 0.42 | 0 | 50.2 |
| Grid frequency, Max (Hz) | float64 | Hz | 0.42 | 0 | 50.34 |
| Grid frequency, Min (Hz) | float64 | Hz | 0.42 | 0 | 50.13 |
| Grid frequency, Standard deviation (Hz) | float64 | Hz | 0.42 | 0 | 24.97 |
| Equivalent Full Load Hours (s) | float64 | s | 0.25 | 0 | 723.5 |
| Equivalent Full Load Hours counter (s) | float64 | s | 100.00 |  |  |
| Production Factor | float64 |  | 0.00 | 0 | 24.03 |
| Performance Index | float64 |  | 5.77 | 0 | 24.03 |
| Investment Performance Ratio | float64 |  | 0.00 | -0.04182 | 9.4 |
| Operating Performance Ratio | float64 |  | 14.20 | -0.3432 | 19.53 |
| Apparent power (kVA) | float64 | kVA | 0.42 | 0 | 2189 |
| Apparent power, Max (kVA) | float64 | kVA | 0.42 | 0 | 2364 |
| Apparent power, Min (kVA) | float64 | kVA | 0.42 | 0 | 2143 |
| Apparent power, StdDev (kVA) | float64 | kVA | 0.42 | 0 | 1081 |
| Cable windings from calibration point | float64 |  | 0.50 | -1.777 | 1.848 |
| Metal particle count | int64 |  | 0.00 | 0 | 8 |
| Metal particle count counter | float64 |  | 0.50 | 436 | 727 |
| Cable windings from calibration point, Max | float64 |  | 0.50 | -1.777 | 1.848 |
| Cable windings from calibration point, Min | float64 |  | 0.50 | -1.777 | 1.848 |
| Cable windings from calibration point, StdDev | float64 |  | 0.50 | 0 | 0.267 |
| Drive train acceleration (mm/ss) | float64 | mm/ss | 0.44 | 0.18 | 51.34 |
| Tower Acceleration X (mm/ss) | float64 | mm/ss | 0.50 | 1.935 | 280.4 |
| Tower Acceleration y (mm/ss) | float64 | mm/ss | 0.50 | 1.942 | 268.3 |
| Tower Acceleration X, Min (mm/ss) | float64 | mm/ss | 0.50 | 0.09885 | 159.2 |
| Tower Acceleration X, Max (mm/ss) | float64 | mm/ss | 0.50 | 3.866 | 989.3 |
| Tower Acceleration Y, Min (mm/ss) | float64 | mm/ss | 0.50 | 0.09546 | 86.13 |
| Tower Acceleration Y, Max (mm/ss) | float64 | mm/ss | 0.50 | 3.629 | 666 |
| Drive train acceleration, Max (mm/ss) | float64 | mm/ss | 0.44 | 0.25 | 51.34 |
| Drive train acceleration, Min (mm/ss) | float64 | mm/ss | 0.44 | 0.05 | 51.34 |
| Drive train acceleration, StdDev (mm/ss) | float64 | mm/ss | 0.44 | 0 | 2.301 |
| Tower Acceleration X, StdDev (mm/ss) | float64 | mm/ss | 0.50 | 0 | 262 |
| Tower Acceleration Y, StdDev (mm/ss) | float64 | mm/ss | 0.50 | 0 | 186.9 |

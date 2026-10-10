# Schema: Penmanshiel H1 2021 (WT11-15) SCADA (raw Greenbyte export, all columns)

- Rows: 130,320
- Columns: 301
- Entities (turbine_id): 5 -> PEN11: 26,064, PEN12: 26,064, PEN13: 26,064, PEN14: 26,064, PEN15: 26,064
- Time span: 2021-01-01 00:00:00+00:00 to 2021-06-30 23:50:00+00:00
- Sampling interval: median 0 days 00:10:00, most common 0 days 00:10:00, share at mode 100.0%, max gap 0 days 00:10:00
- Overall missing cells: 4.87%
- Header: turbine type Senvion MM82, 'Time zone: UTC', '2021-01-01 00:00:00 - 2021-07-01 00:00:00 (181 days)'
- Timestamps are UTC and mark the START of each 10-minute averaging interval (file runs 00:00 to 23:50 of the last day for an interval ending 00:00 next day).
- Units are taken from the column names; signal descriptions in *_WT_dataSignalMapping.* next to the raw data.
- Missing/erroneous values are exported as NaN by Greenbyte.
- Cleaned output: data/processed/penmanshiel_scada_10min.parquet (29 key columns + qc flags); labels in penmanshiel_scada_labeled.parquet

| column | dtype | unit | missing % | min | max |
|---|---|---|---|---|---|
| turbine_id | str |  | 0.00 |  |  |
| timestamp | datetime64[us, UTC] |  | 0.00 | 2021-01-01 00:00:00+00:00 | 2021-06-30 23:50:00+00:00 |
| Wind speed (m/s) | float64 | m/s | 0.81 | 0 | 26.49 |
| Wind speed, Standard deviation (m/s) | float64 | m/s | 1.07 | 0 | 7.859 |
| Wind speed, Minimum (m/s) | float64 | m/s | 1.07 | -17.65 | 21.83 |
| Wind speed, Maximum (m/s) | float64 | m/s | 1.07 | 0 | 34.28 |
| Long Term Wind (m/s) | float64 | m/s | 0.00 | 5.8 | 8.7 |
| Wind speed Sensor 1 (m/s) | float64 | m/s | 0.90 | 0 | 26.19 |
| Wind speed Sensor 1, Standard deviation (m/s) | float64 | m/s | 1.15 | 0 | 8.676 |
| Wind speed Sensor 1, Minimum (m/s) | float64 | m/s | 2.46 | -11.47 | 20.9 |
| Wind speed Sensor 1, Maximum (m/s) | float64 | m/s | 1.15 | 0 | 32.05 |
| Wind speed Sensor 2 (m/s) | float64 | m/s | 0.40 | -9.279 | 26.02 |
| Wind speed Sensor 2, Standard deviation (m/s) | float64 | m/s | 0.66 | 0 | 12.11 |
| Wind speed Sensor 2, Minimum (m/s) | float64 | m/s | 0.66 | -17.65 | 20.68 |
| Wind speed Sensor 2, Maximum (m/s) | float64 | m/s | 0.66 | 0.225 | 35.31 |
| Density adjusted wind speed (m/s) | float64 | m/s | 1.37 | 0 | 26.35 |
| Wind direction (°) | float64 | ° | 0.40 | 0.004118 | 360 |
| Nacelle position (°) | float64 | ° | 0.40 | 0.01744 | 360 |
| Wind direction, Standard deviation (°) | float64 | ° | 0.66 | 0 | 318.8 |
| Wind direction, Minimum (°) | float64 | ° | 0.66 | 0 | 353.1 |
| Wind direction, Maximum (°) | float64 | ° | 0.66 | 9.545 | 360 |
| Nacelle position, Standard deviation (°) | float64 | ° | 0.66 | 0 | 94.64 |
| Nacelle position, Minimum (°) | float64 | ° | 0.66 | 0.006474 | 360 |
| Nacelle position, Maximum (°) | float64 | ° | 0.66 | 0.1679 | 360 |
| Vane position 1+2 (°) | float64 | ° | 0.95 | -174.6 | 175.4 |
| Vane position 1+2, Max (°) | float64 | ° | 0.95 | -172.3 | 180 |
| Vane position 1+2, Min (°) | float64 | ° | 0.95 | -180 | 171.3 |
| Vane position 1+2, StdDev (°) | float64 | ° | 0.95 | 0 | 176.9 |
| Energy Export (kWh) | float64 | kWh | 0.11 | 0 | 413 |
| Energy Export counter (kWh) | float64 | kWh | 18.05 | 2.485e+07 | 3.034e+07 |
| Energy Import (kWh) | float64 | kWh | 5.22 | 0 | 3 |
| Energy Import counter (kWh) | float64 | kWh | 92.64 | 7582 | 1.992e+04 |
| Lost Production (Contractual) (kWh) | float64 | kWh | 0.07 | 0 | 341.2 |
| Lost Production (Time-based IEC B.2.2) (kWh) | float64 | kWh | 0.40 | 0 | 342.9 |
| Lost Production (Time-based IEC B.2.3) (kWh) | float64 | kWh | 0.40 | 0 | 342.9 |
| Lost Production (Time-based IEC B.2.4) (kWh) | float64 | kWh | 0.40 | 0 | 342.9 |
| Lost Production (Time-based IEC B.3.2) (kWh) | float64 | kWh | 0.54 | 0 | 341.2 |
| Lost Production (Production-based IEC B.2.2) (kWh) | float64 | kWh | 0.40 | 0 | 342.9 |
| Lost Production (Production-based IEC B.2.3) (kWh) | float64 | kWh | 22.22 | 0 | 342.9 |
| Lost Production (Production-based IEC B.3.2) (kWh) | float64 | kWh | 0.54 | 0 | 341.2 |
| Energy Budget - Default (kWh) | float64 | kWh | 0.00 | 21.98 | 156.4 |
| Energy Theoretical (kWh) | float64 | kWh | 0.00 | 0 | 342.9 |
| Lost Production to Downtime (kWh) | float64 | kWh | 0.10 | 0 | 342.9 |
| Lost Production to Performance (kWh) | float64 | kWh | 0.81 | -344 | 270 |
| Lost Production Total (kWh) | float64 | kWh | 0.00 | -344 | 342.9 |
| Lost Production to Curtailment (Total) (kWh) | int64 | kWh | 0.00 | 0 | 0 |
| Lost Production to Curtailment (Grid) (kWh) | int64 | kWh | 0.00 | 0 | 0 |
| Lost Production to Curtailment (Noise) (kWh) | int64 | kWh | 0.00 | 0 | 0 |
| Lost Production to Curtailment (Shadow) (kWh) | int64 | kWh | 0.00 | 0 | 0 |
| Lost Production to Curtailment (Bats) (kWh) | int64 | kWh | 0.00 | 0 | 0 |
| Lost Production to Curtailment (Birds) (kWh) | int64 | kWh | 0.00 | 0 | 0 |
| Lost Production to Curtailment (Ice) (kWh) | int64 | kWh | 0.00 | 0 | 0 |
| Lost Production to Curtailment (Sector Management) (kWh) | int64 | kWh | 0.00 | 0 | 0 |
| Lost Production to Curtailment (Technical) (kWh) | int64 | kWh | 0.00 | 0 | 0 |
| Lost Production to Curtailment (Marketing) (kWh) | int64 | kWh | 0.00 | 0 | 0 |
| Lost Production to Curtailment (Boat Action) (kWh) | int64 | kWh | 0.00 | 0 | 0 |
| Compensated Lost Production (kWh) | int64 | kWh | 0.00 | 0 | 0 |
| Virtual Production (kWh) | float64 | kWh | 0.00 | 0 | 413 |
| Lost Production to Curtailment (Grid Constraint) (kWh) | int64 | kWh | 0.00 | 0 | 0 |
| Lost Production to Downtime and Curtailment Total (kWh) | float64 | kWh | 0.00 | 0 | 342.9 |
| Lost Production (Contractual Global) (kWh) | float64 | kWh | 100.00 |  |  |
| Lost Production (Contractual Custom) (kWh) | float64 | kWh | 100.00 |  |  |
| Power (kW) | float64 | kW | 0.40 | -17.87 | 2072 |
| Potential power default PC (kW) | float64 | kW | 0.81 | 0 | 2050 |
| Power, Standard deviation (kW) | float64 | kW | 0.66 | 0 | 1027 |
| Power, Minimum (kW) | float64 | kW | 0.66 | -122.4 | 2047 |
| Power, Maximum (kW) | float64 | kW | 0.66 | -11.79 | 2205 |
| Potential power learned PC (kW) | float64 | kW | 0.81 | 0 | 2057 |
| Potential power reference turbines (kW) | float64 | kW | 0.06 | 0 | 2060 |
| Cascading potential power (kW) | float64 | kW | 0.00 | 0 | 2057 |
| Cascading potential power for performance (kW) | float64 | kW | 0.81 | 0 | 2057 |
| Potential power met mast anemometer (kW) | float64 | kW | 100.00 |  |  |
| Potential power primary reference turbines (kW) | float64 | kW | 0.38 | 0 | 2066 |
| Potential power secondary reference turbines (kW) | float64 | kW | 0.27 | 0 | 2064 |
| Turbine Power setpoint (kW) | float64 | kW | 0.95 | 205.8 | 2060 |
| Potential power estimated (kW) | float64 | kW | 99.60 | -0.8719 | 2050 |
| Potential power MPC (kW) | float64 | kW | 0.81 | 0 | 2050 |
| Potential power met mast anemometer MPC (kW) | float64 | kW | 100.00 |  |  |
| Turbine Power setpoint, Max (kW) | float64 | kW | 0.95 | 206 | 2060 |
| Turbine Power setpoint, Min (kW) | float64 | kW | 0.95 | 205 | 2060 |
| Turbine Power setpoint, StdDev (kW) | float64 | kW | 0.95 | 0 | 927 |
| Available Capacity for Production (kW) | float64 | kW | 0.10 | 0 | 2050 |
| Available Capacity for Production (Planned) (kW) | int64 | kW | 0.00 | 2050 | 2050 |
| APE-2 (kW) | float64 | kW | 0.10 | 0 | 2050 |
| Power factor (cosphi) | float64 | cosphi | 0.40 | -0.9999 | 1 |
| Power factor (cosphi), Max | float64 |  | 0.66 | -1 | 1 |
| Power factor (cosphi), Min | float64 |  | 0.66 | -1 | 1 |
| Power factor (cosphi), Standard deviation | float64 |  | 0.66 | 0 | 1 |
| Reactive power (kvar) | float64 | kvar | 0.40 | -794.7 | 468.4 |
| Reactive power, Max (kvar) | float64 | kvar | 0.66 | -787.2 | 599.6 |
| Reactive power, Min (kvar) | float64 | kvar | 0.66 | -841.2 | 435.8 |
| Reactive power, Standard deviation (kvar) | float64 | kvar | 0.66 | 0 | 399.9 |
| Front bearing temperature (°C) | float64 | °C | 0.96 | 6.603 | 75.4 |
| Rear bearing temperature (°C) | float64 | °C | 0.96 | 7.621 | 66.85 |
| Stator temperature 1 (°C) | float64 | °C | 0.40 | 7.397 | 94.55 |
| Nacelle ambient temperature (°C) | float64 | °C | 0.95 | -3.487 | 22.88 |
| Nacelle temperature (°C) | float64 | °C | 0.95 | 1.197 | 35.61 |
| Transformer temperature (°C) | float64 | °C | 0.95 | 8.057 | 109.4 |
| Gear oil inlet temperature (°C) | float64 | °C | 0.95 | 3.047 | 58.08 |
| Generator bearing rear temperature (°C) | float64 | °C | 0.40 | 7.012 | 72.1 |
| Generator bearing front temperature (°C) | float64 | °C | 0.40 | 6.4 | 75.47 |
| Gear oil temperature (°C) | float64 | °C | 0.96 | 10.01 | 59.97 |
| Temp. top box (°C) | float64 | °C | 0.40 | 9.463 | 33.1 |
| Hub temperature (°C) | float64 | °C | 0.40 | 5.964 | 27 |
| Ambient temperature (converter) (°C) | float64 | °C | 0.40 | -1.255 | 26 |
| Rotor bearing temp (°C) | float64 | °C | 0.40 | 4.347 | 38.61 |
| Transformer cell temperature (°C) | float64 | °C | 0.95 | -0.255 | 28.38 |
| Front bearing temperature, Max (°C) | float64 | °C | 0.96 | 6.65 | 76.05 |
| Front bearing temperature, Min (°C) | float64 | °C | 0.96 | 6.6 | 75.1 |
| Front bearing temperature, Standard deviation (°C) | float64 | °C | 0.96 | 0 | 8.584 |
| Rear bearing temperature, Max (°C) | float64 | °C | 0.96 | 7.7 | 67.4 |
| Rear bearing temperature, Min (°C) | float64 | °C | 0.96 | 7.5 | 66.7 |
| Rear bearing temperature, Standard deviation (°C) | float64 | °C | 0.96 | 0 | 7.8 |
| Temperature motor axis 1 (°C) | float64 | °C | 0.40 | 5.996 | 85.39 |
| Temperature motor axis 2 (°C) | float64 | °C | 0.40 | 6.593 | 83.49 |
| Temperature motor axis 3 (°C) | float64 | °C | 0.40 | 5.158 | 82.98 |
| CPU temperature (°C) | float64 | °C | 0.40 | 24.58 | 64.07 |
| Nacelle temperature, Max (°C) | float64 | °C | 0.95 | 1.2 | 35.7 |
| Nacelle temperature, Min (°C) | float64 | °C | 0.95 | 1 | 35.35 |
| Generator bearing front temperature, Max (°C) | float64 | °C | 0.66 | 6.4 | 76.15 |
| Generator bearing front temperature, Min (°C) | float64 | °C | 0.66 | 6.4 | 74.5 |
| Generator bearing rear temperature, Max (°C) | float64 | °C | 0.66 | 7.1 | 72.7 |
| Generator bearing rear temperature, Min (°C) | float64 | °C | 0.66 | 7 | 71.75 |
| Generator bearing front temperature, Std (°C) | float64 | °C | 0.66 | 0 | 6.595 |
| Generator bearing rear temperature, Std (°C) | float64 | °C | 0.66 | 0 | 5.842 |
| Nacelle temperature, Standard deviation (°C) | float64 | °C | 0.95 | 0 | 3.356 |
| Gear oil temperature, Max (°C) | float64 | °C | 0.96 | 10.2 | 60.5 |
| Gear oil temperature, Min (°C) | float64 | °C | 0.96 | 9.2 | 59.85 |
| Gear oil temperature, Standard deviation (°C) | float64 | °C | 0.96 | 0 | 3.457 |
| Hub temperature, min (°C) | float64 | °C | 0.66 | 5.2 | 27 |
| Hub temperature, max (°C) | float64 | °C | 0.66 | 6 | 27 |
| Hub temperature, standard deviation (°C) | float64 | °C | 0.66 | 0 | 0.849 |
| Ambient temperature (converter), Max (°C) | float64 | °C | 0.66 | -0.9 | 27.05 |
| Ambient temperature (converter), Min (°C) | float64 | °C | 0.66 | -1.65 | 25.65 |
| Ambient temperature (converter), StdDev (°C) | float64 | °C | 0.66 | 0 | 0.6996 |
| Gear oil inlet temperature, Max (°C) | float64 | °C | 0.95 | 3.1 | 58.6 |
| Gear oil inlet temperature, Min (°C) | float64 | °C | 0.95 | 2.7 | 58 |
| Gear oil inlet temperature, StdDev (°C) | float64 | °C | 0.95 | 0 | 14.61 |
| Nacelle ambient temperature, Max (°C) | float64 | °C | 0.95 | -3.45 | 23.25 |
| Nacelle ambient temperature, Min (°C) | float64 | °C | 0.95 | -3.6 | 22.6 |
| Nacelle ambient temperature, StdDev (°C) | float64 | °C | 0.95 | 0 | 1.635 |
| Rotor bearing temp, Max (°C) | float64 | °C | 0.66 | 4.5 | 38.8 |
| Rotor bearing temp, Min (°C) | float64 | °C | 0.66 | 4.3 | 38.5 |
| Rotor bearing temp, StdDev (°C) | float64 | °C | 0.66 | 0 | 0.7407 |
| CPU temperature, Max (°C) | float64 | °C | 0.66 | 28 | 65 |
| CPU temperature, Min (°C) | float64 | °C | 0.66 | 20 | 64 |
| CPU temperature, StdDev (°C) | float64 | °C | 0.66 | 0 | 3.348 |
| Transformer cell temperature, Max (°C) | float64 | °C | 0.95 | 0.1 | 29.3 |
| Transformer cell temperature, Min (°C) | float64 | °C | 0.95 | -0.6 | 27.75 |
| Transformer cell temperature, StdDev (°C) | float64 | °C | 0.95 | 0 | 2.661 |
| Transformer temperature, Max (°C) | float64 | °C | 0.95 | 8.3 | 110.2 |
| Transformer temperature, Min (°C) | float64 | °C | 0.95 | 7.85 | 108.7 |
| Transformer temperature, StdDev (°C) | float64 | °C | 0.95 | 0 | 2.191 |
| Stator temperature 1, Max (°C) | float64 | °C | 0.66 | 7.4 | 94.85 |
| Stator temperature 1, Min (°C) | float64 | °C | 0.66 | 7.3 | 94.35 |
| Stator temperature 1, StdDev (°C) | float64 | °C | 0.66 | 0 | 4.539 |
| Temp. top box, Max (°C) | float64 | °C | 0.66 | 9.5 | 33.1 |
| Temp. top box, Min (°C) | float64 | °C | 0.66 | 7.8 | 33.1 |
| Temp. top box, StdDev (°C) | float64 | °C | 0.66 | 0 | 2.316 |
| Temperature motor axis 1, Max (°C) | float64 | °C | 0.66 | 6 | 86 |
| Temperature motor axis 1, Min (°C) | float64 | °C | 0.66 | 5 | 85 |
| Temperature motor axis 1, StdDev (°C) | float64 | °C | 0.66 | 0 | 13.01 |
| Temperature motor axis 2, Max (°C) | float64 | °C | 0.66 | 7 | 84 |
| Temperature motor axis 2, Min (°C) | float64 | °C | 0.66 | 6 | 83 |
| Temperature motor axis 2, StdDev (°C) | float64 | °C | 0.66 | 0 | 13.2 |
| Temperature motor axis 3, Max (°C) | float64 | °C | 0.66 | 6 | 84 |
| Temperature motor axis 3, Min (°C) | float64 | °C | 0.66 | 5 | 82.33 |
| Temperature motor axis 3, StdDev (°C) | float64 | °C | 0.66 | 0 | 12.46 |
| Voltage L1 / U (V) | float64 | V | 0.95 | 167.1 | 415.2 |
| Voltage L2 / V (V) | float64 | V | 0.95 | 167.3 | 414.7 |
| Voltage L3 / W (V) | float64 | V | 0.95 | 166.4 | 414.6 |
| Grid voltage (V) | float64 | V | 0.40 | 166.9 | 716 |
| Grid voltage, Max (V) | float64 | V | 0.66 | 389.6 | 704 |
| Grid voltage, Min (V) | float64 | V | 0.66 | 0 | 703 |
| Grid voltage, Standard deviation (V) | float64 | V | 0.66 | 0 | 199.5 |
| Voltage L1 / U, Min (V) | float64 | V | 0.95 | 0 | 414.8 |
| Voltage L1 / U, Max (V) | float64 | V | 0.95 | 387.6 | 416.4 |
| Voltage L1 / U, Standard deviation (V) | float64 | V | 0.95 | 0 | 199.7 |
| Voltage L2 / V, Min (V) | float64 | V | 0.95 | 0 | 414.4 |
| Voltage L2 / V, Max (V) | float64 | V | 0.95 | 390.4 | 415.6 |
| Voltage L2 / V, Standard deviation (V) | float64 | V | 0.95 | 0 | 200 |
| Voltage L3 / W, Min (V) | float64 | V | 0.95 | 0 | 414.1 |
| Voltage L3 / W, Max (V) | float64 | V | 0.95 | 391.9 | 415.7 |
| Voltage L3 / W, Standard deviation (V) | float64 | V | 0.95 | 0 | 198.8 |
| Current L1 / U (A) | float64 | A | 0.95 | 0 | 1684 |
| Current L2 / V (A) | float64 | A | 0.95 | 0.1415 | 1692 |
| Current L3 / W (A) | float64 | A | 0.95 | 0.015 | 1682 |
| Grid current (A) | float64 | A | 0.40 | 0.455 | 1689 |
| Motor current axis 1 (A) | float64 | A | 0.40 | -0.01275 | 5.744 |
| Motor current axis 2 (A) | float64 | A | 0.40 | -0.4902 | 5.983 |
| Motor current axis 3 (A) | float64 | A | 0.40 | -0.4902 | 5.758 |
| Current L1 / U, min (A) | float64 | A | 0.95 | 0 | 1663 |
| Current L1 / U, max (A) | float64 | A | 0.95 | 0 | 1806 |
| Current L1 / U, StdDev (A) | float64 | A | 0.95 | 0 | 825.7 |
| Current L2 / V, max (A) | float64 | A | 0.95 | 0.65 | 1814 |
| Current L3 / W, max (A) | float64 | A | 0.95 | 0.155 | 1801 |
| Current L2 / V, min (A) | float64 | A | 0.95 | 0 | 1668 |
| Current L2 / V, StdDev (A) | float64 | A | 0.95 | 0 | 830.9 |
| Current L3 / W, min (A) | float64 | A | 0.95 | 0 | 1660 |
| Current L3 / W, StdDev (A) | float64 | A | 0.95 | 0 | 824.8 |
| Grid current, Max (A) | float64 | A | 0.66 | 0.8267 | 1810 |
| Grid current, Min (A) | float64 | A | 0.66 | 0 | 1664 |
| Grid current, StdDev (A) | float64 | A | 0.66 | 0 | 827.9 |
| Motor current axis 1, Max (A) | float64 | A | 0.66 | -1.192e-07 | 16.3 |
| Motor current axis 1, Min (A) | float64 | A | 0.66 | -0.1765 | 2.475 |
| Motor current axis 1, StdDev (A) | float64 | A | 0.66 | 0 | 4.002 |
| Motor current axis 2, Max (A) | float64 | A | 0.66 | -0.4902 | 16.51 |
| Motor current axis 2, Min (A) | float64 | A | 0.66 | -0.4902 | 4.206 |
| Motor current axis 2, StdDev (A) | float64 | A | 0.66 | 0 | 3.801 |
| Motor current axis 3, Max (A) | float64 | A | 0.66 | -0.4902 | 15.59 |
| Motor current axis 3, Min (A) | float64 | A | 0.66 | -0.4902 | 2.877 |
| Motor current axis 3, StdDev (A) | float64 | A | 0.66 | 0 | 3.97 |
| Rotor speed (RPM) | float64 | RPM | 0.40 | 0 | 17.25 |
| Generator RPM (RPM) | float64 | RPM | 0.40 | -575.3 | 1816 |
| Gearbox speed (RPM) | float64 | RPM | 0.96 | 0 | 1818 |
| Generator RPM, Max (RPM) | float64 | RPM | 0.66 | -575.2 | 1935 |
| Generator RPM, Min (RPM) | float64 | RPM | 0.66 | -577.2 | 1802 |
| Generator RPM, Standard deviation (RPM) | float64 | RPM | 0.66 | 0 | 887.4 |
| Rotor speed, Max (RPM) | float64 | RPM | 0.66 | 0 | 80.65 |
| Rotor speed, Min (RPM) | float64 | RPM | 0.66 | 0 | 17.09 |
| Rotor speed, Standard deviation (RPM) | float64 | RPM | 0.66 | 0 | 14.48 |
| Gearbox speed, Max (RPM) | float64 | RPM | 0.96 | 0 | 1934 |
| Gearbox speed, Min (RPM) | float64 | RPM | 0.96 | 0 | 1798 |
| Gearbox speed, StdDev (RPM) | float64 | RPM | 0.96 | 0 | 887.9 |
| Capacity factor | float64 |  | 0.11 | 0 | 1.209 |
| Data Availability | int64 |  | 0.00 | 0 | 1 |
| Time-based Contractual Avail. | float64 |  | 0.07 | 0 | 1 |
| Time-based IEC B.2.2 (Users View) | float64 | Users View | 0.40 | 0 | 1 |
| Time-based IEC B.2.3 (Users View) | float64 | Users View | 0.40 | 0 | 1 |
| Time-based IEC B.2.4 (Users View) | float64 | Users View | 0.40 | 0 | 1 |
| Time-based IEC B.3.2 (Manufacturers View) | float64 | Manufacturers View | 0.54 | 0 | 1 |
| Production-based IEC B.2.2 (Users View) | float64 | Users View | 0.51 | 0 | 1 |
| Production-based IEC B.2.3 (Users View) | float64 | Users View | 22.26 | 0 | 1 |
| Production-based IEC B.3.2 (Manufacturers View) | float64 | Manufacturers View | 0.65 | 0.0002429 | 1 |
| Time-based System Avail. | float64 |  | 0.10 | 0 | 1 |
| Production-based System Avail. | float64 |  | 0.21 | 0 | 1 |
| Production-based Contractual Avail. | float64 |  | 0.18 | 0 | 1 |
| Time-based System Avail. (Planned) | int64 | Planned | 0.00 | 1 | 1 |
| Production-based System Avail. (virtual) | float64 | virtual | 0.10 | 0 | 1 |
| Time-based Contractual Avail. (Global) | float64 | Global | 100.00 |  |  |
| Time-based Contractual Avail. (Custom) | float64 | Custom | 100.00 |  |  |
| Production-based Contractual Avail. (Global) | float64 | Global | 100.00 |  |  |
| Production-based Contractual Avail. (Custom) | float64 | Custom | 100.00 |  |  |
| Reactive Energy Export (kvarh) | float64 | kvarh | 2.77 | 0 | 95 |
| Reactive Energy Export counter (kvarh) | float64 | kvarh | 81.24 | 1.418e+05 | 4.268e+05 |
| Reactive Energy Import (kvarh) | float64 | kvarh | 0.14 | 0 | 157 |
| Reactive Energy Import counter (kvarh) | float64 | kvarh | 33.34 | 3.02e+06 | 4.562e+06 |
| Blade angle (pitch position) A (°) | float64 | ° | 0.96 | -18.97 | 93.06 |
| Blade angle (pitch position) B (°) | float64 | ° | 0.96 | -17.23 | 138.8 |
| Blade angle (pitch position) C (°) | float64 | ° | 0.96 | -17.31 | 101 |
| Yaw bearing angle (°) | float64 | ° | 0.95 | 0.006817 | 360 |
| Blade angle (pitch position) A, Max (°) | float64 | ° | 0.96 | -0.08 | 93.09 |
| Blade angle (pitch position) A, Min (°) | float64 | ° | 0.96 | -219.4 | 93.06 |
| Blade angle (pitch position) A, Standard deviation (°) | float64 | ° | 0.96 | 0 | 107.5 |
| Blade angle (pitch position) B, Max (°) | float64 | ° | 0.96 | -0.08 | 138.8 |
| Blade angle (pitch position) B, Min (°) | float64 | ° | 0.96 | -211.2 | 138.8 |
| Blade angle (pitch position) B, Standard deviation (°) | float64 | ° | 0.96 | 0 | 111.7 |
| Blade angle (pitch position) C, Max (°) | float64 | ° | 0.96 | -0.08 | 107.2 |
| Blade angle (pitch position) C, Min (°) | float64 | ° | 0.96 | -228.1 | 97.55 |
| Blade angle (pitch position) C, Standard deviation (°) | float64 | ° | 0.96 | 0 | 118.8 |
| Yaw bearing angle, Max (°) | float64 | ° | 0.95 | 0.1679 | 360 |
| Yaw bearing angle, Min (°) | float64 | ° | 0.95 | 0.00401 | 360 |
| Yaw bearing angle, StdDev (°) | float64 | ° | 0.95 | 0 | 94.59 |
| Gear oil inlet pressure (bar) | float64 | bar | 0.40 | -2.648 | 374 |
| Gear oil pump pressure (bar) | float64 | bar | 0.40 | 0.5275 | 1145 |
| Gear oil inlet pressure, Max (bar) | float64 | bar | 0.66 | -1.849 | 518.4 |
| Gear oil inlet pressure, Min (bar) | float64 | bar | 0.66 | -5.676 | 367.1 |
| Gear oil inlet pressure, StdDev (bar) | float64 | bar | 0.66 | 0 | 184.1 |
| Gear oil pump pressure, Max (bar) | float64 | bar | 0.66 | 0.62 | 1427 |
| Gear oil pump pressure, Min (bar) | float64 | bar | 0.66 | -0.2258 | 1133 |
| Gear oil pump pressure, StdDev (bar) | float64 | bar | 0.66 | 0 | 602.4 |
| Grid frequency (Hz) | float64 | Hz | 0.40 | 20.56 | 50.18 |
| Grid frequency, Max (Hz) | float64 | Hz | 0.66 | 49.88 | 50.35 |
| Grid frequency, Min (Hz) | float64 | Hz | 0.66 | 0 | 50.17 |
| Grid frequency, Standard deviation (Hz) | float64 | Hz | 0.66 | 0 | 24.57 |
| Equivalent Full Load Hours (s) | float64 | s | 0.11 | 0 | 725.3 |
| Equivalent Full Load Hours counter (s) | float64 | s | 100.00 |  |  |
| Production Factor | float64 |  | 0.81 | 0 | 2.341 |
| Performance Index | float64 |  | 3.04 | 0 | 2.341 |
| Apparent power (kVA) | float64 | kVA | 0.40 | 0.005335 | 2084 |
| Apparent power, Max (kVA) | float64 | kVA | 0.66 | 0.04268 | 2214 |
| Apparent power, Min (kVA) | float64 | kVA | 0.66 | 0 | 2059 |
| Apparent power, StdDev (kVA) | float64 | kVA | 0.66 | 0 | 1027 |
| Cable windings from calibration point | float64 |  | 0.95 | -1.933 | 1.878 |
| Metal particle count | float64 |  | 0.00 | 0 | 16 |
| Metal particle count counter | float64 |  | 0.95 | 638 | 3070 |
| Cable windings from calibration point, Max | float64 |  | 0.95 | -1.933 | 2.006 |
| Cable windings from calibration point, Min | float64 |  | 0.95 | -1.933 | 1.808 |
| Cable windings from calibration point, StdDev | float64 |  | 0.95 | 0 | 0.2625 |
| Drive train acceleration (mm/ss) | float64 | mm/ss | 0.42 | 0.32 | 23.49 |
| Tower Acceleration X (mm/ss) | float64 | mm/ss | 0.95 | 2.696 | 176.5 |
| Tower Acceleration y (mm/ss) | float64 | mm/ss | 0.95 | 1.63 | 190.7 |
| Tower Acceleration X, Min (mm/ss) | float64 | mm/ss | 0.95 | 0.3335 | 82.54 |
| Tower Acceleration X, Max (mm/ss) | float64 | mm/ss | 0.95 | 3.099 | 770.8 |
| Tower Acceleration Y, Min (mm/ss) | float64 | mm/ss | 0.95 | 0.05397 | 66.34 |
| Tower Acceleration Y, Max (mm/ss) | float64 | mm/ss | 0.95 | 1.979 | 812.6 |
| Drive train acceleration, Max (mm/ss) | float64 | mm/ss | 0.68 | 0.47 | 23.49 |
| Drive train acceleration, Min (mm/ss) | float64 | mm/ss | 0.68 | 0.12 | 23.49 |
| Drive train acceleration, StdDev (mm/ss) | float64 | mm/ss | 0.68 | 0 | 0.9856 |
| Tower Acceleration X, StdDev (mm/ss) | float64 | mm/ss | 0.95 | 0 | 135.5 |
| Tower Acceleration Y, StdDev (mm/ss) | float64 | mm/ss | 0.95 | 0 | 143.3 |

# Wind SCADA cleaning report

Inputs: Kelmarsh 2022 (6 x Senvion MM92, 2,050 kW) and Penmanshiel 2021-01-01 to 2021-07-01 (turbines 11-15, Senvion MM82, 2,050 kW). Code: src/windml/clean_wind.py, run with scripts/run_wind_clean.py.

## Rules

- Timezone: every Greenbyte header says 'Time zone: UTC'; timestamps stored as tz-aware UTC.
- Timestamp convention: interval START (file covers 00:00 to 23:50 for an interval ending 00:00 next day). To align with event logs, a 10-minute row t covers [t, t+10 min).
- Dedupe on timestamp, snap to a regular 10-minute grid per turbine (no duplicates or off-grid stamps were found).
- Gap flags: row_in_source, row_empty (no power and no wind speed), gap_steps (length of the empty run).
- Physical limits (value set to NaN, qc bit 4): power -100 to 1.15 x rated; wind speed 0 to 50 m/s; rotor 0 to 30 rpm; generator -10 to 2,500 rpm; pitch -10 to 100 deg; temperatures -40 to 150 C; angles 0 to 360.
- Frozen sensor: identical value for 6 h or more (36 steps) on wind speed and temperature channels, set to NaN (qc bit 4).
- Short gaps up to 30 min (3 steps) linearly interpolated (qc bit 1); angles interpolated on sin/cos. Longer gaps left NaN (qc bit 2). Energy and lost-production counters are never interpolated.
- 29 key columns kept: power, wind speed (nacelle + sensors 1 and 2), ambient and nacelle temp, rotor and generator speed, gear oil temp / inlet temp / inlet pressure, main (axle) bearing front/rear, rotor bearing, generator bearing front/rear, converter inlet temp, pitch A/B/C, nacelle position, yaw bearing angle, wind direction, power setpoint, available capacity, data availability, energy export, lost production (curtailment total, downtime).
- Not available in this export: a gearbox bearing temperature (only gear oil temperatures) and a time-based availability flag (use available_capacity_kw, data_availability, lost_prod_downtime_kwh and the stop labels instead).

## Per-turbine results

| turbine | rows | empty rows | gaps > 30 min | longest gap (h) | invalid or frozen values removed |
|---|---|---|---|---|---|
| KEL01 | 52,560 | 550 | 7 | 48.8 | wind_speed_2_ms 19, generator_speed_rpm 3, rotor_bearing_temp_c 40 (frozen 40), converter_inlet_temp_c 1, pitch_a_deg 1, pitch_b_deg 3, pitch_c_deg 5 |
| KEL02 | 52,560 | 72 | 4 | 5.0 | wind_speed_2_ms 2, generator_speed_rpm 5, gen_bearing_front_temp_c 79 (frozen 79), gen_bearing_rear_temp_c 134 |
| KEL03 | 52,560 | 112 | 5 | 5.3 | generator_speed_rpm 4 |
| KEL04 | 52,560 | 233 | 5 | 25.5 | generator_speed_rpm 4, rotor_bearing_temp_c 83 (frozen 83), gen_bearing_front_temp_c 133 (frozen 133), gen_bearing_rear_temp_c 36 (frozen 36) |
| KEL05 | 52,560 | 111 | 5 | 5.7 | wind_speed_2_ms 5, generator_speed_rpm 6, rotor_bearing_temp_c 39 (frozen 39), gen_bearing_front_temp_c 56 (frozen 56), gen_bearing_rear_temp_c 48 (frozen 48), pitch_c_deg 6 |
| KEL06 | 52,560 | 236 | 6 | 15.8 | wind_speed_2_ms 25, generator_speed_rpm 1, rotor_bearing_temp_c 36 (frozen 36), pitch_c_deg 1013 |
| PEN11 | 26,064 | 418 | 3 | 44.8 | generator_speed_rpm 8, pitch_a_deg 1, pitch_b_deg 1 |
| PEN12 | 26,064 | 19 | 1 | 3.0 | none |
| PEN13 | 26,064 | 19 | 1 | 3.0 | wind_speed_2_ms 56, pitch_a_deg 1, pitch_c_deg 1 |
| PEN14 | 26,064 | 19 | 1 | 3.0 | pitch_c_deg 1 |
| PEN15 | 26,064 | 48 | 3 | 3.7 | pitch_b_deg 3 |

## Data-quality findings

- Coverage is good: about 0.4% of power values remain missing after cleaning; only 0.01% needed interpolation. Longest outages: KEL01 48.8 h, PEN11 44.8 h, KEL04 25.5 h.
- Gear oil inlet pressure is labeled 'bar' but ranges 0 to about 400, so the unit or scale is wrong (likely 0.01 bar or a raw count). Kept, but don't trust the absolute values.
- Negative 10-minute average generator speed (down to -575 rpm) appears in a few rows per turbine: removed.
- KEL06 pitch C reported impossible angles (to -187 deg) for 1,013 rows, from 12 to 19 May 2022. That's exactly the major 'Pitch angle deviation' stop, so the sensor fault and the event log agree.
- Frozen bearing temperature channels on KEL01, KEL02, KEL04, KEL05, KEL06 (rotor bearing and generator bearing, 36 to 133 rows each).
- Wind speed sensor 2 has a -15 m/s fill value on several turbines (removed); PEN13 has 56 invalid rows on sensor 2.
- Converter inlet temperature at -113 C on one KEL row (removed).
- Penmanshiel status logs start on 2020-12-21, before the SCADA window; events outside the grid are kept in the events table but don't label rows.
- On 19 July 2022 (UK heatwave), four Kelmarsh turbines stopped on converter inlet over-temperature (code 3151). These count as converter major faults under the rules, but the cause is weather; consider excluding them from early-warning targets.

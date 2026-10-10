---
title: Cleaning notes and data problems
description: How the windml SCADA data was cleaned and what problems turned up.
---

## Cleaning steps

- **Time.** Every source file header says UTC, so timestamps are stored as UTC. A row at time t covers the 10 minutes from t to t + 10 min.
- **Regular grid.** Rows were deduplicated and snapped to a regular 10-minute grid per turbine. No duplicate or off-grid timestamps were found.
- **Gap flags.** Each row records whether it was in the source, whether it was empty, and how long the surrounding gap is.
- **Physical limits.** Out-of-range values are set to missing. Examples: wind speed outside 0 to 50 m/s, temperatures outside -40 to 150 C, pitch outside -10 to 100 deg.
- **Frozen sensors.** An identical value for 6 hours or more on wind speed and temperature channels is set to missing.
- **Short gaps.** Gaps of 30 minutes or less are filled by linear interpolation (angles via sine and cosine). Longer gaps are left missing. Energy and lost-production counters are never interpolated.
- **Columns.** 29 key columns kept out of 303 in the source export: power, wind speeds, temperatures (ambient, nacelle, gear oil, bearings, converter), speeds, pitch angles, yaw, availability, and energy counters.

## Coverage after cleaning

- About 0.4% of power values are still missing.
- Only 0.01% needed interpolation.
- Longest outages: KEL01 48.8 h, PEN11 44.8 h, KEL04 25.5 h.

## Data problems found

- **Gear oil inlet pressure unit.** Labeled "bar" but ranges from 0 to about 400, so the unit or scale is wrong. The column is kept, but its absolute values shouldn't be trusted.
- **Negative generator speeds.** A few rows per turbine have negative 10-minute average generator speeds, down to -575 rpm. These were removed.
- **Frozen bearing sensors.** Rotor-bearing and generator-bearing temperatures froze on KEL01, KEL02, KEL04, KEL05, and KEL06, with 36 to 133 rows each set to missing.
- **No gearbox bearing temperature.** The export has gear oil temperatures only, and no time-based availability flag.
- **Pitch sensor matches a logged fault.** KEL06 pitch C reported impossible angles, down to -187 deg, for 1,013 rows from 12 to 19 May 2022. That matches the logged "Pitch angle deviation" stop over the same dates, so the sensor data and the event log agree.
- **Heatwave stops.** On 19 July 2022, during the UK heatwave, four Kelmarsh turbines stopped on converter inlet over-temperature (code 3151). The labeling rules count these as major converter faults, but the cause was weather.
- **Smaller issues.** Wind speed sensor 2 has a -15 m/s fill value on several turbines (removed). PEN13 has 56 invalid sensor-2 rows. One Kelmarsh row shows a converter inlet temperature of -113 C (removed). Penmanshiel status logs start on 2020-12-21, before the SCADA window, so those early events don't label any rows.

## Per-turbine summary

| Turbine | Rows | Empty rows | Gaps over 30 min | Longest gap (h) |
|---|---|---|---|---|
| KEL01 | 52,560 | 550 | 7 | 48.8 |
| KEL02 | 52,560 | 72 | 4 | 5.0 |
| KEL03 | 52,560 | 112 | 5 | 5.3 |
| KEL04 | 52,560 | 233 | 5 | 25.5 |
| KEL05 | 52,560 | 111 | 5 | 5.7 |
| KEL06 | 52,560 | 236 | 6 | 15.8 |
| PEN11 | 26,064 | 418 | 3 | 44.8 |
| PEN12 | 26,064 | 19 | 1 | 3.0 |
| PEN13 | 26,064 | 19 | 1 | 3.0 |
| PEN14 | 26,064 | 19 | 1 | 3.0 |
| PEN15 | 26,064 | 48 | 3 | 3.7 |

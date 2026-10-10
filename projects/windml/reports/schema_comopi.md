# Schema: CoMoPI packaging machines: sensors (10-minute averages)

- Rows: 15,704
- Columns: 18
- Entities (_serial): 8 -> A001: 2,021, A005: 3,360, B002: 7,286, B005: 1,143, C003: 46, C004: 196, E002: 1,442, E004: 210
- Time span: 2022-07-14 14:00:00+00:00 to 2023-01-09 15:50:00+00:00
- Sampling interval: median 0 days 00:10:00, most common 0 days 00:05:00, share at mode 37.2%, max gap 28 days 23:55:00
- Overall missing cells: 0.55%
- Timestamps carry +00:00 (UTC). Sensor names are anonymized (A*/B* = two redundant closure elements); no units published.
- Targets per readme: alarms AL_53 and AL_54 indicate faulty component conditions.

| column | dtype | unit | missing % | min | max |
|---|---|---|---|---|---|
| AE | float64 |  | 0.00 | 0 | 1 |
| BE | float64 |  | 1.25 | 0 | 1 |
| AF | float64 |  | 0.00 | 0 | 1 |
| BF | float64 |  | 1.25 | 0 | 1 |
| APP | float64 |  | 0.00 | 0 | 1 |
| BPP | float64 |  | 1.25 | 0 | 1 |
| AP | float64 |  | 0.00 | 0 | 1 |
| BP | float64 |  | 1.25 | 0 | 1 |
| ALE | float64 |  | 0.00 | 0 | 1 |
| BLE | float64 |  | 1.25 | 0 | 1 |
| ALP | float64 |  | 0.00 | 0 | 1 |
| BLP | float64 |  | 1.25 | 0 | 1 |
| ADS | float64 |  | 0.00 | 0 | 1 |
| BDS | float64 |  | 1.25 | 0 | 1 |
| AES | float64 |  | 0.00 | 0 | 1 |
| BES | float64 |  | 1.25 | 0 | 1 |
| _time | datetime64[us, UTC] |  | 0.00 | 2022-07-14 14:00:00+00:00 | 2023-01-09 15:50:00+00:00 |
| _serial | str |  | 0.00 |  |  |

## alarm file

- Rows 150,650, 123 counter columns, span 2022-07-13 17:00:00+00:00 to 2023-01-09 15:50:00+00:00, missing 0.00%
- Most frequent (rows with count > 0): AL_1 32,749, AL_102 9,446, AL_12 2,184, AL_77 1,838, AL_104 1,529, AL_32 1,001, AL_29 967, AL_117 651, AL_19 596, AL_45 588, AL_36 584, AL_46 528
- Target alarms: AL_53 rows>0 = 23, AL_54 rows>0 = 18

## warnings file

- Rows 126,273, 358 counter columns, span 2022-07-20 08:30:00+00:00 to 2023-01-09 15:30:00+00:00, missing 0.00%
- Most frequent (rows with count > 0): WR_1 4,550, WR_317 1,578, WR_278 1,296, WR_219 939, WR_111 892, WR_176 799, WR_235 725, WR_223 570, WR_330 546, WR_352 523, WR_224 510, WR_139 489

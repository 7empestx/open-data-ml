# Schema: PIADE packaging machines: raw state/alarm intervals

- Rows: 429,394
- Columns: 12
- Entities (equipment_ID): 5 -> s_1: 127,676, s_2: 69,765, s_3: 34,454, s_4: 96,644, s_5: 100,855
- Time span: 2020-01-01 00:05:02.863000+00:00 to 2022-01-01 23:41:35.677000+00:00
- Sampling interval: median 0 days 00:01:04.291000, most common 0 days 00:00:07.680000, share at mode 0.6%, max gap 342 days 13:32:45.375000
- Overall missing cells: 0.00%
- Event-based (irregular) intervals: each row is a machine state/alarm interval, not a fixed sampling grid. Times carry +00:00 (UTC).
- type values: production 146,795, performance_loss 118,584, downtime 92,084, idle 50,149, scheduled_downtime 21,782

| column | dtype | unit | missing % | min | max |
|---|---|---|---|---|---|
| interval_start | datetime64[us, UTC] |  | 0.00 | 2020-01-01 00:05:02.863000+00:00 | 2022-01-01 23:41:35.677000+00:00 |
| equipment_ID | str |  | 0.00 |  |  |
| alarm | str |  | 0.00 |  |  |
| type | str |  | 0.00 |  |  |
| start | float64 | unix s | 0.00 | 1.578e+09 | 1.641e+09 |
| end | float64 | unix s | 0.00 | 1.578e+09 | 1.641e+09 |
| elapsed | int64 | ms | 0.00 | 114 | 79290078 |
| pi | int64 | counter (pieces in) | 0.00 | 0 | 338558998 |
| po | int64 | counter (pieces out) | 0.00 | 0 | 339148800 |
| speed | int64 | machine speed (unspecified) | 0.00 | 0 | 6500 |
| start_utc | datetime64[ns, UTC] |  | 0.00 | 2020-01-01 00:05:02.862999916+00:00 | 2022-01-01 23:41:35.677000046+00:00 |
| end_utc | datetime64[ns, UTC] |  | 0.00 | 2020-01-01 00:05:05.742999792+00:00 | 2022-01-02 00:34:51.645999908+00:00 |

## Schema: PIADE sequences_1h (hourly alarm counts per machine)

- Rows: 23,376
- Columns: 164
- Entities (equipment_ID): 5 -> s_1: 8,973, s_2: 2,725, s_3: 2,976, s_4: 3,959, s_5: 4,743
- Time span: 2020-01-01 01:00:00+00:00 to 2022-01-01 23:00:00+00:00
- Sampling interval: median 0 days 01:00:00, most common 0 days 01:00:00, share at mode 75.6%, max gap 342 days 20:00:00
- Overall missing cells: 38.43%

| column | dtype | unit | missing % | min | max |
|---|---|---|---|---|---|
| interval_start | datetime64[us, UTC] |  | 0.00 | 2020-01-01 01:00:00+00:00 | 2022-01-01 23:00:00+00:00 |
| equipment_ID | str |  | 0.00 |  |  |
| count_sum | int64 |  | 0.00 | 0 | 74 |
| A_028 | float64 |  | 20.29 | 0 | 2 |
| A_029 | int64 |  | 0.00 | 0 | 5 |
| A_024 | int64 |  | 0.00 | 0 | 7 |
| A_045 | float64 |  | 38.39 | 0 | 2 |
| A_001 | float64 |  | 20.29 | 0 | 6 |
| A_058 | float64 |  | 58.68 | 0 | 3 |
| A_064 | float64 |  | 48.88 | 0 | 3 |
| A_030 | float64 |  | 11.66 | 0 | 3 |
| A_101 | float64 |  | 55.32 | 0 | 31 |
| A_002 | int64 |  | 0.00 | 0 | 4 |
| A_107 | float64 |  | 87.27 | 0 | 1 |
| A_056 | int64 |  | 0.00 | 0 | 2 |
| A_015 | float64 |  | 50.04 | 0 | 2 |
| A_032 | float64 |  | 20.29 | 0 | 6 |
| A_026 | float64 |  | 20.29 | 0 | 2 |
| A_003 | int64 |  | 0.00 | 0 | 17 |
| A_008 | int64 |  | 0.00 | 0 | 9 |
| A_078 | float64 |  | 37.23 | 0 | 15 |
| A_070 | float64 |  | 37.23 | 0 | 31 |
| A_004 | int64 |  | 0.00 | 0 | 4 |
| A_005 | int64 |  | 0.00 | 0 | 45 |
| A_009 | int64 |  | 0.00 | 0 | 3 |
| ... 139 more columns omitted | | | | | |

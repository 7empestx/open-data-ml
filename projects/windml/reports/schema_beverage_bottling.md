# Schema: Beverage bottling line (production_raw.xlsx)

- Time zone: not stated; times are plant-local wall clock. Kept naive (no UTC conversion possible).
- No raw sensor channels; production, operation time, downtime and efficiency only.

## Schema: sheet processed_hourly

- Rows: 272
- Columns: 4
- Time span: 2022-07-22 00:00:00 to 2023-02-10 00:00:00
- Sampling interval: median 0 days 00:00:00, most common 0 days 00:00:00, share at mode 79.7%, max gap 29 days 00:00:00
- Overall missing cells: 0.00%

| column | dtype | unit | missing % | min | max |
|---|---|---|---|---|---|
| date | datetime64[us] |  | 0.00 | 2022-07-22 00:00:00 | 2023-02-10 00:00:00 |
| hour_start | int64 |  | 0.00 | 7 | 20 |
| hour_end | int64 |  | 0.00 | 8 | 21 |
| production_gallons | int64 |  | 0.00 | 0 | 673 |

## Schema: sheet daily_operation_summary

- Rows: 59
- Columns: 11
- Time span: 2022-07-22 00:00:00 to 2023-02-10 00:00:00
- Sampling interval: median 3 days 00:00:00, most common 3 days 00:00:00, share at mode 27.6%, max gap 29 days 00:00:00
- Overall missing cells: 0.00%

| column | dtype | unit | missing % | min | max |
|---|---|---|---|---|---|
| date | datetime64[us] |  | 0.00 | 2022-07-22 00:00:00 | 2023-02-10 00:00:00 |
| product_type_l | int64 |  | 0.00 | 3 | 5 |
| production_units | int64 |  | 0.00 | 76 | 2849 |
| liters_produced | int64 |  | 0.00 | 380 | 10740 |
| production_start_time | timedelta64[us] |  | 0.00 |  |  |
| production_end_time | timedelta64[us] |  | 0.00 |  |  |
| efficiency | float64 |  | 0.00 | 0.1538 | 0.9484 |
| gallons_per_hour | float64 |  | 0.00 | 94.57 | 1232 |
| monitored_time_dec | float64 |  | 0.00 | 0.2042 | 9.879 |
| operation_time_dec | float64 |  | 0.00 | 0.07922 | 5.064 |
| pause_time_dec | float64 |  | 0.00 | 0.1249 | 6.999 |

## Schema: sheet hourly_operation_breakdown

- Rows: 265
- Columns: 7
- Time span: 2022-07-22 00:00:00 to 2023-02-10 00:00:00
- Sampling interval: median 0 days 00:00:00, most common 0 days 00:00:00, share at mode 79.5%, max gap 29 days 00:00:00
- Overall missing cells: 0.00%

| column | dtype | unit | missing % | min | max |
|---|---|---|---|---|---|
| date | datetime64[us] |  | 0.00 | 2022-07-22 00:00:00 | 2023-02-10 00:00:00 |
| hour_start | int64 |  | 0.00 | 7 | 20 |
| hour_end | int64 |  | 0.00 | 8 | 21 |
| monitored_time_h | float64 |  | 0.00 | 0 | 1 |
| operation_time_h | float64 |  | 0.00 | 0 | 1 |
| downtime_h | float64 |  | 0.00 | 0 | 1 |
| efficiency | float64 |  | 0.00 | 0 | 1 |

## Schema: sheet downtime_event_log

- Rows: 1,388
- Columns: 5
- Time span: 2022-01-13 00:00:00 to 2023-02-10 00:00:00
- Sampling interval: median 0 days 00:00:00, most common 0 days 00:00:00, share at mode 96.1%, max gap 190 days 00:00:00
- Overall missing cells: 0.00%

| column | dtype | unit | missing % | min | max |
|---|---|---|---|---|---|
| downtime_id | str |  | 0.00 |  |  |
| date | datetime64[us] |  | 0.00 | 2022-01-13 00:00:00 | 2023-02-10 00:00:00 |
| downtime_start_time | timedelta64[us] |  | 0.00 |  |  |
| downtime_end_time | timedelta64[us] |  | 0.00 |  |  |
| downtime_time | timedelta64[us] |  | 0.00 |  |  |


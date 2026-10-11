# Operator mappings (windml.ingest)

One YAML file per operator export describes how to read it and how its columns map onto the canonical windml
schema. Everything operator-specific lives here; the loader itself has no per-operator code.

| file | export shape |
|---|---|
| `kelmarsh.yaml`, `penmanshiel.yaml` | Greenbyte wide CSV, one file per turbine, `#` preamble, UTC, separate status log |
| `la_haute_borne.yaml` | one CSV for all turbines (turbine id column), short tags (`P_avg`), ISO-8601 with UTC offsets |
| `examples/acme_messy.yaml` | synthetic: `;` + decimal comma, latin-1, vendor tags, W/°F/kPa, Europe/London local time, interval-end labels, monthly files, German alarm log |
| `examples/longco_long.yaml` | synthetic: long tag/value parquet, IEC 61400-25 tags, epoch ms |
| `examples/xlsx_sheets.yaml` | synthetic: Excel workbook, one sheet per turbine, title rows above the header |
| `examples/highres_1min.yaml` | synthetic high-res: 1-min CSV, decimal comma, Europe/London, end stamps, state code, dropouts and an outage |
| `examples/highres_1s.yaml` | synthetic high-res: 1-s parquet, UTC |
| `smarteole.yaml` | real high-res: SMARTEOLE (ENGIE) 1-min avg/min/max/std/count, one CSV, turbine number inside the column names |

The synthetic exports are generated from Kelmarsh by `scripts/make_messy_fixtures.py` and
`scripts/make_highres_fixtures.py` (`make ingest-fixtures`). `make ingest-proof` loads all of them (plus SMARTEOLE when
`make download-smarteole` has been run) and writes `reports/ingest/proof.md`.

## Mapping format

```yaml
name: acme                        # used for output file names
description: "..."
license: "..."                    # data license / NDA reference, copied into the report
rated_power_kw: 2050              # used by cleaning (power-curve QC)

scada:
  files:                          # globs relative to WINDML_RAW_DIR (or absolute); any number of files
    - "acme/WTG*_*.csv"
    - {glob: "acme/odd_name.csv", turbine_id: {from: constant, value: KEL07}}   # per-file override
    - {glob: "acme/*/*.csv", exclude: "acme/old_export/*"}   # exclude: glob(s) relative to WINDML_RAW_DIR
  format: auto                    # auto (by extension) | csv | excel | parquet
  csv:
    delimiter: auto               # auto | "," | ";" | "\t" | "|"
    decimal: ","                  # decimal comma
    thousands: "."                # optional
    encoding: latin-1             # utf-8 (default), utf-8-sig, latin-1, cp1252, ...
    header_match: '^Zeitstempel;' # regex for the header line (skips any preamble); or header_row: N
    na_values: ["NaN", "-", ""]
  excel: {sheets: all, header_row: 2}   # sheets: all | <name> | <index>; all adds a _sheet column
  layout: wide                    # wide (one column per signal) | long (tag/value rows)
  long: {tag_column: tag, value_column: value}       # only for layout: long
  turbine_id:
    from: filename                # column | columns | filename | sheet | constant
    # from: columns, values: [1, 2, 3]   -> turbine number inside the column names; write signal columns as
    #                                       templates, e.g. "active_power_{turbine}_avg"
    column: asset                 # for from: column
    regex: 'WTG(\d+)_'            # first group = raw id (applied to the file name, column value or sheet name)
    map: {R80711: LHB01}          # optional raw -> canonical id
    format: "KEL{:02d}"           # optional; numeric ids are formatted as integers
  timestamp:
    column: Zeitstempel           # or columns: [Date, Time] (joined with a space)
    format: "%d.%m.%Y %H:%M"      # auto | iso | epoch_s | epoch_ms | excel | strftime pattern
    dayfirst: false               # for format: auto
    timezone: Europe/London       # IANA zone of naive timestamps (UTC default); ignored when the data has offsets
    ambiguous: infer              # repeated autumn hour: infer (needs time-ordered files) | earliest | latest | drop
    nonexistent: drop             # skipped spring hour: drop | shift_forward
    label: end                    # start | end: does the stamp mark the start or the end of the interval?
    shift: 0min                   # extra fixed correction, e.g. "-1h" for a known clock offset
  interval: auto                  # native sampling interval: auto (detected per turbine) or e.g. "1min"; 1 s .. 10 min
  aggregate:                      # only used when the native interval is shorter than 10 min
    min_coverage: 0.5             # bins with fewer samples than this share of the expected count are blanked
    stats: [power_kw, wind_speed_ms]   # signals that also get <signal>_min/_max/_std (default: key signals)
  states:                         # status-like columns: 10-min <name>_last and <name>_mode, never averaged
    operating_state: Betriebszustand
  signals:                        # canonical name -> source (see the schema below)
    wind_speed_ms: "WindSpd_Avg [m/s]"           # short form: column (wide) or tag (long)
    power_kw: {column: "ActPwr [W]", unit: W}    # converted to the canonical unit
    ambient_temp_c: {column: "AmbTmp [°F]", unit: degF}
    gear_oil_inlet_pressure_bar:
      column: "Gear oil inlet pressure (bar)"
      unit_switch: {low: bar, high: kPa, threshold: 20}   # per-row unit when the logger switched units
    pitch_a_deg: {column: Ba_avg, unit: auto}    # auto = pick the unit that best fits the plausible range (warns)
    nacelle_temp_c: {column: NacTmp, scale: 0.1, offset: 0}   # raw counts -> value, applied after unit conversion
    power_kw:                     # high-res samples that are themselves statistics (e.g. 1-min of 1-Hz data):
      {column: P_avg, min: P_min, max: P_max, std: P_std, count: P_n}   # -> count-weighted mean, pooled std

status:                           # optional alarm / status log -> stop and fault labels
  files: ["acme/Alarme_WTG*.csv"]
  csv: {delimiter: ";"}           # same reader options and turbine_id rules as scada
  turbine_id: {from: filename, regex: 'WTG(\d+)_', format: "KEL{:02d}"}
  start: {column: Beginn, format: "%d.%m.%Y %H:%M:%S", timezone: Europe/London, ambiguous: earliest}
  end: {column: Ende, format: "%d.%m.%Y %H:%M:%S", timezone: Europe/London}
  end_missing: ["", "-"]          # values meaning "no end" (instantaneous / open event)
  duration: Duration              # optional "HH:MM:SS"; fills a missing end
  status: {column: Typ, map: {Halt: Stop, Warnung: Warning, Info: Informational}}
  code: Fehlercode
  message: Meldung
  service_category: Kategorie     # optional, used by the default classifier
  iec_category: IEC               # optional (IEC 61400-26 wording)
  class_by_code: {9999: maintenance}                 # explicit class per code (wins over the classifier)
  class_rules:                                       # regex rules on a field (default: message)
    - {match: "grid|netz", class: grid}
```

### High-res input (1 s to 10 min)

The loader detects the native interval per turbine (the most common step, snapped to 1/2/5/10/15/30 s or 1/2/5/10 min)
and aggregates anything finer than 10 min to the canonical 10-minute bins:

- Stamps are first moved to the sample start (`label: end` shifts back by the native interval, not by 10 min), so a
  bin holds exactly the samples that start in `[t, t + 10 min)`.
- Mean for linear signals, circular mean (and circular std) for `nacelle_position_deg` / `wind_direction_deg`; `_min`,
  `_max`, `_std` (population) for the `aggregate.stats` signals; `_last` / `_mode` for `states`.
- `n_samples` and `coverage` (samples / expected, capped at 1) per bin. Bins with no samples do not exist (gaps stay
  gaps); bins under `min_coverage` keep `n_samples`/`coverage` but their values are blanked. Duplicate samples are
  dropped (the most complete row wins).
- `windml ingest load --keep-raw` also writes the un-aggregated canonical samples to `<farm>_raw_highres.parquet` for
  later high-res features. Exported `_min/_max/_std` columns end up in `<farm>_stats_<tid>.parquet`.
- Coarser than 10 min: rows are placed on the 10-min grid, nothing is interpolated (warning).

Supported units (`src/windml/ingest/units.py`): °C/°F/K; kW/W/MW; kWh/Wh/MWh; bar/kPa/Pa/hPa/mbar/MPa/psi;
m/s, km/h, mph, kn; rpm, rad/s; deg, rad; fraction, percent. Unknown keys anywhere in the file are rejected, so typos
fail fast (`windml ingest validate --schema-only`).

## Canonical schema

Generated by `windml ingest schema`.

Index columns: `timestamp` (UTC, start of the 10-minute interval) and `turbine_id`.

| signal | unit | quantity | plausible range | description |
|---|---|---|---|---|
| `power_kw` (required) | kW | power | -200 to 10000 | Active power, 10-min mean |
| `wind_speed_ms` (required) | m/s | speed | 0 to 60 | Nacelle wind speed, 10-min mean |
| `wind_speed_1_ms` | m/s | speed | 0 to 60 | Wind speed sensor 1 |
| `wind_speed_2_ms` | m/s | speed | 0 to 60 | Wind speed sensor 2 |
| `rotor_speed_rpm` | rpm | rotational_speed | 0 to 40 | Rotor speed |
| `generator_speed_rpm` | rpm | rotational_speed | -50 to 3000 | Generator speed |
| `pitch_a_deg` | deg | angle | -10 to 100 | Blade A pitch angle |
| `pitch_b_deg` | deg | angle | -10 to 100 | Blade B pitch angle |
| `pitch_c_deg` | deg | angle | -10 to 100 | Blade C pitch angle |
| `nacelle_position_deg` | deg | angle | 0 to 360 | Nacelle direction (yaw position, 0-360) |
| `yaw_bearing_angle_deg` | deg | angle | -1500 to 1500 | Yaw bearing angle (may exceed 360, cable twist) |
| `wind_direction_deg` | deg | angle | 0 to 360 | Absolute wind direction |
| `ambient_temp_c` | degC | temperature | -45 to 55 | Ambient (outdoor) temperature |
| `nacelle_temp_c` | degC | temperature | -40 to 80 | Nacelle internal temperature |
| `gear_oil_temp_c` | degC | temperature | -30 to 110 | Gearbox oil sump temperature |
| `gear_oil_inlet_temp_c` | degC | temperature | -30 to 110 | Gearbox oil inlet temperature |
| `gear_oil_inlet_pressure_bar` | bar | pressure | 0 to 15 | Gearbox oil inlet pressure |
| `gear_oil_pump_pressure_bar` | bar | pressure | 0 to 25 | Gearbox oil pump pressure |
| `main_bearing_front_temp_c` | degC | temperature | -30 to 110 | Main (axle) bearing front temperature |
| `main_bearing_rear_temp_c` | degC | temperature | -30 to 110 | Main (axle) bearing rear temperature |
| `rotor_bearing_temp_c` | degC | temperature | -30 to 110 | Rotor bearing temperature |
| `gen_bearing_front_temp_c` | degC | temperature | -30 to 130 | Generator bearing, drive end |
| `gen_bearing_rear_temp_c` | degC | temperature | -30 to 130 | Generator bearing, non-drive end |
| `converter_inlet_temp_c` | degC | temperature | -30 to 80 | Converter (cabinet) ambient temperature |
| `hub_temp_c` | degC | temperature | -40 to 70 | Hub temperature |
| `pitch_motor_temp_1_c` | degC | temperature | -40 to 150 | Pitch motor temperature, axis 1 |
| `pitch_motor_temp_2_c` | degC | temperature | -40 to 150 | Pitch motor temperature, axis 2 |
| `pitch_motor_temp_3_c` | degC | temperature | -40 to 150 | Pitch motor temperature, axis 3 |
| `power_setpoint_kw` | kW | power | -10 to 10000 | Turbine power setpoint |
| `available_capacity_kw` | kW | power | -10 to 10000 | Available capacity for production |
| `data_availability` | fraction | fraction | 0 to 1 | Share of the 10-min interval with valid data (0-1) |
| `energy_export_kwh` | kWh | energy | -100 to 2000 | Energy exported in the interval |
| `lost_prod_curtail_total_kwh` | kWh | energy | 0 to 2000 | Lost production to curtailment |
| `lost_prod_downtime_kwh` | kWh | energy | 0 to 2000 | Lost production to downtime |

Status / alarm events:

| column | meaning |
|---|---|
| `turbine_id` | operator turbine id after mapping |
| `start` | event start, UTC |
| `end` | event end, UTC (NaT for instantaneous or open events) |
| `status` | Stop, Warning, Informational, Curtailment or Communication (map operator wording with `status: {column, map}`) |
| `code` | alarm / status code (integer if possible) |
| `message` | alarm text |
| `service_category` | optional manufacturer category |
| `iec_category` | optional IEC 61400-26 category (Forced outage, Scheduled Maintenance, ...) |
| `event_class` | optional pre-set class (fault, maintenance, curtailment, grid, weather, routine, other, info); set via class_by_code / class_rules in the mapping, otherwise inferred by labeling.classify_events |
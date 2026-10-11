"""windml canonical SCADA schema.

Every operator export is mapped to ONE long table per farm:

    timestamp   datetime64[ns, UTC]  start of the 10-minute averaging interval, on the 10-min grid
    turbine_id  str                  operator turbine id after mapping (e.g. KEL01)
    <signal>    float64              one column per canonical signal below, in the canonical unit

Signal names carry their unit as a suffix (``_kw``, ``_ms``, ``_c``, ``_bar``, ``_rpm``, ``_deg``) and match the
names the windml pipeline already uses (``clean_wind.KEY_COLUMNS`` plus the extra NBM signals), so a loaded dataset
can go straight into cleaning, labeling, the NBM and the trip models.

Status / alarm logs map to the canonical event table (see ``EVENT_COLUMNS``), which feeds ``labeling.classify_events``.
"""
from __future__ import annotations
from dataclasses import dataclass, field

FREQ = "10min"


@dataclass(frozen=True)
class Signal:
    name: str
    unit: str                 # canonical unit (see units.py)
    quantity: str             # power, speed, temperature, pressure, rotational_speed, angle, energy, fraction
    description: str
    plausible: tuple[float, float]   # physically plausible range in the canonical unit (for QC and auto-suggest)
    aliases: tuple[str, ...] = field(default_factory=tuple)  # extra names seen in exports (auto-suggest)
    required: bool = False


def _s(name, unit, quantity, description, plausible, aliases=(), required=False):
    return Signal(name, unit, quantity, description, plausible, tuple(aliases), required)


SIGNALS: dict[str, Signal] = {s.name: s for s in [
    # --- core (needed for cleaning / power-curve work) ---
    _s("power_kw", "kW", "power", "Active power, 10-min mean", (-200, 10_000),
       ["Power (kW)", "active power", "P_avg", "ActivePower", "WTUR.W", "WTUR_W", "Grd_Prod_Pwr_Avg", "power output", "output power", "Leistung"], True),
    _s("wind_speed_ms", "m/s", "speed", "Nacelle wind speed, 10-min mean", (0, 60),
       ["Wind speed (m/s)", "Ws_avg", "WindSpeed", "WNAC.WdSpd", "WNAC_WdSpd", "Amb_WindSpeed_Avg", "anemometer", "Windgeschwindigkeit"], True),
    _s("wind_speed_1_ms", "m/s", "speed", "Wind speed sensor 1", (0, 60), ["Wind speed Sensor 1 (m/s)", "Ws1_avg", "anemometer 1"]),
    _s("wind_speed_2_ms", "m/s", "speed", "Wind speed sensor 2", (0, 60), ["Wind speed Sensor 2 (m/s)", "Ws2_avg", "anemometer 2"]),
    _s("rotor_speed_rpm", "rpm", "rotational_speed", "Rotor speed", (0, 40),
       ["Rotor speed (RPM)", "Rs_avg", "RotorSpeed", "WROT.RotSpd", "WROT_RotSpd", "Rtr_RPM_Avg", "rotor rpm"]),
    _s("generator_speed_rpm", "rpm", "rotational_speed", "Generator speed", (-50, 3_000),
       ["Generator RPM (RPM)", "Ds_avg", "GeneratorSpeed", "WGEN.Spd", "WGEN_Spd", "Gen_RPM_Avg", "generator rpm", "gen speed"]),
    _s("pitch_a_deg", "deg", "angle", "Blade A pitch angle", (-10, 100),
       ["Blade angle (pitch position) A (°)", "Ba_avg", "pitch angle", "PitchAngle", "WROT.BlPthAngVal", "WROT_BlPthAngVal1", "Blds_PitchAngle_Avg", "pitch 1", "blade 1 pitch"]),
    _s("pitch_b_deg", "deg", "angle", "Blade B pitch angle", (-10, 100), ["Blade angle (pitch position) B (°)", "Bb_avg", "WROT_BlPthAngVal2", "pitch 2", "blade 2 pitch"]),
    _s("pitch_c_deg", "deg", "angle", "Blade C pitch angle", (-10, 100), ["Blade angle (pitch position) C (°)", "Bc_avg", "WROT_BlPthAngVal3", "pitch 3", "blade 3 pitch"]),
    _s("nacelle_position_deg", "deg", "angle", "Nacelle direction (yaw position, 0-360)", (0, 360),
       ["Nacelle position (°)", "Ya_avg", "NacellePosition", "nacelle angle", "WYAW.YwAng", "WNAC_Dir", "Nac_Direction_Avg", "yaw position"]),
    _s("yaw_bearing_angle_deg", "deg", "angle", "Yaw bearing angle (may exceed 360, cable twist)", (-1_500, 1_500), ["Yaw bearing angle (°)"]),
    _s("wind_direction_deg", "deg", "angle", "Absolute wind direction", (0, 360),
       ["Wind direction (°)", "Wa_avg", "WindDirection", "absolute wind direction", "WNAC.WdDir", "Amb_WindDir_Abs_Avg"]),
    _s("ambient_temp_c", "degC", "temperature", "Ambient (outdoor) temperature", (-45, 55),
       ["Nacelle ambient temperature (°C)", "Ot_avg", "AmbientTemperature", "outdoor temperature", "WNAC.ExTmp", "WNAC_ExTmp", "Amb_Temp_Avg", "Aussentemperatur"]),
    _s("nacelle_temp_c", "degC", "temperature", "Nacelle internal temperature", (-40, 80), ["Nacelle temperature (°C)", "WNAC.Tmp", "Nac_Temp_Avg", "nacelle temp"]),
    _s("gear_oil_temp_c", "degC", "temperature", "Gearbox oil sump temperature", (-30, 110),
       ["Gear oil temperature (°C)", "Gost_avg", "GearboxOilTemp", "WTRM.TrmTmp.GbxOil", "WTRM_TrmTmp_GbxOil", "Gear_Oil_Temp_Avg", "gearbox oil temp"]),
    _s("gear_oil_inlet_temp_c", "degC", "temperature", "Gearbox oil inlet temperature", (-30, 110), ["Gear oil inlet temperature (°C)", "Gear_Oil_Inlet_Temp_Avg"]),
    _s("gear_oil_inlet_pressure_bar", "bar", "pressure", "Gearbox oil inlet pressure", (0, 15),
       ["Gear oil inlet pressure (bar)", "WTRM.GbxOilPres", "Gear_Oil_Inlet_Press_Avg", "gearbox oil pressure"]),
    _s("gear_oil_pump_pressure_bar", "bar", "pressure", "Gearbox oil pump pressure", (0, 25), ["Gear oil pump pressure (bar)", "oil pump pressure"]),
    _s("main_bearing_front_temp_c", "degC", "temperature", "Main (axle) bearing front temperature", (-30, 110),
       ["Front bearing temperature (°C)", "Db1t_avg", "MainBearingTemp", "WTRM.TrmTmp.ShfBrg", "main bearing temp", "axle bearing temperature 1"]),
    _s("main_bearing_rear_temp_c", "degC", "temperature", "Main (axle) bearing rear temperature", (-30, 110),
       ["Rear bearing temperature (°C)", "Db2t_avg", "axle bearing temperature 2"]),
    _s("rotor_bearing_temp_c", "degC", "temperature", "Rotor bearing temperature", (-30, 110), ["Rotor bearing temp (°C)"]),
    _s("gen_bearing_front_temp_c", "degC", "temperature", "Generator bearing, drive end", (-30, 130),
       ["Generator bearing front temperature (°C)", "WGEN.BrgTmp.DE", "Gen_Bear_Temp_Avg", "generator bearing de"]),
    _s("gen_bearing_rear_temp_c", "degC", "temperature", "Generator bearing, non-drive end", (-30, 130),
       ["Generator bearing rear temperature (°C)", "Gen_Bear2_Temp_Avg", "generator bearing nde"]),
    _s("converter_inlet_temp_c", "degC", "temperature", "Converter (cabinet) ambient temperature", (-30, 80), ["Ambient temperature (converter) (°C)"]),
    _s("hub_temp_c", "degC", "temperature", "Hub temperature", (-40, 70), ["Hub temperature (°C)", "Spinner_Temp_Avg"]),
    _s("pitch_motor_temp_1_c", "degC", "temperature", "Pitch motor temperature, axis 1", (-40, 150), ["Temperature motor axis 1 (°C)"]),
    _s("pitch_motor_temp_2_c", "degC", "temperature", "Pitch motor temperature, axis 2", (-40, 150), ["Temperature motor axis 2 (°C)"]),
    _s("pitch_motor_temp_3_c", "degC", "temperature", "Pitch motor temperature, axis 3", (-40, 150), ["Temperature motor axis 3 (°C)"]),
    _s("power_setpoint_kw", "kW", "power", "Turbine power setpoint", (-10, 10_000), ["Turbine Power setpoint (kW)", "power setpoint"]),
    _s("available_capacity_kw", "kW", "power", "Available capacity for production", (-10, 10_000), ["Available Capacity for Production (kW)"]),
    _s("data_availability", "fraction", "fraction", "Share of the 10-min interval with valid data (0-1)", (0, 1), ["Data Availability"]),
    _s("energy_export_kwh", "kWh", "energy", "Energy exported in the interval", (-100, 2_000), ["Energy Export (kWh)", "net energy"]),
    _s("lost_prod_curtail_total_kwh", "kWh", "energy", "Lost production to curtailment", (0, 2_000), ["Lost Production to Curtailment (Total) (kWh)"]),
    _s("lost_prod_downtime_kwh", "kWh", "energy", "Lost production to downtime", (0, 2_000), ["Lost Production to Downtime (kWh)"]),
]}

# Status / alarm log -> canonical event table (input of labeling.classify_events)
EVENT_COLUMNS = {
    "turbine_id": "operator turbine id after mapping",
    "start": "event start, UTC",
    "end": "event end, UTC (NaT for instantaneous or open events)",
    "status": "Stop, Warning, Informational, Curtailment or Communication (map operator wording with `status: {column, map}`)",
    "code": "alarm / status code (integer if possible)",
    "message": "alarm text",
    "service_category": "optional manufacturer category",
    "iec_category": "optional IEC 61400-26 category (Forced outage, Scheduled Maintenance, ...)",
    "event_class": "optional pre-set class (fault, maintenance, curtailment, grid, weather, routine, other, info); "
                   "set via class_by_code / class_rules in the mapping, otherwise inferred by labeling.classify_events",
}
EVENT_CLASSES = ("fault", "maintenance", "curtailment", "grid", "weather", "routine", "other", "info")


def schema_markdown() -> str:
    """The schema as a markdown table (used in docs and the data-quality report)."""
    rows = ["| signal | unit | quantity | plausible range | description |", "|---|---|---|---|---|"]
    for s in SIGNALS.values():
        rows.append(f"| `{s.name}`{' (required)' if s.required else ''} | {s.unit} | {s.quantity} | {s.plausible[0]:g} to {s.plausible[1]:g} | {s.description} |")
    ev = ["| column | meaning |", "|---|---|"] + [f"| `{k}` | {v} |" for k, v in EVENT_COLUMNS.items()]
    return "\n".join(["Index columns: `timestamp` (UTC, start of the 10-minute interval) and `turbine_id`.", "", *rows,
                      "", "Status / alarm events:", "", *ev])

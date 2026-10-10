"""Parse + classify status logs, join labels to the cleaned 10-minute SCADA grid.
Outputs: data/processed/<farm>_events.parquet, data/processed/<farm>_scada_labeled.parquet,
         reports/labels_<farm>.md"""
import sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from windml import labeling as lb

WINDOWS = (7, 14, 30)
for farm in ["kelmarsh", "penmanshiel"]:
    ev = lb.classify_events(lb.parse_events(farm), major_min_duration="1h")
    ev.to_parquet(ROOT / f"data/processed/{farm}_events.parquet", index=False)
    scada = pd.read_parquet(ROOT / f"data/processed/{farm}_scada_10min.parquet")
    lab = lb.label_grid(scada, ev, WINDOWS)
    lab.to_parquet(ROOT / f"data/processed/{farm}_scada_labeled.parquet", index=False)
    s = lb.summarize(ev)
    lcols = ["in_any_stop", "in_fault", "in_major_fault"] + [f"pre_fault_{w}d" for w in WINDOWS] + \
            [c for c in lab.columns if c.startswith("in_stop_")]
    rows = lab.groupby("turbine_id", observed=True)[lcols].sum()
    rows.loc["ALL"] = rows.sum()
    majors = ev[ev["is_major_fault"]][["turbine_id", "major_episode", "start", "end_filled", "duration", "code", "message", "component"]]
    L = [f"# Failure labels: {farm}", "",
         f"Source: Greenbyte status logs ({ev['start'].min():%Y-%m-%d} to {ev['start'].max():%Y-%m-%d}, UTC). Rules in src/windml/labeling.py.",
         "Major fault = Stop classified as fault, component in gearbox/generator/bearing/converter/pitch/yaw/hydraulics, duration >= 1 h; "
         "major faults on the same turbine within 24 h are merged into one episode. Pre-fault windows count back from each episode start.", "",
         f"- Events: {s['events_total']:,} ({', '.join(f'{k} {v:,}' for k, v in s['events_by_status'].items())})",
         f"- Stops by class: {s['stops_by_class']}",
         f"- Stop hours by class: {s['stop_hours_by_class']}",
         f"- Fault stops by component: {s['fault_stops_by_component']}",
         f"- Major faults: {s['major_faults']} events in {s['major_fault_episodes']} episodes; by component {s['major_faults_by_component']}", "",
         "## Top stop codes (count)", "", s["top_stop_codes"].rename("count").reset_index().to_markdown(index=False), "",
         "## Top fault codes by downtime hours", "", s["top_fault_codes_by_hours"].rename("hours").reset_index().to_markdown(index=False), "",
         "## Major fault events", "", majors.to_markdown(index=False), "",
         "## Labeled 10-minute rows per turbine", "", rows.to_markdown(), "",
         f"Total rows: {len(lab):,}. Rows within the last 30 days of the record without a later major fault are right-censored (days_to_next_major_fault is NaN)."]
    (ROOT / f"reports/labels_{farm}.md").write_text("\n".join(L))
    print(farm, "events", len(ev), "major", s["major_faults"], "episodes", s["major_fault_episodes"]); print(rows.loc["ALL"].to_dict())

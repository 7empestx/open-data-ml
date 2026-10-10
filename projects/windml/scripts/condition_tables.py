"""Markdown table fragments + headline numbers for the sample condition report."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / "reports/condition_report/tables"
NAME = {"kelmarsh": "Kelmarsh", "penmanshiel": "Penmanshiel"}


def pct(v, d=1):
    return "" if pd.isna(v) else f"{v * 100:.{d}f}%"


def main():
    sc = pd.read_csv(T / "scorecard.csv")
    ty = pd.read_csv(T / "turbine_year.csv")
    dt = pd.read_csv(T / "downtime_by_cause.csv"); lo = pd.read_csv(T / "lost_by_cause.csv")
    ep = pd.read_csv(T / "trip_episodes.csv", parse_dates=["start"]); tr = pd.read_csv(T / "trips.csv", parse_dates=["start"])
    out, head = {}, {}
    for farm in ("kelmarsh", "penmanshiel"):
        s = sc[sc.farm == farm]
        rows = ["| Turbine | Flag | Tech. avail. | Energy avail. | Fault h/yr | Largest fault cause | Oil episodes | Pitch episodes | Repeat share oil / pitch (30 d, all years) | Abnormal oil days, final yr | Pump pressure: baseline to last month (bar) | Oil-temp model error vs 2018-22 |",
                "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for _, r in s.iterrows():
            rows.append(f"| {r.turbine_id} | **{r.flag}** | {pct(r.avail_time)} | {pct(r.avail_energy)} | {r.fault_h_per_yr:.0f} | {r.top_fault_cause} | "
                        f"{r.oil_ep_window} | {r.pitch_ep_window} | {pct(r.oil_repeat30, 0) or '-'} / {pct(r.pitch_repeat30, 0) or '-'} | "
                        f"{pct(r.oil_abn_final_year, 0)} | {r.pump_base_bar:.1f} to {r.pump_last_month_bar:.1f} | {r.oil_temp_mae_ratio:.1f}x |")
        out[f"scorecard_{farm}"] = "\n".join(rows)
        rows = ["| Turbine | Flag | Triggered rules |", "|---|---|---|"]
        for _, r in s.iterrows():
            rows.append(f"| {r.turbine_id} | **{r.flag}** | {r.reasons} |")
        out[f"flags_{farm}"] = "\n".join(rows)
        rows = ["| Turbine | Data missing (window) | Longest gap (window) | Invalid or frozen 10-min values, all years | Oil-pressure unit switches (bar/kPa) |",
                "|---|---|---|---|---|"]
        for _, r in s.iterrows():
            rows.append(f"| {r.turbine_id} | {pct(r.missing_window, 2)} | {r.longest_gap_h_window:.0f} h | {r.frozen_or_invalid_rows_all:,} | {r.oil_unit_switches} |")
        out[f"sensors_{farm}"] = "\n".join(rows)
        # downtime by cause, all years and window
        d = dt[dt.farm == farm].copy(); l = lo[lo.farm == farm].copy()
        nty = ty[ty.farm == farm]
        tyears = nty[nty.year >= (2017 if farm == "penmanshiel" else 2016)]["rows"].sum() / 52560
        win = {"kelmarsh": (2023, 2024), "penmanshiel": (2022, 2024)}[farm]
        h_all = d[d.year >= 2017].groupby("cause")["hours"].sum() if farm == "penmanshiel" else d.groupby("cause")["hours"].sum()
        l_all = l[l.year >= 2017].groupby("cause")["lost_mwh"].sum() if farm == "penmanshiel" else l.groupby("cause")["lost_mwh"].sum()
        n_all = d[d.year >= 2017].groupby("cause")["n_stops"].sum() if farm == "penmanshiel" else d.groupby("cause")["n_stops"].sum()
        tab = pd.DataFrame({"stops": n_all, "hours": h_all, "lost": l_all}).fillna(0)
        tab = tab[tab.index != "other"]
        tab["h_per_ty"] = tab["hours"] / tyears
        tab["share_lost"] = tab["lost"] / tab["lost"].sum()
        tab = tab.sort_values("lost", ascending=False)
        rows = ["| Cause | Stops | Downtime (turbine-h) | h per turbine-year | Lost production (MWh) | Share of lost production |", "|---|---|---|---|---|---|"]
        for c, r in tab.iterrows():
            rows.append(f"| {c} | {r.stops:,.0f} | {r.hours:,.0f} | {r.h_per_ty:.1f} | {r.lost:,.0f} | {pct(r.share_lost)} |")
        out[f"downtime_{farm}"] = "\n".join(rows)
        e = nty[nty.year >= (2017 if farm == "penmanshiel" else 2016)]
        head[farm] = {
            "turbine_years": round(tyears, 1),
            "avail_time_mean": float((e.avail_time * e.rows).sum() / e.rows.sum()),
            "avail_energy_all": float(e.export_mwh.sum() / (e.export_mwh.sum() + e.lost_downtime_mwh.sum())),
            "export_gwh": float(e.export_mwh.sum() / 1000), "lost_gwh": float(e.lost_downtime_mwh.sum() / 1000),
            "fault_share_lost": float(tab[tab.index.str.startswith("fault")]["lost"].sum() / tab["lost"].sum()),
            "maint_share_lost": float(tab.loc["maintenance", "lost"] / tab["lost"].sum()),
            "fault_hours_per_ty": float(tab[tab.index.str.startswith("fault")]["hours"].sum() / tyears),
            "maint_hours_per_ty": float(tab.loc["maintenance", "hours"] / tyears),
            "oil_trips": int((tr.farm == farm).mul(tr.kind == "oil").sum()), "pitch_trips": int((tr.farm == farm).mul(tr.kind == "pitch").sum()),
            "oil_eps": int(((ep.farm == farm) & (ep.kind == "oil")).sum()), "pitch_eps": int(((ep.farm == farm) & (ep.kind == "pitch")).sum()),
            "flags": s.flag.value_counts().to_dict(),
        }
        yy = nty.groupby("year").apply(lambda g: (g.avail_time * g.rows).sum() / g.rows.sum())
        head[farm]["avail_by_year"] = {int(k): round(float(v), 4) for k, v in yy.items()}
    for k, v in out.items():
        (T / f"{k}.md").write_text(v + "\n")
    (T / "headline.json").write_text(json.dumps(head, indent=1))
    print(json.dumps(head, indent=1))


if __name__ == "__main__":
    main()

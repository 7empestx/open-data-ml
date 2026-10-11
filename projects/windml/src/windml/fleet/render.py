"""Stage 5: condition report as markdown + figures, html (print CSS) and pdf (headless Chrome, if available).

The executive summary comes first and is written for an O&M manager: which turbines to look at, why, how sure we
are, and what to do next. The technical sections follow, then methods and limits.
"""
from __future__ import annotations
import os
import re
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

CSS = """
@page { size: A4; margin: 15mm 13mm 16mm 13mm; }
body { font-family: "DejaVu Sans", "Liberation Sans", Arial, sans-serif; font-size: 9.4pt; line-height: 1.36; color: #1d2733; max-width: 1100px; margin: auto; }
h1 { font-size: 19pt; color: #12324d; border-bottom: 3px solid #12324d; padding-bottom: 4px; margin-top: 0; }
h2 { font-size: 13.5pt; color: #12324d; border-bottom: 1px solid #b8c4d0; padding-bottom: 2px; margin-top: 18px; break-after: avoid; }
h2.newpage, .pb { break-before: page; }
h3 { font-size: 11pt; color: #1f4e79; margin-top: 12px; break-after: avoid; }
p, li { orphans: 3; widows: 3; }
blockquote { border-left: 4px solid #1f4e79; background: #eef3f8; margin: 8px 0; padding: 5px 11px; }
table { border-collapse: collapse; width: 100%; font-size: 7.6pt; margin: 6px 0 10px 0; break-inside: auto; }
th { background: #12324d; color: white; text-align: left; padding: 3px 4px; font-weight: 600; }
td { border-bottom: 1px solid #d5dde5; padding: 2.5px 4px; vertical-align: top; }
tr { break-inside: avoid; }
tr:nth-child(even) td { background: #f5f8fb; }
img { max-width: 100%; display: block; margin: 6px auto 2px auto; break-inside: avoid; }
code { font-size: 8pt; background: #eef2f6; padding: 0 2px; }
.flag-RED { color: #fff; background: #c0392b; padding: 0 4px; border-radius: 2px; font-weight: bold; }
.flag-AMBER { color: #1d2733; background: #f5b041; padding: 0 4px; border-radius: 2px; font-weight: bold; }
.flag-GREEN { color: #fff; background: #27ae60; padding: 0 4px; border-radius: 2px; font-weight: bold; }
"""
COMP_LABEL = {"oil": "gearbox oil system", "main_bearing": "main bearing", "pitch": "pitch system", "performance": "power curve",
              "gearbox": "gearbox temperatures"}


def _pct(v, d=0):
    return "-" if v is None or (isinstance(v, float) and np.isnan(v)) else f"{v:.{d}%}"


def _num(v, fmt="{:.1f}"):
    return "-" if v is None or (isinstance(v, float) and np.isnan(v)) else fmt.format(v)


def _table(rows: list[list], head: list[str]) -> str:
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def figures(M: dict, S: dict, out: Path, rated: dict) -> dict:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fdir = out / "figures"
    fdir.mkdir(parents=True, exist_ok=True)
    figs = {}
    mon = M["monthly"]
    tids = sorted(M["turbines"])
    if len(mon):
        mon = mon.copy()
        # 1. data coverage heatmap
        piv = mon.pivot_table(index="turbine_id", columns="month", values="coverage").reindex(tids)
        fig, ax = plt.subplots(figsize=(10, 0.35 * len(tids) + 1.4))
        im = ax.imshow(piv.to_numpy(), aspect="auto", cmap="RdYlGn", vmin=0.5, vmax=1)
        ax.set_yticks(range(len(tids)), tids, fontsize=7)
        step = max(1, len(piv.columns) // 18)
        ax.set_xticks(range(0, len(piv.columns), step), piv.columns[::step], rotation=90, fontsize=6)
        fig.colorbar(im, ax=ax, label="share of 10-min slots with data", fraction=0.025)
        ax.set_title("Data coverage by month", fontsize=9)
        fig.tight_layout(); fig.savefig(fdir / "coverage.png", dpi=130); plt.close(fig)
        figs["coverage"] = "figures/coverage.png"
        # 2. NBM abnormal-day heatmaps
        comps = [c[4:] for c in mon.columns if c.startswith("abn_")]
        comps = [c for c in ("oil", "performance", "pitch", "main_bearing") if c in comps]
        if comps:
            w0 = min(r["window_start"] for r in M["turbines"].values()) - pd.DateOffset(months=12)
            m2 = mon[mon["month"] >= f"{w0:%Y-%m}"]
            fig, axes = plt.subplots(len(comps), 1, figsize=(10, (0.3 * len(tids) + 0.8) * len(comps) + 0.6), squeeze=False)
            for ax, c in zip(axes[:, 0], comps):
                pv = m2.pivot_table(index="turbine_id", columns="month", values=f"abn_{c}").reindex(tids)
                im = ax.imshow(pv.to_numpy(), aspect="auto", cmap="Reds", vmin=0, vmax=0.6)
                ax.set_yticks(range(len(tids)), tids, fontsize=7)
                step = max(1, len(pv.columns) // 18)
                ax.set_xticks(range(0, len(pv.columns), step), pv.columns[::step], rotation=90, fontsize=6)
                ax.set_title(f"Share of abnormal days per month: {COMP_LABEL.get(c, c)} (blank = not scored)", fontsize=8.5)
                fig.colorbar(im, ax=ax, fraction=0.025)
            fig.tight_layout(); fig.savefig(fdir / "nbm_heatmap.png", dpi=130); plt.close(fig)
            figs["nbm"] = "figures/nbm_heatmap.png"
        # 3. oil trends
        have = [c for c in ("pump", "inlet", "oil_t") if c in mon]
        if have:
            lab = {"pump": "gear-oil pump pressure (bar)", "inlet": "gear-oil inlet pressure (bar)", "oil_t": "gear-oil temperature (°C)"}
            fig, axes = plt.subplots(len(have), 1, figsize=(10, 2.5 * len(have) + 0.4), squeeze=False, sharex=True)
            months = sorted(mon["month"].unique())
            xi = {m: i for i, m in enumerate(months)}
            for ax, c in zip(axes[:, 0], have):
                for tid in tids:
                    g = mon[(mon["turbine_id"] == tid) & (mon.get(f"n_{c}", 0) >= 50)]
                    flag = S[tid]["flag"]
                    ax.plot([xi[m] for m in g["month"]], g[c], lw=1.6 if flag == "RED" else 0.9,
                            color={"RED": "#c0392b", "AMBER": "#e67e22"}.get(flag, "#9aa5b1"), alpha=1 if flag != "GREEN" else 0.6,
                            label=tid if flag != "GREEN" else None)
                ax.set_ylabel(lab[c], fontsize=7.5); ax.grid(alpha=0.3)
            step = max(1, len(months) // 18)
            axes[-1, 0].set_xticks(range(0, len(months), step), months[::step], rotation=90, fontsize=6)
            axes[0, 0].set_title("Monthly medians at full load, flagged turbines highlighted (others grey)", fontsize=9)
            h, l_ = axes[0, 0].get_legend_handles_labels()
            if h:
                axes[0, 0].legend(fontsize=6.5, ncol=6)
            fig.tight_layout(); fig.savefig(fdir / "oil_trends.png", dpi=130); plt.close(fig)
            figs["oil"] = "figures/oil_trends.png"
    dr = M["drift"]
    if len(dr):
        sigs = list(dict.fromkeys(dr["signal"]))
        fig, axes = plt.subplots(len(sigs), 1, figsize=(10, 2.3 * len(sigs) + 0.4), squeeze=False)
        lab = {"ambient_temp_c": "ambient temp. minus fleet (°C)", "wind_speed_ms": "wind speed / fleet"}
        for ax, s in zip(axes[:, 0], sigs):
            g = dr[dr["signal"] == s]
            months = sorted(g["month"].unique())
            xi = {m: i for i, m in enumerate(months)}
            for tid, gg in g.groupby("turbine_id"):
                ax.plot([xi[m] for m in gg["month"]], gg["offset"], lw=0.9, label=tid)
            step = max(1, len(months) // 18)
            ax.set_xticks(range(0, len(months), step), months[::step], rotation=90, fontsize=6)
            ax.set_ylabel(lab.get(s, s), fontsize=7.5); ax.grid(alpha=0.3)
        axes[0, 0].legend(fontsize=6, ncol=8)
        axes[0, 0].set_title("Sensor offsets vs the median of the other turbines (monthly median)", fontsize=9)
        fig.tight_layout(); fig.savefig(fdir / "drift.png", dpi=130); plt.close(fig)
        figs["drift"] = "figures/drift.png"
    dt = M["downtime"]
    if len(dt):
        p = dt.assign(cause=dt["cause"].str.replace("fault: ", "", regex=False))
        top = p.groupby("cause")["hours"].sum().sort_values(ascending=False).index[:8]
        p["cause"] = np.where(p["cause"].isin(top), p["cause"], "other")
        pv = p.pivot_table(index="turbine_id", columns="cause", values="hours", aggfunc="sum").fillna(0).reindex(tids).fillna(0)
        fig, ax = plt.subplots(figsize=(10, 3.2))
        pv.plot.bar(stacked=True, ax=ax, width=0.8, colormap="tab20")
        ax.set_ylabel("hours in window (first cause)", fontsize=8); ax.legend(fontsize=6.5, ncol=3); ax.grid(axis="y", alpha=0.3)
        ax.set_title("Downtime by cause in the assessment window", fontsize=9)
        fig.tight_layout(); fig.savefig(fdir / "downtime.png", dpi=130); plt.close(fig)
        figs["downtime"] = "figures/downtime.png"
    return figs


def markdown_report(M: dict, S: dict, prep: dict, opts: dict, figs: dict) -> str:
    T = M["turbines"]
    tids = sorted(T)
    H = M["health"]
    farm = prep["farm"]
    has_log = prep["has_status_log"]
    any_t = next(iter(T.values()))
    w0 = min(r["window_start"] for r in T.values())
    end = max(r["end"] for r in T.values())
    first = min(r["first"] for r in T.values())
    order = {"RED": 0, "AMBER": 1, "GREEN": 2}
    look = sorted([t for t in tids if S[t]["flag"] != "GREEN"], key=lambda t: (order[S[t]["flag"]], -len(S[t]["red"]) - len(S[t]["amber"]), t))
    green = [t for t in tids if S[t]["flag"] == "GREEN"]
    schemes = {H.get(t, {}).get("scheme", "none") for t in tids}
    sigs = sorted({s for t in prep["turbines"] for s in t.get("signals", []) if not s.endswith(("_min", "_max", "_std")) and s not in ("n_samples", "coverage")})
    title = re.split(r" \(|,", prep.get("description") or "")[0].strip() or farm
    L = [f"# Fleet condition report: {title}", "",
         f"{prep.get('description') or farm}. {len(tids)} turbines, SCADA {first:%d %b %Y} to {(end - pd.Timedelta('1s')):%d %b %Y}; "
         f"assessment window: the last {opts['window_months']} months of each turbine ({w0:%b %Y} to {(end - pd.Timedelta('1s')):%b %Y}). "
         f"Generated by `windml report` from the mapping `{opts['mapping_name']}`.", "",
         "## Executive summary", ""]
    nred, namb = sum(S[t]["flag"] == "RED" for t in tids), sum(S[t]["flag"] == "AMBER" for t in tids)
    ngreen = len(tids) - nred - namb
    if look:
        L.append(f"**{ngreen} of {len(tids)} turbines are green, {namb} amber, {nred} red.** "
                 + ("Red means act now: a strong, specific warning sign. " if nred else "")
                 + ("Amber means check at the next visit: a specific, unusual pattern. " if namb else "")
                 + "Green means no validated warning sign in the data, not a guarantee.")
    else:
        L.append(f"**All {len(tids)} turbines are green**: no validated warning sign in the data up to "
                 f"{(end - pd.Timedelta('1s')):%d %b %Y}. Green is not a guarantee; see the notes and limits below.")
    L.append("")
    if look:
        rows = []
        for t in look:
            s = S[t]
            items = s["red"] + s["amber"]
            why = items[0][2] + (f" Also: {'; '.join(x[2].rstrip('.') for x in items[1:])}." if len(items) > 1 else "")
            ao = s.get("as_of")
            if ao is not None and ao < end - pd.Timedelta(days=60):
                why += f" (This turbine's published data ends {ao:%d %b %Y}.)"
            rows.append([t, f"**{s['flag']}**", why, items[0][3], s["confidence"]])
        L += [_table(rows, ["Turbine", "Rating", "Why", "Suggested check", "Confidence"]), ""]
    if green:
        L.append(f"**Green:** {', '.join(green)}.")
        L.append("")
    noted = [(t, n) for t in tids for n in S[t].get("notes", []) if n[0] != "data"]
    if noted:
        L += ["**Worth knowing.** Shown for context only: these signals (model alerts, past availability) did not reliably "
              "precede events in the validation, so they do not change the rating.", ""]
        L += [f"- **{t}**: {n[2]}" for t, n in noted[:8]]
        if len(noted) > 8:
            L.append(f"- and {len(noted) - 8} more in section 2.")
        L.append("")
    L += ["**How the ratings work.** " + rating_method_short(has_log, len(tids)), ""]
    lim = []
    if not has_log:
        lim.append("There is **no alarm log**, so we cannot see faults, trips or availability. Stops are inferred from SCADA "
                   "(no power while the wind blows), and the trip rules cannot run.")
    if not has_log and not any(T[t].get("pump_base") is not None for t in tids):
        lim.append("With neither an alarm log nor gear-oil pump pressure, only the sensor checks can change a rating for this "
                   "fleet: green here mostly means 'no sensor problem found'. Model alerts are still shown as notes.")
    if "none" in schemes:
        n = sum(H.get(t, {}).get("scheme", "none") == "none" for t in tids)
        lim.append(f"{n} turbine(s) have less than 12 months of data: no normal-behaviour model was trained for them.")
    if "cross-fit" in schemes:
        lim.append("The history is short (under two years), so models were cross-fitted within the record: they spot sudden "
                   "changes and outliers, but a slow change that started before the data begins is invisible.")
    missing = [lab for sig, lab in (("gear_oil_temp_c", "gearbox oil temperatures"), ("gear_oil_inlet_pressure_bar", "oil pressures"),
                                    ("main_bearing_front_temp_c", "main-bearing temperatures"), ("pitch_motor_temp_1_c", "pitch-motor temperatures"))
               if sig not in sigs]
    if missing:
        lim.append(f"The export has no {', no '.join(missing)}, so those components could not be checked.")
    ws = [T[t].get("window_scored_share") for t in tids if T[t].get("window_scored_share") is not None]
    if ws and np.median(ws) < 0.8:
        lim.append(f"Models scored only about {np.median(ws):.0%} of the window (the first year of a record is needed to train them).")
    L += ["**How sure are we.** Confidence is *High* when the turbine has 3+ years of history, near-complete data, models "
          "trained on earlier years, an alarm log and at least 3 sister turbines to compare with; it drops when any of "
          "these is missing. A red rating is a reason to look, not a diagnosis.", ""]
    if lim:
        L += ["**What this report could not check:**", ""] + [f"- {x}" for x in lim] + [""]
    # 1. data quality
    L += ['<h2 class="newpage">1. Data quality</h2>', ""]
    rows = []
    for t in tids:
        r = T[t]
        fro = r.get("frozen_rows_window", {})
        st = ", ".join(r.get("stuck_sensors", [])) or "-"
        rows.append([t, f"{r['first']:%Y-%m-%d}", f"{(r['end'] - pd.Timedelta('1s')):%Y-%m-%d}", f"{r['history_months']:.0f}",
                     _pct(r["coverage_window"], 1), _num(r["longest_gap_h_window"], "{:.0f}"), len(r.get("signals", [])),
                     r.get("native_interval", "10min"), f"{sum(fro.values()):,}", st, r["label_source"]])
    L += [_table(rows, ["Turbine", "First data", "Last data", "Months", "Coverage (window)", "Longest gap (h)", "Signals",
                        "Native interval", "Frozen rows (window)", "Stuck sensors (>= 1%)", "Stop/fault labels"]), ""]
    if figs.get("coverage"):
        L += [f"![coverage]({figs['coverage']})", ""]
    warns = list(dict.fromkeys(w for t in prep["turbines"] for w in t.get("warnings", [])))
    if warns:
        L += ["Ingest warnings (deduplicated, first 15):", ""] + [f"- {w}" for w in warns[:15]] + [""]
    L += [f"Signals present in at least one turbine: {', '.join(f'`{s}`' for s in sigs)}.", ""]
    # 2. scorecard
    L += ['<h2 class="newpage">2. Turbine scorecard</h2>', ""]
    head = ["Turbine", "Flag", "Confidence"]
    if has_log:
        head += ["Tech. avail.", "Energy avail.", "Fault h/yr", "Largest fault cause", "Oil ep.", "Pitch ep."]
    else:
        head += ["Non-production at wind (inferred)"]
    head += ["Abnormal oil days, final yr", "Under-perf. days, final yr", "Pump pressure: base to last (bar)", "Oil-temp model error"]
    rows = []
    for t in tids:
        r, s = T[t], S[t]
        row = [t, f"**{s['flag']}**", s["confidence"]]
        if has_log:
            row += [_pct(r.get("avail_time"), 1), _pct(r.get("avail_energy"), 1), _num(r.get("fault_h_per_yr"), "{:.0f}"),
                    r.get("top_fault_cause") or "-", r.get("oil_ep_window", "-"), r.get("pitch_ep_window", "-")]
        else:
            row += [_pct(r.get("nonprod_at_wind"), 1)]
        pb = f"{_num(r.get('pump_base'))} to {_num(r.get('pump_last'))}" if r.get("pump_base") is not None else "-"
        row += [_pct(r.get("abn_oil_final_year")), _pct(r.get("abn_performance_final_year")), pb, _num(r.get("oil_temp_mae_ratio"), "{:.1f}x")]
        rows.append(row)
    L += [_table(rows, head), ""]
    L += ["### Ratings, reasons and notes", ""]
    for t in tids:
        s = S[t]
        items = s["red"] + s["amber"]
        L.append(f"- **{t}** **{s['flag']}** (confidence {s['confidence']}: {', '.join(s['confidence_notes'])}). " +
                 (" ".join(("RED: " if x in s["red"] else "AMBER: ") + f"{x[2]} *Check:* {x[3]}" for x in items) if items else "No rating trigger.")
                 + ("" if not s.get("notes") else " Notes: " + " ".join(n[2] for n in s["notes"])))
    L.append("")
    # 3. NBM
    L += ['<h2 class="newpage">3. Model-based health (normal-behaviour residuals)</h2>', ""]
    L += ["Each turbine gets its own models that predict a signal (oil temperature, bearing temperature, pitch angle, "
          "power...) from operating conditions. A day is *abnormal* when the turbine's median deviation from its own model "
          "is beyond 3 robust standard deviations in the harmful direction. *Chronic* means at least 30% abnormal days in a month.", ""]
    rows = []
    comps = [c for c in ("oil", "main_bearing", "pitch", "performance") if any(f"abn_{c}_final_year" in T[t] for t in tids)]
    for t in tids:
        r, h = T[t], H.get(t, {})
        row = [t, h.get("scheme", "none"), len(h.get("targets", [])), _pct(r.get("window_scored_share"))]
        for c in comps:
            row.append(f"{_pct(r.get(f'abn_{c}_final_year'))} / {r.get(f'chronic_months_{c}', '-')}")
        rows.append(row)
    L += [_table(rows, ["Turbine", "Training scheme", "Models", "Window scored"] +
                 [f"{COMP_LABEL[c]}: abnormal days final yr / chronic months" for c in comps]), ""]
    chronic = [(t, c, T[t].get(f"chronic_run_{c}", 0)) for t in tids for c in comps if T[t].get(f"chronic_run_{c}", 0) >= 3]
    if chronic:
        L += ["**Chronic abnormal turbines** (3+ consecutive months with >= 30% abnormal days): " +
              "; ".join(f"{t} {COMP_LABEL[c]} ({n} months)" for t, c, n in chronic) + ".", ""]
    else:
        L += ["No turbine has 3 or more consecutive chronic months in the window.", ""]
    if figs.get("nbm"):
        L += [f"![nbm]({figs['nbm']})", ""]
    # 4. oil trends
    if figs.get("oil") or any(T[t].get("pump_base") is not None for t in tids):
        L += ['<h2 class="newpage">4. Gearbox oil pressure and temperature trends</h2>', ""]
        rows = []
        for t in tids:
            r = T[t]
            rows.append([t] + [f"{_num(r.get(f'{k}_base'))} → {_num(r.get(f'{k}_last'))} ({_num(r.get(f'{k}_rise'), '{:+.1f}')})"
                               if r.get(f"{k}_base") is not None else "-" for k in ("pump", "inlet", "oil_t")]
                        + [r.get("pump_base_period") or r.get("oil_t_base_period") or "-"])
        L += [_table(rows, ["Turbine", "Pump pressure (bar): baseline → last month", "Inlet pressure (bar)", "Oil temperature (°C)",
                            "Baseline months"]), ""]
        if figs.get("oil"):
            L += [f"![oil]({figs['oil']})", ""]
    # 5. sensors
    L += ['<h2 class="newpage">5. Sensor drift and stuck sensors</h2>', ""]
    dsig = [s for s in ("ambient_temp_c", "wind_speed_ms") if any(f"drift_{s}" in T[t] for t in tids)]
    if dsig:
        rows = [[t] + [(_num(T[t].get(f"drift_{s}"), "{:+.2f} °C") if s != "wind_speed_ms" else _pct(T[t].get(f"drift_{s}"), 1))
                       for s in dsig] + [", ".join(T[t].get("stuck_sensors", [])) or "-"] for t in tids]
        L += ["Drift = change of a turbine's offset to the median of the other turbines, last 3 months vs before the window "
              "(thresholds: 1.5 °C, 5% wind speed).", "", _table(rows, ["Turbine"] + [f"drift {s}" for s in dsig] + ["Stuck sensors"]), ""]
    else:
        L += ["Fewer than 4 turbines share a drift-check signal, so sensor drift against the fleet could not be checked.", ""]
    if figs.get("drift"):
        L += [f"![drift]({figs['drift']})", ""]
    # 6. stops
    L += ['<h2 class="newpage">6. Stop and fault history</h2>', ""]
    if has_log:
        rows = []
        for t in tids:
            r = T[t]
            sw = r.get("stops_window", {})
            rows.append([t, sw.get("fault", 0), sw.get("maintenance", 0), sw.get("grid", 0), sw.get("weather", 0), sw.get("curtailment", 0),
                         r.get("major_faults_window", 0), _num(r.get("maint_h_per_yr"), "{:.0f}"),
                         f"{r.get('oil_trips_window', 0)} / {r.get('pitch_trips_window', 0)}"])
        L += [_table(rows, ["Turbine", "Fault stops", "Maintenance", "Grid", "Weather", "Curtailment", "Major-fault episodes",
                            "Maint. h/yr", "Oil / pitch trips"]), ""]
        if figs.get("downtime"):
            L += [f"![downtime]({figs['downtime']})", ""]
        fc = M["fault_codes"]
        if len(fc):
            g = fc.groupby(["code", "message", "component"], dropna=False)["n"].sum().sort_values(ascending=False).head(12).reset_index()
            L += ["Most frequent fault stops in the window (all turbines):", "",
                  _table([[c, m, comp, n] for c, m, comp, n in g.itertuples(index=False)], ["Code", "Message", "Component", "Stops"]), ""]
    else:
        L += ["The export has no alarm or status log. Stops were inferred from SCADA: power below 1% of rated while the "
              "wind is between 4.5 and 25 m/s. That catches downtime, but cannot tell a fault from a grid outage, "
              "maintenance or curtailment, so no stop/fault history, availability or trip analysis is possible.", ""]
    # 7. methods
    L += ['<h2 class="newpage">7. Methods, thresholds and limits</h2>', "",
          f"- **Pipeline.** `windml report` reads the raw export only through the mapping (`windml.ingest`), cleans and labels "
          "each turbine (QC flags, short-gap interpolation, alarm-log stop labels), trains the models, computes the metrics "
          "and writes this report. Every number here is reproducible from the mapping and the raw files.",
          "- **Window.** The last 24 months of each turbine; *final year* = its last 12 months.",
          "- **Models.** LightGBM per turbine and signal on healthy operating rows (no stop within 6 h, no fault, not in the 30 "
          "days before a major fault, QC clean). With 2+ calendar years, each year is scored by a model trained only on "
          "earlier years (3-day embargo, training must cover all 12 months). With 12-23 months, the record is cut into 6 "
          "blocks scored by models trained on the other blocks (cross-fit). Under 12 months, no model.",
          "- **Ratings.** " + rating_method_long(),
          "- **Validation.** " + validation_text(),
          "- **Confidence.** Points for history (3+ years: 2, 2-3 years: 1), coverage >= 95%, models trained on earlier years, "
          "an alarm log, and a fleet of 4+ turbines (peer comparison). High >= 5, Medium 3-4, Low <= 2.",
          "- **Limits.** The alarm-log classes come from the mapping's rules; trip detection uses Senvion-style oil/pitch codes "
          "and messages (other vendors need `class_rules`). Full-load oil medians assume one oil circuit design across the "
          "fleet. Models learn whatever was normal in their training data, including a fault that was already present. "
          "Sensor drift is relative to the other turbines, so a fleet-wide drift is invisible. The rating thresholds were "
          "calibrated on two UK farms of one turbine family (Senvion MM92/MM82); on other fleets the peer-relative "
          "logic still applies but the hit rates are unknown. Ratings look back up to 6 months and only at what SCADA and "
          "the alarm log show: inspections, oil analyses, vibration (CMS) data and work orders are not used, so "
          "a recent repair or a fault the sensors cannot see changes nothing here.",
          f"- **Data.** {prep.get('license') or 'see the mapping'}.", ""]
    return "\n".join(L)


def _pc(v):
    return "–" if v is None else f"{v:.0%}"


def rating_method_short(has_log: bool, n: int) -> str:
    from . import rules
    v = rules.CALIBRATION.get("validation", {}).get("overall_test", {}).get("pooled", {})
    ar = v.get("amber_or_red", {})
    txt = ("A turbine is amber only for a specific, unusual pattern: gear-oil pump pressure building up far beyond its "
           "sister turbines, repeated oil-system or pitch trips, or a faulty sensor. It is red when the pattern is strong "
           "(e.g. a pump pressure rise of 2 bar or more) or persistent and still active. Thresholds were chosen on "
           f"2017-2020 data from two UK wind farms and checked on 2021-2024: ")
    if ar.get("flagged"):
        txt += (f"amber or red turbine-months were followed by a logged fault, trip or long service stop within 90 days "
                f"{_pc(ar.get('hit_rate'))} of the time, against {_pc(ar.get('expected'))} for random turbines in the same "
                f"months; but only {_pc(ar.get('recall'))} of the turbine-months before such an event carried a flag. ")
    txt += "Ratings help decide where to look first; most faults still arrive without a warning sign in SCADA data."
    if not has_log:
        txt += " This export has no alarm log, so the trip rules could not run."
    if n < 4:
        txt += f" With only {n} turbines there is no peer comparison, so only very large changes can be flagged."
    return txt


def rating_method_long() -> str:
    from . import rules
    pr, red = rules.PARAMS, {"persist": rules.RED_PERSIST, "rel": rules.RED_REL, "pump": rules.RED_PUMP_BAR, "mult": rules.RED_TRIP_MULT}
    return (f"Computed at each month-end from data up to that date (latest month-end shown here). AMBER when: the full-load "
            f"gear-oil pump pressure (median of the last 15 days) is >= {pr['pump']['a']:g} bar above the turbine's own baseline "
            f"(days 60-365 before) AND >= {pr['pump']['r']:g} robust standard deviations above the other turbines' rise that month; "
            f">= {pr['oil_trips']['n']} oil-system trip episodes in 6 months; >= {pr['pitch_trips']['n']} pitch trip episodes in "
            f"6 months; an ambient-temperature or wind-speed sensor drifting vs the fleet over the last 3 months (1.5 °C, 5%); or a "
            f"monitored sensor frozen on more than 2% of the last 90 days. RED when the pump rise is >= {red['pump']:g} bar; or a trip rule has held {red['persist']} month-ends in a row "
            f"with >= {red['mult']:g}x the amber count and a trip in the last 30 days; or two independent systems are amber at once. "
            "Shown as notes but never colour-setting, because they had no reliable lead on events in the validation: low "
            "availability (it describes the past), model-based abnormal-day rates (oil, pitch, main bearing, power curve) and "
            "missing data. A trip episode merges trips less than 24 h apart.")


def validation_text() -> str:
    from . import rules
    c = rules.CALIBRATION.get("validation")
    if not c:
        return "No calibration file found (run scripts/calibrate_flags.py)."
    fam = c["families_test"]
    o = c["overall_test"]
    parts = []
    for f, lab in (("pump", "pump build-up → oil trip or service stop"), ("oil_trips", "repeat oil trips → further oil trips"),
                   ("pitch_trips", "repeat pitch trips → further pitch trips")):
        s = fam.get(f, {})
        if s.get("flagged"):
            parts.append(f"{lab}: {_pc(s['hit_rate'])} of {s['flagged']} flagged turbine-months vs {_pc(s['expected'])} by chance")
    ov = o.get("pooled", {})
    share = c.get("test_share", {})
    return (f"Retrospective check on Kelmarsh and Penmanshiel (21 turbines). Thresholds selected on {rules.CALIBRATION['selected_on']}, "
            f"checked on {rules.CALIBRATION['checked_on']} ({c['families_test']['pump']['rows']} turbine-months): " + "; ".join(parts)
            + f". Any amber or red: {_pc(ov['amber_or_red']['hit_rate'])} followed by a logged event within 90 days vs "
            f"{_pc(ov['amber_or_red']['expected'])} by chance (recall {_pc(ov['amber_or_red']['recall'])}); red alone "
            f"{_pc(ov['red']['hit_rate'])} vs {_pc(ov['red']['expected'])} on only {ov['red']['flagged']} turbine-months, so red marks "
            f"strength and persistence more than a higher probability. Held-out ratings: {_pc(share.get('GREEN'))} green, "
            f"{_pc(share.get('AMBER'))} amber, {_pc(share.get('RED'))} red. Consecutive months overlap, so the effective "
            "sample is much smaller than the row counts; details in `reports/fleet_proof/calibration.md`.")


def for_html(md: str) -> str:
    out, prev = [], ""
    for line in md.split("\n"):
        m = re.match(r"^( *)([-*]|\d+\.) ", line)
        if m:
            ind = len(m.group(1))
            line = " " * (ind * 2) + line[ind:]
            if prev.strip() and not re.match(r"^ *([-*]|\d+\.) ", prev):
                out.append("")
        out.append(line)
        prev = line
    return "\n".join(out)


def write(md: str, out: Path, title: str, pdf: bool = True) -> dict:
    import markdown
    out.mkdir(parents=True, exist_ok=True)
    (out / "condition_report.md").write_text(md, encoding="utf-8")
    html = markdown.markdown(for_html(md), extensions=["tables", "sane_lists"])
    html = re.sub(r"<strong>(RED|AMBER|GREEN)</strong>", r'<span class="flag-\1">\1</span>', html)
    doc = f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title><style>{CSS}</style></head><body>{html}</body></html>"
    hp = out / "condition_report.html"
    hp.write_text(doc, encoding="utf-8")
    res = {"md": str(out / "condition_report.md"), "html": str(hp), "pdf": None}
    if not pdf:
        return res
    chrome = os.environ.get("WINDML_CHROME") or next(
        (c for c in ("google-chrome", "chromium", "chromium-browser", "chrome") if shutil.which(c)), None)
    if not chrome:
        res["pdf_note"] = "no Chrome/Chromium found (set WINDML_CHROME); PDF skipped"
        return res
    pp = out / "condition_report.pdf"
    subprocess.run([chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pp}", hp.resolve().as_uri()], check=True, capture_output=True, timeout=180)
    res["pdf"] = str(pp)
    return res

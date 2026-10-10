"""Figures and summary tables for the sample condition report (reads reports/condition_report/tables/)."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / "reports/condition_report/tables"
F = ROOT / "reports/condition_report/figures"
F.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 150,
                     "savefig.bbox": "tight", "axes.titleweight": "bold", "axes.titlesize": 10})
NAME = {"kelmarsh": "Kelmarsh", "penmanshiel": "Penmanshiel"}
C = {"oil": "#c0504d", "pitch": "#4f81bd"}


def heat(ax, piv, fmt, cmap, vmin, vmax, title):
    im = ax.imshow(piv.values, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
    ax.set_xticks(range(piv.shape[1]), piv.columns); ax.set_yticks(range(piv.shape[0]), piv.index)
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            v = piv.values[i, j]
            if np.isfinite(v):
                ax.text(j, i, fmt(v), ha="center", va="center", fontsize=7)
    ax.set_title(title)
    for s in ax.spines.values(): s.set_visible(False)
    return im


def main():
    ty = pd.read_csv(T / "turbine_year.csv")
    # 1 availability heatmap
    fig, axs = plt.subplots(1, 2, figsize=(10, 4.6), gridspec_kw={"width_ratios": [6, 14]})
    for ax, farm in zip(axs, ["kelmarsh", "penmanshiel"]):
        p = ty[ty.farm == farm].pivot(index="year", columns="turbine_id", values="avail_time") * 100
        heat(ax, p, lambda v: f"{v:.0f}" if v < 99.5 else "", "RdYlGn", 88, 100, f"{NAME[farm]}: technical availability (%)")
    fig.text(0.5, -0.02, "Time not in a fault or maintenance stop, per calendar year. Blank cells are >= 99.5%. "
             "Penmanshiel 2016 is the partial first year; PEN01-10 have no 2024 data.", ha="center", fontsize=7.5)
    fig.savefig(F / "fig1_availability.png"); plt.close(fig)

    # 2 downtime and lost production by cause
    dt = pd.read_csv(T / "downtime_by_cause.csv"); lo = pd.read_csv(T / "lost_by_cause.csv")
    fig, axs = plt.subplots(1, 2, figsize=(10.5, 4.4), gridspec_kw={"wspace": 0.55})
    summ = []
    for ax, farm in zip(axs, ["kelmarsh", "penmanshiel"]):
        h = dt[dt.farm == farm].groupby("cause")["hours"].sum()
        l = lo[lo.farm == farm].groupby("cause")["lost_mwh"].sum()
        s = pd.DataFrame({"hours": h, "lost_mwh": l}).fillna(0)
        s["farm"] = farm; summ.append(s.reset_index())
        s = s[s.index != "other"].sort_values("hours").tail(12)
        col = ["#c0504d" if c.startswith("fault") else "#9aa5b1" for c in s.index]
        ax.barh(s.index, s["hours"], color=col)
        for i, (hh, mw) in enumerate(zip(s["hours"], s["lost_mwh"])):
            ax.text(hh, i, f" {hh:,.0f} h / {mw:,.0f} MWh", va="center", fontsize=7)
        ax.set_xlim(0, s["hours"].max() * 1.75)
        ax.set_title(f"{NAME[farm]}: downtime by cause, all years"); ax.set_xlabel("turbine-hours (first-cause, no double counting)")
    fig.text(0.5, -0.03, "Red = fault stops by component; grey = maintenance (manual stops, mostly unattributed), grid, weather, "
             "curtailment, routine. Labels: hours / lost production (SCADA counter).", ha="center", fontsize=7.5)
    fig.savefig(F / "fig2_downtime_by_cause.png"); plt.close(fig)
    pd.concat(summ).to_csv(T / "downtime_lost_summary.csv", index=False)

    # 3 trip seasonality per 100 turbine-months
    ep = pd.read_csv(T / "trip_episodes.csv", parse_dates=["start"])
    op = pd.read_csv(T / "oil_pressure_monthly.csv")
    op = op[(op["n"] > 0) & (op["month"] >= "2017-01")]; op["mo"] = op["month"].str[5:7].astype(int)
    ep = ep[ep["year"] >= 2017]  # first operating year (2016) left out: Penmanshiel commissioning skews it
    expo = op.groupby(["farm", "mo"]).size()
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.4), sharey=True)
    seas = []
    for ax, farm in zip(axs, ["kelmarsh", "penmanshiel"]):
        for k, off in (("oil", -0.2), ("pitch", 0.2)):
            e = ep[(ep.farm == farm) & (ep.kind == k)]
            # count only episodes in turbine-months that are in the exposure table
            e = e.assign(month=e["start"].dt.strftime("%Y-%m"))
            e = e.merge(op[op.farm == farm][["turbine_id", "month"]], on=["turbine_id", "month"])
            cnt = e.groupby(e["start"].dt.month).size().reindex(range(1, 13), fill_value=0)
            rate = cnt / expo.loc[farm].reindex(range(1, 13)) * 100
            seas.append(pd.DataFrame({"farm": farm, "kind": k, "month": range(1, 13), "episodes": cnt.values,
                                      "turbine_months": expo.loc[farm].reindex(range(1, 13)).values, "per100": rate.values}))
            ax.bar(np.arange(1, 13) + off, rate.values, width=0.4, color=C[k], label=f"{k} trip episodes")
        ax.set_xticks(range(1, 13), list("JFMAMJJASOND")); ax.set_title(f"{NAME[farm]}: trips by month (2017 to 2024)")
        ax.set_ylabel("episodes per 100 turbine-months"); ax.legend(frameon=False)
    fig.savefig(F / "fig3_trip_seasonality.png"); plt.close(fig)
    pd.concat(seas).to_csv(T / "trip_seasonality.csv", index=False)

    # 4 trip episodes per turbine-year
    fig, axs = plt.subplots(1, 2, figsize=(10, 4.6), gridspec_kw={"width_ratios": [6, 14]})
    for ax, farm in zip(axs, ["kelmarsh", "penmanshiel"]):
        e = ep[ep.farm == farm]
        allt = sorted(ty[ty.farm == farm].turbine_id.unique()); yrs = list(range(2016, 2025))
        p = e.pivot_table(index="year", columns="turbine_id", values="n_trips", aggfunc="size", fill_value=0).reindex(index=yrs, columns=allt, fill_value=0).astype(float)
        have = ty[ty.farm == farm].pivot(index="year", columns="turbine_id", values="rows").reindex(index=yrs, columns=allt)
        p = p.where(have.notna())
        po = e[e.kind == "oil"].pivot_table(index="year", columns="turbine_id", values="n_trips", aggfunc="size").reindex(index=p.index, columns=allt).fillna(0)
        pp = e[e.kind == "pitch"].pivot_table(index="year", columns="turbine_id", values="n_trips", aggfunc="size").reindex(index=p.index, columns=allt).fillna(0)
        cm = plt.get_cmap("Oranges").copy(); cm.set_bad("#e6e6e6")
        im = ax.imshow(np.ma.masked_invalid(p.values), cmap=cm, vmin=0, vmax=16, aspect="auto")
        ax.set_xticks(range(len(allt)), allt, rotation=90); ax.set_yticks(range(len(p.index)), p.index)
        for i in range(p.shape[0]):
            for j in range(p.shape[1]):
                o_, q_ = int(po.values[i, j]), int(pp.values[i, j])
                if np.isfinite(p.values[i, j]) and o_ + q_: ax.text(j, i, f"{o_}/{q_}", ha="center", va="center", fontsize=6.5)
        ax.set_title(f"{NAME[farm]}: oil / pitch trip episodes")
        for s in ax.spines.values(): s.set_visible(False)
    fig.text(0.5, -0.04, "Cell text = oil-system episodes / pitch episodes (trips < 24 h apart merged). Shading = total. Grey = no data.", ha="center", fontsize=7.5)
    fig.savefig(F / "fig4_trips_turbine_year.png"); plt.close(fig)

    # 5 Penmanshiel full-load pump pressure
    o = pd.read_csv(T / "oil_pressure_monthly.csv"); o["t"] = pd.to_datetime(o["month"])
    o = o[o.t >= "2017-01-01"]
    hi = {"PEN02": "#c0504d", "PEN04": "#e46c0a", "PEN05": "#8064a2", "PEN14": "#1f497d", "PEN15": "#9bbb59"}
    fig, ax = plt.subplots(figsize=(10, 3.8))
    for tid, g in o[o.farm == "penmanshiel"].groupby("turbine_id"):
        ax.plot(g.t, g.pump, color=hi.get(tid, "#c8c8c8"), lw=1.4 if tid in hi else 0.8, label=tid if tid in hi else None,
                zorder=3 if tid in hi else 1)
    for d, lab, yy in (("2023-01-26", "PEN15 oil change (particles)", 11.9), ("2023-03-17", "PEN05/06 filter-choked inspection", 11.5),
                       ("2023-11-27", "fleet gear-oil exchange (Nov-Dec 2023)", 12.3), ("2024-04-16", "PEN15 gearbox exchange", 11.1)):
        ax.axvline(pd.Timestamp(d), color="k", lw=0.6, ls=":"); ax.text(pd.Timestamp(d) - pd.Timedelta(days=10), yy, lab, fontsize=6.5, ha="right", va="center",
                                                                        bbox=dict(fc="white", ec="none", pad=0.5))
    ax.set_ylim(3.5, 12.6); ax.set_ylabel("bar (monthly median, >1000 kW)")
    ax.set_title("Penmanshiel: gear-oil pump pressure at full load (unit-corrected)")
    ax.legend(frameon=False, ncol=5, loc="upper left", fontsize=7.5)
    ax.text(pd.Timestamp("2019-12-15"), 4.3, "PEN09/PEN10 2018-02 to 2019-11:\nboth read about half (cause not logged)", fontsize=6.5)
    fig.savefig(F / "fig5_pen_pump_pressure.png"); plt.close(fig)

    # 6 Kelmarsh model-error drift
    meta = pd.concat(pd.read_csv(f) for f in (ROOT / "data/nbm_years").glob("kelmarsh_*_meta.csv"))
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.4), sharey=True)
    pal = {"KEL01": "#4f81bd", "KEL02": "#9bbb59", "KEL03": "#8064a2", "KEL04": "#c0504d", "KEL05": "#f79646", "KEL06": "#4bacc6"}
    for ax, tg, lab in zip(axs, ["gear_oil_temp_c", "main_bearing_front_temp_c"], ["gear-oil temperature", "main bearing (front)"]):
        m = meta[meta.target == tg].pivot_table(index="test_year", columns="turbine_id", values="mae_test_healthy")
        for tid in m.columns:
            ax.plot(m.index, m[tid], marker="o", ms=3, lw=1.6 if tid == "KEL04" else 1, label=tid,
                    color=pal[tid])
        ax.set_title(f"Kelmarsh: {lab} model error"); ax.set_xlabel("test year"); ax.set_ylabel("MAE on healthy rows (deg C)")
        ax.axvline(2023, color="k", lw=0.6, ls=":")
    axs[0].legend(frameon=False, ncol=3, fontsize=7)
    axs[1].text(2023.05, axs[1].get_ylim()[1] * 0.97, "KEL04 gearbox\nexchange Jul 2023", fontsize=7, va="top")
    fig.savefig(F / "fig6_kelmarsh_drift.png"); plt.close(fig)

    # 7 fault-stop rate by ambient temperature
    ft = pd.read_csv(T / "faults_by_ambient_temp.csv")
    grp = {"converter": "converter", "pitch": "pitch", "gearbox": "gearbox"}
    ft["g"] = ft["component"].map(grp).fillna("other")
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.4), sharey=True)
    temp_tab = []
    order = ["(-30, 0]", "(0, 5]", "(5, 10]", "(10, 15]", "(15, 20]", "(20, 25]", "(25, 30]", "(30, 45]"]
    for ax, farm in zip(axs, ["kelmarsh", "penmanshiel"]):
        f = ft[ft.farm == farm]
        hours = f.drop_duplicates(["turbine_id", "tbin"]).groupby("tbin")["hours"].sum().reindex(order)
        n = f.groupby(["tbin", "g"])["n"].sum().unstack().reindex(order).fillna(0)
        r = n.div(hours, axis=0) * 1000
        tt = n.assign(hours=hours).reset_index(); tt["farm"] = farm; temp_tab.append(tt)
        x = np.arange(len(order))
        for i, (g, col) in enumerate([("gearbox", "#c0504d"), ("pitch", "#4f81bd"), ("converter", "#9bbb59")]):
            ax.bar(x + (i - 1) * 0.27, r[g], width=0.27, color=col, label=g)
        ax.set_xticks(x, ["<0", "0-5", "5-10", "10-15", "15-20", "20-25", "25-30", ">30"])
        ax.set_xlabel("ambient temperature (deg C)"); ax.set_ylabel("fault stops per 1,000 h")
        ax.set_title(f"{NAME[farm]}: fault-stop rate by ambient temperature"); ax.legend(frameon=False)
        for j, hh in enumerate(hours.values):
            ax.text(j, ax.get_ylim()[1] * 0.98 if False else 0, "", fontsize=6)
    fig.text(0.5, -0.04, "Exposure = all 10-min rows at that temperature. Bins above 25 C have little exposure: Kelmarsh > 30 C is "
             "4 stops in 1,122 turbine-hours (all 19 Jul 2022); Penmanshiel 25-30 C is 2 stops in 1,714 h.", ha="center", fontsize=7.5)
    fig.savefig(F / "fig7_faults_by_temperature.png"); plt.close(fig)
    pd.concat(temp_tab).to_csv(T / "faults_by_temp_summary.csv", index=False)


if __name__ == "__main__":
    main()

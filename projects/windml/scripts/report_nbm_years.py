"""Figures + markdown tables for reports/nbm_all_years.md (run after eval_nbm_years.py)."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pyarrow.parquet as pq
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts"))
from windml import nbm_years as ny
import eval_nbm_years as ev

REP = ROOT / "reports"; FIG = REP / "figures"; FIG.mkdir(exist_ok=True)
DATA = ROOT / "data/processed/all_years"; NB = ROOT / "data/nbm_years"
chosen = json.loads((REP / "nbmy_chosen.json").read_text())

# 1. pressure unit switch
fig, axes = plt.subplots(2, 1, figsize=(11, 6), sharex=True)
for farm, tid, c in [("kelmarsh", "KEL01", "C0"), ("penmanshiel", "PEN01", "C1")]:
    l = pq.read_table(DATA / f"{farm}_scada_labeled.parquet", columns=["timestamp", "power_kw", "in_any_stop", "gear_oil_inlet_pressure_bar"],
                      filters=[("turbine_id", "==", tid)]).to_pandas()
    r = l[(l.power_kw > 100) & (~l.in_any_stop.astype(bool))]
    dm = r.set_index("timestamp").gear_oil_inlet_pressure_bar.resample("D").median()
    axes[0].plot(dm.index, dm.values, ".", ms=2, color=c, label=tid)
    axes[1].plot(dm.index, ny.normalize_pressure(dm).values, ".", ms=2, color=c, label=tid)
axes[0].set_yscale("log"); axes[0].set_ylabel("as logged (log scale)"); axes[0].set_title("Gear oil inlet pressure, daily median while producing: logged as bar in some periods, x100 (kPa) in others")
axes[1].set_ylabel("normalized to bar"); axes[0].legend(markerscale=5); axes[1].legend(markerscale=5)
fig.tight_layout(); fig.savefig(FIG / "nbmy_oil_pressure_units.png", dpi=110); plt.close(fig)

# 2. detection vs chance by year
BY = pd.read_csv(REP / "nbmy_by_year.csv")
b = BY[BY.horizon_d == 30]
fig, axes = plt.subplots(2, 2, figsize=(13, 7))
for r, fault in enumerate(["gearbox", "pitch"]):
    for c, farm in enumerate(ev.FARMS):
        ax = axes[r, c]; x = b[(b.fault == fault) & (b.farm == farm)].sort_values("year")
        xs = np.arange(len(x))
        ax.bar(xs - 0.2, x.episodes, 0.2, color="lightgray", label="evaluable episodes")
        ax.bar(xs, x.detected, 0.2, color="C3", label="detected (alarm onset <=30 d before)")
        ax.bar(xs + 0.2, x.expected_chance, 0.2, color="C0", label="expected by season-matched chance")
        ax.set_xticks(xs); ax.set_xticklabels([f"{y}\n{'dev' if y <= 2020 else 'HELD-OUT'}" for y in x.year], fontsize=8)
        ax2 = ax.twinx(); ax2.plot(xs, x.fa_per_turbine_month, "k.--", label="false alarms / turbine-month"); ax2.set_ylim(0, max(1.5, x.fa_per_turbine_month.max() * 1.2))
        ax.set_title(f"{farm} {fault} ({chosen[fault]['variant']}, {chosen[fault]['subgroup']}, hl {chosen[fault]['halflife_h']} h, thr {chosen[fault]['thr']})", fontsize=9)
        if r == 0 and c == 0:
            ax.legend(fontsize=7, loc="upper left"); ax2.legend(fontsize=7, loc="upper right")
fig.suptitle("Selected setting (chosen on 2017-2020 only), episodes detected vs chance, by year", fontsize=11)
fig.tight_layout(); fig.savefig(FIG / "nbmy_detection_by_year.png", dpi=110); plt.close(fig)

# 3. superposed-epoch: selected score around held-out episodes vs control dates
rng = np.random.default_rng(0)
fig, axes = plt.subplots(2, 2, figsize=(13, 7), sharex=True)
for c, farm in enumerate(ev.FARMS):
    tids, grid, Z = ev.load_farm(farm)
    eps_all = ev.episodes(farm)
    for r, fault in enumerate(["gearbox", "pitch"]):
        ch = chosen[fault]
        Zv = Z if ch["variant"] == "raw" else ev.fleet(Z)
        subs = {ch["subgroup"]: ny.SUBGROUPS[fault][ch["subgroup"]]}
        S = ev.group_scores({t: Zv[t] for t in subs[ch["subgroup"]]}, tids, ev.HALFLIVES[int(ch["halflife_h"])], subs)[ch["subgroup"]]
        np.save(NB / f"selscore_{farm}_{fault}.npy", S)
        ep = eps_all[(eps_all.component == fault) & eps_all.year.isin(ev.HELD) & eps_all.turbine_id.isin(tids)]
        rel = np.arange(-60 * 24, 14 * 24 + 1)  # hours
        def traces(starts):
            out = []
            for tid, s in starts:
                i = tids.index(tid); k = grid.get_indexer([s.floor("10min")])[0]
                if k < 0: continue
                idx = k + rel * 6
                ok = (idx >= 0) & (idx < len(grid))
                tr = np.full(len(rel), np.nan); tr[ok] = S[i, idx[ok]]
                out.append(tr)
            return np.array(out)
        T = traces(list(zip(ep.turbine_id, ep.start.dt.tz_convert("UTC").dt.tz_localize(None).dt.tz_localize("UTC"))))
        # control: random dates in held-out years, same turbines, no episode of any type within 60 days after
        ctrl = []
        allst = eps_all.groupby("turbine_id").start.apply(list).to_dict()
        while len(ctrl) < max(200, 4 * len(ep)):
            tid = rng.choice(ep.turbine_id.values); y = rng.choice(ev.HELD)
            s = pd.Timestamp(f"{y}-01-01", tz="UTC") + pd.Timedelta(minutes=10 * int(rng.integers(0, 52000)))
            if any(pd.Timedelta(0) <= (x - s) <= pd.Timedelta(days=74) or pd.Timedelta(0) <= (s - x) <= pd.Timedelta(days=14) for x in allst.get(tid, [])):
                continue
            ctrl.append((tid, s))
        C = traces(ctrl)
        ax = axes[r, c]; d = rel / 24
        for M, col, lab in [(T, "C3", f"before held-out {fault} episodes (n={len(T)})"), (C, "C0", f"random control dates (n={len(C)})")]:
            with np.errstate(all="ignore"):
                ax.plot(d, np.nanmedian(M, 0), color=col, label=lab)
                ax.fill_between(d, np.nanpercentile(M, 25, 0), np.nanpercentile(M, 75, 0), color=col, alpha=0.2)
                ax.plot(d, np.nanpercentile(M, 90, 0), color=col, ls=":", lw=1)
        ax.axvline(0, color="k", lw=1); ax.axhline(ch["thr"], color="gray", ls="--", lw=1)
        ax.set_title(f"{farm} {fault}: selected score, median/IQR (dotted = 90th pct)", fontsize=9); ax.legend(fontsize=7)
        ax.set_xlabel("days relative to episode start / control date")
    del Z
fig.tight_layout(); fig.savefig(FIG / "nbmy_superposed_epoch_heldout.png", dpi=110); plt.close(fig)

# 4. healthy MAE by test year
M = pd.concat(pd.read_csv(f) for f in NB.glob("*_meta.csv"))
M = M[M.skipped.isna() | (M.skipped == "")]
M = M[M.target.isin(ny.NBM_TARGETS)]
mt = M.groupby(["farm", "target", "test_year"]).mae_test_healthy.median().unstack().round(2)
mt.to_csv(REP / "nbmy_mae_by_year.csv")
fig, axes = plt.subplots(1, 2, figsize=(13, 4.5), sharey=False)
for ax, farm in zip(axes, ev.FARMS):
    x = mt.loc[farm]
    for t in x.index:
        ax.plot(x.columns, x.loc[t], marker="o", label=t)
    ax.set_title(f"{farm}: healthy test MAE (median over turbines) by test year"); ax.set_ylabel("MAE (deg C / bar / deg)")
axes[1].legend(fontsize=7, ncol=2)
fig.tight_layout(); fig.savefig(FIG / "nbmy_mae_by_year.png", dpi=110); plt.close(fig)
print("figures written")

# 5. turbine-level ranking check (does time-in-alarm in dev years predict which turbines fail in held-out years?)
rows = []
for farm in ev.FARMS:
    files = sorted(f for f in NB.glob(f"{farm}_*.parquet") if f.stem.count("_") == 1)
    tids = [f.stem.split("_")[1] for f in files]
    p0 = [pd.read_parquet(f, columns=["timestamp"]) for f in files]
    grid = pd.date_range(min(p.timestamp.min() for p in p0), max(p.timestamp.max() for p in p0), freq="10min")
    eps = ev.episodes(farm)
    for fault in ["gearbox", "pitch"]:
        S = np.load(NB / f"selscore_{farm}_{fault}.npy"); thr = chosen[fault]["thr"]
        g = eps[eps.component == fault]
        dev = (grid.year >= 2017) & (grid.year <= 2020); held = grid.year >= 2021
        for i, t in enumerate(tids):
            with np.errstate(all="ignore"):
                rows.append(dict(farm=farm, fault=fault, turbine_id=t,
                                 frac_time_alarm_dev=round(float(np.nanmean(S[i, dev] > thr)), 4),
                                 frac_time_alarm_heldout=round(float(np.nanmean(S[i, held] > thr)), 4),
                                 episodes_dev=int(((g.turbine_id == t) & g.year.between(2017, 2020)).sum()),
                                 episodes_heldout=int(((g.turbine_id == t) & (g.year >= 2021)).sum())))
R = pd.DataFrame(rows); R.to_csv(REP / "nbmy_turbine_ranking.csv", index=False)
rk = []
for (farm, fault), x in R.groupby(["farm", "fault"]):
    sp = lambda a, b: round(float(np.corrcoef(a.rank(), b.rank())[0, 1]), 3) if a.nunique() > 1 and b.nunique() > 1 else np.nan
    rk.append(dict(farm=farm, fault=fault, turbines=len(x), spearman_alarmtime_dev_vs_episodes_heldout=sp(x.frac_time_alarm_dev, x.episodes_heldout),
                   spearman_episodes_dev_vs_episodes_heldout=sp(x.episodes_dev.astype(float), x.episodes_heldout)))
RK = pd.DataFrame(rk)

# 6. markdown tables
S = pd.read_csv(REP / "nbmy_selected.csv"); G = pd.read_csv(REP / "nbmy_grid.csv")
cols = ["fault", "farm", "split", "subset", "episodes", "detected", "expected_chance", "p_value", "median_lead_days", "fa_per_turbine_month", "turbine_months"]
T = ["### Table 1. Selected settings (chosen on 2017-2020, pooled farms, H = 30 d)\n", pd.DataFrame(chosen).T.to_markdown(),
     "\n### Table 2. Selected setting, H = 30 days\n", S[S.horizon_d == 30][cols].to_markdown(index=False),
     "\n### Table 3. Selected setting, H = 7 days\n", S[(S.horizon_d == 7) & (S.subset == "all")][cols].to_markdown(index=False),
     "\n### Table 4. By test year (selected setting, H = 30 d)\n",
     BY[BY.horizon_d == 30][["fault", "farm", "split", "year", "episodes", "detected", "expected_chance", "p_value", "median_lead_days", "fa_per_turbine_month"]].to_markdown(index=False)]
gs = []
for (farm, fault, split), x in G[(G.horizon_d == 30) & (G.episodes > 0)].groupby(["farm", "fault", "split"]):
    b = x.sort_values("p_value").iloc[0]
    gs.append(dict(farm=farm, fault=fault, split=split, configs=len(x), n_p_below_005=int((x.p_value < 0.05).sum()),
                   expected_by_chance_if_independent=round(0.05 * len(x), 1), min_p=b.p_value,
                   best_config=f"{b.variant}/{b.subgroup}/hl{b.halflife_h}/thr{b.thr}", best_detected=f"{int(b.detected)}/{int(b.episodes)} (exp {b.expected_chance})"))
T += ["\n### Table 5. Whole grid (168 settings per farm and fault, H = 30 d): how many settings reach p < 0.05\n", pd.DataFrame(gs).to_markdown(index=False),
      "\n### Table 6. Turbine-level ranking check (Spearman rank correlation)\n", RK.to_markdown(index=False),
      "\n### Table 7. Healthy test-period MAE by test year (median over turbines; deg C, bar, or deg)\n", mt.reset_index().to_markdown(index=False)]
(REP / "nbmy_tables.md").write_text("\n".join(T) + "\n")
print("tables written")

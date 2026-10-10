"""Figures + markdown tables for reports/trip_shortterm.md (run after eval_trip.py)."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from windml import config as cfg  # noqa: E402
sys.path.insert(0, str(ROOT / "scripts"))
import eval_trip as et
REP = cfg.REPORTS_DIR; FIG = REP / "figures"; P = cfg.TRIP_PREDS_DIR
R = pd.read_csv(REP / "trip_metrics.csv"); T = pd.read_csv(REP / "trip_primary_tests.csv")
SEL = json.loads((REP / "trip_selected.json").read_text())
COL = {"season": "#999999", "history": "#1f77b4", "sensors": "#ff7f0e", "sensors_nbm": "#d62728", "sensors_hist": "#2ca02c", "sensors_nbm_hist": "#9467bd"}

# 1. held-out PR-AUC
h = R[(R.split == "heldout") & (R.farm == "pooled")]
fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
for ax, fault in zip(axes, et.FAULTS):
    x = h[h.fault == fault]
    for j, fs in enumerate(et.FSETS):
        v = x[x.feature_set == fs].sort_values("horizon_h")
        ax.bar(np.arange(3) + (j - 2.5) * 0.13, v.pr_auc, 0.13, color=COL[fs], label=fs)
    pv = x[x.feature_set == "season"].sort_values("horizon_h").prevalence
    for k, p in enumerate(pv):
        ax.plot([k - 0.42, k + 0.42], [p, p], "k--", lw=1, label="prevalence (random)" if k == 0 else None)
    ax.set_xticks(range(3)); ax.set_xticklabels([f"{H} h" for H in et.HS]); ax.set_ylabel("PR-AUC, held-out 2021-2024 (pooled farms)")
    ax.set_title(f"{fault} trips"); ax.set_yscale("log")
axes[0].legend(fontsize=7)
fig.tight_layout(); fig.savefig(FIG / "trip_prauc_heldout.png", dpi=110); plt.close(fig)

# 2. PR curves (48 h)
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
for ax, fault in zip(axes, et.FAULTS):
    s = SEL[f"{fault}_48"]
    for fs in ["season", "history", s["no_history"], s["with_history"]]:
        d = pd.read_parquet(P / f"{fault}_48_{fs}.parquet"); d = d[d.year.isin(et.HELD) & d.score.notna()]
        o = np.argsort(-d.score.to_numpy(), kind="stable"); y = d.y.to_numpy()[o]
        tp = np.cumsum(y); prec = tp / np.arange(1, len(y) + 1); rec = tp / max(tp[-1], 1)
        ax.plot(rec, prec, color=COL[fs], label=f"{fs} (AP {et.ap(d.score.to_numpy(), d.y.to_numpy()):.3f})")
    ax.axhline(d.y.mean(), color="k", ls="--", lw=1, label=f"prevalence {d.y.mean():.4f}")
    ax.set_xlabel("recall"); ax.set_ylabel("precision"); ax.set_yscale("log"); ax.set_ylim(1e-3, 1); ax.set_title(f"{fault} trip within 48 h, held-out 2021-2024")
    ax.legend(fontsize=7)
fig.tight_layout(); fig.savefig(FIG / "trip_pr_curves_48h.png", dpi=110); plt.close(fig)

# 3. episode detection vs chance at the alarm budget
fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
for ax, fault in zip(axes, et.FAULTS):
    labels, det, exs, ext, n = [], [], [], [], []
    for H in et.HS:
        s = SEL[f"{fault}_{H}"]
        for fs in ["season", "history", s["no_history"], s["with_history"]]:
            r = h[(h.fault == fault) & (h.horizon_h == H) & (h.feature_set == fs)].iloc[0]
            labels.append(f"{H}h\n{fs.replace('sensors', 'sens').replace('_', '+')}"); det.append(r.detected); exs.append(r.expected_chance)
            ext.append(r.expected_turbine_matched); n.append(r.episodes)
    xs = np.arange(len(labels))
    ax.bar(xs - 0.27, det, 0.27, color="C3", label="detected")
    ax.bar(xs, exs, 0.27, color="C0", label="expected: season-matched (farm)")
    ax.bar(xs + 0.27, ext, 0.27, color="C2", label="expected: turbine-matched")
    ax.set_xticks(xs); ax.set_xticklabels(labels, fontsize=6.5); ax.set_title(f"{fault} trip episodes, held-out (n = {n[0]}/{n[4]}/{n[8]} for 24/48/72 h)")
    ax.legend(fontsize=7)
fig.suptitle("Trip episodes with an alarm in the H hours before the trip, at a budget of one alarm event per turbine-month (held-out 2021-2024)", fontsize=10)
fig.tight_layout(); fig.savefig(FIG / "trip_episode_detection.png", dpi=110); plt.close(fig)

# 4. importance (48 h picks)
fig, axes = plt.subplots(2, 2, figsize=(13, 8))
for r_, fault in enumerate(et.FAULTS):
    for c_, kind in enumerate(["no_history", "with_history"]):
        fs = SEL[f"{fault}_48"][kind]
        im = pd.read_csv(P / f"{fault}_48_{fs}_importance.csv").head(15)[::-1]
        ax = axes[r_, c_]; ax.barh(im.feature, im.gain / im.gain.sum(), color=COL[fs]); ax.set_title(f"{fault} 48 h, {fs}: top-15 gain share", fontsize=9)
        ax.tick_params(labelsize=7)
fig.tight_layout(); fig.savefig(FIG / "trip_importance_48h.png", dpi=110); plt.close(fig)

# 5. per-year held-out PR-AUC (48 h)
rows = []
for fault in et.FAULTS:
    s = SEL[f"{fault}_48"]
    for fs in ["season", "history", s["no_history"], s["with_history"]]:
        d = pd.read_parquet(P / f"{fault}_48_{fs}.parquet"); d = d[d.score.notna() & d.year.between(2017, 2024)]
        for y, g in d.groupby("year"):
            rows.append(dict(fault=fault, feature_set=fs, year=y, positives=int(g.y.sum()), prevalence=round(g.y.mean(), 5),
                             pr_auc=round(et.ap(g.score.to_numpy(), g.y.to_numpy()), 4) if g.y.sum() else np.nan))
PY = pd.DataFrame(rows); PY.to_csv(REP / "trip_prauc_by_year_48h.csv", index=False)
fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
for ax, fault in zip(axes, et.FAULTS):
    x = PY[PY.fault == fault]
    for fs, g in x.groupby("feature_set"):
        ax.plot(g.year, g.pr_auc, marker="o", color=COL[fs], label=fs)
    pv = x.groupby("year").prevalence.first(); ax.plot(pv.index, pv.values, "k--", label="prevalence")
    ax.axvspan(2020.5, 2024.5, color="gold", alpha=0.15, label="held-out")
    ax.set_yscale("log"); ax.set_title(f"{fault} trip within 48 h: PR-AUC by test year"); ax.legend(fontsize=7)
fig.tight_layout(); fig.savefig(FIG / "trip_prauc_by_year_48h.png", dpi=110); plt.close(fig)

# tables
R["event_precision"] = (R.true_alarm_events / R.alarm_events).round(3)
R["false_alarm_events_per_turbine_month"] = ((R.alarm_events - R.true_alarm_events) / R.turbine_months).round(3)
h = R[(R.split == "heldout") & (R.farm == "pooled")]
# episode subsets: exclude episodes with a previous trip of the same type in the 7 days before (repeat-trip clusters)
import sys as _s; _s.path.insert(0, str(ROOT / "src"))
from windml import nbm_years as ny, trip_features as tf
E = pd.read_csv(REP / "trip_heldout_episodes.csv", parse_dates=["start"])
allep = []
for f in ["kelmarsh", "penmanshiel"]:
    ev = pd.read_parquet(cfg.ALL_YEARS_DIR / f"{f}_events.parquet")
    for k in et.FAULTS:
        allep.append(tf.trip_episodes(tf.trips(ev, k)).assign(farm=f, fault=k))
allep = pd.concat(allep).sort_values(["fault", "turbine_id", "start"])
allep["prev_gap_d"] = allep.groupby(["fault", "turbine_id"]).start.diff().dt.total_seconds() / 86400
E = E[E.evaluable].merge(allep[["fault", "turbine_id", "start", "prev_gap_d"]], on=["fault", "turbine_id", "start"], how="left")
sub = []
for (fault, H, fs), g in E.groupby(["fault", "horizon_h", "feature_set"]):
    for name, m in (("all", np.ones(len(g), bool)), ("no_prior_trip_7d", (g.prev_gap_d.isna() | (g.prev_gap_d > 7)).to_numpy())):
        x = g[m]; k = int(x.detected.sum())
        sub.append(dict(fault=fault, horizon_h=H, feature_set=fs, subset=name, episodes=len(x), detected=k,
                        expected_season_matched=round(x.chance.fillna(0).sum(), 2), expected_turbine_matched=round(x.chance_turbine.fillna(0).sum(), 2),
                        p_turbine_matched=float(f"{ny.poisson_binomial_sf(k, x.chance_turbine.fillna(0).to_numpy()):.3g}"),
                        median_lead_h=x.loc[x.detected, "lead_h"].median()))
SUB = pd.DataFrame(sub); SUB.to_csv(REP / "trip_heldout_episode_subsets.csv", index=False)
cols = ["fault", "horizon_h", "feature_set", "positives", "prevalence", "pr_auc", "precision_at_budget", "alarm_events", "event_precision",
        "false_alarm_events_per_turbine_month", "episodes", "detected",
        "expected_chance", "p_episode", "expected_turbine_matched", "p_episode_turbine_matched", "median_lead_h"]
md = ["### Table A. Primary tests on held-out 2021-2024 (pooled farms; PR-AUC difference, one-sided block bootstrap over turbine-months; Bonferroni alpha = 0.05/12 = 0.0042)\n",
      T.to_markdown(index=False),
      "\n### Table B. Held-out 2021-2024, pooled farms, all feature sets\n", h[cols].to_markdown(index=False),
      "\n### Table C. Held-out 2021-2024 by farm (48 h)\n", R[(R.split == "heldout") & (R.farm != "pooled") & (R.horizon_h == 48)][["farm"] + cols].to_markdown(index=False),
      "\n### Table B2. Held-out episode detection, all episodes vs episodes without a same-type trip in the previous 7 days (pooled farms)\n",
      SUB.to_markdown(index=False),
      "\n### Table D. Dev 2017-2020, pooled farms (used for selection)\n", R[(R.split == "dev") & (R.farm == "pooled")][cols[:8]].to_markdown(index=False),
      "\n### Table E. PR-AUC by test year (48 h)\n", PY.pivot_table(index=["fault", "feature_set"], columns="year", values="pr_auc").round(4).reset_index().to_markdown(index=False)]
(REP / "trip_tables.md").write_text("\n".join(md) + "\n")
print("done")

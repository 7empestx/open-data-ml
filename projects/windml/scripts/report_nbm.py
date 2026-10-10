"""Figures + markdown tables for the NBM baseline (reads data/nbm and reports/nbm_*.csv)."""
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from windml import nbm

D, REP, FIG = ROOT / "data/nbm", ROOT / "reports", ROOT / "reports/figures"
FIG.mkdir(exist_ok=True, parents=True)
SHORT = {"gear_oil_temp_c": "gear oil", "gear_oil_inlet_temp_c": "gear oil inlet", "main_bearing_front_temp_c": "main brg front",
         "main_bearing_rear_temp_c": "main brg rear", "rotor_bearing_temp_c": "rotor brg", "gen_bearing_front_temp_c": "gen brg front",
         "gen_bearing_rear_temp_c": "gen brg rear"}


def panel(ax, s, e, title, thr=3.0):
    w = s[(s["timestamp"] >= e["start"] - pd.Timedelta(days=30)) & (s["timestamp"] <= e["start"] + pd.Timedelta(days=2))]
    for t in nbm.TARGETS:
        if f"ewma_{t}" in w:
            ax.plot(w["timestamp"], w[f"ewma_{t}"], lw=0.8, label=SHORT[t])
    if w[[c for c in w.columns if c.startswith("ewma_")]].notna().sum().sum() == 0:
        ax.text(0.5, 0.5, "not evaluable: no scored data before this episode\n(its 30-day pre-fault window covers the only training month)",
                ha="center", va="center", fontsize=7, transform=ax.transAxes)
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(title, fontsize=8)
        return
    ax.axhline(thr, color="k", ls="--", lw=0.8)
    ax.axvline(e["start"], color="r", lw=1.2)
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    ax.set_title(title, fontsize=8)
    ax.tick_params(labelsize=6)
    ax.set_ylabel("EWMA z (12 h)", fontsize=7)


def fig_farm(farm, setting, fname, title):
    eps = pd.read_csv(REP / f"nbm_episodes_{farm}.csv", parse_dates=["start", "end"])
    n = len(eps)
    cols = 3 if n > 2 else n
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(4.2 * cols, 2.6 * rows), squeeze=False)
    for ax, (_, e) in zip(axes.ravel(), eps.iterrows()):
        f = D / (f"{farm}_{e['turbine_id']}_nbm.parquet" if setting == "in_farm" else f"crossfarm_{e['turbine_id']}_scores.parquet")
        s = pd.read_parquet(f)
        hw = " (heatwave)" if e["heatwave_20220719"] else ""
        panel(ax, s, e, f"{e['turbine_id']} ep{e['major_episode']} {e['start']:%Y-%m-%d} code {e['codes']} {e['component']}{hw}")
    for ax in axes.ravel()[n:]:
        ax.axis("off")
    axes.ravel()[0].legend(fontsize=5, ncol=2)
    fig.suptitle(title + "\nflat segments = score held during stops/ineligible rows; red = episode start; dashed = alarm threshold 3", fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / fname, dpi=130)
    plt.close(fig)
    return FIG / fname


def fig_timeline():
    eps = pd.read_csv(REP / "nbm_episodes_kelmarsh.csv", parse_dates=["start", "end"])
    fig, axes = plt.subplots(6, 1, figsize=(11, 9), sharex=True)
    for ax, tid in zip(axes, [f"KEL0{i}" for i in range(1, 7)]):
        s = pd.read_parquet(D / f"kelmarsh_{tid}_nbm.parquet")
        ax.plot(s["timestamp"], s["score_ewma"], lw=0.5, color="tab:blue")
        ax.axhline(3.0, color="k", ls="--", lw=0.7)
        for _, e in eps[eps["turbine_id"] == tid].iterrows():
            ax.axvspan(e["start"] - pd.Timedelta(days=30), e["start"], color="orange", alpha=0.2)
            ax.axvline(e["start"], color="r", lw=1)
        ax.set_ylabel(tid, fontsize=7); ax.tick_params(labelsize=6)
        ax.set_ylim(-3, 12)
    axes[0].set_title("Kelmarsh 2022: turbine score = max over 7 targets of EWMA residual z (forward-chained; Jan = training only). "
                      "Orange = 30 days before a major-fault episode, red = episode start, dashed = threshold 3", fontsize=7)
    fig.tight_layout(); fig.savefig(FIG / "nbm_score_timeline_kelmarsh.png", dpi=120); plt.close(fig)
    return FIG / "nbm_score_timeline_kelmarsh.png"


paths = [fig_farm("kelmarsh", "in_farm", "nbm_prefault_residuals_kelmarsh.png", "Kelmarsh 2022: EWMA residual z per target, 30 days before each major-fault episode (in-farm, forward-chained)"),
         fig_farm("penmanshiel", "in_farm", "nbm_prefault_residuals_penmanshiel.png", "Penmanshiel 2021 H1: in-farm models"),
         fig_farm("penmanshiel", "cross", "nbm_prefault_residuals_crossfarm.png", "Penmanshiel 2021 H1: Kelmarsh-trained models (cross-farm, offset calibrated on Jan)"),
         fig_timeline()]
for p in paths:
    print(p)

# ------------------------------------------------------------------ markdown tables
S = pd.read_csv(REP / "nbm_summary.csv")
EPD = pd.read_csv(REP / "nbm_episode_detection.csv")
MAE = pd.read_csv(REP / "nbm_mae.csv")
CM = pd.read_csv(REP / "nbm_crossfarm_mae.csv")
T = []
main = S[(S.score == "score_ewma") & (S.thr == 3.0)]
cols = ["farm", "setting", "horizon", "subset", "episodes", "detected_onset", "expected_by_chance_onset", "expected_seasonal_onset",
        "p_value_seasonal_onset", "detected_active", "median_lead_onset_days", "false_alarms_per_turbine_month"]
T.append("### Table A. Primary setting: EWMA (12 h half-life) of residual z, alarm when max over targets > 3\n")
T.append(main[cols].rename(columns={"detected_onset": "detected (onset)", "expected_by_chance_onset": "chance (flat)",
                                    "expected_seasonal_onset": "chance (season-matched)", "p_value_seasonal_onset": "p (season-matched)",
                                    "detected_active": "detected (any active alarm)", "median_lead_onset_days": "median lead (d)",
                                    "false_alarms_per_turbine_month": "false alarms / turbine-month"}).to_markdown(index=False))
T.append("\n### Table B. Sensitivity: all score types and thresholds, 30-day horizon, all episodes\n")
sb = S[(S.horizon == 30) & (S.subset == "all")]
T.append(sb[["farm", "setting", "score", "thr", "episodes", "detected_onset", "expected_seasonal_onset", "p_value_seasonal_onset",
             "false_alarms_per_turbine_month"]].to_markdown(index=False))
T.append("\n### Table C. Per-episode result (EWMA > 3, 30-day horizon)\n")
pe = EPD[(EPD.score == "score_ewma") & (EPD.thr == 3.0) & (EPD.horizon == 30)]
T.append(pe[["setting", "turbine_id", "episode", "start", "codes", "component", "heatwave", "window_scored_days", "detected_onset",
             "lead_onset_days", "detected_active"]].to_markdown(index=False))
T.append("\n### Table D. Healthy test-period MAE (deg C), forward-chained, mean over turbines\n")
mt = MAE.groupby(["farm", "target", "model"]).mae_healthy_test.mean().unstack().round(2).reset_index()
T.append(mt.to_markdown(index=False))
T.append("\n### Table E. Cross-farm MAE on Penmanshiel healthy rows Feb-Jun (deg C), Kelmarsh-trained model, mean over turbines\n")
ct = CM.groupby("target")[["mae_raw", "mae_after_offset", "calib_offset"]].mean().round(2).reset_index()
ip = MAE[(MAE.farm == "penmanshiel") & (MAE.model == "lgbm")].groupby("target").mae_healthy_test.mean().round(2).rename("in_farm_lgbm_mae")
T.append(ct.merge(ip, left_on="target", right_index=True).to_markdown(index=False))
(REP / "nbm_tables.md").write_text("\n".join(T) + "\n")
print(REP / "nbm_tables.md")

"""Evaluate all-years NBM scores against gearbox and pitch major-fault episodes.

Settings grid (per fault type): variant {raw, fleet} x EWMA half-life {6, 24, 72 h} x signal subgroup x threshold {2,3,4,5,6,8,10}.
Selection: on DEV years (2017-2020) pooled over both farms, among settings with false alarms <= 1 per turbine-month and
>= 3 detections, pick the lowest season-matched p-value. That single setting per fault type is then reported on the
HELD-OUT years (2021-2024). Horizon H = 30 days (primary) and 7 days (secondary, same selected setting).
Writes reports/nbmy_grid.csv, reports/nbmy_selected.csv, reports/nbmy_heldout_episodes.csv, reports/nbmy_by_year.csv,
data/nbm_years/scores_<farm>_<fault>.parquet (selected score, for plots)."""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from windml import nbm_years as ny

NB = ROOT / "data/nbm_years"; DATA = ROOT / "data/processed/all_years"; REP = ROOT / "reports"
import os
FARMS = os.environ.get("NBMY_FARMS", "kelmarsh,penmanshiel").split(",")
DEV, HELD = [2017, 2018, 2019, 2020], [2021, 2022, 2023, 2024]
HALFLIVES = {6: 36, 24: 144, 72: 432}
THRS = [2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0]
FA_MAX, MIN_DET = 1.0, 3
SEASON_DAYS = 30
TARGETS = list(ny.NBM_TARGETS) + list(ny.DIRECT)


def episodes(farm):
    e = pd.read_parquet(DATA / f"{farm}_events.parquet")
    m = e[e["is_major_fault"]].sort_values("start")
    g = m.groupby(["turbine_id", "major_episode"]).agg(start=("start", "min"), component=("component", "first"),
                                                       codes=("code", lambda s: ",".join(sorted(set(map(str, s))))),
                                                       n_events=("code", "size")).reset_index()
    g["start"] = pd.to_datetime(g["start"], utc=True)
    g = g.sort_values(["turbine_id", "start"])
    prev = g.groupby("turbine_id")["start"].shift(1)
    g["isolated"] = (prev.isna()) | ((g["start"] - prev) > pd.Timedelta(days=60))
    g["year"] = g["start"].dt.year
    return g.reset_index(drop=True)


def load_farm(farm):
    files = sorted(NB.glob(f"{farm}_*.parquet")); files = [f for f in files if not f.stem.startswith(("scores_",)) and f.stem.count("_") == 1]
    tids = [f.stem.split("_")[1] for f in files]
    parts = [pd.read_parquet(f) for f in files]
    t0 = min(p["timestamp"].min() for p in parts); t1 = max(p["timestamp"].max() for p in parts)
    grid = pd.date_range(t0, t1, freq="10min")
    Z = {t: np.full((len(tids), len(grid)), np.nan, np.float32) for t in TARGETS}
    for i, p in enumerate(parts):
        idx = grid.get_indexer(p["timestamp"])
        for t in TARGETS:
            Z[t][i, idx] = p[f"z_{t}"].to_numpy(np.float32)
    return tids, grid, Z


def fleet(Z):
    out = {}
    for t, M in Z.items():
        cnt = np.sum(~np.isnan(M), axis=0)
        with np.errstate(all="ignore"):
            med = np.nanmedian(M, axis=0)
        med[cnt < 3] = np.nan
        out[t] = M - med[None, :]
    return out


def group_scores(Zv, tids, hl_steps, subgroups):
    """EWMA per target (held across gaps), side transform, max over targets in each subgroup -> {sub: (n_turb, N)}."""
    E = {}
    for t, M in Zv.items():
        A = np.full_like(M, np.nan)
        for i in range(M.shape[0]):
            A[i] = ny.ewma_held(pd.Series(M[i]), hl_steps).to_numpy()
        E[t] = np.abs(A) if ny.SIDE[t] == "abs" else A
    out = {}
    for sub, ts in subgroups.items():
        with np.errstate(all="ignore"):
            out[sub] = np.nanmax(np.stack([E[t] for t in ts]), axis=0)
    return out


def scored_days(Zv, subgroups, day_idx, n_days):
    """(n_turb, n_days) bool: day has >= 36 rows with any valid raw z in the subgroup."""
    out = {}
    for sub, ts in subgroups.items():
        valid = np.zeros_like(Zv[ts[0]], dtype=bool)
        for t in ts:
            valid |= ~np.isnan(Zv[t])
        cnt = np.zeros((valid.shape[0], n_days), np.int32)
        for i in range(valid.shape[0]):
            cnt[i] = np.bincount(day_idx[valid[i]], minlength=n_days)
        out[sub] = cnt >= 36
    return out


def evaluate(onsets, sdays, eps, tids, days, H, years):
    """onsets: list per turbine of np.datetime64 arrays. Returns (episode rows, fa_count, turbine_months)."""
    n_days = len(days)
    tix = {t: i for i, t in enumerate(tids)}
    oc = np.zeros((len(tids), n_days), np.int32)
    for i, o in enumerate(onsets):
        if len(o):
            di = np.searchsorted(days.values, o.astype("datetime64[ns]"), side="right") - 1
            np.add.at(oc[i], di, 1)
    ocum = np.concatenate([np.zeros((len(tids), 1), np.int32), np.cumsum(oc, axis=1)], axis=1)
    scum = np.concatenate([np.zeros((len(tids), 1), np.int32), np.cumsum(sdays, axis=1)], axis=1)
    Hn = np.timedelta64(H, "D")
    rows = []
    sel = eps[eps["year"].isin(years) & eps["turbine_id"].isin(tids)]
    for _, e in sel.iterrows():
        i = tix[e["turbine_id"]]
        s = np.datetime64(e["start"].tz_convert(None))
        sd = int(np.searchsorted(days.values, s, side="right") - 1)
        evaluable = sd - H >= 0 and (scum[i, sd] - scum[i, sd - H]) >= H / 2
        o = onsets[i]
        inwin = o[(o >= s - Hn) & (o < s)] if len(o) else o
        det = len(inwin) > 0
        lead = float((s - inwin.min()) / np.timedelta64(1, "h") / 24) if det else np.nan
        # season-matched chance: all turbines, window ends within +-30 days of the episode day
        hits = valid = 0
        for k in range(-SEASON_DAYS, SEASON_DAYS + 1):
            d = sd + k
            if d - H < 0 or d > n_days:
                continue
            ok = (scum[:, d] - scum[:, d - H]) >= H / 2
            valid += ok.sum(); hits += ((ocum[:, d] - ocum[:, d - H]) > 0)[ok].sum()
        rows.append(dict(turbine_id=e["turbine_id"], episode=int(e["major_episode"]), start=e["start"], year=int(e["year"]),
                         codes=e["codes"], isolated=bool(e["isolated"]), evaluable=bool(evaluable),
                         detected=bool(det and evaluable), lead_days=lead if evaluable else np.nan,
                         chance=float(hits / valid) if valid else np.nan))
    # false alarms: onsets in `years` not within H days before an episode of this fault type on that turbine
    fa, tm = 0, 0.0
    yr_of_day = days.year.values
    for i, t in enumerate(tids):
        o = onsets[i]
        if len(o):
            oy = pd.DatetimeIndex(o).year.values
            o = o[np.isin(oy, years)]
            st = eps.loc[eps["turbine_id"] == t, "start"].dt.tz_convert(None).values.astype("datetime64[ns]")
            for x in o:
                if not np.any((st > x) & (st - x <= Hn)):
                    fa += 1
        tm += sdays[i][np.isin(yr_of_day, years)].sum() / 30.44
    return pd.DataFrame(rows), fa, tm


def summarize(ep, fa, tm):
    ev = ep[ep["evaluable"]] if len(ep) else ep
    n = len(ev); k = int(ev["detected"].sum()) if n else 0
    exp = float(ev["chance"].sum()) if n else np.nan
    return dict(episodes_total=len(ep), episodes=n, detected=k, rate=round(k / n, 3) if n else np.nan,
                expected_chance=round(exp, 2) if n else np.nan,
                p_value=round(ny.poisson_binomial_sf(k, ev["chance"].to_numpy()), 4) if n else np.nan,
                median_lead_days=round(float(ev.loc[ev["detected"], "lead_days"].median()), 2) if k else np.nan,
                false_alarms=fa, turbine_months=round(tm, 1), fa_per_turbine_month=round(fa / tm, 3) if tm else np.nan)


def main():
    grid_rows, ONS, SD, META = [], {}, {}, {}
    for farm in FARMS:
        tids, grid, Z = load_farm(farm)
        eps_all = episodes(farm)
        days = pd.DatetimeIndex(grid.floor("D").unique())
        day_idx = np.searchsorted(days.values, grid.floor("D").values)
        gts = grid.values
        META[farm] = (tids, days, eps_all)
        for variant in ["raw", "fleet"]:
            Zv = Z if variant == "raw" else fleet(Z)
            for fault, subs in ny.SUBGROUPS.items():
                eps = eps_all[eps_all["component"] == fault]
                sd = scored_days(Zv, subs, day_idx, len(days))
                for sub in subs:
                    SD[(farm, variant, fault, sub)] = sd[sub]
                for hl, steps in HALFLIVES.items():
                    S = group_scores({t: Zv[t] for t in set(sum(subs.values(), []))}, tids, steps, subs)
                    for sub in subs:
                        for thr in THRS:
                            ons = [ny.alarm_onsets(gts, S[sub][i], thr) for i in range(len(tids))]
                            ONS[(farm, fault, variant, hl, sub, thr)] = ons
                            for H in (30, 7):
                                for split, yrs in (("dev", DEV), ("heldout", HELD)):
                                    ep, fa, tm = evaluate(ons, sd[sub], eps, tids, days, H, yrs)
                                    grid_rows.append(dict(farm=farm, fault=fault, variant=variant, halflife_h=hl, subgroup=sub,
                                                          thr=thr, horizon_d=H, split=split, **summarize(ep, fa, tm)))
                    del S
                print(farm, variant, fault, "done", flush=True)
            del Zv
        del Z
    G = pd.DataFrame(grid_rows)
    G.to_csv(REP / "nbmy_grid.csv", index=False)

    def run(farm, fault, cfg, H, yrs):
        variant, hl, sub, thr = cfg
        tids, days, eps_all = META[farm]
        return evaluate(ONS[(farm, fault, variant, hl, sub, thr)], SD[(farm, variant, fault, sub)],
                        eps_all[eps_all["component"] == fault], tids, days, H, yrs)

    sel_rows, held_eps, by_year, chosen = [], [], [], {}
    for fault, subs in ny.SUBGROUPS.items():
        cands = []
        for variant in ["raw", "fleet"]:
            for hl in HALFLIVES:
                for sub in subs:
                    for thr in THRS:
                        cfg = (variant, hl, sub, thr)
                        parts = [run(f, fault, cfg, 30, DEV) for f in FARMS]
                        s = summarize(pd.concat([p[0] for p in parts]), sum(p[1] for p in parts), sum(p[2] for p in parts))
                        cands.append(dict(variant=variant, halflife_h=hl, subgroup=sub, thr=thr, **s))
        C = pd.DataFrame(cands)
        C.to_csv(REP / f"nbmy_dev_pooled_{fault}.csv", index=False)
        ok = C[(C.fa_per_turbine_month <= FA_MAX) & (C.detected >= MIN_DET)]
        best = (ok if len(ok) else C).sort_values(["p_value", "fa_per_turbine_month"]).iloc[0]
        cfg = (best["variant"], int(best["halflife_h"]), best["subgroup"], float(best["thr"]))
        chosen[fault] = dict(variant=cfg[0], halflife_h=cfg[1], subgroup=cfg[2], thr=cfg[3], n_candidates=len(C), n_eligible=len(ok))
        for H in (30, 7):
            for split, yrs in (("dev", DEV), ("heldout", HELD)):
                allep, allfa, alltm = [], 0, 0.0
                for f in FARMS:
                    ep, fa, tm = run(f, fault, cfg, H, yrs)
                    base = dict(fault=fault, farm=f, split=split, horizon_d=H, variant=cfg[0], halflife_h=cfg[1], subgroup=cfg[2], thr=cfg[3])
                    sel_rows.append({**base, "subset": "all", **summarize(ep, fa, tm)})
                    sel_rows.append({**base, "subset": "isolated", **summarize(ep[ep["isolated"]] if len(ep) else ep, fa, tm)})
                    allep.append(ep.assign(farm=f)); allfa += fa; alltm += tm
                    if split == "heldout":
                        held_eps.append(ep.assign(farm=f, fault=fault, horizon_d=H))
                    for y in yrs:
                        epy, fay, tmy = run(f, fault, cfg, H, [y])
                        by_year.append(dict(fault=fault, farm=f, split=split, horizon_d=H, year=y, **summarize(epy, fay, tmy)))
                pe = pd.concat(allep)
                base = dict(fault=fault, farm="pooled", split=split, horizon_d=H, variant=cfg[0], halflife_h=cfg[1], subgroup=cfg[2], thr=cfg[3])
                sel_rows.append({**base, "subset": "all", **summarize(pe, allfa, alltm)})
                sel_rows.append({**base, "subset": "isolated", **summarize(pe[pe["isolated"]], allfa, alltm)})
    S = pd.DataFrame(sel_rows)
    S.to_csv(REP / "nbmy_selected.csv", index=False)
    pd.concat(held_eps).to_csv(REP / "nbmy_heldout_episodes.csv", index=False)
    pd.DataFrame(by_year).to_csv(REP / "nbmy_by_year.csv", index=False)
    (REP / "nbmy_chosen.json").write_text(json.dumps(chosen, indent=1, default=str))
    print(json.dumps(chosen, indent=1, default=str))
    print(S[S.subset == "all"].to_string())


if __name__ == "__main__":
    main()

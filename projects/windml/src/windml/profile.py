"""Schema / data-quality profiling to markdown."""
from __future__ import annotations
import re
import numpy as np
import pandas as pd


def unit_from_name(c: str) -> str:
    m = re.search(r"\(([^()]*)\)\s*$", str(c))
    return m.group(1) if m else ""


def profile(df: pd.DataFrame, name: str, *, time_col=None, entity_col=None, units: dict | None = None,
            notes: list[str] | None = None, max_cols: int = 400) -> str:
    units = units or {}
    L = [f"# Schema: {name}", ""]
    L += [f"- Rows: {len(df):,}", f"- Columns: {df.shape[1]}"]
    if entity_col and entity_col in df:
        vc = df[entity_col].value_counts().sort_index()
        L.append(f"- Entities ({entity_col}): {len(vc)} -> " + ", ".join(f"{k}: {v:,}" for k, v in vc.items()))
    if time_col and time_col in df:
        t = df[time_col]
        L.append(f"- Time span: {t.min()} to {t.max()}")
        grp = df.groupby(entity_col)[time_col] if entity_col and entity_col in df else None
        d = (grp.diff() if grp is not None else t.sort_values().diff()).dropna()
        if len(d):
            L.append(f"- Sampling interval: median {d.median()}, most common {d.mode().iloc[0]}, "
                     f"share at mode {float((d == d.mode().iloc[0]).mean()) * 100:.1f}%, max gap {d.max()}")
    tot_missing = float(df.isna().mean().mean() * 100)
    L.append(f"- Overall missing cells: {tot_missing:.2f}%")
    for n in notes or []:
        L.append(f"- {n}")
    L += ["", "| column | dtype | unit | missing % | min | max |", "|---|---|---|---|---|---|"]
    for c in list(df.columns)[:max_cols]:
        s = df[c]
        mn = mx = ""
        if pd.api.types.is_numeric_dtype(s) or pd.api.types.is_datetime64_any_dtype(s):
            if s.notna().any():
                mn, mx = s.min(), s.max()
                if isinstance(mn, (float, np.floating)):
                    mn, mx = f"{mn:.4g}", f"{mx:.4g}"
        L.append(f"| {c} | {s.dtype} | {units.get(c, unit_from_name(c))} | {s.isna().mean() * 100:.2f} | {mn} | {mx} |")
    if df.shape[1] > max_cols:
        L.append(f"| ... {df.shape[1] - max_cols} more columns omitted | | | | | |")
    return "\n".join(L) + "\n"

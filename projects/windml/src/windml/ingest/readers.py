"""File readers: CSV (any delimiter, decimal comma, comment/preamble lines), Excel (one or many sheets), parquet."""
from __future__ import annotations
import csv
import fnmatch
import glob as _glob
import re
from pathlib import Path
import pandas as pd


def expand(files: list[dict], raw_dir: Path) -> list[tuple[Path, dict]]:
    out = []
    for f in files:
        pat = f["glob"]
        p = pat if Path(pat).is_absolute() else str(raw_dir / pat)
        hits = sorted(Path(x) for x in _glob.glob(p, recursive=True))
        # exclude: glob patterns matched against the path relative to raw_dir (e.g. "*/scada_2021_wt11-15/*")
        ex = f.get("exclude") or []
        rel = lambda h: str(h.relative_to(raw_dir)) if h.is_relative_to(raw_dir) else str(h)
        out += [(h, f) for h in hits if h.is_file() and not any(fnmatch.fnmatch(rel(h), e) for e in ex)]
    return out


def file_format(path: Path, fmt: str) -> str:
    if fmt != "auto":
        return fmt
    suf = path.suffix.lower()
    if suf in (".xlsx", ".xlsm", ".xls"):
        return "excel"
    if suf in (".parquet", ".pq"):
        return "parquet"
    return "csv"


def _head_lines(path: Path, encoding: str, n: int = 200) -> list[str]:
    with open(path, encoding=encoding, errors="replace") as fh:
        return [next(fh, "") for _ in range(n)]


def header_index(lines: list[str], header_match: str | None, header_row: int) -> int:
    if header_match:
        rx = re.compile(header_match)
        for i, line in enumerate(lines):
            if rx.search(line):
                return i
        raise ValueError(f"no line matches header_match {header_match!r} in the first {len(lines)} lines")
    return int(header_row or 0)


def sniff_delimiter(lines: list[str]) -> str:
    sample = "".join(lines[:50])
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
    except csv.Error:
        counts = {d: sample.count(d) for d in ",;\t|"}
        return max(counts, key=counts.get)


def read_csv(path: Path, opts: dict, usecols=None) -> pd.DataFrame:
    lines = _head_lines(path, opts["encoding"])
    hi = header_index(lines, opts.get("header_match"), opts.get("header_row", 0))
    delim = opts["delimiter"]
    if delim in (None, "auto"):
        delim = sniff_delimiter(lines[hi:])
    if delim == "\\t":
        delim = "\t"
    kw = dict(sep=delim, skiprows=hi, header=0, encoding=opts["encoding"], decimal=opts.get("decimal", "."),
              na_values=opts.get("na_values"), keep_default_na=True, low_memory=False)
    if opts.get("thousands"):
        kw["thousands"] = opts["thousands"]
    if usecols is not None:
        kw["usecols"] = lambda c: c in usecols
    return pd.read_csv(path, **kw)


def read_excel(path: Path, opts: dict) -> pd.DataFrame:
    sheets = opts.get("sheets", 0)
    sheet_name = None if sheets == "all" else sheets
    data = pd.read_excel(path, sheet_name=sheet_name, header=opts.get("header_row", 0))
    if isinstance(data, dict):
        return pd.concat([d.assign(_sheet=str(k)) for k, d in data.items()], ignore_index=True)
    return data.assign(_sheet=str(sheets))


def read_any(path: Path, src: dict, usecols: set[str] | None = None) -> pd.DataFrame:
    fmt = file_format(path, src["format"])
    if fmt == "csv":
        df = read_csv(path, src["csv"], usecols)
    elif fmt == "excel":
        df = read_excel(path, src["excel"])
    else:
        cols = None
        if usecols is not None:
            import pyarrow.parquet as pq
            names = pq.ParquetFile(path).schema.names
            cols = [c for c in names if c in usecols]
        df = pd.read_parquet(path, columns=cols)
    return df.copy().assign(_file=str(path.name))  # copy() de-fragments very wide frames


def sample_text(path: Path, encoding: str = "utf-8", n: int = 200) -> str:
    return "".join(_head_lines(path, encoding, n))


def read_sample(path: Path, nrows: int = 20_000) -> tuple[pd.DataFrame, dict]:
    """Best-effort read of an unknown export for auto-suggest. Returns (frame, detected csv/excel options)."""
    fmt = file_format(path, "auto")
    if fmt == "excel":
        xl = pd.ExcelFile(path)
        sheets = xl.sheet_names
        # header row = first row that is (nearly) as wide as the widest of the first 30 rows (skips title rows)
        head = xl.parse(sheets[0], header=None, nrows=30)
        width = head.notna().sum(axis=1)
        hr = int(next((i for i, w in enumerate(width) if w >= 0.8 * width.max()), 0))
        pre = " ".join(str(v) for v in head.iloc[:hr].stack().tolist())
        df = pd.concat([xl.parse(s, nrows=nrows, header=hr).assign(_sheet=s) for s in sheets[:20]], ignore_index=True)
        return df, {"format": "excel", "sheets": "all" if len(sheets) > 1 else sheets[0], "n_sheets": len(sheets),
                    "header_row": hr, "preamble": pre}
    if fmt == "parquet":
        return pd.read_parquet(path).head(nrows), {"format": "parquet"}
    enc = "utf-8"
    with open(path, "rb") as fh:
        raw = fh.read(200_000)
    if raw.startswith(b"\xef\xbb\xbf"):
        enc = "utf-8-sig"
    else:
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError as e:
            if e.start < len(raw) - 4:  # not just a character cut at the sample boundary
                enc = "latin-1"
    lines = _head_lines(path, enc)
    # header = first line (after leading '#' preamble) whose delimiter count matches the data rows below it
    delim = sniff_delimiter([ln for ln in lines if ln.strip() and not ln.startswith("#")][:50] or lines)
    # count fields with the csv module so quoted names containing the delimiter ("Wind speed, Minimum (m/s)") count once
    counts = [len(next(csv.reader([ln], delimiter=delim), [])) - 1 if ln.strip() else 0 for ln in lines]
    data_cnt = pd.Series([c for c in counts if c > 0]).mode().iloc[0] if any(counts) else 0
    hi = next((i for i, c in enumerate(counts) if c == data_cnt), 0)
    header_match = None
    if hi > 0:
        first = next(csv.reader([lines[hi]], delimiter=delim), [""])[0]
        header_match = "^" + re.escape(lines[hi][:lines[hi].find(first) + len(first)].strip()[:40]) + (re.escape(delim) if len(first) <= 40 else "")
    body = "".join(lines[hi + 1:hi + 60])
    # decimal comma: with ';' or tab delimiter and numbers like 12,5
    decimal = "," if delim != "," and re.search(r"(?<![\d.])-?\d+,\d+(?![\d,])", body) and not re.search(r"\d\.\d+[;\t]", body) else "."
    thousands = "." if decimal == "," and re.search(r"\d{1,3}\.\d{3},\d", body) else None
    preamble = "".join(lines[:hi])
    tz_m = re.search(r"(?im)^#?\s*time\s*zone\s*[:=]\s*([A-Za-z_/+\-0-9]+)", "".join(lines[:hi]))
    opts = {"format": "csv", "preamble": preamble.strip(), "preamble_timezone": tz_m.group(1) if tz_m else None, "delimiter": delim, "decimal": decimal, "thousands": thousands, "encoding": enc,
            "header_match": header_match, "header_row": hi}
    kw = dict(sep=delim, skiprows=hi, header=0, encoding=enc, decimal=decimal, nrows=nrows, low_memory=False,
              na_values=["NaN", "nan", "NA", "N/A", "", "-", "#N/A"])
    if thousands:
        kw["thousands"] = thousands
    return pd.read_csv(path, **kw), opts

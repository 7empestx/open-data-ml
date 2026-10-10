"""Download the Kelmarsh and Penmanshiel wind farm data (CC BY 4.0, Cubico Sustainable Investments) from Zenodo
and lay it out the way src/windml/greenbyte.py expects.

    $WINDML_RAW_DIR/kelmarsh-wind-scada/{zips/, scada_<year>/, Kelmarsh_WT_static.csv, ...}
    $WINDML_RAW_DIR/penmanshiel-wind-scada/{zips/, scada_<period>_<turbines>/, Penmanshiel_WT_static.csv, ...}

Every file is checked against the MD5 that Zenodo publishes. Re-running skips verified zips and finished folders.
The 2023/2024 exports repeat each timestamp up to ~80x; those zips (and all Penmanshiel zips) are extracted with
extract_dedup.py (most complete row per timestamp, conflicts logged). PMU and grid-meter zips are not needed and are skipped.

Usage:
  python scripts/download_wind_data.py                         # both farms, all years (~9.7 GB of zips, ~40 GB extracted)
  python scripts/download_wind_data.py --farms kelmarsh --years 2016-2018   # smoke-test subset (~535 MB)
  python scripts/download_wind_data.py --delete-zips           # delete each zip after extraction (saves ~9.7 GB)
Attribution: Cubico Sustainable Investments Ltd, Kelmarsh (doi:10.5281/zenodo.16807551) and
Penmanshiel (doi:10.5281/zenodo.16807304) wind farm data, CC BY 4.0."""
from __future__ import annotations
import argparse, hashlib, json, re, shutil, sys, time, urllib.request, zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts"))
from windml import config as cfg  # noqa: E402
import extract_dedup  # noqa: E402

RECORDS = {
    "kelmarsh": {"record": "16807551", "dir": "kelmarsh-wind-scada", "doi": "10.5281/zenodo.16807551"},
    "penmanshiel": {"record": "16807304", "dir": "penmanshiel-wind-scada", "doi": "10.5281/zenodo.16807304"},
}
API = "https://zenodo.org/api/records/{}"
UA = {"User-Agent": "open-data-ml windml downloader (+https://github.com/7empestx/open-data-ml)"}


def _years(spec):
    if not spec:
        return None
    out = set()
    for p in spec.split(","):
        a, _, b = p.partition("-")
        out.update(range(int(a), int(b or a) + 1))
    return out


def folder_name(farm: str, key: str) -> str | None:
    """Zip name -> extraction folder (same names as the original pipeline)."""
    if farm == "kelmarsh":
        m = re.match(r"Kelmarsh_SCADA_(\d{4})_\d+\.zip$", key)
        return f"scada_{m.group(1)}" if m else None
    if not key.startswith("Penmanshiel_SCADA_"):
        return None
    d = re.sub(r"^Penmanshiel_SCADA_", "", key[:-4])
    d = re.sub(r"_[0-9]+$", "", d)
    d = re.sub(r"WT_?01-10", "wt01-10", d); d = re.sub(r"WT_?11-15", "wt11-15", d)
    d = d.replace(" ", "_").lower()
    if d == "2021_wt11-15":  # full-2021 file (v4461); the older H1-2021 record is a different folder and is excluded
        d = "2021_wt11-15_v4461"
    return f"scada_{d}"


def md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def fetch(url: str, dest: Path, want_md5: str, size: int, tries: int = 5) -> None:
    if dest.exists() and dest.stat().st_size == size and md5(dest) == want_md5:
        print(f"  ok (cached) {dest.name}", flush=True); return
    tmp = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(1, tries + 1):
        try:
            t0 = time.time()
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r, open(tmp, "wb") as out:
                shutil.copyfileobj(r, out, 1 << 22)
            got = md5(tmp)
            if got != want_md5:
                raise IOError(f"md5 mismatch {got} != {want_md5}")
            tmp.rename(dest)
            print(f"  ok {dest.name} ({size / 1e6:.0f} MB in {time.time() - t0:.0f}s)", flush=True); return
        except Exception as e:  # Zenodo has no byte ranges: restart the file
            print(f"  retry {attempt}/{tries} {dest.name}: {e}", flush=True)
            time.sleep(min(60, 5 * attempt))
    raise SystemExit(f"FAILED {dest.name}")


def extract(zp: Path, dest: Path) -> None:
    if (dest / ".done").exists():
        return
    if dest.exists():
        shutil.rmtree(dest)
    year = int(re.search(r"(\d{4})", dest.name).group(1))
    print(f"  extract {zp.name} -> {dest.name}", flush=True)
    # Same rule as the original pipeline: every Penmanshiel zip and the padded Kelmarsh 2023/2024 exports go through
    # extract_dedup (collapses repeated timestamps); older Kelmarsh zips are plain extractions.
    if year >= 2023 or dest.parent.name.startswith("penmanshiel"):
        extract_dedup.extract(str(zp), str(dest), verbose=False)
    else:
        dest.mkdir(parents=True)
        with zipfile.ZipFile(zp) as z:
            for m in z.namelist():
                name = Path(m).name
                if name.endswith(".csv"):
                    with z.open(m) as s, open(dest / name, "wb") as d:
                        shutil.copyfileobj(s, d, 1 << 22)
    (dest / ".done").touch()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--farms", default="kelmarsh,penmanshiel")
    ap.add_argument("--years", default="", help='e.g. "2016-2017" (default: all)')
    ap.add_argument("--raw-dir", default=str(cfg.RAW_DIR))
    ap.add_argument("--jobs", type=int, default=2, help="parallel downloads")
    ap.add_argument("--delete-zips", action="store_true", help="delete each zip after it is extracted")
    a = ap.parse_args()
    years, raw = _years(a.years), Path(a.raw_dir)
    for farm in a.farms.split(","):
        rec = RECORDS[farm]
        base = raw / rec["dir"]; zdir = base / "zips"; zdir.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(urllib.request.Request(API.format(rec["record"]), headers=UA), timeout=60) as r:
            meta = json.load(r)
        lic = meta["metadata"].get("license", {}).get("id")
        print(f"{farm}: Zenodo record {rec['record']} (license {lic})", flush=True)
        jobs, small = [], []
        for f in meta["files"]:
            key, size, sum_ = f["key"], f["size"], f["checksum"].split(":", 1)[1]
            url = f["links"]["self"]
            if key.endswith(".csv") or key.endswith(".xlsx"):
                small.append((url, base / key, sum_, size))
                continue
            folder = folder_name(farm, key)
            if folder is None:
                continue  # PMU, grid meter, kmz
            if years and int(re.search(r"(\d{4})", folder).group(1)) not in years:
                continue
            jobs.append((url, zdir / key, sum_, size, base / folder))
        for url, dest, s, size in small:
            fetch(url, dest, s, size)
        print(f"  {len(jobs)} SCADA zips, {sum(j[3] for j in jobs) / 1e9:.2f} GB", flush=True)

        def one(j):
            url, zp, s, size, folder = j
            if not (folder / ".done").exists():
                fetch(url, zp, s, size)
                extract(zp, folder)
            else:
                print(f"  ok (extracted) {folder.name}", flush=True)
            if a.delete_zips and zp.exists():
                zp.unlink()
        with ThreadPoolExecutor(max(1, a.jobs)) as ex:
            list(ex.map(one, jobs))
        (base / "SOURCE.txt").write_text(
            f"Dataset: {farm.title()} wind farm data, Cubico Sustainable Investments Ltd\n"
            f"Zenodo record: {rec['record']} (doi:{rec['doi']})\nLicense: {lic} (CC BY 4.0, attribution required)\n"
            f"Retrieved: {date.today()} by projects/windml/scripts/download_wind_data.py (MD5-verified)\n")
    print("done:", raw, flush=True)


if __name__ == "__main__":
    main()

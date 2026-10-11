"""Download the SMARTEOLE wind-farm-control open dataset (Zenodo 7342466, Licence Ouverte 2.0) and extract the 1-min
SCADA file, the ReadMe and the coordinates into $WINDML_RAW_DIR/smarteole/ with a SOURCE.txt. ~150 MB zip, MD5 checked."""
import argparse, hashlib, sys, urllib.request, zipfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from windml import config as cfg  # noqa: E402

URL = "https://zenodo.org/records/7342466/files/SMARTEOLE-WFC-open-dataset.zip?download=1"
MD5 = "ffecd4b8cfe3ef3c744a5e0ff4a981c2"
KEEP = {"SMARTEOLE_WakeSteering_SCADA_1minData.csv", "SMARTEOLE_WakeSteering_ReadMe.xlsx", "SMARTEOLE_WakeSteering_Coordinates_staticData.csv"}
SOURCE = """Dataset: SMARTEOLE Wind Farm Control open dataset (7x Senvion MM82, Sole du Moulin Vieux, France), Feb-May 2020
Source: https://zenodo.org/records/7342466 (DOI 10.5281/zenodo.7342466)
License: Licence Ouverte / Open Licence 2.0 (Etalab), compatible with CC BY 4.0
Attribution: SMARTEOLE consortium / ENGIE Green, Zenodo DOI 10.5281/zenodo.7342466
Retrieved: {date}
"""


def md5(p: Path) -> str:
    h = hashlib.md5()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--raw-dir", default=str(cfg.RAW_DIR))
    a = ap.parse_args()
    dest = Path(a.raw_dir) / "smarteole"
    dest.mkdir(parents=True, exist_ok=True)
    z = dest / "SMARTEOLE-WFC-open-dataset.zip"
    if not z.exists() or md5(z) != MD5:
        print(f"downloading {URL}")
        urllib.request.urlretrieve(URL, z)
    if md5(z) != MD5:
        sys.exit("MD5 mismatch")
    with zipfile.ZipFile(z) as zf:
        for m in zf.namelist():
            if Path(m).name in KEEP:
                (dest / Path(m).name).write_bytes(zf.read(m))
    (dest / "SOURCE.txt").write_text(SOURCE.format(date=date.today().isoformat()))
    print(f"extracted to {dest}")


if __name__ == "__main__":
    main()

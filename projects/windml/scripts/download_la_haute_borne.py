"""Download the La Haute Borne (ENGIE) 2014-2015 SCADA extract that ships with NREL OpenOA.

Pinned to an OpenOA commit and checked against a SHA-256, extracted into $WINDML_RAW_DIR/la-haute-borne/ with a
SOURCE.txt. Data license: Licence Ouverte / Open Licence 2.0 (Etalab), compatible with CC BY 4.0; credit the ENGIE Group.
"""
import argparse, hashlib, sys, urllib.request, zipfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from windml import config as cfg  # noqa: E402

COMMIT = "9bfc7a3dc542b17bbfc06b692dbfb8b23c754975"
URL = f"https://github.com/NREL/OpenOA/raw/{COMMIT}/examples/data/la_haute_borne.zip"
SHA256 = "be5ea66a3355286e491f5618250dc83e85252a8cb337748d7ba19edc50df6138"
KEEP = {"la-haute-borne-data-2014-2015.csv", "la-haute-borne_asset_table.csv", "SCADA_data_description.csv", "plant_data.csv"}
SOURCE = f"""Dataset: La Haute Borne wind farm SCADA, 4x Senvion MM82 (ENGIE Group), 2014-2015 extract
Source: {URL}
  (distributed with NREL OpenOA, https://github.com/NREL/OpenOA, code BSD-3-Clause)
License: Licence Ouverte / Open Licence 2.0 (Etalab), https://www.etalab.gouv.fr/licence-ouverte-open-licence/
  designed to be compatible with CC BY 4.0
Attribution: ENGIE Group, La Haute Borne open data; via NREL OpenOA
Retrieved: {{date}}
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--raw-dir", default=str(cfg.RAW_DIR))
    a = ap.parse_args()
    dest = Path(a.raw_dir) / "la-haute-borne"
    dest.mkdir(parents=True, exist_ok=True)
    z = dest / "la_haute_borne.zip"
    if not z.exists() or hashlib.sha256(z.read_bytes()).hexdigest() != SHA256:
        print(f"downloading {URL}")
        urllib.request.urlretrieve(URL, z)
    got = hashlib.sha256(z.read_bytes()).hexdigest()
    if got != SHA256:
        sys.exit(f"SHA-256 mismatch: {got} != {SHA256}")
    with zipfile.ZipFile(z) as zf:
        for m in zf.namelist():
            # only the ENGIE files; the zip also carries ERA5/MERRA-2 reanalysis extracts under their own licenses
            if Path(m).name in KEEP:
                (dest / Path(m).name).write_bytes(zf.read(m))
    (dest / "SOURCE.txt").write_text(SOURCE.format(date=date.today().isoformat()))
    print(f"extracted to {dest}: {sorted(p.name for p in dest.glob('*.csv'))}")


if __name__ == "__main__":
    main()

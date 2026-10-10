"""Clean Kelmarsh 2022 and Penmanshiel H1 2021 SCADA -> data/processed/<farm>_scada_10min.parquet"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from windml import config as cfg  # noqa: E402
from windml import clean_wind as cw

for farm in ["kelmarsh", "penmanshiel"]:
    df, stats = cw.clean_farm(farm)
    out = cfg.PROCESSED_DIR / f"{farm}_scada_10min.parquet"
    df.to_parquet(out, index=False)
    (cfg.REPORTS_DIR / f"cleaning_stats_{farm}.json").write_text(json.dumps(stats, indent=1, default=str))
    print(farm, df.shape, "->", out)

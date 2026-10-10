"""Clean Kelmarsh 2022 and Penmanshiel H1 2021 SCADA -> data/processed/<farm>_scada_10min.parquet"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from windml import clean_wind as cw

for farm in ["kelmarsh", "penmanshiel"]:
    df, stats = cw.clean_farm(farm)
    out = ROOT / "data/processed" / f"{farm}_scada_10min.parquet"
    df.to_parquet(out, index=False)
    (ROOT / "reports" / f"cleaning_stats_{farm}.json").write_text(json.dumps(stats, indent=1, default=str))
    print(farm, df.shape, "->", out)

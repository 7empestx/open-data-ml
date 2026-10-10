import io
import py_compile
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def test_all_scripts_compile():
    for p in sorted((ROOT / "scripts").glob("*.py")) + sorted((ROOT / "src").rglob("*.py")):
        py_compile.compile(str(p), doraise=True)


def test_normalize_pressure():
    from windml import nbm_years as ny
    s = pd.Series([2.5, 250.0, np.nan, 7.0, 700.0])
    out = ny.normalize_pressure(s)
    assert np.allclose(out.fillna(-1), [2.5, 2.5, -1, 7.0, 7.0])


def test_zenodo_folder_names():
    from download_wind_data import folder_name
    assert folder_name("kelmarsh", "Kelmarsh_SCADA_2016_3082.zip") == "scada_2016"
    assert folder_name("kelmarsh", "Kelmarsh_PMU_4459.zip") is None
    assert folder_name("penmanshiel", "Penmanshiel_SCADA_2023_Q3 Q4_WT_01-10_5973.zip") == "scada_2023_q3_q4_wt01-10"
    assert folder_name("penmanshiel", "Penmanshiel_SCADA_2021_WT11-15_4461.zip") == "scada_2021_wt11-15_v4461"
    assert folder_name("penmanshiel", "Penmanshiel_Grid_4464.zip") is None


def test_extract_dedup(tmp_path):
    import extract_dedup
    data = "\n".join(["# header", "# Date and time,a,b",
                      "2023-01-01 00:00:00,1,2", "2023-01-01 00:00:00,NaN,NaN", "2023-01-01 00:00:00,1,NaN",
                      "2023-01-01 00:10:00,NaN,5", "2023-01-01 00:10:00,3,5"]) + "\n"
    zp = tmp_path / "x.zip"
    with zipfile.ZipFile(zp, "w") as z:
        z.writestr("dir/Turbine_Data_Kelmarsh_1_2023.csv", data)
        z.writestr("dir/Status_Kelmarsh_1_2023.csv", "keep,as,is\n")
    extract_dedup.extract(str(zp), str(tmp_path / "out"), verbose=False)
    lines = (tmp_path / "out" / "Turbine_Data_Kelmarsh_1_2023.csv").read_text().splitlines()
    assert lines == ["# header", "# Date and time,a,b", "2023-01-01 00:00:00,1,2", "2023-01-01 00:10:00,3,5"]
    assert (tmp_path / "out" / "Status_Kelmarsh_1_2023.csv").read_text() == "keep,as,is\n"
    assert io.StringIO((tmp_path / "out" / "_dedup_log.json").read_text()).read().count("conflicting_lines_kept") == 1

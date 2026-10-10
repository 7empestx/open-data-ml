import importlib

from windml import config


def test_year_and_list_parsing():
    assert config._years("") is None
    assert config._years("2016-2018,2021") == {2016, 2017, 2018, 2021}
    assert config._list("kel01, KEL02") == {"KEL01", "KEL02"}
    assert config._list(" ") is None


def test_defaults_are_repo_relative(monkeypatch):
    for k in ("WINDML_RAW_DIR", "WINDML_DATA_DIR", "WINDML_REPORTS_DIR", "WINDML_LOG_DIR"):
        monkeypatch.delenv(k, raising=False)
    c = importlib.reload(config)
    assert c.RAW_DIR == c.PROJECT_ROOT / "data" / "raw"
    assert c.ALL_YEARS_DIR == c.PROJECT_ROOT / "data" / "processed" / "all_years"
    assert c.REPORTS_DIR == c.PROJECT_ROOT / "reports"
    assert c.CONDITION_TEMPLATE_DIR.is_dir()


def test_env_overrides(monkeypatch, tmp_path):
    monkeypatch.setenv("WINDML_DATA_DIR", str(tmp_path / "d"))
    monkeypatch.setenv("WINDML_WORKERS", "3")
    c = importlib.reload(config)
    assert c.NBM_YEARS_DIR == (tmp_path / "d" / "nbm_years").resolve()
    assert c.workers(8) == 3
    monkeypatch.delenv("WINDML_DATA_DIR")
    monkeypatch.delenv("WINDML_WORKERS")
    importlib.reload(config)

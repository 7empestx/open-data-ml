# windml: one-command setup and pipeline. Run from projects/windml.
#   make setup        create .venv with pinned dependencies
#   make smoke        ~535 MB download + the whole pipeline on Kelmarsh 2016-2018, 2 turbines (a few minutes)
#   make all          full reproduction: download (~9.7 GB) -> preprocess -> NBM -> trip models -> evaluations -> condition report
# Paths come from WINDML_RAW_DIR / WINDML_DATA_DIR / WINDML_REPORTS_DIR / WINDML_LOG_DIR (see src/windml/config.py).

SHELL := /bin/bash
.SHELLFLAGS := -eo pipefail -c
.DEFAULT_GOAL := help

PYTHON ?= python3
VENV   ?= .venv
PY     := $(VENV)/bin/python
FARMS  ?= kelmarsh penmanshiel
YEARS  ?=
comma  := ,
empty  :=
space  := $(empty) $(empty)
LOG_DIR := $(or $(WINDML_LOG_DIR),logs)
RUN     = mkdir -p $(LOG_DIR) && $(PY)
LOG     = 2>&1 | tee $(LOG_DIR)/$(1).log

# Smoke-test subset (override any of these on the command line)
SMOKE_DIR      ?= $(CURDIR)/data/smoke
SMOKE_RAW_DIR  ?= $(SMOKE_DIR)/raw
SMOKE_FARMS    ?= kelmarsh
SMOKE_YEARS    ?= 2016-2018
SMOKE_TURBINES ?= KEL01,KEL02
SMOKE_ENV = WINDML_RAW_DIR=$(SMOKE_RAW_DIR) WINDML_DATA_DIR=$(SMOKE_DIR)/data WINDML_REPORTS_DIR=$(SMOKE_DIR)/reports \
            WINDML_LOG_DIR=$(SMOKE_DIR)/logs WINDML_YEARS=$(SMOKE_YEARS) WINDML_TURBINES=$(SMOKE_TURBINES) \
            WINDML_TRIP_MIN_POS=1 WINDML_WORKERS=2

.PHONY: help setup setup-dev config download download-cmapss download-lhb download-smarteole preprocess nbm nbm-eval trip trip-eval report all smoke smoke-clean test lint \
        ingest-suggest ingest-validate ingest-load ingest-fixtures ingest-proof

help:
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/^## //'

## setup            create .venv and install pinned requirements.txt
setup: $(VENV)/.installed
$(VENV)/.installed: requirements.txt
	$(PYTHON) -m venv $(VENV)
	$(PY) -m pip install --quiet --upgrade pip
	$(PY) -m pip install --quiet -r requirements.txt
	touch $@

## setup-dev        setup + pytest and ruff
setup-dev: setup
	$(PY) -m pip install --quiet -r requirements-dev.txt

## config           print the resolved paths
config: setup
	$(PY) src/windml/config.py

## download         Kelmarsh + Penmanshiel SCADA from Zenodo (MD5-verified; FARMS=..., YEARS=2016-2017 to subset)
download: setup
	$(RUN) scripts/download_wind_data.py --farms $(subst $(space),$(comma),$(strip $(FARMS))) $(if $(YEARS),--years $(YEARS)) $(call LOG,download)

## download-cmapss  NASA C-MAPSS (not used by windml; side dataset, not redistributed)
download-cmapss:
	bash scripts/download_cmapss.sh

## download-lhb     La Haute Borne (ENGIE, Licence Ouverte 2.0) 2014-2015 extract via NREL OpenOA (~37 MB, SHA-256 pinned)
download-lhb: setup
	$(PY) scripts/download_la_haute_borne.py

## download-smarteole SMARTEOLE (ENGIE, Licence Ouverte 2.0) 1-min SCADA, 7 turbines, Feb-May 2020 (~150 MB, MD5 pinned)
download-smarteole: setup
	$(PY) scripts/download_smarteole.py

## preprocess       clean + label all years, extract extra and 10-min statistic signals
preprocess: setup
	$(RUN) scripts/run_all_years.py $(FARMS) $(call LOG,preprocess)
	$(RUN) scripts/extract_extra_signals.py $(FARMS) $(call LOG,extract_extra)
	$(RUN) scripts/extract_stat_signals.py $(FARMS) $(call LOG,extract_stats)

## nbm              walk-forward-by-year normal-behaviour models (cached per turbine)
nbm: setup
	$(RUN) scripts/run_nbm_years.py $(FARMS) $(call LOG,nbm_years)

## nbm-eval         NBM evaluation (selection 2017-2020, held-out 2021-2024) + figures/tables
nbm-eval: setup
	$(RUN) scripts/eval_nbm_years.py $(call LOG,eval_nbm_years)
	$(RUN) scripts/report_nbm_years.py $(call LOG,report_nbm_years)

## trip             hourly trip features + 24/48/72 h trip classifiers (cached)
trip: setup
	$(RUN) scripts/build_trip_features.py $(FARMS) $(call LOG,trip_features)
	$(RUN) scripts/run_trip_models.py $(call LOG,trip_models)

## trip-eval        trip-model evaluation + figures/tables
trip-eval: setup
	$(RUN) scripts/eval_trip.py $(call LOG,eval_trip)
	$(RUN) scripts/report_trip.py $(call LOG,report_trip)

## report           sample condition report (tables, figures, markdown, PDF if Chrome/Chromium is installed)
report: setup
	$(RUN) scripts/condition_metrics.py $(call LOG,condition_metrics)
	$(RUN) scripts/condition_oil_pressure.py $(FARMS) $(call LOG,condition_oil_pressure)
	$(RUN) scripts/condition_scorecard.py $(call LOG,condition_scorecard)
	$(RUN) scripts/condition_tables.py $(call LOG,condition_tables)
	$(RUN) scripts/condition_figures.py $(call LOG,condition_figures)
	$(RUN) scripts/build_condition_report.py $(call LOG,build_condition_report)

## all              full reproduction (hours; run under nohup, see README)
all: download preprocess nbm nbm-eval trip trip-eval report

## smoke            small end-to-end run into data/smoke/ (download subset -> preprocess -> NBM -> trip models -> checks)
smoke: setup
	@echo "smoke: $(SMOKE_FARMS) $(SMOKE_YEARS) $(SMOKE_TURBINES) -> $(SMOKE_DIR)"
	$(SMOKE_ENV) $(MAKE) --no-print-directory download FARMS="$(SMOKE_FARMS)" YEARS=$(SMOKE_YEARS)
	$(SMOKE_ENV) $(MAKE) --no-print-directory preprocess nbm trip FARMS="$(SMOKE_FARMS)"
	$(SMOKE_ENV) $(PY) scripts/smoke_check.py $(SMOKE_FARMS)

## smoke-clean      delete derived smoke outputs (keeps the downloaded raw subset)
smoke-clean:
	rm -rf $(SMOKE_DIR)/data $(SMOKE_DIR)/reports $(SMOKE_DIR)/logs

## ingest-suggest   draft a mapping from a sample export: make ingest-suggest SAMPLE=path/to/export.csv [OUT=mappings/acme.yaml]
ingest-suggest: setup
	@test -n "$(SAMPLE)" || { echo "usage: make ingest-suggest SAMPLE=<file> [OUT=mappings/<name>.yaml]"; exit 2; }
	bin/windml ingest suggest "$(SAMPLE)" $(if $(OUT),--out "$(OUT)")

## ingest-validate  check a mapping + write the day-1 data-quality report: make ingest-validate MAPPING=mappings/x.yaml
ingest-validate: setup
	@test -n "$(MAPPING)" || { echo "usage: make ingest-validate MAPPING=<yaml> [REPORT=reports/ingest/dq_x.md]"; exit 2; }
	bin/windml ingest validate --mapping "$(MAPPING)" $(if $(REPORT),--report "$(REPORT)")

## ingest-load      load to canonical parquet + pipeline layout: make ingest-load MAPPING=mappings/x.yaml OUT=data/ingest/x
ingest-load: setup
	@test -n "$(MAPPING)" -a -n "$(OUT)" || { echo "usage: make ingest-load MAPPING=<yaml> OUT=<dir>"; exit 2; }
	bin/windml ingest load --mapping "$(MAPPING)" --out "$(OUT)" --export

## ingest-fixtures  synthetic messy operator exports from Kelmarsh 2022 (needs make download YEARS=2022)
ingest-fixtures: setup
	$(PY) scripts/make_messy_fixtures.py
	$(PY) scripts/make_highres_fixtures.py

## ingest-proof     load 8-9 differently shaped inputs (incl. high-res), compare with references -> reports/ingest/proof.md + dq_*.md
ingest-proof: setup
	$(RUN) scripts/ingest_proof.py $(call LOG,ingest_proof)

## test             unit tests on tiny fixtures (no data needed)
test: setup-dev
	$(PY) -m pytest -q tests

## lint             ruff (errors only)
lint: setup-dev
	$(PY) -m ruff check src scripts tests

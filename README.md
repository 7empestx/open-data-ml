# open-data-ml

Machine-learning models for industrial operations and maintenance, trained **only on openly licensed public datasets**.

Every project in this repo:

- uses data published under an open license (for example CC BY 4.0 or US Government public domain),
- lists each source, its license, and the required attribution in its own `DATA_SOURCES.md`,
- commits only processed derivatives and code. Raw downloads are never committed.

See [DATA_POLICY.md](DATA_POLICY.md) for the rules. Project site: https://ml.beehivewebstudio.com

## Projects

| Project | Status | What it does |
|---|---|---|
| [projects/windml](projects/windml/) | **First target**, cleaning and failure labeling done | Wind turbine failure prediction from 10-minute SCADA data and status logs for the Kelmarsh (6 turbines, 2022) and Penmanshiel (5 turbines, 2021 H1) wind farms (CC BY 4.0, Cubico Sustainable Investments via Zenodo). See [RESULTS.md](projects/windml/RESULTS.md) and [DATA_SOURCES.md](projects/windml/DATA_SOURCES.md). |

## Possible future projects

These datasets are already profiled and lightly cleaned in `projects/windml/data/processed/`, unless marked otherwise. Each one could become its own project:

- **Solar PV underperformance and soiling**: NREL PVDAQ (CC BY 4.0)
- **Packaging-line alarm and failure prediction**: CoMoPI and PIADE (CC BY 4.0)
- **Beverage bottling downtime and OEE analytics**: beverage bottling line dataset (CC BY 4.0)
- **Air-compressor failure prediction**: MetroPT-3, Porto metro (CC BY 4.0)
- **Remaining useful life benchmarks**: NASA C-MAPSS turbofan (simulated; not committed, fetch with `projects/windml/scripts/download_cmapss.sh`)
- **Hydraulic condition classification**: UCI hydraulic systems (CC BY 4.0)
- **Manufacturing fault and yield classification**: UCI AI4I 2020 (synthetic) and UCI SECOM (CC BY 4.0). Downloaded, not yet processed.

Datasets with unclear or copyleft licenses (for example NASA IMS bearings and SKAB) are excluded.

## Layout

    projects/<name>/
      README.md         how to run the project
      DATA_SOURCES.md   source, license, attribution for every dataset used
      RESULTS.md        findings so far
      src/ scripts/     code
      data/processed/   processed derivatives only (no raw data)
      reports/          schema, cleaning, and labeling reports

## License

The code in this repository is released under the [MIT License](LICENSE), Copyright (c) 2026 Beehive AI Labs LLC.

The MIT License covers the code only. **Datasets and their processed derivatives keep their own licenses.** The Kelmarsh and Penmanshiel wind farm data (Cubico Sustainable Investments, via Zenodo) are CC BY 4.0, and so are the other committed datasets. Reuse requires attribution as listed in each project's `DATA_SOURCES.md` (for windml: [projects/windml/DATA_SOURCES.md](projects/windml/DATA_SOURCES.md)). NASA C-MAPSS data is not committed; fetch it from NASA with `projects/windml/scripts/download_cmapss.sh`.

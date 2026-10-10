# Data sources, licenses, and attribution

The source, license, and attribution for every dataset below come from the `SOURCE.txt` file saved next to each raw download (retrieved 2026-10-09). This repo contains only processed derivatives (`data/processed/`). It contains no raw files.

| Dataset | Used here | Source | License | Required attribution |
|---|---|---|---|---|
| Kelmarsh wind farm SCADA (6x Senvion MM92, UK), 2016 to 2024 | Yes, cleaned and labeled (2022 single-year set + all-years set) | https://zenodo.org/records/16807551 (DOI 10.5281/zenodo.16807551) | CC BY 4.0 | Credit Cubico Sustainable Investments and the Zenodo DOI 10.5281/zenodo.16807551 |
| Penmanshiel wind farm SCADA (14x Senvion MM82, UK), WT01-10 2016 to 2023, WT11-15 2016 to 2024 (H1-2021 WT11-15 single-period set from the earlier version) | Yes, cleaned and labeled (H1-2021 single-period set + all-years set) | https://zenodo.org/records/16807304 (DOI 10.5281/zenodo.16807304); earlier version https://zenodo.org/records/5946808 | CC BY 4.0 | Credit Cubico Sustainable Investments and the Zenodo DOI 10.5281/zenodo.16807304 (and 10.5281/zenodo.5946808 for the H1-2021 set) |
| NREL PVDAQ public PV data, system 10 (NREL CIS-1), 2008 | Yes, light cleaning | https://data.openei.org/submissions/4568 (DOI 10.25984/1846021) | CC BY 4.0 (verified on the OEDI page, 2026-10-10) | Credit NREL PVDAQ / OEDI and DOI 10.25984/1846021 |
| CoMoPI: Condition Monitoring for Packaging Industry | Yes, light cleaning | https://zenodo.org/records/7572501 | CC BY 4.0 | Credit the dataset authors and Zenodo record 7572501 |
| PIADE: Packaging Industry Anomaly DEtection | Yes, light cleaning | https://zenodo.org/records/7071747 | CC BY 4.0 | Credit the dataset authors and Zenodo record 7071747 |
| Industrial Production Time-Series from a Beverage Bottling Line | Yes, light cleaning | https://zenodo.org/records/18146866 | CC BY 4.0 | Credit the dataset authors and Zenodo record 18146866 |
| MetroPT-3 (Porto metro air compressor) | Yes, light cleaning | https://archive.ics.uci.edu/dataset/791 (DOI 10.24432/C5VW3R) | CC BY 4.0 (verified on the dataset page, 2026-10-10) | Cite the UCI DOI 10.24432/C5VW3R and the authors |
| NASA C-MAPSS Turbofan Engine Degradation Simulation (simulated) | Profiled locally only. **Not committed** (no raw or processed files in this repo); fetch it with `scripts/download_cmapss.sh` | https://phm-datasets.s3.amazonaws.com/NASA/6.+Turbofan+Engine+Degradation+Simulation+Data+Set.zip (NASA Ames PCoE data repository) | Not specified: data.nasa.gov lists the license as "not specified" (checked 2026-10-10). Presumed US Government work (17 USC 105), but because it is unconfirmed we do not redistribute it. | Cite Saxena & Goebel (2008), NASA Ames Prognostics Center of Excellence |
| UCI Condition monitoring of hydraulic systems (ZeMA) | Yes, light cleaning | https://archive.ics.uci.edu/dataset/447 (DOI 10.24432/C5CW21) | CC BY 4.0 (verified on the dataset page, 2026-10-10) | Cite the UCI DOI 10.24432/C5CW21 and the authors |
| UCI AI4I 2020 Predictive Maintenance (synthetic) | Downloaded, not yet processed | https://archive.ics.uci.edu/dataset/601 (DOI 10.24432/C5HS5C) | CC BY 4.0 (verified on the dataset page, 2026-10-10) | Cite the UCI DOI 10.24432/C5HS5C and Matzka (2020) |
| UCI SECOM semiconductor process data | Downloaded, not yet processed | https://archive.ics.uci.edu/dataset/179 (DOI 10.24432/C54305) | CC BY 4.0 (verified on the dataset page, 2026-10-10) | Cite the UCI DOI 10.24432/C54305 and the authors |

Zenodo licenses (Kelmarsh, Penmanshiel, CoMoPI, PIADE, bottling line) were rechecked through the Zenodo records API on 2026-10-10: all CC BY 4.0. The four UCI dataset pages each state CC BY 4.0.

## NASA C-MAPSS: download it yourself

C-MAPSS has no stated license, so this repo does not include it, in raw or processed form. To use it:

    projects/windml/scripts/download_cmapss.sh [DEST_DIR]   # default: $WINDML_RAW_DIR/nasa-cmapss
    python projects/windml/scripts/profile_and_clean.py     # rebuilds data/processed/cmapss_all.parquet locally (gitignored)

The script downloads the zip from the official NASA PCoE data repository
(https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/),
checks its SHA-256, unpacks the FD001 to FD004 train, test and RUL files, and writes a `SOURCE.txt` next to them.
Review NASA's terms before redistributing anything derived from it. `reports/schema_nasa_cmapss.md` (column names, units, row counts and min/max only) stays in the repo as documentation.

## Excluded datasets

These are deliberately **not used** and not included in this repo:

- **NASA IMS bearing data**: no clear license.
- **SKAB (Skoltech Anomaly Benchmark) water-pump data**: copyleft license, which doesn't fit a commercial product.

Both were moved to an `_excluded/` folder outside this repo.

## Attribution in published work

Every CC BY 4.0 dataset requires attribution in any published demo, model card, or derived result. Name the source, link the record or DOI, and state the license (CC BY 4.0, https://creativecommons.org/licenses/by/4.0/). Note any changes you made, such as cleaning, resampling, or labeling.

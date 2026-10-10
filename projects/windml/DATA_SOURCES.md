# Data sources, licenses, and attribution

The source, license, and attribution for every dataset below come from the `SOURCE.txt` file saved next to each raw download (retrieved 2026-10-09). This repo contains only processed derivatives (`data/processed/`). It contains no raw files.

| Dataset | Used here | Source | License | Required attribution |
|---|---|---|---|---|
| Kelmarsh wind farm SCADA (6x Senvion MM92, UK), 2022 | Yes, cleaned and labeled | https://zenodo.org/records/16807551 (DOI 10.5281/zenodo.16807551) | CC BY 4.0 | Credit Cubico Sustainable Investments and the Zenodo DOI 10.5281/zenodo.16807551 |
| Penmanshiel wind farm SCADA (Senvion MM82, UK), WT11-15, 2021-01-01 to 2021-07-01 | Yes, cleaned and labeled | https://zenodo.org/records/5946808 (DOI 10.5281/zenodo.5946808) | CC BY 4.0 | Credit Cubico Sustainable Investments and the Zenodo DOI 10.5281/zenodo.5946808 |
| NREL PVDAQ public PV data, system 10 (NREL CIS-1), 2008 | Yes, light cleaning | https://data.openei.org/submissions/4568 (DOI 10.25984/1846021) | CC BY 4.0 (per OEDI / data.gov metadata) | Credit NREL PVDAQ / OEDI and DOI 10.25984/1846021 |
| CoMoPI: Condition Monitoring for Packaging Industry | Yes, light cleaning | https://zenodo.org/records/7572501 | CC BY 4.0 | Credit the dataset authors and Zenodo record 7572501 |
| PIADE: Packaging Industry Anomaly DEtection | Yes, light cleaning | https://zenodo.org/records/7071747 | CC BY 4.0 | Credit the dataset authors and Zenodo record 7071747 |
| Industrial Production Time-Series from a Beverage Bottling Line | Yes, light cleaning | https://zenodo.org/records/18146866 | CC BY 4.0 | Credit the dataset authors and Zenodo record 18146866 |
| MetroPT-3 (Porto metro air compressor) | Yes, light cleaning | https://archive.ics.uci.edu/dataset/791 (DOI 10.24432/C5VW3R) | CC BY 4.0 (UCI repository policy)* | Cite the UCI DOI 10.24432/C5VW3R and the authors |
| NASA C-MAPSS Turbofan Engine Degradation Simulation (simulated) | Yes, light cleaning | https://phm-datasets.s3.amazonaws.com/NASA/6.+Turbofan+Engine+Degradation+Simulation+Data+Set.zip (NASA Ames PCoE) | US Government work, public (17 USC 105). No license file. | Cite Saxena & Goebel (2008), NASA Ames Prognostics Center of Excellence |
| UCI Condition monitoring of hydraulic systems (ZeMA) | Yes, light cleaning | https://archive.ics.uci.edu/dataset/447 (DOI 10.24432/C5CW21) | CC BY 4.0 (UCI repository policy)* | Cite the UCI DOI 10.24432/C5CW21 and the authors |
| UCI AI4I 2020 Predictive Maintenance (synthetic) | Downloaded, not yet processed | https://archive.ics.uci.edu/dataset/601 (DOI 10.24432/C5HS5C) | CC BY 4.0 (UCI repository policy)* | Cite the UCI DOI 10.24432/C5HS5C and Matzka (2020) |
| UCI SECOM semiconductor process data | Downloaded, not yet processed | https://archive.ics.uci.edu/dataset/179 (DOI 10.24432/C54305) | CC BY 4.0 (UCI repository policy)* | Cite the UCI DOI 10.24432/C54305 and the authors |

\* The UCI repository states that its datasets are licensed CC BY 4.0. The per-dataset license badge couldn't be machine-read, so verify it on each dataset page before shipping anything public.

## Excluded datasets

These are deliberately **not used** and not included in this repo:

- **NASA IMS bearing data**: no clear license.
- **SKAB (Skoltech Anomaly Benchmark) water-pump data**: copyleft license, which doesn't fit a commercial product.

Both were moved to an `_excluded/` folder outside this repo.

## Attribution in published work

Every CC BY 4.0 dataset requires attribution in any published demo, model card, or derived result. Name the source, link the record or DOI, and state the license (CC BY 4.0, https://creativecommons.org/licenses/by/4.0/). Note any changes you made, such as cleaning, resampling, or labeling.

---
title: Data sources and licenses
description: Where the windml data comes from, its license, and the required attribution.
---

The source, license, and attribution below come from the `SOURCE.txt` file saved next to each raw download (retrieved 2026-10-09). The project keeps only processed derivatives. Raw files stay on Zenodo.

## Wind farm data used by windml

| Dataset | Source | License | Required attribution |
|---|---|---|---|
| Kelmarsh wind farm SCADA (6 x Senvion MM92, UK), 2022 | [Zenodo record 16807551](https://zenodo.org/records/16807551), DOI [10.5281/zenodo.16807551](https://doi.org/10.5281/zenodo.16807551) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | Credit Cubico Sustainable Investments and the Zenodo DOI |
| Penmanshiel wind farm SCADA (Senvion MM82, UK), turbines 11 to 15, 2021-01-01 to 2021-07-01 | [Zenodo record 5946808](https://zenodo.org/records/5946808), DOI [10.5281/zenodo.5946808](https://doi.org/10.5281/zenodo.5946808) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | Credit Cubico Sustainable Investments and the Zenodo DOI |

## Attribution

Kelmarsh and Penmanshiel wind farm data, Cubico Sustainable Investments Ltd, published on Zenodo under CC BY 4.0. Changes made by this project: cleaning, resampling to a regular 10-minute grid, column selection, and fault labeling.

Every page, model card, or result that uses this data carries the same credit.

## Other open datasets

The repository also holds lightly cleaned copies of other openly licensed industrial datasets (solar, packaging, metro compressor, and NASA's simulated turbofan data) for possible future projects. They aren't part of windml. Two datasets were left out on purpose: the NASA IMS bearing data (no clear license) and the SKAB water-pump benchmark (copyleft license).

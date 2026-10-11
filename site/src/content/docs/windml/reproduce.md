---
title: Reproduce it
description: Rerun the windml pipeline from the public repository, from a 10-minute smoke test to the full 2016 to 2024 results.
---

All windml code is public at [github.com/7empestx/open-data-ml](https://github.com/7empestx/open-data-ml) under the MIT license. Raw data is downloaded from Zenodo (CC BY 4.0) by the scripts and never committed. Every push runs lint, an import check and the unit tests in [GitHub Actions](https://github.com/7empestx/open-data-ml/actions).

## Quick check: the smoke test

```bash
git clone https://github.com/7empestx/open-data-ml
cd open-data-ml/projects/windml
make setup   # virtual environment with pinned requirements (about 1 minute)
make smoke   # Kelmarsh 2016 to 2018: download, clean, label, models, output checks
make test    # unit tests on tiny fixtures, no data needed
```

`make smoke` downloads about 535 MB and runs the whole pipeline end to end in about 5 to 10 minutes, mostly download time. It's a real run, not a mock: its 2018 normal-behavior scores for KEL01 and KEL02 are identical to the full run's, because both train only on 2016 and 2017.

## Full reproduction

```bash
make download     # Kelmarsh + Penmanshiel from Zenodo, MD5-verified
make preprocess   # clean and label all years
make nbm          # walk-forward normal-behavior models
make nbm-eval     # pick settings on 2017 to 2020, score once on 2021 to 2024
make trip         # 24, 48 and 72 hour trip models
make trip-eval
make report       # the sample condition report
```

Each step is cached and resumable, and logs to `logs/<step>.log`. `make all` runs everything.

## What you need

| | Smoke test | Full run |
|---|---|---|
| Download | about 535 MB | about 9.7 GB of zips |
| Disk | about 2.6 GB | about 35 to 45 GB |
| Machine | a laptop | 8 cores and 16 GB RAM recommended |
| Time | 5 to 10 minutes | 1 to 3 hours of download, then about 3 hours of extraction and compute |

Python 3.11 or newer, `make` and internet access to zenodo.org. Google Chrome or Chromium is optional and only needed to render the report PDF.

Full details, including environment variables for data paths and subsets, are in the [windml README](https://github.com/7empestx/open-data-ml/blob/main/projects/windml/README.md#reproduce).

## Found a problem?

Open an [issue on GitHub](https://github.com/7empestx/open-data-ml/issues) or email [hello@beehivewebstudio.com](mailto:hello@beehivewebstudio.com). Corrections are welcome, especially ones that change a result.

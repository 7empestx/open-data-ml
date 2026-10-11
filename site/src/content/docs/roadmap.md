---
title: Roadmap
description: What's done and what's planned next for open-data-ml and windml.
---

## Done

- Cleaned and labeled every published year of Kelmarsh (2016 to 2024) and Penmanshiel (2016 to 2024).
- Tested normal-behavior models (30-day warning) and short-term trip models (24 to 72 hours) under a strict walk-forward test. Neither beat chance. See [Results](/windml/results/).
- Built a [sample condition report](/windml/condition-report/) from the same data.
- Published the code on [GitHub](https://github.com/7empestx/open-data-ml) under the MIT license, with automated tests and a [one-command smoke test](/windml/reproduce/).

## windml next

1. **Operator data loader.** Map an unfamiliar SCADA export (different column names, units and status codes) into the windml format in a day, not a week.
2. **Repeatable condition report.** Turn the sample report into a pipeline that runs on any fleet's SCADA and status logs, with a short summary up front.
3. **Better data.** Look for openly licensed wind data with 1-second to 1-minute resolution, maintenance or work-order records, or vibration data.
4. **Cross-farm checks.** Test whether findings from one farm hold at the other.

## open-data-ml

- Add new projects on other openly licensed datasets, with the same license checks and attribution.

## For wind operators

The free pilot is open now. See [Work with us](/work-with-us/) or email [hello@beehivewebstudio.com](mailto:hello@beehivewebstudio.com). Your data stays yours.

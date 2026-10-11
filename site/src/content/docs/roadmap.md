---
title: Roadmap
description: What's done and what's planned next for open-data-ml and windml.
---

## Done

- Cleaned and labeled every published year of Kelmarsh (2016 to 2024) and Penmanshiel (2016 to 2024).
- Tested normal-behavior models (30-day warning) and short-term trip models (24 to 72 hours) under a strict walk-forward test. Neither beat chance. See [Results](/windml/results/).
- Built a [sample condition report](/windml/condition-report/) from the same data.
- Published the code on [GitHub](https://github.com/7empestx/open-data-ml) under the MIT license, with automated tests and a [one-command smoke test](/windml/reproduce/).
- **Operator data loader.** One YAML mapping reads an unfamiliar SCADA export (other column names, units, time zones, file layouts, status codes) into the windml format, with a day-1 data-quality report. Tested on Kelmarsh, Penmanshiel, La Haute Borne and three deliberately messy synthetic exports.
- **High-resolution data.** 1-second to 1-minute SCADA is detected and summarized into 10-minute bins (mean, min, max, standard deviation, coverage). Tested on synthetic data built from Kelmarsh and on the open 1-minute SMARTEOLE dataset (ENGIE).
- **Repeatable condition report.** One command turns any mapped fleet into a condition report with a one-page summary up front: which turbines to look at, why, and how sure we are. On Kelmarsh and Penmanshiel it flags the same turbines as the hand-built sample report. It works with 12 months of data or more and says what it could not check (for example, when there is no alarm log).

## windml next

1. **Features from high-resolution data.** Use the 1-second to 1-minute signals (not just their 10-minute summaries) for earlier warnings.
2. **Better data.** Look for openly licensed maintenance or work-order records and vibration data, to check flags against what technicians found.
3. **Cross-farm checks.** Test whether findings from one farm hold at the other.
4. **Calibrated flags.** Replace the fixed red/amber/green rules with thresholds checked against real outcomes.

## open-data-ml

- Add new projects on other openly licensed datasets, with the same license checks and attribution.

## For wind operators

The free pilot is open now. See [Work with us](/work-with-us/) or email [hello@beehivewebstudio.com](mailto:hello@beehivewebstudio.com). Your data stays yours.

# Data policy

These rules apply to every project in this repository.

1. **Openly licensed data only.** Use only datasets published under a clear open license that permits commercial use and redistribution of derivatives, for example CC BY 4.0, CC0, or US Government works (17 USC 105). Check the license on the original source page before using a dataset.
2. **Track every source.** Each project keeps a `DATA_SOURCES.md` that lists, for every dataset it uses, the source URL or DOI, the license, the retrieval date, and the attribution that license requires. Published demos, model cards, and results must carry that attribution.
3. **Exclude unclear and copyleft licenses.** Do not use a dataset with no clear license, a non-commercial license, or a copyleft or share-alike license (for example GPL-style or CC BY-SA terms that would bind the project's outputs). Record excluded datasets and the reason in the project's `DATA_SOURCES.md` (current examples: NASA IMS bearings for no clear license, SKAB for copyleft).
4. **Never resell data.** This work builds models and services on top of public data. Raw or processed datasets are never sold or licensed as a product. Processed derivatives in this repo exist only to make the work reproducible, with attribution.
5. **No raw data in git.** Commit only code, reports, and processed derivatives (under each project's `data/processed/`). Raw downloads stay outside the repo and can be re-fetched from the listed sources.
6. **No private or customer data.** Don't add proprietary, personal, or customer data to this repository.

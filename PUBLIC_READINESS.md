# Public readiness check: open-data-ml

Checked 2026-10-10 (MT) against `main` at commit 5ae138f. The repo is still **private**. Nothing here changes visibility, deploys, or posts anything.

## Verdict

**Not ready to make public yet.** The data licenses are clean. There is one hard blocker (no code license file) and a few decisions only Grant can make. None need a history rewrite.

## 1. Blockers (fix before flipping to public)

| # | Item | Why it matters | Fix |
|---|---|---|---|
| B1 | **No `LICENSE` file** at the repo root. | Without one, the code is "all rights reserved" and nobody can legally reuse it. | Add MIT (the plan's choice) with "Copyright (c) 2026 <LLC name>". Needs Grant's OK on the LLC name. |
| B2 | **Employer IP confirmation in writing.** | Grant acknowledged it as not blocking, but the plan says to confirm IP ownership before publishing. | Grant gets a short written confirmation (email is fine). |
| B3 | **NASA C-MAPSS license wording.** `projects/windml/data/processed/cmapss_all.parquet` (7.3 MB) is committed. data.nasa.gov lists the license as "not specified". | US Government works are public domain under 17 USC 105, but the record doesn't say so, and contractors may have worked on it. Low risk, not verified. | Pick one: (a) keep it, with the 17 USC 105 note and citation already in DATA_SOURCES.md; or (b) **recommended:** untrack it (`git rm --cached`, add to .gitignore) and re-fetch from NASA with a script. It's a side dataset, not part of windml. It stays in history either way. If (b) matters, the only clean option is a new public repo created from a fresh snapshot, never a force-push. |

## 2. Dataset license check

Licenses checked at the source on 2026-10-10. Zenodo via the records API (`/api/records/<id>`), UCI and OEDI from the dataset pages, NASA via the data.nasa.gov catalog API.

| Dataset | Source | License found | Committed derivative | OK to publish? |
|---|---|---|---|---|
| Kelmarsh wind farm, 2016 to 2024 | Zenodo 16807551 | CC BY 4.0 | `kelmarsh_scada_10min/labeled.parquet`, `kelmarsh_events.parquet`, `all_years/kelmarsh_events.parquet`, reports, figures, PDF | Yes, with attribution and a note of changes (already in DATA_SOURCES.md and on the site) |
| Penmanshiel wind farm, 2016 to 2024 | Zenodo 16807304 | CC BY 4.0 | `all_years/penmanshiel_events.parquet`, reports, figures | Yes, with attribution |
| Penmanshiel, earlier version (H1 2021) | Zenodo 5946808 | CC BY 4.0 | `penmanshiel_scada_10min/labeled.parquet`, `penmanshiel_events.parquet` | Yes, with attribution |
| CoMoPI (packaging) | Zenodo 7572501 | CC BY 4.0 | 3 parquets | Yes, with attribution |
| PIADE (packaging) | Zenodo 7071747 | CC BY 4.0 | 2 parquets | Yes, with attribution |
| Beverage bottling line | Zenodo 18146866 | CC BY 4.0 | 2 parquets | Yes, with attribution |
| MetroPT-3 | UCI 791 | CC BY 4.0 (dataset page) | `metropt3.parquet` | Yes, with attribution |
| Hydraulic systems (ZeMA) | UCI 447 | CC BY 4.0 (dataset page) | `hydraulic_cycle_features.parquet` | Yes, with attribution |
| AI4I 2020 | UCI 601 | CC BY 4.0 (dataset page) | none | n/a |
| SECOM | UCI 179 | CC BY 4.0 (dataset page) | none | n/a |
| NREL PVDAQ system 10 | OEDI 4568 | CC BY 4.0 (OEDI page) | `nrel_pvdaq_system10_2008.parquet` | Yes, with attribution |
| NASA C-MAPSS | NASA PCoE | Presumed US Gov work; catalog says "not specified" | `cmapss_all.parquet` | See B3 |
| NASA IMS bearings | excluded | no clear license | none, never in history | n/a |
| SKAB | excluded | copyleft | none, never in history | n/a |

Every license above allows commercial use and redistribution of changed versions, as long as you credit the source. None is non-commercial or share-alike. That matches DATA_POLICY.md.

**Raw data:** no raw files, zips, or excluded datasets show up anywhere in git history (checked every path ever committed). Only processed derivatives are tracked, as DATA_POLICY.md requires.

**Content of the event logs:** I scanned the 265 unique operator comments in the Kelmarsh and Penmanshiel status logs for names, emails, and phone numbers. Found none. They're short maintenance notes like "Annual Service", and Cubico already published them.

## 3. Secrets and personal info

- **Secrets:** scanned every commit for AWS keys, private keys, GitHub, Slack, OpenAI and Hugging Face tokens, and `password=`. **None found.**
- **Commit identity:** all 9 commits use the GitHub noreply address `51809789+7empestx@users.noreply.github.com`. 7 show the name "Grant Starkman" and 2 show "7empestx". Your name will be public on the commits. If you'd rather they show the LLC, set `user.name` for future commits. Past commits stay as they are, since rewriting them would mean a force-push.
- **Emails in files:** only `hello@beehivewebstudio.com`, which is the intended public contact.
- **Machine paths:** scripts hardcode `/workspace/industrial-data` and `/workspace/logs`, for example `RAW = Path("/workspace/industrial-data")` in `src/windml/greenbyte.py` and `scripts/profile_and_clean.py`. These aren't sensitive, but nobody else can run the code. Make the raw-data path an environment variable (for example `WINDML_RAW_DIR`) with a sensible default.

## 4. Not blocking, but should fix soon

1. **No dependency file.** Add `pyproject.toml` with a `uv.lock` (or `requirements.txt`) so the results can be reproduced.
2. **No data-download scripts.** DATA_POLICY says raw data "can be re-fetched", but there's no script that does it. Add `scripts/download_data.py` that pulls each Zenodo/UCI record by DOI and checks file hashes.
3. **Name clash: "windML".** An older, unmaintained project of the same name exists: github.com/cigroup-ol/windml (about 130 stars, windml.org), and it holds the PyPI name `windML` (v0.3.8). Using windml as a repo folder or site section is fine. Don't publish a PyPI package called `windml`, and say "not affiliated" somewhere, or think about a different name (for example `windml-scada` or `open-windml`). Before using either name as a brand, also run a USPTO search (free) for "open-data-ml" and "windml". `open-data-ml` isn't taken on PyPI.
4. **Repo size.** About 189 MB of loose objects, mostly the processed wind parquets (about 135 MB). That's under GitHub's limits, but cloning is slow. A later option is to move processed data to a Hugging Face dataset (also CC BY 4.0 with attribution) and keep git for code.
5. **Top-level README:** add a "not engineering advice" line and a data-credit block like the one on the site.
6. **`site/DEPLOY.md`** mentions Grant by name and describes AWS setup steps. Nothing sensitive, but you could move it to a private notes file if you don't want it public.

## 5. Before making it public (Grant's approval needed)

- [ ] Add LICENSE (MIT, LLC as copyright holder) (B1)
- [ ] Get employer IP confirmation in writing (B2)
- [ ] Decide on C-MAPSS (B3)
- [ ] Decide on the windml name clash (section 4.3)
- [ ] Grant flips visibility himself. This check doesn't change it.

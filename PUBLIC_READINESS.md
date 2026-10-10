# Public readiness check: open-data-ml

First checked 2026-10-10 (MT) against `main` at commit 5ae138f. Updated 2026-10-10 after the pre-public cleanup (commits 5ce2116 and 579fbae). The repo is still **private**. Nothing here changes visibility, deploys, or posts anything.

## Verdict

**Ready to make public.** All three blockers are resolved. The only remaining step is for the owner to flip the repo's visibility on GitHub. No history rewrite was done or is needed.

## 1. Blockers (all resolved)

| # | Item | Status | Resolution |
|---|---|---|---|
| B1 | No `LICENSE` file at the repo root. | **Done** | MIT `LICENSE` added: "Copyright (c) 2026 Beehive AI Labs LLC" (commit 5ce2116). README.md has a License section saying the MIT License covers the code only, and that datasets keep their own licenses (Kelmarsh and Penmanshiel CC BY 4.0, attribution per `projects/windml/DATA_SOURCES.md`). |
| B2 | Employer IP confirmation in writing. | **Done** | Written IP confirmation from Nexio received 2026-10-10. |
| B3 | NASA C-MAPSS license is "not specified" on data.nasa.gov. | **Handled** | Option (b): `projects/windml/data/processed/cmapss_all.parquet` is no longer tracked (`git rm --cached`, commit 579fbae) and C-MAPSS patterns are in `.gitignore`. `projects/windml/scripts/download_cmapss.sh` fetches it from the official NASA PCoE source (SHA-256 checked), documented in `projects/windml/DATA_SOURCES.md`. `reports/schema_nasa_cmapss.md` stays as documentation (column names, units, row counts and min/max only, no data rows). **Note:** the parquet (7.5 MB) is still in git history (added in dee0925, removed in 579fbae), so anyone can recover it from a public clone. It is a presumed US Government work and low risk. The only way to remove it would be to publish a fresh-snapshot repo; force-pushing is not allowed. |

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
| NASA C-MAPSS | NASA PCoE | Presumed US Gov work; catalog says "not specified" | none (untracked in 579fbae; still in history) | Not redistributed. Users fetch it with `download_cmapss.sh` (B3) |
| NASA IMS bearings | excluded | no clear license | none, never in history | n/a |
| SKAB | excluded | copyleft | none, never in history | n/a |

Every license above allows commercial use and redistribution of changed versions, as long as you credit the source. None is non-commercial or share-alike. That matches DATA_POLICY.md.

**Raw data:** no raw files, zips, or excluded datasets show up anywhere in git history (checked every path ever committed). Only processed derivatives are tracked, as DATA_POLICY.md requires.

**Content of the event logs:** I scanned the 265 unique operator comments in the Kelmarsh and Penmanshiel status logs for names, emails, and phone numbers. Found none. They're short maintenance notes like "Annual Service", and Cubico already published them.

## 3. Secrets and personal info

Re-scanned 2026-10-10 after the cleanup, covering the tracked files at HEAD and the full history (`git log -p --all`).

- **Secrets:** no AWS access keys, private keys, or GitHub, Slack, OpenAI or Hugging Face tokens. No `password=`, `secret=` or `token=` assignments. **None found** in HEAD or in history.
- **AWS account IDs, ARNs, CloudFront and Route 53 IDs:** none. `site/DEPLOY.md` uses only placeholders (`<account-id>`, `<distribution-id>`, `<bucket>`, `<profile>`). The real deploy script is not in the repo.
- **Emails:** only `hello@beehivewebstudio.com` (the public contact) and the GitHub noreply address in commit metadata. This holds for history too.
- **Local laptop paths:** no `/Users/...` or home-directory paths, and no AWS profile names, in HEAD or history.
- **Commit identity:** every commit uses `51809789+7empestx@users.noreply.github.com`. The names "Grant Starkman" and "7empestx" will be public on the commits.
- **Box paths:** fixed 2026-10-10. Paths come from `projects/windml/src/windml/config.py` (`WINDML_RAW_DIR`, `WINDML_DATA_DIR`, `WINDML_REPORTS_DIR`, `WINDML_LOG_DIR`) with repo-relative defaults. No `/workspace` paths remain in code or docs.
- **Large files:** no tracked file or blob in history is over 50 MB. The largest is `kelmarsh_scada_labeled.parquet` at 47 MB, which is under GitHub's 100 MB hard limit. GitHub may warn about files over 50 MB on push, but none are that big.
- **PDF metadata:** the two condition-report PDFs show only a title and HeadlessChrome/Skia as producer. No author and no paths.

## 4. Not blocking, but should fix soon

1. **Dependency file:** done 2026-10-10. `projects/windml/requirements.txt` is pinned, and `make setup` installs it.
2. **Data-download scripts:** wind data done 2026-10-10 (`projects/windml/scripts/download_wind_data.py`, MD5-checked against Zenodo, plus `make smoke` and CI). The side datasets (UCI, PVDAQ and so on) still have no download script.
3. **Name clash: "windML".** An older, unmaintained project of the same name exists: github.com/cigroup-ol/windml (about 130 stars, windml.org), and it holds the PyPI name `windML` (v0.3.8). Using windml as a repo folder or site section is fine. Don't publish a PyPI package called `windml`, and say "not affiliated" somewhere, or think about a different name (for example `windml-scada` or `open-windml`). Before using either name as a brand, also run a USPTO search (free) for "open-data-ml" and "windml". `open-data-ml` isn't taken on PyPI.
4. **Repo size.** About 189 MB of loose objects, mostly the processed wind parquets (about 135 MB). That's under GitHub's limits, but cloning is slow. A later option is to move processed data to a Hugging Face dataset (also CC BY 4.0 with attribution) and keep git for code.
5. **Top-level README:** add a "not engineering advice" line and a data-credit block like the one on the site.
6. **`site/DEPLOY.md`** mentions Grant by name and describes AWS setup steps with placeholders only (no account ID, ARN, or bucket). Nothing sensitive, but you could move it to a private notes file if you don't want it public.

## 5. Before making it public

- [x] Add LICENSE (MIT, Beehive AI Labs LLC) (B1), commit 5ce2116
- [x] Employer IP confirmation in writing, received from Nexio on 2026-10-10 (B2)
- [x] C-MAPSS untracked, with a download script added (B3), commit 579fbae
- [ ] Optional: decide on the windml name clash (section 4.3). This doesn't block going public.
- [ ] **Remaining: the owner (Grant) flips repo visibility to public on GitHub.** This check doesn't change it.

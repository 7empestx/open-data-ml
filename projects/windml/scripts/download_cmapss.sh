#!/usr/bin/env bash
# Download NASA C-MAPSS (Turbofan Engine Degradation Simulation, Saxena & Goebel 2008)
# from the official NASA Ames Prognostics Center of Excellence (PCoE) data repository.
#
# The data is NOT committed to this repo: data.nasa.gov lists its license as "not specified".
# Fetch it yourself and review NASA's terms before redistributing.
#   Landing pages:
#     https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/
#     https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data
#   Cite: A. Saxena and K. Goebel (2008). "Turbofan Engine Degradation Simulation Data Set",
#         NASA Prognostics Data Repository, NASA Ames Research Center, Moffett Field, CA.
#
# Usage: projects/windml/scripts/download_cmapss.sh [DEST_DIR]
#   DEST_DIR defaults to $WINDML_RAW_DIR/nasa-cmapss, or /workspace/industrial-data/nasa-cmapss
#   (the raw path used by scripts/profile_and_clean.py). Then run profile_and_clean.py to rebuild
#   data/processed/cmapss_all.parquet locally (it is gitignored).
set -euo pipefail

URL="https://phm-datasets.s3.amazonaws.com/NASA/6.+Turbofan+Engine+Degradation+Simulation+Data+Set.zip"
# SHA-256 of the outer zip as served on 2026-10-10. Set CMAPSS_SKIP_SHA=1 if NASA republishes it.
SHA256="c9c5dec12a945a82e8bb4446589d7fb3cc057b5e5d81fa1a12e25ee9912ad3b2"

DEST="${1:-${WINDML_RAW_DIR:-/workspace/industrial-data}/nasa-cmapss}"
mkdir -p "$DEST"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "Downloading C-MAPSS from NASA PCoE..."
curl -fSL --retry 3 -o "$TMP/outer.zip" "$URL"

if [[ "${CMAPSS_SKIP_SHA:-0}" != "1" ]]; then
  echo "$SHA256  $TMP/outer.zip" | sha256sum -c -
fi

# The outer zip wraps CMAPSSData.zip, which holds the train/test/RUL text files.
unzip -q -o "$TMP/outer.zip" -d "$TMP/outer"
INNER="$(find "$TMP/outer" -name 'CMAPSSData.zip' | head -n 1)"
[[ -n "$INNER" ]] || { echo "CMAPSSData.zip not found in download" >&2; exit 1; }
unzip -q -o -j "$INNER" -d "$DEST"

cat > "$DEST/SOURCE.txt" <<SRC
Dataset: NASA C-MAPSS Turbofan Engine Degradation Simulation Data Set (Saxena & Goebel, 2008), NASA Ames PCoE
URL: $URL
License: not specified on data.nasa.gov (presumed US Government work, 17 USC 105). Not redistributed by open-data-ml.
Retrieved: $(date -u +%Y-%m-%d)
SRC

for f in train_FD001.txt test_FD001.txt RUL_FD001.txt train_FD004.txt; do
  [[ -f "$DEST/$f" ]] || { echo "Missing expected file $f" >&2; exit 1; }
done
echo "C-MAPSS files written to $DEST"

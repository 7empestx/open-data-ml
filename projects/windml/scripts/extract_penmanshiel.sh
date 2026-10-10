#!/bin/bash
# Extract every verified Penmanshiel SCADA zip into scada_<period>_<turbines>/ (dedup of padded rows; see extract_dedup.py)
cd /workspace/industrial-data/penmanshiel-wind-scada
for z in zips/Penmanshiel_SCADA_*.zip; do
  b=$(basename "$z" .zip)
  grep -qF "OK $b.zip" ../_dl/dl*.log* 2>/dev/null || { echo "skip (not verified yet) $b"; continue; }
  d=$(echo "$b" | sed -E 's/^Penmanshiel_SCADA_//; s/_[0-9]+$//; s/WT_?01-10/wt01-10/; s/WT_?11-15/wt11-15/; s/ /_/g' | tr 'A-Z' 'a-z')
  [ "$d" = "2021_wt11-15" ] && d="2021_wt11-15_v4461"
  dest="scada_$d"
  [ -f "$dest/.done" ] && continue
  echo "extract $b -> $dest"
  rm -rf "$dest"; python3 ../_tools/extract_dedup.py "$z" "$dest" > /dev/null && touch "$dest/.done"
done

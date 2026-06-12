#!/usr/bin/env bash
#
# Refresh the data behind the people visualizations
# (associated-people-2d / -3d / -hive).
#
# Pipeline:
#   1. download_network_data_assoicated.py -> associated_entities_raw.json
#   2. download_entity_lookup.py           -> people_lookup.json
#   3. scrub_dead_blocks.py                -> associated_entities_raw.cleaned.json, dead_blocks.txt
#   4. build_networks.py                   -> people_network.json, people_network.js
#
# The artworks pages (artworks-2d, artworks-hive) query the wikibase live
# and need no update.
#
# set -e matters here: build_networks.py prefers the *.cleaned.json file, so
# stopping on the first failure prevents building from a stale clean file
# that no longer matches a freshly downloaded raw file.

set -euo pipefail
cd "$(dirname "$0")"

echo "==> [1/4] Downloading document/entity associations (slow: one query per document)..."
uv run --with requests download_network_data_assoicated.py

echo "==> [2/4] Downloading people lookup (labels + images)..."
uv run --with requests download_entity_lookup.py

echo "==> [3/4] Scrubbing references to deleted blocks..."
uv run scrub_dead_blocks.py

echo "==> [4/4] Building people_network.json / people_network.js..."
uv run build_networks.py

echo
echo "Done. Updated files:"
ls -lh associated_entities_raw.json associated_entities_raw.cleaned.json \
       dead_blocks.txt people_lookup.json people_network.json people_network.js

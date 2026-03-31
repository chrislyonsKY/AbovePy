#!/bin/bash
# CLI Workflows — Common abovepy command-line patterns.
#
# Demonstrates:
# 1. Search with feet-based buffers
# 2. Provenance output for documentation
# 3. Download with concurrent workers
# 4. Estimate before download
# 5. Generate tile URLs for web maps

set -e

echo "=== Search with 500ft buffer ==="
abovepy search --point=-84.87,38.20 --buffer-feet 500 -p dem_phase3

echo ""
echo "=== Provenance metadata (JSON) ==="
abovepy search --county Franklin -p dem_phase3 --format provenance

echo ""
echo "=== Estimate download size ==="
abovepy estimate --county Franklin -p ortho_phase3

echo ""
echo "=== Download DEM tiles ==="
abovepy download --county Franklin -p dem_phase3 -o ./output/franklin_dem --workers 8

echo ""
echo "=== Generate hillshade tile URL ==="
abovepy tile-url --bbox=-84.9,38.15,-84.8,38.25 --algorithm hillshade

echo ""
echo "=== Preview image URL ==="
abovepy preview --county Franklin -p ortho_phase3

echo ""
echo "Done!"

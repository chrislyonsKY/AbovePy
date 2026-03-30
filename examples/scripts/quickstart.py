"""abovepy Quickstart — Search, download, and mosaic DEM tiles.

This script demonstrates the core abovepy workflow:
1. Search for tiles by county name
2. Estimate download size
3. Download matching tiles
4. Mosaic into a single VRT

Usage:
    python quickstart.py
"""

from pathlib import Path

import abovepy


def main():
    output_dir = Path("./output/quickstart")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Search for DEM Phase 3 tiles covering Franklin County (Frankfort)
    print("Searching for DEM tiles...")
    result = abovepy.search(county="Franklin", product="dem_phase3")
    print(result)  # SearchResult('dem_phase3', N tiles, ~X MB)

    # Estimate download size before committing
    est = result.estimate_size()
    print(f"Estimated download: {est['total_mb']} MB")

    # Download tiles (concurrent by default)
    print("\nDownloading tiles...")
    paths = result.download(output_dir=output_dir / "tiles")
    print(f"Downloaded {len(paths)} files")

    # Mosaic into a single VRT
    print("\nBuilding mosaic...")
    vrt = result.mosaic(output=output_dir / "franklin_dem.vrt")
    print(f"Mosaic created: {vrt}")


if __name__ == "__main__":
    main()

# Expected output:
# Searching for DEM tiles...
# SearchResult('dem_phase3', 342 tiles, ~1710.0 MB)
# Estimated download: 1710.0 MB
#
# Downloading tiles...
# Downloaded 342 files
#
# Building mosaic...
# Mosaic created: output/quickstart/franklin_dem.vrt

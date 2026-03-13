"""abovepy Quickstart — Search, download, and mosaic DEM tiles.

This script demonstrates the core abovepy workflow:
1. Search for tiles by county name
2. Download matching tiles
3. Mosaic into a single VRT

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
    tiles = abovepy.search(county="Franklin", product="dem_phase3")
    print(f"Found {len(tiles)} tiles")
    print(tiles[["tile_id", "file_size"]].head(10))

    # Download tiles
    print("\nDownloading tiles...")
    paths = abovepy.download(tiles, output_dir=output_dir / "tiles")
    print(f"Downloaded {len(paths)} files")

    # Mosaic into a single VRT
    print("\nBuilding mosaic...")
    vrt = abovepy.mosaic(paths, output=output_dir / "franklin_dem.vrt")
    print(f"Mosaic created: {vrt}")


if __name__ == "__main__":
    main()

# Expected output:
# Searching for DEM tiles...
# Found 342 tiles
#     tile_id                                    file_size
# 0   N087E279_2025_DEM_Phase3_cog.tif            1245678
# 1   N087E278_2025_DEM_Phase3_cog.tif            1198432
# ... (first 10 tiles shown)
#
# Downloading tiles...
# Downloaded 342 files
#
# Building mosaic...
# Mosaic created: output/quickstart/franklin_dem.vrt

"""LandXML Surface Export — DEM to TIN for Civil 3D, Carlson, and OpenRoads.

Demonstrates exporting a KyFromAbove DEM tile as a LandXML 1.2 TIN surface
that can be imported directly into:
  - AutoCAD Civil 3D (Import > LandXML)
  - Carlson Survey/Civil (File > Import LandXML)
  - Bentley OpenRoads Designer (File > Import > LandXML)

The export triangulates the DEM grid using Delaunay triangulation and writes
point coordinates in the DEM's native CRS (EPSG:3089, US Survey Feet).

Requirements:
    pip install abovepy[analysis]  # includes scipy for triangulation

Usage:
    python landxml_export.py
"""

from pathlib import Path

import abovepy
from abovepy.export import to_landxml


def main():
    output_dir = Path("./output/landxml")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Search for a DEM tile near the Kentucky State Capitol
    print("Searching for DEM tiles near Frankfort...")
    result = abovepy.search(
        point=(-84.87, 38.20),
        buffer_feet=2000,
        product="dem_phase3",
    )
    print(result)

    if result.empty:
        print("No tiles found.")
        return

    # Read the first tile as a numpy array
    tile_url = result.tiles.iloc[0]["asset_url"]
    print(f"\nReading DEM tile: {tile_url}")
    data, profile = abovepy.read(tile_url)
    print(f"  Shape: {data.shape}")
    print(f"  CRS: {profile.get('crs')}")
    print(f"  Dtype: {profile.get('dtype')}")

    # Export full resolution LandXML
    print("\nExporting full resolution LandXML...")
    full_path = to_landxml(
        data, profile,
        output=output_dir / "frankfort_dem_full.xml",
        surface_name="Frankfort DEM Phase 3",
    )
    size_mb = full_path.stat().st_size / (1024 * 1024)
    print(f"  Written: {full_path} ({size_mb:.1f} MB)")

    # Export decimated version (every 4th pixel — 1/16 the points)
    print("\nExporting decimated LandXML (decimate=4)...")
    dec_path = to_landxml(
        data, profile,
        output=output_dir / "frankfort_dem_decimated.xml",
        surface_name="Frankfort DEM Phase 3 (decimated)",
        decimate=4,
    )
    dec_size_mb = dec_path.stat().st_size / (1024 * 1024)
    print(f"  Written: {dec_path} ({dec_size_mb:.1f} MB)")

    print(f"\nSize reduction: {size_mb:.1f} MB → {dec_size_mb:.1f} MB "
          f"({dec_size_mb/size_mb*100:.0f}%)")

    print("\nTo import in Civil 3D:")
    print("  1. Open Civil 3D")
    print("  2. Insert tab > Import > Import LandXML")
    print(f"  3. Browse to {full_path.resolve()}")
    print("  4. The TIN surface will appear in your drawing")


if __name__ == "__main__":
    main()

# Expected output:
# Searching for DEM tiles near Frankfort...
# SearchResult('dem_phase3', N tile(s), ~X MB)
#
# Reading DEM tile: https://...
#   Shape: (1, XXXX, XXXX)
#   CRS: EPSG:3089
#   Dtype: float32
#
# Exporting full resolution LandXML...
#   Written: output/landxml/frankfort_dem_full.xml (XX.X MB)
#
# Exporting decimated LandXML (decimate=4)...
#   Written: output/landxml/frankfort_dem_decimated.xml (X.X MB)
#
# Size reduction: XX.X MB → X.X MB (X%)
#
# To import in Civil 3D:
#   1. Open Civil 3D
#   2. Insert tab > Import > Import LandXML
#   3. Browse to ...\frankfort_dem_full.xml
#   4. The TIN surface will appear in your drawing

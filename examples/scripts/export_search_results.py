"""Export search results to GeoJSON, GeoPackage, and CSV.

Demonstrates how to take abovepy search results (a GeoDataFrame) and
export them to standard GIS interchange formats for use in QGIS,
ArcGIS Pro, or other tools.

Usage:
    python export_search_results.py
"""

from pathlib import Path

import abovepy


def main():
    output_dir = Path("./output/exports")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Search for DEM tiles covering Fayette County (Lexington)
    print("=== Searching DEM Phase 3 — Fayette County ===")
    tiles = abovepy.search(county="Fayette", product="dem_phase3")
    print(f"Found {len(tiles)} tiles")
    print(f"Columns: {list(tiles.columns)}")
    print(f"CRS: {tiles.crs}\n")

    if len(tiles) == 0:
        print("No tiles found.")
        return

    # Preview the data
    print("=== Preview ===")
    print(tiles[["tile_id", "product", "file_size"]].head(5).to_string(index=False))

    # Export to GeoJSON — widely supported, text-based
    geojson_path = output_dir / "fayette_dem_tiles.geojson"
    tiles.to_file(str(geojson_path), driver="GeoJSON")
    print(f"\nGeoJSON:    {geojson_path} ({geojson_path.stat().st_size / 1024:.1f} KB)")

    # Export to GeoPackage — efficient binary format, good for large datasets
    gpkg_path = output_dir / "fayette_dem_tiles.gpkg"
    tiles.to_file(str(gpkg_path), driver="GPKG", layer="dem_tiles")
    print(f"GeoPackage: {gpkg_path} ({gpkg_path.stat().st_size / 1024:.1f} KB)")

    # Export to CSV — for spreadsheet / non-GIS use (geometry as WKT)
    csv_path = output_dir / "fayette_dem_tiles.csv"
    csv_df = tiles.copy()
    csv_df["geometry_wkt"] = csv_df.geometry.to_wkt()
    csv_df.drop(columns=["geometry"]).to_csv(str(csv_path), index=False)
    print(f"CSV:        {csv_path} ({csv_path.stat().st_size / 1024:.1f} KB)")

    # Show how to reload
    print("\n=== Reload Examples ===")
    print("  import geopandas as gpd")
    print(f'  tiles = gpd.read_file("{geojson_path}")  # GeoJSON')
    print(f'  tiles = gpd.read_file("{gpkg_path}", layer="dem_tiles")  # GeoPackage')
    print(f'  tiles = pd.read_csv("{csv_path}")  # CSV (no geometry)')


if __name__ == "__main__":
    main()


# Expected output:
# =================================================================
# === Searching DEM Phase 3 — Fayette County ===
# Found 62 tiles
# Columns: ['tile_id', 'product', 'geometry', 'asset_url', 'file_size', 'datetime', 'collection_id']
# CRS: EPSG:4326
#
# === Preview ===
#  tile_id    product  file_size
# N160E243  dem_phase3   23456789
# N160E244  dem_phase3   23012456
# N160E245  dem_phase3   22890123
# N161E243  dem_phase3   24567890
# N161E244  dem_phase3   23678901
#
# GeoJSON:    output/exports/fayette_dem_tiles.geojson (48.2 KB)
# GeoPackage: output/exports/fayette_dem_tiles.gpkg (36.0 KB)
# CSV:        output/exports/fayette_dem_tiles.csv (12.8 KB)
#
# === Reload Examples ===
#   import geopandas as gpd
#   tiles = gpd.read_file("output/exports/fayette_dem_tiles.geojson")  # GeoJSON
#   tiles = gpd.read_file("output/exports/fayette_dem_tiles.gpkg", layer="dem_tiles")  # GeoPackage
#   tiles = pd.read_csv("output/exports/fayette_dem_tiles.csv")  # CSV (no geometry)
# =================================================================

"""Explore available KyFromAbove data products.

Lists all products, their formats, resolutions, and collection IDs.

Usage:
    python explore_products.py
"""

import abovepy


def main():
    # List all available products
    print("=== KyFromAbove Data Products ===\n")
    info = abovepy.info()
    print(info.to_string(index=False))

    # Show details for a specific product
    print("\n=== DEM Phase 3 Details ===\n")
    products = abovepy.list_products()
    dem3 = products["dem_phase3"]
    print(f"  Key:           {dem3.key}")
    print(f"  Display Name:  {dem3.display_name}")
    print(f"  Collection ID: {dem3.collection_id}")
    print(f"  Format:        {dem3.format}")
    print(f"  Resolution:    {dem3.resolution}")
    print(f"  Phase:         {dem3.phase}")
    print(f"  Native CRS:    {dem3.native_crs}")

    # Quick tile count for a county
    print("\n=== Tile counts for Franklin County ===\n")
    for product_key in ["dem_phase3", "ortho_phase3", "laz_phase2"]:
        try:
            tiles = abovepy.search(county="Franklin", product=product_key)
            print(f"  {product_key}: {len(tiles)} tiles")
        except Exception as e:
            print(f"  {product_key}: error — {e}")


if __name__ == "__main__":
    main()

# Expected output:
# === KyFromAbove Data Products ===
#
#      product            display_name collection_id format resolution  phase       crs
#   dem_phase1     DEM Phase 1 (5ft)    dem-phase1    COG        5ft      1  EPSG:3089
#   dem_phase2     DEM Phase 2 (2ft)    dem-phase2    COG        2ft      2  EPSG:3089
#   dem_phase3     DEM Phase 3 (2ft)    dem-phase3    COG        2ft      3  EPSG:3089
#   ortho_phase1   Orthoimagery ...   orthos-phase1   COG        6in      1  EPSG:3089
#   ... (9 rows total)
#
# === DEM Phase 3 Details ===
#
#   Key:           dem_phase3
#   Display Name:  DEM Phase 3 (2ft)
#   Collection ID: dem-phase3
#   Format:        COG
#   Resolution:    2ft
#   Phase:         3
#   Native CRS:    EPSG:3089
#
# === Tile counts for Franklin County ===
#
#   dem_phase3: 342 tiles
#   ortho_phase3: 342 tiles
#   laz_phase2: 342 tiles

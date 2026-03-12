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

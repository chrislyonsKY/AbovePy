"""Batch search across multiple Kentucky counties.

Iterates over a list of counties, searches DEM Phase 3 tiles for each,
and aggregates results into a single GeoDataFrame. Demonstrates an
operational batch workflow for multi-county planning projects.

Usage:
    python batch_county_search.py
"""

import pandas as pd

import abovepy


def main():
    counties = ["Franklin", "Fayette", "Jefferson", "Pike"]
    product = "dem_phase3"

    print(f"=== Batch Search: {product} ===\n")

    all_tiles = []
    summary = []

    for county in counties:
        print(f"Searching {county} County...")
        tiles = abovepy.search(county=county, product=product)

        total_mb = tiles.file_size.sum() / (1024 * 1024) if len(tiles) > 0 else 0.0

        summary.append({
            "county": county,
            "tile_count": len(tiles),
            "total_mb": round(total_mb, 1),
        })
        all_tiles.append(tiles)
        print(f"  -> {len(tiles)} tiles ({total_mb:.1f} MB)")

    # Combine into one GeoDataFrame
    combined = pd.concat(all_tiles, ignore_index=True)

    # Summary table
    print("\n=== Summary ===")
    summary_df = pd.DataFrame(summary)
    print(summary_df.to_string(index=False))

    print(f"\nTotal: {len(combined)} tiles across {len(counties)} counties")
    grand_total_mb = summary_df.total_mb.sum()
    print(f"Estimated download: {grand_total_mb:.1f} MB ({grand_total_mb / 1024:.1f} GB)")

    # Show unique tile IDs (some counties may share border tiles)
    unique_tiles = combined.tile_id.nunique()
    if unique_tiles < len(combined):
        dupes = len(combined) - unique_tiles
        print(f"Note: {dupes} duplicate tiles found at county borders")


if __name__ == "__main__":
    main()


# Expected output:
# =================================================================
# === Batch Search: dem_phase3 ===
#
# Searching Franklin County...
#   -> 48 tiles (1104.2 MB)
# Searching Fayette County...
#   -> 62 tiles (1426.0 MB)
# Searching Jefferson County...
#   -> 185 tiles (4255.0 MB)
# Searching Pike County...
#   -> 210 tiles (4830.0 MB)
#
# === Summary ===
#  county  tile_count  total_mb
# Franklin          48    1104.2
# Fayette           62    1426.0
# Jefferson        185    4255.0
#     Pike         210    4830.0
#
# Total: 505 tiles across 4 counties
# Estimated download: 11615.2 MB (11.3 GB)
# Note: 3 duplicate tiles found at county borders
# =================================================================

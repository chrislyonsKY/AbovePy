"""Compare DEM Phase 1 (5ft) vs Phase 3 (2ft) for the same area.

Searches both DEM phases for a bbox near Frankfort, KY, compares tile
counts, then reads a small window from each to compare resolution and
elevation statistics. Useful for deciding which phase to use.

Usage:
    python compare_dem_phases.py
"""

import abovepy


def main():
    # Small area in downtown Frankfort, KY (state capitol area)
    bbox = (-84.88, 38.18, -84.86, 38.20)

    # Search Phase 1 (5ft resolution) and Phase 3 (2ft resolution)
    print("=== Searching DEM Phase 1 (5ft) ===")
    result_p1 = abovepy.search(bbox=bbox, product="dem_phase1")
    print(result_p1)

    print("\n=== Searching DEM Phase 3 (2ft) ===")
    result_p3 = abovepy.search(bbox=bbox, product="dem_phase3")
    print(result_p3)

    # Compare coverage using SearchResult.compare()
    print("\n=== Spatial Overlap ===")
    overlap = result_p1.compare(result_p3)
    print(f"  {len(overlap)} overlapping tile pairs")

    # Estimate sizes
    print("\n=== Size Estimates ===")
    for label, result in [("Phase 1", result_p1), ("Phase 3", result_p3)]:
        est = result.estimate_size()
        print(f"  {label}: {est['tile_count']} tiles, ~{est['total_mb']} MB")

    # Read the same window from both phases
    print("\n=== Reading window from each phase ===")
    print(f"    bbox: {bbox}")

    tiles_p1 = result_p1.tiles
    tiles_p3 = result_p3.tiles

    if not result_p1.empty:
        data_p1, prof_p1 = abovepy.read(
            tiles_p1.iloc[0].asset_url, bbox=bbox, crs="EPSG:4326"
        )
        res_p1 = prof_p1["transform"][0]
        print("\n  Phase 1 (5ft):")
        print(f"    Array shape:  {data_p1.shape}")
        print(f"    Pixel size:   {res_p1:.2f} ft")
        print(f"    Elevation:    min={data_p1.min():.1f}  max={data_p1.max():.1f}  "
              f"mean={data_p1.mean():.1f}")

    if not result_p3.empty:
        data_p3, prof_p3 = abovepy.read(
            tiles_p3.iloc[0].asset_url, bbox=bbox, crs="EPSG:4326"
        )
        res_p3 = prof_p3["transform"][0]
        print("\n  Phase 3 (2ft):")
        print(f"    Array shape:  {data_p3.shape}")
        print(f"    Pixel size:   {res_p3:.2f} ft")
        print(f"    Elevation:    min={data_p3.min():.1f}  max={data_p3.max():.1f}  "
              f"mean={data_p3.mean():.1f}")

    if not result_p1.empty and not result_p3.empty:
        ratio = data_p3.shape[1] / data_p1.shape[1]
        print(f"\n  Phase 3 has ~{ratio:.1f}x more pixels per axis than Phase 1")


if __name__ == "__main__":
    main()

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
    tiles_p1 = abovepy.search(bbox=bbox, product="dem_phase1")
    print(f"Found {len(tiles_p1)} tiles")

    print("\n=== Searching DEM Phase 3 (2ft) ===")
    tiles_p3 = abovepy.search(bbox=bbox, product="dem_phase3")
    print(f"Found {len(tiles_p3)} tiles")

    # Compare tile metadata
    print("\n=== Tile Comparison ===")
    for label, tiles in [("Phase 1", tiles_p1), ("Phase 3", tiles_p3)]:
        if len(tiles) > 0:
            total_mb = tiles.file_size.sum() / (1024 * 1024)
            print(f"  {label}: {len(tiles)} tiles, {total_mb:.1f} MB total")

    # Read the same window from both phases
    print("\n=== Reading window from each phase ===")
    print(f"    bbox: {bbox}")

    if len(tiles_p1) > 0:
        data_p1, prof_p1 = abovepy.read(
            tiles_p1.iloc[0].asset_url, bbox=bbox, crs="EPSG:4326"
        )
        res_p1 = prof_p1["transform"][0]
        print("\n  Phase 1 (5ft):")
        print(f"    Array shape:  {data_p1.shape}")
        print(f"    Pixel size:   {res_p1:.2f} ft")
        print(f"    Elevation:    min={data_p1.min():.1f}  max={data_p1.max():.1f}  "
              f"mean={data_p1.mean():.1f}")

    if len(tiles_p3) > 0:
        data_p3, prof_p3 = abovepy.read(
            tiles_p3.iloc[0].asset_url, bbox=bbox, crs="EPSG:4326"
        )
        res_p3 = prof_p3["transform"][0]
        print("\n  Phase 3 (2ft):")
        print(f"    Array shape:  {data_p3.shape}")
        print(f"    Pixel size:   {res_p3:.2f} ft")
        print(f"    Elevation:    min={data_p3.min():.1f}  max={data_p3.max():.1f}  "
              f"mean={data_p3.mean():.1f}")

    if len(tiles_p1) > 0 and len(tiles_p3) > 0:
        ratio = data_p3.shape[1] / data_p1.shape[1]
        print(f"\n  Phase 3 has ~{ratio:.1f}x more pixels per axis than Phase 1")


if __name__ == "__main__":
    main()


# Expected output:
# =================================================================
# === Searching DEM Phase 1 (5ft) ===
# Found 2 tiles
#
# === Searching DEM Phase 3 (2ft) ===
# Found 2 tiles
#
# === Tile Comparison ===
#   Phase 1: 2 tiles, 8.4 MB total
#   Phase 3: 2 tiles, 45.2 MB total
#
# === Reading window from each phase ===
#     bbox: (-84.88, 38.18, -84.86, 38.2)
#
#   Phase 1 (5ft):
#     Array shape:  (1, 145, 120)
#     Pixel size:   5.00 ft
#     Elevation:    min=502.3  max=812.6  mean=648.1
#
#   Phase 3 (2ft):
#     Array shape:  (1, 362, 300)
#     Pixel size:   2.00 ft
#     Elevation:    min=501.8  max=813.2  mean=647.9
#
#   Phase 3 has ~2.5x more pixels per axis than Phase 1
# =================================================================

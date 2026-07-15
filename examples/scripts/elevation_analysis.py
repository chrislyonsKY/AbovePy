"""Elevation analysis one-liners — sample, profile, zonal stats, change.

Demonstrates the v2.2 analysis APIs. Everything streams windowed reads
from the KyFromAbove COGs — nothing is downloaded.

Usage:
    python elevation_analysis.py

Requires:
    pip install abovepy
"""

from shapely.geometry import box

import abovepy

# Frankfort, on the Kentucky River bluffs
POINT = (-84.8715, 38.1867)
TRANSECT = [(-84.90, 38.17), (-84.84, 38.20)]
AOI = box(-84.88, 38.17, -84.85, 38.20)
BBOX = (-84.88, 38.17, -84.85, 38.20)


def main():
    print("=== Point elevation ===")
    elev = abovepy.sample(POINT)
    print(f"  Elevation at {POINT}: {elev:.1f} ft")

    print("\n=== Cross-valley profile ===")
    df = abovepy.profile(TRANSECT, n_points=50)
    print(f"  {len(df)} samples over {df.distance_ft.iloc[-1]:.0f} ft")
    print(f"  Elevation range: {df.elevation.min():.0f}–{df.elevation.max():.0f} ft")

    print("\n=== Zonal statistics ===")
    stats = abovepy.zonal_stats(AOI)
    print(f"  mean {stats['mean']:.1f} ft over {stats['cell_count']:,} cells")
    print(f"  min {stats['min']:.1f} / max {stats['max']:.1f} / std {stats['std']:.1f}")

    print("\n=== Phase 2 → Phase 3 change detection ===")
    diff, _profile = abovepy.change_detection(
        BBOX, product_before="dem_phase2", product_after="dem_phase3"
    )
    import numpy as np

    print(f"  Mean change: {np.nanmean(diff):+.2f} ft")
    print(f"  Max cut: {np.nanmin(diff):+.1f} ft, max fill: {np.nanmax(diff):+.1f} ft")


if __name__ == "__main__":
    main()

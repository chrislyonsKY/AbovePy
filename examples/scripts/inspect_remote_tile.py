"""Inspect a remote KyFromAbove tile without downloading it.

Uses abovepy.info() to read metadata from a cloud-hosted COG, then
uses abovepy.read() with a small bbox to fetch just the pixels needed.
Demonstrates zero-download inspection and windowed streaming.

Usage:
    python inspect_remote_tile.py
"""

import abovepy


def main():
    # First, find a tile to inspect
    print("=== Finding a DEM tile near Lexington ===")
    tiles = abovepy.search(
        bbox=(-84.50, 38.03, -84.48, 38.05),
        product="dem_phase3",
    )
    print(f"Found {len(tiles)} tiles\n")

    if len(tiles) == 0:
        print("No tiles found.")
        return

    tile_url = tiles.iloc[0].asset_url
    tile_id = tiles.iloc[0].tile_id

    # Inspect metadata without downloading any pixels
    print(f"=== Inspecting tile: {tile_id} ===")
    print(f"URL: {tile_url}\n")

    metadata = abovepy.info(tile_url)
    for key, value in metadata.items():
        print(f"  {key:12s}: {value}")

    # Read a small window — only the bytes within the bbox are fetched
    read_bbox = (-84.50, 38.03, -84.49, 38.04)
    print("\n=== Windowed Read ===")
    print(f"bbox: {read_bbox}")

    data, profile = abovepy.read(tile_url, bbox=read_bbox, crs="EPSG:4326")

    print(f"\n  Shape:      {data.shape}")
    print(f"  Dtype:      {data.dtype}")
    print(f"  CRS:        {profile['crs']}")
    print(f"  Pixel size: {profile['transform'][0]:.2f} x "
          f"{-profile['transform'][4]:.2f} ft")
    print(f"  Elevation:  min={data.min():.1f}  max={data.max():.1f}  "
          f"mean={data.mean():.1f}")
    print("\nNo files downloaded — all data streamed via /vsicurl/.")


if __name__ == "__main__":
    main()


# Expected output:
# =================================================================
# === Finding a DEM tile near Lexington ===
# Found 1 tiles
#
# === Inspecting tile: N162E245 ===
# URL: https://s3.us-west-2.amazonaws.com/kyfromabove/dem-phase3/N162E245.tif
#
#   path        : https://s3.us-west-2.amazonaws.com/kyfromabove/dem-phase3/N162E245.tif
#   width       : 2500
#   height      : 2500
#   crs         : EPSG:3089
#   bounds      : (1225000.0, 810000.0, 1230000.0, 815000.0)
#   dtype       : float32
#   band_count  : 1
#   driver      : GTiff
#   nodata      : -9999.0
#   transform   : (2.0, 0.0, 1225000.0, 0.0, -2.0, 815000.0, 0.0, 0.0, 1.0)
#
# === Windowed Read ===
# bbox: (-84.5, 38.03, -84.49, 38.04)
#
#   Shape:      (1, 180, 148)
#   Dtype:      float32
#   CRS:        EPSG:3089
#   Pixel size: 2.00 x 2.00 ft
#   Elevation:  min=925.4  max=1012.8  mean=968.7
#
# No files downloaded — all data streamed via /vsicurl/.
# =================================================================

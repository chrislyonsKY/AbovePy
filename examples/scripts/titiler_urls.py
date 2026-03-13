"""Generate TiTiler URLs for web map integration.

Searches for a DEM tile, generates TiTiler tile/preview/stats URLs,
and fetches raster statistics via httpx. Demonstrates how abovepy
connects cloud-hosted tiles to web mapping frameworks.

Usage:
    python titiler_urls.py

Note:
    This script generates valid TiTiler URLs for any TiTiler instance.
    The stats fetch requires a running TiTiler (e.g., via docker-compose).
    See examples/docker-compose.yml to run TiTiler locally.
"""

import abovepy
from abovepy.titiler import cog_preview_url, cog_stats_url, cog_tile_url


def main():
    # Find a DEM tile near Frankfort
    print("=== Searching for a DEM tile ===")
    tiles = abovepy.search(
        bbox=(-84.88, 38.18, -84.86, 38.20),
        product="dem_phase3",
    )
    print(f"Found {len(tiles)} tiles")

    if len(tiles) == 0:
        print("No tiles found.")
        return

    cog_url = tiles.iloc[0].asset_url
    tile_id = tiles.iloc[0].tile_id
    print(f"Using tile: {tile_id}")
    print(f"COG URL:    {cog_url}\n")

    # Generate TiTiler URLs (default endpoint: https://titiler.xyz)
    print("=== TiTiler URLs (default endpoint) ===")
    tile_url = cog_tile_url(cog_url)
    preview_url = cog_preview_url(cog_url, max_size=512)
    stats_url = cog_stats_url(cog_url)

    print(f"  TileJSON: {tile_url}")
    print(f"  Preview:  {preview_url}")
    print(f"  Stats:    {stats_url}")

    # Generate for a local TiTiler instance
    local_endpoint = "http://localhost:8000"
    print(f"\n=== TiTiler URLs (local: {local_endpoint}) ===")
    local_tile_url = cog_tile_url(cog_url, titiler_endpoint=local_endpoint)
    local_stats_url = cog_stats_url(cog_url, titiler_endpoint=local_endpoint)

    print(f"  TileJSON: {local_tile_url}")
    print(f"  Stats:    {local_stats_url}")

    # Fetch stats from a running TiTiler (optional — requires live server)
    print("\n=== Fetching Stats (requires running TiTiler) ===")
    try:
        import httpx

        resp = httpx.get(local_stats_url, timeout=10)
        resp.raise_for_status()
        stats = resp.json()

        for band_name, band_stats in stats.items():
            print(f"  {band_name}:")
            print(f"    min:    {band_stats['min']:.2f}")
            print(f"    max:    {band_stats['max']:.2f}")
            print(f"    mean:   {band_stats['mean']:.2f}")
            print(f"    stddev: {band_stats['std']:.2f}")
    except httpx.ConnectError:
        print("  TiTiler not running at localhost:8000.")
        print("  Start it with: docker compose -f examples/docker-compose.yml up")
    except Exception as e:
        print(f"  Could not fetch stats: {e}")

    # Show how to use the TileJSON URL in a web map
    print("\n=== MapLibre GL JS Usage ===")
    print("  Add this source to your MapLibre map:")
    print('  map.addSource("dem", {')
    print('    type: "raster",')
    print(f'    url: "{local_tile_url}"')
    print("  });")


if __name__ == "__main__":
    main()


# Expected output:
# =================================================================
# === Searching for a DEM tile ===
# Found 2 tiles
# Using tile: N163E227
# COG URL:    https://s3.us-west-2.amazonaws.com/kyfromabove/dem-phase3/N163E227.tif
#
# === TiTiler URLs (default endpoint) ===
#   TileJSON: https://titiler.xyz/cog/tilejson.json?url=https%3A%2F%2Fs3.us-west-2...
#   Preview:  https://titiler.xyz/cog/preview.png?url=https%3A%2F%2Fs3.us-west-2...&max_size=512
#   Stats:    https://titiler.xyz/cog/statistics?url=https%3A%2F%2Fs3.us-west-2...
#
# === TiTiler URLs (local: http://localhost:8000) ===
#   TileJSON: http://localhost:8000/cog/tilejson.json?url=https%3A%2F%2Fs3.us-west-2...
#   Stats:    http://localhost:8000/cog/statistics?url=https%3A%2F%2Fs3.us-west-2...
#
# === Fetching Stats (requires running TiTiler) ===
#   TiTiler not running at localhost:8000.
#   Start it with: docker compose -f examples/docker-compose.yml up
#
# === MapLibre GL JS Usage ===
#   Add this source to your MapLibre map:
#   map.addSource("dem", {
#     type: "raster",
#     url: "http://localhost:8000/cog/tilejson.json?url=https%3A%2F%2Fs3.us-west-2..."
#   });
# =================================================================

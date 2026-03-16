"""Generate TiTiler URLs for web map integration.

Demonstrates three tiers of tile URL generation:
  1. COG URLs — standalone TiTiler (individual COG files)
  2. pgSTAC collection URLs — collection-based (no individual URLs needed)
  3. Terrain algorithm URLs — server-side hillshade, slope, contours
  4. Registered search URLs — persistent virtual mosaics

Usage:
    python titiler_urls.py

Note:
    All URL generation is local (no HTTP calls except the search registration
    demo). The KyFromAbove TiTiler endpoints are used by default.
"""

import abovepy
from abovepy.searches import (
    search_info_url,
    search_map_url,
    search_tile_url,
)
from abovepy.titiler import (
    cog_preview_url,
    cog_stats_url,
    cog_tile_url,
    collection_map_url,
    collection_tile_url,
    contour_tile_url,
    hillshade_tile_url,
    slope_tile_url,
    terrain_rgb_tile_url,
)
from abovepy.viz import tile_url, preview_url


def main():
    # ---------------------------------------------------------------
    # 1. COG tile URLs (standalone TiTiler)
    # ---------------------------------------------------------------
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

    print("=== COG Tile URLs (standalone TiTiler) ===")
    print(f"  TileJSON: {cog_tile_url(cog_url)}")
    print(f"  Preview:  {cog_preview_url(cog_url, max_size=512)}")
    print(f"  Stats:    {cog_stats_url(cog_url)}")

    # ---------------------------------------------------------------
    # 2. pgSTAC collection URLs (no individual COG URLs needed)
    # ---------------------------------------------------------------
    print("\n=== pgSTAC Collection URLs ===")
    print("  These only need a product name + optional bbox — no COG URLs!")
    bbox = (-84.9, 38.15, -84.8, 38.25)

    print(f"  DEM tiles:   {collection_tile_url('dem_phase3', bbox=bbox)}")
    print(f"  Ortho tiles: {collection_tile_url('ortho_phase3', bbox=bbox)}")
    print(f"  Map viewer:  {collection_map_url('dem_phase3', bbox=bbox)}")

    # ---------------------------------------------------------------
    # 3. Terrain analysis URLs (server-side algorithms)
    # ---------------------------------------------------------------
    print("\n=== Terrain Analysis URLs ===")
    print(f"  Hillshade:   {hillshade_tile_url(bbox=bbox)}")
    print(f"  Slope:       {slope_tile_url(bbox=bbox)}")
    print(f"  Contours:    {contour_tile_url(bbox=bbox, increment=50)}")
    print(f"  Terrain RGB: {terrain_rgb_tile_url(bbox=bbox)}")

    # ---------------------------------------------------------------
    # 4. Viz convenience helpers
    # ---------------------------------------------------------------
    print("\n=== Viz Convenience Helpers ===")
    print(f"  tile_url (DEM):       {tile_url('dem_phase3', bbox=bbox)}")
    print(f"  tile_url (hillshade): {tile_url('dem_phase3', bbox=bbox, algorithm='hillshade')}")
    print(f"  tile_url (county):    {tile_url('dem_phase3', county='Franklin')}")
    print(f"  preview_url:          {preview_url('dem_phase3', bbox=bbox)}")

    # ---------------------------------------------------------------
    # 5. Registered search (persistent virtual mosaic)
    # ---------------------------------------------------------------
    print("\n=== Registered Search (requires network) ===")
    try:
        search_id = abovepy.register_search("dem_phase3", bbox=bbox)
        print(f"  Search ID:  {search_id}")
        print(f"  TileJSON:   {search_tile_url(search_id)}")
        print(f"  Map viewer: {search_map_url(search_id)}")
        print(f"  Info:       {search_info_url(search_id)}")
    except Exception as e:
        print(f"  Could not register search: {e}")
        print("  (This requires the TiTiler-pgSTAC endpoint to be running)")

    # ---------------------------------------------------------------
    # MapLibre GL JS usage example
    # ---------------------------------------------------------------
    print("\n=== MapLibre GL JS Usage ===")
    hs_url = hillshade_tile_url(bbox=bbox)
    print("  Add this source to your MapLibre map:")
    print('  map.addSource("hillshade", {')
    print('    type: "raster",')
    print(f'    url: "{hs_url}"')
    print("  });")


if __name__ == "__main__":
    main()

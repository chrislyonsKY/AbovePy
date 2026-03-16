"""pgSTAC Collection Viewer — browse entire collections as map tiles.

Demonstrates TiTiler-pgSTAC collection endpoints — the simplest way
to serve dynamic map tiles from KyFromAbove data. No individual COG
URLs needed; just specify a product name and optional bbox.

Usage:
    python pgstac_collection_viewer.py

Requires:
    pip install abovepy
"""

from abovepy.titiler import (
    collection_bbox_url,
    collection_info_url,
    collection_map_url,
    collection_point_url,
    collection_tile_url,
    item_info_url,
    item_preview_url,
    item_tile_url,
)


def main():
    bbox = (-84.9, 38.15, -84.8, 38.25)  # Frankfort area

    # ---------------------------------------------------------------
    # Collection-level URLs (whole collection, server picks tiles)
    # ---------------------------------------------------------------
    print("=== Collection-Level URLs ===")
    print("  No individual COG URLs needed — just product + bbox.\n")

    products = ["dem_phase3", "ortho_phase3", "dem_phase1"]
    for prod in products:
        tile = collection_tile_url(prod, bbox=bbox)
        print(f"  {prod}:")
        print(f"    TileJSON: {tile[:80]}...")
        print(f"    Info:     {collection_info_url(prod)}")
        print(f"    Map:      {collection_map_url(prod, bbox=bbox)[:80]}...")
        print()

    # ---------------------------------------------------------------
    # Bbox image render (server composites and returns a PNG)
    # ---------------------------------------------------------------
    print("=== Bbox Image Renders ===")
    print("  Get a rendered PNG of any area — server composites on the fly.\n")

    dem_img = collection_bbox_url(
        "dem_phase3", bbox=bbox, width=1024, height=1024, fmt="png",
        colormap_name="viridis", rescale="400,1200",
    )
    print(f"  DEM (viridis): {dem_img[:80]}...")

    ortho_img = collection_bbox_url(
        "ortho_phase3", bbox=bbox, width=1024, height=1024, fmt="png",
    )
    print(f"  Ortho (RGB):   {ortho_img[:80]}...")

    # ---------------------------------------------------------------
    # Point queries (get pixel values at a coordinate)
    # ---------------------------------------------------------------
    print("\n=== Point Queries ===")
    print("  Query the elevation or pixel value at any coordinate.\n")

    points = [
        ("KY Capitol", -84.8763, 38.1867),
        ("KY River Bridge", -84.8680, 38.2010),
        ("Frankfort Cemetery", -84.8720, 38.2050),
    ]
    for name, lon, lat in points:
        url = collection_point_url("dem_phase3", lon=lon, lat=lat)
        print(f"  {name} ({lon}, {lat}):")
        print(f"    {url}")

    # ---------------------------------------------------------------
    # Item-level URLs (single STAC item / tile)
    # ---------------------------------------------------------------
    print("\n=== Item-Level URLs ===")
    print("  For when you know the exact tile ID.\n")

    item_id = "N163E227"
    print(f"  Item: {item_id}")
    print(f"    TileJSON: {item_tile_url('dem_phase3', item_id)[:80]}...")
    print(f"    Preview:  {item_preview_url('dem_phase3', item_id, max_size=512)[:80]}...")
    print(f"    Info:     {item_info_url('dem_phase3', item_id)}")

    # ---------------------------------------------------------------
    # Colormap options
    # ---------------------------------------------------------------
    print("\n=== Colormap Options for DEM ===")
    print("  Pass colormap_name= to any URL builder.\n")

    colormaps = ["viridis", "cividis", "inferno", "terrain", "gray"]
    for cmap in colormaps:
        url = collection_tile_url(
            "dem_phase3", bbox=bbox, colormap_name=cmap, rescale="400,1200",
        )
        print(f"  {cmap:10s}: {url[:80]}...")

    # ---------------------------------------------------------------
    # Usage with MapLibre / Leaflet
    # ---------------------------------------------------------------
    tile = collection_tile_url("dem_phase3", bbox=bbox,
                               colormap_name="viridis", rescale="400,1200")
    print("\n=== MapLibre GL JS Integration ===")
    print("  map.addSource('kfa-dem', {")
    print("    type: 'raster',")
    print(f"    url: '{tile}',")
    print("    tileSize: 256")
    print("  });")
    print("  map.addLayer({")
    print("    id: 'kfa-dem-layer',")
    print("    type: 'raster',")
    print("    source: 'kfa-dem',")
    print("    paint: { 'raster-opacity': 0.8 }")
    print("  });")


if __name__ == "__main__":
    main()

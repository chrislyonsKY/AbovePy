"""pgSTAC Terrain Tiles — server-side DEM analysis without downloads.

Demonstrates the new TiTiler-pgSTAC terrain analysis features:
  1. Hillshade tiles for shaded relief maps
  2. Slope tiles for terrain steepness
  3. Contour tiles for topographic overlays
  4. Terrain-RGB tiles for 3D MapLibre rendering
  5. Registered searches for persistent shareable URLs

All processing happens server-side — no raster downloads needed.

Usage:
    python pgstac_terrain_tiles.py

Requires:
    pip install abovepy httpx
"""

from pathlib import Path

import httpx

from abovepy.searches import register_search, search_map_url, search_tile_url
from abovepy.titiler import (
    collection_bbox_url,
    collection_map_url,
    collection_point_url,
    contour_tile_url,
    hillshade_tile_url,
    slope_tile_url,
    terrain_rgb_tile_url,
)
from abovepy.viz import preview_url, tile_url

OUTPUT = Path(__file__).parent.parent / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)

# WCAG 2.1 AA compliant colors
_TITLE_COLOR = "#222222"
_LABEL_COLOR = "#333333"


def _apply_wcag_style(fig, axes_list):
    """Apply WCAG 2.1 AA compliant text colors."""
    fig.patch.set_facecolor("white")
    for text in fig.texts:
        text.set_color(_TITLE_COLOR)
    for ax in axes_list:
        ax.title.set_color(_TITLE_COLOR)
        ax.xaxis.label.set_color(_LABEL_COLOR)
        ax.yaxis.label.set_color(_LABEL_COLOR)
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_color(_LABEL_COLOR)


def demo_terrain_urls():
    """Show all terrain URL types for a bbox."""
    bbox = (-84.9, 38.15, -84.8, 38.25)  # Frankfort area

    print("=== Server-Side Terrain Analysis URLs ===")
    print(f"  Bbox: {bbox}\n")

    # Hillshade with custom sun angle
    hs = hillshade_tile_url(bbox=bbox, azimuth=315, altitude=45)
    print(f"  Hillshade (NW sun):  {hs[:90]}...")

    # Slope in degrees
    sl = slope_tile_url(bbox=bbox)
    print(f"  Slope (degrees):     {sl[:90]}...")

    # Contours every 20ft
    ct = contour_tile_url(bbox=bbox, increment=20, thickness=2)
    print(f"  Contours (20ft):     {ct[:90]}...")

    # Terrain-RGB for MapLibre 3D
    tr = terrain_rgb_tile_url(bbox=bbox)
    print(f"  Terrain-RGB (3D):    {tr[:90]}...")

    # Interactive map viewer
    mv = collection_map_url("dem_phase3", bbox=bbox)
    print(f"\n  Map viewer: {mv}")


def demo_point_query():
    """Query elevation at a specific point."""
    print("\n=== Point Elevation Query ===")
    # Kentucky State Capitol coordinates
    lon, lat = -84.8763, 38.1867
    url = collection_point_url("dem_phase3", lon=lon, lat=lat, assets="asset")
    print(f"  Capitol ({lon}, {lat})")
    print(f"  URL: {url}")

    try:
        resp = httpx.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        assets = data.get("assets", [])
        if assets:
            elev = assets[0].get("values", [None])[0]
            print(f"  Elevation: {elev:.1f} ft")
        else:
            print(f"  Response: {data}")
    except Exception as e:
        print(f"  Could not query (endpoint may be down): {e}")


def demo_registered_search():
    """Register a persistent search and get a shareable URL."""
    bbox = (-84.9, 38.15, -84.8, 38.25)

    print("\n=== Registered Search (Persistent Virtual Mosaic) ===")
    try:
        search_id = register_search("dem_phase3", bbox=bbox)
        print(f"  Search ID: {search_id}")
        print(f"  TileJSON:  {search_tile_url(search_id)}")
        print(f"  Map:       {search_map_url(search_id)}")
        print("  This URL is stable — share it, bookmark it, use it in dashboards.")
    except Exception as e:
        print(f"  Could not register search: {e}")


def demo_preview_images():
    """Fetch preview images from the pgSTAC endpoint."""
    import matplotlib.pyplot as plt
    from matplotlib import image as mpimg

    # Smaller bbox to stay within Lambda size limits
    bbox = (-84.88, 38.19, -84.86, 38.20)  # Downtown Frankfort

    print("\n=== Fetching Terrain Preview Images ===")
    print("  (Note: pgSTAC bbox render requires assets=asset param)\n")

    configs = [
        ("DEM Elevation", collection_bbox_url(
            "dem_phase3", bbox=bbox, width=256, height=256, fmt="png",
            assets="asset", colormap_name="viridis", rescale="400,800",
        )),
        ("Hillshade", collection_bbox_url(
            "dem_phase3", bbox=bbox, width=256, height=256, fmt="png",
            assets="asset", algorithm="hillshade",
        )),
        ("Ortho Imagery", collection_bbox_url(
            "ortho_phase3", bbox=bbox, width=256, height=256, fmt="png",
            assets="asset",
        )),
    ]

    images = []
    for label, url in configs:
        print(f"  Fetching {label}...")
        try:
            resp = httpx.get(url, timeout=30)
            resp.raise_for_status()
            # Save temp file and load as image
            tmp = OUTPUT / f"_tmp_{label.lower().replace(' ', '_')}.png"
            tmp.write_bytes(resp.content)
            img = mpimg.imread(str(tmp))
            images.append((label, img))
            tmp.unlink()
            print(f"    OK ({len(resp.content) / 1024:.0f} KB)")
        except Exception as e:
            print(f"    Failed: {e}")

    if not images:
        print("  No images fetched — skipping plot.")
        return

    # Plot side by side
    fig, axes = plt.subplots(1, len(images), figsize=(6 * len(images), 6))
    if len(images) == 1:
        axes = [axes]

    for ax, (label, img) in zip(axes, images, strict=False):
        ax.imshow(img)
        ax.set_title(label, fontsize=13, color=_TITLE_COLOR)
        ax.axis("off")

    plt.suptitle(
        "KyFromAbove pgSTAC Terrain Previews — Frankfort, KY",
        fontsize=14, color=_TITLE_COLOR,
    )
    _apply_wcag_style(fig, list(axes))
    plt.tight_layout()
    path = OUTPUT / "pgstac_terrain_previews.png"
    plt.savefig(str(path), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


def demo_viz_helpers():
    """Show the high-level viz convenience functions."""
    bbox = (-84.9, 38.15, -84.8, 38.25)

    print("\n=== Viz Convenience Helpers ===")
    print(f"  tile_url('dem_phase3', county='Franklin'):")
    print(f"    {tile_url('dem_phase3', county='Franklin')[:90]}...")
    print(f"  tile_url('dem_phase3', algorithm='hillshade'):")
    print(f"    {tile_url('dem_phase3', bbox=bbox, algorithm='hillshade')[:90]}...")
    print(f"  preview_url('ortho_phase3', county='Franklin'):")
    print(f"    {preview_url('ortho_phase3', county='Franklin')[:90]}...")


def main():
    demo_terrain_urls()
    demo_point_query()
    demo_viz_helpers()
    demo_registered_search()

    try:
        import matplotlib  # noqa: F401
        demo_preview_images()
    except ImportError:
        print("\n  Install matplotlib for preview images: pip install matplotlib")

    print("\nDone!")


if __name__ == "__main__":
    main()

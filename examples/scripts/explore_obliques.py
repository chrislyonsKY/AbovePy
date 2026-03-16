"""Explore KyFromAbove oblique imagery.

Lists available seasons and frames from the S3-hosted oblique imagery.
Once the STAC collection is published, abovepy.search() will also work.

Usage:
    python explore_obliques.py

Requires:
    pip install abovepy
"""

from abovepy.obliques import list_oblique_seasons, search_obliques
from abovepy.products import ProductType, list_products


def main():
    # Show available oblique products
    print("=== Oblique Products ===")
    oblique_products = list_products(ProductType.OBLIQUE)
    for p in oblique_products:
        print(f"  {p.key:25s}  {p.display_name}")

    # List available seasons
    print("\n=== Available Seasons ===")
    try:
        seasons = list_oblique_seasons()
        for s in seasons:
            print(f"  {s}")
    except Exception as e:
        print(f"  Could not list seasons: {e}")
        return

    if not seasons:
        print("  No seasons found.")
        return

    # Search for frames in each direction (most recent season)
    print(f"\n=== Frames in {seasons[-1]} ===")
    for direction in ["bwd", "fwd", "left", "right"]:
        try:
            frames = search_obliques(
                direction=direction,
                season=seasons[-1],
                max_items=5,
            )
            print(f"  {direction.upper():5s}: {len(frames)} frames (showing first 5)")
            for f in frames[:3]:
                print(f"         {f['frame_id']}")
                print(f"         TIF: {f['tif_url']}")
        except Exception as e:
            print(f"  {direction.upper():5s}: error — {e}")

    # Show how to read an oblique frame
    print("\n=== Reading an Oblique Frame ===")
    print("  import abovepy")
    print("  from abovepy.obliques import search_obliques")
    print("")
    print("  frames = search_obliques(direction='bwd', max_items=1)")
    print("  data, profile = abovepy.read(frames[0]['tif_url'])")
    print("  print(f'Shape: {data.shape}, CRS: {profile[\"crs\"]}')")


if __name__ == "__main__":
    main()

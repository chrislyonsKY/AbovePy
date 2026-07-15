"""Oblique spatial search — find the frames that cover a location.

Searches KyFromAbove Phase 3 oblique imagery by point + radius, then
builds a 4-direction bundle (best Backward/Forward/Left/Right frame)
for rapid site inspection.

Usage:
    python oblique_spatial_search.py

Requires:
    pip install abovepy
"""

import abovepy

# Kentucky State Capitol, Frankfort
SITE = (-84.8715, 38.1867)


def main():
    print(f"=== Oblique frames within 500 ft of {SITE} ===")
    try:
        frames = abovepy.search_obliques(point=SITE, radius_feet=500, direction=None)
    except ValueError as exc:
        # A statewide season with no bulk index can exceed the sidecar
        # fetch cap — narrow by direction/season or raise the cap.
        print(f"Search needs narrowing: {exc}")
        return

    for frame in frames:
        stamp = frame.timestamp.date() if frame.timestamp else "unknown date"
        print(f"  {frame.direction:>5s}  {frame.frame_id:20s}  {stamp}")

    print("\n=== 4-direction site-inspection bundle ===")
    bundle = abovepy.oblique_bundle(SITE)
    for direction, frame in bundle.items():
        if frame is None:
            print(f"  {direction:>5s}  (no coverage)")
            continue
        print(f"  {direction:>5s}  {frame.tif_url}")
        # Sidecar metadata is already fetched during spatial search:
        if frame.footprint is not None:
            print(f"         footprint bounds: {frame.footprint.bounds}")


if __name__ == "__main__":
    main()

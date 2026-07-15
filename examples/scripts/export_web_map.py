"""Export shareable web maps — self-contained MapLibre GL JS viewers.

Writes HTML files that display KyFromAbove products (optionally through
server-side terrain algorithms) with no build step or server required.

Usage:
    python export_web_map.py

Requires:
    pip install abovepy
"""

from pathlib import Path

import abovepy


def main():
    output_dir = Path("./output/web_maps")

    # Franklin County hillshade (server-side via TiTiler)
    path = abovepy.export_map_html(
        output_dir / "franklin_hillshade.html",
        county="Franklin",
        algorithm="hillshade",
        title="Franklin County Hillshade",
    )
    print(f"Wrote {path}")

    # 3-inch orthoimagery over downtown Frankfort
    path = abovepy.export_map_html(
        output_dir / "frankfort_ortho.html",
        product="ortho_phase3",
        bbox=(-84.88, 38.18, -84.86, 38.20),
        title="Frankfort 3-inch Orthoimagery",
    )
    print(f"Wrote {path}")

    # Statewide DEM viewer
    path = abovepy.export_map_html(
        output_dir / "kentucky_dem.html",
        product="dem_phase3",
        title="Kentucky Statewide DEM",
    )
    print(f"Wrote {path}")

    print("\nOpen any of these files in a browser — no server needed.")


if __name__ == "__main__":
    main()

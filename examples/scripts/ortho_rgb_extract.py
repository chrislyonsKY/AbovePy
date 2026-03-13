"""Extract RGB imagery from a KyFromAbove orthophoto tile.

Searches for Phase 3 ortho tiles (3-inch resolution) near the Kentucky
State Capitol, reads a small bbox window, separates RGB bands, and saves
the result as a PNG using matplotlib.

Usage:
    python ortho_rgb_extract.py

Requires:
    pip install abovepy[viz]
"""

from pathlib import Path

import numpy as np

import abovepy


def main():
    output_dir = Path("./output/ortho_extract")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Search for Phase 3 ortho near the Kentucky State Capitol
    bbox = (-84.878, 38.186, -84.874, 38.190)
    print("=== Searching Phase 3 Orthoimagery ===")
    print(f"bbox: {bbox}")
    tiles = abovepy.search(bbox=bbox, product="ortho_phase3")
    print(f"Found {len(tiles)} tiles")

    if len(tiles) == 0:
        print("No tiles found.")
        return

    # Read a small window — only fetches the bytes we need
    url = tiles.iloc[0].asset_url
    print(f"\nReading window from: {tiles.iloc[0].tile_id}")
    data, profile = abovepy.read(url, bbox=bbox, crs="EPSG:4326")

    print(f"  Shape: {data.shape}  (bands, height, width)")
    print(f"  Dtype: {data.dtype}")
    print(f"  Pixel size: {profile['transform'][0]:.4f} ft "
          f"(~{profile['transform'][0] * 12:.1f} inches)")

    # Separate RGB bands (ortho COGs are typically 3- or 4-band)
    red = data[0]
    green = data[1]
    blue = data[2]

    print("\n=== Band Statistics ===")
    for name, band in [("Red", red), ("Green", green), ("Blue", blue)]:
        print(f"  {name:5s}: min={band.min():3d}  max={band.max():3d}  "
              f"mean={band.mean():.1f}")

    # Stack to RGB array for display (height, width, 3)
    rgb = np.moveaxis(data[:3], 0, -1)

    # Save as PNG
    try:
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 2, figsize=(12, 5))

        axes[0].imshow(rgb)
        axes[0].set_title("RGB Composite (3-inch)")
        axes[0].axis("off")

        # Show single band (green) as grayscale
        axes[1].imshow(green, cmap="Greens")
        axes[1].set_title("Green Band")
        axes[1].axis("off")

        plt.tight_layout()
        png_path = output_dir / "ortho_rgb_extract.png"
        plt.savefig(str(png_path), dpi=150, bbox_inches="tight")
        print(f"\nSaved: {png_path}")
        plt.show()
    except ImportError:
        print("\nInstall matplotlib to save PNG: pip install abovepy[viz]")


if __name__ == "__main__":
    main()


# Expected output:
# =================================================================
# === Searching Phase 3 Orthoimagery ===
# bbox: (-84.878, 38.186, -84.874, 38.19)
# Found 1 tiles
#
# Reading window from: N163E227
#   Shape: (3, 480, 400)  (bands, height, width)
#   Dtype: uint8
#   Pixel size: 0.2500 ft (~3.0 inches)
#
# === Band Statistics ===
#   Red  : min= 12  max=248  mean=134.2
#   Green: min= 18  max=241  mean=128.7
#   Blue : min=  8  max=230  mean=112.5
#
# Saved: output/ortho_extract/ortho_rgb_extract.png
# =================================================================

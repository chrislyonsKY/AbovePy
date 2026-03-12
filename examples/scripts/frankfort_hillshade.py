"""Frankfort DEM Hillshade — Full workflow from search to visualization.

Searches for Phase 3 DEM tiles near Frankfort, KY, downloads them,
builds a mosaic, generates a hillshade, and saves the result.

Usage:
    python frankfort_hillshade.py

Requires:
    pip install abovepy[viz]
"""

from pathlib import Path

import numpy as np
import rasterio

import abovepy


def compute_hillshade(dem, res_x, res_y, azimuth_deg=315, altitude_deg=45):
    """Compute hillshade from a DEM array."""
    dx, dy = np.gradient(dem, res_x, res_y)
    slope = np.sqrt(dx**2 + dy**2)
    aspect = np.arctan2(-dy, dx)

    azimuth = np.radians(azimuth_deg)
    altitude = np.radians(altitude_deg)

    hillshade = (
        np.sin(altitude) * np.cos(np.arctan(slope))
        + np.cos(altitude) * np.sin(np.arctan(slope)) * np.cos(azimuth - aspect)
    )
    return np.clip(hillshade * 255, 0, 255).astype(np.uint8)


def main():
    output_dir = Path("./output/frankfort_hillshade")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Search for DEM tiles covering downtown Frankfort
    print("Searching for DEM tiles near Frankfort...")
    tiles = abovepy.search(
        bbox=(-84.9, 38.17, -84.83, 38.22),
        product="dem_phase3",
    )
    print(f"Found {len(tiles)} tiles")

    # Download
    print("Downloading...")
    paths = abovepy.download(tiles, output_dir=output_dir / "tiles")

    # Mosaic
    print("Building mosaic...")
    vrt = abovepy.mosaic(paths, output=output_dir / "frankfort_dem.vrt")

    # Read DEM and compute hillshade
    print("Computing hillshade...")
    with rasterio.open(str(vrt)) as src:
        dem = src.read(1)
        profile = src.profile
        res_x, res_y = src.res

    hillshade = compute_hillshade(dem, res_x, res_y)

    # Save hillshade as GeoTIFF
    hillshade_path = output_dir / "frankfort_hillshade.tif"
    profile.update(dtype="uint8", count=1, compress="deflate")
    with rasterio.open(str(hillshade_path), "w", **profile) as dst:
        dst.write(hillshade, 1)
    print(f"Hillshade saved: {hillshade_path}")

    # Plot if matplotlib is available
    try:
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        axes[0].imshow(dem, cmap="terrain")
        axes[0].set_title("DEM (2ft)")
        axes[0].axis("off")

        axes[1].imshow(hillshade, cmap="gray")
        axes[1].set_title("Hillshade")
        axes[1].axis("off")

        plt.tight_layout()
        png_path = output_dir / "frankfort_hillshade.png"
        plt.savefig(str(png_path), dpi=150, bbox_inches="tight")
        print(f"Plot saved: {png_path}")
        plt.show()
    except ImportError:
        print("Install matplotlib for visualization: pip install abovepy[viz]")


if __name__ == "__main__":
    main()

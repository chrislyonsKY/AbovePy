"""Generate output PNG images for all examples.

Produces sample images that are checked into the repo for documentation.
Requires: pip install abovepy[all] matplotlib

Usage:
    python generate_images.py
"""

from pathlib import Path

import numpy as np

import abovepy

OUTPUT = Path(__file__).parent.parent / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)


def generate_stream_window():
    """Stream a DEM window and save elevation plot."""
    import matplotlib.pyplot as plt

    print("=== Stream Window ===")
    tiles = abovepy.search(
        bbox=(-84.85, 38.18, -84.82, 38.21),
        product="dem_phase3",
    )
    url = tiles.iloc[0].asset_url
    data, profile = abovepy.read(
        url, bbox=(-84.85, 38.18, -84.82, 38.21)
    )
    print(f"  Shape: {data.shape}, range: {data.min():.0f}-{data.max():.0f}")

    fig, ax = plt.subplots(figsize=(10, 4))
    im = ax.imshow(data.squeeze(), cmap="terrain")
    fig.colorbar(im, ax=ax, label="Elevation (ft)")
    ax.set_title("Streamed DEM Window — Frankfort, KY")
    ax.axis("off")
    plt.tight_layout()
    path = OUTPUT / "stream_window.png"
    plt.savefig(str(path), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


def generate_ortho_rgb():
    """Extract ortho RGB and save composite."""
    import matplotlib.pyplot as plt

    print("=== Ortho RGB Extract ===")
    tiles = abovepy.search(
        bbox=(-84.876, 38.196, -84.872, 38.200),
        product="ortho_phase3",
    )
    if len(tiles) == 0:
        print("  No ortho tiles found, skipping")
        return

    url = tiles.iloc[0].asset_url
    data, profile = abovepy.read(
        url, bbox=(-84.876, 38.196, -84.872, 38.200)
    )
    print(f"  Shape: {data.shape}")

    if data.shape[0] >= 3:
        rgb = np.moveaxis(data[:3], 0, -1)
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.imshow(rgb)
        ax.set_title("Ortho Phase 3 — KY State Capitol")
        ax.axis("off")
        plt.tight_layout()
        path = OUTPUT / "ortho_rgb.png"
        plt.savefig(str(path), dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  Saved: {path}")


def generate_compare_phases():
    """Compare DEM phases side by side."""
    import matplotlib.pyplot as plt

    print("=== Compare DEM Phases ===")
    bbox = (-84.88, 38.18, -84.86, 38.20)

    tiles1 = abovepy.search(bbox=bbox, product="dem_phase1")
    tiles3 = abovepy.search(bbox=bbox, product="dem_phase3")

    if len(tiles1) == 0 or len(tiles3) == 0:
        print("  Missing tiles, skipping")
        return

    data1, _ = abovepy.read(
        tiles1.iloc[0].asset_url, bbox=bbox
    )
    data3, _ = abovepy.read(
        tiles3.iloc[0].asset_url, bbox=bbox
    )
    print(f"  Phase 1: {data1.shape}, Phase 3: {data3.shape}")

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    vmin = min(data1.min(), data3.min())
    vmax = max(data1.max(), data3.max())

    axes[0].imshow(
        data1.squeeze(), cmap="terrain", vmin=vmin, vmax=vmax
    )
    axes[0].set_title(f"DEM Phase 1 (5ft) — {data1.shape}")
    axes[0].axis("off")

    im = axes[1].imshow(
        data3.squeeze(), cmap="terrain", vmin=vmin, vmax=vmax
    )
    axes[1].set_title(f"DEM Phase 3 (2ft) — {data3.shape}")
    axes[1].axis("off")

    fig.colorbar(im, ax=axes, label="Elevation (ft)", shrink=0.8)
    plt.suptitle("DEM Phase Comparison — Frankfort, KY")
    plt.tight_layout()
    path = OUTPUT / "compare_dem_phases.png"
    plt.savefig(str(path), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


def generate_search_map():
    """Plot search results tile boundaries."""
    import matplotlib.pyplot as plt

    print("=== Search Results Map ===")
    tiles = abovepy.search(
        county="Franklin", product="dem_phase3"
    )
    print(f"  Found {len(tiles)} tiles")

    fig, ax = plt.subplots(figsize=(10, 8))
    tiles.plot(
        ax=ax,
        edgecolor="teal",
        facecolor="teal",
        alpha=0.3,
        linewidth=0.5,
    )
    ax.set_title(
        f"Franklin County — {len(tiles)} DEM Phase 3 Tiles"
    )
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    plt.tight_layout()
    path = OUTPUT / "search_results_map.png"
    plt.savefig(str(path), dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


if __name__ == "__main__":
    import matplotlib
    matplotlib.use("Agg")

    generate_stream_window()
    generate_ortho_rgb()
    generate_compare_phases()
    generate_search_map()
    print("\nDone! All images saved to examples/output/")

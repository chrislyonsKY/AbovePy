"""Stream a windowed read from a remote COG — no download required.

Demonstrates reading a small spatial window from a cloud-hosted tile
without downloading the full file.

Usage:
    python stream_window.py
"""

import abovepy


def main():
    # Search for a single DEM tile
    print("Searching for DEM tiles...")
    tiles = abovepy.search(
        bbox=(-84.85, 38.18, -84.82, 38.21),
        product="dem_phase3",
    )
    print(f"Found {len(tiles)} tiles")

    if len(tiles) == 0:
        print("No tiles found.")
        return

    # Stream a windowed read — only fetches the bytes within the bbox
    url = tiles.iloc[0].asset_url
    print(f"\nStreaming from: {url}")
    print("Reading window bbox=(-84.85, 38.18, -84.82, 38.21)...")

    data, profile = abovepy.read(
        url,
        bbox=(-84.85, 38.18, -84.82, 38.21),
    )

    print(f"\nArray shape: {data.shape}")
    print(f"Data type: {data.dtype}")
    print(f"CRS: {profile['crs']}")
    print(f"Resolution: {profile['transform'][0]:.2f} x {-profile['transform'][4]:.2f}")
    print(f"Value range: {data.min():.1f} - {data.max():.1f}")

    # Plot if matplotlib is available
    try:
        import matplotlib.pyplot as plt

        plt.figure(figsize=(8, 6))
        plt.imshow(data.squeeze(), cmap="terrain")
        plt.colorbar(label="Elevation (ft)")
        plt.title("Streamed DEM Window")
        plt.axis("off")
        plt.tight_layout()
        plt.show()
    except ImportError:
        print("\nInstall matplotlib for visualization: pip install abovepy[viz]")


if __name__ == "__main__":
    main()

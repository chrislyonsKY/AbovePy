"""Download orthoimagery for a Kentucky county.

Downloads all Phase 3 (3-inch) ortho tiles covering the specified county.

Usage:
    python county_ortho_download.py --county Pike --output ./output/pike_ortho
    python county_ortho_download.py --county Fayette
"""

import argparse
from pathlib import Path

import abovepy


def main():
    parser = argparse.ArgumentParser(description="Download KyFromAbove orthoimagery by county")
    parser.add_argument("--county", required=True, help="Kentucky county name (e.g., Pike)")
    parser.add_argument(
        "--product", default="ortho_phase3",
        help="Product key (default: ortho_phase3)",
    )
    parser.add_argument(
        "--output", default=None,
        help="Output directory (default: ./output/<county>_ortho)",
    )
    args = parser.parse_args()

    output_dir = Path(args.output) if args.output else Path(f"./output/{args.county.lower()}_ortho")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Search
    print(f"Searching {args.product} tiles for {args.county} County...")
    result = abovepy.search(county=args.county, product=args.product)
    print(f"Found {result.count} tiles")

    if result.empty:
        print("No tiles found. Check county name and product key.")
        return

    # Estimate download size
    size_info = result.estimate_size()
    print(f"Estimated download size: {size_info['total_mb']:.0f} MB")

    # Download
    print(f"\nDownloading to {output_dir}...")
    paths = result.download(output_dir=output_dir)
    print(f"\nDone. {len(paths)} files saved to {output_dir}")


if __name__ == "__main__":
    main()

# Expected output (for --county Pike):
# Searching ortho_phase3 tiles for Pike County...
# Found 500 tiles
# Estimated download size: 48500 MB
#
# Downloading to output/pike_ortho...
# Done. 500 files saved to output/pike_ortho

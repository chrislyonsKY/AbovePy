"""CLI for abovepy — ``abovepy <subcommand>`` or ``python -m abovepy <subcommand>``.

Subcommands: search, download, mosaic, info, products, tile-url, preview, estimate.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> None:
    """Main CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)

    try:
        args.func(args)
    except Exception as exc:
        # Catch abovepy errors and print friendly message
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def _build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="abovepy",
        description="KyFromAbove geospatial data access for Python",
    )
    parser.add_argument(
        "--version", action="store_true",
        help="Show version and exit",
    )

    subparsers = parser.add_subparsers(dest="command")

    # --- search ---
    p_search = subparsers.add_parser("search", help="Find tiles by area")
    _add_product_arg(p_search)
    _add_area_args(p_search)
    p_search.add_argument("--datetime", help="ISO 8601 datetime or range")
    p_search.add_argument("--max-items", type=int, default=500, help="Max tiles (default: 500)")
    p_search.add_argument("--sortby", help="Sort field (e.g., +datetime)")
    p_search.add_argument("--ids", help="Comma-separated STAC item IDs")
    _add_format_arg(p_search, choices=["table", "json", "geojson"])
    p_search.set_defaults(func=_cmd_search)

    # --- download ---
    p_download = subparsers.add_parser("download", help="Download tiles")
    _add_product_arg(p_download)
    _add_area_args(p_download)
    p_download.add_argument("--output-dir", "-o", default=".", help="Output directory (default: .)")
    p_download.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    p_download.add_argument(
        "--workers", type=int, default=4, help="Concurrent downloads (default: 4)",
    )
    p_download.add_argument("--no-resume", action="store_true", help="Disable download resume")
    p_download.set_defaults(func=_cmd_download)

    # --- mosaic ---
    p_mosaic = subparsers.add_parser("mosaic", help="Mosaic tiles into a single raster")
    p_mosaic.add_argument("input", nargs="+", help="Input tile paths or directory")
    p_mosaic.add_argument("--output", "-o", required=True, help="Output path (.vrt or .tif)")
    p_mosaic.add_argument("--bbox", help="Clip bbox: xmin,ymin,xmax,ymax")
    p_mosaic.add_argument("--crs", help="Reproject to CRS (e.g., EPSG:3089)")
    p_mosaic.set_defaults(func=_cmd_mosaic)

    # --- info ---
    p_info = subparsers.add_parser("info", help="Inspect a product or remote tile")
    p_info.add_argument("source", nargs="?", help="Product key, URL, or S3 URI")
    _add_format_arg(p_info, choices=["table", "json"])
    p_info.set_defaults(func=_cmd_info)

    # --- products ---
    p_products = subparsers.add_parser("products", help="List available products")
    p_products.add_argument(
        "--type", dest="product_type",
        choices=["dem", "ortho", "pointcloud", "oblique"],
        help="Filter by product type",
    )
    _add_format_arg(p_products, choices=["table", "json"])
    p_products.set_defaults(func=_cmd_products)

    # --- tile-url ---
    p_tile = subparsers.add_parser("tile-url", help="Generate a TiTiler tile URL")
    _add_product_arg(p_tile)
    _add_area_args(p_tile)
    p_tile.add_argument(
        "--algorithm", choices=["hillshade", "slope", "contours", "terrainrgb"],
        help="Terrain algorithm",
    )
    p_tile.set_defaults(func=_cmd_tile_url)

    # --- preview ---
    p_preview = subparsers.add_parser("preview", help="Generate a preview image URL")
    _add_product_arg(p_preview)
    _add_area_args(p_preview)
    p_preview.add_argument("--width", type=int, default=512, help="Width (default: 512)")
    p_preview.add_argument("--height", type=int, default=512, help="Height (default: 512)")
    p_preview.add_argument("--save", metavar="PATH", help="Download preview to file")
    p_preview.add_argument(
        "--open", dest="open_browser", action="store_true", help="Open in browser",
    )
    p_preview.set_defaults(func=_cmd_preview)

    # --- estimate ---
    p_estimate = subparsers.add_parser("estimate", help="Estimate download size for an area")
    _add_product_arg(p_estimate)
    _add_area_args(p_estimate)
    _add_format_arg(p_estimate, choices=["table", "json"])
    p_estimate.set_defaults(func=_cmd_estimate)

    return parser


# ---------------------------------------------------------------------------
# Subcommand handlers
# ---------------------------------------------------------------------------


def _cmd_search(args: argparse.Namespace) -> None:
    """Execute the 'search' subcommand."""
    import abovepy

    bbox = _parse_bbox(args.bbox) if args.bbox else None
    point = _parse_point(args.point) if args.point else None
    ids = args.ids.split(",") if args.ids else None
    sortby = args.sortby if args.sortby else None

    result = abovepy.search(
        product=args.product,
        bbox=bbox,
        county=args.county,
        point=point,
        buffer_miles=args.buffer,
        ids=ids,
        sortby=sortby,
        datetime=args.datetime,
        max_items=args.max_items,
    )

    fmt = args.format or "table"
    if fmt == "geojson":
        print(result.to_geojson())
    elif fmt == "json":
        # Drop geometry for JSON
        print(result.tiles.drop(columns="geometry").to_json(orient="records", indent=2))
    else:
        _print_table(result.tiles)
        est = result.estimate_size()
        print(f"\nFound {est['tile_count']} tile(s), ~{est['total_mb']} MB estimated")


def _cmd_download(args: argparse.Namespace) -> None:
    """Execute the 'download' subcommand."""
    import abovepy

    bbox = _parse_bbox(args.bbox) if args.bbox else None
    point = _parse_point(args.point) if args.point else None

    result = abovepy.search(
        product=args.product,
        bbox=bbox,
        county=args.county,
        point=point,
        buffer_miles=args.buffer,
    )

    if result.empty:
        print("No tiles found.", file=sys.stderr)
        sys.exit(1)

    est = result.estimate_size()
    print(f"Found {est['tile_count']} tile(s), ~{est['total_mb']} MB estimated. Downloading...")
    paths = result.download(
        output_dir=args.output_dir,
        overwrite=args.overwrite,
        max_workers=args.workers,
    )
    print(f"Downloaded {len(paths)} file(s) to {args.output_dir}")


def _cmd_mosaic(args: argparse.Namespace) -> None:
    """Execute the 'mosaic' subcommand."""
    import abovepy

    # Resolve input paths
    inputs = []
    for inp in args.input:
        p = Path(inp)
        if p.is_dir():
            inputs.extend(sorted(p.glob("*.tif")))
        else:
            inputs.append(p)

    if not inputs:
        print("No input files found.", file=sys.stderr)
        sys.exit(1)

    bbox = _parse_bbox(args.bbox) if args.bbox else None
    result = abovepy.mosaic(inputs, bbox=bbox, output=args.output, crs=args.crs)
    print(f"Mosaic written to {result}")


def _cmd_info(args: argparse.Namespace) -> None:
    """Execute the 'info' subcommand."""
    import abovepy

    result = abovepy.info(source=args.source)
    fmt = args.format or "table"

    if isinstance(result, dict):
        if fmt == "json":
            print(json.dumps(result, indent=2, default=str))
        else:
            for key, val in result.items():
                print(f"  {key}: {val}")
    else:
        if fmt == "json":
            print(result.to_json(orient="records", indent=2))
        else:
            print(result.to_string(index=False))


def _cmd_products(args: argparse.Namespace) -> None:
    """Execute the 'products' subcommand."""
    import abovepy

    products = abovepy.list_products()
    if args.product_type:
        products = [p for p in products if p.product_type.value == args.product_type]

    fmt = args.format or "table"
    if fmt == "json":
        rows = [
            {
                "key": p.key,
                "display_name": p.display_name,
                "collection_id": p.collection_id,
                "type": p.product_type.value,
                "resolution": p.resolution,
                "format": p.format,
                "phase": p.phase,
            }
            for p in products
        ]
        print(json.dumps(rows, indent=2))
    else:
        print(f"{'Product':<24} {'Type':<12} {'Resolution':<12} {'Phase'}")
        print("-" * 60)
        for p in products:
            print(f"{p.key:<24} {p.product_type.value:<12} {p.resolution:<12} {p.phase}")


def _cmd_tile_url(args: argparse.Namespace) -> None:
    """Execute the 'tile-url' subcommand."""
    from abovepy.viz import tile_url

    bbox = _parse_bbox(args.bbox) if args.bbox else None

    url = tile_url(
        product=args.product,
        bbox=bbox,
        county=args.county,
        algorithm=args.algorithm,
    )
    print(url)


def _cmd_preview(args: argparse.Namespace) -> None:
    """Execute the 'preview' subcommand."""
    from abovepy.viz import preview_url

    bbox = _parse_bbox(args.bbox) if args.bbox else None

    url = preview_url(
        product=args.product,
        bbox=bbox,
        county=args.county,
        width=args.width,
        height=args.height,
    )

    if args.save:
        import httpx
        resp = httpx.get(url, timeout=60)
        resp.raise_for_status()
        Path(args.save).write_bytes(resp.content)
        print(f"Preview saved to {args.save}")
    elif args.open_browser:
        import webbrowser
        webbrowser.open(url)
        print(url)
    else:
        print(url)


def _cmd_estimate(args: argparse.Namespace) -> None:
    """Execute the 'estimate' subcommand."""
    import abovepy

    bbox = _parse_bbox(args.bbox) if args.bbox else None
    point = _parse_point(args.point) if args.point else None

    result = abovepy.search(
        product=args.product,
        bbox=bbox,
        county=args.county,
        point=point,
        buffer_miles=args.buffer,
    )

    est = result.estimate_size()
    fmt = args.format or "table"

    if fmt == "json":
        print(json.dumps(est, indent=2))
    else:
        print(f"Product:    {args.product}")
        print(f"Tiles:      {est['tile_count']}")
        print(f"Avg size:   {est['avg_tile_mb']} MB/tile")
        print(f"Total est:  {est['total_mb']} MB")


# ---------------------------------------------------------------------------
# Argument helpers
# ---------------------------------------------------------------------------


def _add_product_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--product", "-p", default="dem_phase3",
        help="Product key (default: dem_phase3)",
    )


def _add_area_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--bbox", help="Bounding box: xmin,ymin,xmax,ymax")
    parser.add_argument("--county", help="Kentucky county name")
    parser.add_argument("--point", help="Longitude,latitude (e.g., -84.85,38.19)")
    parser.add_argument("--buffer", type=float, help="Buffer in miles (used with --point)")


def _add_format_arg(
    parser: argparse.ArgumentParser,
    choices: list[str] | None = None,
) -> None:
    parser.add_argument(
        "--format", "-f", choices=choices or ["table", "json"],
        help="Output format",
    )


def _parse_bbox(value: str) -> tuple[float, float, float, float]:
    """Parse 'xmin,ymin,xmax,ymax' string to tuple."""
    parts = value.split(",")
    if len(parts) != 4:
        raise argparse.ArgumentTypeError(
            f"Expected 4 comma-separated values, got {len(parts)}"
        )
    return tuple(float(p) for p in parts)  # type: ignore[return-value]


def _parse_point(value: str) -> tuple[float, float]:
    """Parse 'lon,lat' string to tuple."""
    parts = value.split(",")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError(
            f"Expected 2 comma-separated values (lon,lat), got {len(parts)}"
        )
    return (float(parts[0]), float(parts[1]))


def _print_table(gdf: object) -> None:
    """Print a GeoDataFrame as a terminal-friendly table."""
    import pandas as pd

    df = gdf.drop(columns="geometry", errors="ignore") if hasattr(gdf, "drop") else gdf  # type: ignore[union-attr]
    print(pd.DataFrame(df).to_string(index=False))  # type: ignore[arg-type]


if __name__ == "__main__":
    main()

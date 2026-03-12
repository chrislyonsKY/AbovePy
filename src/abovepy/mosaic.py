"""Tile mosaicking and VRT construction.

Defaults to VRT (zero-copy) for performance. Only writes a full GeoTIFF
when the user explicitly requests .tif output.
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


def mosaic_tiles(
    tiles_or_paths,
    bbox: tuple[float, float, float, float] | None = None,
    output: str | Path | None = None,
    crs: str | None = None,
):
    """Mosaic tiles into a VRT or GeoTIFF.

    Parameters
    ----------
    tiles_or_paths : list[Path] or GeoDataFrame
        Tile file paths or tile index with 'asset_url'.
    bbox : tuple, optional
        Clip to bounding box (xmin, ymin, xmax, ymax).
    output : str or Path, optional
        Output path. .vrt -> VRT, .tif -> merged GeoTIFF.
        None -> VRT in a temp directory.
    crs : str, optional
        Reproject output to this CRS.

    Returns
    -------
    Path or tuple[numpy.ndarray, dict]
        Path to output file, or (data, profile) if no output specified
        and fewer than 20 tiles (in-memory merge).
    """
    paths = _resolve_paths(tiles_or_paths)

    if not paths:
        raise ValueError("No tile paths provided for mosaicking.")

    if output is not None:
        output = Path(output)
        if output.suffix.lower() == ".vrt":
            return _build_vrt(paths, output, bbox=bbox)
        else:
            return _merge_tiles(paths, output, bbox=bbox, crs=crs)
    else:
        vrt_path = Path(tempfile.mkdtemp()) / "mosaic.vrt"
        return _build_vrt(paths, vrt_path, bbox=bbox)


def _resolve_paths(tiles_or_paths) -> list[Path]:
    """Extract file paths from a list or GeoDataFrame.

    Parameters
    ----------
    tiles_or_paths : list or GeoDataFrame
        Path list or tile index GeoDataFrame.

    Returns
    -------
    list[Path]
    """
    import geopandas as gpd

    if isinstance(tiles_or_paths, gpd.GeoDataFrame):
        if "local_path" in tiles_or_paths.columns:
            return [Path(p) for p in tiles_or_paths["local_path"].dropna()]
        if "asset_url" in tiles_or_paths.columns:
            return [Path(u) for u in tiles_or_paths["asset_url"].dropna()]
        raise ValueError(
            "GeoDataFrame must have 'local_path' or 'asset_url' column."
        )

    return [Path(p) for p in tiles_or_paths]


def _build_vrt(
    paths: list[Path],
    output: Path,
    bbox: tuple[float, float, float, float] | None = None,
) -> Path:
    """Build a GDAL VRT from tile paths (zero-copy).

    Parameters
    ----------
    paths : list[Path]
        Input raster file paths.
    output : Path
        Output .vrt path.
    bbox : tuple, optional
        Clip extent (xmin, ymin, xmax, ymax) in the source CRS.

    Returns
    -------
    Path
        Path to the created VRT file.
    """
    from osgeo import gdal

    gdal.UseExceptions()

    str_paths = [str(p) for p in paths]
    output.parent.mkdir(parents=True, exist_ok=True)

    vrt_options = gdal.BuildVRTOptions()
    if bbox is not None:
        vrt_options = gdal.BuildVRTOptions(
            outputBounds=(bbox[0], bbox[1], bbox[2], bbox[3]),
        )

    vrt_ds = gdal.BuildVRT(str(output), str_paths, options=vrt_options)
    if vrt_ds is None:
        raise RuntimeError("GDAL BuildVRT failed for {}".format(output))
    vrt_ds.FlushCache()
    vrt_ds = None  # Close dataset

    logger.info("Built VRT from %d tiles: %s", len(paths), output)
    return output


def _merge_tiles(
    paths: list[Path],
    output: Path,
    bbox: tuple[float, float, float, float] | None = None,
    crs: str | None = None,
) -> Path:
    """Merge tiles into a single GeoTIFF via rasterio.merge.

    Parameters
    ----------
    paths : list[Path]
        Input raster file paths.
    output : Path
        Output .tif path.
    bbox : tuple, optional
        Clip extent (xmin, ymin, xmax, ymax) in the source CRS.
    crs : str, optional
        Reproject merged output to this CRS.

    Returns
    -------
    Path
        Path to the created GeoTIFF.
    """
    import numpy as np
    import rasterio
    from rasterio.merge import merge

    output.parent.mkdir(parents=True, exist_ok=True)

    datasets = [rasterio.open(p) for p in paths]

    try:
        merge_kwargs = {}
        if bbox is not None:
            merge_kwargs["bounds"] = bbox

        merged, transform = merge(datasets, **merge_kwargs)

        profile = datasets[0].profile.copy()
        profile.update(
            driver="GTiff",
            height=merged.shape[1],
            width=merged.shape[2],
            transform=transform,
            count=merged.shape[0],
            compress="deflate",
            tiled=True,
            blockxsize=512,
            blockysize=512,
        )

        if crs is not None:
            from rasterio.warp import calculate_default_transform, reproject, Resampling

            dst_crs = rasterio.crs.CRS.from_user_input(crs)
            dst_transform, dst_width, dst_height = calculate_default_transform(
                profile["crs"], dst_crs,
                profile["width"], profile["height"],
                *rasterio.transform.array_bounds(
                    profile["height"], profile["width"], transform
                ),
            )
            dst_data = np.zeros(
                (merged.shape[0], dst_height, dst_width), dtype=merged.dtype
            )
            for i in range(merged.shape[0]):
                reproject(
                    source=merged[i],
                    destination=dst_data[i],
                    src_transform=transform,
                    src_crs=profile["crs"],
                    dst_transform=dst_transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.bilinear,
                )
            merged = dst_data
            profile.update(
                crs=dst_crs,
                transform=dst_transform,
                width=dst_width,
                height=dst_height,
            )

        with rasterio.open(output, "w", **profile) as dst:
            dst.write(merged)

    finally:
        for ds in datasets:
            ds.close()

    logger.info("Merged %d tiles to GeoTIFF: %s", len(paths), output)
    return output

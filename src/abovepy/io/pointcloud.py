"""Point cloud reads for COPC/LAZ files.

Requires optional dependencies: ``pip install abovepy[lidar]``

Supports reading point cloud data from local files, S3 URIs, and HTTPS
URLs. For COPC files, spatial filtering via bbox is supported without
downloading the entire file.
"""

from __future__ import annotations

import contextlib
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_INSTALL_MSG = "Point cloud support requires laspy. Install with: pip install abovepy[lidar]"


def read_pointcloud(
    source: str | Path,
    bbox: tuple[float, float, float, float] | None = None,
    classifications: list[int] | None = None,
) -> tuple[Any, dict[str, Any]]:
    """Read a COPC or LAZ point cloud file.

    Parameters
    ----------
    source : str or Path
        Local path, S3 URI, or HTTPS URL to a LAZ/COPC file.
    bbox : tuple, optional
        Spatial filter (xmin, ymin, xmax, ymax) in the file's native CRS.
    classifications : list[int], optional
        Filter to specific LAS classification codes (e.g., [2] for ground).

    Returns
    -------
    tuple[laspy.LasData, dict]
        (point_cloud, metadata) — LasData object and metadata dict.

    Raises
    ------
    ImportError
        If laspy is not installed.
    """
    try:
        import laspy
    except ImportError as err:
        raise ImportError(_INSTALL_MSG) from err

    source_str = str(source)

    # Read the file
    if source_str.startswith(("https://", "http://", "s3://")):
        las = _read_remote(source_str)
    else:
        las = laspy.read(source_str)

    # Apply spatial filter
    if bbox is not None:
        xmin, ymin, xmax, ymax = bbox
        mask = (las.x >= xmin) & (las.x <= xmax) & (las.y >= ymin) & (las.y <= ymax)
        las.points = las.points[mask]
        logger.info(
            "Spatial filter kept %d of %d points",
            mask.sum(),
            len(mask),
        )

    # Apply classification filter
    if classifications is not None:
        cls_mask = sum(las.classification == c for c in classifications) > 0
        las.points = las.points[cls_mask]

    metadata = {
        "path": str(source),
        "point_count": len(las.points),
        "point_format": las.header.point_format.id,
        "version": f"{las.header.version.major}.{las.header.version.minor}",
        "scales": tuple(las.header.scales),
        "offsets": tuple(las.header.offsets),
        "mins": (las.header.x_min, las.header.y_min, las.header.z_min),
        "maxs": (las.header.x_max, las.header.y_max, las.header.z_max),
    }

    return las, metadata


def inspect_pointcloud(source: str | Path) -> dict[str, Any]:
    """Inspect a point cloud file header without reading all points.

    Parameters
    ----------
    source : str or Path
        Local path to a LAZ/COPC file.

    Returns
    -------
    dict
        Metadata dict.

    Raises
    ------
    ImportError
        If laspy is not installed.
    """
    try:
        import laspy
    except ImportError as err:
        raise ImportError(_INSTALL_MSG) from err

    with laspy.open(str(source)) as reader:
        header = reader.header
        return {
            "path": str(source),
            "point_count": header.point_count,
            "point_format": header.point_format.id,
            "version": f"{header.version.major}.{header.version.minor}",
            "scales": tuple(header.scales),
            "offsets": tuple(header.offsets),
            "mins": (header.x_min, header.y_min, header.z_min),
            "maxs": (header.x_max, header.y_max, header.z_max),
            "creation_date": str(header.creation_date),
        }


def read_copc(
    source: str | Path,
    bbox: tuple[float, float, float, float] | None = None,
    resolution: float | None = None,
    classifications: list[int] | None = None,
    z_range: tuple[float, float] | None = None,
    crs: str | None = None,
) -> tuple[Any, dict[str, Any]]:
    """Read a COPC file with cloud-native spatial queries.

    Unlike :func:`read_pointcloud`, this uses ``laspy.CopcReader`` for
    efficient, range-request-based reads of Cloud Optimised Point Cloud
    files — no full download required.

    Parameters
    ----------
    source : str or Path
        Local path, S3 URI, or HTTPS URL to a COPC file.
    bbox : tuple, optional
        Spatial filter ``(xmin, ymin, xmax, ymax)`` in the CRS specified
        by *crs* (defaults to the file's native CRS).
    resolution : float, optional
        COPC resolution level for the query.  ``None`` returns all
        resolutions.
    classifications : list[int], optional
        Filter to specific LAS classification codes (e.g., ``[2]`` for
        ground).
    z_range : tuple[float, float], optional
        ``(zmin, zmax)`` range to include in the query bounds.  If
        *bbox* is given without *z_range*, z bounds default to ±inf.
    crs : str, optional
        CRS of the *bbox* coordinates (e.g. ``"EPSG:4326"``).  If the
        file's CRS differs, the bbox is reprojected before querying.

    Returns
    -------
    tuple[laspy.ScaleAwarePointRecord, dict]
        ``(points, metadata)`` — point record and a metadata dict with
        keys: *path*, *point_count*, *point_format*, *scales*, *offsets*,
        *bounds*.

    Raises
    ------
    ImportError
        If laspy or numpy is not installed.
    """
    try:
        import laspy
        import laspy.copc
        import numpy as np
    except ImportError as err:
        raise ImportError(_INSTALL_MSG) from err

    source_str = str(source)

    # Resolve S3 URIs to HTTPS
    source_url = source_str
    if source_str.startswith("s3://"):
        parts = source_str.replace("s3://", "").split("/", 1)
        bucket, key = parts[0], parts[1]
        source_url = f"https://{bucket}.s3.amazonaws.com/{key}"

    try:
        reader = laspy.CopcReader.open(source_url)
    except Exception:
        # If the file is LAZ (not COPC), fall back to read_pointcloud
        logger.warning(
            "Failed to open as COPC; falling back to read_pointcloud: %s",
            source_str,
        )
        return read_pointcloud(source, bbox=bbox, classifications=classifications)

    try:
        # Build query kwargs
        query_kwargs: dict[str, Any] = {}

        if bbox is not None:
            xmin, ymin, xmax, ymax = bbox

            # Reproject bbox if a CRS was given and differs from file CRS
            file_crs_wkt = None
            with contextlib.suppress(Exception):
                file_crs_wkt = reader.header.parse_crs().to_wkt()
            if crs is not None and file_crs_wkt:
                try:
                    from pyproj import CRS as ProjCRS
                    from pyproj import Transformer

                    src_crs = ProjCRS.from_user_input(crs)
                    dst_crs = ProjCRS.from_wkt(file_crs_wkt)
                    if src_crs != dst_crs:
                        transformer = Transformer.from_crs(src_crs, dst_crs, always_xy=True)
                        xmin, ymin = transformer.transform(xmin, ymin)
                        xmax, ymax = transformer.transform(xmax, ymax)
                except Exception:
                    logger.warning("CRS reprojection failed; using bbox as-is")

            zmin = z_range[0] if z_range is not None else -np.inf
            zmax = z_range[1] if z_range is not None else np.inf

            bounds = laspy.copc.Bounds(
                mins=np.array([xmin, ymin, zmin]),
                maxs=np.array([xmax, ymax, zmax]),
            )
            query_kwargs["bounds"] = bounds

        if resolution is not None:
            query_kwargs["resolution"] = resolution

        points = reader.query(**query_kwargs)

        # Apply classification filter
        if classifications is not None:
            cls_mask = sum(points.classification == c for c in classifications) > 0
            points = points[cls_mask]

        header = reader.header
        metadata = {
            "path": source_str,
            "point_count": len(points),
            "point_format": header.point_format.id,
            "scales": tuple(header.scales),
            "offsets": tuple(header.offsets),
            "bounds": {
                "mins": (header.x_min, header.y_min, header.z_min),
                "maxs": (header.x_max, header.y_max, header.z_max),
            },
        }
    finally:
        reader.close()

    return points, metadata


def _read_remote(url: str) -> Any:
    """Download a remote LAZ/COPC file and read it with laspy.

    Parameters
    ----------
    url : str
        HTTPS URL or S3 URI.

    Returns
    -------
    laspy.LasData
    """
    import io

    import httpx
    import laspy

    from abovepy._constants import DOWNLOAD_TIMEOUT

    if url.startswith("s3://"):
        # Convert to HTTPS for public bucket
        parts = url.replace("s3://", "").split("/", 1)
        bucket, key = parts[0], parts[1]
        url = f"https://{bucket}.s3.amazonaws.com/{key}"

    logger.info("Downloading point cloud: %s", url)
    with httpx.Client(timeout=DOWNLOAD_TIMEOUT) as client:
        response = client.get(url)
        response.raise_for_status()

    return laspy.read(io.BytesIO(response.content))

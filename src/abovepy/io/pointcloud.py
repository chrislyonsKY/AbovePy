"""Point cloud reads for COPC/LAZ files.

Requires optional dependencies: ``pip install abovepy[lidar]``

Supports reading point cloud data from local files, S3 URIs, and HTTPS
URLs. For COPC files, spatial filtering via bbox is supported without
downloading the entire file.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_INSTALL_MSG = (
    "Point cloud support requires laspy. "
    "Install with: pip install abovepy[lidar]"
)


def read_pointcloud(
    source: str | Path,
    bbox: tuple[float, float, float, float] | None = None,
    classifications: list[int] | None = None,
) -> tuple:
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
        mask = (
            (las.x >= xmin) & (las.x <= xmax)
            & (las.y >= ymin) & (las.y <= ymax)
        )
        las.points = las.points[mask]
        logger.info(
            "Spatial filter kept %d of %d points",
            mask.sum(), len(mask),
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


def inspect_pointcloud(source: str | Path) -> dict:
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


def _read_remote(url: str):
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

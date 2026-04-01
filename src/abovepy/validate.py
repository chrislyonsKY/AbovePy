"""Cloud-native format validation for COG and COPC files.

Provides lightweight built-in checks using rasterio and laspy, with
optional deep validation via rio-cogeo when installed.

Quick start::

    import abovepy

    result = abovepy.validate("path/to/dem.tif")
    print(result.is_valid)  # True if COG requirements are met
    print(result.checks)    # Individual check details

    # Deep validation (requires: pip install rio-cogeo)
    result = abovepy.validate("path/to/dem.tif", deep=True)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Check:
    """Result of a single validation check."""

    name: str
    passed: bool
    message: str
    detail: Any = None


@dataclass
class ValidationResult:
    """Aggregated result of format validation.

    Attributes
    ----------
    source : str
        Path or URL that was validated.
    format : str
        Detected format: ``"COG"``, ``"GeoTIFF"``, ``"COPC"``, ``"LAZ"``,
        or ``"unknown"``.
    is_valid : bool
        True if all required checks passed.
    checks : list[Check]
        Individual check results.
    """

    source: str
    format: str
    is_valid: bool
    checks: list[Check] = field(default_factory=list)

    def summary(self) -> str:
        """One-line human-readable summary."""
        passed = sum(1 for c in self.checks if c.passed)
        total = len(self.checks)
        status = "VALID" if self.is_valid else "INVALID"
        return f"{self.format} {status} — {passed}/{total} checks passed: {self.source}"

    def __repr__(self) -> str:
        return self.summary()


def validate(
    source: str | Path,
    deep: bool = False,
) -> ValidationResult:
    """Validate a raster or point cloud file for cloud-native compliance.

    Runs built-in checks using rasterio (COG) or laspy (COPC). When
    ``deep=True``, uses rio-cogeo for thorough COG validation including
    IFD order and overview structure checks.

    Parameters
    ----------
    source : str or Path
        Local path, S3 URI, or HTTPS URL to a raster or point cloud file.
    deep : bool
        If True, run deep validation via rio-cogeo (must be installed).
        Falls back to built-in checks with a warning if not available.

    Returns
    -------
    ValidationResult
        Aggregated validation result with individual checks.
    """
    source_str = str(source)
    lower = source_str.lower()

    if lower.endswith((".copc.laz",)):
        return _validate_copc(source_str)
    elif lower.endswith((".laz", ".las")):
        return _validate_pointcloud(source_str)
    elif lower.endswith((".tif", ".tiff")):
        if deep:
            return _validate_cog_deep(source_str)
        return _validate_cog(source_str)
    else:
        return ValidationResult(
            source=source_str,
            format="unknown",
            is_valid=False,
            checks=[Check("format_detection", False, f"Unrecognized file extension: {lower}")],
        )


def _open_rasterio_source(source: str) -> str:
    """Convert source to a path rasterio can open."""
    if source.startswith("s3://"):
        return source.replace("s3://", "/vsis3/", 1)
    if source.startswith("https://"):
        return f"/vsicurl/{source}"
    return source


def _validate_cog(source: str) -> ValidationResult:
    """Built-in COG validation using rasterio."""
    import rasterio

    checks: list[Check] = []
    vsi_path = _open_rasterio_source(source)

    try:
        with rasterio.open(vsi_path) as src:
            profile = src.profile

            # Check: valid GeoTIFF
            driver = profile.get("driver", "")
            checks.append(
                Check(
                    "geotiff_format",
                    driver == "GTiff",
                    f"Driver is {driver}" if driver != "GTiff" else "Valid GeoTIFF format",
                )
            )

            # Check: has CRS
            has_crs = src.crs is not None
            checks.append(
                Check(
                    "has_crs",
                    has_crs,
                    f"CRS: {src.crs}" if has_crs else "No CRS defined",
                )
            )

            # Check: internal tiling
            is_tiled = profile.get("tiled", False)
            blockxsize = profile.get("blockxsize", 0)
            blockysize = profile.get("blockysize", 0)
            checks.append(
                Check(
                    "internal_tiling",
                    is_tiled,
                    f"Tiled {blockxsize}x{blockysize}"
                    if is_tiled
                    else "Not internally tiled (strips)",
                    detail={"blockxsize": blockxsize, "blockysize": blockysize},
                )
            )

            # Check: overviews
            overviews = src.overviews(1)
            has_overviews = len(overviews) > 0
            checks.append(
                Check(
                    "has_overviews",
                    has_overviews,
                    f"{len(overviews)} overview levels: {overviews}"
                    if has_overviews
                    else "No internal overviews",
                    detail=overviews,
                )
            )

            # Check: compression
            compression = profile.get("compress")
            checks.append(
                Check(
                    "compression",
                    compression is not None,
                    f"Compression: {compression}"
                    if compression
                    else "No compression (larger file size)",
                    detail=compression,
                )
            )

            # Info: dimensions and bands
            checks.append(
                Check(
                    "dimensions",
                    True,
                    f"{src.width}x{src.height}, {src.count} band(s), {src.dtypes[0]}",
                    detail={
                        "width": src.width,
                        "height": src.height,
                        "bands": src.count,
                        "dtype": str(src.dtypes[0]),
                    },
                )
            )

    except Exception as exc:
        return ValidationResult(
            source=source,
            format="unknown",
            is_valid=False,
            checks=[Check("readable", False, f"Cannot open file: {exc}")],
        )

    is_cog = all(
        c.passed
        for c in checks
        if c.name
        in {
            "geotiff_format",
            "has_crs",
            "internal_tiling",
            "has_overviews",
        }
    )
    fmt = "COG" if is_cog else "GeoTIFF"

    return ValidationResult(source=source, format=fmt, is_valid=is_cog, checks=checks)


def _validate_cog_deep(source: str) -> ValidationResult:
    """Deep COG validation using rio-cogeo."""
    try:
        from rio_cogeo import cog_validate
    except ImportError:
        logger.warning(
            "rio-cogeo not installed, falling back to built-in checks. "
            "Install with: pip install rio-cogeo"
        )
        return _validate_cog(source)

    # Run built-in checks first for the details
    result = _validate_cog(source)

    # Add rio-cogeo deep validation
    vsi_path = _open_rasterio_source(source)
    try:
        is_valid, errors, warnings = cog_validate(vsi_path, quiet=True)
    except Exception as exc:
        result.checks.append(
            Check(
                "rio_cogeo_validate",
                False,
                f"rio-cogeo validation failed: {exc}",
            )
        )
        result.is_valid = False
        return result

    result.checks.append(
        Check(
            "rio_cogeo_validate",
            is_valid,
            "Passed rio-cogeo deep validation" if is_valid else f"Failed: {'; '.join(errors)}",
            detail={"errors": errors, "warnings": warnings},
        )
    )

    if warnings:
        for w in warnings:
            result.checks.append(Check("rio_cogeo_warning", True, f"Warning: {w}"))

    result.is_valid = is_valid
    result.format = "COG" if is_valid else "GeoTIFF"

    return result


def _validate_copc(source: str) -> ValidationResult:
    """Validate a COPC (Cloud-Optimized Point Cloud) file using laspy."""
    try:
        import laspy
    except ImportError:
        return ValidationResult(
            source=source,
            format="COPC",
            is_valid=False,
            checks=[
                Check(
                    "laspy_available",
                    False,
                    "laspy not installed. Install with: pip install abovepy[lidar]",
                )
            ],
        )

    checks: list[Check] = []

    try:
        reader = laspy.CopcReader.open(source)
        header = reader.header

        # Check: COPC format (if we get here, laspy confirmed it)
        checks.append(Check("copc_format", True, "Valid COPC format (spatial index present)"))

        # Check: has CRS
        try:
            crs_wkt = header.parse_crs().to_wkt()
            has_crs = bool(crs_wkt)
        except Exception:
            has_crs = False
            crs_wkt = None
        checks.append(
            Check(
                "has_crs",
                has_crs,
                "CRS defined" if has_crs else "No CRS in VLR records",
                detail=crs_wkt[:80] + "..." if crs_wkt and len(crs_wkt) > 80 else crs_wkt,
            )
        )

        # Check: point format
        point_format = header.point_format.id
        checks.append(
            Check(
                "point_format",
                point_format in (6, 7, 8),
                f"Point format {point_format}"
                + (" (standard for COPC)" if point_format in (6, 7, 8) else " (unusual for COPC)"),
                detail=point_format,
            )
        )

        # Check: point count
        point_count = header.point_count
        checks.append(
            Check(
                "point_count",
                point_count > 0,
                f"{point_count:,} points",
                detail=point_count,
            )
        )

        # Info: spatial bounds
        mins = header.mins
        maxs = header.maxs
        checks.append(
            Check(
                "spatial_bounds",
                True,
                f"Bounds: X[{mins[0]:.1f}, {maxs[0]:.1f}] "
                f"Y[{mins[1]:.1f}, {maxs[1]:.1f}] "
                f"Z[{mins[2]:.1f}, {maxs[2]:.1f}]",
                detail={"mins": mins.tolist(), "maxs": maxs.tolist()},
            )
        )

        if hasattr(reader, "close"):
            reader.close()

    except Exception as exc:
        exc_str = str(exc)
        if "copc" in exc_str.lower() or "not a copc" in exc_str.lower():
            return ValidationResult(
                source=source,
                format="LAZ",
                is_valid=False,
                checks=[Check("copc_format", False, f"File is LAZ but not COPC: {exc_str}")],
            )
        return ValidationResult(
            source=source,
            format="unknown",
            is_valid=False,
            checks=[Check("readable", False, f"Cannot open file: {exc_str}")],
        )

    is_valid = all(
        c.passed
        for c in checks
        if c.name
        in {
            "copc_format",
            "has_crs",
            "point_format",
        }
    )

    return ValidationResult(source=source, format="COPC", is_valid=is_valid, checks=checks)


def _validate_pointcloud(source: str) -> ValidationResult:
    """Basic validation for LAZ/LAS files (not COPC)."""
    try:
        import laspy
    except ImportError:
        return ValidationResult(
            source=source,
            format="LAZ",
            is_valid=False,
            checks=[
                Check(
                    "laspy_available",
                    False,
                    "laspy not installed. Install with: pip install abovepy[lidar]",
                )
            ],
        )

    checks: list[Check] = []

    try:
        with laspy.open(source) as reader:
            header = reader.header

            checks.append(Check("laz_format", True, "Valid LAZ/LAS format"))

            point_count = header.point_count
            checks.append(
                Check(
                    "point_count",
                    point_count > 0,
                    f"{point_count:,} points",
                    detail=point_count,
                )
            )

            checks.append(
                Check(
                    "not_copc",
                    False,
                    "File is LAZ, not COPC — does not support cloud-native range reads. "
                    "Consider converting with: pdal translate input.laz output.copc.laz",
                )
            )

    except Exception as exc:
        return ValidationResult(
            source=source,
            format="unknown",
            is_valid=False,
            checks=[Check("readable", False, f"Cannot open file: {exc}")],
        )

    return ValidationResult(source=source, format="LAZ", is_valid=False, checks=checks)

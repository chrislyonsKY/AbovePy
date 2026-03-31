"""County mosaic URL builders — pre-built county-level mosaics on S3.

KyFromAbove provides pre-built county mosaics for Phase 3 orthoimagery
as MrSID (.sid) and ArcGIS Tile Package (.tpkx) files. These are
full-county mosaics at 3-inch resolution — no tile stitching needed.

MrSID files can be streamed directly by QGIS and any GDAL-based tool
via /vsicurl/ without downloading the entire file.
"""

from __future__ import annotations

import logging

from abovepy._constants import (
    S3_BASE_URL,
    S3_COUNTY_MOSAIC_MRSID,
    S3_COUNTY_MOSAIC_TPKX,
)
from abovepy.utils.bbox import list_counties

logger = logging.getLogger(__name__)

# Year mappings for MrSID filenames (county → acquisition year)
# Most counties are 2023 or 2024. This is a best-effort mapping;
# if a file isn't found at the expected year, the caller should
# try the alternate year.
_DEFAULT_MRSID_YEAR = "2023"

# Formats available for county mosaics
MOSAIC_FORMATS = ("mrsid", "tpkx")


def county_mosaic_url(
    county: str,
    fmt: str = "mrsid",
    year: str | None = None,
) -> str:
    """Get the S3 URL for a pre-built county orthoimagery mosaic.

    KyFromAbove provides pre-built Phase 3 county mosaics as MrSID
    (GDAL-compatible, streamable) and TPKX (ArcGIS) files.

    Parameters
    ----------
    county : str
        Kentucky county name (e.g., "Franklin", "Pike"). Case-insensitive.
    fmt : str
        File format: ``"mrsid"`` (default, works in QGIS/GDAL) or
        ``"tpkx"`` (ArcGIS tile package).
    year : str or None
        Acquisition year for MrSID naming (e.g., "2023", "2024").
        Default ``None`` auto-selects "2023". Ignored for TPKX.

    Returns
    -------
    str
        HTTPS URL to the county mosaic on S3.

    Raises
    ------
    ValueError
        If county name is invalid or format is not recognized.

    Examples
    --------
    >>> county_mosaic_url("Franklin")
    'https://kyfromabove.s3.us-west-2.amazonaws.com/imagery/orthos/Phase3/County-Mosaics/MrSIDs/KY_KYAPED_Franklin_2023_3IN.sid'

    >>> county_mosaic_url("Franklin", fmt="tpkx")
    'https://kyfromabove.s3.us-west-2.amazonaws.com/imagery/orthos/Phase3/County-Mosaics/Tile-Packages-tpkx/Franklin_KyFromAbove_Phase3_3IN.tpkx'
    """
    from abovepy.utils.bbox import get_county_bbox

    # Validate county name (raises CountyError if invalid)
    get_county_bbox(county)

    # Normalize county name to title case
    normalized = county.strip().title()

    fmt = fmt.lower()
    if fmt not in MOSAIC_FORMATS:
        raise ValueError(f"Invalid format {fmt!r}. Supported: {', '.join(MOSAIC_FORMATS)}")

    if fmt == "mrsid":
        yr = year or _DEFAULT_MRSID_YEAR
        filename = f"KY_KYAPED_{normalized}_{yr}_3IN.sid"
        return f"{S3_BASE_URL}/{S3_COUNTY_MOSAIC_MRSID}{filename}"
    else:
        filename = f"{normalized}_KyFromAbove_Phase3_3IN.tpkx"
        return f"{S3_BASE_URL}/{S3_COUNTY_MOSAIC_TPKX}{filename}"


def list_county_mosaics(fmt: str = "mrsid") -> list[dict[str, str]]:
    """List all available county mosaic URLs.

    Parameters
    ----------
    fmt : str
        File format: ``"mrsid"`` or ``"tpkx"``.

    Returns
    -------
    list[dict]
        List of dicts with keys: county, url, format.
    """
    counties = list_counties()
    results = []
    for county in counties:
        url = county_mosaic_url(county, fmt=fmt)
        results.append(
            {
                "county": county,
                "url": url,
                "format": fmt,
            }
        )
    return results

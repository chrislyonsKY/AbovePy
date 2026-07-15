"""Oblique imagery access — S3-based discovery until STAC collection is ready.

KyFromAbove Phase 3 oblique imagery is captured from 4 directions (Backward,
Forward, Left, Right) using a 5-camera Vexcel system.  The imagery lives on
S3 as Cloud-Optimized GeoTIFFs with JSON sidecar metadata files.

Once Ian Horn's ``kyobliques`` STAC collection is published, the normal
``abovepy.search()`` flow will work.  Until then, these helpers provide
direct S3-based discovery.

Data organization on S3::

    s3://kyfromabove/imagery/obliques/Phase3/
        KY_KYAPED_2022_Season2_3IN/
            Bwd_2025_401340.tif
            Bwd_2025_401340.json
            Fwd_2025_401340.tif
            ...
        KY_KYAPED_2023_Season1_3IN/
        KY_KYAPED_2023_Season2_3IN/
        KY_KYAPED_2024_Season1_3IN/
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET

import httpx

from abovepy._constants import S3_BUCKET, S3_OBLIQUES_PREFIX, S3_REGION
from abovepy._security import validate_remote_url
from abovepy.obliques._metadata import ObliqueFrame, fetch_all_metadata

logger = logging.getLogger(__name__)

# Map user-facing direction names to the S3 filename prefix
DIRECTIONS = {
    "bwd": "Bwd",
    "fwd": "Fwd",
    "left": "Left",
    "right": "Right",
}

S3_BASE_URL = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com"

# S3 XML namespace
_S3_NS = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}


def _list_bucket(params: dict[str, str]) -> ET.Element:
    """Issue a validated S3 ListObjects request and return the parsed XML."""
    url = f"{S3_BASE_URL}/"
    validate_remote_url(url)
    resp = httpx.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return ET.fromstring(resp.text)  # noqa: S314 — trusted AWS S3 ListObjects response


def list_oblique_seasons() -> list[str]:
    """List available oblique imagery seasons from S3.

    Returns
    -------
    list[str]
        Season directory names (e.g., ``["KY_KYAPED_2022_Season2_3IN", ...]``).
    """
    tree = _list_bucket({"prefix": S3_OBLIQUES_PREFIX, "delimiter": "/"})
    seasons = []
    for prefix_el in tree.findall(".//s3:CommonPrefixes/s3:Prefix", _S3_NS):
        text = prefix_el.text or ""
        # Extract the season directory name from the full prefix
        name = text.rstrip("/").split("/")[-1]
        if name.startswith("KY_"):
            seasons.append(name)

    return sorted(seasons)


def _resolve_season(season: str | None) -> str | None:
    """Return the given season, or the most recent one from S3."""
    if season is not None:
        return season
    seasons = list_oblique_seasons()
    if not seasons:
        logger.warning("No oblique seasons found on S3.")
        return None
    resolved = seasons[-1]  # Most recent
    logger.info("Using most recent season: %s", resolved)
    return resolved


def _list_frames(direction: str, season: str, max_items: int = 100) -> list[ObliqueFrame]:
    """List oblique frames for one direction + season from the S3 bucket.

    ``direction`` must already be lowercase and validated against
    ``DIRECTIONS``.
    """
    file_prefix = DIRECTIONS[direction]
    s3_prefix = f"{S3_OBLIQUES_PREFIX}{season}/{file_prefix}_"
    tree = _list_bucket({"prefix": s3_prefix, "max-keys": str(max_items * 2)})

    results: list[ObliqueFrame] = []
    for key_el in tree.findall(".//s3:Contents/s3:Key", _S3_NS):
        key = key_el.text or ""
        if not key.endswith(".tif"):
            continue

        filename = key.split("/")[-1]
        frame_id = filename.replace(".tif", "")
        results.append(
            ObliqueFrame(
                frame_id=frame_id,
                tif_url=f"{S3_BASE_URL}/{key}",
                json_url=f"{S3_BASE_URL}/{key.replace('.tif', '.json')}",
                season=season,
                direction=direction,
            )
        )

        if len(results) >= max_items:
            break

    return results


def search_obliques(
    direction: str | None = "bwd",
    season: str | None = None,
    max_items: int = 100,
    *,
    point: tuple[float, float] | None = None,
    radius_feet: float = 500.0,
    fetch_metadata: bool = False,
    max_sidecar_fetches: int = 500,
) -> list[ObliqueFrame]:
    """List available oblique frames from S3.

    Without ``point``, lists frames for one direction + season (S3 listing
    order). With ``point``, performs a spatial search: frames whose ground
    footprint (from the JSON sidecar) intersects a ``radius_feet`` buffer
    around the point, sorted nearest-first.

    Parameters
    ----------
    direction : str or None
        Camera direction: ``"bwd"``, ``"fwd"``, ``"left"``, or ``"right"``.
        Case-insensitive. Pass ``None`` (only with ``point``) to search
        all four directions.
    season : str, optional
        Season directory name (e.g., ``"KY_KYAPED_2023_Season1_3IN"``).
        If not provided, uses the most recent season.
    max_items : int
        Maximum frames to return. Default 100.
    point : tuple, optional
        (longitude, latitude) in EPSG:4326 for spatial search.
    radius_feet : float
        Search radius around ``point`` in US survey feet. Default 500.
    fetch_metadata : bool
        Eagerly fetch JSON sidecars for the returned frames. Always
        true for spatial searches (footprints come from sidecars).
    max_sidecar_fetches : int
        Upper bound on sidecar downloads during a spatial search.
        Default 500.

    Returns
    -------
    list[ObliqueFrame]
        Frames with ``frame_id``, ``tif_url``, ``json_url``, ``season``,
        ``direction``. Dict-style access (``frame["tif_url"]``) is
        supported for backward compatibility.

    Raises
    ------
    ValueError
        If ``direction`` is invalid, or ``direction`` is None without
        ``point``, or a spatial search would exceed
        ``max_sidecar_fetches``.
    """
    direction_lower: str | None = None
    if direction is not None:
        direction_lower = direction.lower()
        if direction_lower not in DIRECTIONS:
            valid = ", ".join(sorted(DIRECTIONS))
            raise ValueError(f"Invalid direction '{direction}'. Valid directions: {valid}")
    elif point is None:
        raise ValueError("direction=None searches all four directions and requires point=.")

    if point is not None:
        from abovepy.obliques._spatial import search_obliques_near

        return search_obliques_near(
            point,
            radius_feet=radius_feet,
            direction=direction_lower,
            season=season,
            max_items=max_items,
            max_sidecar_fetches=max_sidecar_fetches,
        )

    season = _resolve_season(season)
    if season is None or direction_lower is None:
        return []

    frames = _list_frames(direction_lower, season, max_items=max_items)
    if fetch_metadata:
        fetch_all_metadata(frames)
    return frames

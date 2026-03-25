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


def list_oblique_seasons() -> list[str]:
    """List available oblique imagery seasons from S3.

    Returns
    -------
    list[str]
        Season directory names (e.g., ``["KY_KYAPED_2022_Season2_3IN", ...]``).
    """
    url = f"{S3_BASE_URL}/"
    resp = httpx.get(
        url,
        params={"prefix": S3_OBLIQUES_PREFIX, "delimiter": "/"},
        timeout=30,
    )
    resp.raise_for_status()

    tree = ET.fromstring(resp.text)
    seasons = []
    for prefix_el in tree.findall(".//s3:CommonPrefixes/s3:Prefix", _S3_NS):
        text = prefix_el.text or ""
        # Extract the season directory name from the full prefix
        name = text.rstrip("/").split("/")[-1]
        if name.startswith("KY_"):
            seasons.append(name)

    return sorted(seasons)


def search_obliques(
    direction: str = "bwd",
    season: str | None = None,
    max_items: int = 100,
) -> list[dict[str, str]]:
    """List available oblique frames from S3 for a given direction and season.

    Parameters
    ----------
    direction : str
        Camera direction: ``"bwd"``, ``"fwd"``, ``"left"``, or ``"right"``.
        Case-insensitive.
    season : str, optional
        Season directory name (e.g., ``"KY_KYAPED_2023_Season1_3IN"``).
        If not provided, uses the most recent season.
    max_items : int
        Maximum frames to return. Default 100.

    Returns
    -------
    list[dict[str, str]]
        List of dicts with keys: ``frame_id``, ``tif_url``, ``json_url``,
        ``season``, ``direction``.

    Raises
    ------
    ValueError
        If ``direction`` is invalid.
    """
    direction_lower = direction.lower()
    if direction_lower not in DIRECTIONS:
        valid = ", ".join(sorted(DIRECTIONS))
        raise ValueError(
            f"Invalid direction '{direction}'. Valid directions: {valid}"
        )

    file_prefix = DIRECTIONS[direction_lower]

    # Resolve season
    if season is None:
        seasons = list_oblique_seasons()
        if not seasons:
            logger.warning("No oblique seasons found on S3.")
            return []
        season = seasons[-1]  # Most recent
        logger.info("Using most recent season: %s", season)

    # List TIF files for this direction + season
    s3_prefix = f"{S3_OBLIQUES_PREFIX}{season}/{file_prefix}_"
    url = f"{S3_BASE_URL}/"
    resp = httpx.get(
        url,
        params={"prefix": s3_prefix, "max-keys": str(max_items * 2)},
        timeout=30,
    )
    resp.raise_for_status()

    tree = ET.fromstring(resp.text)
    results: list[dict[str, str]] = []

    for key_el in tree.findall(".//s3:Contents/s3:Key", _S3_NS):
        key = key_el.text or ""
        if not key.endswith(".tif"):
            continue

        filename = key.split("/")[-1]
        frame_id = filename.replace(".tif", "")
        tif_url = f"{S3_BASE_URL}/{key}"
        json_url = f"{S3_BASE_URL}/{key.replace('.tif', '.json')}"

        results.append({
            "frame_id": frame_id,
            "tif_url": tif_url,
            "json_url": json_url,
            "season": season,
            "direction": direction_lower,
        })

        if len(results) >= max_items:
            break

    return results

"""Spatial oblique search — point/radius queries and 4-direction bundles.

Oblique frame footprints live only in per-frame JSON sidecars, so a naive
statewide spatial search would need thousands of HTTP requests. The search
here uses a three-tier strategy:

1. **Season index (one fetch, preferred).** The S3 bucket carries
   ``ExteriorOrientationFiles/`` and ``Metadata/`` prefixes with per-season
   bulk metadata. If a parseable index exists for the season, every frame's
   exposure center comes from a single request.
2. **Bounded sidecar fetch (fallback).** Without an index, candidate
   sidecars are fetched concurrently — hard-capped by
   ``max_sidecar_fetches`` with a loud error rather than a silent partial
   result.
3. **Precise filter.** Frames whose footprint intersects the search buffer
   win; frames with only an exposure center are kept when the center falls
   within the buffer plus a slack allowance for oblique ground coverage.
"""

from __future__ import annotations

import csv
import io
import json
import logging
from typing import TYPE_CHECKING, Any

import httpx

from abovepy._constants import (
    S3_OBLIQUES_EO_PREFIX,
    S3_OBLIQUES_METADATA_PREFIX,
    SIDECAR_CACHE_TTL,
)
from abovepy._security import validate_remote_url
from abovepy.obliques._metadata import ObliqueFrame, fetch_all_metadata
from abovepy.utils.cache import TTLCache

if TYPE_CHECKING:
    from shapely.geometry.base import BaseGeometry

logger = logging.getLogger(__name__)

# Oblique frames image the ground well beyond their exposure center. When
# only a center point is known (no footprint), the search buffer is widened
# by this many feet before testing containment.
OBLIQUE_CENTER_SLACK_FEET = 1500.0

# Parsed per-season index: {season: {frame_id: (lon, lat)} or None}
_season_index_cache = TTLCache(maxsize=16, ttl=SIDECAR_CACHE_TTL)

_INDEX_ID_KEYS = ("frame_id", "frame", "id", "image", "image_id", "photoid", "photo_id")
_INDEX_LON_KEYS = ("longitude", "lon", "lng", "x", "easting")
_INDEX_LAT_KEYS = ("latitude", "lat", "y", "northing")


def _distance_feet(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Distance in US survey feet between two (lon, lat) points."""
    from pyproj import Transformer

    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3089", always_xy=True)
    ax, ay = transformer.transform(a[0], a[1])
    bx, by = transformer.transform(b[0], b[1])
    return float(((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5)


def _to_lonlat(x: float, y: float) -> tuple[float, float]:
    """Coerce a coordinate pair to (lon, lat), reprojecting from EPSG:3089
    when the magnitudes look like Kentucky Single Zone feet."""
    if abs(x) <= 360 and abs(y) <= 90:
        return (x, y)
    from pyproj import Transformer

    transformer = Transformer.from_crs("EPSG:3089", "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(x, y)
    return (float(lon), float(lat))


# ---------------------------------------------------------------------------
# Tier 1 — per-season bulk index
# ---------------------------------------------------------------------------


def _parse_index_records(records: list[dict[str, Any]]) -> dict[str, tuple[float, float]]:
    """Extract {frame_id: (lon, lat)} from a list of record dicts."""
    positions: dict[str, tuple[float, float]] = {}
    for record in records:
        lowered = {str(k).strip().lower(): v for k, v in record.items()}
        frame_id = next(
            (str(lowered[k]).strip() for k in _INDEX_ID_KEYS if lowered.get(k)),
            None,
        )
        lon = next((lowered[k] for k in _INDEX_LON_KEYS if k in lowered), None)
        lat = next((lowered[k] for k in _INDEX_LAT_KEYS if k in lowered), None)
        if not frame_id or lon is None or lat is None:
            continue
        try:
            positions[frame_id] = _to_lonlat(float(lon), float(lat))
        except (ValueError, TypeError):
            continue
    return positions


def _parse_index_payload(text: str) -> dict[str, tuple[float, float]]:
    """Parse a bulk index file (JSON or delimited text) into positions."""
    stripped = text.lstrip()
    if stripped.startswith(("{", "[")):
        try:
            payload = json.loads(text)
        except ValueError:
            return {}
        if isinstance(payload, dict):
            positions: dict[str, tuple[float, float]] = {}
            for frame_id, value in payload.items():
                if isinstance(value, list | tuple) and len(value) >= 2:
                    try:
                        positions[str(frame_id)] = _to_lonlat(float(value[0]), float(value[1]))
                    except (ValueError, TypeError):
                        continue
                elif isinstance(value, dict):
                    parsed = _parse_index_records([{"frame_id": frame_id, **value}])
                    positions.update(parsed)
            return positions
        if isinstance(payload, list):
            return _parse_index_records([r for r in payload if isinstance(r, dict)])
        return {}

    # Delimited text (CSV or whitespace) with a header row
    sample = stripped[:2048]
    delimiter = "\t" if "\t" in sample else ("," if "," in sample else " ")
    try:
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter, skipinitialspace=True)
        return _parse_index_records([dict(row) for row in reader])
    except csv.Error:
        return {}


def _load_season_index(season: str) -> dict[str, tuple[float, float]] | None:
    """Try to load a bulk exposure-center index for a season (Tier 1).

    Returns ``None`` when no parseable index exists — the caller falls
    back to per-frame sidecar fetches.
    """
    cached = _season_index_cache.get(season)
    if cached is not None:
        return cached if cached else None  # {} sentinel means "no index"

    from abovepy.obliques._s3 import _S3_NS, S3_BASE_URL, _list_bucket

    positions: dict[str, tuple[float, float]] = {}
    for prefix in (S3_OBLIQUES_EO_PREFIX, S3_OBLIQUES_METADATA_PREFIX):
        try:
            tree = _list_bucket({"prefix": prefix, "max-keys": "1000"})
        except (httpx.HTTPError, ValueError):
            continue
        for key_el in tree.findall(".//s3:Contents/s3:Key", _S3_NS):
            key = key_el.text or ""
            if season not in key or not key.lower().endswith((".json", ".csv", ".txt")):
                continue
            url = f"{S3_BASE_URL}/{key}"
            try:
                validate_remote_url(url)
                resp = httpx.get(url, timeout=60, follow_redirects=True)
                resp.raise_for_status()
            except (httpx.HTTPError, ValueError) as exc:
                logger.debug("Could not fetch index candidate %s: %s", key, exc)
                continue
            parsed = _parse_index_payload(resp.text)
            if parsed:
                logger.info("Loaded %d exposure centers from %s", len(parsed), key)
                positions.update(parsed)
        if positions:
            break

    _season_index_cache.set(season, positions)
    return positions or None


def clear_season_index_cache() -> None:
    """Clear the cached per-season bulk indexes."""
    _season_index_cache.clear()


# ---------------------------------------------------------------------------
# Spatial search
# ---------------------------------------------------------------------------


def _frame_position(
    frame: ObliqueFrame,
    index: dict[str, tuple[float, float]] | None,
) -> tuple[float, float] | None:
    """Best-known (lon, lat) for a frame: footprint centroid, sidecar
    camera position, or bulk-index exposure center."""
    footprint = frame.footprint
    if footprint is not None:
        centroid = footprint.centroid
        return (float(centroid.x), float(centroid.y))
    position = frame.camera_position
    if position is not None:
        return position
    if index is not None:
        return index.get(frame.frame_id)
    return None


def _frame_matches(
    frame: ObliqueFrame,
    index: dict[str, tuple[float, float]] | None,
    aoi: BaseGeometry,
    slack_aoi: BaseGeometry,
) -> bool:
    """Tier 3 — precise filter for one frame."""
    from shapely.geometry import Point

    footprint = frame.footprint
    if footprint is not None:
        return bool(footprint.intersects(aoi))
    position = frame.camera_position or (index.get(frame.frame_id) if index else None)
    if position is not None:
        return bool(slack_aoi.contains(Point(position)))
    logger.warning(
        "Frame %s has no footprint or exposure center; excluded from spatial search.",
        frame.frame_id,
    )
    return False


def search_obliques_near(
    point: tuple[float, float],
    *,
    radius_feet: float = 500.0,
    direction: str | None = None,
    season: str | None = None,
    max_items: int = 20,
    max_sidecar_fetches: int = 500,
    max_workers: int = 8,
) -> list[ObliqueFrame]:
    """Find oblique frames covering a point, nearest first.

    Parameters
    ----------
    point : tuple
        (longitude, latitude) in EPSG:4326.
    radius_feet : float
        Search radius in US survey feet. Default 500.
    direction : str or None
        Restrict to one camera direction, or None for all four.
    season : str, optional
        Season directory name. Defaults to the most recent season.
    max_items : int
        Maximum frames to return. Default 20.
    max_sidecar_fetches : int
        Hard cap on per-frame sidecar downloads when no bulk index is
        available. Default 500.
    max_workers : int
        Concurrent sidecar fetch threads. Default 8.

    Returns
    -------
    list[ObliqueFrame]
        Matching frames sorted by distance from ``point``.

    Raises
    ------
    ValueError
        If the search would require more sidecar fetches than
        ``max_sidecar_fetches``.
    """
    from shapely.geometry import Point

    from abovepy.obliques._s3 import DIRECTIONS, _list_frames, _resolve_season
    from abovepy.utils.crs import buffer_feet

    season = _resolve_season(season)
    if season is None:
        return []

    directions = [direction] if direction else sorted(DIRECTIONS)

    # Candidate listing (cheap S3 XML) — bounded well above max_items so
    # the radius filter has enough to work with.
    listing_cap = max(max_items, max_sidecar_fetches)
    candidates: list[ObliqueFrame] = []
    for d in directions:
        candidates.extend(_list_frames(d, season, max_items=listing_cap))

    if not candidates:
        return []

    # Tier 1: bulk index; Tier 2: bounded sidecar fetches.
    index = _load_season_index(season)
    if index:
        center = Point(point)
        slack: Any = buffer_feet(center, radius_feet + OBLIQUE_CENTER_SLACK_FEET)
        prefiltered = [
            f
            for f in candidates
            if f.frame_id not in index or slack.contains(Point(index[f.frame_id]))
        ]
        logger.info(
            "Season index prefilter: %d of %d candidates kept.",
            len(prefiltered),
            len(candidates),
        )
        candidates = prefiltered

    pending = [f for f in candidates if f.metadata is None]
    if len(pending) > max_sidecar_fetches:
        raise ValueError(
            f"Spatial search over season '{season}' needs {len(pending)} sidecar "
            f"fetches, exceeding the limit of {max_sidecar_fetches}. Narrow the "
            f"search with direction= and season=, or raise max_sidecar_fetches=."
        )
    fetch_all_metadata(candidates, max_workers=max_workers)

    aoi = buffer_feet(Point(point), radius_feet)
    slack_aoi = buffer_feet(Point(point), radius_feet + OBLIQUE_CENTER_SLACK_FEET)
    matches = [f for f in candidates if _frame_matches(f, index, aoi, slack_aoi)]

    def _sort_key(frame: ObliqueFrame) -> float:
        position = _frame_position(frame, index)
        if position is None:
            return float("inf")
        return _distance_feet(point, position)

    matches.sort(key=_sort_key)
    return matches[:max_items]


def oblique_bundle(
    point: tuple[float, float],
    season: str | None = None,
    radius_feet: float = 500.0,
    *,
    max_sidecar_fetches: int = 500,
) -> dict[str, ObliqueFrame | None]:
    """Best oblique frame per camera direction for a point.

    Returns the frame set a site inspector wants: the closest usable
    Backward, Forward, Left, and Right view of a location.

    Parameters
    ----------
    point : tuple
        (longitude, latitude) in EPSG:4326.
    season : str, optional
        Season directory name. Defaults to the most recent season.
    radius_feet : float
        Search radius in US survey feet. Default 500.
    max_sidecar_fetches : int
        Hard cap on per-frame sidecar downloads. Default 500.

    Returns
    -------
    dict[str, ObliqueFrame | None]
        Keys ``"bwd"``, ``"fwd"``, ``"left"``, ``"right"``. ``None``
        for a direction with no frame covering the point.
    """
    from shapely.geometry import Point

    from abovepy.obliques._s3 import DIRECTIONS

    matches = search_obliques_near(
        point,
        radius_feet=radius_feet,
        direction=None,
        season=season,
        max_items=len(DIRECTIONS) * 25,
        max_sidecar_fetches=max_sidecar_fetches,
    )

    target = Point(point)
    bundle: dict[str, ObliqueFrame | None] = dict.fromkeys(sorted(DIRECTIONS))

    def _rank(frame: ObliqueFrame) -> tuple[int, float, float]:
        footprint = frame.footprint
        contains = footprint is not None and footprint.contains(target)
        position = _frame_position(frame, None)
        distance = _distance_feet(point, position) if position else float("inf")
        timestamp = frame.timestamp
        recency = -timestamp.timestamp() if timestamp else 0.0
        return (0 if contains else 1, distance, recency)

    for direction in bundle:
        frames = [f for f in matches if f.direction == direction]
        if frames:
            bundle[direction] = min(frames, key=_rank)

    return bundle

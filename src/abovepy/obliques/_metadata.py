"""Oblique frame metadata — ObliqueFrame dataclass and JSON sidecar handling.

Each KyFromAbove oblique frame on S3 has a JSON sidecar file next to the
COG (``Bwd_2025_401340.json`` beside ``Bwd_2025_401340.tif``) carrying
georeferencing and camera metadata. The exact sidecar schema is not yet
published, so parsing here is deliberately tolerant: the raw payload is
always preserved on the frame, and every derived property returns ``None``
when the expected keys are absent or unparseable.

``ObliqueFrame`` implements the ``Mapping`` protocol over its five core
keys (``frame_id``, ``tif_url``, ``json_url``, ``season``, ``direction``)
so code written against the pre-2.2 ``list[dict]`` return type of
``search_obliques()`` keeps working unchanged.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, ClassVar

import httpx

from abovepy._constants import REQUEST_TIMEOUT, SIDECAR_CACHE_TTL
from abovepy._security import validate_remote_url
from abovepy.utils.cache import TTLCache

if TYPE_CHECKING:
    from shapely.geometry.base import BaseGeometry

logger = logging.getLogger(__name__)

# Session-lifetime cache of parsed sidecar payloads, keyed by URL.
_sidecar_cache = TTLCache(maxsize=4096, ttl=SIDECAR_CACHE_TTL)

# Candidate key names tried, in order, when extracting known fields from
# the (undocumented) sidecar schema.
_CAMERA_KEYS = ("camera", "exterior_orientation", "eo", "sensor")
_FOOTPRINT_KEYS = ("footprint", "geometry", "boundary", "extent")
_TIMESTAMP_KEYS = ("datetime", "timestamp", "acquisition_date", "acquired", "date")
_CENTER_KEYS = ("center", "camera_center", "position")


def clear_sidecar_cache() -> None:
    """Clear the module-level sidecar metadata cache."""
    _sidecar_cache.clear()


def fetch_sidecar(
    json_url: str,
    *,
    timeout: float = REQUEST_TIMEOUT,
    use_cache: bool = True,
) -> dict[str, Any]:
    """Fetch and cache a frame's JSON sidecar metadata.

    Parameters
    ----------
    json_url : str
        URL of the sidecar ``.json`` file. Must be a trusted
        KyFromAbove host.
    timeout : float
        Request timeout in seconds. Default 30.
    use_cache : bool
        Serve repeat fetches from the in-memory cache. Default True.

    Returns
    -------
    dict
        Parsed sidecar payload. Empty dict if the response body is
        not a JSON object (logged as a warning).

    Raises
    ------
    ValueError
        If the URL host is not a known KyFromAbove endpoint.
    httpx.HTTPError
        On request failure or non-2xx response.
    """
    validate_remote_url(json_url)

    if use_cache:
        cached = _sidecar_cache.get(json_url)
        if cached is not None:
            return dict(cached)

    resp = httpx.get(json_url, timeout=timeout, follow_redirects=True)
    resp.raise_for_status()

    try:
        payload = resp.json()
    except ValueError:
        logger.warning("Sidecar at %s is not valid JSON; ignoring.", json_url)
        payload = {}

    if not isinstance(payload, dict):
        logger.warning(
            "Sidecar at %s is JSON but not an object (got %s); ignoring.",
            json_url,
            type(payload).__name__,
        )
        payload = {}

    _sidecar_cache.set(json_url, payload)
    return dict(payload)


def _parse_timestamp(value: Any) -> datetime | None:
    """Coerce a sidecar timestamp value (ISO string or epoch) to datetime."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        try:
            return datetime.fromtimestamp(value, tz=UTC)
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _coerce_geometry(value: Any) -> BaseGeometry | None:
    """Coerce a GeoJSON dict, coordinate list, or WKT string to shapely."""
    if isinstance(value, dict) and "type" in value and "coordinates" in value:
        try:
            from shapely.geometry import shape

            return shape(value)
        except (ImportError, ValueError, TypeError, AttributeError):
            return None
    if isinstance(value, list | tuple) and len(value) >= 3:
        try:
            from shapely.geometry import Polygon

            return Polygon([(float(x), float(y)) for x, y in value])
        except (ImportError, ValueError, TypeError):
            return None
    if isinstance(value, str):
        try:
            from shapely import wkt

            return wkt.loads(value)
        except Exception:
            return None
    return None


@dataclass
class ObliqueFrame(Mapping[str, Any]):
    """A single oblique imagery frame with optional sidecar metadata.

    Behaves like the plain dict returned by pre-2.2 ``search_obliques()``
    (``frame["tif_url"]``, ``dict(frame)``, ``frame.get(...)`` all work)
    while exposing parsed sidecar metadata through tolerant properties.

    Attributes
    ----------
    frame_id : str
        Frame identifier (TIF filename without extension).
    tif_url : str
        HTTPS URL of the frame's Cloud-Optimized GeoTIFF.
    json_url : str
        HTTPS URL of the frame's JSON sidecar.
    season : str
        Season directory name (e.g. ``"KY_KYAPED_2023_Season1_3IN"``).
    direction : str
        Camera direction: ``"bwd"``, ``"fwd"``, ``"left"``, or ``"right"``.
    metadata : dict or None
        Raw sidecar payload, if fetched. ``None`` until
        :meth:`fetch_metadata` is called (or metadata was passed in).
    """

    frame_id: str
    tif_url: str
    json_url: str
    season: str
    direction: str
    metadata: dict[str, Any] | None = field(default=None, repr=False)

    _KEYS: ClassVar[tuple[str, ...]] = (
        "frame_id",
        "tif_url",
        "json_url",
        "season",
        "direction",
    )

    # ------------------------------------------------------------------
    # Mapping protocol — backward compatibility with the v2.1 dict shape
    # ------------------------------------------------------------------

    def __getitem__(self, key: str) -> Any:
        if key in self._KEYS:
            return getattr(self, key)
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        return iter(self._KEYS)

    def __len__(self) -> int:
        return len(self._KEYS)

    def to_dict(self) -> dict[str, str]:
        """Return the frame's core fields as a plain dict."""
        return {key: getattr(self, key) for key in self._KEYS}

    # ------------------------------------------------------------------
    # Sidecar metadata
    # ------------------------------------------------------------------

    def fetch_metadata(
        self,
        *,
        force: bool = False,
        timeout: float = REQUEST_TIMEOUT,
    ) -> dict[str, Any]:
        """Fetch this frame's JSON sidecar and attach it to the frame.

        Parameters
        ----------
        force : bool
            Refetch even if metadata is already attached (bypasses the
            module cache). Default False.
        timeout : float
            Request timeout in seconds.

        Returns
        -------
        dict
            The raw sidecar payload (also stored on ``self.metadata``).
        """
        if self.metadata is not None and not force:
            return self.metadata
        self.metadata = fetch_sidecar(self.json_url, timeout=timeout, use_cache=not force)
        return self.metadata

    @property
    def raw(self) -> dict[str, Any] | None:
        """The untouched sidecar payload (``None`` if not fetched)."""
        return self.metadata

    @property
    def camera(self) -> dict[str, Any] | None:
        """Camera / exterior-orientation parameters, if present."""
        if not self.metadata:
            return None
        for key in _CAMERA_KEYS:
            value = self.metadata.get(key)
            if isinstance(value, dict):
                return value
        return None

    @property
    def timestamp(self) -> datetime | None:
        """Acquisition timestamp, if present and parseable."""
        if not self.metadata:
            return None
        for key in _TIMESTAMP_KEYS:
            if key in self.metadata:
                parsed = _parse_timestamp(self.metadata[key])
                if parsed is not None:
                    return parsed
        return None

    @property
    def footprint(self) -> BaseGeometry | None:
        """Ground footprint geometry (EPSG:4326), if present and parseable."""
        if not self.metadata:
            return None
        for key in _FOOTPRINT_KEYS:
            value = self.metadata.get(key)
            if value is None:
                continue
            geom = _coerce_geometry(value)
            if geom is not None:
                return geom
        bounds = self.metadata.get("bbox") or self.metadata.get("bounds")
        if isinstance(bounds, list | tuple) and len(bounds) == 4:
            try:
                from shapely.geometry import box

                return box(*(float(v) for v in bounds))
            except (ImportError, ValueError, TypeError):
                return None
        return None

    @property
    def camera_position(self) -> tuple[float, float] | None:
        """Exposure-center (lon, lat), if present in the sidecar."""
        if not self.metadata:
            return None
        for key in _CENTER_KEYS:
            value = self.metadata.get(key)
            if (
                isinstance(value, dict)
                and value.get("type") == "Point"
                and isinstance(value.get("coordinates"), list | tuple)
                and len(value["coordinates"]) >= 2
            ):
                try:
                    return (float(value["coordinates"][0]), float(value["coordinates"][1]))
                except (ValueError, TypeError):
                    continue
        sources: list[dict[str, Any]] = [self.metadata]
        camera = self.camera
        if camera is not None:
            sources.append(camera)
        for source in sources:
            for lon_key, lat_key in (("longitude", "latitude"), ("lon", "lat"), ("lng", "lat")):
                if lon_key in source and lat_key in source:
                    try:
                        return (float(source[lon_key]), float(source[lat_key]))
                    except (ValueError, TypeError):
                        continue
        return None

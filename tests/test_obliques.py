"""Tests for oblique imagery helpers."""

import httpx
import pytest
import respx

from abovepy.obliques import (
    DIRECTIONS,
    S3_BASE_URL,
    list_oblique_seasons,
    search_obliques,
)

# Sample S3 list-objects-v2 XML response
_SEASONS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <Name>kyfromabove</Name>
  <Prefix>imagery/obliques/Phase3/</Prefix>
  <Delimiter>/</Delimiter>
  <CommonPrefixes>
    <Prefix>imagery/obliques/Phase3/ExteriorOrientationFiles/</Prefix>
  </CommonPrefixes>
  <CommonPrefixes>
    <Prefix>imagery/obliques/Phase3/KY_KYAPED_2022_Season2_3IN/</Prefix>
  </CommonPrefixes>
  <CommonPrefixes>
    <Prefix>imagery/obliques/Phase3/KY_KYAPED_2023_Season1_3IN/</Prefix>
  </CommonPrefixes>
  <CommonPrefixes>
    <Prefix>imagery/obliques/Phase3/Metadata/</Prefix>
  </CommonPrefixes>
</ListBucketResult>"""

_FRAMES_XML = """<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <Name>kyfromabove</Name>
  <Contents>
    <Key>imagery/obliques/Phase3/KY_KYAPED_2023_Season1_3IN/Bwd_0_40721.json</Key>
    <Size>1234</Size>
  </Contents>
  <Contents>
    <Key>imagery/obliques/Phase3/KY_KYAPED_2023_Season1_3IN/Bwd_0_40721.tif</Key>
    <Size>88125139</Size>
  </Contents>
  <Contents>
    <Key>imagery/obliques/Phase3/KY_KYAPED_2023_Season1_3IN/Bwd_0_40722.json</Key>
    <Size>1234</Size>
  </Contents>
  <Contents>
    <Key>imagery/obliques/Phase3/KY_KYAPED_2023_Season1_3IN/Bwd_0_40722.tif</Key>
    <Size>88125139</Size>
  </Contents>
</ListBucketResult>"""


def test_directions_mapping():
    assert set(DIRECTIONS.keys()) == {"bwd", "fwd", "left", "right"}


@respx.mock
def test_list_oblique_seasons():
    respx.get(f"{S3_BASE_URL}/").mock(return_value=httpx.Response(200, text=_SEASONS_XML))
    seasons = list_oblique_seasons()
    assert "KY_KYAPED_2022_Season2_3IN" in seasons
    assert "KY_KYAPED_2023_Season1_3IN" in seasons
    # Non-KY_ prefixes should be filtered out
    assert "ExteriorOrientationFiles" not in seasons
    assert "Metadata" not in seasons


@respx.mock
def test_search_obliques_basic():
    # First call resolves seasons, second lists frames
    respx.get(f"{S3_BASE_URL}/").mock(
        side_effect=[
            httpx.Response(200, text=_SEASONS_XML),
            httpx.Response(200, text=_FRAMES_XML),
        ]
    )
    results = search_obliques(direction="bwd")
    assert len(results) == 2
    assert results[0]["frame_id"] == "Bwd_0_40721"
    assert results[0]["tif_url"].endswith(".tif")
    assert results[0]["json_url"].endswith(".json")
    assert results[0]["direction"] == "bwd"
    assert "Season1" in results[0]["season"]


@respx.mock
def test_search_obliques_explicit_season():
    respx.get(f"{S3_BASE_URL}/").mock(return_value=httpx.Response(200, text=_FRAMES_XML))
    results = search_obliques(
        direction="bwd",
        season="KY_KYAPED_2023_Season1_3IN",
    )
    assert len(results) == 2


def test_search_obliques_invalid_direction():
    with pytest.raises(ValueError, match="Invalid direction"):
        search_obliques(direction="up")


def test_search_obliques_case_insensitive():
    """Direction should be case-insensitive."""
    # Just test it doesn't raise — actual HTTP would be mocked
    with pytest.raises(ValueError, match="Invalid direction"):
        search_obliques(direction="DIAGONAL")

    # These should not raise ValueError
    import contextlib

    for d in ["BWD", "Fwd", "LEFT", "Right"]:
        # Will fail on HTTP but not on validation
        with contextlib.suppress(httpx.ConnectError, httpx.HTTPError):
            search_obliques(direction=d, season="fake")


# ---------------------------------------------------------------------------
# Spatial search + bundles (v2.2)
# ---------------------------------------------------------------------------

from abovepy.obliques import (  # noqa: E402
    ObliqueFrame,
    clear_season_index_cache,
    clear_sidecar_cache,
    oblique_bundle,
)

SEASON = "KY_KYAPED_2023_Season1_3IN"
_PREFIX = f"imagery/obliques/Phase3/{SEASON}"

# Near-frame footprint covers the search point (-84.85, 38.20); far frame is
# ~0.5 degrees away.
_NEAR_SIDECAR = {
    "datetime": "2023-04-12T15:30:00Z",
    "footprint": {
        "type": "Polygon",
        "coordinates": [
            [[-84.86, 38.19], [-84.84, 38.19], [-84.84, 38.21], [-84.86, 38.21], [-84.86, 38.19]]
        ],
    },
}
_FAR_SIDECAR = {
    "datetime": "2023-04-12T15:31:00Z",
    "footprint": {
        "type": "Polygon",
        "coordinates": [
            [[-84.36, 38.69], [-84.34, 38.69], [-84.34, 38.71], [-84.36, 38.71], [-84.36, 38.69]]
        ],
    },
}


def _frames_xml(direction_prefix: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <Name>kyfromabove</Name>
  <Contents><Key>{_PREFIX}/{direction_prefix}_0_1.tif</Key></Contents>
  <Contents><Key>{_PREFIX}/{direction_prefix}_0_1.json</Key></Contents>
  <Contents><Key>{_PREFIX}/{direction_prefix}_0_2.tif</Key></Contents>
  <Contents><Key>{_PREFIX}/{direction_prefix}_0_2.json</Key></Contents>
</ListBucketResult>"""


_EMPTY_XML = """<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <Name>kyfromabove</Name>
</ListBucketResult>"""


@pytest.fixture(autouse=True)
def _clear_oblique_caches():
    clear_sidecar_cache()
    clear_season_index_cache()
    yield
    clear_sidecar_cache()
    clear_season_index_cache()


def _mock_listing_router():
    """Route S3 ListObjects requests by prefix param; sidecars by URL."""

    def _list_route(request):
        prefix = request.url.params.get("prefix", "")
        for key, dir_prefix in (
            ("Bwd_", "Bwd"),
            ("Fwd_", "Fwd"),
            ("Left_", "Left"),
            ("Right_", "Right"),
        ):
            if prefix.endswith(key.rstrip("_") + "_") or prefix.endswith(f"/{dir_prefix}_"):
                return httpx.Response(200, text=_frames_xml(dir_prefix))
        # EO / Metadata index prefixes → empty (no bulk index available)
        return httpx.Response(200, text=_EMPTY_XML)

    respx.get(f"{S3_BASE_URL}/").mock(side_effect=_list_route)


def _mock_sidecars(direction_prefix: str):
    respx.get(f"{S3_BASE_URL}/{_PREFIX}/{direction_prefix}_0_1.json").mock(
        return_value=httpx.Response(200, json=_NEAR_SIDECAR)
    )
    respx.get(f"{S3_BASE_URL}/{_PREFIX}/{direction_prefix}_0_2.json").mock(
        return_value=httpx.Response(200, json=_FAR_SIDECAR)
    )


class TestReturnTypeCompat:
    @respx.mock
    def test_search_returns_oblique_frames(self):
        respx.get(f"{S3_BASE_URL}/").mock(return_value=httpx.Response(200, text=_frames_xml("Bwd")))
        results = search_obliques(direction="bwd", season=SEASON)
        assert all(isinstance(f, ObliqueFrame) for f in results)
        # Legacy dict-style consumption still works
        assert results[0]["frame_id"] == "Bwd_0_1"
        assert dict(results[0])["direction"] == "bwd"

    def test_direction_none_without_point_raises(self):
        with pytest.raises(ValueError, match="requires point="):
            search_obliques(direction=None, season=SEASON)


class TestSpatialSearch:
    @respx.mock
    def test_point_search_filters_by_radius(self):
        _mock_listing_router()
        _mock_sidecars("Bwd")
        results = search_obliques(
            direction="bwd", season=SEASON, point=(-84.85, 38.20), radius_feet=500
        )
        assert [f.frame_id for f in results] == ["Bwd_0_1"]

    @respx.mock
    def test_point_search_all_directions(self):
        _mock_listing_router()
        for d in ("Bwd", "Fwd", "Left", "Right"):
            _mock_sidecars(d)
        results = search_obliques(
            direction=None, season=SEASON, point=(-84.85, 38.20), radius_feet=500
        )
        assert {f.direction for f in results} == {"bwd", "fwd", "left", "right"}
        assert all(f.frame_id.endswith("_0_1") for f in results)

    @respx.mock
    def test_nearest_first_ordering(self):
        _mock_listing_router()
        _mock_sidecars("Bwd")
        # Huge radius: both frames match; near frame must sort first
        results = search_obliques(
            direction="bwd", season=SEASON, point=(-84.85, 38.20), radius_feet=500_000
        )
        assert [f.frame_id for f in results] == ["Bwd_0_1", "Bwd_0_2"]

    @respx.mock
    def test_sidecar_fetch_cap_raises(self):
        _mock_listing_router()
        with pytest.raises(ValueError, match="max_sidecar_fetches"):
            search_obliques(
                direction="bwd",
                season=SEASON,
                point=(-84.85, 38.20),
                max_sidecar_fetches=1,
            )

    @respx.mock
    def test_camera_center_fallback_with_slack(self):
        _mock_listing_router()
        # Sidecars with only a camera center (no footprint)
        respx.get(f"{S3_BASE_URL}/{_PREFIX}/Bwd_0_1.json").mock(
            return_value=httpx.Response(
                200, json={"center": {"type": "Point", "coordinates": [-84.851, 38.201]}}
            )
        )
        respx.get(f"{S3_BASE_URL}/{_PREFIX}/Bwd_0_2.json").mock(
            return_value=httpx.Response(
                200, json={"center": {"type": "Point", "coordinates": [-84.35, 38.70]}}
            )
        )
        results = search_obliques(
            direction="bwd", season=SEASON, point=(-84.85, 38.20), radius_feet=100
        )
        # Center is ~450 ft away — outside radius but inside radius + slack
        assert [f.frame_id for f in results] == ["Bwd_0_1"]

    @respx.mock
    def test_frames_without_geometry_excluded(self):
        _mock_listing_router()
        respx.get(f"{S3_BASE_URL}/{_PREFIX}/Bwd_0_1.json").mock(
            return_value=httpx.Response(200, json={})
        )
        respx.get(f"{S3_BASE_URL}/{_PREFIX}/Bwd_0_2.json").mock(
            return_value=httpx.Response(200, json={})
        )
        results = search_obliques(
            direction="bwd", season=SEASON, point=(-84.85, 38.20), radius_feet=500
        )
        assert results == []


class TestObliqueBundle:
    @respx.mock
    def test_bundle_picks_best_per_direction(self):
        _mock_listing_router()
        for d in ("Bwd", "Fwd", "Left", "Right"):
            _mock_sidecars(d)
        bundle = oblique_bundle((-84.85, 38.20), season=SEASON)
        assert set(bundle) == {"bwd", "fwd", "left", "right"}
        for direction, frame in bundle.items():
            assert frame is not None
            assert frame.direction == direction
            assert frame.frame_id.endswith("_0_1")

    @respx.mock
    def test_bundle_missing_direction_is_none(self):
        def _list_route(request):
            prefix = request.url.params.get("prefix", "")
            if prefix.endswith("/Bwd_"):
                return httpx.Response(200, text=_frames_xml("Bwd"))
            return httpx.Response(200, text=_EMPTY_XML)

        respx.get(f"{S3_BASE_URL}/").mock(side_effect=_list_route)
        _mock_sidecars("Bwd")
        bundle = oblique_bundle((-84.85, 38.20), season=SEASON)
        assert bundle["bwd"] is not None
        assert bundle["fwd"] is None
        assert bundle["left"] is None
        assert bundle["right"] is None

"""Tests for ObliqueFrame and sidecar metadata fetching."""

from datetime import UTC, datetime

import httpx
import pytest
import respx

from abovepy.obliques import ObliqueFrame, clear_sidecar_cache, fetch_sidecar

SEASON = "KY_KYAPED_2023_Season1_3IN"
BASE = "https://kyfromabove.s3.us-west-2.amazonaws.com/imagery/obliques/Phase3"
JSON_URL = f"{BASE}/{SEASON}/Bwd_2025_401340.json"
TIF_URL = f"{BASE}/{SEASON}/Bwd_2025_401340.tif"

FULL_SIDECAR = {
    "frame_id": "Bwd_2025_401340",
    "datetime": "2023-04-12T15:30:00Z",
    "camera": {"focal_length_mm": 100.5, "omega": -0.1, "phi": 44.9, "kappa": 0.2},
    "footprint": {
        "type": "Polygon",
        "coordinates": [
            [[-84.9, 38.15], [-84.8, 38.15], [-84.8, 38.25], [-84.9, 38.25], [-84.9, 38.15]]
        ],
    },
    "center": {"type": "Point", "coordinates": [-84.85, 38.2]},
}


@pytest.fixture(autouse=True)
def _clear_cache():
    clear_sidecar_cache()
    yield
    clear_sidecar_cache()


@pytest.fixture
def frame():
    return ObliqueFrame(
        frame_id="Bwd_2025_401340",
        tif_url=TIF_URL,
        json_url=JSON_URL,
        season=SEASON,
        direction="bwd",
    )


# ---------------------------------------------------------------------------
# Mapping protocol (v2.1 dict compatibility)
# ---------------------------------------------------------------------------


class TestMappingProtocol:
    def test_subscript_access(self, frame):
        assert frame["frame_id"] == "Bwd_2025_401340"
        assert frame["tif_url"] == TIF_URL
        assert frame["json_url"] == JSON_URL
        assert frame["season"] == SEASON
        assert frame["direction"] == "bwd"

    def test_dict_conversion(self, frame):
        as_dict = dict(frame)
        assert as_dict == {
            "frame_id": "Bwd_2025_401340",
            "tif_url": TIF_URL,
            "json_url": JSON_URL,
            "season": SEASON,
            "direction": "bwd",
        }
        assert as_dict == frame.to_dict()

    def test_len_and_iteration(self, frame):
        assert len(frame) == 5
        assert list(frame) == ["frame_id", "tif_url", "json_url", "season", "direction"]

    def test_get_method(self, frame):
        assert frame.get("direction") == "bwd"
        assert frame.get("missing") is None
        assert frame.get("missing", "fallback") == "fallback"

    def test_unknown_key_raises(self, frame):
        with pytest.raises(KeyError):
            _ = frame["metadata"]

    def test_membership(self, frame):
        assert "tif_url" in frame
        assert "camera" not in frame


# ---------------------------------------------------------------------------
# Sidecar property parsing
# ---------------------------------------------------------------------------


class TestSidecarProperties:
    def test_no_metadata_all_none(self, frame):
        assert frame.raw is None
        assert frame.camera is None
        assert frame.footprint is None
        assert frame.timestamp is None
        assert frame.camera_position is None

    def test_full_sidecar(self, frame):
        frame.metadata = dict(FULL_SIDECAR)
        assert frame.raw == FULL_SIDECAR
        assert frame.camera == FULL_SIDECAR["camera"]
        assert frame.timestamp == datetime(2023, 4, 12, 15, 30, tzinfo=UTC)
        assert frame.camera_position == (-84.85, 38.2)
        footprint = frame.footprint
        assert footprint is not None
        assert footprint.bounds == (-84.9, 38.15, -84.8, 38.25)

    def test_partial_sidecar_missing_camera(self, frame):
        frame.metadata = {"datetime": "2023-04-12T15:30:00Z"}
        assert frame.camera is None
        assert frame.footprint is None
        assert frame.timestamp is not None

    def test_alternate_key_names(self, frame):
        frame.metadata = {
            "exterior_orientation": {"omega": 1.0},
            "geometry": FULL_SIDECAR["footprint"],
            "acquisition_date": "2024-01-15",
        }
        assert frame.camera == {"omega": 1.0}
        assert frame.footprint is not None
        assert frame.timestamp == datetime(2024, 1, 15)

    def test_footprint_from_bounds_list(self, frame):
        frame.metadata = {"bounds": [-84.9, 38.15, -84.8, 38.25]}
        footprint = frame.footprint
        assert footprint is not None
        assert footprint.bounds == (-84.9, 38.15, -84.8, 38.25)

    def test_footprint_from_coordinate_list(self, frame):
        frame.metadata = {"footprint": [[-84.9, 38.15], [-84.8, 38.15], [-84.85, 38.25]]}
        assert frame.footprint is not None

    def test_footprint_from_wkt(self, frame):
        wkt = "POLYGON ((-84.9 38.15, -84.8 38.15, -84.85 38.25, -84.9 38.15))"
        frame.metadata = {"geometry": wkt}
        assert frame.footprint is not None

    def test_malformed_values_return_none(self, frame):
        frame.metadata = {
            "camera": "not-a-dict",
            "footprint": {"type": "Polygon"},  # missing coordinates
            "datetime": "not-a-date",
            "bounds": [1, 2, 3],  # wrong length
        }
        assert frame.camera is None
        assert frame.footprint is None
        assert frame.timestamp is None
        assert frame.raw is not None  # raw payload always preserved

    def test_epoch_timestamp(self, frame):
        frame.metadata = {"timestamp": 1_681_313_400}
        ts = frame.timestamp
        assert ts is not None
        assert ts.year == 2023

    def test_camera_position_from_lon_lat_keys(self, frame):
        frame.metadata = {"camera": {"longitude": -84.87, "latitude": 38.19}}
        assert frame.camera_position == (-84.87, 38.19)


# ---------------------------------------------------------------------------
# fetch_sidecar
# ---------------------------------------------------------------------------


class TestFetchSidecar:
    @respx.mock
    def test_fetch_success(self, frame):
        respx.get(JSON_URL).mock(return_value=httpx.Response(200, json=FULL_SIDECAR))
        payload = fetch_sidecar(JSON_URL)
        assert payload == FULL_SIDECAR

    @respx.mock
    def test_fetch_metadata_populates_frame(self, frame):
        respx.get(JSON_URL).mock(return_value=httpx.Response(200, json=FULL_SIDECAR))
        result = frame.fetch_metadata()
        assert result == FULL_SIDECAR
        assert frame.metadata == FULL_SIDECAR
        assert frame.footprint is not None

    @respx.mock
    def test_cache_prevents_refetch(self):
        route = respx.get(JSON_URL).mock(return_value=httpx.Response(200, json=FULL_SIDECAR))
        fetch_sidecar(JSON_URL)
        fetch_sidecar(JSON_URL)
        assert route.call_count == 1

    @respx.mock
    def test_force_refetch(self, frame):
        route = respx.get(JSON_URL).mock(return_value=httpx.Response(200, json=FULL_SIDECAR))
        frame.fetch_metadata()
        frame.fetch_metadata(force=True)
        assert route.call_count == 2

    @respx.mock
    def test_attached_metadata_not_refetched(self, frame):
        route = respx.get(JSON_URL).mock(return_value=httpx.Response(200, json=FULL_SIDECAR))
        frame.fetch_metadata()
        frame.fetch_metadata()  # second call served from frame.metadata
        assert route.call_count == 1

    @respx.mock
    def test_malformed_json_returns_empty(self):
        respx.get(JSON_URL).mock(return_value=httpx.Response(200, text="{not json"))
        assert fetch_sidecar(JSON_URL) == {}

    @respx.mock
    def test_non_object_json_returns_empty(self):
        respx.get(JSON_URL).mock(return_value=httpx.Response(200, json=[1, 2, 3]))
        assert fetch_sidecar(JSON_URL) == {}

    @respx.mock
    def test_http_error_raises(self):
        respx.get(JSON_URL).mock(return_value=httpx.Response(404))
        with pytest.raises(httpx.HTTPStatusError):
            fetch_sidecar(JSON_URL)

    def test_untrusted_host_rejected(self):
        with pytest.raises(ValueError, match="not a known KyFromAbove endpoint"):
            fetch_sidecar("https://evil.example.com/frame.json")

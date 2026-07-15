"""Tests for the high-level analysis APIs (sample, profile, zonal_stats,
change_detection). All searches and remote reads are mocked."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from rasterio.transform import from_bounds
from shapely.geometry import LineString, box

from abovepy._exceptions import AnalysisError
from abovepy.analysis import (
    MAX_ANALYSIS_TILES,
    change_detection,
    profile,
    sample,
    zonal_stats,
)

# A 20x20 DEM over Frankfort in EPSG:4326: elevation = 800 + row index.
# Pixel size 0.005 deg; point (-84.85, 38.20) lands on row 10, col 10 → 810.
BOUNDS = (-84.9, 38.15, -84.8, 38.25)
NODATA = -9999.0


def _dem_profile(width=20, height=20, bounds=BOUNDS):
    return {
        "driver": "GTiff",
        "dtype": "float32",
        "width": width,
        "height": height,
        "count": 1,
        "crs": "EPSG:4326",
        "transform": from_bounds(*bounds, width, height),
        "nodata": NODATA,
    }


@pytest.fixture
def ramp_dem():
    dem = 800.0 + np.arange(20, dtype=np.float64).reshape(-1, 1) * np.ones((1, 20))
    return dem, _dem_profile()


@pytest.fixture
def search_result():
    result = MagicMock()
    result.empty = False
    result.count = 1
    return result


# ---------------------------------------------------------------------------
# sample
# ---------------------------------------------------------------------------


class TestSample:
    def test_single_point(self, ramp_dem, search_result):
        with (
            patch("abovepy.search", return_value=search_result),
            patch("abovepy.analysis._read_aoi", return_value=ramp_dem),
        ):
            elev = sample((-84.85, 38.20))
        assert elev == pytest.approx(810.0)

    def test_multiple_points(self, ramp_dem, search_result):
        with (
            patch("abovepy.search", return_value=search_result),
            patch("abovepy.analysis._read_aoi", return_value=ramp_dem),
        ):
            values = sample([(-84.85, 38.20), (-84.85, 38.155)])
        assert isinstance(values, list)
        assert values[0] == pytest.approx(810.0)
        assert values[1] == pytest.approx(819.0)  # bottom row

    def test_nodata_returns_nan(self, ramp_dem, search_result):
        dem, dem_profile = ramp_dem
        dem = dem.copy()
        dem[10, 10] = NODATA
        with (
            patch("abovepy.search", return_value=search_result),
            patch("abovepy.analysis._read_aoi", return_value=(dem, dem_profile)),
        ):
            elev = sample((-84.85, 38.20))
        assert np.isnan(elev)

    def test_point_outside_window_returns_nan(self, ramp_dem, search_result):
        with (
            patch("abovepy.search", return_value=search_result),
            patch("abovepy.analysis._read_aoi", return_value=ramp_dem),
        ):
            elev = sample((-80.0, 36.0))
        assert np.isnan(elev)

    def test_empty_search_raises(self):
        result = MagicMock()
        result.empty = True
        with (
            patch("abovepy.search", return_value=result),
            pytest.raises(AnalysisError, match="No dem_phase3 tiles"),
        ):
            sample((-84.85, 38.20))

    def test_too_many_tiles_raises(self):
        result = MagicMock()
        result.empty = False
        result.count = MAX_ANALYSIS_TILES + 1
        with (
            patch("abovepy.search", return_value=result),
            pytest.raises(AnalysisError, match="Download and"),
        ):
            sample((-84.85, 38.20))

    def test_no_points_raises(self):
        with pytest.raises(AnalysisError, match="No points"):
            sample([])


# ---------------------------------------------------------------------------
# profile
# ---------------------------------------------------------------------------


class TestProfile:
    def _run(self, line, ramp_dem, search_result, n_points=50):
        with (
            patch("abovepy.search", return_value=search_result),
            patch("abovepy.analysis._read_aoi", return_value=ramp_dem),
        ):
            return profile(line, n_points=n_points)

    def test_dataframe_shape_and_columns(self, ramp_dem, search_result):
        df = self._run([(-84.85, 38.16), (-84.85, 38.24)], ramp_dem, search_result)
        assert list(df.columns) == ["distance_ft", "elevation", "lon", "lat"]
        assert len(df) == 50

    def test_distances_monotonic_and_in_feet(self, ramp_dem, search_result):
        df = self._run([(-84.85, 38.16), (-84.85, 38.24)], ramp_dem, search_result)
        assert df["distance_ft"].iloc[0] == 0.0
        assert (df["distance_ft"].diff().dropna() > 0).all()
        # 0.08 degrees of latitude ≈ 29,000 ft — sanity-check the units
        assert 20_000 < df["distance_ft"].iloc[-1] < 40_000

    def test_elevations_follow_ramp(self, ramp_dem, search_result):
        df = self._run([(-84.85, 38.16), (-84.85, 38.24)], ramp_dem, search_result)
        assert df["elevation"].notna().all()
        # Northward line: row index (and thus elevation) decreases
        assert df["elevation"].iloc[0] > df["elevation"].iloc[-1]

    def test_accepts_linestring(self, ramp_dem, search_result):
        line = LineString([(-84.85, 38.16), (-84.85, 38.24)])
        df = self._run(line, ramp_dem, search_result)
        assert len(df) == 50

    def test_n_points_too_small_raises(self):
        with pytest.raises(AnalysisError, match="n_points"):
            profile([(-84.85, 38.16), (-84.85, 38.24)], n_points=1)

    def test_empty_search_raises(self):
        result = MagicMock()
        result.empty = True
        with (
            patch("abovepy.search", return_value=result),
            pytest.raises(AnalysisError, match="transect"),
        ):
            profile([(-84.85, 38.16), (-84.85, 38.24)])


# ---------------------------------------------------------------------------
# zonal_stats
# ---------------------------------------------------------------------------


class TestZonalStats:
    def test_stats_keys_and_ranges(self, ramp_dem, search_result):
        polygon = box(-84.88, 38.16, -84.82, 38.24)
        with (
            patch("abovepy.search", return_value=search_result),
            patch("abovepy.analysis._read_aoi", return_value=ramp_dem),
        ):
            stats = zonal_stats(polygon)
        for key in ("min", "max", "mean", "median", "std", "area", "cell_count"):
            assert key in stats
        assert 800.0 <= stats["min"] <= stats["mean"] <= stats["max"] <= 820.0
        assert stats["cell_count"] > 0

    def test_nodata_excluded(self, ramp_dem, search_result):
        dem, dem_profile = ramp_dem
        dem = dem.copy()
        dem[:10, :] = NODATA  # top half nodata
        polygon = box(-84.88, 38.16, -84.82, 38.24)
        with (
            patch("abovepy.search", return_value=search_result),
            patch("abovepy.analysis._read_aoi", return_value=(dem, dem_profile)),
        ):
            stats = zonal_stats(polygon)
        # Only the bottom (high-row-index) half contributes
        assert stats["min"] >= 810.0

    def test_all_nodata_raises(self, ramp_dem, search_result):
        dem, dem_profile = ramp_dem
        dem = np.full_like(dem, NODATA)
        polygon = box(-84.88, 38.16, -84.82, 38.24)
        with (
            patch("abovepy.search", return_value=search_result),
            patch("abovepy.analysis._read_aoi", return_value=(dem, dem_profile)),
            pytest.raises(AnalysisError, match="no valid DEM cells"),
        ):
            zonal_stats(polygon)

    def test_empty_search_raises(self):
        result = MagicMock()
        result.empty = True
        with (
            patch("abovepy.search", return_value=result),
            pytest.raises(AnalysisError, match="polygon"),
        ):
            zonal_stats(box(-84.88, 38.16, -84.82, 38.24))


# ---------------------------------------------------------------------------
# change_detection
# ---------------------------------------------------------------------------


class TestChangeDetection:
    def test_aligned_grids(self, ramp_dem, search_result):
        dem_before, dem_profile = ramp_dem
        dem_after = dem_before + 5.0
        with (
            patch("abovepy.search", return_value=search_result),
            patch(
                "abovepy.analysis._read_aoi",
                side_effect=[(dem_before, dem_profile), (dem_after, dict(dem_profile))],
            ),
        ):
            diff, out_profile = change_detection(BOUNDS)
        assert diff.shape == dem_before.shape
        assert np.nanmean(diff) == pytest.approx(5.0)
        assert out_profile["count"] == 1

    def test_mismatched_grids_resampled(self, ramp_dem, search_result):
        dem_before, dem_profile = ramp_dem
        # After epoch on a coarser 10x10 grid over the same bounds
        dem_after = 805.0 + np.arange(10, dtype=np.float64).reshape(-1, 1) * 2 * np.ones((1, 10))
        after_profile = _dem_profile(width=10, height=10)
        with (
            patch("abovepy.search", return_value=search_result),
            patch(
                "abovepy.analysis._read_aoi",
                side_effect=[(dem_before, dem_profile), (dem_after, after_profile)],
            ),
        ):
            diff, _ = change_detection(BOUNDS)
        assert diff.shape == dem_before.shape
        # Smooth ramps: interior difference stays close to +5
        interior = diff[2:-2, 2:-2]
        assert np.nanmean(interior) == pytest.approx(5.0, abs=1.0)

    def test_output_written(self, ramp_dem, search_result, tmp_path):
        dem_before, dem_profile = ramp_dem
        dem_after = dem_before + 5.0
        output = tmp_path / "diff.tif"
        with (
            patch("abovepy.search", return_value=search_result),
            patch(
                "abovepy.analysis._read_aoi",
                side_effect=[(dem_before, dem_profile), (dem_after, dict(dem_profile))],
            ),
        ):
            change_detection(BOUNDS, output=output)
        assert output.exists()

    def test_empty_before_search_raises(self):
        result = MagicMock()
        result.empty = True
        with (
            patch("abovepy.search", return_value=result),
            pytest.raises(AnalysisError, match="dem_phase2"),
        ):
            change_detection(BOUNDS)

    def test_nodata_propagates_as_nan(self, ramp_dem, search_result):
        dem_before, dem_profile = ramp_dem
        dem_before = dem_before.copy()
        dem_before[0, 0] = NODATA
        dem_after = 800.0 + np.arange(20, dtype=np.float64).reshape(-1, 1) * np.ones((1, 20)) + 5.0
        with (
            patch("abovepy.search", return_value=search_result),
            patch(
                "abovepy.analysis._read_aoi",
                side_effect=[(dem_before, dem_profile), (dem_after, dict(dem_profile))],
            ),
        ):
            diff, _ = change_detection(BOUNDS)
        assert np.isnan(diff[0, 0])

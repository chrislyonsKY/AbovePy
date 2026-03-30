"""Tests for terrain analysis functions."""

import numpy as np
import pytest

from abovepy._exceptions import AnalysisError
from abovepy.terrain import (
    aspect,
    dem_diff,
    elevation_profile,
    flood_depth,
    flood_inundation,
    hillshade,
    slope,
    volume,
    volume_from_surface,
    zonal_stats,
)


@pytest.fixture
def flat_dem():
    """A flat DEM at elevation 100."""
    return np.full((50, 50), 100.0)


@pytest.fixture
def sloped_dem():
    """A DEM sloping from west (0) to east (100)."""
    return np.tile(np.linspace(0, 100, 50), (50, 1))


@pytest.fixture
def valley_dem():
    """A V-shaped valley DEM — low in center, high on edges."""
    row = np.abs(np.linspace(-50, 50, 100))
    return np.tile(row, (100, 1))


# ---------------------------------------------------------------------------
# hillshade
# ---------------------------------------------------------------------------


class TestHillshade:
    def test_returns_uint8(self, sloped_dem):
        result = hillshade(sloped_dem, resolution=1.0)
        assert result.dtype == np.uint8

    def test_shape_preserved(self, sloped_dem):
        result = hillshade(sloped_dem, resolution=1.0)
        assert result.shape == sloped_dem.shape

    def test_values_in_range(self, sloped_dem):
        result = hillshade(sloped_dem, resolution=1.0)
        assert result.min() >= 0
        assert result.max() <= 255

    def test_flat_dem_uniform(self, flat_dem):
        result = hillshade(flat_dem, resolution=1.0)
        # Flat surface should have uniform illumination
        assert np.unique(result).size <= 2  # Edge effects may create 2 values

    def test_rejects_3d_array(self):
        with pytest.raises(AnalysisError, match="2D"):
            hillshade(np.zeros((3, 3, 3)), resolution=1.0)


# ---------------------------------------------------------------------------
# slope
# ---------------------------------------------------------------------------


class TestSlope:
    def test_flat_dem_zero_slope(self, flat_dem):
        result = slope(flat_dem, resolution=1.0)
        # Interior should be zero (edges may have artifacts)
        interior = result[2:-2, 2:-2]
        assert np.allclose(interior, 0.0)

    def test_degrees_range(self, sloped_dem):
        result = slope(sloped_dem, resolution=1.0, units="degrees")
        assert result.min() >= 0
        assert result.max() <= 90

    def test_percent_range(self, sloped_dem):
        result = slope(sloped_dem, resolution=1.0, units="percent")
        assert result.min() >= 0

    def test_invalid_units(self, flat_dem):
        with pytest.raises(AnalysisError, match="Invalid units"):
            slope(flat_dem, resolution=1.0, units="radians")

    def test_rejects_3d_array(self):
        with pytest.raises(AnalysisError, match="2D"):
            slope(np.zeros((3, 3, 3)), resolution=1.0)


# ---------------------------------------------------------------------------
# aspect
# ---------------------------------------------------------------------------


class TestAspect:
    def test_flat_returns_negative_one(self, flat_dem):
        result = aspect(flat_dem, resolution=1.0)
        interior = result[2:-2, 2:-2]
        assert np.all(interior == -1)

    def test_values_in_range(self, sloped_dem):
        result = aspect(sloped_dem, resolution=1.0)
        valid = result[result >= 0]
        assert valid.min() >= 0
        assert valid.max() < 360

    def test_rejects_3d_array(self):
        with pytest.raises(AnalysisError, match="2D"):
            aspect(np.zeros((3, 3, 3)), resolution=1.0)


# ---------------------------------------------------------------------------
# flood_inundation
# ---------------------------------------------------------------------------


class TestFloodInundation:
    def test_all_flooded(self, flat_dem):
        result = flood_inundation(flat_dem, water_level=200.0)
        assert result.all()

    def test_none_flooded(self, flat_dem):
        result = flood_inundation(flat_dem, water_level=50.0)
        assert not result.any()

    def test_partial_flood(self, sloped_dem):
        result = flood_inundation(sloped_dem, water_level=50.0)
        assert result.any()
        assert not result.all()

    def test_nodata_excluded(self):
        dem = np.array([[10, 20, -9999], [30, 40, 50]])
        result = flood_inundation(dem, water_level=100.0, nodata=-9999)
        assert not result[0, 2]  # nodata cell not flooded
        assert result[0, 0]  # regular cell is flooded


# ---------------------------------------------------------------------------
# flood_depth
# ---------------------------------------------------------------------------


class TestFloodDepth:
    def test_depth_calculation(self):
        dem = np.array([[10, 20], [30, 40]], dtype=float)
        result = flood_depth(dem, water_level=25.0)
        np.testing.assert_allclose(result, [[15.0, 5.0], [0.0, 0.0]])

    def test_nodata_becomes_nan(self):
        dem = np.array([[10, -9999]], dtype=float)
        result = flood_depth(dem, water_level=100.0, nodata=-9999)
        assert np.isnan(result[0, 1])
        assert result[0, 0] == 90.0


# ---------------------------------------------------------------------------
# dem_diff
# ---------------------------------------------------------------------------


class TestDemDiff:
    def test_no_change(self, flat_dem):
        result = dem_diff(flat_dem, flat_dem)
        assert np.allclose(result, 0.0)

    def test_positive_fill(self):
        before = np.full((5, 5), 10.0)
        after = np.full((5, 5), 15.0)
        result = dem_diff(before, after)
        assert np.allclose(result, 5.0)

    def test_negative_cut(self):
        before = np.full((5, 5), 15.0)
        after = np.full((5, 5), 10.0)
        result = dem_diff(before, after)
        assert np.allclose(result, -5.0)

    def test_shape_mismatch(self):
        with pytest.raises(AnalysisError, match="Shape mismatch"):
            dem_diff(np.zeros((3, 3)), np.zeros((4, 4)))


# ---------------------------------------------------------------------------
# elevation_profile
# ---------------------------------------------------------------------------


class TestElevationProfile:
    def test_horizontal_transect(self, sloped_dem):
        dists, elevs = elevation_profile(
            sloped_dem,
            start=(25, 0),
            end=(25, 49),
            resolution=1.0,
        )
        assert len(dists) == len(elevs)
        # Elevation should increase along the transect
        assert elevs[-1] > elevs[0]

    def test_distances_start_at_zero(self, sloped_dem):
        dists, _ = elevation_profile(
            sloped_dem,
            start=(0, 0),
            end=(49, 49),
            resolution=5.0,
        )
        assert dists[0] == 0.0
        assert dists[-1] > 0.0

    def test_custom_num_points(self, sloped_dem):
        dists, elevs = elevation_profile(
            sloped_dem,
            start=(0, 0),
            end=(49, 49),
            resolution=1.0,
            num_points=10,
        )
        assert len(dists) == 10
        assert len(elevs) == 10


# ---------------------------------------------------------------------------
# zonal_stats
# ---------------------------------------------------------------------------


class TestZonalStats:
    def test_full_mask(self, flat_dem):
        mask = np.ones_like(flat_dem, dtype=bool)
        stats = zonal_stats(flat_dem, mask, resolution=5.0)
        assert stats["min"] == 100.0
        assert stats["max"] == 100.0
        assert stats["mean"] == 100.0
        assert stats["cell_count"] == 2500
        assert stats["area"] == 2500 * 25.0  # 2500 cells * 5^2

    def test_partial_mask(self, sloped_dem):
        mask = np.zeros_like(sloped_dem, dtype=bool)
        mask[20:30, 20:30] = True
        stats = zonal_stats(sloped_dem, mask, resolution=1.0)
        assert stats["cell_count"] == 100
        assert stats["min"] < stats["max"]

    def test_empty_mask_raises(self, flat_dem):
        mask = np.zeros_like(flat_dem, dtype=bool)
        with pytest.raises(AnalysisError, match="No cells"):
            zonal_stats(flat_dem, mask, resolution=1.0)


# ---------------------------------------------------------------------------
# volume
# ---------------------------------------------------------------------------


class TestVolume:
    def test_flat_at_reference(self, flat_dem):
        result = volume(flat_dem, reference_elevation=100.0, resolution=1.0)
        assert result["cut_volume"] == 0.0
        assert result["fill_volume"] == 0.0
        assert result["net_volume"] == 0.0

    def test_all_above_reference(self, flat_dem):
        result = volume(flat_dem, reference_elevation=90.0, resolution=1.0)
        assert result["fill_volume"] > 0
        assert result["cut_volume"] == 0.0

    def test_all_below_reference(self, flat_dem):
        result = volume(flat_dem, reference_elevation=110.0, resolution=1.0)
        assert result["cut_volume"] > 0
        assert result["fill_volume"] == 0.0

    def test_with_mask(self, flat_dem):
        mask = np.zeros_like(flat_dem, dtype=bool)
        mask[0:10, 0:10] = True  # 100 cells
        result = volume(flat_dem, reference_elevation=90.0, mask=mask, resolution=2.0)
        # 100 cells * 10ft diff * 4 sq units = 4000
        assert result["fill_volume"] == pytest.approx(4000.0)


# ---------------------------------------------------------------------------
# volume_from_surface
# ---------------------------------------------------------------------------


class TestVolumeFromSurface:
    def test_identical_surfaces(self, flat_dem):
        result = volume_from_surface(flat_dem, flat_dem, resolution=1.0)
        assert result["net_volume"] == 0.0

    def test_shape_mismatch(self):
        with pytest.raises(AnalysisError, match="Shape mismatch"):
            volume_from_surface(np.zeros((3, 3)), np.zeros((4, 4)))

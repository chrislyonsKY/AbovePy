"""Tests for EPSG:3089 geometry utilities in utils/crs.py."""

from __future__ import annotations

from shapely.geometry import LineString, Point

from abovepy.utils.crs import (
    buffer_feet,
    corridor_buffer,
    reproject_bbox,
    validate_crs_units,
)


class TestBufferFeet:
    def test_point_buffer_returns_polygon(self):
        pt = Point(-84.85, 38.19)
        result = buffer_feet(pt, 500.0)
        assert result.geom_type in ("Polygon", "MultiPolygon")
        assert not result.is_empty

    def test_buffer_size_is_reasonable(self):
        """500 feet buffer around a point should be roughly 500ft radius."""
        pt = Point(-84.85, 38.19)
        result = buffer_feet(pt, 500.0)
        # Result is in EPSG:4326 — 500ft is ~0.0014 degrees at KY latitude
        bounds = result.bounds
        width_deg = bounds[2] - bounds[0]
        assert 0.002 < width_deg < 0.005  # reasonable range

    def test_zero_buffer(self):
        pt = Point(-84.85, 38.19)
        result = buffer_feet(pt, 0.0)
        assert result.is_empty or result.area < 1e-12


class TestCorridorBuffer:
    def test_line_corridor(self):
        line = LineString([(-84.9, 38.2), (-84.8, 38.2)])
        result = corridor_buffer(line, 200.0)
        assert result.geom_type in ("Polygon", "MultiPolygon")
        assert not result.is_empty

    def test_corridor_contains_centerline(self):
        line = LineString([(-84.9, 38.2), (-84.8, 38.2)])
        result = corridor_buffer(line, 500.0)
        # Midpoint of line should be inside corridor
        midpoint = Point(-84.85, 38.2)
        assert result.contains(midpoint)


class TestReprojectBbox:
    def test_4326_to_3089(self):
        bbox = (-84.85, 38.19, -84.80, 38.22)
        result = reproject_bbox(bbox, "EPSG:4326", "EPSG:3089")
        # EPSG:3089 coordinates are in feet, should be large numbers
        assert result[0] > 1_000_000  # x in feet
        assert result[1] > 1_000_000  # y in feet

    def test_roundtrip(self):
        bbox = (-84.85, 38.19, -84.80, 38.22)
        to_3089 = reproject_bbox(bbox, "EPSG:4326", "EPSG:3089")
        back = reproject_bbox(to_3089, "EPSG:3089", "EPSG:4326")
        assert abs(back[0] - bbox[0]) < 0.001
        assert abs(back[1] - bbox[1]) < 0.001


class TestValidateCrsUnits:
    def test_3089_is_feet(self):
        assert validate_crs_units("EPSG:3089", "feet") is True

    def test_4326_is_not_feet(self):
        assert validate_crs_units("EPSG:4326", "feet") is False

    def test_4326_is_degrees(self):
        assert validate_crs_units("EPSG:4326", "degree") is True

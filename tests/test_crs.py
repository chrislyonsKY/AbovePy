"""Tests for CRS conversion utilities."""

from abovepy.utils.crs import bbox_intersects_kentucky, transform_bbox


def test_transform_bbox_4326_to_3089():
    """Test reprojection from WGS84 to Kentucky Single Zone."""
    bbox_4326 = (-84.9, 38.15, -84.8, 38.25)
    bbox_3089 = transform_bbox(bbox_4326, "EPSG:4326", "EPSG:3089")

    # EPSG:3089 coords should be much larger (US feet)
    assert all(abs(v) > 1000 for v in bbox_3089)
    assert bbox_3089[0] < bbox_3089[2]  # xmin < xmax
    assert bbox_3089[1] < bbox_3089[3]  # ymin < ymax


def test_transform_bbox_roundtrip():
    """Test 4326 -> 3089 -> 4326 roundtrip preserves values."""
    original = (-84.9, 38.15, -84.8, 38.25)
    intermediate = transform_bbox(original, "EPSG:4326", "EPSG:3089")
    result = transform_bbox(intermediate, "EPSG:3089", "EPSG:4326")

    for orig, res in zip(original, result, strict=True):
        assert abs(orig - res) < 0.001


def test_transform_bbox_identity():
    """Same CRS -> same coords."""
    bbox = (-84.9, 38.15, -84.8, 38.25)
    result = transform_bbox(bbox, "EPSG:4326", "EPSG:4326")
    for orig, res in zip(bbox, result, strict=True):
        assert abs(orig - res) < 1e-8


def test_bbox_intersects_kentucky_inside():
    """Frankfort area should intersect Kentucky."""
    assert bbox_intersects_kentucky((-84.9, 38.15, -84.8, 38.25))


def test_bbox_intersects_kentucky_outside():
    """New York City should not intersect Kentucky."""
    assert not bbox_intersects_kentucky((-74.1, 40.6, -73.9, 40.8))


def test_bbox_intersects_kentucky_partial():
    """Bbox straddling KY border should still intersect."""
    assert bbox_intersects_kentucky((-85.0, 36.4, -84.5, 36.6))


def test_bbox_intersects_kentucky_whole_us():
    """Continental US bbox should intersect Kentucky."""
    assert bbox_intersects_kentucky((-125.0, 24.0, -66.0, 50.0))

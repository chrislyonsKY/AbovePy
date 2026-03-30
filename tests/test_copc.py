"""Tests for abovepy.io.pointcloud.read_copc."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_header():
    """Build a mock LAS header with plausible attributes."""
    header = MagicMock()
    header.point_format.id = 7
    header.scales = (0.001, 0.001, 0.001)
    header.offsets = (0.0, 0.0, 0.0)
    header.x_min = 0.0
    header.y_min = 0.0
    header.z_min = 0.0
    header.x_max = 100.0
    header.y_max = 100.0
    header.z_max = 50.0
    header.parse_crs = MagicMock(side_effect=AttributeError)
    return header


def _make_mock_points(n: int = 100, classifications: np.ndarray | None = None):
    """Return a mock point record of *n* points."""
    points = MagicMock()
    points.__len__ = lambda self: n
    if classifications is None:
        classifications = np.ones(n, dtype=np.uint8)
    points.classification = classifications

    # Support boolean-mask indexing: points[mask]
    def _getitem(self_mock, mask):
        if isinstance(mask, np.ndarray):
            subset = _make_mock_points(int(mask.sum()), classifications[mask])
            return subset
        return self_mock

    points.__getitem__ = _getitem
    return points


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestReadCopcBasic:
    """Test basic read_copc with a mocked CopcReader."""

    @patch("laspy.CopcReader")
    def test_basic_read(self, mock_copc_cls):
        """read_copc returns points and metadata for a local file."""
        from abovepy.io.pointcloud import read_copc

        reader = MagicMock()
        header = _make_mock_header()
        reader.header = header
        points = _make_mock_points(50)
        reader.query.return_value = points
        mock_copc_cls.open.return_value = reader

        result_pts, meta = read_copc("/data/test.copc.laz")

        mock_copc_cls.open.assert_called_once_with("/data/test.copc.laz")
        reader.query.assert_called_once_with()
        assert meta["path"] == "/data/test.copc.laz"
        assert meta["point_count"] == 50
        assert meta["point_format"] == 7
        reader.close.assert_called_once()


class TestS3UriConversion:
    """Test that S3 URIs are converted to HTTPS URLs."""

    @patch("laspy.CopcReader")
    def test_s3_uri_to_https(self, mock_copc_cls):
        from abovepy.io.pointcloud import read_copc

        reader = MagicMock()
        reader.header = _make_mock_header()
        reader.query.return_value = _make_mock_points(10)
        mock_copc_cls.open.return_value = reader

        read_copc("s3://my-bucket/path/to/file.copc.laz")

        mock_copc_cls.open.assert_called_once_with(
            "https://my-bucket.s3.amazonaws.com/path/to/file.copc.laz"
        )
        reader.close.assert_called_once()


class TestBboxBoundsConstruction:
    """Test that bbox/z_range are correctly converted to Bounds."""

    @patch("laspy.copc.Bounds")
    @patch("laspy.CopcReader")
    def test_bbox_without_z_range(self, mock_copc_cls, mock_bounds_cls):
        from abovepy.io.pointcloud import read_copc

        reader = MagicMock()
        reader.header = _make_mock_header()
        reader.query.return_value = _make_mock_points(5)
        mock_copc_cls.open.return_value = reader

        bounds_instance = MagicMock()
        mock_bounds_cls.return_value = bounds_instance

        read_copc("/data/test.copc.laz", bbox=(10, 20, 30, 40))

        # Bounds should have been constructed with z = ±inf
        call_kwargs = mock_bounds_cls.call_args
        mins = call_kwargs.kwargs["mins"]
        maxs = call_kwargs.kwargs["maxs"]
        np.testing.assert_array_equal(mins[:2], [10, 20])
        np.testing.assert_array_equal(maxs[:2], [30, 40])
        assert mins[2] == -np.inf
        assert maxs[2] == np.inf
        reader.query.assert_called_once_with(bounds=bounds_instance)
        reader.close.assert_called_once()

    @patch("laspy.copc.Bounds")
    @patch("laspy.CopcReader")
    def test_bbox_with_z_range(self, mock_copc_cls, mock_bounds_cls):
        from abovepy.io.pointcloud import read_copc

        reader = MagicMock()
        reader.header = _make_mock_header()
        reader.query.return_value = _make_mock_points(5)
        mock_copc_cls.open.return_value = reader

        bounds_instance = MagicMock()
        mock_bounds_cls.return_value = bounds_instance

        read_copc(
            "/data/test.copc.laz",
            bbox=(10, 20, 30, 40),
            z_range=(5.0, 15.0),
        )

        call_kwargs = mock_bounds_cls.call_args
        mins = call_kwargs.kwargs["mins"]
        maxs = call_kwargs.kwargs["maxs"]
        np.testing.assert_array_equal(mins, [10, 20, 5.0])
        np.testing.assert_array_equal(maxs, [30, 40, 15.0])
        reader.close.assert_called_once()


class TestClassificationFilter:
    """Test that classification filtering is applied post-query."""

    @patch("laspy.CopcReader")
    def test_filter_by_classification(self, mock_copc_cls):
        from abovepy.io.pointcloud import read_copc

        reader = MagicMock()
        reader.header = _make_mock_header()

        # 10 points: classifications [1,2,1,2,1,2,1,2,1,2]
        cls_arr = np.array([1, 2, 1, 2, 1, 2, 1, 2, 1, 2], dtype=np.uint8)
        points = _make_mock_points(10, cls_arr)
        reader.query.return_value = points
        mock_copc_cls.open.return_value = reader

        result_pts, meta = read_copc(
            "/data/test.copc.laz", classifications=[2]
        )

        # Only class-2 points kept → 5 points
        assert meta["point_count"] == 5
        reader.close.assert_called_once()


class TestLazFallback:
    """Test fallback to read_pointcloud when the file is not COPC."""

    @patch("abovepy.io.pointcloud.read_pointcloud")
    @patch("laspy.CopcReader")
    def test_fallback_logs_warning(self, mock_copc_cls, mock_rpc, caplog):
        from abovepy.io.pointcloud import read_copc

        mock_copc_cls.open.side_effect = RuntimeError("Not a COPC file")

        mock_rpc.return_value = (MagicMock(), {"point_count": 42})

        with caplog.at_level(logging.WARNING):
            pts, meta = read_copc("/data/test.laz")

        assert "falling back to read_pointcloud" in caplog.text.lower()
        mock_rpc.assert_called_once_with(
            "/data/test.laz", bbox=None, classifications=None
        )
        reader.close.assert_not_called() if False else None  # noqa: no reader

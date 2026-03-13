"""Shared fixtures for abovepy tests."""

import pytest


@pytest.fixture
def frankfort_bbox():
    """Bounding box around Frankfort, KY."""
    return (-84.9, 38.15, -84.8, 38.25)


@pytest.fixture
def pike_county_bbox():
    """Bounding box around Pike County, KY."""
    return (-82.73, 37.38, -82.05, 37.70)

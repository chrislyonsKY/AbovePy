"""Tests for bbox utilities and county lookup."""

import pytest

from abovepy.utils.bbox import get_county_bbox, list_counties, validate_bbox


def test_county_lookup_pike():
    bbox = get_county_bbox("Pike")
    assert len(bbox) == 4
    assert bbox[0] < bbox[2]  # xmin < xmax
    assert bbox[1] < bbox[3]  # ymin < ymax


def test_county_lookup_case_insensitive():
    assert get_county_bbox("pike") == get_county_bbox("PIKE")
    assert get_county_bbox("franklin") == get_county_bbox("Franklin")


def test_county_lookup_invalid():
    with pytest.raises(ValueError, match="Unknown county"):
        get_county_bbox("Nonexistent")


def test_list_counties_count():
    counties = list_counties()
    assert len(counties) == 120


def test_list_counties_includes_key_counties():
    counties = list_counties()
    for c in ["Franklin", "Pike", "Fayette", "Jefferson", "Harlan"]:
        assert c in counties


def test_validate_bbox_valid():
    validate_bbox((-84.5, 38.0, -84.3, 38.2))


def test_validate_bbox_xmin_gt_xmax():
    with pytest.raises(ValueError, match="xmin"):
        validate_bbox((-84.3, 38.0, -84.5, 38.2))


def test_validate_bbox_wrong_length():
    with pytest.raises(ValueError, match="4 elements"):
        validate_bbox((-84.5, 38.0, -84.3))

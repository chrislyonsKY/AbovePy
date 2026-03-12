"""Tests for the product registry."""
import pytest

from abovepy.products import PRODUCTS, ProductType, get_product, list_products


def test_all_products_have_collection_ids():
    for key, prod in PRODUCTS.items():
        assert prod.collection_id, f"Product {key} missing collection_id"


def test_nine_products_total():
    assert len(PRODUCTS) == 9


def test_get_product_valid():
    prod = get_product("dem_phase3")
    assert prod.collection_id == "dem-phase3"
    assert prod.resolution == "2ft"
    assert prod.phase == 3


def test_get_product_invalid():
    with pytest.raises(ValueError, match="Unknown product"):
        get_product("nonexistent")


def test_list_products_by_type():
    dems = list_products(ProductType.DEM)
    assert len(dems) == 3
    assert all(p.product_type == ProductType.DEM for p in dems)

    orthos = list_products(ProductType.ORTHO)
    assert len(orthos) == 3

    pcs = list_products(ProductType.POINTCLOUD)
    assert len(pcs) == 3


def test_collection_id_format():
    """Verify collection IDs match the pattern from the AWS registry."""
    assert get_product("dem_phase1").collection_id == "dem-phase1"
    assert get_product("ortho_phase3").collection_id == "orthos-phase3"
    assert get_product("laz_phase2").collection_id == "laz-phase2"

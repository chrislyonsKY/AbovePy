"""KyFromAbove product registry — maps human-readable keys to STAC collection IDs.

This is the single source of truth for what data exists and how to find it.
Collection IDs confirmed from the AWS Open Data Registry (2026-03).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ProductType(Enum):
    """KyFromAbove data product types."""

    DEM = "dem"
    ORTHO = "ortho"
    POINTCLOUD = "pointcloud"


@dataclass(frozen=True)
class Product:
    """A KyFromAbove data product definition.

    Parameters
    ----------
    key : str
        Short identifier used in the public API (e.g., "dem_phase3").
    display_name : str
        Human-readable label for UI dropdowns and docs.
    collection_id : str
        STAC collection ID in the KyFromAbove API.
    product_type : ProductType
        Category: DEM, ORTHO, or POINTCLOUD.
    resolution : str
        Spatial resolution description.
    format : str
        File format: "COG", "COPC", or "LAZ".
    phase : int
        KyFromAbove acquisition phase (1, 2, or 3).
    native_crs : str
        Native coordinate reference system.
    """

    key: str
    display_name: str
    collection_id: str
    product_type: ProductType
    resolution: str
    format: str
    phase: int
    native_crs: str = "EPSG:3089"

    def __repr__(self) -> str:
        return f"Product({self.key!r}, {self.display_name!r}, {self.format}, {self.resolution})"


# fmt: off
PRODUCTS: dict[str, Product] = {
    # --- DEM ---
    "dem_phase1": Product(
        key="dem_phase1",
        display_name="DEM Phase 1 (5ft)",
        collection_id="dem-phase1",
        product_type=ProductType.DEM,
        resolution="5ft",
        format="COG",
        phase=1,
    ),
    "dem_phase2": Product(
        key="dem_phase2",
        display_name="DEM Phase 2 (2ft)",
        collection_id="dem-phase2",
        product_type=ProductType.DEM,
        resolution="2ft",
        format="COG",
        phase=2,
    ),
    "dem_phase3": Product(
        key="dem_phase3",
        display_name="DEM Phase 3 (2ft)",
        collection_id="dem-phase3",
        product_type=ProductType.DEM,
        resolution="2ft",
        format="COG",
        phase=3,
    ),
    # --- Orthoimagery ---
    "ortho_phase1": Product(
        key="ortho_phase1",
        display_name="Orthoimagery Phase 1 (6-inch)",
        collection_id="orthos-phase1",
        product_type=ProductType.ORTHO,
        resolution="6in",
        format="COG",
        phase=1,
    ),
    "ortho_phase2": Product(
        key="ortho_phase2",
        display_name="Orthoimagery Phase 2 (6-inch)",
        collection_id="orthos-phase2",
        product_type=ProductType.ORTHO,
        resolution="6in",
        format="COG",
        phase=2,
    ),
    "ortho_phase3": Product(
        key="ortho_phase3",
        display_name="Orthoimagery Phase 3 (3-inch)",
        collection_id="orthos-phase3",
        product_type=ProductType.ORTHO,
        resolution="3in",
        format="COG",
        phase=3,
    ),
    # --- Point Cloud / LiDAR ---
    "laz_phase1": Product(
        key="laz_phase1",
        display_name="LiDAR Point Cloud Phase 1 (LAZ)",
        collection_id="laz-phase1",
        product_type=ProductType.POINTCLOUD,
        resolution="varies",
        format="LAZ",
        phase=1,
    ),
    "laz_phase2": Product(
        key="laz_phase2",
        display_name="LiDAR Point Cloud Phase 2 (COPC)",
        collection_id="laz-phase2",
        product_type=ProductType.POINTCLOUD,
        resolution="varies",
        format="COPC",
        phase=2,
    ),
    "laz_phase3": Product(
        key="laz_phase3",
        display_name="LiDAR Point Cloud Phase 3 (COPC)",
        collection_id="laz-phase3",
        product_type=ProductType.POINTCLOUD,
        resolution="varies",
        format="COPC",
        phase=3,
    ),
}
# fmt: on

VALID_PRODUCTS = set(PRODUCTS.keys())

# Reverse lookup: collection_id → Product
_COLLECTION_TO_PRODUCT = {p.collection_id: p for p in PRODUCTS.values()}


def get_product(key: str) -> Product:
    """Get a product by key, raising ValueError if invalid.

    Parameters
    ----------
    key : str
        Product key (e.g., "dem_phase3").

    Returns
    -------
    Product

    Raises
    ------
    ValueError
        If key is not a valid product.
    """
    if key not in PRODUCTS:
        from abovepy._exceptions import ProductError

        valid = ", ".join(sorted(VALID_PRODUCTS))
        raise ProductError(f"Unknown product '{key}'. Valid products: {valid}")
    return PRODUCTS[key]


def list_products(product_type: ProductType | None = None) -> list[Product]:
    """List available products, optionally filtered by type.

    Parameters
    ----------
    product_type : ProductType, optional
        Filter to DEM, ORTHO, or POINTCLOUD.

    Returns
    -------
    list[Product]
    """
    products = list(PRODUCTS.values())
    if product_type is not None:
        products = [p for p in products if p.product_type == product_type]
    return products

"""TiTiler URL helpers — generates tile URLs for web map integration.

This package provides URL builders for TiTiler and TiTiler-pgSTAC instances.
All functions are re-exported here for backward compatibility.
"""

from abovepy.titiler._cog import (
    cog_bounds_url,
    cog_info_url,
    cog_preview_url,
    cog_stats_url,
    cog_tile_url,
    mosaic_tile_url,
)
from abovepy.titiler._pgstac import (
    DEFAULT_PGSTAC_ENDPOINT,
    DEFAULT_TILE_MATRIX_SET,
    _pgstac_query_string,
    _resolve_collection_id,
    collection_bbox_url,
    collection_info_url,
    collection_map_url,
    collection_point_url,
    collection_tile_url,
    contour_tile_url,
    hillshade_tile_url,
    item_info_url,
    item_preview_url,
    item_statistics_url,
    item_tile_url,
    slope_tile_url,
    terrain_rgb_tile_url,
)
from abovepy.titiler._searches import (
    register_search,
    search_bbox_url,
    search_info_url,
    search_map_url,
    search_tile_url,
)

__all__ = [
    "DEFAULT_PGSTAC_ENDPOINT",
    "DEFAULT_TILE_MATRIX_SET",
    "cog_bounds_url",
    "cog_info_url",
    "cog_preview_url",
    "cog_stats_url",
    "cog_tile_url",
    "collection_bbox_url",
    "collection_info_url",
    "collection_map_url",
    "collection_point_url",
    "collection_tile_url",
    "contour_tile_url",
    "hillshade_tile_url",
    "item_info_url",
    "item_preview_url",
    "item_statistics_url",
    "item_tile_url",
    "mosaic_tile_url",
    "register_search",
    "search_bbox_url",
    "search_info_url",
    "search_map_url",
    "search_tile_url",
    "slope_tile_url",
    "terrain_rgb_tile_url",
]

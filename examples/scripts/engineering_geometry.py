"""Kentucky Engineering Geometry — Feet-based buffers and corridor searches.

Demonstrates abovepy's EPSG:3089 geometry utilities for surveyors and
civil engineers who work in Kentucky State Plane coordinates
(Northing/Easting in US survey feet):

1. Point buffer from State Plane coordinates (Northing/Easting)
2. Corridor buffer along a road centerline
3. Search using feet-based geometry
4. Converting between State Plane and WGS84

Usage:
    python engineering_geometry.py
"""

from shapely.geometry import LineString, Point

import abovepy
from abovepy import buffer_feet, corridor_buffer
from abovepy.utils.crs import reproject_bbox


def main():
    # --- State Plane coordinates (how surveyors work) ---
    # Kentucky Single Zone (EPSG:3089) uses Northing/Easting in US feet
    # Frankfort, KY ~ Easting: 1,600,000 ft, Northing: 312,000 ft

    easting = 1_600_000.0
    northing = 312_000.0
    site_3089 = Point(easting, northing)

    # Buffer 500 feet around the survey point — stays in State Plane
    area_3089 = buffer_feet(site_3089, 500.0, input_crs="EPSG:3089")
    print("=== State Plane Point Buffer (500 ft) ===")
    print(f"  Input:  E {easting:,.0f}, N {northing:,.0f} (EPSG:3089)")
    print(f"  Output: {area_3089.geom_type}")
    bounds = area_3089.bounds
    print(f"  Bounds: E {bounds[0]:,.0f} - {bounds[2]:,.0f}, N {bounds[1]:,.0f} - {bounds[3]:,.0f}")

    # --- Corridor buffer from State Plane coordinates ---
    # Road centerline in Easting/Northing
    road_3089 = LineString([
        (1_599_000, 312_000),
        (1_600_000, 311_500),
        (1_601_000, 312_500),
    ])
    corridor_3089 = corridor_buffer(road_3089, 400.0, input_crs="EPSG:3089")  # 200ft each side
    print("\n=== State Plane Corridor Buffer (400 ft total) ===")
    print(f"  Input:  LineString with {len(road_3089.coords)} vertices")
    print(f"  Output: {corridor_3089.geom_type}")
    cb = corridor_3089.bounds
    print(f"  Bounds: E {cb[0]:,.0f} - {cb[2]:,.0f}, N {cb[1]:,.0f} - {cb[3]:,.0f}")

    # --- WGS84 workflow (for users who have lat/lon) ---
    # buffer_feet defaults to EPSG:4326 input, projects to 3089 internally
    site_wgs84 = Point(-84.87, 38.20)
    area_wgs84 = buffer_feet(site_wgs84, 500.0)  # input_crs defaults to EPSG:4326
    print("\n=== WGS84 Point Buffer (500 ft) ===")
    print(f"  Input:  lon {site_wgs84.x}, lat {site_wgs84.y} (EPSG:4326)")
    print(f"  Output: {area_wgs84.geom_type}, returned in EPSG:4326")
    print(f"  Bounds: {tuple(round(c, 6) for c in area_wgs84.bounds)}")

    # --- Coordinate conversion ---
    # Convert a bbox from State Plane to WGS84 for STAC searches
    bbox_3089 = (1_598_000, 310_000, 1_602_000, 314_000)
    bbox_4326 = reproject_bbox(bbox_3089, "EPSG:3089", "EPSG:4326")
    print("\n=== Bbox Conversion (State Plane -> WGS84) ===")
    print(f"  State Plane: E {bbox_3089[0]:,.0f}-{bbox_3089[2]:,.0f}, "
          f"N {bbox_3089[1]:,.0f}-{bbox_3089[3]:,.0f}")
    print(f"  WGS84:       {tuple(round(c, 6) for c in bbox_4326)}")

    # --- Search with buffer_feet from lon/lat ---
    print("\n=== Search with buffer_feet ===")
    result = abovepy.search(
        point=(-84.87, 38.20),
        buffer_feet=1000,
        product="dem_phase3",
    )
    print(result)

    # --- Search with corridor geometry ---
    print("\n=== Corridor Search ===")
    road_wgs84 = LineString([(-84.90, 38.20), (-84.87, 38.19), (-84.85, 38.21)])
    result = abovepy.search(
        geometry=road_wgs84,
        buffer_feet=200,
        product="ortho_phase3",
    )
    print(result)


if __name__ == "__main__":
    main()

# Expected output:
# === State Plane Point Buffer (500 ft) ===
#   Input:  E 1,600,000, N 312,000 (EPSG:3089)
#   Output: Polygon
#   Bounds: E 1,599,500 - 1,600,500, N 311,500 - 312,500
#
# === State Plane Corridor Buffer (400 ft total) ===
#   Input:  LineString with 3 vertices
#   Output: Polygon
#   Bounds: E 1,598,800 - 1,601,200, N 311,300 - 312,700
#
# === WGS84 Point Buffer (500 ft) ===
#   Input:  lon -84.87, lat 38.2 (EPSG:4326)
#   Output: Polygon, returned in EPSG:4326
#   Bounds: (-84.8718XX, 38.198XXX, -84.8681XX, 38.201XXX)
#
# === Bbox Conversion (State Plane -> WGS84) ===
#   State Plane: E 1,598,000-1,602,000, N 310,000-314,000
#   WGS84:       (-84.88XXXX, 38.18XXXX, -84.85XXXX, 38.22XXXX)
#
# === Search with buffer_feet ===
# SearchResult('dem_phase3', N tile(s), ~X MB)
#
# === Corridor Search ===
# SearchResult('ortho_phase3', N tile(s), ~X MB)

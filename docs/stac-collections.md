# KyFromAbove Collections

All data comes from the [KyFromAbove](https://kyfromabove.ky.gov/) program, managed by the Kentucky Division of Geographic Information. Data is publicly hosted on AWS S3 with a STAC API for discovery.

## STAC API

| Property | Value |
|---|---|
| **Endpoint** | `https://spved5ihrl.execute-api.us-west-2.amazonaws.com/` |
| **Type** | stac-fastapi with CQL2, OGC API Features |
| **S3 Bucket** | `s3://kyfromabove/` (public, us-west-2) |
| **Tile Grid** | 5,000 x 5,000 ft, EPSG:3089 |
| **Native CRS** | EPSG:3089 (Kentucky Single Zone, US feet) |

## Digital Elevation Models (DEM)

| Product Key | Collection ID | Resolution | Format | Phase |
|---|---|---|---|---|
| `dem_phase1` | `dem-phase1` | 5 ft | Cloud-Optimized GeoTIFF | 1 |
| `dem_phase2` | `dem-phase2` | 2 ft | Cloud-Optimized GeoTIFF | 2 |
| `dem_phase3` | `dem-phase3` | 2 ft | Cloud-Optimized GeoTIFF | 3 |

DEMs are bare-earth elevation models derived from LiDAR point clouds. Phase 2 and 3 provide 2-foot resolution across the state.

```python
tiles = abovepy.search(county="Pike", product="dem_phase3")
```

## Orthoimagery

| Product Key | Collection ID | Resolution | Format | Phase |
|---|---|---|---|---|
| `ortho_phase1` | `orthos-phase1` | 6 in | Cloud-Optimized GeoTIFF | 1 |
| `ortho_phase2` | `orthos-phase2` | 6 in | Cloud-Optimized GeoTIFF | 2 |
| `ortho_phase3` | `orthos-phase3` | 3 in | Cloud-Optimized GeoTIFF | 3 |

RGB aerial photography. Phase 3 provides 3-inch resolution — enough to see individual cars and sidewalks.

```python
tiles = abovepy.search(county="Fayette", product="ortho_phase3")
```

## LiDAR Point Clouds

| Product Key | Collection ID | Resolution | Format | Phase |
|---|---|---|---|---|
| `laz_phase1` | `laz-phase1` | varies | LAZ | 1 |
| `laz_phase2` | `laz-phase2` | varies | COPC | 2 |
| `laz_phase3` | `laz-phase3` | varies | COPC (partial) | 3 |

!!! note
    LiDAR support requires the `lidar` extra: `pip install abovepy[lidar]`

Phase 1 files are classic LAZ. Phase 2 and 3 use [COPC](https://copc.io/) (Cloud-Optimized Point Cloud), which supports spatial indexing for efficient bbox reads without downloading full files.

```python
tiles = abovepy.search(county="Harlan", product="laz_phase2")
```

## CRS Details

All KyFromAbove data is natively in **EPSG:3089** — Kentucky Single Zone (NAD83), US survey feet.

abovepy accepts bounding boxes in **EPSG:4326** (WGS 84, longitude/latitude) by default and converts transparently. You can also pass coordinates in EPSG:3089 directly:

```python
tiles = abovepy.search(
    bbox=(1600000, 200000, 1650000, 250000),
    product="dem_phase3",
    crs="EPSG:3089"
)
```

## Direct STAC Access

For power users who need the full pystac-client API:

```python
client = abovepy.KyFromAboveClient()
stac = client.get_stac_client()

for collection in stac.get_collections():
    print(f"{collection.id}: {collection.title}")
```

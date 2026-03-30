# Start Here

Welcome to abovepy, a Python library for accessing KyFromAbove LiDAR, DEM, and orthoimagery data.

## Quick Start

```bash
pip install abovepy
```

```python
import abovepy

# Search for DEM tiles covering Frankfort
result = abovepy.search(county="Franklin", product="dem_phase3")
print(result)  # SearchResult('dem_phase3', 42 tiles, ~210.0 MB)

# Estimate download size before committing
result.estimate_size()

# Download
paths = result.download("./data")

# Or use the CLI
# abovepy search --county Franklin --product dem_phase3
# abovepy estimate --county Franklin
# abovepy download --county Franklin -o ./data
```

## Key Resources

| Resource | Location |
| --- | --- |
| Installation and usage | [Getting Started](docs/getting-started.md) |
| API reference | [docs/api/](docs/api/) |
| Tutorials | [docs/tutorials/](docs/tutorials/) |
| Architecture overview | [ARCHITECTURE](docs/architecture.md) |
| Development setup | [DEVELOPMENT.md](DEVELOPMENT.md) |
| Contributing | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Roadmap | [ROADMAP.md](ROADMAP.md) |
| Support | [SUPPORT.md](SUPPORT.md) |
| Security | [SECURITY.md](SECURITY.md) |

## Project Structure

```
src/abovepy/
    __init__.py          # Public API: search, download, read, mosaic, info
    result.py            # SearchResult workflow object
    client.py            # KyFromAboveClient
    products.py          # Product registry (13 products)
    stac.py              # STAC API wrapper with retry and caching
    cli.py               # Command-line interface
    terrain.py           # Local terrain analysis (hillshade, slope, etc.)
    export.py            # GeoTIFF, GeoPackage, Shapefile export
    _download.py         # Concurrent/resumable tile downloader
    _mosaic.py           # VRT/GeoTIFF mosaicking
    io/                  # COG and point cloud readers
    titiler/             # TiTiler URL builders
    viz/                 # Visualization helpers and notebook maps
    obliques/            # Oblique imagery S3 discovery
    utils/               # Bbox, CRS, cache utilities
```

## Who This Is For

- Kentucky GIS analysts working with KyFromAbove data
- Government agencies and consultants needing elevation, imagery, and LiDAR access
- Researchers studying Kentucky terrain, land use, and environmental change
- ArcGIS Pro users via the AbovePro toolbox

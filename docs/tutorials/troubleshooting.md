# Troubleshooting

Solutions for common issues when using abovepy. Each section describes the problem, explains why it happens, and provides a fix.

---

## "No module named abovepy"

**Symptom:** You run `import abovepy` and get:

```text
ModuleNotFoundError: No module named 'abovepy'
```

**Cause:** abovepy is not installed in the Python environment you are using.

**Fix:**

Install abovepy in the correct environment:

```bash
pip install abovepy
```

Then verify it worked:

```bash
python -c "import abovepy; print(abovepy.__version__)"
```

```text
0.1.0
```

!!! warning "Multiple Python environments"
    This error most commonly occurs when you have multiple Python installations (system Python, conda environments, virtual environments, ArcGIS Pro's environment). Make sure you install abovepy in the same environment you are running your code from.

    Check which Python you are using:

    ```bash
    python --version
    which python
    ```

    ```text
    Python 3.12.3
    /home/user/miniconda3/envs/abovepy/bin/python
    ```

    If you are using a conda environment, activate it first:

    ```bash
    conda activate myenv
    pip install abovepy
    ```

    If you are using ArcGIS Pro, open **Pro's Python Command Prompt** (not a regular terminal) and install there. See the [ArcGIS Pro Toolbox](arcgis-pro.md) guide for details.

---

## Slow downloads

**Symptom:** `abovepy.download()` takes a very long time, or appears to hang.

**Cause:** KyFromAbove tiles are large files, especially orthoimagery and LiDAR data. Download speed depends on your internet connection, the number of tiles, and the product type.

### Typical file sizes per tile

| Product | Typical tile size | Tiles per county (avg) |
|---------|-------------------|------------------------|
| DEM Phase 1 (5ft) | 2-5 MB | 40-200 |
| DEM Phase 2 (2ft) | 5-10 MB | 40-200 |
| DEM Phase 3 (2ft) | 5-10 MB | 40-200 |
| Ortho Phase 1 (6in) | 50-150 MB | 40-200 |
| Ortho Phase 2 (6in) | 50-150 MB | 40-200 |
| Ortho Phase 3 (3in) | 100-400 MB | 40-200 |
| LiDAR Phase 1 (LAZ) | 100-400 MB | 40-200 |
| LiDAR Phase 2 (COPC) | 150-500 MB | 40-200 |
| LiDAR Phase 3 (COPC) | 150-500 MB | 40-200 |

**Fix:**

**1. Check total size before downloading:**

```python
tiles = abovepy.search(county="Jefferson", product="ortho_phase3")
total_gb = tiles.file_size.sum() / 1e9
print(f"Total download: {total_gb:.1f} GB across {len(tiles)} tiles")
```

```text
Total download: 42.7 GB across 312 tiles
```

**2. Use a bounding box to limit the area:**

Instead of downloading an entire county, search for just the area you need:

```python
# Instead of this (entire county):
tiles = abovepy.search(county="Jefferson", product="ortho_phase3")

# Do this (specific area):
tiles = abovepy.search(
    bbox=(-85.72, 38.22, -85.68, 38.26),
    product="ortho_phase3"
)
print(f"Reduced to {len(tiles)} tiles")
```

```text
Reduced to 4 tiles
```

**3. Use streaming reads instead of downloading:**

If you only need to inspect or preview data, read directly from the cloud without downloading:

```python
data, profile = abovepy.read(
    tiles.iloc[0].asset_url,
    bbox=(-85.72, 38.22, -85.68, 38.26)
)
print(f"Read {data.shape} array without downloading")
```

```text
Read (1, 1847, 1534) array without downloading
```

**4. Download a subset:**

```python
# Download only the first 5 tiles
paths = abovepy.download(tiles.head(5), output_dir="./sample")
```

!!! tip "Downloads are resumable"
    If a download is interrupted, re-run `abovepy.download()` with the same output directory. Files that were fully downloaded will be skipped automatically.

---

## Empty search results

**Symptom:** `abovepy.search()` returns an empty GeoDataFrame with zero rows.

```python
tiles = abovepy.search(bbox=(-90.0, 35.0, -89.0, 36.0), product="dem_phase3")
print(f"Found {len(tiles)} tiles")
```

```text
Found 0 tiles
```

**Cause:** There are three common reasons for empty results.

### 1. Bounding box is outside Kentucky

KyFromAbove only covers the state of Kentucky. If your bounding box is outside Kentucky's borders, no tiles will be found.

Kentucky's approximate bounding box is:

```text
West:  -89.57
South:  36.50
East:  -81.96
North:  39.15
```

**Fix:** Verify your coordinates are within Kentucky:

```python
# This bbox is in Tennessee, not Kentucky
tiles = abovepy.search(bbox=(-90.0, 35.0, -89.0, 36.0), product="dem_phase3")
print(f"Found {len(tiles)} tiles")  # 0

# This bbox is in Kentucky
tiles = abovepy.search(bbox=(-84.9, 38.15, -84.8, 38.25), product="dem_phase3")
print(f"Found {len(tiles)} tiles")  # > 0
```

```text
Found 0 tiles
Found 6 tiles
```

!!! note "Bbox format"
    The bounding box format is `(west, south, east, north)` in EPSG:4326 (longitude, latitude). A common mistake is swapping latitude and longitude. Longitude values for Kentucky are negative (west of the Prime Meridian); latitude values are positive.

    ```python
    # WRONG: lat/lon swapped
    bbox = (38.15, -84.9, 38.25, -84.8)

    # CORRECT: (west, south, east, north) = (lon, lat, lon, lat)
    bbox = (-84.9, 38.15, -84.8, 38.25)
    ```

### 2. Wrong product name

Product names must match exactly. A typo or incorrect name returns zero results.

**Fix:** List available products and use the exact key:

```python
print(abovepy.info())
```

```text
Available KyFromAbove Products:
  dem_phase1     DEM Phase 1 (5ft)       COG
  dem_phase2     DEM Phase 2 (2ft)       COG
  dem_phase3     DEM Phase 3 (2ft)       COG
  ortho_phase1   Ortho Phase 1 (6in)     COG
  ortho_phase2   Ortho Phase 2 (6in)     COG
  ortho_phase3   Ortho Phase 3 (3in)     COG
  laz_phase1     LiDAR Phase 1           LAZ
  laz_phase2     LiDAR Phase 2           COPC
  laz_phase3     LiDAR Phase 3           COPC
```

Common mistakes:

```python
# WRONG
abovepy.search(product="dem3")           # Missing "phase"
abovepy.search(product="dem-phase3")     # Hyphen instead of underscore
abovepy.search(product="DEM_Phase3")     # Wrong capitalization
abovepy.search(product="lidar_phase2")   # Use "laz", not "lidar"

# CORRECT
abovepy.search(product="dem_phase3")
abovepy.search(product="laz_phase2")
```

### 3. Misspelled county name

If you use a county name that does not match any of the 120 Kentucky counties, the search will fail or return no results.

**Fix:** County names must be spelled correctly (case-insensitive):

```python
# These all work
abovepy.search(county="Pike", product="dem_phase3")
abovepy.search(county="pike", product="dem_phase3")
abovepy.search(county="PIKE", product="dem_phase3")

# This does NOT work
abovepy.search(county="Pikeville", product="dem_phase3")  # City name, not county
```

---

## CRS confusion (EPSG:4326 vs EPSG:3089)

**Symptom:** Coordinates do not look right, data does not align with other layers, or elevation values seem wrong.

**Explanation:**

KyFromAbove data uses two coordinate reference systems:

| CRS | Name | Units | Used for |
|-----|------|-------|----------|
| **EPSG:4326** | WGS 84 (Geographic) | Degrees (lon, lat) | Input to abovepy (bbox, county) |
| **EPSG:3089** | Kentucky Single Zone (NAD83) | US Survey Feet | Native tile CRS, output data |

abovepy handles CRS conversion automatically:

- **Input:** You provide bounding boxes in EPSG:4326 (longitude, latitude). This is the standard GPS coordinate system that most people are familiar with.
- **Conversion:** abovepy converts your EPSG:4326 bbox to EPSG:3089 internally before querying the STAC API.
- **Output:** Downloaded tiles, mosaics, and streaming reads are in **EPSG:3089**. Coordinate values are in US Survey Feet.

**Fix:**

You do not need to do any CRS conversion yourself. Just provide EPSG:4326 coordinates:

```python
# You provide EPSG:4326 (degrees)
tiles = abovepy.search(
    bbox=(-84.9, 38.15, -84.8, 38.25),
    product="dem_phase3"
)

# Output data is in EPSG:3089 (feet)
data, profile = abovepy.read(tiles.iloc[0].asset_url)
print(f"CRS: {profile['crs']}")
print(f"Bounds: {profile['transform'] * (0, 0)} (in feet)")
```

```text
CRS: EPSG:3089
Bounds: (1234000.0, 5698000.0) (in feet)
```

!!! tip "Converting output coordinates"
    If you need to convert output coordinates back to EPSG:4326 (e.g., for web mapping), use pyproj:

    ```python
    from pyproj import Transformer

    transformer = Transformer.from_crs("EPSG:3089", "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(1234000.0, 5698000.0)
    print(f"Longitude: {lon:.6f}, Latitude: {lat:.6f}")
    ```

    ```text
    Longitude: -84.871234, Latitude: 38.196789
    ```

!!! warning "Elevation units"
    Elevation values in KyFromAbove DEMs are in **US Survey Feet**, not meters. If you are comparing with data in meters, convert accordingly: `meters = feet * 0.3048006096`.

---

## Memory issues with large mosaics

**Symptom:** Python crashes, you see `MemoryError`, or your system becomes unresponsive when mosaicking or reading many tiles.

**Cause:** Loading many high-resolution tiles into memory at once can exhaust available RAM. A single DEM tile at 2-foot resolution is approximately 2500x2500 pixels (25 MB as float32). A county with 200 tiles would require ~5 GB of RAM to hold all pixels simultaneously.

**Fix:**

### 1. Use VRT instead of GeoTIFF mosaic

VRT creates a virtual mosaic that does not load all pixels into memory:

```python
# GOOD: VRT uses almost no memory
vrt = abovepy.mosaic(paths, output="mosaic.vrt")

# CAUTION: GeoTIFF loads everything into memory during creation
tif = abovepy.mosaic(paths, output="mosaic.tif")
```

!!! tip
    VRT is the default and recommended approach. It creates an XML file that references the original tiles. Data is only loaded into memory when you actually read pixels from the VRT.

### 2. Use windowed reads with a bbox

Instead of reading an entire mosaic, read just the area you need:

```python
# GOOD: Read only the pixels you need
data, profile = abovepy.read(
    tiles.iloc[0].asset_url,
    bbox=(-84.87, 38.19, -84.84, 38.21)
)
print(f"Shape: {data.shape}")
```

```text
Shape: (1, 1847, 1534)
```

```python
# CAUTION: Reading the entire tile
data, profile = abovepy.read(tiles.iloc[0].asset_url)
print(f"Shape: {data.shape}")
```

```text
Shape: (1, 2500, 2500)
```

### 3. Process tiles one at a time

For operations that do not require all tiles in memory simultaneously (e.g., computing statistics), iterate:

```python
import rasterio
import numpy as np

# Instead of loading all tiles, process one at a time
min_elev = float("inf")
max_elev = float("-inf")

for path in paths:
    with rasterio.open(str(path)) as src:
        data = src.read(1)
        min_elev = min(min_elev, np.nanmin(data))
        max_elev = max(max_elev, np.nanmax(data))
        # Memory is freed when the loop moves to the next tile

print(f"Elevation range across all tiles: {min_elev:.1f} to {max_elev:.1f} ft")
```

```text
Elevation range across all tiles: 482.3 to 891.7 ft
```

### 4. Reduce the search area

If memory is a persistent issue, work with a smaller area:

```python
# Instead of an entire county
tiles = abovepy.search(county="Jefferson", product="dem_phase3")  # 312 tiles

# Use a bounding box for just your area of interest
tiles = abovepy.search(
    bbox=(-85.72, 38.22, -85.68, 38.26),
    product="dem_phase3"
)  # 4 tiles
```

---

## LiDAR optional dependency errors

**Symptom:** You try to work with LiDAR data and get:

```text
ModuleNotFoundError: No module named 'laspy'
```

**Cause:** LiDAR support requires the `laspy` package, which is an optional dependency. It is not installed with the base `abovepy` package because it is a heavier dependency that most DEM and orthoimagery users do not need.

**Fix:**

Install the LiDAR extra:

```bash
pip install abovepy[lidar]
```

```text
Successfully installed laspy-2.5.4 lazrs-0.6.0
```

Verify:

```python
import laspy
print(f"laspy version: {laspy.__version__}")
```

```text
laspy version: 2.5.4
```

!!! note "Shell quoting"
    Some shells (especially zsh on macOS) interpret square brackets specially. If you get an error, quote the package name:

    ```bash
    pip install "abovepy[lidar]"
    ```

!!! note "All optional dependencies"
    You can also install everything at once:

    ```bash
    pip install abovepy[all]
    ```

    This installs LiDAR support (`laspy`), visualization (`leafmap`, `matplotlib`), and S3 access (`boto3`).

---

## Network and timeout errors

**Symptom:** You see errors like:

```text
httpx.ConnectTimeout: timed out
httpx.ReadTimeout: timed out
ConnectionError: Failed to establish a new connection
```

**Cause:** abovepy connects to two external services over the internet:

1. **KyFromAbove STAC API** (`spved5ihrl.execute-api.us-west-2.amazonaws.com`) for search queries
2. **S3 bucket** (`s3://kyfromabove/`) for tile downloads

Network errors can occur due to:

- No internet connection
- Firewall or proxy blocking outbound HTTPS
- The STAC API experiencing a temporary outage (it runs on AWS Lambda, which can have cold starts)
- Very slow or unstable connections

**Fix:**

### 1. Check your internet connection

```bash
curl -s https://spved5ihrl.execute-api.us-west-2.amazonaws.com/ | python -m json.tool
```

If this returns a JSON response, the API is reachable. If it times out, you have a network issue.

### 2. Retry behavior

abovepy includes built-in retry logic for transient failures. By default, it retries failed requests up to 3 times with exponential backoff. Most temporary errors (5xx responses, connection resets) resolve on retry.

If you are seeing persistent timeouts, the issue is likely on your end (firewall, proxy, or ISP).

### 3. Proxy configuration

If you are behind a corporate proxy, configure it via environment variables:

```bash
export HTTPS_PROXY=http://proxy.example.com:8080
export HTTP_PROXY=http://proxy.example.com:8080
```

On Windows (PowerShell):

```powershell
$env:HTTPS_PROXY = "http://proxy.example.com:8080"
$env:HTTP_PROXY = "http://proxy.example.com:8080"
```

httpx (the HTTP client used by abovepy) respects these standard environment variables.

### 4. STAC API cold starts

The KyFromAbove STAC API runs on AWS Lambda (serverless). The first request after a period of inactivity may be slow (2-5 seconds) due to a "cold start." Subsequent requests in the same session will be faster.

If the first `search()` call is slow but subsequent calls are fast, this is normal behavior.

!!! tip "SSL certificate errors"
    If you see `ssl.SSLCertVerificationError`, your Python installation may have outdated root certificates. On macOS, run:

    ```bash
    /Applications/Python\ 3.12/Install\ Certificates.command
    ```

    On other systems, ensure `certifi` is up to date:

    ```bash
    pip install --upgrade certifi
    ```

---

## Rasterio or GDAL errors

**Symptom:** Errors mentioning `rasterio`, `GDAL`, or `libgdal` when trying to read or mosaic tiles.

```text
rasterio.errors.RasterioIOError: '/vsicurl/...' not recognized as a supported file format
ImportError: DLL load failed while importing _base
```

**Cause:** rasterio depends on GDAL, a C library that must be installed correctly. Binary wheels on PyPI usually handle this, but issues can arise on some systems.

**Fix:**

### pip (most systems)

```bash
pip install --upgrade rasterio
```

The PyPI wheels for rasterio include a bundled GDAL. This works on most systems without additional setup.

### conda (if pip fails)

If the pip install fails or GDAL errors persist, use conda which manages the native library dependencies:

```bash
conda install -c conda-forge rasterio
```

### ArcGIS Pro

ArcGIS Pro includes its own GDAL/rasterio. Do not install a separate version — it will conflict. Use Pro's built-in Python environment as-is.

!!! note "Windows-specific"
    On Windows, if you see `DLL load failed` errors, it usually means conflicting GDAL installations. Ensure you do not have a standalone GDAL/OSGeo4W installation interfering with rasterio's bundled GDAL. Using a clean virtual environment is the safest approach.

---

## Getting help

If your issue is not covered here:

1. **Check the [API Reference](../api/reference.md)** for function signatures and parameter details
2. **Search [GitHub Issues](https://github.com/chrislyonsKY/abovepy/issues)** for similar problems
3. **Open a new issue** with:
    - Your Python version (`python --version`)
    - Your abovepy version (`python -c "import abovepy; print(abovepy.__version__)"`)
    - The full error traceback
    - A minimal code example that reproduces the issue

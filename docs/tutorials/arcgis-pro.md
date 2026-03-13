# ArcGIS Pro Toolbox

Use abovepy inside ArcGIS Pro with the **AbovePro** Python Toolbox. This guide covers installation, adding the toolbox, and using each of the five tools with detailed parameter descriptions and expected behavior.

## Requirements

- ArcGIS Pro 3.2+
- abovepy installed in Pro's Python environment

---

## Installation

### Step 1: Install abovepy in Pro's conda environment

Open the **Python Command Prompt** from ArcGIS Pro (not a regular terminal) and run:

```bash
pip install abovepy
```

```text
Successfully installed abovepy-0.1.0 geopandas-0.14.4 httpx-0.27.0 ...
```

!!! warning "Use Pro's Python environment"
    ArcGIS Pro uses its own isolated conda environment. You must install abovepy there, not in a separate Python installation. If you install it in the wrong environment, the toolbox will fail with `ModuleNotFoundError`.

    To verify you are in the correct environment:

    ```bash
    where python
    ```

    You should see a path like `C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe`. If you see a different Python, you are in the wrong environment.

### Step 2: Verify the installation

Still in Pro's Python Command Prompt:

```bash
python -c "import abovepy; print(abovepy.__version__)"
```

```text
0.1.0
```

### Step 3: Add the toolbox to ArcGIS Pro

1. Open ArcGIS Pro and create or open a project
2. In the **Catalog** pane, right-click **Toolboxes**
3. Click **Add Toolbox**
4. Navigate to the `arcgis/AbovePro.pyt` file in the abovepy repository
5. Click **OK**

The **AbovePro** toolbox appears in the Catalog pane with five tools.

<!-- Screenshot placeholder: Catalog pane showing AbovePro toolbox with five tools expanded -->
*The AbovePro toolbox in the Catalog pane, showing all five tools.*

!!! tip "Make AbovePro available in every project"
    To avoid re-adding the toolbox each time:

    1. In the Catalog pane, right-click **AbovePro.pyt**
    2. Click **Add To Favorites**

    The toolbox will now appear under **Favorites** in every ArcGIS Pro project.

---

## Tools Overview

The AbovePro toolbox provides five tools that cover the most common KyFromAbove workflows:

| Tool | Purpose | Typical use case |
|------|---------|------------------|
| **Find KyFromAbove Tiles** | Search for tiles by extent and product | "What tiles cover my area?" |
| **Download Tiles** | Download tiles to a local folder | "Get the files onto my machine" |
| **Download and Load** | Search + download + add to map in one step | "I just want the data on my map" |
| **DEM Hillshade** | Full DEM-to-hillshade pipeline | "Generate a hillshade for this area" |
| **County Download** | Download all tiles for a county | "Give me everything for Pike County" |

---

## Tool 1: Find KyFromAbove Tiles

Search for tiles by map extent, drawn rectangle, or county name. This tool queries the KyFromAbove STAC API and returns tile footprints as a feature layer.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| **Product** | Dropdown | Yes | — | Data product to search. Options: DEM Phase 1, DEM Phase 2, DEM Phase 3, Ortho Phase 1, Ortho Phase 2, Ortho Phase 3, LiDAR Phase 1, LiDAR Phase 2, LiDAR Phase 3 |
| **Extent** | GPExtent | Yes (unless County set) | Current map extent | The geographic area to search. Can be the current map extent, a drawn rectangle, or the extent of an existing layer |
| **County** | String (optional) | No | — | A Kentucky county name. If provided, overrides the Extent parameter. Dropdown lists all 120 Kentucky counties |
| **Max Tiles** | Long | No | 500 | Maximum number of tiles to return. Use this to prevent accidentally querying very large areas |

### Expected behavior

1. The tool queries the KyFromAbove STAC API for tiles matching your product and area
2. A new **feature layer** is added to your active map showing tile footprint polygons
3. Each polygon's attribute table contains: tile ID, asset URL, file size, and collection metadata
4. The map zooms to the extent of the returned tiles

<!-- Screenshot placeholder: Map view showing tile footprint polygons overlaid on a basemap -->
*Tile footprints displayed on the map after running Find KyFromAbove Tiles.*

### Messages window output

```text
Running: Find KyFromAbove Tiles
  Product: DEM Phase 3
  Extent: -84.90, 38.17, -84.83, 38.22
  Querying STAC API...
  Found 6 tiles
  Adding feature layer to map...
  Complete.
```

!!! tip "Use this tool first"
    Run **Find KyFromAbove Tiles** before downloading to see how many tiles cover your area and estimate the total download size. The attribute table includes a `file_size` column you can sum.

---

## Tool 2: Download Tiles

Download tiles from a previous search result to a local folder. Supports progress tracking and skip-existing behavior.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| **Tiles** | Feature Layer | Yes | — | The tile footprint layer from **Find KyFromAbove Tiles**, or any feature layer with an `asset_url` field |
| **Output Directory** | Folder | Yes | — | Local folder where files will be saved. Created if it does not exist |
| **Overwrite** | Boolean | No | False | If True, re-downloads files that already exist on disk. If False (default), existing files are skipped |

### Expected behavior

1. The tool reads the `asset_url` field from each feature in the input layer
2. Files are downloaded with a progress bar in the Geoprocessing pane
3. Existing files are skipped unless **Overwrite** is checked
4. The tool reports the number of files downloaded and total size

### Messages window output

```text
Running: Download Tiles
  Output directory: C:\Data\frankfort_dem
  Downloading 6 tiles...
    [1/6] N1234E5678.tif  (6.8 MB) — downloaded
    [2/6] N1234E5679.tif  (7.0 MB) — downloaded
    [3/6] N1235E5678.tif  (6.9 MB) — downloaded
    [4/6] N1235E5679.tif  (7.2 MB) — downloaded
    [5/6] N1236E5678.tif  (6.5 MB) — downloaded
    [6/6] N1236E5679.tif  (7.1 MB) — downloaded
  Complete. Downloaded 6 files (41.5 MB total).
```

!!! warning "Large downloads"
    LiDAR tiles can be hundreds of megabytes each. Check the tile count and total file size with **Find KyFromAbove Tiles** before starting a large download. Consider downloading a subset by selecting specific features in the tile layer before running this tool.

---

## Tool 3: Download and Load

Combines search, download, and add-to-map in one step. This is the most convenient tool for quickly getting data onto your map.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| **Product** | Dropdown | Yes | — | Data product (same options as Find Tiles) |
| **Extent** | GPExtent | Yes (unless County set) | Current map extent | Area to search |
| **County** | String (optional) | No | — | Kentucky county name (overrides Extent) |
| **Output Directory** | Folder | Yes | — | Local folder for downloaded files |

### Expected behavior

1. Searches for tiles matching the product and area
2. Downloads all matching tiles to the output directory
3. Adds the downloaded rasters to the active map as a **group layer**
4. DEM tiles are added with an elevation color ramp; ortho tiles are added as RGB

### Messages window output

```text
Running: Download and Load
  Product: Ortho Phase 3
  County: Franklin
  Searching for tiles...
  Found 42 tiles
  Downloading to C:\Data\franklin_ortho...
    Downloading: 42/42 complete
  Adding rasters to map as group layer "Ortho Phase 3 — Franklin"...
  Complete. 42 rasters added to map.
```

<!-- Screenshot placeholder: Map showing downloaded ortho tiles loaded as a group layer -->
*Orthoimagery tiles loaded as a group layer after running Download and Load.*

---

## Tool 4: DEM Hillshade

The signature tool. Runs the complete DEM-to-hillshade pipeline: search, download, mosaic, compute hillshade, and add to the map with appropriate symbology.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| **DEM Product** | Dropdown | Yes | — | DEM Phase 1 (5ft), DEM Phase 2 (2ft), or DEM Phase 3 (2ft) |
| **Extent** | GPExtent | Yes (unless County set) | Current map extent | Area of interest |
| **County** | String (optional) | No | — | Kentucky county name (overrides Extent) |
| **Output Directory** | Folder | Yes | — | Folder for downloaded DEM tiles and output hillshade |
| **Azimuth** | Double | No | 315 | Sun azimuth in degrees (0-360). 315 = northwest, which is the cartographic standard |
| **Altitude** | Double | No | 45 | Sun altitude in degrees above the horizon (0-90). Lower values produce more dramatic shadows |

### Expected behavior

1. Searches for DEM tiles covering the area
2. Downloads all DEM tiles
3. Mosaics tiles into a single raster (VRT)
4. Computes a hillshade using the specified sun angle
5. Saves the hillshade as a GeoTIFF in the output directory
6. Adds both the DEM mosaic and the hillshade to the map
7. The hillshade is rendered with grayscale symbology; the DEM with an elevation color ramp

### Messages window output

```text
Running: DEM Hillshade
  DEM Product: DEM Phase 3
  Area: Frankfort (bbox)
  Azimuth: 315°, Altitude: 45°
  Searching for DEM tiles...
  Found 6 tiles
  Downloading DEM tiles...
    Downloading: 6/6 complete
  Creating mosaic (VRT)...
  Computing hillshade...
  Saving hillshade to C:\Data\frankfort\hillshade.tif...
  Adding layers to map...
  Complete. DEM mosaic and hillshade added to map.
```

<!-- Screenshot placeholder: Map showing hillshade rendering with DEM elevation overlay -->
*Hillshade output from the DEM Hillshade tool, showing terrain near Frankfort.*

!!! tip "Azimuth and altitude"
    The default values (azimuth 315, altitude 45) produce a classic cartographic hillshade. To experiment:

    - **Azimuth 90, altitude 25**: Dramatic low-angle light from the east — highlights ridgelines
    - **Azimuth 315, altitude 70**: Flatter appearance, shows less terrain detail
    - **Azimuth 180, altitude 35**: Light from the south — unusual but useful for north-facing slopes

---

## Tool 5: County Download

Download all tiles for a selected Kentucky county in one click. Useful for building a local data library.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| **County** | Dropdown | Yes | — | Kentucky county name. All 120 counties are listed alphabetically |
| **Product** | Dropdown | Yes | — | Data product to download |
| **Output Directory** | Folder | Yes | — | Local folder for downloaded files |

### Expected behavior

1. Looks up the county's bounding box from the built-in lookup table
2. Searches for all tiles of the selected product within the county
3. Downloads all tiles with progress tracking
4. Reports the total number of files and download size

### Messages window output

```text
Running: County Download
  County: Pike
  Product: DEM Phase 3
  Searching for tiles...
  Found 187 tiles (estimated 4.8 GB)
  Downloading to C:\Data\pike_dem...
    Downloading: 187/187 complete
  Complete. Downloaded 187 files (4.8 GB total).
```

!!! warning "Large counties"
    Some counties have hundreds of tiles, especially for orthoimagery and LiDAR products. Always check the tile count and estimated size before running County Download on large counties. Consider using **Find KyFromAbove Tiles** first to preview the count.

    Approximate tile counts for large counties:

    | County | DEM Tiles | Ortho Tiles | LiDAR Tiles |
    |--------|-----------|-------------|-------------|
    | Pike | ~187 | ~187 | ~187 |
    | Jefferson | ~312 | ~312 | ~312 |
    | Fayette | ~68 | ~68 | ~68 |
    | Franklin | ~42 | ~42 | ~42 |

---

## Tips and Best Practices

!!! tip "Check tile count first"
    Always run **Find KyFromAbove Tiles** before a large download. This lets you see the footprints on the map, check the attribute table for file sizes, and select a subset if needed.

!!! tip "Use the correct coordinate system"
    KyFromAbove data uses **EPSG:3089** (Kentucky Single Zone, US Survey Feet). When the tools add data to your map, Pro will reproject on-the-fly if your map uses a different coordinate system. For best performance, set your map's coordinate system to EPSG:3089.

!!! tip "Pro 3.4+ STAC support"
    ArcGIS Pro 3.4+ has a built-in **Explore STAC** pane that can connect to the KyFromAbove STAC API directly. The AbovePro toolbox complements it by providing Kentucky-specific shortcuts (county lookup, one-click hillshade) that the generic STAC browser does not offer.

!!! note "Troubleshooting in Pro"
    If you encounter errors:

    - Check the **Messages** window at the bottom of the Geoprocessing pane for detailed error messages
    - Verify abovepy is installed in Pro's environment (see Installation above)
    - Ensure you have internet access (the tools query the KyFromAbove STAC API)
    - See the [Troubleshooting Guide](troubleshooting.md) for common issues and solutions

---

## Using abovepy in Pro's Python Window

You can also use abovepy directly in ArcGIS Pro's built-in Python window or Notebook:

```python
import abovepy

# Search for tiles
tiles = abovepy.search(county="Fayette", product="dem_phase3")
print(f"Found {len(tiles)} tiles")

# Download
paths = abovepy.download(tiles, output_dir=r"C:\Data\fayette_dem")

# Add to map using arcpy
import arcpy
for p in paths:
    arcpy.management.MakeRasterLayer(str(p), p.stem)
```

```text
Found 68 tiles
Downloading: 100%|██████████| 68/68 [03:42<00:00,  3.27s/file]
Downloaded 68 files
```

This gives you full programmatic control while still working within Pro's environment.

---

## Next steps

- [DEM + Hillshade Tutorial](dem-hillshade.md) — The same workflow in pure Python
- [Getting Started](../getting-started.md) — abovepy basics
- [Troubleshooting](troubleshooting.md) — Solutions for common issues

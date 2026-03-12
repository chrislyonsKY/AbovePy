# ArcGIS Pro Toolbox

Use abovepy inside ArcGIS Pro with the **AbovePro** Python Toolbox.

## Requirements

- ArcGIS Pro 3.2+
- abovepy installed in Pro's Python environment

## Installation

### Step 1: Install abovepy in Pro's conda environment

Open the **Python Command Prompt** from ArcGIS Pro and run:

```bash
pip install abovepy
```

!!! note
    ArcGIS Pro uses its own conda environment. Make sure you install abovepy there, not in a separate Python installation.

### Step 2: Add the toolbox to Pro

1. Open ArcGIS Pro
2. In the **Catalog** pane, right-click **Toolboxes**
3. Click **Add Toolbox**
4. Navigate to the `arcgis/AbovePro.pyt` file in the abovepy repository
5. Click **OK**

The **AbovePro** toolbox appears with five tools.

## Tools

### Find KyFromAbove Tiles

Search for tiles by extent and product type.

**Parameters:**

| Parameter | Description |
|---|---|
| Product | Dropdown: DEM Phase 1–3, Ortho Phase 1–3, LiDAR Phase 1–3 |
| Extent | Map extent, drawn rectangle, or layer extent |
| County (optional) | Kentucky county name — overrides extent |
| Max Tiles | Maximum tiles to return (default 500) |

**Output:** Feature layer of tile footprints added to the map.

### Download Tiles

Download selected tiles to a local folder.

**Parameters:**

| Parameter | Description |
|---|---|
| Tiles | Feature layer from Find Tiles, or a GeoDataFrame |
| Output Directory | Local folder for downloaded files |
| Overwrite | Re-download existing files (default: No) |

**Output:** Downloaded files in the output directory, with a progress bar.

### Download and Load

Combines search + download + add-to-map in one step.

**Parameters:**

| Parameter | Description |
|---|---|
| Product | Product dropdown |
| Extent / County | Search area |
| Output Directory | Download folder |

**Output:** Downloaded rasters added directly to the active map as a group layer.

### DEM Hillshade

Automated DEM-to-hillshade workflow — the signature tool.

**Parameters:**

| Parameter | Description |
|---|---|
| DEM Product | DEM Phase 1, 2, or 3 |
| Extent / County | Area of interest |
| Output Directory | Download folder |
| Azimuth | Sun azimuth in degrees (default 315) |
| Altitude | Sun altitude in degrees (default 45) |

**Output:** Hillshade raster added to the map with appropriate symbology.

This tool runs the full pipeline: search → download → mosaic → hillshade → add to map.

### County Download

Download all tiles for a county in one click.

**Parameters:**

| Parameter | Description |
|---|---|
| County | Dropdown of all 120 Kentucky counties |
| Product | Product dropdown |
| Output Directory | Download folder |

**Output:** All tiles for the selected county downloaded to the output directory.

## Tips

!!! tip "Persistent toolbox"
    To make AbovePro available in every project, add the toolbox path to your **Favorites** in the Catalog pane.

!!! tip "Large downloads"
    For county-wide downloads, check the tile count first with **Find KyFromAbove Tiles** before running **County Download**. Some counties have hundreds of tiles.

!!! tip "Pro 3.4+ STAC support"
    ArcGIS Pro 3.4+ has a built-in **Explore STAC** pane. The AbovePro toolbox complements it by providing Kentucky-specific shortcuts (county lookup, one-click hillshade) that the generic STAC browser doesn't offer.

# -*- coding: utf-8 -*-
"""Shared parameter utilities for AbovePro geoprocessing tools.

Provides common parameter definitions, value lists, and conversion
helpers used across multiple tools.
"""

import arcpy

# Alphabetical Kentucky county list for dropdown parameters
KY_COUNTY_LIST = [
    "Adair", "Allen", "Anderson", "Ballard", "Barren", "Bath", "Bell",
    "Boone", "Bourbon", "Boyd", "Boyle", "Bracken", "Breathitt",
    "Breckinridge", "Bullitt", "Butler", "Caldwell", "Calloway",
    "Campbell", "Carlisle", "Carroll", "Carter", "Casey", "Christian",
    "Clark", "Clay", "Clinton", "Crittenden", "Cumberland", "Daviess",
    "Edmonson", "Elliott", "Estill", "Fayette", "Fleming", "Floyd",
    "Franklin", "Fulton", "Gallatin", "Garrard", "Grant", "Graves",
    "Grayson", "Green", "Greenup", "Hancock", "Hardin", "Harlan",
    "Harrison", "Hart", "Henderson", "Henry", "Hickman", "Hopkins",
    "Jackson", "Jefferson", "Jessamine", "Johnson", "Kenton", "Knott",
    "Knox", "Larue", "Laurel", "Lawrence", "Lee", "Leslie", "Letcher",
    "Lewis", "Lincoln", "Livingston", "Logan", "Lyon", "Madison",
    "Magoffin", "Marion", "Marshall", "Martin", "Mason", "McCracken",
    "McCreary", "McLean", "Meade", "Menifee", "Mercer", "Metcalfe",
    "Monroe", "Montgomery", "Morgan", "Muhlenberg", "Nelson", "Nicholas",
    "Ohio", "Oldham", "Owen", "Owsley", "Pendleton", "Perry", "Pike",
    "Powell", "Pulaski", "Robertson", "Rockcastle", "Rowan", "Russell",
    "Scott", "Shelby", "Simpson", "Spencer", "Taylor", "Todd", "Trigg",
    "Trimble", "Union", "Warren", "Washington", "Wayne", "Webster",
    "Whitley", "Wolfe", "Woodford",
]

# Product display names -> abovepy product keys
PRODUCT_MAP = {
    "DEM Phase 1 (5ft)": "dem_phase1",
    "DEM Phase 2 (2ft)": "dem_phase2",
    "DEM Phase 3 (2ft)": "dem_phase3",
    "Orthoimagery Phase 1 (6-inch)": "ortho_phase1",
    "Orthoimagery Phase 2 (6-inch)": "ortho_phase2",
    "Orthoimagery Phase 3 (3-inch)": "ortho_phase3",
    "LiDAR Point Cloud Phase 1 (LAZ)": "laz_phase1",
    "LiDAR Point Cloud Phase 2 (COPC)": "laz_phase2",
    "LiDAR Point Cloud Phase 3 (COPC)": "laz_phase3",
}

# DEM-only subset for hillshade tool
DEM_PRODUCTS = [
    "DEM Phase 1 (5ft)",
    "DEM Phase 2 (2ft)",
    "DEM Phase 3 (2ft)",
]


def make_county_param(required=True, default="Franklin"):
    """Create a county dropdown parameter.

    Parameters
    ----------
    required : bool
        Whether the parameter is required.
    default : str
        Default county value.

    Returns
    -------
    arcpy.Parameter
    """
    param = arcpy.Parameter(
        displayName="County",
        name="county",
        datatype="GPString",
        parameterType="Required" if required else "Optional",
        direction="Input",
    )
    param.filter.type = "ValueList"
    param.filter.list = KY_COUNTY_LIST if required else [""] + KY_COUNTY_LIST
    if default:
        param.value = default
    return param


def make_product_param(products=None, default="DEM Phase 3 (2ft)"):
    """Create a product type dropdown parameter.

    Parameters
    ----------
    products : list, optional
        Product display names. Defaults to all products.
    default : str
        Default product value.

    Returns
    -------
    arcpy.Parameter
    """
    product_list = products or list(PRODUCT_MAP.keys())
    param = arcpy.Parameter(
        displayName="Product Type",
        name="product_type",
        datatype="GPString",
        parameterType="Required",
        direction="Input",
    )
    param.filter.type = "ValueList"
    param.filter.list = product_list
    param.value = default
    return param


def make_output_folder_param():
    """Create an output folder parameter.

    Returns
    -------
    arcpy.Parameter
    """
    return arcpy.Parameter(
        displayName="Output Folder",
        name="out_folder",
        datatype="DEFolder",
        parameterType="Required",
        direction="Input",
    )


def make_add_to_map_param(default=True):
    """Create an 'Add to Map' boolean parameter.

    Parameters
    ----------
    default : bool
        Default value.

    Returns
    -------
    arcpy.Parameter
    """
    param = arcpy.Parameter(
        displayName="Add to Map",
        name="add_to_map",
        datatype="GPBoolean",
        parameterType="Optional",
        direction="Input",
    )
    param.value = default
    return param


def extent_to_bbox_4326(extent):
    """Convert an ArcGIS Extent to an EPSG:4326 bbox tuple.

    Parameters
    ----------
    extent : arcpy.Extent
        ArcGIS extent object.

    Returns
    -------
    tuple
        (xmin, ymin, xmax, ymax) in EPSG:4326.
    """
    sr_4326 = arcpy.SpatialReference(4326)
    projected = extent.projectAs(sr_4326)
    return (projected.XMin, projected.YMin, projected.XMax, projected.YMax)


def add_paths_to_map(paths, group_name=None):
    """Add downloaded tile paths to the active ArcGIS Pro map.

    Parameters
    ----------
    paths : list[Path]
        File paths to add.
    group_name : str, optional
        Name for a group layer. If None, adds directly.
    """
    try:
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        active_map = aprx.activeMap
        if active_map is None:
            arcpy.AddWarning("No active map found.")
            return
        for path in paths:
            active_map.addDataFromPath(str(path))
        arcpy.AddMessage("Added {} layers to map.".format(len(paths)))
    except Exception as e:
        arcpy.AddWarning("Could not add to map: {}".format(e))

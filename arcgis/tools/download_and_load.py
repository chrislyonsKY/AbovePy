# -*- coding: utf-8 -*-
"""Download and Load — download KyFromAbove tiles and add to map.

One-click workflow: search by extent or county, download tiles,
and add them to the active map.
"""

import arcpy


class DownloadAndLoad:
    """Download KyFromAbove tiles and add them to the active map.

    Combines search, download, and map loading into a single tool.
    Pick a county or draw an extent, choose a product, run.
    """

    def __init__(self):
        self.label = "Download and Load KyFromAbove Tiles"
        self.description = (
            "Download KyFromAbove tiles and add them to the current map. "
            "Search by extent or county name."
        )
        self.canRunInBackground = True
        self.category = "KyFromAbove"

    def getParameterInfo(self):
        param_extent = arcpy.Parameter(
            displayName="Area of Interest (Map Extent)",
            name="in_extent",
            datatype="GPExtent",
            parameterType="Optional",
            direction="Input",
        )

        param_county = arcpy.Parameter(
            displayName="Or Select County",
            name="county",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
        )
        param_county.filter.type = "ValueList"
        from utils.parameters import KY_COUNTY_LIST
        param_county.filter.list = [""] + KY_COUNTY_LIST

        param_product = arcpy.Parameter(
            displayName="Product Type",
            name="product_type",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
        )
        param_product.filter.type = "ValueList"
        from utils.parameters import PRODUCT_MAP
        param_product.filter.list = list(PRODUCT_MAP.keys())
        param_product.value = "DEM Phase 3 (2ft)"

        param_folder = arcpy.Parameter(
            displayName="Output Folder",
            name="out_folder",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input",
        )

        return [param_extent, param_county, param_product, param_folder]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        extent = parameters[0].value
        county = parameters[1].valueAsText
        if not extent and not county:
            parameters[0].setErrorMessage(
                "Provide a map extent or select a county."
            )
        return

    def execute(self, parameters, messages):
        try:
            import abovepy
        except ImportError:
            arcpy.AddError(
                "The 'abovepy' package is not installed. "
                "Install with: pip install abovepy"
            )
            return

        from utils.parameters import PRODUCT_MAP, extent_to_bbox_4326, add_paths_to_map

        extent = parameters[0].value
        county = parameters[1].valueAsText
        product_display = parameters[2].valueAsText
        out_folder = parameters[3].valueAsText

        product_key = PRODUCT_MAP.get(product_display)

        # Search
        arcpy.SetProgressor("default", "Querying STAC catalog...")
        try:
            if county:
                arcpy.AddMessage(
                    "Searching {} County for {} tiles...".format(
                        county, product_display
                    )
                )
                tiles = abovepy.search(county=county, product=product_key)
            else:
                bbox = extent_to_bbox_4326(extent)
                arcpy.AddMessage(
                    "Searching extent for {} tiles...".format(product_display)
                )
                tiles = abovepy.search(bbox=bbox, product=product_key)
        except Exception as e:
            arcpy.AddError("Search failed: {}".format(e))
            return

        if tiles.empty:
            arcpy.AddWarning("No tiles found.")
            return

        # Download
        tile_count = len(tiles)
        arcpy.AddMessage("Found {} tiles. Downloading...".format(tile_count))
        arcpy.SetProgressor("step", "Downloading tiles...", 0, tile_count, 1)

        try:
            paths = abovepy.download(tiles, output_dir=out_folder)
        except Exception as e:
            arcpy.AddError("Download failed: {}".format(e))
            return

        arcpy.AddMessage(
            "Downloaded {} tiles to {}".format(len(paths), out_folder)
        )

        # Add to map
        if paths:
            add_paths_to_map(paths)

        arcpy.ResetProgressor()

    def postExecute(self, parameters):
        return

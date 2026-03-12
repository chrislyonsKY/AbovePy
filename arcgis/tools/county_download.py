# -*- coding: utf-8 -*-
"""County Download — Download KyFromAbove data by county name.

This is the tool ArcGIS Pro doesn't have. Pick a county from a dropdown,
pick a product, click Run. No bbox drawing, no STAC URLs, no collection IDs.
"""

import arcpy


class CountyDownload:
    """Download KyFromAbove data for an entire county.

    Pick a county from a dropdown, pick a product, and download all
    matching tiles. The tool ArcGIS Pro's native STAC browser doesn't provide.
    """

    def __init__(self):
        self.label = "Download KyFromAbove by County"
        self.description = (
            "Download KyFromAbove tiles for a Kentucky county. "
            "Pick a county from the dropdown — no bbox drawing required."
        )
        self.canRunInBackground = True
        self.category = "KyFromAbove"

    def getParameterInfo(self):
        from utils.parameters import (
            make_county_param,
            make_product_param,
            make_output_folder_param,
            make_add_to_map_param,
        )

        return [
            make_county_param(),
            make_product_param(),
            make_output_folder_param(),
            make_add_to_map_param(),
        ]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
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

        from utils.parameters import PRODUCT_MAP, add_paths_to_map

        county = parameters[0].valueAsText
        product_display = parameters[1].valueAsText
        product_key = PRODUCT_MAP.get(product_display)
        out_folder = parameters[2].valueAsText
        add_to_map = parameters[3].value

        arcpy.AddMessage("Searching for {} tiles in {} County...".format(
            product_display, county))
        arcpy.SetProgressor("default", "Querying STAC catalog...")

        try:
            tiles = abovepy.search(county=county, product=product_key)
        except Exception as e:
            arcpy.AddError("Search failed: {}".format(e))
            return

        if tiles.empty:
            arcpy.AddWarning("No tiles found for {} County.".format(county))
            return

        tile_count = len(tiles)
        arcpy.AddMessage("Found {} tiles. Downloading...".format(tile_count))
        arcpy.SetProgressor("step", "Downloading tiles...", 0, tile_count, 1)

        try:
            paths = abovepy.download(tiles, output_dir=out_folder)
        except Exception as e:
            arcpy.AddError("Download failed: {}".format(e))
            return

        arcpy.AddMessage("Downloaded {} tiles to {}".format(len(paths), out_folder))

        if add_to_map and paths:
            add_paths_to_map(paths)

        arcpy.ResetProgressor()

    def postExecute(self, parameters):
        return

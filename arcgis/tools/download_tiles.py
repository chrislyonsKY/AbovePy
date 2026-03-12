# -*- coding: utf-8 -*-
"""Download Tiles — download KyFromAbove tiles by extent.

Search by map extent, then download matching tiles with progress
tracking and skip-existing support.
"""

import arcpy


class DownloadTiles:
    """Download KyFromAbove tiles for a map extent.

    Draw an extent, pick a product, and download all matching tiles
    with progress tracking. Skips files already on disk.
    """

    def __init__(self):
        self.label = "Download KyFromAbove Tiles"
        self.description = (
            "Download KyFromAbove tiles for a map extent. "
            "Supports progress tracking and skip-existing."
        )
        self.canRunInBackground = True
        self.category = "KyFromAbove"

    def getParameterInfo(self):
        param_extent = arcpy.Parameter(
            displayName="Download Extent",
            name="in_extent",
            datatype="GPExtent",
            parameterType="Required",
            direction="Input",
        )

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

        param_overwrite = arcpy.Parameter(
            displayName="Overwrite Existing Files",
            name="overwrite",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input",
        )
        param_overwrite.value = False

        return [param_extent, param_product, param_folder, param_overwrite]

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

        from utils.parameters import PRODUCT_MAP, extent_to_bbox_4326

        extent = parameters[0].value
        product_display = parameters[1].valueAsText
        out_folder = parameters[2].valueAsText
        overwrite = parameters[3].value or False

        product_key = PRODUCT_MAP.get(product_display)
        bbox = extent_to_bbox_4326(extent)

        arcpy.SetProgressor("default", "Querying STAC catalog...")
        arcpy.AddMessage("Searching for {} tiles...".format(product_display))

        try:
            tiles = abovepy.search(bbox=bbox, product=product_key)
        except Exception as e:
            arcpy.AddError("Search failed: {}".format(e))
            return

        if tiles.empty:
            arcpy.AddWarning("No tiles found in the specified extent.")
            return

        tile_count = len(tiles)
        arcpy.AddMessage("Found {} tiles. Downloading...".format(tile_count))
        arcpy.SetProgressor("step", "Downloading tiles...", 0, tile_count, 1)

        try:
            paths = abovepy.download(
                tiles, output_dir=out_folder, overwrite=overwrite
            )
        except Exception as e:
            arcpy.AddError("Download failed: {}".format(e))
            return

        arcpy.AddMessage(
            "Downloaded {} tiles to {}".format(len(paths), out_folder)
        )
        arcpy.ResetProgressor()

    def postExecute(self, parameters):
        return

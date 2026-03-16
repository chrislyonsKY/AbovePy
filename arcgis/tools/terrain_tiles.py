# -*- coding: utf-8 -*-
"""Terrain Tile Service — server-side DEM analysis via TiTiler-pgSTAC.

Generate hillshade, slope, contour, or terrain RGB tile URLs directly
from the cloud — no downloads required. Opens the result in a browser
or copies the TileJSON URL for use in ArcGIS Pro or web maps.
"""

import webbrowser

import arcpy


class TerrainTiles:
    """Generate terrain analysis tile URLs from KyFromAbove DEMs.

    Server-side processing via TiTiler — no data download needed.
    Pick an algorithm, define your area, and get a live tile service URL.
    """

    def __init__(self):
        self.label = "Terrain Tile Service"
        self.description = (
            "Generate server-side terrain analysis tiles (hillshade, slope, "
            "contours, terrain RGB) from KyFromAbove DEMs via TiTiler. "
            "No download required."
        )
        self.canRunInBackground = True
        self.category = "KyFromAbove"

    def getParameterInfo(self):
        from utils.parameters import (
            DEM_PRODUCTS,
            KY_COUNTY_LIST,
            TERRAIN_ALGORITHMS,
        )

        param_algorithm = arcpy.Parameter(
            displayName="Terrain Algorithm",
            name="algorithm",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
        )
        param_algorithm.filter.type = "ValueList"
        param_algorithm.filter.list = TERRAIN_ALGORITHMS
        param_algorithm.value = "Hillshade"

        param_dem = arcpy.Parameter(
            displayName="DEM Product",
            name="dem_product",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
        )
        param_dem.filter.type = "ValueList"
        param_dem.filter.list = DEM_PRODUCTS
        param_dem.value = "DEM Phase 3 (2ft)"

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
        param_county.filter.list = [""] + KY_COUNTY_LIST

        param_azimuth = arcpy.Parameter(
            displayName="Azimuth (Hillshade only)",
            name="azimuth",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input",
        )
        param_azimuth.value = 315

        param_altitude = arcpy.Parameter(
            displayName="Altitude (Hillshade only)",
            name="altitude",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input",
        )
        param_altitude.value = 45

        param_open_browser = arcpy.Parameter(
            displayName="Open Map in Browser",
            name="open_browser",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input",
        )
        param_open_browser.value = True

        param_out_url = arcpy.Parameter(
            displayName="Output TileJSON URL",
            name="out_url",
            datatype="GPString",
            parameterType="Derived",
            direction="Output",
        )

        return [
            param_algorithm, param_dem, param_extent, param_county,
            param_azimuth, param_altitude, param_open_browser, param_out_url,
        ]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        extent = parameters[2].value
        county = parameters[3].valueAsText
        if not extent and not county:
            parameters[2].setErrorMessage(
                "Provide a map extent or select a county."
            )
        return

    def execute(self, parameters, messages):
        try:
            from abovepy.titiler import (
                collection_map_url,
                contour_tile_url,
                hillshade_tile_url,
                slope_tile_url,
                terrain_rgb_tile_url,
            )
        except ImportError:
            arcpy.AddError(
                "The 'abovepy' package is not installed. "
                "Install with: pip install abovepy"
            )
            return

        from utils.parameters import PRODUCT_MAP, extent_to_bbox_4326

        algorithm_display = parameters[0].valueAsText
        dem_display = parameters[1].valueAsText
        extent = parameters[2].value
        county = parameters[3].valueAsText
        azimuth = parameters[4].value or 315
        altitude = parameters[5].value or 45
        open_browser = parameters[6].value

        product_key = PRODUCT_MAP.get(dem_display)

        # Resolve bbox
        bbox = None
        if county:
            arcpy.AddMessage("Using {} County bounds.".format(county))
        elif extent:
            bbox = extent_to_bbox_4326(extent)

        # Build kwargs
        kwargs = {"bbox": bbox} if bbox else {}
        if county:
            from abovepy.utils.bbox import county_bbox
            kwargs["bbox"] = county_bbox(county)

        # Map algorithm display names to URL builders
        builders = {
            "Hillshade": hillshade_tile_url,
            "Slope": slope_tile_url,
            "Contours": contour_tile_url,
            "Terrain RGB": terrain_rgb_tile_url,
        }

        builder = builders[algorithm_display]
        arcpy.SetProgressor("default", "Generating {} tile URL...".format(
            algorithm_display
        ))

        try:
            if algorithm_display == "Hillshade":
                tile_url = builder(
                    product_key, azimuth=azimuth, altitude=altitude, **kwargs
                )
            else:
                tile_url = builder(product_key, **kwargs)
        except Exception as e:
            arcpy.AddError("Failed to generate tile URL: {}".format(e))
            return

        arcpy.AddMessage("Algorithm: {}".format(algorithm_display))
        arcpy.AddMessage("TileJSON URL: {}".format(tile_url))

        # Set derived output
        parameters[7].value = tile_url

        # Open interactive map in browser
        if open_browser:
            try:
                map_url = collection_map_url(product_key)
                arcpy.AddMessage("Opening map viewer in browser...")
                webbrowser.open(map_url)
            except Exception as e:
                arcpy.AddWarning("Could not open browser: {}".format(e))

        arcpy.ResetProgressor()

    def postExecute(self, parameters):
        return

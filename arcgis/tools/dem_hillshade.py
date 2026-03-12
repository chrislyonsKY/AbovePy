# -*- coding: utf-8 -*-
"""DEM Hillshade — Automated DEM download, mosaic, and hillshade generation.

The full workflow in one tool: search -> download -> mosaic -> hillshade.
This is the domain-specific workflow Pro's STAC browser cannot do.
"""

import os

import arcpy


class DEMHillshade:
    """Generate a hillshade from KyFromAbove DEM tiles."""

    def __init__(self):
        self.label = "Generate KyFromAbove Hillshade"
        self.description = (
            "Download DEM tiles, mosaic them, and generate a hillshade. "
            "Complete workflow from county name to rendered hillshade."
        )
        self.canRunInBackground = True
        self.category = "KyFromAbove"

    def getParameterInfo(self):
        param_extent = arcpy.Parameter(
            displayName="Area of Interest",
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

        param_dem = arcpy.Parameter(
            displayName="DEM Product",
            name="dem_product",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
        )
        param_dem.filter.type = "ValueList"
        from utils.parameters import DEM_PRODUCTS
        param_dem.filter.list = DEM_PRODUCTS
        param_dem.value = "DEM Phase 3 (2ft)"

        param_out_dem = arcpy.Parameter(
            displayName="Output DEM",
            name="out_dem",
            datatype="DERasterDataset",
            parameterType="Required",
            direction="Output",
        )

        param_out_hillshade = arcpy.Parameter(
            displayName="Output Hillshade",
            name="out_hillshade",
            datatype="DERasterDataset",
            parameterType="Required",
            direction="Output",
        )

        param_azimuth = arcpy.Parameter(
            displayName="Azimuth (degrees)",
            name="azimuth",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input",
        )
        param_azimuth.value = 315

        param_altitude = arcpy.Parameter(
            displayName="Altitude (degrees)",
            name="altitude",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input",
        )
        param_altitude.value = 45

        return [
            param_extent, param_county, param_dem,
            param_out_dem, param_out_hillshade,
            param_azimuth, param_altitude,
        ]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        extent = parameters[0].value
        county = parameters[1].valueAsText
        if not extent and not county:
            parameters[0].setErrorMessage("Provide an extent or select a county.")
        return

    def execute(self, parameters, messages):
        try:
            import abovepy
        except ImportError:
            arcpy.AddError("Install abovepy: pip install abovepy")
            return

        from utils.parameters import PRODUCT_MAP, extent_to_bbox_4326

        extent = parameters[0].value
        county = parameters[1].valueAsText
        dem_display = parameters[2].valueAsText
        out_dem = parameters[3].valueAsText
        out_hillshade = parameters[4].valueAsText
        azimuth = parameters[5].value or 315
        altitude = parameters[6].value or 45

        product_key = PRODUCT_MAP.get(dem_display)

        # Step 1: Search
        arcpy.SetProgressor("default", "Searching for DEM tiles...")
        try:
            if county:
                arcpy.AddMessage(
                    "Searching {} County for {} tiles...".format(county, dem_display)
                )
                tiles = abovepy.search(county=county, product=product_key)
            else:
                bbox = extent_to_bbox_4326(extent)
                tiles = abovepy.search(bbox=bbox, product=product_key)
        except Exception as e:
            arcpy.AddError("Search failed: {}".format(e))
            return

        if tiles.empty:
            arcpy.AddWarning("No DEM tiles found.")
            return

        tile_count = len(tiles)
        arcpy.AddMessage("Found {} DEM tiles.".format(tile_count))

        # Step 2: Download to scratch folder
        scratch_folder = os.path.join(arcpy.env.scratchFolder, "abovepy_dem")
        arcpy.SetProgressor("step", "Downloading DEM tiles...", 0, tile_count, 1)
        try:
            paths = abovepy.download(tiles, output_dir=scratch_folder)
        except Exception as e:
            arcpy.AddError("Download failed: {}".format(e))
            return

        arcpy.AddMessage("Downloaded {} tiles.".format(len(paths)))

        # Step 3: Mosaic to output DEM
        arcpy.SetProgressor("default", "Mosaicking DEM tiles...")
        arcpy.AddMessage("Mosaicking tiles to {}...".format(out_dem))
        try:
            abovepy.mosaic(paths, output=out_dem)
        except Exception as e:
            arcpy.AddError("Mosaic failed: {}".format(e))
            return

        # Step 4: Generate hillshade
        arcpy.SetProgressor("default", "Generating hillshade...")
        arcpy.AddMessage("Generating hillshade (azimuth={}, altitude={})...".format(
            azimuth, altitude
        ))
        try:
            arcpy.ddd.HillShade(out_dem, out_hillshade, azimuth, altitude)
        except Exception:
            try:
                # Fall back to Spatial Analyst if 3D Analyst unavailable
                hillshade_result = arcpy.sa.Hillshade(
                    out_dem, azimuth, altitude
                )
                hillshade_result.save(out_hillshade)
            except Exception as e:
                arcpy.AddError("Hillshade generation failed: {}".format(e))
                return

        arcpy.AddMessage("Hillshade saved to {}".format(out_hillshade))

        # Add to map
        try:
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            active_map = aprx.activeMap
            if active_map:
                active_map.addDataFromPath(out_hillshade)
                arcpy.AddMessage("Added hillshade to map.")
        except Exception as e:
            arcpy.AddWarning("Could not add to map: {}".format(e))

        arcpy.ResetProgressor()

    def postExecute(self, parameters):
        return

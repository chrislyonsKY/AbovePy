# -*- coding: utf-8 -*-
"""Browse Obliques — discover KyFromAbove Phase 3 oblique imagery on S3.

Lists available oblique frames by direction and season. Oblique imagery
is not yet in the STAC catalog, so this tool queries S3 directly.
"""

import arcpy


class BrowseObliques:
    """Browse KyFromAbove Phase 3 oblique imagery.

    Select a camera direction and season to discover available frames.
    Returns a table of frame IDs with S3 URLs for each image.
    """

    def __init__(self):
        self.label = "Browse Oblique Imagery"
        self.description = (
            "Discover KyFromAbove Phase 3 oblique imagery on S3. "
            "Select a direction and season to list available frames."
        )
        self.canRunInBackground = True
        self.category = "KyFromAbove"

    def getParameterInfo(self):
        from utils.parameters import OBLIQUE_DIRECTIONS

        param_direction = arcpy.Parameter(
            displayName="Camera Direction",
            name="direction",
            datatype="GPString",
            parameterType="Required",
            direction="Input",
        )
        param_direction.filter.type = "ValueList"
        param_direction.filter.list = OBLIQUE_DIRECTIONS
        param_direction.value = "Backward"

        param_season = arcpy.Parameter(
            displayName="Season (leave blank for most recent)",
            name="season",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
        )

        param_max_items = arcpy.Parameter(
            displayName="Maximum Frames",
            name="max_items",
            datatype="GPLong",
            parameterType="Optional",
            direction="Input",
        )
        param_max_items.value = 50

        param_out_table = arcpy.Parameter(
            displayName="Output Table",
            name="out_table",
            datatype="DETable",
            parameterType="Required",
            direction="Output",
        )

        return [param_direction, param_season, param_max_items, param_out_table]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        try:
            from abovepy.obliques import list_oblique_seasons, search_obliques
        except ImportError:
            arcpy.AddError(
                "The 'abovepy' package is not installed. "
                "Install with: pip install abovepy"
            )
            return

        from utils.parameters import OBLIQUE_DIRECTION_MAP

        direction_display = parameters[0].valueAsText
        season = parameters[1].valueAsText or None
        max_items = parameters[2].value or 50
        out_table = parameters[3].valueAsText

        direction_key = OBLIQUE_DIRECTION_MAP.get(direction_display)

        # List available seasons if user wants to see them
        arcpy.SetProgressor("default", "Querying S3 for oblique imagery...")
        try:
            if season is None:
                seasons = list_oblique_seasons()
                if seasons:
                    arcpy.AddMessage(
                        "Available seasons: {}".format(", ".join(seasons))
                    )
                    arcpy.AddMessage(
                        "Using most recent: {}".format(seasons[-1])
                    )
                else:
                    arcpy.AddWarning("No oblique seasons found on S3.")
                    return

            arcpy.AddMessage(
                "Searching for {} obliques...".format(direction_display)
            )
            frames = search_obliques(
                direction=direction_key,
                season=season,
                max_items=max_items,
            )
        except Exception as e:
            arcpy.AddError("Search failed: {}".format(e))
            return

        if not frames:
            arcpy.AddWarning("No oblique frames found.")
            return

        arcpy.AddMessage("Found {} frames.".format(len(frames)))

        # Create output table
        import os

        out_dir = os.path.dirname(out_table)
        out_name = os.path.basename(out_table)
        arcpy.management.CreateTable(out_dir, out_name)

        arcpy.management.AddField(out_table, "frame_id", "TEXT", field_length=100)
        arcpy.management.AddField(out_table, "direction", "TEXT", field_length=10)
        arcpy.management.AddField(out_table, "season", "TEXT", field_length=100)
        arcpy.management.AddField(out_table, "tif_url", "TEXT", field_length=500)
        arcpy.management.AddField(out_table, "json_url", "TEXT", field_length=500)

        with arcpy.da.InsertCursor(
            out_table,
            ["frame_id", "direction", "season", "tif_url", "json_url"],
        ) as cursor:
            for frame in frames:
                cursor.insertRow([
                    frame["frame_id"],
                    frame["direction"],
                    frame["season"],
                    frame["tif_url"],
                    frame["json_url"],
                ])

        arcpy.AddMessage("Oblique frame table saved to {}".format(out_table))
        arcpy.ResetProgressor()

    def postExecute(self, parameters):
        return

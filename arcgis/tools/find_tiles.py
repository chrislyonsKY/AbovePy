# -*- coding: utf-8 -*-
"""Find KyFromAbove Tiles — search by extent or county name.

Queries the STAC catalog and returns a tile index as a feature class.
No download required — just discover what tiles cover your area.
"""

import arcpy


class FindTiles:
    """Find KyFromAbove tiles covering an area of interest.

    Draw an extent on the map or pick a county from the dropdown.
    Returns a feature layer showing tile footprints with metadata.
    """

    def __init__(self):
        self.label = "Find KyFromAbove Tiles"
        self.description = (
            "Search for KyFromAbove tiles by map extent or county name. "
            "Returns tile footprints as a feature layer."
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

        param_out_fc = arcpy.Parameter(
            displayName="Output Feature Class",
            name="out_features",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Output",
        )

        return [param_extent, param_county, param_product, param_out_fc]

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

        from utils.parameters import PRODUCT_MAP, extent_to_bbox_4326

        extent = parameters[0].value
        county = parameters[1].valueAsText
        product_display = parameters[2].valueAsText
        out_fc = parameters[3].valueAsText

        product_key = PRODUCT_MAP.get(product_display)

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
            arcpy.AddWarning("No tiles found in the specified area.")
            return

        arcpy.AddMessage("Found {} tiles.".format(len(tiles)))

        # Convert GeoDataFrame to feature class
        sr_4326 = arcpy.SpatialReference(4326)
        arcpy.management.CreateFeatureclass(
            arcpy.env.scratchGDB,
            "temp_tiles",
            "POLYGON",
            spatial_reference=sr_4326,
        )
        temp_fc = arcpy.env.scratchGDB + "/temp_tiles"

        # Add fields
        arcpy.management.AddField(temp_fc, "tile_id", "TEXT", field_length=100)
        arcpy.management.AddField(temp_fc, "product", "TEXT", field_length=50)
        arcpy.management.AddField(temp_fc, "asset_url", "TEXT", field_length=500)
        arcpy.management.AddField(temp_fc, "collection_id", "TEXT", field_length=50)

        # Insert rows
        with arcpy.da.InsertCursor(
            temp_fc,
            ["SHAPE@", "tile_id", "product", "asset_url", "collection_id"],
        ) as cursor:
            for _, row in tiles.iterrows():
                geom = row.geometry
                coords = list(geom.exterior.coords)
                polygon = arcpy.Polygon(
                    arcpy.Array([arcpy.Point(x, y) for x, y in coords]),
                    sr_4326,
                )
                cursor.insertRow([
                    polygon,
                    str(row.get("tile_id", "")),
                    str(row.get("product", "")),
                    str(row.get("asset_url", "")),
                    str(row.get("collection_id", "")),
                ])

        arcpy.management.CopyFeatures(temp_fc, out_fc)
        arcpy.management.Delete(temp_fc)
        arcpy.AddMessage("Tile footprints saved to {}".format(out_fc))
        arcpy.ResetProgressor()

    def postExecute(self, parameters):
        return

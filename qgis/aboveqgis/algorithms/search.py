"""Search KyFromAbove Tiles — find tiles by county or map extent."""

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFeature,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterEnum,
    QgsProcessingParameterExtent,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterNumber,
    QgsWkbTypes,
)
from qgis.PyQt.QtCore import QVariant


# Kentucky counties (sorted) for the dropdown
COUNTIES = [
    "", "Adair", "Allen", "Anderson", "Ballard", "Barren", "Bath", "Bell",
    "Boone", "Bourbon", "Boyd", "Boyle", "Bracken", "Breathitt",
    "Breckinridge", "Bullitt", "Butler", "Caldwell", "Calloway", "Campbell",
    "Carlisle", "Carroll", "Carter", "Casey", "Christian", "Clark", "Clay",
    "Clinton", "Crittenden", "Cumberland", "Daviess", "Edmonson", "Elliott",
    "Estill", "Fayette", "Fleming", "Floyd", "Franklin", "Fulton",
    "Gallatin", "Garrard", "Grant", "Graves", "Grayson", "Green",
    "Greenup", "Hancock", "Hardin", "Harlan", "Harrison", "Hart",
    "Henderson", "Henry", "Hickman", "Hopkins", "Jackson", "Jefferson",
    "Jessamine", "Johnson", "Kenton", "Knott", "Knox", "Larue", "Laurel",
    "Lawrence", "Lee", "Leslie", "Letcher", "Lewis", "Lincoln",
    "Livingston", "Logan", "Lyon", "Madison", "Magoffin", "Marion",
    "Marshall", "Martin", "Mason", "McCracken", "McCreary", "McLean",
    "Meade", "Menifee", "Mercer", "Metcalfe", "Monroe", "Montgomery",
    "Morgan", "Muhlenberg", "Nelson", "Nicholas", "Ohio", "Oldham", "Owen",
    "Owsley", "Pendleton", "Perry", "Pike", "Powell", "Pulaski",
    "Robertson", "Rockcastle", "Rowan", "Russell", "Scott", "Shelby",
    "Simpson", "Spencer", "Taylor", "Todd", "Trigg", "Trimble", "Union",
    "Warren", "Washington", "Wayne", "Webster", "Whitley", "Wolfe",
    "Woodford",
]

PRODUCTS = [
    "dem_phase3", "dem_phase2", "dem_phase1",
    "ortho_phase3", "ortho_phase2", "ortho_phase1",
    "laz_phase3", "laz_phase2", "laz_phase1",
]


class SearchTilesAlgorithm(QgsProcessingAlgorithm):
    COUNTY = "COUNTY"
    EXTENT = "EXTENT"
    PRODUCT = "PRODUCT"
    MAX_ITEMS = "MAX_ITEMS"
    OUTPUT = "OUTPUT"

    def name(self):
        return "search_tiles"

    def displayName(self):  # noqa: N802
        return "Search KyFromAbove Tiles"

    def group(self):
        return "KyFromAbove"

    def groupId(self):  # noqa: N802
        return "kyfromabove"

    def shortHelpString(self):  # noqa: N802
        return (
            "Find KyFromAbove tiles by county name or map extent.\n\n"
            "Select a county from the dropdown OR draw/enter an extent. "
            "County takes priority if both are provided.\n\n"
            "Output is a vector layer with tile footprints and download URLs."
        )

    def createInstance(self):  # noqa: N802
        return SearchTilesAlgorithm()

    def initAlgorithm(self, config=None):  # noqa: N802
        self.addParameter(
            QgsProcessingParameterEnum(
                self.COUNTY,
                "County (leave blank to use extent)",
                options=COUNTIES,
                defaultValue=0,
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterExtent(
                self.EXTENT,
                "Search extent (used if no county selected)",
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.PRODUCT,
                "Product",
                options=PRODUCTS,
                defaultValue=0,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MAX_ITEMS,
                "Maximum tiles",
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=500,
                minValue=1,
                maxValue=5000,
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                "Search results",
                type=QgsProcessing.TypeVectorPolygon,
            )
        )

    def processAlgorithm(self, parameters, context, feedback):  # noqa: N802
        import abovepy

        county_idx = self.parameterAsEnum(parameters, self.COUNTY, context)
        county = COUNTIES[county_idx] if county_idx > 0 else None
        product = PRODUCTS[self.parameterAsEnum(parameters, self.PRODUCT, context)]
        max_items = self.parameterAsInt(parameters, self.MAX_ITEMS, context)

        # Resolve search area
        bbox = None
        if county:
            feedback.pushInfo(f"Searching {county} County for {product}...")
        else:
            extent = self.parameterAsExtent(
                parameters, self.EXTENT, context,
                crs=QgsCoordinateReferenceSystem("EPSG:4326"),
            )
            if extent.isNull():
                feedback.reportError("Provide either a county or an extent.")
                return {}
            bbox = (extent.xMinimum(), extent.yMinimum(),
                    extent.xMaximum(), extent.yMaximum())
            feedback.pushInfo(f"Searching bbox {bbox} for {product}...")

        # Run search
        result = abovepy.search(
            county=county,
            bbox=bbox,
            product=product,
            max_items=max_items,
        )

        feedback.pushInfo(f"Found {result.count} tile(s), ~{result.estimate_size()['total_mb']} MB")

        # Validate and report warnings
        warnings = result.validate()
        for w in warnings:
            feedback.pushWarning(w)

        # Build output fields
        fields = QgsFields()
        fields.append(QgsField("tile_id", QVariant.String))
        fields.append(QgsField("product", QVariant.String))
        fields.append(QgsField("datetime", QVariant.String))
        fields.append(QgsField("asset_url", QVariant.String))
        fields.append(QgsField("collection_id", QVariant.String))

        (sink, dest_id) = self.parameterAsSink(
            parameters, self.OUTPUT, context,
            fields, QgsWkbTypes.Polygon,
            QgsCoordinateReferenceSystem("EPSG:4326"),
        )

        if sink is None:
            return {}

        gdf = result.tiles
        for idx, row in gdf.iterrows():
            if feedback.isCanceled():
                break
            feat = QgsFeature(fields)
            feat["tile_id"] = str(row.get("tile_id", ""))
            feat["product"] = str(row.get("product", ""))
            feat["datetime"] = str(row.get("datetime", ""))
            feat["asset_url"] = str(row.get("asset_url", ""))
            feat["collection_id"] = str(row.get("collection_id", ""))

            geom = row.geometry
            if geom is not None:
                feat.setGeometry(QgsGeometry.fromWkt(geom.wkt))
            sink.addFeature(feat)

        return {self.OUTPUT: dest_id}

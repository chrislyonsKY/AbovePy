"""Hillshade Tile URL — generate a server-side hillshade URL for web maps."""

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsProcessingAlgorithm,
    QgsProcessingParameterEnum,
    QgsProcessingParameterExtent,
    QgsProcessingParameterNumber,
    QgsProcessingOutputString,
)

from .search import COUNTIES

DEM_PRODUCTS = ["dem_phase3", "dem_phase2", "dem_phase1"]


class HillshadeTileURLAlgorithm(QgsProcessingAlgorithm):
    COUNTY = "COUNTY"
    EXTENT = "EXTENT"
    PRODUCT = "PRODUCT"
    AZIMUTH = "AZIMUTH"
    ALTITUDE = "ALTITUDE"
    TILE_URL = "TILE_URL"

    def name(self):
        return "hillshade_tile_url"

    def displayName(self):  # noqa: N802
        return "Generate Hillshade Tile URL"

    def group(self):
        return "KyFromAbove"

    def groupId(self):  # noqa: N802
        return "kyfromabove"

    def shortHelpString(self):  # noqa: N802
        return (
            "Generate a TileJSON URL for server-side DEM hillshade.\n\n"
            "The URL can be used with QGIS XYZ Tiles, MapLibre, or Leaflet. "
            "No data download required — hillshade is computed on-the-fly "
            "by the TiTiler-pgSTAC server.\n\n"
            "Select a county or extent and DEM product to get started."
        )

    def createInstance(self):  # noqa: N802
        return HillshadeTileURLAlgorithm()

    def initAlgorithm(self, config=None):  # noqa: N802
        self.addParameter(
            QgsProcessingParameterEnum(
                self.COUNTY,
                "County",
                options=COUNTIES,
                defaultValue=0,
                optional=False,
            )
        )
        extent_param = QgsProcessingParameterExtent(
            self.EXTENT,
            "Extent (only used when county is not selected)",
            optional=True,
        )
        extent_param.setHelp(
            "Bounding box for the hillshade. Use 'Use Map Canvas Extent' "
            "to match your current map view. Only used when no county is selected."
        )
        self.addParameter(extent_param)

        product_param = QgsProcessingParameterEnum(
            self.PRODUCT,
            "DEM product",
            options=DEM_PRODUCTS,
            defaultValue=0,
            optional=False,
        )
        product_param.setHelp(
            "DEM product for hillshade:\n"
            "- dem_phase3: 2ft resolution (2022-2025, recommended)\n"
            "- dem_phase2: 2ft resolution (2018-2020)\n"
            "- dem_phase1: 5ft resolution (2012-2014)"
        )
        self.addParameter(product_param)

        azimuth_param = QgsProcessingParameterNumber(
            self.AZIMUTH,
            "Sun azimuth (degrees)",
            type=QgsProcessingParameterNumber.Double,
            defaultValue=315.0,
            minValue=0.0,
            maxValue=360.0,
        )
        azimuth_param.setHelp(
            "Direction of the light source in degrees clockwise from north. "
            "315 (northwest) is the cartographic standard."
        )
        self.addParameter(azimuth_param)

        altitude_param = QgsProcessingParameterNumber(
            self.ALTITUDE,
            "Sun altitude (degrees)",
            type=QgsProcessingParameterNumber.Double,
            defaultValue=45.0,
            minValue=0.0,
            maxValue=90.0,
        )
        altitude_param.setHelp(
            "Angle of the light source above the horizon. "
            "45 is a good default. Lower values create more dramatic shadows."
        )
        self.addParameter(altitude_param)

        self.addOutput(QgsProcessingOutputString(self.TILE_URL, "Tile URL"))

    def processAlgorithm(self, parameters, context, feedback):  # noqa: N802
        try:
            from abovepy.titiler import hillshade_tile_url
            from abovepy.utils.bbox import get_county_bbox
        except ImportError:
            feedback.reportError(
                "abovepy is not installed. Run: pip install abovepy\n"
                "in your QGIS Python environment."
            )
            return {}

        county_idx = self.parameterAsEnum(parameters, self.COUNTY, context)
        product = DEM_PRODUCTS[self.parameterAsEnum(parameters, self.PRODUCT, context)]
        azimuth = self.parameterAsDouble(parameters, self.AZIMUTH, context)
        altitude = self.parameterAsDouble(parameters, self.ALTITUDE, context)

        # Resolve bbox
        bbox = None
        if county_idx > 0:
            county = COUNTIES[county_idx]
            bbox = get_county_bbox(county)
            feedback.pushInfo(f"Using {county} County extent")
        else:
            try:
                extent = self.parameterAsExtent(
                    parameters, self.EXTENT, context,
                    crs=QgsCoordinateReferenceSystem("EPSG:4326"),
                )
                if extent is not None and not extent.isNull() and not extent.isEmpty():
                    bbox = (extent.xMinimum(), extent.yMinimum(),
                            extent.xMaximum(), extent.yMaximum())
            except Exception:
                pass

        try:
            url = hillshade_tile_url(
                collection=product,
                bbox=bbox,
                azimuth=azimuth,
                altitude=altitude,
            )
        except Exception as e:
            feedback.reportError(f"Failed to generate URL: {e}")
            return {}

        feedback.pushInfo(f"Hillshade TileJSON URL:\n{url}")
        feedback.pushInfo(
            "\nTo use in QGIS: Layer > Add Layer > Add XYZ Tiles, "
            "then paste the tiles URL from the TileJSON."
        )

        return {self.TILE_URL: url}

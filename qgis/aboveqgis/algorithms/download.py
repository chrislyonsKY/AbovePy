"""Download KyFromAbove Tiles — download tiles to a local directory."""

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsProcessingAlgorithm,
    QgsProcessingParameterEnum,
    QgsProcessingParameterExtent,
    QgsProcessingParameterFile,
    QgsProcessingParameterNumber,
    QgsProcessingOutputString,
)

from .search import COUNTIES, PRODUCTS


class DownloadTilesAlgorithm(QgsProcessingAlgorithm):
    COUNTY = "COUNTY"
    EXTENT = "EXTENT"
    PRODUCT = "PRODUCT"
    OUTPUT_DIR = "OUTPUT_DIR"
    MAX_ITEMS = "MAX_ITEMS"
    WORKERS = "WORKERS"
    RESULT_MSG = "RESULT_MSG"

    def name(self):
        return "download_tiles"

    def displayName(self):  # noqa: N802
        return "Download KyFromAbove Tiles"

    def group(self):
        return "KyFromAbove"

    def groupId(self):  # noqa: N802
        return "kyfromabove"

    def shortHelpString(self):  # noqa: N802
        return (
            "Search and download KyFromAbove tiles to a local directory.\n\n"
            "Select a county or draw an extent, pick a product, and choose "
            "an output folder. Downloads use concurrent transfers for speed."
        )

    def createInstance(self):  # noqa: N802
        return DownloadTilesAlgorithm()

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
            QgsProcessingParameterFile(
                self.OUTPUT_DIR,
                "Output directory",
                behavior=QgsProcessingParameterFile.Folder,
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
            QgsProcessingParameterNumber(
                self.WORKERS,
                "Concurrent downloads",
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=4,
                minValue=1,
                maxValue=16,
            )
        )
        self.addOutput(QgsProcessingOutputString(self.RESULT_MSG, "Result"))

    def processAlgorithm(self, parameters, context, feedback):  # noqa: N802
        import abovepy

        county_idx = self.parameterAsEnum(parameters, self.COUNTY, context)
        county = COUNTIES[county_idx] if county_idx > 0 else None
        product = PRODUCTS[self.parameterAsEnum(parameters, self.PRODUCT, context)]
        output_dir = self.parameterAsFile(parameters, self.OUTPUT_DIR, context)
        max_items = self.parameterAsInt(parameters, self.MAX_ITEMS, context)
        workers = self.parameterAsInt(parameters, self.WORKERS, context)

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

        # Search
        result = abovepy.search(
            county=county, bbox=bbox, product=product, max_items=max_items,
        )

        if result.empty:
            feedback.reportError("No tiles found.")
            return {self.RESULT_MSG: "No tiles found."}

        est = result.estimate_size()
        feedback.pushInfo(
            f"Found {est['tile_count']} tile(s), ~{est['total_mb']} MB. Downloading..."
        )

        # Download
        paths = result.download(
            output_dir=output_dir,
            max_workers=workers,
        )

        msg = f"Downloaded {len(paths)} file(s) to {output_dir}"
        feedback.pushInfo(msg)
        return {self.RESULT_MSG: msg}

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
                "County",
                options=COUNTIES,
                defaultValue=0,
                optional=False,
            )
        )
        self.addParameter(
            QgsProcessingParameterExtent(
                self.EXTENT,
                "Search extent (only used when county is not selected)",
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.PRODUCT,
                "Product",
                options=PRODUCTS,
                defaultValue=0,
                optional=False,
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
        try:
            import abovepy
        except ImportError:
            feedback.reportError(
                "abovepy is not installed. Run: pip install abovepy\n"
                "in your QGIS Python environment."
            )
            return {}

        county_idx = self.parameterAsEnum(parameters, self.COUNTY, context)
        product = PRODUCTS[self.parameterAsEnum(parameters, self.PRODUCT, context)]
        output_dir = self.parameterAsFile(parameters, self.OUTPUT_DIR, context)
        max_items = self.parameterAsInt(parameters, self.MAX_ITEMS, context)
        workers = self.parameterAsInt(parameters, self.WORKERS, context)

        # Resolve search area
        county = None
        bbox = None

        if county_idx > 0:
            county = COUNTIES[county_idx]
            feedback.pushInfo(f"Searching {county} County for {product}...")
        else:
            try:
                extent = self.parameterAsExtent(
                    parameters, self.EXTENT, context,
                    crs=QgsCoordinateReferenceSystem("EPSG:4326"),
                )
                if extent is not None and not extent.isNull() and not extent.isEmpty():
                    bbox = (extent.xMinimum(), extent.yMinimum(),
                            extent.xMaximum(), extent.yMaximum())
                else:
                    feedback.reportError(
                        "Select a county from the dropdown, or provide a map extent."
                    )
                    return {}
            except Exception:
                feedback.reportError(
                    "Select a county from the dropdown, or provide a map extent."
                )
                return {}

        # Search
        try:
            result = abovepy.search(
                county=county, bbox=bbox, product=product, max_items=max_items,
            )
        except Exception as e:
            feedback.reportError(f"Search failed: {e}")
            return {}

        if result.empty:
            msg = "No tiles found."
            feedback.reportError(msg)
            return {self.RESULT_MSG: msg}

        est = result.estimate_size()
        feedback.pushInfo(
            f"Found {est['tile_count']} tile(s), ~{est['total_mb']} MB. Downloading..."
        )

        # Download
        try:
            paths = result.download(
                output_dir=output_dir,
                max_workers=workers,
            )
        except Exception as e:
            feedback.reportError(f"Download failed: {e}")
            return {}

        msg = f"Downloaded {len(paths)} file(s) to {output_dir}"
        feedback.pushInfo(msg)
        return {self.RESULT_MSG: msg}

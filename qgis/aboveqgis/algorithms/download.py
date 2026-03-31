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
            "an output folder. Downloads use concurrent transfers for speed.\n\n"
            "Tip: Use the Search tool first to check tile count and "
            "estimated size before downloading."
        )

    def createInstance(self):  # noqa: N802
        return DownloadTilesAlgorithm()

    def initAlgorithm(self, config=None):  # noqa: N802
        county_param = QgsProcessingParameterEnum(
            self.COUNTY,
            "County",
            options=COUNTIES,
            defaultValue=0,
            optional=False,
        )
        county_param.setHelp(
            "Select a Kentucky county to download. All 120 counties are available. "
            "Choose '(use map extent instead)' to use the extent below."
        )
        self.addParameter(county_param)

        extent_param = QgsProcessingParameterExtent(
            self.EXTENT,
            "Search extent (only used when county is not selected)",
            optional=True,
        )
        extent_param.setHelp(
            "Draw or enter a bounding box to download. Only used when no "
            "county is selected. You can use 'Use Map Canvas Extent'."
        )
        self.addParameter(extent_param)

        product_param = QgsProcessingParameterEnum(
            self.PRODUCT,
            "Product",
            options=PRODUCTS,
            defaultValue=0,
            optional=False,
        )
        product_param.setHelp(
            "KyFromAbove data product to download. DEM tiles are ~5 MB each, "
            "ortho tiles are ~40-80 MB each, LiDAR tiles are ~100-150 MB each."
        )
        self.addParameter(product_param)

        outdir_param = QgsProcessingParameterFile(
            self.OUTPUT_DIR,
            "Output directory",
            behavior=QgsProcessingParameterFile.Folder,
        )
        outdir_param.setHelp(
            "Folder to save downloaded tiles. Files are organized into "
            "subdirectories by collection (e.g., dem-phase3/)."
        )
        self.addParameter(outdir_param)

        max_param = QgsProcessingParameterNumber(
            self.MAX_ITEMS,
            "Maximum tiles",
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=500,
            minValue=1,
            maxValue=5000,
        )
        max_param.setHelp(
            "Maximum number of tiles to download. Use the Search tool first "
            "to check tile count and estimated size before downloading."
        )
        self.addParameter(max_param)

        workers_param = QgsProcessingParameterNumber(
            self.WORKERS,
            "Concurrent downloads",
            type=QgsProcessingParameterNumber.Integer,
            defaultValue=8,
            minValue=1,
            maxValue=16,
        )
        workers_param.setHelp(
            "Number of simultaneous download threads. Higher values download "
            "faster but use more bandwidth. 8 is a good default for broadband."
        )
        self.addParameter(workers_param)

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

        if not output_dir:
            feedback.reportError("Please select an output directory.")
            return {}

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

        if feedback.isCanceled():
            return {}

        # Search
        feedback.setProgress(5)
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
        feedback.setProgress(10)

        if feedback.isCanceled():
            return {}

        # Download
        try:
            paths = result.download(
                output_dir=output_dir,
                max_workers=workers,
            )
        except Exception as e:
            feedback.reportError(f"Download failed: {e}")
            return {}

        feedback.setProgress(100)
        msg = f"Downloaded {len(paths)} file(s) to {output_dir}"
        feedback.pushInfo(msg)
        return {self.RESULT_MSG: msg}

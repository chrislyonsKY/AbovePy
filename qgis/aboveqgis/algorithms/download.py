"""Download KyFromAbove Tiles — download, auto-load, and style."""

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsProcessingAlgorithm,
    QgsProcessingParameterBoolean,
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

        load_param = QgsProcessingParameterBoolean(
            "LOAD_LAYERS",
            "Load downloaded tiles into project",
            defaultValue=True,
        )
        load_param.setHelp(
            "Automatically add downloaded rasters to the current QGIS project. "
            "DEM tiles get hillshade symbology applied automatically."
        )
        self.addParameter(load_param)

        hillshade_param = QgsProcessingParameterBoolean(
            "APPLY_HILLSHADE",
            "Apply hillshade styling to DEM tiles",
            defaultValue=True,
        )
        hillshade_param.setHelp(
            "When loading DEM tiles, automatically apply hillshade rendering "
            "instead of the default singleband gray. Only applies to DEM products."
        )
        self.addParameter(hillshade_param)

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

        feedback.setProgress(90)

        # Auto-load into project
        load_layers = self.parameterAsBool(parameters, "LOAD_LAYERS", context)
        apply_hillshade = self.parameterAsBool(parameters, "APPLY_HILLSHADE", context)
        is_dem = "dem" in product

        if load_layers and paths:
            from qgis.core import QgsProject, QgsRasterLayer

            loaded = 0
            for path in paths:
                path_str = str(path)
                if not path_str.lower().endswith((".tif", ".tiff")):
                    continue
                layer_name = path.stem if hasattr(path, "stem") else path_str.rsplit("/", 1)[-1]
                layer = QgsRasterLayer(path_str, layer_name)
                if not layer.isValid():
                    feedback.pushWarning(f"Could not load: {path_str}")
                    continue

                # Apply hillshade symbology for DEM products
                if apply_hillshade and is_dem:
                    renderer = layer.renderer()
                    if renderer is not None:
                        from qgis.core import QgsHillshadeRenderer
                        hs = QgsHillshadeRenderer(layer.dataProvider(), 1, 315.0, 45.0)
                        layer.setRenderer(hs)

                QgsProject.instance().addMapLayer(layer)
                loaded += 1

            feedback.pushInfo(f"Loaded {loaded} layer(s) into project")

        feedback.setProgress(100)
        msg = f"Downloaded {len(paths)} file(s) to {output_dir}"
        feedback.pushInfo(msg)
        return {self.RESULT_MSG: msg}

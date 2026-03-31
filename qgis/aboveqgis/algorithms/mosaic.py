"""Mosaic KyFromAbove Tiles — build a VRT or GeoTIFF from downloaded tiles."""

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
    QgsProcessingOutputString,
)


class MosaicTilesAlgorithm(QgsProcessingAlgorithm):
    INPUT_DIR = "INPUT_DIR"
    OUTPUT_FORMAT = "OUTPUT_FORMAT"
    OUTPUT_FILE = "OUTPUT_FILE"
    RESULT_MSG = "RESULT_MSG"

    FORMATS = ["VRT (virtual raster)", "GeoTIFF"]
    EXTENSIONS = [".vrt", ".tif"]

    def name(self):
        return "mosaic_tiles"

    def displayName(self):  # noqa: N802
        return "Mosaic KyFromAbove Tiles"

    def group(self):
        return "KyFromAbove"

    def groupId(self):  # noqa: N802
        return "kyfromabove"

    def shortHelpString(self):  # noqa: N802
        return (
            "Combine downloaded KyFromAbove tiles into a single raster.\n\n"
            "VRT (default) is zero-copy and fast. GeoTIFF creates a single "
            "merged file (larger, but portable).\n\n"
            "Point this at a directory of .tif files from the Download tool."
        )

    def createInstance(self):  # noqa: N802
        return MosaicTilesAlgorithm()

    def initAlgorithm(self, config=None):  # noqa: N802
        input_param = QgsProcessingParameterFile(
            self.INPUT_DIR,
            "Input directory (containing .tif tiles)",
            behavior=QgsProcessingParameterFile.Folder,
        )
        input_param.setHelp(
            "Folder containing downloaded .tif tiles. Subdirectories are "
            "searched recursively (works with hierarchical download layout)."
        )
        self.addParameter(input_param)

        fmt_param = QgsProcessingParameterEnum(
            self.OUTPUT_FORMAT,
            "Output format",
            options=self.FORMATS,
            defaultValue=0,
        )
        fmt_param.setHelp(
            "VRT is recommended — it's instant and doesn't duplicate data. "
            "GeoTIFF creates a single portable file but takes longer and "
            "uses more disk space."
        )
        self.addParameter(fmt_param)

        output_param = QgsProcessingParameterFileDestination(
            self.OUTPUT_FILE,
            "Output file",
            fileFilter="VRT files (*.vrt);;GeoTIFF files (*.tif)",
        )
        output_param.setHelp(
            "Path for the output mosaic. After creation, drag into QGIS to view."
        )
        self.addParameter(output_param)

        self.addOutput(QgsProcessingOutputString(self.RESULT_MSG, "Result"))

    def processAlgorithm(self, parameters, context, feedback):  # noqa: N802
        from pathlib import Path

        try:
            import abovepy
        except ImportError:
            feedback.reportError(
                "abovepy is not installed. Run: pip install abovepy\n"
                "in your QGIS Python environment."
            )
            return {}

        input_dir = Path(self.parameterAsFile(parameters, self.INPUT_DIR, context))
        fmt_idx = self.parameterAsEnum(parameters, self.OUTPUT_FORMAT, context)
        output_file = self.parameterAsFileOutput(parameters, self.OUTPUT_FILE, context)

        if not input_dir.is_dir():
            feedback.reportError(f"Input directory does not exist: {input_dir}")
            return {}

        # Ensure output has correct extension
        ext = self.EXTENSIONS[fmt_idx]
        if not output_file.endswith(ext):
            output_file = output_file.rsplit(".", 1)[0] + ext

        feedback.pushInfo(f"Scanning {input_dir} for .tif files...")
        feedback.setProgress(10)

        # Find .tif files in the directory (including subdirectories)
        tif_files = sorted(input_dir.rglob("*.tif"))
        if not tif_files:
            feedback.reportError(f"No .tif files found in {input_dir}")
            return {self.RESULT_MSG: "No input files found."}

        feedback.pushInfo(f"Found {len(tif_files)} tile(s). Building mosaic...")
        feedback.setProgress(30)

        if feedback.isCanceled():
            return {}

        try:
            result = abovepy.mosaic(tif_files, output=output_file)
        except Exception as e:
            feedback.reportError(f"Mosaic failed: {e}")
            return {}

        feedback.setProgress(100)
        msg = f"Mosaic written to {result}"
        feedback.pushInfo(msg)
        return {self.RESULT_MSG: msg}

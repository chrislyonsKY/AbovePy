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
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT_DIR,
                "Input directory (containing .tif tiles)",
                behavior=QgsProcessingParameterFile.Folder,
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.OUTPUT_FORMAT,
                "Output format",
                options=self.FORMATS,
                defaultValue=0,
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT_FILE,
                "Output file",
                fileFilter="VRT files (*.vrt);;GeoTIFF files (*.tif)",
            )
        )
        self.addOutput(QgsProcessingOutputString(self.RESULT_MSG, "Result"))

    def processAlgorithm(self, parameters, context, feedback):  # noqa: N802
        from pathlib import Path

        import abovepy

        input_dir = Path(self.parameterAsFile(parameters, self.INPUT_DIR, context))
        fmt_idx = self.parameterAsEnum(parameters, self.OUTPUT_FORMAT, context)
        output_file = self.parameterAsFileOutput(parameters, self.OUTPUT_FILE, context)

        # Ensure output has correct extension
        ext = self.EXTENSIONS[fmt_idx]
        if not output_file.endswith(ext):
            output_file = output_file.rsplit(".", 1)[0] + ext

        # Find .tif files in the directory (including subdirectories)
        tif_files = sorted(input_dir.rglob("*.tif"))
        if not tif_files:
            feedback.reportError(f"No .tif files found in {input_dir}")
            return {self.RESULT_MSG: "No input files found."}

        feedback.pushInfo(f"Found {len(tif_files)} tile(s). Building mosaic...")

        result = abovepy.mosaic(tif_files, output=output_file)

        msg = f"Mosaic written to {result}"
        feedback.pushInfo(msg)
        return {self.RESULT_MSG: msg}

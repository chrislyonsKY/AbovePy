"""Load County Mosaic — stream a pre-built county ortho directly from S3."""

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterEnum,
    QgsProcessingOutputString,
)

from .search import COUNTIES


class LoadCountyMosaicAlgorithm(QgsProcessingAlgorithm):
    COUNTY = "COUNTY"
    FORMAT = "FORMAT"
    RESULT_MSG = "RESULT_MSG"

    FORMATS = ["MrSID (streamable, recommended for QGIS)", "TPKX (ArcGIS tile package)"]
    FORMAT_KEYS = ["mrsid", "tpkx"]

    def name(self):
        return "load_county_mosaic"

    def displayName(self):  # noqa: N802
        return "Load County Ortho Mosaic"

    def group(self):
        return "KyFromAbove"

    def groupId(self):  # noqa: N802
        return "kyfromabove"

    def shortHelpString(self):  # noqa: N802
        return (
            "Load a pre-built county orthoimagery mosaic directly from S3.\n\n"
            "KyFromAbove provides Phase 3 (3-inch) ortho mosaics for all "
            "120 Kentucky counties. MrSID files are streamed via the network "
            "— no download required. The layer appears in your project "
            "immediately.\n\n"
            "This is much faster than downloading individual tiles and "
            "mosaicking them yourself."
        )

    def createInstance(self):  # noqa: N802
        return LoadCountyMosaicAlgorithm()

    def initAlgorithm(self, config=None):  # noqa: N802
        county_param = QgsProcessingParameterEnum(
            self.COUNTY,
            "County",
            options=COUNTIES[1:],  # Skip the "(use map extent)" option
            defaultValue=0,
            optional=False,
        )
        county_param.setHelp(
            "Select a Kentucky county. The full 3-inch Phase 3 ortho mosaic "
            "will be streamed directly from S3 into your QGIS project."
        )
        self.addParameter(county_param)

        fmt_param = QgsProcessingParameterEnum(
            self.FORMAT,
            "Format",
            options=self.FORMATS,
            defaultValue=0,
            optional=False,
        )
        fmt_param.setHelp(
            "MrSID is recommended for QGIS — it streams efficiently over "
            "the network without downloading the entire file (18-110 GB). "
            "TPKX is for ArcGIS Pro users."
        )
        self.addParameter(fmt_param)

        self.addOutput(QgsProcessingOutputString(self.RESULT_MSG, "Result"))

    def processAlgorithm(self, parameters, context, feedback):  # noqa: N802
        try:
            from abovepy.mosaics import county_mosaic_url
        except ImportError:
            feedback.reportError(
                "abovepy is not installed. Run: pip install abovepy\n"
                "in your QGIS Python environment."
            )
            return {}

        county_idx = self.parameterAsEnum(parameters, self.COUNTY, context)
        county = COUNTIES[county_idx + 1]  # +1 because we skipped index 0
        fmt_idx = self.parameterAsEnum(parameters, self.FORMAT, context)
        fmt = self.FORMAT_KEYS[fmt_idx]

        feedback.pushInfo(f"Loading {county} County ortho mosaic ({fmt})...")

        try:
            url = county_mosaic_url(county, fmt=fmt)
        except Exception as e:
            feedback.reportError(f"Failed to build URL: {e}")
            return {}

        feedback.pushInfo(f"URL: {url}")
        feedback.setProgress(20)

        if fmt == "tpkx":
            feedback.pushInfo(
                f"TPKX URL generated. Download manually or open in ArcGIS Pro:\n{url}"
            )
            return {self.RESULT_MSG: url}

        # Stream MrSID into QGIS via /vsicurl/
        vsicurl_path = f"/vsicurl/{url}"

        try:
            from qgis.core import QgsProject, QgsRasterLayer

            layer_name = f"{county} County - Phase 3 Ortho"
            layer = QgsRasterLayer(vsicurl_path, layer_name)

            if not layer.isValid():
                # Try alternate year (2024 instead of 2023)
                feedback.pushInfo("Trying alternate year (2024)...")
                url_alt = county_mosaic_url(county, fmt="mrsid", year="2024")
                vsicurl_alt = f"/vsicurl/{url_alt}"
                layer = QgsRasterLayer(vsicurl_alt, layer_name)

            if not layer.isValid():
                feedback.reportError(
                    f"Could not load layer. The mosaic may not be available "
                    f"for {county} County yet.\n\nTried:\n  {url}\n  {url_alt}"
                )
                return {}

            QgsProject.instance().addMapLayer(layer)
            feedback.setProgress(100)

            msg = f"Loaded {county} County ortho mosaic (streaming from S3)"
            feedback.pushInfo(msg)
            return {self.RESULT_MSG: msg}

        except Exception as e:
            feedback.reportError(f"Failed to load layer: {e}")
            return {}

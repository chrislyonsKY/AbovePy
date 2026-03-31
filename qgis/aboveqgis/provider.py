"""AboveQGIS Processing provider — registers all algorithms."""

from qgis.core import QgsProcessingProvider

from .algorithms.download import DownloadTilesAlgorithm
from .algorithms.hillshade import HillshadeTileURLAlgorithm
from .algorithms.mosaic import MosaicTilesAlgorithm
from .algorithms.search import SearchTilesAlgorithm


class AboveQGISProvider(QgsProcessingProvider):
    """Processing provider for KyFromAbove data access."""

    def id(self):
        return "aboveqgis"

    def name(self):
        return "AboveQGIS — KyFromAbove"

    def longName(self):  # noqa: N802
        return "KyFromAbove LiDAR, DEM, and Orthoimagery Access"

    def icon(self):
        return QgsProcessingProvider.icon(self)

    def loadAlgorithms(self):  # noqa: N802
        self.addAlgorithm(SearchTilesAlgorithm())
        self.addAlgorithm(DownloadTilesAlgorithm())
        self.addAlgorithm(MosaicTilesAlgorithm())
        self.addAlgorithm(HillshadeTileURLAlgorithm())

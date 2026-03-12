# -*- coding: utf-8 -*-
"""AbovePro — KyFromAbove Data Access for ArcGIS Pro.

Requires: pip install abovepy
"""
import os, sys

_toolbox_dir = os.path.dirname(os.path.abspath(__file__))
if _toolbox_dir not in sys.path:
    sys.path.insert(0, _toolbox_dir)

from tools.find_tiles import FindTiles
from tools.download_tiles import DownloadTiles
from tools.download_and_load import DownloadAndLoad
from tools.county_download import CountyDownload
from tools.dem_hillshade import DEMHillshade


class Toolbox:
    def __init__(self):
        self.label = "AbovePro — KyFromAbove Data Access"
        self.alias = "abovepro"
        self.description = (
            "Access Kentucky's KyFromAbove data from ArcGIS Pro. "
            "DEMs, orthoimagery, and LiDAR point clouds. "
            "No credentials required."
        )
        self.tools = [
            FindTiles,
            DownloadTiles,
            DownloadAndLoad,
            CountyDownload,
            DEMHillshade,
        ]

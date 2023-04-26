from ticker.data.sec import Sec
from pathlib import Path
import os
import sys
import importlib
import pandas as pd


class Cli:

    """Tools for gathering resources, analyzing data, and publishing the results."""

    def analyze(self,
                tickers: list[str],
                cache_path: Path = Path(os.getcwd()) / ".ticker-cache",
                analysis_plugin: str = 'ticker.analysis') -> None:
        """ Perform stock analysis

        Args:
            tickers (list[str]): tickers to include in the analysis
            cache_path (Path): path where to cache data
            analysis_plugin (str): module to load for analysis
        """
        df = self._doUpdateFromSec(tickers, cache_path)

        # Call analysis plugin
        analysis_module = importlib.import_module(analysis_plugin)
        am = analysis_module.Analysis(df)
        am.analyze(tickers)

    def _doUpdateFromSec(self, tickers: list[str], cache_path: Path) -> pd.DataFrame:
        sec = Sec(storage_path=Path(cache_path))

        return sec.update(tickers=tickers)

    def export(self, tickers: list[str],
               cache_path: Path = Path(os.getcwd()) / ".ticker-cache",
               file: Path = None,
               json: Path = None,
               analysis_plugin: str = 'ticker.analysis') -> None:
        """ Create a report in one of the following formats based on data already analyzed

        Args:
            tickers (list[str]): tickers to include in the analysis
            cache_path (Path): path of cached data
            file (Path): text file containing the report. Defaults to None.
            json (Path): directory to store the reports in individual json files. Defaults to None.
            analysis_plugin (str): module to load for analysis
        """
        sec = Sec(storage_path=Path(cache_path))

        # Call analysis plugin
        analysis_module = importlib.import_module(analysis_plugin)
        am = analysis_module.Analysis(sec.data)
        am.report(tickers)

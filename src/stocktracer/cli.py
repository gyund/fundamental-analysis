import hashlib
import importlib
import logging
import os
from pathlib import Path

import pandas as pd
from diskcache import Cache

logger = logging.getLogger(__name__)


class Options:
    def __init__(self, tickers: frozenset[str], cache_path: Path):
        self.tickers = tickers
        self.cache_path = cache_path


class ReportOptions:
    def __init__(self, results, file: Path = None, json: Path = None, **kwargs):
        self.results = results
        self.file = file
        self.json = json


class Cli:

    """Tools for gathering resources, analyzing data, and publishing the results."""

    default_analysis_module = "ticker.analysis.stub"

    def getDefaultCachePath() -> Path:
        """Get the default path for caching data

        Returns:
            Path: path to cache data
        """
        return Path(os.getcwd()) / ".ticker-cache"

    def analyze(
        self,
        tickers: list[str],
        cache_path: Path = getDefaultCachePath(),
        refresh: bool = False,
        analysis_plugin: str = default_analysis_module,
    ) -> None:
        """Perform stock analysis

        Args:
            tickers (list[str]): tickers to include in the analysis
            cache_path (Path): path where to cache data
            refresh (bool): Whether to refresh the calculation or use the results from a prior one
            analysis_plugin (str): module to load for analysis
        """
        cache, results_key, results = self._getCachedResults(tickers, cache_path, analysis_plugin)

        if (
            refresh
            or results is None
            or not isinstance(results, pd.DataFrame)
            or results.empty()
        ):
            # Call analysis plugin
            tickers = frozenset(tickers)
            analysis_module = importlib.import_module(analysis_plugin)
            options = Options(tickers=tickers, cache_path=cache_path)
            results = analysis_module.analyze(options)
            # Save one week expiry
            cache.set(key=results_key, value=results, expire=3600 * 24 * 7)

        if isinstance(results, pd.DataFrame):
            print(results.to_markdown())
        else:
            print(results)

    def _getCachedResults(self, tickers, cache_path, analysis_plugin):
        cache = Cache(directory=cache_path / "results")
        results_key = Cli._get_results_key(frozenset(tickers), analysis_plugin)
        results = cache.get(key=results_key, default=None)
        return cache,results_key,results

    def _get_results_key(tickers: frozenset, analysis_module: str) -> str:
        """
        >>> Cli._get_results_key({"aapl","msft"},"my.analysis")
        'my.analysis-aapl-msft'
        """
        sorted_tickers = list(tickers)
        sorted_tickers.sort()
        results_key = "-".join(sorted_tickers)
        return "-".join((analysis_module, results_key))

    def export(
        self,
        tickers: list[str],
        cache_path: Path = getDefaultCachePath(),
        file: Path = None,
        json: Path = None,
        analysis_plugin: str = default_analysis_module,
    ) -> None:
        """Create a report in one of the following formats based on data already analyzed

        Args:
            tickers (list[str]): tickers to include in the analysis
            cache_path (Path): path of cached data
            file (Path): text file containing the report. Defaults to None.
            json (Path): directory to store the reports in individual json files. Defaults to None.
            analysis_plugin (str): module to load for analysis
        """
        _, _, results = self._getCachedResults(tickers, cache_path, analysis_plugin)

        if results is None:
            raise LookupError("No analysis results available!")
        

        # Call analysis plugin
        analysis_module = importlib.import_module(analysis_plugin)
        options = ReportOptions(
            results=results, file=file, json=json
        )
        analysis_module.report(options)

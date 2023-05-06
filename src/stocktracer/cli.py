import hashlib
import importlib
import logging
import os
from pathlib import Path

import pandas as pd
from diskcache import Cache

from stocktracer.interface import Analysis as AnalysisInterface
from stocktracer.interface import Options as CliOptions
from stocktracer.interface import ReportOptions as CliReportOptions

logger = logging.getLogger(__name__)


def get_analysis_instance(module_name: str) -> AnalysisInterface:
    """Dynamically import and load the Analysis class from a module

    Args:
        module_name (str): full name of the module. For example, "my.module"

    Returns:
        AnalysisInterface: analysis instance
    """
    module = importlib.import_module(module_name)
    class_ = getattr(module, "Analysis")
    instance = class_()
    assert isinstance(instance, AnalysisInterface)
    return instance


class Cli:

    """Tools for gathering resources, analyzing data, and publishing the results."""

    _default_analysis_module = "stocktracer.analysis.stub"

    def _getDefaultCachePath() -> Path:
        """Get the default path for caching data

        Returns:
            Path: path to cache data
        """
        return Path(os.getcwd()) / ".ticker-cache"

    def analyze(
        self,
        tickers: list[str],
        cache_path: Path = _getDefaultCachePath(),
        refresh: bool = False,
        analysis_plugin: str = _default_analysis_module,
    ) -> None:
        """Perform stock analysis

        Args:
            tickers (list[str]): tickers to include in the analysis
            cache_path (Path): path where to cache data
            refresh (bool): Whether to refresh the calculation or use the results from a prior one
            analysis_plugin (str): module to load for analysis
        """
        analysis_module: AnalysisInterface = get_analysis_instance(analysis_plugin)
        analysis_module.options = CliOptions(tickers=tickers, cache_path=cache_path)

        cache, results_key, results = self._getCachedResults(
            tickers, cache_path, analysis_plugin
        )

        if (
            refresh
            or results is None
            or not isinstance(results, pd.DataFrame)
            or results.empty()
        ):
            # Call analysis plugin
            results = analysis_module.analyze()
            if not isinstance(results, pd.DataFrame):
                raise ValueError("analysis modules must return a pandas.DataFrame")
            if results.empty:
                raise LookupError("No analysis results available!")

            tickers = frozenset(tickers)

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
        return cache, results_key, results

    def _get_results_key(tickers: frozenset, analysis_module: str) -> str:
        """
        >>> Cli._get_results_key({"aapl","msft"},"my.analysis")
        'my.analysis-aapl-msft'
        """
        sorted_tickers = list(tickers)
        sorted_tickers.sort()
        results_key = "-".join(sorted_tickers)
        return "-".join((analysis_module, results_key))

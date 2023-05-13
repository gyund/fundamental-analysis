"""This is the CLI class for stocktracer."""
import importlib
import io
import logging
import os
import warnings
from pathlib import Path
from typing import Literal, Optional, Union

import pandas as pd
from beartype import beartype
from beartype.typing import Sequence, Tuple
from diskcache import Cache

from stocktracer.interface import Analysis as AnalysisInterface
from stocktracer.interface import Options as CliOptions

logger = logging.getLogger(__name__)


@beartype
def get_analysis_instance(module_name: str) -> AnalysisInterface:
    """Dynamically import and load the Analysis class from a module.

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


@beartype
def get_default_cache_path() -> Path:
    """Get the default path for caching data.

    Returns:
        Path: path to cache data
    """
    return Path(os.getcwd()) / ".ticker-cache"


ReportFormat = Literal["csv", "md", "json", "txt"]


@beartype
class Cli:
    """Tools for gathering resources, analyzing data, and publishing the results."""

    return_results: bool = True

    def analyze(
        self,
        tickers: Union[Sequence[str], str],
        cache_path: str = str(get_default_cache_path()),
        refresh: bool = False,
        analysis_plugin: str = "stocktracer.analysis.annual_reports",
        final_year: Optional[int] = None,
        final_quarter: Optional[int] = None,
        report_format: Optional[ReportFormat] = "txt",
        report_file: Optional[str] = None,
    ) -> Optional[pd.DataFrame]:
        """Perform stock analysis.

        Args:
            tickers (Union[Sequence[str], str]): tickers to include in the analysis
            cache_path (str): path where to cache data
            refresh (bool): Whether to refresh the calculation or use the results from a prior one
            analysis_plugin (str): module to load for analysis
            final_year (Optional[int]): last year to consider for report collection
            final_quarter (Optional[int]): last quarter to consider for report collection
            report_format (Optional[ReportFormat]): Format of the report. Options include: csv, json, md (markdown)
            report_file (Optional[str]): Where to store the report. Required if report_format is specified.

        Raises:
            LookupError: no analysis results found

        Returns:
            Optional[pd.DataFrame]: results of analysis
        """
        cache_path = Path(cache_path)
        if report_file:
            report_file = Path(report_file)
        if isinstance(tickers, str):
            tickers = frozenset([tickers])
        else:
            tickers = frozenset(tickers)

        analysis_module: AnalysisInterface = get_analysis_instance(analysis_plugin)
        analysis_module.options = CliOptions(
            tickers=tickers,
            cache_path=cache_path,
            final_year=final_year,
            final_quarter=final_quarter,
        )

        cache, results_key, results = self._get_cached_results(
            tickers, cache_path, analysis_plugin
        )

        if (
            refresh
            or results is None
            or not isinstance(results, pd.DataFrame)
            or results.empty
        ):
            # Call analysis plugin
            results = analysis_module.analyze()
            if results is None or results.empty:
                raise LookupError("No analysis results available!")

            tickers = frozenset(tickers)

            # Save one week expiry
            cache.set(key=results_key, value=results, expire=3600 * 24 * 7)

        self._generate_report(report_format, report_file, results)
        if analysis_module.under_development:
            warnings.warn(
                "This analysis module is under development and may be incorrect, incomplete, or may change."
            )
        if self.return_results:
            return results
        return None

    @classmethod
    def _generate_report(
        cls,
        report_format: ReportFormat,
        report_file: Path | io.StringIO | None,
        results: pd.DataFrame,
    ):
        if report_file is None:
            report_file = io.StringIO()
        match report_format.lower():
            case "csv":
                results.to_csv(report_file)
            case "md":
                results.to_markdown(report_file)
            case "json":
                results.to_json(report_file)
            case "txt":   
                results.to_string(report_file)
        if isinstance(report_file, io.StringIO):
            print(report_file.getvalue())

    def _get_cached_results(
        self, tickers, cache_path, analysis_plugin
    ) -> Tuple[Cache, str, Optional[pd.DataFrame]]:
        assert isinstance(tickers, frozenset)
        cache = Cache(directory=cache_path / "results")
        results_key = get_cached_results_key(tickers, analysis_plugin)
        results = cache.get(key=results_key, default=None)
        return cache, results_key, results


@beartype
def get_cached_results_key(tickers: frozenset[str], analysis_module: str) -> str:
    """Get the key used for caching results from analyzed data.

    >>> get_cached_results_key(frozenset({"aapl","msft"}),"my.analysis")
    'my.analysis-aapl-msft'

    Args:
        tickers (frozenset[str]): tickers to check
        analysis_module (str): name of analysis module

    Returns:
        str: string with the cached key
    """
    sorted_tickers = list(tickers)
    sorted_tickers.sort()
    results_key = "-".join(sorted_tickers)
    return "-".join((analysis_module, results_key))

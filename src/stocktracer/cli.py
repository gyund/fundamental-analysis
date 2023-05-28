"""This is the CLI class for stocktracer."""
import importlib
import io
import logging
import warnings
from pathlib import Path
from typing import Literal, Optional, Union

import pandas as pd
from beartype import beartype
from beartype.typing import Sequence, Tuple
from diskcache import Cache

from stocktracer import settings
from stocktracer.interface import Analysis as AnalysisInterface, ReportDate
from stocktracer.interface import Options as CliOptions

logger = logging.getLogger(__name__)

result_cache = Cache(directory=settings.storage_path / "results")


@beartype
def get_analysis_instance(module_name: str, options: CliOptions) -> AnalysisInterface:
    """Dynamically import and load the Analysis class from a module.

    Args:
        module_name (str): full name of the module. For example, "my.module"
        options (CliOptions): options provided from the CLI

    Returns:
        AnalysisInterface: analysis instance
    """
    module = importlib.import_module(module_name)
    class_ = getattr(module, "Analysis")
    instance = class_(options)
    assert isinstance(instance, AnalysisInterface)
    return instance


ReportFormat = Literal["csv", "md", "json", "txt"]


@beartype
class Cli:
    """Tools for gathering resources, analyzing data, and publishing the results."""

    return_results: bool = True

    def analyze(  # pylint: disable=too-many-arguments
        self,
        tickers: Union[Sequence[str], str],
        cache_path: Path | str = settings.storage_path,
        refresh: bool = False,
        analysis_plugin: str = "stocktracer.analysis.annual_reports",
        final_year: int = ReportDate().year,
        final_quarter: int = ReportDate().quarter,
        report_format: ReportFormat = "txt",
        report_file: Optional[Path | str] = None,
    ) -> Optional[pd.DataFrame]:
        """Perform stock analysis.

        Args:
            tickers (Union[Sequence[str], str]): tickers to include in the analysis
            cache_path (Path | str): path where to cache data
            refresh (bool): Whether to refresh the calculation or use the results from a prior one
            analysis_plugin (str): module to load for analysis
            final_year (int): last year to consider for report collection
            final_quarter (int): last quarter to consider for report collection
            report_format (ReportFormat): Format of the report. Options include: csv, json, md (markdown)
            report_file (Optional[Path | str]): Where to store the report. Required if report_format is specified.

        Raises:
            LookupError: no analysis results found

        Returns:
            Optional[pd.DataFrame]: results of analysis
        """
        settings.storage_path = Path(cache_path)
        if report_file:
            report_file = Path(report_file)
        if isinstance(tickers, str):
            tickers = list([tickers])
        else:
            tickers = list(tickers)

        tickers.sort()

        results, analysis_module = self._get_result(
            tickers=tickers,
            analysis_plugin=analysis_plugin,
            final_year=final_year,
            final_quarter=final_quarter,
        )

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
        results = results.transpose()
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

    @result_cache.memoize(typed=True, expire=60 * 60 * 24 * 7, tag="results")
    def _get_result(
        self,
        tickers: list[str],
        analysis_plugin: str,
        final_year: int,
        final_quarter: int,
    ) -> Tuple[Optional[pd.DataFrame], AnalysisInterface]:
        analysis_module: AnalysisInterface = get_analysis_instance(
            analysis_plugin,
            CliOptions(
                tickers=frozenset(tickers),
                final_year=final_year,
                final_quarter=final_quarter,
            ),
        )

        # Call analysis plugin
        results = None
        results = analysis_module.analyze()
        if results is None or results.empty:
            raise LookupError("No analysis results available!")
        return results, analysis_module


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

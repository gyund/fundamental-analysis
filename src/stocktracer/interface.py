"""Interfaces for the StockTracer Module."""
import abc
from pathlib import Path
from typing import Optional

from beartype import beartype
from pandas import DataFrame

from stocktracer.data.sec import ReportDate


@beartype
class Options:
    """Command Line Options."""

    def __init__(
        self,
        tickers: frozenset[str],
        cache_path: Path,
        final_year: int | None,
        final_quarter: int | None,
    ):
        """Options.

        Args:
            tickers (frozenset[str]): tickers to scrape from data sets
            cache_path (Path): path to cache processed or downloaded information
            final_year (int | None): last year to consider for report collection
            final_quarter (int | None): last quarter to consider for report collection
        """
        self.tickers = tickers
        self.cache_path = cache_path
        self.last_report = ReportDate(year=final_year, quarter=final_quarter)


@beartype
class Analysis(metaclass=abc.ABCMeta):
    """Base class for all analysis techniques."""

    def __init__(self) -> None:
        self.options: Optional[Options] = None

    @abc.abstractmethod
    def analyze(self) -> Optional[DataFrame]:
        """Perform financial analysis.

        Returns:
            Optional[DataFrame]: results of analysis
        """

    under_development: bool = False

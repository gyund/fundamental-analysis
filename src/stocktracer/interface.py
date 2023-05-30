"""Interfaces for the StockTracer Module."""
import abc
from dataclasses import dataclass, field
from typing import Optional

from beartype import beartype
from pandas import DataFrame

from stocktracer.collector.sec import ReportDate


@beartype
@dataclass(frozen=True)
class Options:
    """Command Line Options."""

    tickers: list[str]
    final_report: ReportDate = ReportDate()

    def __post_init__(self):
        self.tickers.sort()


@beartype
class Analysis(metaclass=abc.ABCMeta):
    """Base class for all analysis techniques."""

    def __init__(self, options: Options) -> None:
        self.options = options
        assert self.options is not None

    @abc.abstractmethod
    def analyze(self) -> Optional[DataFrame]:
        """Perform financial analysis.

        Returns:
            Optional[DataFrame]: results of analysis
        """

    under_development: bool = False

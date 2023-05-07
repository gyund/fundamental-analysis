""" Interfaces for the StockTracer Module."""
import abc
from pathlib import Path
from typing import Optional

from beartype import beartype
from pandas import DataFrame


@beartype
class Options:
    """Command Line Options"""

    def __init__(self, tickers: frozenset[str], cache_path: Path):
        """Options

        Args:
            tickers (frozenset[str]): tickers to scrape from data sets
            cache_path (Path): path to cache processed or downloaded information
        """
        self.tickers = tickers
        self.cache_path = cache_path


@beartype
class Analysis(metaclass=abc.ABCMeta):
    """Base class for all analysis techniques.

    Args:
        metaclass (_type_, optional): _description_. Defaults to abc.ABCMeta.

    Returns:
        _type_: _description_
    """

    @abc.abstractmethod
    def analyze(self) -> Optional[DataFrame]:
        """Perform financial analysis.

        Returns:
            Optional[DataFrame]: results of analysis
        """

    @property
    def options(self) -> Optional[Options]:
        """Get current analysis options.

        Returns:
            Optional[Options]: configured options or None.
        """

    @options.setter
    def options(self, options: Options):
        """Set analysis options.

        Args:
            options (Options): options
        """
        self._options = options

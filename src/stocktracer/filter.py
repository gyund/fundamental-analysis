"""Filter Interface.

This may be removed or deprecated in the future. TBD.
"""
from beartype import beartype

from stocktracer.data.sec import Filter as SecFilter


@beartype
class Selectors:
    def __init__(
        self, ticker_filter: set[str] | list[str], sec_filter: SecFilter
    ) -> None:
        """Entry for data to search for in various sources.

        Args:
            ticker_filter (set[str] | list[str]): list of stock tickers to get information about
            sec_filter (SecFilter): filter for SEC reports
        """
        self.ticker_filter = frozenset(ticker_filter)
        self.sec_filter = sec_filter

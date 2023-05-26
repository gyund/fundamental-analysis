"""Filter Interface.

This may be removed or deprecated in the future. TBD.
"""
from beartype import beartype

from stocktracer.data.sec import Filter as SecFilter


@beartype
class Selectors:
    """Selectors provide an aggregation point for a number of built-in filter mechanics.

    The original intent for this was to provide a bag to throw a bunch of filters in. However,
    analysis modules somewhat replace this concept by giving finer grained control over what
    filters get applied. This may go away in the future pending a determination whether or not
    the class is needed.
    """

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

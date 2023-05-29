"""Filter Interface.

This may be removed or deprecated in the future. TBD.
"""
from dataclasses import dataclass

from beartype import beartype

from stocktracer.collector.sec import Filter as SecFilter


@beartype
@dataclass(frozen=True)
class Selectors:
    """Selectors provide an aggregation point for a number of built-in filter mechanics.

    The original intent for this was to provide a bag to throw a bunch of filters in. However,
    analysis modules somewhat replace this concept by giving finer grained control over what
    filters get applied. This may go away in the future pending a determination whether or not
    the class is needed.
    """

    ticker_filter: set[str]
    sec_filter: SecFilter

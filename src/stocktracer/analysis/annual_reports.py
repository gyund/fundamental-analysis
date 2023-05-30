"""Download and retrieves annual reports for the specified stock tickers."""
import logging
from typing import Optional

import pandas as pd
from beartype import beartype

import stocktracer.collector.sec as Sec
from stocktracer.interface import Analysis as AnalysisInterface
from stocktracer.interface import Options

logger = logging.getLogger(__name__)


def create_normalized_sec_table(
    sec_filter: Sec.Filter, tickers: list[str], normalize: bool = True
) -> Sec.Results.Table:
    """Create a normalized SEC table with all NA values removed.

    Args:
        sec_filter (Sec.Filter): filter to use for grabbing results
        tickers (list[str]): tickers to retrieve
        normalize (bool): Remove all columns that contain at least one NA value

    Returns:
        Sec.Results.Table: An SEC table with normalized results
    """
    # prep for caching
    tickers.sort()
    results = Sec.filter_data(tickers=tickers, sec_filter=sec_filter)

    table = results.select()
    # If you prefer to see columns that are not universal across all stocks, comment this out
    if normalize:
        table.normalize()
    return table


@beartype
class Analysis(AnalysisInterface):
    """Class for collecting and processing annual report data."""

    under_development = True

    def analyze(self) -> Optional[pd.DataFrame]:
        # By omitting the tags, we'll collect all tags for securities
        sec_filter = Sec.Filter(
            # tags=["EarningsPerShareDiluted"],
            years=1,  # Over the past 1 years
            last_report=self.options.final_report,
            only_annual=True,  # We only want the 10-K
        )

        # Create an SEC Data Source
        table = create_normalized_sec_table(sec_filter, self.options.tickers, False)

        return table.data

    # Reuse documentation from parent
    analyze.__doc__ = AnalysisInterface.analyze.__doc__

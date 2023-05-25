"""Download and retrieves annual reports for the specified stock tickers."""
import logging
from typing import Optional

import pandas as pd
from beartype import beartype

from stocktracer.data.sec import Filter as SecFilter
from stocktracer.data.sec import Sec as SecDataSource
from stocktracer.interface import Analysis as AnalysisInterface
from stocktracer.interface import Options

logger = logging.getLogger(__name__)


def create_normalized_sec_table(
    sec_filter: SecFilter, options: Options, normalize: bool = True
) -> SecFilter.Results:
    """Create a normalized SEC table with all NA values removed.

    Args:
        sec_filter (SecFilter): filter to use for grabbing results
        options (Options): user provided CLI options
        normalize (bool): Remove all columns that contain at least one NA value

    Returns:
        SecFilter.Results: An SEC table with normalized results
    """
    sec = SecDataSource(storage_path=options.cache_path)
    sec.filter_data(tickers=options.tickers, sec_filter=sec_filter)

    table = sec_filter.select()
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
        sec_filter = SecFilter(
            # tags=["EarningsPerShareDiluted"],
            years=1,  # Over the past 1 years
            last_report=self.options.last_report,
            only_annual=True,  # We only want the 10-K
        )

        # Create an SEC Data Source
        table = create_normalized_sec_table(sec_filter, self.options, False)

        return table.data

    # Reuse documentation from parent
    analyze.__doc__ = AnalysisInterface.analyze.__doc__

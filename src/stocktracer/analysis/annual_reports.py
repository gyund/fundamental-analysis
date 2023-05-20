import logging
from typing import Optional

import pandas as pd
from beartype import beartype

from stocktracer.data.sec import Filter as SecFilter
from stocktracer.data.sec import Sec as SecDataSource
from stocktracer.interface import Analysis as AnalysisInterface

logger = logging.getLogger(__name__)


@beartype
class Analysis(AnalysisInterface):
    """Perform an analysis on the earnings per share over time."""

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
        assert self.options is not None
        assert self.options.cache_path is not None
        sec = SecDataSource(storage_path=self.options.cache_path)
        sec.filter_data(tickers=self.options.tickers, filter=sec_filter)

        table = sec_filter.select()

        # If you prefer to see columns that are not universal across all stocks, comment this out
        table.data = table.data.dropna(axis=1, how="any")

        return table.data

    # Reuse documentation from parent
    analyze.__doc__ = AnalysisInterface.analyze.__doc__

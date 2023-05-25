"""This analysis module determines the trend of EPS over the course of the past 5 years."""
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
    """Class that calculates the EPS slope."""

    under_development = True
    years_of_analysis = 5

    def analyze(self) -> Optional[pd.DataFrame]:
        # Create the filter we'll use to scrape the results
        sec_filter = SecFilter(
            tags=["EarningsPerShareDiluted"],
            years=self.years_of_analysis,
            last_report=self.options.last_report,
            only_annual=True,  # We only want the 10-K
        )

        # Create an SEC Data Source
        sec = SecDataSource(storage_path=self.options.cache_path)

        # This is an expensive operation
        sec.filter_data(tickers=self.options.tickers, sec_filter=sec_filter)
        return sec_filter.select("slope").data

    # Reuse documentation from parent
    analyze.__doc__ = AnalysisInterface.analyze.__doc__

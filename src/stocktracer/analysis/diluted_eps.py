import logging
from typing import Optional

import numpy as np
import pandas as pd
from beartype import beartype

from stocktracer.data.sec import Filter as SecFilter
from stocktracer.data.sec import Sec as SecDataSource
from stocktracer.interface import Analysis as AnalysisInterface

logger = logging.getLogger(__name__)


@beartype
class Analysis(AnalysisInterface):
    """Calculate the slope of EPS values over the course of the past 5 years."""

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
        assert self.options is not None
        assert self.options.cache_path is not None
        sec = SecDataSource(storage_path=self.options.cache_path)

        # This is an expensive operation
        sec.select_data(tickers=self.options.tickers, filter=sec_filter)
        return sec_filter.select("slope").data

    # Reuse documentation from parent
    analyze.__doc__ = AnalysisInterface.analyze.__doc__

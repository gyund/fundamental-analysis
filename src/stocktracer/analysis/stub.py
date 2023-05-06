import logging
from typing import Optional

import pandas as pd

from stocktracer.interface import Analysis as AnalysisInterface

logger = logging.getLogger(__name__)


class Analysis(AnalysisInterface):
    def analyze(self) -> Optional[pd.DataFrame]:
        """Analyze the report

        As a stub, this does nothing

        Args:
            options (Options): options to use for processing

        Returns:
            pd.DataFrame: Containing the results of the report
        """
        print(
            "This is where we would start to process information, but we're not right now"
        )
        return pd.DataFrame()

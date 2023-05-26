"""This stub serves an example for module developers."""
import logging
from typing import Optional

import pandas as pd
from beartype import beartype

from stocktracer.interface import Analysis as AnalysisInterface

logger = logging.getLogger(__name__)


@beartype
class Analysis(AnalysisInterface):
    """Stub for analyzing the report."""

    def analyze(self) -> Optional[pd.DataFrame]:
        """

        As a stub, this does nothing

        Returns:
            Optional[pd.DataFrame]: Always None, since the stub doesn't analyze anything.
        """
        print(
            "This is where we would start to process information, but we're not right now"
        )

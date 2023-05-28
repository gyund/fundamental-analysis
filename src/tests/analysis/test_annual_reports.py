import logging

import mock
import pytest

from stocktracer.analysis.diluted_eps import Analysis
from stocktracer.cli import Cli

logger = logging.getLogger(__name__)

# We only need a year for testing, cut down on data
Analysis.years_of_analysis = 1


class TestCliAnnualReports:
    cli: Cli = Cli()

    @pytest.mark.webtest
    def test_analyze(self):
        self.cli.return_results = True
        result = self.cli.analyze(
            tickers=["aapl", "tmo", "msft", "goog", "wm", "acn"],
            analysis_plugin="stocktracer.analysis.annual_reports",
            final_year=2023,
            final_quarter=1,
        )
        assert result is not None
        logger.debug(f"annual_reports:\n{result.transpose().to_string()}")
        # Note: goog, and googl are pulled in, so it's 7 instead of 6
        assert len(result.index) == 7

    def test_invalid(self):
        with pytest.raises(LookupError, match="unable to find ticker: invalid"):
            self.cli.analyze(
                tickers="invalid", analysis_plugin="stocktracer.analysis.diluted_eps"
            )

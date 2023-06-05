import logging

import pytest

from stocktracer import cache
from stocktracer.analysis.annual_reports import Analysis
from stocktracer.cli import Cli
from stocktracer.interface import Options as CliOptions
from stocktracer.interface import ReportDate

logger = logging.getLogger(__name__)

tickers = ["aapl", "tmo", "msft", "goog", "wm", "acn"]
final_year = 2023
final_quarter = 1


class TestCliAnnualReports:
    cli: Cli = Cli()

    @pytest.mark.webtest
    def test_analyze_direct(self):
        """Test direct calls so we can ensure caching occurs as well."""
        # Ensure at least one test parses through the CSV files
        cache.results.evict(tag="sec")
        options = CliOptions(
            tickers=tickers,
            final_report=ReportDate(final_year, final_quarter),
        )
        analyzer = Analysis(options)
        result = analyzer.analyze()
        assert result is not None

        # logger.debug(f"annual_reports:\n{result.transpose().to_string()}")
        # Note: goog, and googl are pulled in, so it's 7 instead of 6
        assert len(result.index) == 7

    @pytest.mark.webtest
    def test_analyze(self):
        self.cli.return_results = True
        result = self.cli.analyze(
            tickers=tickers,
            analysis_plugin="stocktracer.analysis.annual_reports",
            final_year=final_year,
            final_quarter=final_quarter,
        )
        assert result is not None
        # logger.debug(f"annual_reports:\n{result.transpose().to_string()}")
        # Note: goog, and googl are pulled in, so it's 7 instead of 6
        assert len(result.index) == 7

    def test_invalid(self):
        with pytest.raises(LookupError, match="unable to find ticker: invalid"):
            self.cli.analyze(
                tickers="invalid", analysis_plugin="stocktracer.analysis.diluted_eps"
            )

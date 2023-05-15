import logging
import math

import pytest

from stocktracer.analysis.diluted_eps import Analysis
from stocktracer.cli import Cli

logger = logging.getLogger(__name__)

# We only need a year for testing, cut down on data
Analysis.years_of_analysis = 1


class TestCliDilutedEps:
    cli: Cli = Cli()

    @pytest.mark.webtest
    def test_analyze(self):
        self.cli.return_results = True
        result = self.cli.analyze(
            tickers=["aapl", "tmo", "msft"],
            analysis_plugin="stocktracer.analysis.diluted_eps",
            refresh=True,
            final_year=2023,
            final_quarter=1,
        )
        assert result is not None
        logger.debug(f"diluted_eps_result:\n{result}")
        assert math.isclose(
            result.loc["TMO"]["EarningsPerShareDiluted"], 17.683333, rel_tol=0.001
        )

    def test_invalid(self):
        with pytest.raises(LookupError, match="unable to find ticker: invalid"):
            self.cli.analyze(
                tickers="invalid", analysis_plugin="stocktracer.analysis.diluted_eps"
            )

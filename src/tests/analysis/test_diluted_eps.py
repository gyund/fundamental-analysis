import logging

import mock
import pytest

from stocktracer.cli import Cli

logger = logging.getLogger(__name__)


class TestCliDilutedEps:
    cli: Cli = Cli()

    @pytest.mark.webtest
    def test_analyze(self):
        result = self.cli.analyze(
            tickers=["aapl", "tmo", "msft"],
            analysis_plugin="stocktracer.analysis.diluted_eps",
            refresh=True,
        )
        assert result is not None
        logger.debug(
            f"diluted_eps_result:\n{result.sort_values(ascending=True, by=['ddate'])}"
        )

    def test_invalid(self):
        with pytest.raises(LookupError, match="unable to find ticker: invalid"):
            self.cli.analyze(
                tickers="invalid", analysis_plugin="stocktracer.analysis.diluted_eps"
            )

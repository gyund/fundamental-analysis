import logging

import mock
import pytest

from stocktracer.cli import Cli

logger = logging.getLogger(__name__)


@pytest.mark.webtest
class TestCli:
    cli: Cli = Cli()

    def test_analyze(self):
        self.cli.analyze(
            tickers=["aapl", "tmo", "msft"],
            analysis_plugin="stocktracer.analysis.diluted_eps",
        )

    def test_invalid(self):
        with pytest.raises(LookupError, match="No analysis results available!"):
            self.cli.analyze(
                tickers="invalid", analysis_plugin="stocktracer.analysis.diluted_eps"
            )

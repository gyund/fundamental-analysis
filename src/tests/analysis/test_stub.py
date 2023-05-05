import logging

import mock
import pytest

from stocktracer.cli import Cli

logger = logging.getLogger(__name__)


class TestCli:
    cli: Cli = Cli()

    def test_analyze(self):
        self.cli.analyze(
            refresh=True, tickers=["aapl"], analysis_plugin="stocktracer.analysis.stub"
        )

    def test_invalid(self):
        with pytest.raises(LookupError, match="No analysis results available!"):
            self.cli.analyze(
                tickers="invalid", analysis_plugin="stocktracer.analysis.stub"
            )

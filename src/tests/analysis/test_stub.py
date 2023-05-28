import logging

import pytest

from stocktracer.cli import Cli

logger = logging.getLogger(__name__)


class TestCliStub:
    cli: Cli = Cli()

    def test_analyze(self):
        with pytest.raises(LookupError, match="No analysis results available!"):
            self.cli.analyze(
                tickers=["aapl"],
                analysis_plugin="stocktracer.analysis.stub",
            )

    def test_invalid(self):
        with pytest.raises(LookupError, match="No analysis results available!"):
            self.cli.analyze(
                tickers="invalid", analysis_plugin="stocktracer.analysis.stub"
            )

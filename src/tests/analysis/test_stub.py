import logging

import mock
import pytest

from stocktracer.cli import Cli, Options, ReportOptions

logger = logging.getLogger(__name__)


class TestCli:
    cli: Cli = Cli()

    def test_analyze(self):
        self.cli.analyze(tickers=["aapl"], analysis_plugin="stocktracer.analysis.stub")

    def test_export(self):
        self.cli.export(tickers=["aapl"], analysis_plugin="stocktracer.analysis.stub")

    def test_invalid(self):
        try:
            self.cli.export(
                tickers="invalid", analysis_plugin="stocktracer.analysis.stub"
            )
        except ZeroDivisionError as exc:
            pytest.fail(exc, pytrace=True)

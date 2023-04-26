import pytest
import mock
from ticker.cli import Cli


class TestCli:
    cli: Cli = Cli()

    def test_analyze(self):
        self.cli._doUpdateFromSec = mock.Mock()
        self.cli.analyze(tickers=['aapl'])
        self.cli._doUpdateFromSec.assert_called_once()

    def test_export(self):
        self.cli.export(tickers=['aapl'])

    def test_invalid(self):
        try:
            self.cli.export(tickers="invalid")
        except ZeroDivisionError as exc:
            pytest.fail(exc, pytrace=True)

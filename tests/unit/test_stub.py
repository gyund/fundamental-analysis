import pytest
import mock
from ticker.cli import Cli
from ticker.data.source import Stub


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


class TestStub:
    stub: Stub = Stub()

    def test_calls(self):
        assert self.stub.getCashFlowFromOperatingActivities("msft") == 0

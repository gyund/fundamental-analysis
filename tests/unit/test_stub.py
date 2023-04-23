import pytest
from ticker.cli import Cli
from ticker.data.source import Stub


class TestCli:
    cli: Cli = Cli()

    def test_analyze(self):
        self.cli.analyze(source="stub")

    def test_export(self):
        self.cli.export(source="stub")

    def test_invalid(self):
        try:
            self.cli.export(source="invalid")
        except ZeroDivisionError as exc:
            pytest.fail(exc, pytrace=True)


class TestStub:
    stub: Stub = Stub()

    def test_calls(self):
        assert self.stub.getCashFlowFromOperatingActivities("msft") == 0

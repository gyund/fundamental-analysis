import fire.core
import pytest

from stocktracer.__main__ import main_cli


def test_help():
    with pytest.raises(fire.core.FireExit):
        assert main_cli("--help") == 0


def test_stub():
    result = main_cli("analyze aapl,msft")
    assert isinstance(result, LookupError)
    assert result.args[0] == "No analysis results available!"

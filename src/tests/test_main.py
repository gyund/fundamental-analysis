import fire.core
import pytest

from stocktracer.__main__ import main_cli


def test_main():
    with pytest.raises(fire.core.FireExit):
        main_cli("--help") == 0

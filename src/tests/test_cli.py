import io

import beartype.roar
import mock
import pandas as pd
import pytest

import stocktracer.filter as Filter
from stocktracer.cli import Cli
from stocktracer.data.sec import Sec
from tests.sec.test_sec import sec_harness


def test_generate(sec_harness: tuple[Sec, mock.MagicMock]):
    (sec, download_manager) = sec_harness
    d = {"col1": [1, 2], "col2": [3, 4]}
    data_frame = pd.DataFrame(data=d)
    result = io.StringIO()
    Cli._generate_report("csv", result, data_frame)
    assert data_frame.to_csv() == result.getvalue()
    result = io.StringIO()
    Cli._generate_report("json", result, data_frame)
    assert data_frame.to_json() == result.getvalue()
    result = io.StringIO()
    Cli._generate_report("md", result, data_frame)
    assert data_frame.to_markdown() == result.getvalue()

    with pytest.raises(beartype.roar.BeartypeCallHintParamViolation):
        Cli._generate_report("invalid", None, data_frame)

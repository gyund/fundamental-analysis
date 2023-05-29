import io

import beartype.roar
import mock
import pandas as pd
import pytest

import stocktracer.filter as Filter
from stocktracer.cli import Cli
import stocktracer.collector.sec as Sec
from stocktracer.collector.sec import DownloadManager


def test_generate():
    download_manager = mock.MagicMock(DownloadManager)
    d = {"col1": [1, 2], "col2": [3, 4]}
    data_frame = pd.DataFrame(data=d)
    result = io.StringIO()
    Cli._generate_report("csv", result, data_frame)
    assert data_frame.transpose().to_csv() == result.getvalue()
    result = io.StringIO()
    Cli._generate_report("json", result, data_frame)
    assert data_frame.transpose().to_json() == result.getvalue()
    result = io.StringIO()
    Cli._generate_report("md", result, data_frame)
    assert data_frame.transpose().to_markdown() == result.getvalue()

    with pytest.raises(beartype.roar.BeartypeCallHintParamViolation):
        Cli._generate_report("invalid", None, data_frame)

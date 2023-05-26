import io
import logging
from datetime import date
from pathlib import Path

import mock
import pytest

import stocktracer.filter as Filter
from stocktracer.cli import Cli
from stocktracer.collector.sec import DataSetReader
from tests.fixtures.unit import data_txt_sample, filter_aapl, sub_txt_sample

logger = logging.getLogger(__name__)


def test_benchmark_DataSetReader_processSubText(
    benchmark, filter_aapl: Filter.Selectors, sub_txt_sample
):
    filter_aapl.sec_filter._cik_list = set()
    filter_aapl.sec_filter._cik_list.add(320193)
    benchmark.pedantic(
        DataSetReader._process_sub_text,
        args=(io.StringIO(sub_txt_sample), filter_aapl.sec_filter),
    )


def test_benchmark_DataSetReader_processNumText(
    benchmark, filter_aapl: Filter.Selectors, sub_txt_sample, data_txt_sample
):
    filter_aapl.sec_filter._cik_list = set()
    filter_aapl.sec_filter._cik_list.add(320193)
    sub_df = DataSetReader._process_sub_text(
        filepath_or_buffer=io.StringIO(sub_txt_sample),
        sec_filter=filter_aapl.sec_filter,
    )
    benchmark.pedantic(
        DataSetReader._process_num_text,
        args=(io.StringIO(data_txt_sample), filter_aapl.sec_filter, sub_df),
    )


def test_DataSetReader_processSubText(filter_aapl: Filter.Selectors, sub_txt_sample):
    # Put AAPL's CIK in the list so it will be filtered
    filter_aapl.sec_filter._cik_list = set()
    filter_aapl.sec_filter._cik_list.add(320193)
    sub_df = DataSetReader._process_sub_text(
        filepath_or_buffer=io.StringIO(sub_txt_sample),
        sec_filter=filter_aapl.sec_filter,
    )
    logger.debug(f"sub keys: {sub_df.keys()}")
    logger.debug(sub_df)
    assert "0000320193-23-000006" in sub_df.index.get_level_values("adsh")
    assert "0000723125-23-000022" not in sub_df.index.get_level_values("adsh")
    assert "0000004457-23-000026" not in sub_df.index.get_level_values("adsh")

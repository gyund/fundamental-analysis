import pytest
from ticker.cli import Cli
from ticker.data.sec import Sec, ReportDate, TickerReader, DataSetReader, DataSelector


@pytest.fixture
def sec_instance() -> Sec:
    # test using the real SEC adapter
    return Sec(Cli.getDefaultCachePath())


@pytest.fixture
def sec_dataselector_2023q1(sec_instance) -> DataSelector:
    data = sec_instance.download_manager.getData(
        ReportDate(year=2023, quarter=1))
    df = data.processZip()
    assert df.empty == False
    return DataSelector(df)

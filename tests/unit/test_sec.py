import pytest
import mock
import os
from ticker.cli import Cli
from ticker.data.sec import Sec,ReportDate
from datetime import date
from pathlib import Path

def test_reportDate():
    rd = ReportDate(2023,1)
    assert rd.year == date.today().year
    assert rd.quarter == 1

    try:
        rd = ReportDate(date.today().year+1,1)
        pytest.fail('should throw and exception')
    except ValueError as ex:
        pass

    try:
        rd = ReportDate(date.today().year,0)
        pytest.fail('should throw and exception')
    except ValueError as ex:
        pass

    try:
        rd = ReportDate(date.today().year,5)
        pytest.fail('should throw and exception')
    except ValueError as ex:
        pass

class TestSecHarness:
    sec = Sec(Path(os.path.dirname(os.path.realpath(__file__)))/ ".ticker-cache")

    def test_update_1year(self):
        self.sec._updateCikMappings = mock.Mock()
        self.sec._updateQuarter = mock.Mock()
        self.sec.update(['appl'], 1)
        self.sec._updateCikMappings.assert_called_once()
        assert self.sec._updateQuarter.call_count == 5
    
    def test_update_2year(self):
        self.sec._updateCikMappings = mock.Mock()
        self.sec._updateQuarter = mock.Mock()
        self.sec.update(['appl'], 2)
        self.sec._updateCikMappings.assert_called_once()
        assert self.sec._updateQuarter.call_count == 9

    def test_update_3year(self):
        self.sec._updateCikMappings = mock.Mock()
        self.sec._updateQuarter = mock.Mock()
        self.sec.update(['appl'], 3)
        self.sec._updateCikMappings.assert_called_once()
        assert self.sec._updateQuarter.call_count == 13
        
    def test_processArchive(self):
        try:
            self.sec._processArchive('bad_archive')
            pytest.fail('should throw and exception')
        except:
            pass

    @pytest.mark.skipif(os.getenv("TICKER_TEST_SEC") is None,
                        reason="env variable TICKER_TEST_SEC not set")
    def test_integration(self):
        # TODO: test using the real SEC adapter
        pass
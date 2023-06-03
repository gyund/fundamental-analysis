import logging

import mock
import pytest

from stocktracer import cache
from stocktracer.cli import Cli

logger = logging.getLogger(__name__)

ticker_scan = [
    "v",
    "msft",
    "a",
    "intu",
    "levi",
    "cdns",
    "amat",
    "goog",
    "keys",
    "trow",
    "nvda",
    "adi",
    "mco",
    "ctas",
    "mrk",
    "blk",
    "tmo",
    "dhr",
    "avgo",
    "adp",
    "spns",
    "txn",
    "bmy",
    "spgi",
    "unh",
    "amd",
    "mchp",
    "payx",
    "acn",
    "ew",
    "abt",
    "ma",
    "trex",
    "mnst",
    "syk",
    "HTGC",
    "ISRG",
    "ste",
    "aapl",
    "csco",
    "csgp",
    "mdt",
    "lrcx",
    "cmcsa",
    "intc",
    "hd",
    "gis",
    "cost",
    "amgn",
    "well",
    "brk-b",
    "dis",
    "adbe",
    "ttwo",
    "amzn",
    "panw",
    "tsla",
]


class TestCliTensorflow:
    cli: Cli = Cli()

    @pytest.mark.webtest
    def test_analyze(self):
        pytest.importorskip("tensorflow_decision_forests")
        cache.results.evict(tag="sec")
        self.cli.return_results = True
        result = self.cli.analyze(
            tickers=ticker_scan,
            analysis_plugin="stocktracer.analysis.tensorflow",
            final_year=2023,
            final_quarter=1,
        )
        assert result is not None
        assert result.empty == True
        # logger.debug(f"annual_reports:\n{result.transpose().to_string()}")
        # Note: goog, and googl are pulled in, so it's 7 instead of 6
        # assert len(result.index) == 7

    def test_invalid(self):
        pytest.importorskip("tensorflow_decision_forests")
        with pytest.raises(LookupError, match="unable to find ticker: invalid"):
            self.cli.analyze(
                tickers="invalid", analysis_plugin="stocktracer.analysis.diluted_eps"
            )

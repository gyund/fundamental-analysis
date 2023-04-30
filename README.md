<p align="center">
    <a href='https://github.com/gyund/fundamental-analysis/blob/main/LICENSE'><img alt="License" src="https://img.shields.io/github/license/gyund/fundamental-analysis"></a>
    <img alt="License" src="https://img.shields.io/badge/python-3.10%2B-blue">
    <a href='https://github.com/gyund/fundamental-analysis/actions/workflows/python.yml'><img alt="Test Status" src="https://github.com/gyund/fundamental-analysis/actions/workflows/python.yml/badge.svg?service=github"></a>
    <a href='https://coveralls.io/github/gyund/fundamental-analysis?branch=main'><img src='https://coveralls.io/repos/github/gyund/fundamental-analysis/badge.svg?branch=main&service=github' alt='Coverage Status' /></a>
    <img alt="Development Status" src="https://img.shields.io/badge/status-early%20development-red">
</p>

# Ticker (smart stock analysis)

The goal of this project is to generate data that is consumable in both human readable format as well as JSON to better analyze and make sense of the intrinsic value of publicly traded companies.

The tool seeks to provide extensible options for consuming data from different data sources. There are different methods for gathering data:

- SEC (personal/commercial)
- Site Scraping (only personal)

Generally speaking, scraping sites is only for personal use and to vet the APIs. The tool will provide warnings when using options that may have additional restrictions to their use and will require a `--force` option to ensure that you understand the rules surrounding their use.

Additionally, the tools will utilize file based caching to limit interaction with expensive networking resources. Since fundamental analysis generally requires a long term view of companies with a proven track record, you generally will be downloading an initial history for a given equity and updating quarterly or annually based on new information.

## Requirements

- `python 3.10+`

## Getting Started

```sh
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt

# Perform analysis (not supported yet)
python -m ticker analyze --tickers aapl,msft
```

If you wish to use your own analysis plugin, you simply create your own module that implements this interface:

```python
from ticker.cli import Options, ReportOptions
from ticker.data.sec import DataSelector as SecDataSelector
from ticker.filter import Selectors,SecFilter

def analyze(options: Options) -> None:
    print("This is where we would start to process information, but we're not right now")

def report(options: ReportOptions) -> None: 
    print("This is where we would report our findings, but we're not right now")
```

Then call the tool in the following manner:

```sh
# Not yet supported 
python -m ticker analyze --tickers aapl,msft --analysis_plugin 'mypkg.analysis'
```

More information can be found in our [documentation](https://gyund.github.io/fundamental-analysis/)

### Testing

Run tests by running the following:

```sh
pytest
```

If you wish to run tests using real network resources, such as downloading real reports and processing them, run the following:

```sh
TICKER_TEST_NETWORK=1 pytest
```

Note that all data sets will be cached in the directory `${cwd}/.ticker-cache/` for both real and test runs. Expiry for quarterly reports are cached for 5 years and ticker mappings for `CIK -> Ticker` conversion are cached on a yearly basis. You generally won't be researching companies with less than a year's worth of reports though this could cause recently listed companies to lack `CIK -> Ticker` conversions for up to two years from poor timing. Just delete `${cwd}/.ticker-cache/tickers.sqlite` to get the latest.

## Disclaimer

This projects seeks to use publicly available information about stocks and securities to help perform long term risk analysis. Results provided from this project are for academic use only and are not considered advice or recommendations. Usage of any data is at your own risk.

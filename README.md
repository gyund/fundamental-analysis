[![python](https://github.com/gyund/fundamental-analysis/actions/workflows/python.yml/badge.svg?branch=main)](https://github.com/gyund/fundamental-analysis/actions/workflows/python.yml)
[![Coverage Status](https://coveralls.io/repos/github/gyund/fundamental-analysis/badge.svg?branch=main&kill_cache=1)](https://coveralls.io/github/gyund/fundamental-analysis?branch=main)

# Ticker (smart stock analysis)

**__EARLY DEVELOPMENT__**

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

# Perform analysis
python -m ticker analyze --tickers aapl,msft
```

More information can be found in our [documentation](https://gyund.github.io/fundamental-analysis/)

### Testing

Run tests by running the following:

```sh
pytest
```

The test infrastructure supports running integration tests using real network endpoints using environment flags, but this is still a work in progress and should be avoided at the moment. Documentation will be provided on how to run these once it has matured and is ready.

## Disclaimer

This projects seeks to use publicly available information about stocks and securities to help perform long term risk analysis. Results provided from this project are for academic use only and are not considered advice or recommendations. Usage of any data is at your own risk.  

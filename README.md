<p align="center">
    <a href='https://github.com/gyund/fundamental-analysis/blob/main/LICENSE'><img alt="License" src="https://img.shields.io/github/license/gyund/fundamental-analysis"></a>
    <img alt="License" src="https://img.shields.io/badge/python-3.10%2B-blue">
    <a href='https://github.com/gyund/fundamental-analysis/actions/workflows/python.yml'><img alt="Test Status" src="https://github.com/gyund/fundamental-analysis/actions/workflows/python.yml/badge.svg?service=github"></a>
    <a href='https://coveralls.io/github/gyund/fundamental-analysis?branch=main'><img src='https://coveralls.io/repos/github/gyund/fundamental-analysis/badge.svg?branch=main&service=github' alt='Coverage Status' /></a>
    <img alt="Development Status" src="https://img.shields.io/badge/status-early%20development-red">
</p>

# Ticker - Stock Analysis Framework

The goal of this project is aggregate a variety of ways to consume information about a particular equity traded on the US stock market and provide a modular mechanism to process it. Core tenants of this project include:

- **Heavy data caching** - don't download static data more than once
- **Efficient use of storage** - leave data compressed while not in use
- **Batch Processing** - We can't store all information in memory, so break problems up
- **Speed** - Find and avoid bottlenecks of big data processing

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

More information can be found in our [documentation](https://gyund.github.io/fundamental-analysis/)

## Disclaimer

This project seeks to use publicly available information to perform security analysis and
help perform long term risk analysis. Results provided from this project are generally for 
academic use only and are not considered advice or recommendations. This project makes no
performance claims or guarantees. Please read the [license](LICENSE) 
for this project. Usage of any data is at your own risk.

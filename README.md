<p align="center">
    <a href='https://github.com/gyund/fundamental-analysis/blob/main/LICENSE'><img alt="License" src="https://img.shields.io/github/license/gyund/fundamental-analysis"></a>
    <img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/stocktracer">
    <a href='https://github.com/gyund/fundamental-analysis/actions/workflows/python.yml'><img alt="Test Status" src="https://github.com/gyund/fundamental-analysis/actions/workflows/python.yml/badge.svg?service=github"></a>
    <a href='https://coveralls.io/github/gyund/fundamental-analysis?branch=main'><img src='https://coveralls.io/repos/github/gyund/fundamental-analysis/badge.svg' alt='Coverage Status' /></a>
    <a href="https://beartype.readthedocs.io"><img src="https://raw.githubusercontent.com/beartype/beartype-assets/main/badge/bear-ified.svg?" alt="bear-ified"></a>
    <a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code style: black"></a>
    <a href='https://pypi.org/project/stocktracer/'><img alt="PyPI - Python Version" src="https://img.shields.io/pypi/v/stocktracer"></a>
    <img alt="PyPI - Downloads" src="https://img.shields.io/pypi/dm/stocktracer">
    <img alt="PyPI - Status" src="https://img.shields.io/pypi/status/stocktracer">
</p>

# StockTracer

**Stock Analysis Framework**

The goal of this project is aggregate a variety of ways to consume information about a particular equity traded on the US stock market and provide a modular mechanism to process it. Core tenants of this project include:

- **Heavy data caching** - don't download static data more than once
- **Efficient use of storage** - leave data compressed while not in use
- **Batch Processing** - We can't store all information in memory, so break problems up
- **Speed** - Find and avoid bottlenecks of big data processing

## Requirements

- `python 3.10+`

## Getting Started

### Users

```sh
# basic install
pip install stocktracer

# with tensorflow dependencies for analysis modules
pip install stocktracer[tensorflow]

# Perform analysis
stocktracer analyze --tickers aapl,msft > report.txt

# Help
stocktracer

```

For development guides, see our [documentation](https://gyund.github.io/fundamental-analysis/getting-started)

## Disclaimer

This project seeks to use publicly available information to perform security analysis and
help perform long term risk analysis. Results provided from this project are generally for 
academic use only and are not considered advice or recommendations. This project makes no
performance claims or guarantees. Please read the [license](LICENSE) 
for this project. Usage of any data is at your own risk.

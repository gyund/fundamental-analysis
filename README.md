[![python](https://github.com/gyund/fundamental-analysis/actions/workflows/python.yml/badge.svg?branch=main)](https://github.com/gyund/fundamental-analysis/actions/workflows/python.yml)

# Smart Fundamental Analysis

**__UNDER DEVELOPMENT__**

The goal of this project is to generate data that is consumable in both human readable format as well as JSON to better analyze and make sense of the intrinsic value of publicly traded companies.

The tool seeks to provide extensible options for consuming data from different data sources. There are different methods for gathering data:

- SEC (personal/commercial)
- Site Scraping (only personal)

Generally speaking, scraping sites is only for personal use and to vet the APIs. The tool will provide warnings when using options that may have additional restrictions to their use and will require a `--force` option to ensure that you understand the rules surrounding their use. 

Additionally, the tools will utilize file based caching to limit interaction with expensive networking resources. Since fundamental analysis generally requires a long term view of companies with a proven track record, you generally will be downloading an initial history for a given equity and updating quarterly or annually based on new information.

## Requirements

- `python 3.8+`

## Getting Started 

```sh
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

## Updating Dependencies

```sh
pip freeze > requirements.txt
```

## Disclaimer

This projects seeks to use publicly available information about stocks and securities to help perform long term risk analysis. Results provided from this project are for academic use only and are not considered advice or recommendations. Usage of any data is at your own risk.  

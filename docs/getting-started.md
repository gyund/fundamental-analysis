# Getting Started

**Requirements:** python 3.10+

## Install

Make sure you have `pipenv` installed through a package manager or through pip.

=== "git"

    ```sh
    # Clone Repository
    git clone https://github.com/gyund/fundamental-analysis.git
    cd fundamental-analysis.git

    pipenv install --dev

    # Perform analysis
    PYTHONPATH=src pipenv run python -m stocktracer analyze --tickers aapl,msft

    # Help
    PYTHONPATH=src pipenv run python -m stocktracer

    # Run Unit Tests
    pipenv run pytest
    ```

## Generating a Basic Report

```sh
# Perform analysis
python -m ticker analyze --tickers aapl,msft
```


## Plugins

If you wish to use your own analysis plugin, create your own module that implements this interface:

```python
from ticker.data.sec import DataSelector as SecDataSelector
from ticker.filter import Selectors,SecFilter

def analyze(options: Options) -> None:
    print("This is where we would start to process information, but we're not right now")

```

Then call the tool in the following manner:

```sh
python -m ticker analyze --tickers aapl,msft --analysis_plugin 'mypkg.analysis'
```

## Testing

Run tests by running the following:

```sh
pytest
```

If you wish to run tests using real network resources, such as downloading real reports and processing them, run the following:

```sh
pytest --run-webtest
```

Note that all data sets will be cached in the directory `${cwd}/.ticker-cache/` for both real and test runs. Expiry for quarterly reports are cached for 5 years and ticker mappings for `CIK -> Ticker` conversion are cached on a yearly basis. You generally won't be researching companies with less than a year's worth of reports though this could cause recently listed companies to lack `CIK -> Ticker` conversions for up to two years from poor timing. Just delete `${cwd}/.ticker-cache/tickers.sqlite` to get the latest.

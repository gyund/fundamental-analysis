# Getting Started

**Requirements:** python 3.10+

## Install

=== "pip"
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

=== "git"

    ```sh
    # Clone Repository
    git clone https://github.com/gyund/fundamental-analysis.git
    cd fundamental-analysis.git

    # Normal development install
    poetry install --sync # (1)!

    # With mkdocs
    poetry install --sync --with docs
    
    # with mkdocs and tensorflow dependency support
    poetry install --sync --extras "tensorflow"  --with docs

    # Perform analysis
    PYTHONPATH=src poetry run python -m stocktracer analyze --tickers aapl,msft
    PYTHONPATH=src poetry run python -m stocktracer analyze --tickers aapl,msft -a stocktracer.analysis.diluted_eps
    PYTHONPATH=src poetry run python -m stocktracer analyze --tickers aapl,msft -a stocktracer.analysis.diluted_eps --report-format csv
    PYTHONPATH=src poetry run python -m stocktracer analyze --tickers aapl,msft -a stocktracer.analysis.diluted_eps --report-format json --report-file my_results.json

    # Help
    PYTHONPATH=src poetry run python -m stocktracer

    # Run Unit Tests
    poetry run pytest
    ```
    
    1. Make sure you have [poetry](https://python-poetry.org/docs/) installed.

## Generating a Basic Report

=== "pip"
    ```sh
    # Perform analysis
    stocktracer analyze --tickers appl,msft > report.txt
    ```

=== "git"
    ```sh
    # Perform analysis
    python -m stocktracer analyze --tickers aapl,msft > report.txt
    ```

!!! tip
    If you want to figure out a list of tags you can filter the reports on, run the default analysis report. This shows the annual report and will then filter out any columns that contain `null` or `NaN` values. From here, you can establish what algorithms you can use and apply consistently across the stocks of interest. You may find that different sectors or 10-K/10-Q reports will have different data sets.


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

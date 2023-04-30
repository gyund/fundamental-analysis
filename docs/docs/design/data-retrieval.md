# Data Retrieval

There's is A LOT of data, and we can't download gigabytes of data. The general idea is that we:

- Provide a list of tickers to retrieve reports for
- Download and cache the reports for those tickers (cache works by starting from the last report date to the present)
- Delete reports that are too old to be useful
- Perform analysis on them
- If the ticker is considered "garbage quality", we will put it in the list of stocks not to query again in the future. If it is ever suggested again, there will be a warning but it will be silently ignored unless the user wants to override it. We will delete the cache of Edgar reports for stocks that are considered "garbage".

## Edgar Downloads

### SEC Financial Data Sets

!!! success "Planned Approach"

**Source:** [Financial Data Sets](https://www.sec.gov/dera/data/financial-statement-data-sets)

The SEC provides data sets in the form of compressed text files. The quarterly downloads are around 50MB but they decompress to a couple hundred MB.

The important parts of the zip file are as follows:

- sub.txt
- num.txt

This `sub.txt` file contains contents similar to the following:

``` title="sub.txt"
0000320193-23-000006	320193	APPLE INC	3571	US	CA	CUPERTINO	95014	ONE APPLE PARK WAY		(408) 996-1010	US	CA	CUPERTINO	95014	ONE APPLE PARK WAY		US	CA	942404110	APPLE INC	20070109	1-LAF	0	0930	10-Q	20221231	2023	Q1	20230203	2023-02-02 18:02:00.0	0	1	aapl-20221231_htm.xml	1
```

The first item contains the adsh value. This essentially maps to the document that contains all the information for this report. The `cik` is the second number. This is what is commonly used to identify the company. Further down, we have a column that specifies the report. In this case, above we have a `10-Q` filing for a quarterly report. The second to last line also contains the xml file, which is conveniently prefixed with the ticker number of the company.

The next document, `num.txt`, contains all the important financial information. Here's an example

``` title="num.txt"
0000320193-23-000006	AssetsCurrent	us-gaap/2022		20220930	0	USD	135405000000.0000	
```

You can see how easy it is now to pull financial information out of these data sets. In this one line, we can map the report to the value. In this case, the value corresponds to `AssetsCurrent`.

### Data Storage

Our design will attempt to use [pandas](https://pandas.pydata.org/) to extract the data dumps and then filter down the data sets to contain only relevant information. There are important points to identify as part of R&D in this area.

!!! warning "Warning - There be dragons!!!"

First, large data sets are a problem for various databases, pandas included. In our initial design we tried to push the limits of pandas by loading as much data inside the DataFrame except for a few useless columns. After about 3-4 quarters worth of data from over 7000 ticker symbols, the panda cried uncle with a glorified, but not so glorified:

```sh
tests/test_sec.py ss........                                                                                    [ 58%]
tests/test_sec_network.py .s.Killed
```

The `Killed` message is a signal from the OS that you've successfully exhausted all the memory of the system and they're *ending you* unceremoniously with a `kill -9`. 

So what's next? Well we're still going to try and use [pandas](https://pandas.pydata.org/), just for the sake of trying to do a few things:

- Solve interesting algorithmic problems
- Keep our storage size small
- Use as much native python code as possible for simplifying usage and analysis for the end-user
- Avoid taking the easy way out by just throwing more memory and storage at the problem

This means that we'll need to refactor the processing a bit so that we can pass a set of analytics to collect while looking at a particular stock ticker. This will allow us to scrape a very small subset of information about a company without unpacking these 50MB compressed archives (which can easily take 0.5 GB of storage per quarter uncompressed)

Here is an example of the data scraped from AAPL for q after the refactoring.

```python
# Filter used in test
def filter_aapl() -> Filter.Selectors:
    return Filter.Selectors(
        ticker_filter={"aapl"},
        sec_filter=Filter.SecFilter(
            tags=["EntityCommonStockSharesOutstanding"],
            years=0,  # Just want the current
            last_report=ReportDate(year=2023, quarter=1),
            only_annual=False,
        ),  # We want the 10-Q
    )

There are 67 records about apple (test_sec_network.py:55)
2023-04-30 17:53:05 [   DEBUG]
```

!!! bug
    Note there's a bug in the filtering in this example. The `tags` field should have reduced this to one row, but it did not.

```markdown
|                                                                                                                                                    | uom    |         value |   fy | fp   |
|:---------------------------------------------------------------------------------------------------------------------------------------------------|:-------|--------------:|-----:|:-----|
| ('0000320193-23-000006', 'EntityCommonStockSharesOutstanding', 320193)                                                                             | shares |   1.58219e+10 | 2023 | Q1   |
| ('0000320193-23-000006', 'AccountsPayableCurrent', 320193)                                                                                         | USD    |   5.7918e+10  | 2023 | Q1   |
| ('0000320193-23-000006', 'AccountsPayableCurrent', 320193)                                                                                         | USD    |   6.4115e+10  | 2023 | Q1   |
| ('0000320193-23-000006', 'AccountsReceivableNetCurrent', 320193)                                                                                   | USD    |   2.3752e+10  | 2023 | Q1   |
| ('0000320193-23-000006', 'AccountsReceivableNetCurrent', 320193)                                                                                   | USD    |   2.8184e+10  | 2023 | Q1   |
| ('0000320193-23-000006', 'AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment', 320193)                                       | USD    |   6.8044e+10  | 2023 | Q1   |
| ('0000320193-23-000006', 'AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment', 320193)                                       | USD    |   7.234e+10   | 2023 | Q1   |
| ('0000320193-23-000006', 'AccumulatedOtherComprehensiveIncomeLossNetOfTax', 320193)                                                                | USD    |  -1.2912e+10  | 2023 | Q1   |
| ('0000320193-23-000006', 'AccumulatedOtherComprehensiveIncomeLossNetOfTax', 320193)                                                                | USD    |  -1.1109e+10  | 2023 | Q1   |
| ('0000320193-23-000006', 'AllocatedShareBasedCompensationExpense', 320193)                                                                         | USD    |   2.905e+09   | 2023 | Q1   |
| ('0000320193-23-000006', 'AllocatedShareBasedCompensationExpense', 320193)                                                                         | USD    |   2.265e+09   | 2023 | Q1   |
| ('0000320193-23-000006', 'Assets', 320193)                                                                                                         | USD    |   3.52755e+11 | 2023 | Q1   |
| ('0000320193-23-000006', 'Assets', 320193)                                                                                                         | USD    |   3.46747e+11 | 2023 | Q1   |
| ('0000320193-23-000006', 'AssetsCurrent', 320193)                                                                                                  | USD    |   1.35405e+11 | 2023 | Q1   |
| ('0000320193-23-000006', 'AssetsCurrent', 320193)                                                                                                  | USD    |   1.28777e+11 | 2023 | Q1   |
| ('0000320193-23-000006', 'AssetsNoncurrent', 320193)                                                                                               | USD    |   2.1735e+11  | 2023 | Q1   |
| ('0000320193-23-000006', 'AssetsNoncurrent', 320193)                                                                                               | USD    |   2.1797e+11  | 2023 | Q1   |
| ('0000320193-23-000006', 'AvailableForSaleSecuritiesDebtMaturitiesRollingAfterYearTenFairValue', 320193)                                           | USD    |   1.7355e+10  | 2023 | Q1   |
| ('0000320193-23-000006', 'AvailableForSaleSecuritiesDebtMaturitiesRollingYearSixThroughTenFairValue', 320193)                                      | USD    |   1.4243e+10  | 2023 | Q1   |
| ('0000320193-23-000006', 'AvailableForSaleSecuritiesDebtMaturitiesRollingYearTwoThroughFiveFairValue', 320193)                                     | USD    |   8.2497e+10  | 2023 | Q1   |
| ('0000320193-23-000006', 'AvailableForSaleSecuritiesDebtMaturitiesSingleMaturityDate', 320193)                                                     | USD    |   1.14095e+11 | 2023 | Q1   |
| ('0000320193-23-000006', 'CashAndCashEquivalentsAtCarryingValue', 320193)                                                                          | USD    |   2.3646e+10  | 2023 | Q1   |
| ('0000320193-23-000006', 'CashAndCashEquivalentsAtCarryingValue', 320193)                                                                          | USD    |   2.0535e+10  | 2023 | Q1   |
| ('0000320193-23-000006', 'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents', 320193)                                                  | USD    |   3.5929e+10  | 2023 | Q1   |
| ('0000320193-23-000006', 'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents', 320193)                                                  | USD    |   3.863e+10   | 2023 | Q1   |
| ('0000320193-23-000006', 'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents', 320193)                                                  | USD    |   2.4977e+10  | 2023 | Q1   |
| ('0000320193-23-000006', 'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents', 320193)                                                  | USD    |   2.1974e+10  | 2023 | Q1   |
| ('0000320193-23-000006', 'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect', 320193) | USD    |   2.701e+09   | 2023 | Q1   |
| ('0000320193-23-000006', 'CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect', 320193) | USD    |  -3.003e+09   | 2023 | Q1   |
| ('0000320193-23-000006', 'CommercialPaper', 320193)                                                                                                | USD    |   9.982e+09   | 2023 | Q1   |
| ('0000320193-23-000006', 'CommercialPaper', 320193)                                                                                                | USD    |   1.743e+09   | 2023 | Q1   |
| ('0000320193-23-000006', 'CommitmentsAndContingencies', 320193)                                                                                    | USD    | nan           | 2023 | Q1   |
| ('0000320193-23-000006', 'CommitmentsAndContingencies', 320193)                                                                                    | USD    | nan           | 2023 | Q1   |
| ('0000320193-23-000006', 'CommonStockDividendsPerShareDeclared', 320193)                                                                           | USD    |   0.22        | 2023 | Q1   |
| ('0000320193-23-000006', 'CommonStockDividendsPerShareDeclared', 320193)                                                                           | USD    |   0.23        | 2023 | Q1   |
| ('0000320193-23-000006', 'CommonStockParOrStatedValuePerShare', 320193)                                                                            | USD    |   0           | 2023 | Q1   |
| ('0000320193-23-000006', 'CommonStockParOrStatedValuePerShare', 320193)                                                                            | USD    |   0           | 2023 | Q1   |
| ('0000320193-23-000006', 'CommonStockSharesAuthorized', 320193)                                                                                    | shares |   5.04e+10    | 2023 | Q1   |
| ('0000320193-23-000006', 'CommonStockSharesAuthorized', 320193)                                                                                    | shares |   5.04e+10    | 2023 | Q1   |
| ('0000320193-23-000006', 'CommonStockSharesIssued', 320193)                                                                                        | shares |   1.59434e+10 | 2023 | Q1   |
| ('0000320193-23-000006', 'CommonStockSharesIssued', 320193)                                                                                        | shares |   1.58424e+10 | 2023 | Q1   |
| ('0000320193-23-000006', 'CommonStockSharesOutstanding', 320193)                                                                                   | shares |   1.59434e+10 | 2023 | Q1   |
| ('0000320193-23-000006', 'CommonStockSharesOutstanding', 320193)                                                                                   | shares |   1.58424e+10 | 2023 | Q1   |
| ('0000320193-23-000006', 'CommonStocksIncludingAdditionalPaidInCapital', 320193)                                                                   | USD    |   6.4849e+10  | 2023 | Q1   |
| ('0000320193-23-000006', 'CommonStocksIncludingAdditionalPaidInCapital', 320193)                                                                   | USD    |   6.6399e+10  | 2023 | Q1   |
| ('0000320193-23-000006', 'ComprehensiveIncomeNetOfTax', 320193)                                                                                    | USD    |   3.354e+10   | 2023 | Q1   |
| ('0000320193-23-000006', 'ComprehensiveIncomeNetOfTax', 320193)                                                                                    | USD    |   2.8195e+10  | 2023 | Q1   |
| ('0000320193-23-000006', 'ContractWithCustomerLiability', 320193)                                                                                  | USD    |   1.24e+10    | 2023 | Q1   |
| ('0000320193-23-000006', 'ContractWithCustomerLiability', 320193)                                                                                  | USD    |   1.26e+10    | 2023 | Q1   |
| ('0000320193-23-000006', 'ContractWithCustomerLiabilityCurrent', 320193)                                                                           | USD    |   7.912e+09   | 2023 | Q1   |
| ('0000320193-23-000006', 'ContractWithCustomerLiabilityCurrent', 320193)                                                                           | USD    |   7.992e+09   | 2023 | Q1   |
| ('0000320193-23-000006', 'ContractWithCustomerLiabilityRevenueRecognized', 320193)                                                                 | USD    |   3e+09       | 2023 | Q1   |
| ('0000320193-23-000006', 'ContractWithCustomerLiabilityRevenueRecognized', 320193)                                                                 | USD    |   3.4e+09     | 2023 | Q1   |
| ('0000320193-23-000006', 'CostOfGoodsAndServicesSold', 320193)                                                                                     | USD    |   6.9702e+10  | 2023 | Q1   |
| ('0000320193-23-000006', 'CostOfGoodsAndServicesSold', 320193)                                                                                     | USD    |   6.6822e+10  | 2023 | Q1   |
| ('0000320193-23-000006', 'DebtSecuritiesAvailableForSaleRestricted', 320193)                                                                       | USD    |   1.27e+10    | 2023 | Q1   |
| ('0000320193-23-000006', 'DebtSecuritiesAvailableForSaleRestricted', 320193)                                                                       | USD    |   1.36e+10    | 2023 | Q1   |
| ('0000320193-23-000006', 'DepreciationDepletionAndAmortization', 320193)                                                                           | USD    |   2.697e+09   | 2023 | Q1   |
| ('0000320193-23-000006', 'DepreciationDepletionAndAmortization', 320193)                                                                           | USD    |   2.916e+09   | 2023 | Q1   |
| ('0000320193-23-000006', 'DerivativeFairValueOfDerivativeNet', 320193)                                                                             | USD    |   4.12e+08    | 2023 | Q1   |
| ('0000320193-23-000006', 'EarningsPerShareBasic', 320193)                                                                                          | USD    |   2.11        | 2023 | Q1   |
| ('0000320193-23-000006', 'EarningsPerShareBasic', 320193)                                                                                          | USD    |   1.89        | 2023 | Q1   |
| ('0000320193-23-000006', 'EarningsPerShareDiluted', 320193)                                                                                        | USD    |   2.1         | 2023 | Q1   |
| ('0000320193-23-000006', 'EarningsPerShareDiluted', 320193)                                                                                        | USD    |   1.88        | 2023 | Q1   |
| ('0000320193-23-000006', 'EmployeeServiceShareBasedCompensationNonvestedAwardsTotalCompensationCostNotYetRecognized', 320193)                      | USD    |   2.55e+10    | 2023 | Q1   |
| ('0000320193-23-000006', 'EmployeeServiceShareBasedCompensationTaxBenefitFromCompensationExpense', 320193)                                         | USD    |   1.536e+09   | 2023 | Q1   |
| ('0000320193-23-000006', 'EmployeeServiceShareBasedCompensationTaxBenefitFromCompensationExpense', 320193)                                         | USD    |   1.178e+09   | 2023 | Q1   |
```

<!--
### sec-edgar

The first thing that's required for analysis is report filed with the SEC. One of the ways this can be retrieved is using [sec-edgar](https://github.com/sec-edgar/sec-edgar). All this python utility does is facilitate the lookup of the desired document for the desired ticker and download the reports.

``` python title="Example"
import secedgar as se
import os
from secedgar.client import NetworkClient
from dateutil.relativedelta import relativedelta
from datetime import date


# SEC User Agent requirements
my_client = NetworkClient(
    user_agent='User (agent@someprovider.com)', backoff_factor=1, rate_limit=9)

# start_date=date.today()-relativedelta(years=2
my_start_date = date ( 2020 , 12 , 10 ) 
my_end_date = date ( 2021 , 12 , 31 )

my_filings = se.filings(cik_lookup=['aapl'],
                            #    filing_type=se.FilingType.FILING_10Q, # quarterly
                               filing_type=se.FilingType.FILING_10K, # annual
                            #    count=4,
                               client=my_client,
                               start_date=my_start_date,
                               end_date=my_end_date)

my_filings.save(os.getcwd() + '/.edgar-filings')
```

These reports are large and not compact. In order to really get to what we want, I found the SEC [Financial Data Sets](https://www.sec.gov/dera/data/financial-statement-data-sets). Now these seem to be ordered and mapped using different files, but it's a lot more concise. However, it only includes quarterly reports, not annual.

#### Notes

- We will need to use the start/end dates for this, which can be derived from existing reports. 
- The user agent will need to be provided

## Yahoo Finance

!!! failure
    This particular API failed on one of the first smoke tests implemented due to decryption issues. I'll have to see how we did this in the past, but this is also likely going to be an unreliable and less versatile approach. For now, we will document the progress but efforts will be focused on accessing this information from the [edgar reports](#edgar-downloads) .

!!! important
    This library is for personal use only. Please see documentation on [yfinance](https://github.com/ranaroussi/yfinance) licensing notices regarding Yahoo's APIs. Extensive work has been made to minimize loads and requests through caching mechanisms. This project uses a sqlite cache for the results.

For testing and for personal use until we can get [Edgar processing](#edgar-downloads) working, we will be using the [yfinance](https://github.com/ranaroussi/yfinance) python library.

-->

---
tags:
  - Design
  - In-Progress
---

# Data Retrieval

There's is A LOT of data, and we can't download gigabytes of data. The general idea is that we:

- Provide a list of tickers to retrieve reports for
- Download and cache the reports for those tickers (cache works by starting from the last report date to the present)
- Delete reports that are too old to be useful
- Perform analysis on them
- If the ticker is considered "garbage quality", we will put it in the list of stocks not to query again in the future. If it is ever suggested again, there will be a warning but it will be silently ignored unless the user wants to override it. We will delete the cache of Edgar reports for stocks that are considered "garbage".

## Edgar Downloads

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

### Notes

- We will need to use the start/end dates for this, which can be derived from existing reports. 
- The user agent will need to be provided

## Yahoo Finance

!!! failure
    This particular API failed on one of the first smoke tests implemented due to decryption issues. I'll have to see how we did this in the past, but this is also likely going to be an unreliable and less versatile approach. For now, we will document the progress but efforts will be focused on accessing this information from the [edgar reports](#edgar-downloads) .

!!! important
    This library is for personal use only. Please see documentation on [yfinance](https://github.com/ranaroussi/yfinance) licensing notices regarding Yahoo's APIs. Extensive work has been made to minimize loads and requests through caching mechanisms. This project uses a sqlite cache for the results.

For testing and for personal use until we can get [Edgar processing](#edgar-downloads) working, we will be using the [yfinance](https://github.com/ranaroussi/yfinance) python library.

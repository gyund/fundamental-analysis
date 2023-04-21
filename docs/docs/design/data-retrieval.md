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

The first thing that's required for analysis is report filed with the SEC. These can be retrieved using [sec-edgar](https://github.com/sec-edgar/sec-edgar). All this python utility does is facilitate the lookup of the desired document for the desired ticker.

### Notes

- We will need to use the start/end dates for this, which can be derived from existing reports. 
- The user agent will need to be provided
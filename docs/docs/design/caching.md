# Slow is Fast

It's important not to rush past figuring out where performance is a problem and where it can be improved. As we encounter areas where performance is/was a problem, we'll post a writeup here.

## Network

We want to be responsible citizens when downloading from the SEC website. Generally, the defaults are as follows:

| Description          | Cache Duration | Typical Size      |
| -------------------- | -------------- | ----------------- |
| CIK Tickers          | 1 Year         | < 1MB             |
| Quarterly Data Dumps | 5 Years        | ~50MB per quarter |

We experimented with a few different caches. What seemed to perform reasonably well was SQLite with pickled serialization. Initially we thought that FileCache would have performed well, but it seems that serializing to JSON may have been impacting the performance.


# Accessing the Report

The general concept is that the report could be accessed locally or remotely via cached results created from the report generation. Because companies are like battleships, fundamental analysis of short term data is unlikely to have much of an impact on long-term results so generating period reports in a static format keeps the access time $O(1)$. 

## Local Access

Local reports could be accessed or displayed as JSON or TEXT.

## Remote Access

For the API specification, we could use [Swagger](https://swagger.io/) to generate a specification that accesses the statically generated JSON reports via HTTP GET requests on a server hosting the reports. TBD

Once the API specification is in place, we'll use [Flutter](https://flutter.dev/) to create web/mobile apps to access and display the data in a more user friendly format.
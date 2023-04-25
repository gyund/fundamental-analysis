---
tags:
  - Install
---

# Getting Started 

**Requirements:** python 3.10+

## Install

!!! info
    This is the proposed design and approach for how the tool will function. Implementation is currently under development.

=== "git"
    ```sh
    # Clone Repository 
    git clone https://github.com/gyund/fundamental-analysis.git
    cd fundamental-analysis.git

    # Setup python virtual environment
    python3 -m venv venv
    . venv/bin/activate
    pip install -r requirements.txt

    # Perform analysis / Run tool
    python -m ticker analyze --tickers aapl,msft
    ```

## Generating a Basic Report

```sh
# Perform analysis
python -m ticker analyze --tickers aapl,msft
```
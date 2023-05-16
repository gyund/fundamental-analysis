#!/bin/bash

dir=`dirname $0`
results_dir='.results'
set -e

pushd ${dir} > /dev/null
mkdir -p ${results_dir}
echo "Running default analysis..."
PYTHONPATH=src pipenv run python -m stocktracer analyze --refresh --tickers aapl,msft,tmo > ${results_dir}/default.txt

echo "Running diluted_eps analysis..."
PYTHONPATH=src pipenv run python -m stocktracer analyze --refresh --tickers aapl,msft,tmo -a stocktracer.analysis.diluted_eps --report-file=${results_dir}/diluted_eps.md

popd > /dev/null
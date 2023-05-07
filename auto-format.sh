#!/bin/bash

dir=`dirname $0`

# Stop script on first failure
set -e

pushd $dir > /dev/null
echo "Running auto-format tools..."
pipenv run ruff check --fix .
pipenv run isort src/
pipenv run black src/

echo "Running pydoctest..."
PYTHONPATH=src pipenv run pydoctest --config pydocktest.json

# Note: false positivies in the src/test from fixtures, etc.
echo "Running pylint..."
pipenv run pylint src/stocktracer
echo "Running pydocstyle..."
pipenv run pydocstyle
echo "success!
popd > /dev/null
#!/bin/bash

dir=`dirname $0`
PYLINT_FLAG=${PYLINT_FLAG:=""}

# Stop script on first failure
set -e

pushd $dir > /dev/null
echo "Running auto-format tools..."
poetry run ruff check --fix .
poetry run isort src/
poetry run black src/

echo "Running pydoctest..."
PYTHONPATH=src poetry run pydoctest --config pydocktest.json

# Note: false positivies in the src/test from fixtures, etc.
echo "Running pylint..."
poetry run pylint ${PYLINT_FLAG} src/stocktracer
echo "Running pydocstyle... (not required to pass)"
poetry run pydocstyle || echo "warnings - see above for recommendations"
echo "success!"
popd > /dev/null
#!/bin/bash

dir=`dirname $0`

pushd $dir > /dev/null
pipenv run ruff check --fix .
pipenv run black src/
pipenv run isort src/
PYTHONPATH=src pipenv run pydoctest --config pydocktest.json
popd > /dev/null
#!/bin/bash

dir=`dirname $0`

set -e

pushd ${dir} > /dev/null
rm -rf dist/
pipenv requirements > requirements.txt
pipenv run pip install build
pipenv run python -m build
pipenv uninstall --all
pipenv run pip install dist/*.whl
rm requirements.txt
popd > /dev/null
#!/bin/bash

dir=`dirname $0`

set -e

pushd ${dir} > /dev/null
rm -rf dist/
poetry build
poetry env remove --all
poetry run pip install dist/*.whl
popd > /dev/null
#!/bin/bash

dir=`dirname $0`

set -e

pushd ${dir} > /dev/null
rm -rf dist/
hatch build
python -m pip install dist/*.whl
popd > /dev/null
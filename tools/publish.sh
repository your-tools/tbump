#!/bin/bash

set -e

rm -fr dist/
python setup.py sdist bdist_wheel
twine upload dist/*

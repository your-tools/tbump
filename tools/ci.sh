#!/bin/bash

set -e

pipenv run python setup.py develop
pipenv run python ci/ci.py

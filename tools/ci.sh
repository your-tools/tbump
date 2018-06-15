#!/bin/bash

set -x
set -e

pipenv check
pipenv run pycodestyle .
pipenv run pyflakes .
pipenv run mypy --strict --ignore-missing-imports tbump
pipenv run pytest --cov . --cov-report term-missing

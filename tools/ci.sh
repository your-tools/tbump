#!/bin/bash

set -x
set -e

pipenv check
pipenv run pyflakes .
pipenv run pycodestyle .
pipenv run pytest --cov . --cov-report term-missing

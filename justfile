poetry := "python -m poetry"
poetry_run := poetry + " run"

default:
    just --list --unsorted

setup:
    {{ poetry }} install

lint:
    {{ poetry_run }} black --check .
    {{ poetry_run }} isort --check .
    {{ poetry_run }} flake8  .
    {{ poetry_run }} mypy

test:
    {{ poetry_run }} pytest

format:
    {{ poetry_run }} black .
    {{ poetry_run }} isort .

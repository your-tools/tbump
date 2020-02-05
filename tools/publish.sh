#!/bin/bash

set -e

rm -fr dist/
poetry build
poetry publish

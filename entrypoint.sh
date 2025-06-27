#!/bin/bash

black .

pybabel compile -d app/locales

# shellcheck disable=SC2155
export PYTHONPATH="$(pwd)"


python app/server/server.py

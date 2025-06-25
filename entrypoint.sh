#!/bin/bash

black .

pybabel compile -d app/locales

# shellcheck disable=SC2155
export PYTHONPATH="$(pwd)"

alembic revision --autogenerate -m "initial migration"
alembic upgrade head

python app/server/server.py

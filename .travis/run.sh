#!/bin/bash

set -e
set -x

source ~/.venv/bin/activate
which python
tox -e $TOX_ENV -- $TOX_FLAGS

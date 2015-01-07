#!/bin/bash

set -e
set -x

if [[ "$(uname -s)" == "Darwin" ]]; then
    eval "$(pyenv init -)"
fi

source ~/.venv/bin/activate
# run the tests for a single env
tox -e $TOXENV

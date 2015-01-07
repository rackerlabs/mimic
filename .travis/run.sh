#!/bin/bash

set -e
set -x

source ~/.venv/bin/activate
if [[ "$(uname -s)" == "Darwin" ]]; then
    eval "$(pyenv init -)"
fi

tox -e "${TOXENV}"

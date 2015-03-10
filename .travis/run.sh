#!/bin/bash

set -e
set -x

if [[ "$(uname -s)" == "Darwin" ]]; then
    eval "$(pyenv init -)"
fi

source ~/.venv/bin/activate
tox --develop -e $TOX_ENV -- $TOX_FLAGS

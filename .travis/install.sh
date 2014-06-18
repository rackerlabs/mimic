#!/bin/bash

# Getting around a buggy PyPy in Travis
# Script from pyca/cryptography

set -e
set -x

if [[ "${TOX_ENV}" == "pypy"* ]]; then
    sudo add-apt-repository -y ppa:pypy/ppa
    sudo apt-get -y update
    sudo apt-get install -y pypy pypy-dev

    # This is required because we need to get rid of the Travis installed PyPy
    # or it'll take precedence over the PPA installed one.
    sudo rm -rf /usr/local/pypy/bin
fi

if [[ "${TOX_ENV}" == "docs-spellcheck" ]]; then
    if [[ "$DARWIN" = true ]]; then
        brew update
        brew install enchant
    else
        sudo apt-get -y update
        sudo apt-get install libenchant-dev
    fi
fi

pip --version
pip install --upgrade pip
pip install tox coveralls

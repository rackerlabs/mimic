#!/bin/bash

set -e
set -x

if [[ "$(uname -s)" == 'Darwin' ]]; then
    DARWIN=true
else
    DARWIN=false
fi

if [[ "$DARWIN" = true ]]; then
    brew update

    if which pyenv > /dev/null; then
        eval "$(pyenv init -)"
    fi

    case "${TOXENV}" in
        py26)
            curl -O https://bootstrap.pypa.io/get-pip.py
            sudo python get-pip.py
            ;;
        py27)
            curl -O https://bootstrap.pypa.io/get-pip.py
            sudo python get-pip.py
            ;;
        pypy)
            brew upgrade pyenv
            pyenv install pypy-2.4.0
            pyenv global pypy-2.4.0
            ;;
        docs)
            curl -O https://bootstrap.pypa.io/get-pip.py
            sudo python get-pip.py
            ;;
	bundle)
	    curl -O https://bootstrap.pypa.io/get-pip.py
            sudo python get-pip.py
	    #brew install python
	    ;;
    esac
    pyenv rehash

else
    sudo add-apt-repository -y ppa:fkrull/deadsnakes

    if [[ "${TOXENV}" == "pypy" ]]; then
        sudo add-apt-repository -y ppa:pypy/ppa
    fi

    sudo apt-get -y update

    case "${TOXENV}" in
        py26)
            sudo apt-get install python2.6 python2.6-dev
            ;;
        py27)
            sudo apt-get install python2.7 python2.7-dev
            ;;
        pypy)
            sudo apt-get install --force-yes pypy pypy-dev
            ;;
        docs)
            sudo apt-get install libenchant-dev
            ;;
    esac
fi

sudo pip install virtualenv
virtualenv ~/.venv
source ~/.venv/bin/activate
pip install tox coveralls

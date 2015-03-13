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

    case "${TOX_ENV}" in
        py26)
            brew upgrade pyenv
            pyenv install 2.6.9
            pyenv global 2.6.9
            ;;
        py27)
            brew upgrade pyenv
            pyenv install 2.7.8
            pyenv global 2.7.8
            ;;
        pypy)
            brew upgrade pyenv
            pyenv install pypy-2.5.0
            pyenv global pypy-2.5.0
            ;;
        docs)
            curl -O https://bootstrap.pypa.io/get-pip.py
            sudo python get-pip.py
            ;;
    esac
    pyenv rehash

else

    sudo add-apt-repository -y ppa:fkrull/deadsnakes

    if [[ "${TOX_ENV}" == "pypy" ]]; then
        sudo add-apt-repository -y ppa:pypy/ppa
    fi

    sudo apt-get -y update || true;

    case "${TOX_ENV}" in
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
        docs-spellcheck)
            sudo apt-get install libenchant-dev
            ;;
    esac
fi

sudo pip install virtualenv

if [[ "${MACAPP_ENV}" == "system" ]]; then
    brew install python
else
    virtualenv ~/.venv
    source ~/.venv/bin/activate
    pip install tox coveralls
    tox -e "${TOX_ENV}" --recreate --notest

    # If "installdeps" fails, "tox" exits with an error, and the "set -e" above
    # causes it to retry.  If "inst" fails, however, no error is reported for some
    # reason.  The following line causes "grep" to exit with error (and thanks to
    # "set -e", the whole script, so travis will retry it) if we didn't get to the
    # end stage of "inst" (i.e. installing mimic itself).
    ./.tox/"${TOX_ENV}"/bin/pip freeze | grep -e '^mimic=='
fi

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
        py27)
            brew upgrade pyenv
            pyenv install 2.7.9
            pyenv global 2.7.9
            ;;
        pypy)
            brew upgrade pyenv
            pyenv install pypy-2.5.1
            pyenv global pypy-2.5.1
            ;;
    esac
    pyenv rehash
    pip install --user virtualenv
else
    pip install virtualenv
fi

if [[ "${MACAPP_ENV}" == "system" ]]; then
    brew install python
else
    python -m virtualenv ~/.venv
    source ~/.venv/bin/activate
    pip install wheel
    pip wheel cryptography lxml
    pip install codecov
    tox --recreate --notest

    # If "installdeps" fails, "tox" exits with an error, and the "set -e" above
    # causes it to retry.  If "inst" fails, however, no error is reported for some
    # reason.  The following line causes "grep" to exit with error (and thanks to
    # "set -e", the whole script, so travis will retry it) if we didn't get to the
    # end stage of "inst" (i.e. installing mimic itself).
    ./.tox/"${TOXENV}"/bin/pip freeze | grep -e '^mimic=='
fi

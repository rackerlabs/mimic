#!/bin/bash

set -e
set -x

if [[ "$(uname -s)" == 'Darwin' ]]; then
    DARWIN=true
else
    DARWIN=false
fi

PYPY_VERSION="pypy-4.0.0";
PYTHON_VERSION="2.7.10";

if [[ "$DARWIN" = true ]]; then
    sw_vers; # report system version.
    brew update

    if which pyenv > /dev/null; then
        eval "$(pyenv init -)"
    fi

    case "${TOXENV}" in
        py27)
            brew install python
            ;;
        pypy)
            brew upgrade pyenv
            pyenv install "${PYPY_VERSION}";
            pyenv global "${PYPY_VERSION}";
            ;;
    esac
    pyenv rehash
    pip install --user virtualenv
else
    uname -a; # report system version
    # temporary pyenv installation to get pypy-2.6 before container infra upgrade
    if [[ "${TOXENV}" == "pypy" ]]; then
        git clone https://github.com/yyuu/pyenv.git ~/.pyenv
        PYENV_ROOT="$HOME/.pyenv"
        PATH="$PYENV_ROOT/bin:$PATH"
        eval "$(pyenv init -)"
        pyenv install "${PYPY_VERSION}";
        pyenv global "${PYPY_VERSION}";
    fi
    pip install virtualenv
fi

if [[ "${MACAPP_ENV}" == "system" ]]; then
    brew install python
else
    python -m virtualenv ~/.venv
    source ~/.venv/bin/activate
    pip install tox codecov
    coverage erase
    tox --recreate --notest

    # If "installdeps" fails, "tox" exits with an error, and the "set -e" above
    # causes it to retry.  If "inst" fails, however, no error is reported for some
    # reason.  The following line causes "grep" to exit with error (and thanks to
    # "set -e", the whole script, so travis will retry it) if we didn't get to the
    # end stage of "inst" (i.e. installing mimic itself).
    ./.tox/"${TOXENV}"/bin/pip freeze | grep -e '^mimic=='
fi

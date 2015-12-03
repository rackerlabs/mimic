#!/bin/bash

set -e
set -x

# Create an isolated virtualenv (travis's default is system-site-packages) for
# tooling, so that it's all the right versions.
virtualenv ~/.venv;
source ~/.venv/bin/activate;

pip install --upgrade pip;
pip install --upgrade pip;
pip --version;
pip install --upgrade --requirement=requirements/toolchain.txt;

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
            pyenv install pypy-2.6.1
            pyenv global pypy-2.6.1
            ;;
    esac
    pyenv rehash
else
    # temporary pyenv installation to get pypy-2.6 before container infra upgrade
    if [[ "${TOXENV}" == "pypy" ]]; then
        git clone https://github.com/yyuu/pyenv.git ~/.pyenv
        PYENV_ROOT="$HOME/.pyenv"
        PATH="$PYENV_ROOT/bin:$PATH"
        eval "$(pyenv init -)"
        pyenv install pypy-2.6.1
        pyenv global pypy-2.6.1
    fi
fi

if [[ "${MACAPP_ENV}" == "system" ]]; then
    deactivate;
    brew install python;
else
    # Codecov is special and must be allowed to float since it is a client for
    # an online service, and changes actually do need to be synchronized with
    # that service, unlike everything else which should be pinned to insulate
    # against behavior changes.
    pip install --upgrade --requirement=requirements/toolchain.txt codecov
    coverage erase
    tox --version;
    env;
    tox --recreate --notest

    # If "installdeps" fails, "tox" exits with an error, and the "set -e" above
    # causes it to retry.  If "inst" fails, however, no error is reported for some
    # reason.  The following line causes "grep" to exit with error (and thanks to
    # "set -e", the whole script, so travis will retry it) if we didn't get to the
    # end stage of "inst" (i.e. installing mimic itself).
    ./.tox/"${TOXENV}"/bin/pip freeze | grep -e '^mimic=='
fi

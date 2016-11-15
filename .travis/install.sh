#!/bin/bash

set -e
set -x

UPDATED_BREW="false";

function _brew_update () {
    if "${UPDATED_BREW}"; then
        return 0;
    else
        UPDATED_BREW=true;
        brew update;
    fi;
}

if [[ "${MACAPP_ENV}" == "system" ]]; then
    # If we are testing the mac app environment, it's a bit of a special case;
    # the only setup we need to do is to ensure that homebrew python is the
    # default.

    _brew_update;
    brew list python || brew install python;
    exit 0;
fi;

if [[ "$(uname -s)" == 'Darwin' ]]; then
    DARWIN="true";
else
    DARWIN="false";
fi


# Do we need to use a Python from pyenv, or will the system one suffice?
PYENV_PYTHON="";

if [[ "${TOXENV}" == "pypy" ]]; then
    PYENV_PYTHON="pypy-5.4.1";
    if [[ "$DARWIN" == "true" ]]; then
        _brew_update;
        brew install openssl;

        # Set up build environment so we can create Cryptography wheels if
        # necessary.
        kegpath="$(brew --prefix)/opt/openssl";
        export LDFLAGS="-L${kegpath}/lib $LDFLAGS";
        export CPPFLAGS="-I${kegpath}/include $CPPFLAGS";
        export CFLAGS="${LDFLAGS} ${CPPFLAGS} ${CFLAGS}";
        export PATH="${kegpath}/bin:$PATH";
    fi;
fi;

# If we need a python not available in Travis's environment, install pyenv in a
# way appropriate to the platform.

if [[ -n "${PYENV_PYTHON}" ]]; then
    if [[ "$DARWIN" == "true" ]]; then
        _brew_update;
        brew install pyenv || brew upgrade pyenv;
    else
        git clone https://github.com/yyuu/pyenv.git ~/.pyenv;
        PYENV_ROOT="$HOME/.pyenv";
        PATH="$PYENV_ROOT/bin:$PATH";
    fi
    eval "$(pyenv init -)";
    pyenv install "${PYENV_PYTHON}";
    pyenv global "${PYENV_PYTHON}";
    pyenv rehash;
fi;

# Now that we know which Python we're using, create an isolated virtualenv
# (travis's default is system-site-packages) for tooling, so that it's all the
# right versions.

virtualenv ~/.venv -p "$(which python)";
source ~/.venv/bin/activate;

pip install --upgrade pip;
pip --version;
# Codecov is special and must be allowed to float since it is a client for an
# online service, and changes actually do need to be synchronized with that
# service, unlike everything else which should be pinned to insulate against
# behavior changes.
pip install --upgrade --requirement=requirements/toolchain.txt codecov;
hash -r;

coverage erase;
tox --version;

tox --recreate --notest;

# Pip has no dependency resolver: https://github.com/pypa/pip/issues/988.  This
# means that if requirements.txt conflicts with setup.py, we won't find out
# about it from tox alone.  Therefore, let's ensure that we give tox *only* the
# versions of the wheels specified in the pinned dependencies, and ensure that
# they satisfy the requirements specified in setup.py.

export PIP_WHEEL_DIR=".wheels";
export PIP_FIND_LINKS=".wheels";

for req in requirements/*.txt; do
    # Ignore failures, because not all requirements are relevant on all
    # platforms.
    ./.tox/"${TOXENV}"/bin/pip wheel -r "${req}" < /dev/null || true;
done;

# If "installdeps" fails, "tox" exits with an error, and the "set -e" above
# causes it to retry.  If "inst" fails, however, no error is reported for some
# reason.  The following line causes "grep" to exit with error (and thanks to
# "set -e", the whole script, so travis will retry it) if we didn't get to the
# end stage of "inst" (i.e. installing mimic itself).
./.tox/"${TOXENV}"/bin/pip freeze | grep -e '^mimic==';

#!/bin/bash

set -e
set -x

if [[ "$(uname -s)" == "Darwin" ]]; then
    eval "$(pyenv init -)"
fi

if [[ "${MACAPP_ENV}" == "system" ]]; then
    ./build-app.sh;
    exit "$?";
fi;

source ~/.venv/bin/activate;

# Pip has no dependency resolver: https://github.com/pypa/pip/issues/988.  This
# means that if requirements.txt conflicts with setup.py, we won't find out
# about it from tox alone.  However, pip *will* barf if it is confronted with a
# situation where *all* it has to go on is `setup.py`, the local installed
# dependencies don't match, and it can't contact the index for more
# information.  So the following command ensures that the requirements
# specified in requirements.txt do not conflict with those specified in
# setup.py.  This is here, rather than in the tox configuration itself, because
# it depends on certain aspects of the tox run on travis: the installation has
# already completed so the sdist is in dist/ and not distshare/, there is only
# a single sdist, it is the current version, and there's no possibility the
# user used the '-e' option to skip building an sdist entirely.

./.tox/"${TOXENV}"/bin/pip install --no-index .tox/dist/*

tox --develop -- $TOX_FLAGS;

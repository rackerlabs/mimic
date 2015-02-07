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

    if [[ "${BUNDLE_ENV}" == "standalone" ]]; then
        brew install python
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
	    # travis/tox are not finding pypy when installed using pyenv.
            brew install pypy
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

    sudo apt-get -y update

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


# check if darwin here, then check if BUNDLE_ENV=system or standalone
sudo pip install virtualenv

# now dependencies for virtualenvs
case "${BUNDLE_ENV}" in
    system)
	virtualenv ~/.venv -p /usr/bin/python2.7 --system-site-packages
	source ~/.venv/bin/activate
	pip install -r requirements.txt
	pip install -r dev-requirements.txt
        ;;
    standalone)
	virtualenv ~/.venv -p /usr/local/bin/python2.7
	source ~/.venv/bin/activate
	pip install -r requirements.txt
	pip install -r dev-requirements.txt
	pip install -r py2app-requirements.txt
        ;;
    *)
        virtualenv ~/.venv
        source ~/.venv/bin/activate
        pip install tox coveralls
        ;;
esac

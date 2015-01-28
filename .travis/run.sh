#!/bin/bash

set -e
set -x


case "${TOX_ENV}" in
    bundle)
	virtualenv ~/.venv2 -p /usr/local/bin/python2.7
	source ~/.venv2/bin/activate
	pip install -r requirements.txt
	pip install -r dev-requirements.txt
	pip install -r py2app-requirements.txt
	make build
	make test
    ;;
    bundle-system)
	virtualenv ~/.venv2 -p /usr/bin/python2.7 --system-site-packages
	source ~/.venv2/bin/activate
	pip install -r requirements.txt
	pip install -r dev-requirements.txt
	make build
	make test
    ;;
    *)
	source ~/.venv/bin/activate
	tox -e $TOX_ENV
esac

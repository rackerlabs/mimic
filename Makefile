all: clean build test

build:
	python setup-mac.py py2app --extra-scripts=mimic-bundle/run-tests.py

test:
	./dist/mimic.app/Contents/MacOS/run-tests

clean:
	find . -name 'dist' -print0 | xargs rm -rf
	find . -name 'build' -print0 | xargs rm -rf

.PHONY:
	build test clean

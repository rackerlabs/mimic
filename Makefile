all: clean build test run

build:
	python setup-mac.py py2app --extra-scripts=bundle/run-tests.py

test:
	./dist/mimic.app/Contents/MacOS/run-tests

clean:
	find . -name 'dist' -print0 | xargs rm -rf
	find . -name 'build' -print0 | xargs rm -rf

run:
	open ./dist/mimic.app

.PHONY:
	build test clean run

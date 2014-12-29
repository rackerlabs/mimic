all: clean build test

build:
	python setup-mac.py py2app

test:
	./dist/mimic.app/Contents/MacOS/run-tests

clean:
	find . -name 'dist' -print0 | xargs rm -rf
	find . -name 'build' -print0 | xargs rm -rf

run:
	open ./dist/mimic.app

.PHONY:
	build test clean run

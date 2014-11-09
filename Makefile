build:	clean
	python setup.py py2app

clean:
	find . -name 'dist' -print0 | xargs rm -rf
	find . -name 'build' -print0 | xargs rm -rf

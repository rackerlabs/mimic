Getting started
===============

Working on ``mimic`` requires the installation of a small number of
development dependencies, which are listed in ``dev-requirements.txt``.
They can be installed in a `virtualenv`_ using `pip`_.
This also installs ``mimic`` in ``editable`` mode.

For example:

.. code-block:: console

    $ # Create a virtualenv and activate it
    $ pip install --requirement dev-requirements.txt

You are now ready to run the tests and build the documentation.

Some of the `tox`_ jobs may require certain packages to be installed, so
having `homebrew`_ installed would be useful if developing on Mac OS.


Running tests
~~~~~~~~~~~~~

``mimic`` unit tests are found in the ``mimic/test/`` directory.
They are written as `Twisted`_ tests and can be run either with Twisted's
`trial`_ or with ``unittest2``.

.. code-block:: console

    $ trial mimic

Or

.. code-block:: console

    $ python -m unittest discover

You can also check test coverage by using the `coverage`_ tool:

.. code-block:: console

    $ coverage run `which trial` mimic

Or

.. code-block:: console

    $ coverage run -m unittest discover


You can also run the tests for other python interpreters.  We use
`tox`_, which creates a `virtualenv`_ per tox job to run tests, linting, etc.:

.. code-block:: console

    $ tox
    ...
     py26: commands succeeded
     py27: commands succeeded
     pypy: commands succeeded
     docs: commands succeeded
     lint: commands succeeded


Building documentation
~~~~~~~~~~~~~~~~~~~~~~

``mimic`` documentation is stored in the ``docs/`` directory. It is
written in `reStructured Text`_ and rendered using `Sphinx`_.

To build the documentation, run ``sphinx``:

.. code-block:: console

    $ sphinx-build -W -b html -d _tmp/doctrees docs docs/_build/html

The HTML documentation index can now be found at
``docs/_build/html/index.html``.

Alternately, you can use our ``tox`` job:

.. code-block:: console

    $ tox -e docs

Building a Mac application
~~~~~~~~~~~~~~~~~~~~~~~~~~

``mimic`` can be built using either the system python or a standalone
application.

To build using the system python, you need only to create a `virtualenv`_
using the system python and the `pyobjc`_ and `py2app`_ packages
preinstalled on your system.

.. code-block:: console

   $ cd /dir/where/mimic/lives/

   # build a virtualenv using system of py2app and pyobjc
   $ virtualenv -p /usr/bin/python2.7 --system-site-packages ./venv
   $ source ./venv/bin/activate

   # install mimic's requirements
   $ pip install -r requirements.txt -r dev-requirements.txt

   # build the application and run its tests
   $ make


The alternative is to build the application without the dependency on the
system's python.

In my experience, it has been simplest to install a brewed 2.7 python.
To install a brew python, you'll need to have homebrew installed on your Mac.

.. code-block:: console

   $ brew install python
   $ cd /dir/where/mimic/lives/

   # build a virtualenv using the brewed python
   $ virtualenv -p /usr/local/bin/python2.7 ./venv
   $ source ./venv/bin/activate

   # install mimic's dependencies including pyobjc and py2app
   $ pip install -r requirements.txt
   $ pip install -r dev-requirements.txt
   $ pip install -r py2app-requirements.txt

   # build the application and run its tests
   $ make

Once built, ``mimic.app`` can be found in the ``./dist`` directory.
This application can be treated like any other mac application and moved into
~/Applications.

To run the application normally, you need only use ``open path/to/mimic.app``.
If you have just built the application, running ``make run`` from the
working directory will start mimic.

When the application is running, the letter ``M`` will be visible in the
menubar. To quit the application, simply click on the ``M`` and select
``Quit``. Application logs can be seen by opening
``Applications/Utilities/Console.app``.

To run ``mimic``\'s test suite using the application's bundled interpreter,
type

.. code-block:: console

   $ ./mimic.app/Contents/MacOS/run-tests

.. _`homebrew`: http://brew.sh/
.. _`pytest`: https://pypi.python.org/pypi/pytest
.. _`tox`: https://pypi.python.org/pypi/tox
.. _`virtualenv`: https://pypi.python.org/pypi/virtualenv
.. _`pip`: https://pypi.python.org/pypi/pip
.. _`sphinx`: https://pypi.python.org/pypi/Sphinx
.. _`reStructured Text`: http://sphinx-doc.org/rest.html
.. _`Twisted`: http://twistedmatrix.com
.. _`trial`: http://twistedmatrix.com/documents/current/core/howto/testing.html
.. _`unittest2`: https://pypi.python.org/pypi/unittest2
.. _`coverage`: https://pypi.python.org/pypi/coverage
.. _`pep8`: http://legacy.python.org/dev/peps/pep-0008/
.. _`pyflakes`: https://pypi.python.org/pypi/coverage
.. _`pyobjc`: https://pypi.python.org/pypi/pyobjc
.. _`py2app`: https://pypi.python.org/pypi/py2app

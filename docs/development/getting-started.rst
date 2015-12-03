Getting started
===============

Working on ``mimic`` requires the installation of a small number of development
dependencies, which are listed in ``requirements/development.txt``.  They can
be installed in a `virtualenv`_ using `pip`_.  This also installs ``mimic`` in
``editable`` mode.

For example:

.. code-block:: console

    $ # Create a virtualenv and activate it
    $ pip install --requirement requirements/development.txt

You are now ready to run the tests and build the documentation.

Some of the `tox`_ jobs may require certain packages to be installed, so
having `homebrew`_ installed would be useful if developing on Mac OS.


Running tests
~~~~~~~~~~~~~

``mimic`` unit tests are found in the ``mimic/test/`` directory.  Then can be
run via the built-in ``tox`` commands after setting up ``tox``.

.. code-block:: console

    $ tox -e py27

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

To build the documentation, use ``tox``:

.. code-block:: console

    $ tox -e docs

The HTML documentation index can now be found at
``docs/_build/html/index.html``.

Alternately, you can use ``sphinx`` directly, if you would like to specify
options:

.. code-block:: console

    $ sphinx-build -W -b html -d _tmp/doctrees docs docs/_build/html

Building a Mac application
~~~~~~~~~~~~~~~~~~~~~~~~~~

The officially supported method of building of the application depends on the
system python, and the `pyobjc`_, and `py2app`_ libraries.  `Travis-CI`_ is
configured to build the mac application and run its tests.

To build the application and run its tests locally use the following commands.

.. code-block:: console

   $ cd /dir/where/mimic/lives/
   $ ./build-app.sh


Once built, ``mimic.app`` can be found in the ``./dist`` directory.
This application can be treated like any other mac application and moved into
``~/Applications``.
To start ``mimic``, use the open command with the path to ``mimic.app``
, e.g. ``open ./dist/mimic.app``.

When the application is running, the letter ``M`` will be visible in the
menubar. To quit the application, simply click on the ``M`` and select
``Quit``. You can view the application logs by opening
``Applications/Utilities/Console.app``.

To run ``mimic.app``'s tests use

.. code-block:: console

   $ /path/to/mimic.app/Contents/MacOS/run-tests

The application can also built as a standalone application
that does not depend on the system python.
This is *not* the officially supported method of building the application and
is *not* tested by `Travis-CI`_.

To build a standalone application, ``py2app`` requires the installation of a
non-system framework python.
In my experience, it is easiest to install a brewed 2.7 python.
To install a brew python, you'll need to have `homebrew`_ installed.

The following commands will build the standalone application and run its
tests.

.. code-block:: console

   $ brew install python
   $ cd /dir/where/mimic/lives/

   # build a virtualenv using the brewed python
   $ virtualenv -p /usr/local/bin/python2.7 ./venv
   $ source ./venv/bin/activate

   # install mimic's dependencies including pyobjc and py2app
   $ pip install -r requirements/production.txt
   $ pip install -r requirements/mac-app.txt
   $ python setup.py py2app
   $ ./dist/mimic.app/Contents/MacOS/run-tests


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
.. _`Travis-CI`: https://travis-ci.org/rackerlabs/mimic

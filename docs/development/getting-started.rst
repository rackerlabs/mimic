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
     py27: commands succeeded
     pypy: commands succeeded
     docs: commands succeeded
     pep8: commands succeeded


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

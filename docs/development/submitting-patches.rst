Submitting patches
==================

* If you have access to the `mimic`_ repository, always make a new branch for
  your work.
* If you don't have access to the `mimic`_ repository, working on branches in
  your
  fork is also nice because that will you can work on more than one PR at a
  time.
* Patches should be small to facilitate easier review.

Code
----

When in doubt, refer to :pep:`8` for Python code (with some exceptions).
You can check if your code meets our automated requirements by running
``flake8`` against it.  Even better would be to run the ``tox`` job:

.. code-block:: console

    $ tox -e lint
    ...
      lint: commands succeeded
      congratulations :)

`Write comments as complete sentences.`_

Every Python code file must contain:

.. code-block:: python

    from __future__ import absolute_import, division


Tests
-----

All code changes must be accompanied by unit tests with 100% code coverage
(as measured by the tool `coverage`_.)

To test code coverage you'll need to install `detox`_ and `coverage`_.
They can be installed by running:

.. code-block:: console

   pip install --user requirements/toolchain.txt

(Or you may prefer to install those requirements in a ``virtualenv``.)

Then run:

.. code-block:: console

    $ coverage erase \
      && detox \
      && coverage combine \
      && coverage html

And open ``htmlcov/index.html`` in your web browser.

Documentation
-------------

All features should be documented with prose in the ``docs`` section.
To ensure it builds and passes style checks you can run `doc8`_ against it or
run our ``tox`` job to lint docs.  We also provide a spell-check job for docs:

.. code-block:: console

    $ tox -e docs
      docs: commands succeeded
      congratulations :)

    $ tox -e docs-spellcheck
      docs-spellcheck: commands succeeded
      congratulations :)

    $ tox -e docs-linkcheck
      docs-linkcheck: commands succeeded
      congratulations :)

The spell-check can catch jargon or abbreviations - if you are sure it is not
an error, please add that word to the :file:`spelling_wordlist.txt` in
alphabetical order.

Docstrings
==========

Docstrings generally follow `pep257`_, with a few exceptions.  They should
be written like this:

.. code-block:: python

    def some_function(some_arg):
        """
        Does some things.

        :param some_arg: Some argument.
        """

So, specifically:

* Always use three double quotes.
* Put the three double quotes on their own line.
* No blank line at the end.
* Use Sphinx parameter/attribute documentation `syntax`_.

The same job that lints code also lints docstrings:

.. code-block:: console

    $ tox -e lint
    ...
      lint: commands succeeded
      congratulations :)


.. _`mimic`: https://github.com/rackerlabs/mimic
.. _`Write comments as complete sentences.`: http://nedbatchelder.com/blog/201401/comments_should_be_sentences.html
.. _`syntax`: http://sphinx-doc.org/domains.html#info-field-lists
.. _`doc8`: https://github.com/stackforge/doc8
.. _`detox`: https://pypi.python.org/pypi/detox
.. _`coverage`: https://pypi.python.org/pypi/coverage
.. _`pep257`: http://legacy.python.org/dev/peps/pep-0257/

Submitting patches
==================

* If you have access to the `mimic`_ repo, always make a new branch for your
  work.
* If you don't have access to the `mimic`_ repo, working on branches in your
  fork is also nice because that will you can work on more than one PR at a
  time.
* Patches should be small to facilitate easier review.
* New features and significant bug fixes should be documented in the
  :doc:`/changelog`.

Code
----

When in doubt, refer to :pep:`8` for Python code (with some exceptions).
You can check if your code meets our automated requirements by running
``flake8`` against it:

.. code-block:: console

    $ flake8 --max-line-length 105 mimic

`Write comments as complete sentences.`_

Every code file must start with the boilerplate notice of the Apache License.
Additionally, every Python code file must contain

.. code-block:: python

    from __future__ import absolute_import, division, print_function


Tests
-----

All code changes must be accompanied by unit tests with 100% code coverage (as
measured by the tool `coverage`_.


Documentation
-------------

All features should be documented with prose in the ``docs`` section.
To ensure it builds and passes style checks you can run `doc8`_ against it.

Docstrings generally follow `pep257`_, with a few exceptions.  They should
be written like this:

.. code-block:: python

    def some_function(some_arg):
        """
        Does some things.

        :param some_arg: Some argument.
        """

To lint docstrings, run:

.. code-block:: console

    $ pep257 --ignore=D400,D401,D200,D203,D204,D205 mimic

So, specifically:

* Always use three double quotes.
* Put the three double quotes on their own line.
* No blank line at the end.
* Use Sphinx parameter/attribute documentation `syntax`_.

.. _`mimic`: https://github.com/rackerlabs/mimic
.. _`Write comments as complete sentences.`: http://nedbatchelder.com/blog/201401/comments_should_be_sentences.html
.. _`syntax`: http://sphinx-doc.org/domains.html#info-field-lists
.. _`doc8`: https://github.com/stackforge/doc8
.. _`coverage`: https://pypi.python.org/pypi/coverage
.. _`pep257`: http://legacy.python.org/dev/peps/pep-0257/

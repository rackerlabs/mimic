Submitting patches
==================

* If you have access to the `mimic`_ repository, always make a new branch for
  your work.
* If you don't have access to the `mimic`_ repository, working on branches in
  your
  fork is also nice because that will you can work on more than one PR at a
  time.
* Patches should be small to facilitate easier review.
* New features and significant bug fixes should be documented in the
  :doc:`/changelog`.

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

Every code file must start with the boilerplate notice of the Apache License.
Additionally, every Python code file must contain

.. code-block:: python

    from __future__ import absolute_import, division, print_function


Tests
-----

All code changes must be accompanied by unit tests with 100% branch code
coverage (as measured by the tool `coverage`_.) Test coverage is displayed as
part of our ``tox`` test jobs:

.. code-block:: console

    $ tox
    ...
    mimic.test.test_auth
      AuthIntegrationTests
        test_api_key_then_other_token_same_tenant ...                          [OK]
      ...
      TestRandomString
        test_length ...                                                        [OK]
        test_selectable ...                                                    [OK]

    -------------------------------------------------------------------------------
    Ran 389 tests in 5.000s

    PASSED (successes=389)
    py27-twisted_new_logging runtests: commands[2] | coverage report -m
    Name                                                    Stmts   Miss Branch BrMiss  Cover   Missing
    ---------------------------------------------------------------------------------------------------
    mimic/__init__                                              1      0      0      0   100%
    mimic/canned_responses/__init__                             0      0      0      0   100%
    mimic/canned_responses/auth                                29      0     10      0   100%
    ...
    mimic/session                                              72      0     28      2    98%
    mimic/tap                                                  19      0      2      0   100%
    mimic/util/__init__                                         0      0      0      0   100%
    mimic/util/helper                                          43      0      6      0   100%
    twisted/plugins/mimic                                       2      2      0      0     0%   4-7
    ---------------------------------------------------------------------------------------------------
    TOTAL                                                    2812      6    801     57    98%

To view per-line branch coverage, open the file `_htmlcov/<tox environment>/index.html`.


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
.. _`coverage`: https://pypi.python.org/pypi/coverage
.. _`pep257`: http://legacy.python.org/dev/peps/pep-0257/

JvPlot - Development Notes
==========================

This file contains notes about the development of PyPlot.  These notes
will likely only be useful to somebody who tries to modify or enhance
PyPlot.

Development Mode
----------------

To be able to make changes to the source without re-installing
the package after every change:

    python3 setup.py build
    pip3 install -e .

Unit Tests
----------

Unit tests use `pytest`_.  To run the tests call:

    pytest

.. _pytest: https://docs.pytest.org/en/latest/contents.html

Documentation
-------------

The JvPlot documentation is generated using `Sphinx`_.

.. _Sphinx: http://sphinx-doc.org/

Doc Strings
...........

The API documentation is extracted from the Python doc strings, using
the `Napoleon extension`_ for Sphinx.  Doc strings should follow the
`Google Python style guide`_.  To build the documentations:

    make -C doc html

.. _Napoleon extension: http://sphinxcontrib-napoleon.readthedocs.org/en/latest/
.. _Google Python style guide: https://github.com/google/styleguide/blob/gh-pages/pyguide.md

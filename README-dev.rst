JvPlot - Development Notes
==========================

This file contains notes about the development of PyPlot.  These notes
will likely only be useful to somebody who tries to modify or enhance
PyPlot.

Unit Tests
----------

Unit tests use the `Nose testing framework`_.

.. _Nose testing framework: https://nose.readthedocs.org/en/latest/

Documentation
-------------

The JvPlot documentation is generated using `Sphinx`_.

.. _Sphinx: http://sphinx-doc.org/

Doc Strings
...........

The API documentation is extracted from the Python doc strings, using
the `Napoleon extension`_ for Sphinx.  Doc strings should follow the
`Google Python style guide`_.

.. _Napoleon extension: http://sphinxcontrib-napoleon.readthedocs.org/en/latest/
.. _Google Python style guide: http://google.github.io/styleguide/pyguide.html#Comments
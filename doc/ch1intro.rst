Introduction
============

JvPlot is a Python package which can be used to non-interactively
generate plots using Python scripts.

Installation
------------

You can install JvPlot from source by downloading the source files and
using `setup.py` to install the package::

    git clone https://github.com/seehuhn/py-jvplot
    cd py-jvplot
    python setup.py install

Usage
-----

The JvPlot package is work in progress.  A simple example plot can be
generated as follows::

    import numpy as np

    from jvplot import JvPlot

    with JvPlot('test.pdf', '5in', '3in') as pl:
	pl.scatter_plot(np.random.rand(137),
			col=(1, 0, 0), size='1mm')

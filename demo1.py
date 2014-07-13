#! /usr/bin/env python

import numpy as np

from jvplot import Plot

with Plot('demo1.pdf', '3in', '4.5in') as pl:
    pl.scatter_plot(np.random.rand(1000), np.random.rand(1000), aspect=None)

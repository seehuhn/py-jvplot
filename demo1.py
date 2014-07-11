#! /usr/bin/env python

import numpy as np

from jvplot import Plot

with Plot('demo1.pdf', '4in', '4in') as pl:
    pl.scatter_plot(np.random.rand(1000), np.random.rand(1000))
